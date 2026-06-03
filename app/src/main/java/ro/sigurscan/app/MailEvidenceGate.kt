package ro.sigurscan.app

import java.net.URI
import java.net.URLDecoder
import java.nio.charset.StandardCharsets
import java.util.Locale
import java.util.regex.Pattern
import kotlin.math.max

object MailEvidenceGate {
    private val urlRegex = Pattern.compile(
        "(?:https?://|www\\.)[\\w\\-.~:/?#\\[\\]@!$&'()*+,;=%]+",
        Pattern.CASE_INSENSITIVE
    )

    private val weakMarketingSignals = listOf(
        "azi doar",
        "oferta limitata",
        "ofertă limitată",
        "nu rata",
        "profita",
        "profită",
        "voucher",
        "promotie",
        "promoție",
        "reducere",
        "ultima sansa",
        "ultima șansă"
    )

    private val sensitiveActionSignals = listOf(
        "card",
        "cvv",
        "cvc",
        "otp",
        "parola",
        "parolă",
        "password",
        "login",
        "logare",
        "iban",
        "cnp",
        "plata",
        "plată",
        "pay",
        "payment",
        "checkout",
        "verify",
        "verifica",
        "verifică",
        "actualizeaza",
        "actualizează",
        "deblocheaza",
        "deblochează",
        "unlock"
    )

    private val suspiciousDomainHints = listOf(
        ".ru",
        ".top",
        ".xyz",
        ".pw",
        ".click",
        ".shop",
        ".online",
        ".info",
        ".biz",
        ".site",
        ".fun"
    )

    private val brandSignals = mapOf(
        "Uber" to listOf("uber", "ubereats", "uber eats"),
        "eMAG" to listOf("emag", "eMAG"),
        "FAN Courier" to listOf("fan courier", "fancourier"),
        "Poșta Română" to listOf("posta romana", "poșta română", "posta-romana"),
        "ANAF" to listOf("anaf", "spv", "mfinante"),
        "Revolut" to listOf("revolut"),
        "Banca Transilvania" to listOf("banca transilvania", "bt pay", "btpay"),
        "BCR" to listOf("bcr", "george"),
        "ING" to listOf("ing")
    )

    private val brandOfficialDomains = mapOf(
        "Uber" to ScamRules.TRUSTED_OFFICIAL_DOMAINS["uber"].orEmpty(),
        "eMAG" to ScamRules.TRUSTED_OFFICIAL_DOMAINS["emag"].orEmpty(),
        "FAN Courier" to ScamRules.TRUSTED_OFFICIAL_DOMAINS["fanCourier"].orEmpty(),
        "Poșta Română" to ScamRules.TRUSTED_OFFICIAL_DOMAINS["postaRomana"].orEmpty(),
        "ANAF" to ScamRules.TRUSTED_OFFICIAL_DOMAINS["anaf"].orEmpty(),
        "Revolut" to listOf("revolut.com", "revolut.me"),
        "Banca Transilvania" to listOf("bancatransilvania.ro", "btpay.ro", "neo-bt.ro", "neo.bancatransilvania.ro"),
        "BCR" to listOf("bcr.ro", "george.bcr.ro"),
        "ING" to listOf("ing.ro", "ing.com", "ingbusiness.ro")
    )

    private val trustedMarketingRedirectHosts = listOf(
        "sng.link",
        "app.link",
        "branch.link",
        "bnc.lt",
        "safelinks.protection.outlook.com",
        "urldefense.com",
        "google.com",
        "facebook.com"
    )

    fun apply(current: OfflineAssessment, scannedText: String): OfflineAssessment {
        val normalized = scannedText.lowercase(Locale.getDefault())
        val urls = extractUrls(scannedText)
        val isSharedMailPayload = normalized.contains("scanare mail:") ||
            normalized.contains("url-uri ascunse/expuse detectate")

        if (!isSharedMailPayload || urls.isEmpty()) return current

        val riskLevel = current.riskLevel.lowercase(Locale.getDefault())
        if (riskLevel !in listOf("low", "safe", "none", "unknown") && current.riskScore >= 45) {
            return current
        }

        val actionableUrls = urls.distinct()
        if (actionableUrls.all { isTrustedOfficialOrMarketingRedirect(it, normalized) }) {
            return current
        }

        val evidence = buildMediumEvidence(actionableUrls, normalized)
        if (evidence.isEmpty()) {
            return current
        }

        val reasons = (current.reasons + evidence).distinct()
        val keyDangers = (
            current.keyDangers +
                "Butonul sau textul vizibil poate trimite către un domeniu neoficial care cere date sensibile."
            ).distinct()
        val safeActions = (
            current.safeActions +
                "Nu apăsa pe buton până nu confirmi domeniul final în aplicația sau site-ul oficial."
            ).distinct()

        return current.copy(
            family = if (current.family == "Necunoscut" || current.family == "Analiză Link Extern") {
                "Mail cu link ascuns"
            } else {
                current.family
            },
            riskScore = max(current.riskScore, 55),
            riskLevel = "medium",
            reasons = reasons,
            keyDangers = keyDangers,
            safeActions = safeActions
        )
    }

