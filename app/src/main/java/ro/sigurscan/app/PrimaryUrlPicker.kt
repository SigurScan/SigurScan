package ro.sigurscan.app

import java.net.URI
import java.util.Locale

internal object PrimaryUrlPicker {
    private val officialDomains = ScamRules.TRUSTED_OFFICIAL_DOMAINS.values.flatten().distinct()

    private val ignoredPathHints = listOf(
        "unsubscribe",
        "dezabon",
        "optout",
        "opt-out",
        "preferences",
        "terms",
        "termeni",
        "privacy",
        "protectia-datelor",
        "legal",
        "contact",
        "support",
        "suport",
        "help"
    )

    private val sensitivePathHints = listOf(
        "login",
        "logare",
        "verify",
        "verifica",
        "verificare",
        "secure",
        "account",
        "cont",
        "unlock",
        "debloc",
        "payment",
        "pay",
        "plata",
        "taxa",
        "card",
        "otp",
        "password",
        "parola",
        "spv",
        "invoice",
        "factura"
    )

    private val suspiciousTlds = listOf(
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

    private val brandHints = mapOf(
        "emag" to listOf("emag"),
        "uber" to listOf("uber", "ubereats"),
        "fan courier" to listOf("fan", "fancourier", "fan courier"),
        "posta romana" to listOf("posta", "poșta", "posta romana", "poșta română"),
        "anaf" to listOf("anaf", "spv"),
        "revolut" to listOf("revolut"),
        "bcr" to listOf("bcr", "george"),
        "ing" to listOf("ing"),
        "banca transilvania" to listOf("bt", "banca transilvania", "btpay")
    )

    fun pick(candidates: Collection<String>, rawText: String = ""): String {
        return candidates
            .mapNotNull(::normalize)
            .distinct()
            .map { candidate ->
                RankedUrl(
                    url = candidate,
                    score = score(candidate, rawText)
                )
            }
            .maxWithOrNull(compareBy<RankedUrl> { it.score }.thenByDescending { it.url.length })
            ?.url
            .orEmpty()
    }

    private fun score(url: String, rawText: String): Int {
        val host = hostOf(url)
        val lowerUrl = url.lowercase(Locale.US)
        val official = isOfficialHost(host)
        var score = if (official) 10 else 100

        if (isIgnoredUtilityUrl(lowerUrl)) score -= 160
        if (sensitivePathHints.any { lowerUrl.contains(it) }) score += 45
        if (suspiciousTlds.any { host.endsWith(it) }) score += 35

        val claimedBrandTokens = detectClaimedBrandTokens(rawText)
        if (!official && claimedBrandTokens.any { host.contains(it) || lowerUrl.contains(it) }) {
            score += 35
        }

        if (official && claimedBrandTokens.isNotEmpty()) score -= 20
        return score
    }

    private fun detectClaimedBrandTokens(rawText: String): List<String> {
        val normalized = rawText.lowercase(Locale.getDefault())
        return brandHints
            .filter { (brand, hints) -> normalized.contains(brand) || hints.any { normalized.contains(it) } }
            .flatMap { it.value }
            .map { it.replace(" ", "") }
            .distinct()
    }

    private fun isIgnoredUtilityUrl(lowerUrl: String): Boolean {
        if (ignoredPathHints.any { lowerUrl.contains(it) }) return true
        return listOf(".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".css", ".js").any {
            lowerUrl.substringBefore('?').endsWith(it)
        }
    }

    private fun normalize(raw: String): String? {
        val trimmed = raw.trim()
        val normalized = when {
            trimmed.startsWith("http://", ignoreCase = true) || trimmed.startsWith("https://", ignoreCase = true) -> trimmed
            trimmed.startsWith("www.", ignoreCase = true) -> "https://$trimmed"
            else -> trimmed
        }
        return HtmlLinkExtractor.normalizeCandidateUrl(normalized)
            ?: normalized.takeIf { it.startsWith("http://", true) || it.startsWith("https://", true) }
    }

    private fun isOfficialHost(host: String): Boolean {
        return officialDomains.any { official ->
            host == official || host.endsWith(".$official")
        }
    }

    private fun hostOf(url: String): String {
        return runCatching { URI(url).host?.lowercase(Locale.US)?.removePrefix("www.") }
            .getOrNull()
            .orEmpty()
    }

    private data class RankedUrl(
        val url: String,
        val score: Int
    )
}