    private fun buildMediumEvidence(urls: List<String>, normalizedText: String): List<String> {
        val untrustedUrls = urls.filterNot { isTrustedOfficialOrMarketingRedirect(it, normalizedText) }
        if (untrustedUrls.isEmpty()) return emptyList()

        val reasons = mutableListOf<String>()
        val claimedBrands = detectClaimedBrands(normalizedText)
        val sensitiveIntent = hasSensitiveActionIntent(normalizedText, untrustedUrls)
        val suspiciousDomain = untrustedUrls.any { url ->
            val host = hostOf(url)
            suspiciousDomainHints.any { hint -> host.endsWith(hint) || url.lowercase(Locale.US).contains(hint) }
        }

        val mismatchedBrand = claimedBrands.firstOrNull { brand ->
            val officialDomains = brandOfficialDomains[brand].orEmpty()
            officialDomains.isNotEmpty() && untrustedUrls.any { url -> !isOfficialForDomains(url, officialDomains) }
        }

        if (mismatchedBrand != null && sensitiveIntent) {
            reasons.add("Mesajul pretinde $mismatchedBrand, dar linkul duce către un domeniu neoficial și cere o acțiune sensibilă.")
        } else if (sensitiveIntent) {
            reasons.add("Linkul din structura HTML duce către un domeniu neoficial asociat cu date sensibile sau verificare.")
        }

        if (suspiciousDomain) {
            reasons.add("Un link extras din mail folosește un domeniu cu reputație/terminație des întâlnită în campanii suspecte.")
        }

        val onlyWeakMarketing = weakMarketingSignals.any { normalizedText.contains(it) } &&
            !sensitiveIntent &&
            !suspiciousDomain &&
            mismatchedBrand == null
        if (onlyWeakMarketing) return emptyList()

        return reasons.distinct()
    }

    private fun detectClaimedBrands(normalizedText: String): List<String> {
        return brandSignals
            .filterValues { signals -> signals.any { normalizedText.contains(it.lowercase(Locale.getDefault())) } }
            .keys
            .toList()
    }

    private fun hasSensitiveActionIntent(normalizedText: String, urls: List<String>): Boolean {
        if (sensitiveActionSignals.any { normalizedText.contains(it) }) return true
        return urls.any { url ->
            val normalizedUrl = url.lowercase(Locale.US)
            sensitiveActionSignals.any { normalizedUrl.contains(it) }
        }
    }

    private fun isTrustedOfficialOrMarketingRedirect(url: String, normalizedText: String): Boolean {
        if (isTrustedOfficialUrl(url)) return true

        val host = hostOf(url)
        val isKnownRedirector = trustedMarketingRedirectHosts.any { known ->
            host == known || host.endsWith(".$known")
        }
        if (!isKnownRedirector) return false

        val extractedDestinations = HtmlLinkExtractor.extractHtmlLinks(url)
            .filter { it != url }
        if (extractedDestinations.any(::isTrustedOfficialUrl)) return true

        return hasTrustedAppDeepLink(url, normalizedText)
    }

    private fun hasTrustedAppDeepLink(url: String, normalizedText: String): Boolean {
        val params = queryParams(url)
        val deepLink = params["_dl"] ?: params["deep_link"] ?: params["app_link"] ?: return false
        val scheme = deepLink.substringBefore("://", missingDelimiterValue = "").lowercase(Locale.US)
        return scheme == "uber" && normalizedText.contains("uber")
    }

    private fun isTrustedOfficialUrl(url: String): Boolean {
        return isOfficialForDomains(url, ScamRules.TRUSTED_OFFICIAL_DOMAINS.values.flatten())
    }

    private fun isOfficialForDomains(url: String, officialDomains: List<String>): Boolean {
        val host = hostOf(url).removePrefix("www.")
        if (host.isBlank()) return false

        return officialDomains.any { domain ->
            val normalizedDomain = domain.lowercase(Locale.US).removePrefix("www.")
            host == normalizedDomain || host.endsWith(".$normalizedDomain")
        }
    }

    private fun extractUrls(input: String): List<String> {
        val matcher = urlRegex.matcher(input)
        val urls = mutableListOf<String>()
        while (matcher.find()) {
            urls.add(matcher.group().trimEnd('.', ',', ';', ')', ']', '}', '"', '\''))
        }
        return urls
    }

    private fun hostOf(url: String): String {
        val normalized = normalizeUrl(url)
        return runCatching {
            URI(normalized).host.orEmpty()
        }.getOrElse {
            normalized.substringAfter("://", normalized)
                .substringBefore('/')
                .substringBefore('?')
                .substringBefore('#')
                .substringBefore(':')
        }.lowercase(Locale.US)
    }

    private fun normalizeUrl(url: String): String {
        val cleaned = url.trim().trimEnd('.', ',', ';', ')', ']', '}', '"', '\'')
        return when {
            cleaned.startsWith("http://", ignoreCase = true) || cleaned.startsWith("https://", ignoreCase = true) -> cleaned
            cleaned.startsWith("www.", ignoreCase = true) -> "https://$cleaned"
            else -> cleaned
        }
    }

    private fun queryParams(url: String): Map<String, String> {
        val query = normalizeUrl(url)
            .substringAfter('?', missingDelimiterValue = "")
            .substringBefore('#')
        if (query.isBlank()) return emptyMap()

        return query.split('&')
            .mapNotNull { pair ->
                val key = pair.substringBefore('=').lowercase(Locale.US)
                val value = pair.substringAfter('=', missingDelimiterValue = "")
                if (key.isBlank() || value.isBlank()) return@mapNotNull null
                key to decode(value)
            }
            .toMap()
    }

    private fun decode(value: String): String {
        return runCatching {
            URLDecoder.decode(value, StandardCharsets.UTF_8.name())
        }.getOrElse { value }
    }
}
