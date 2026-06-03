package ro.sigurscan.app

import java.net.URI
import java.util.Locale
import java.util.regex.Pattern
import kotlin.math.min

internal object OfflineRiskPolicy {
    private val urlRegex = Pattern.compile(
        "(?:https?://|www\\.)[\\w\\-.~:/?#\\[\\]@!$&'()*+,;=%]+",
        Pattern.CASE_INSENSITIVE
    )

    private val marketingOnlySignals = listOf(
        "azi doar",
        "oferta",
        "ofertă",
        "oferta limitata",
        "ofertă limitată",
        "nu rata",
        "profita",
        "profită",
        "voucher",
        "promotie",
        "promoție",
        "reducere",
        "discount",
        "card cadou",
        "premiu",
        "gratuit",
        "castiga",
        "câștigă",
        "castigat",
        "câștigat",
        "ultima sansa",
        "ultima șansă"
    )

    private val explicitSensitiveDataSignals = listOf(
        "cvv",
        "cvc",
        "otp",
        "parola",
        "parolă",
        "password",
        "iban",
        "cnp",
        "cod pin",
        "pin bancar",
        "datele cardului",
        "date card",
        "numar card",
        "număr card"
    )

    private val officialDomains = ScamRules.TRUSTED_OFFICIAL_DOMAINS.values.flatten().distinct()

    fun applyEvidenceCap(
        current: OfflineAssessment,
        scannedText: String
    ): OfflineAssessment {
        val normalized = scannedText.lowercase(Locale.getDefault())
        val urls = extractUrls(scannedText)
        val hasExplicitSensitiveData = explicitSensitiveDataSignals.any { normalized.contains(it) }
        if (hasExplicitSensitiveData) return current

        val riskLevel = current.riskLevel.lowercase(Locale.getDefault())
        val looksMarketingOnly = marketingOnlySignals.any { normalized.contains(it) } ||
            familyLooksTextDerived(current.family)

        val allUrlsOfficial = urls.isNotEmpty() && urls.all(::isOfficialUrl)
        if (allUrlsOfficial && looksMarketingOnly) {
            return current.copy(
                family = "Marketing pe domeniu oficial",
                riskScore = min(current.riskScore, 25),
                riskLevel = "low",
                reasons = (
                    current.reasons +
                        "Offline: linkul detectat folosește un domeniu oficial cunoscut; limbajul de ofertă nu este dovadă de scam."
                    ).distinct(),
                safeActions = (
                    current.safeActions +
                        "Poți continua cu prudență dacă recunoști expeditorul și nu ți se cer coduri sau date de card."
                    ).distinct(),
                keyDangers = current.keyDangers.filterNot { it.contains("fals", ignoreCase = true) }
            )
        }

        if (riskLevel in listOf("high", "critical") && looksMarketingOnly) {
            return current.copy(
                family = "Verificare oficială recomandată",
                riskScore = min(current.riskScore, 60),
                riskLevel = "medium",
                reasons = (
                    current.reasons +
                        "Offline: avem doar semnale de text/marketing, fără reputație externă sau confirmare a destinației finale."
                    ).distinct(),
                safeActions = (
                    current.safeActions +
                        "Verifică oferta pe canalul oficial înainte să folosești linkul primit."
                    ).distinct(),
                keyDangers = (
                    current.keyDangers +
                        "Nu avem destule dovezi tehnice ca să clasificăm mesajul drept fraudă confirmată."
                    ).distinct()
            )
        }

        return current
    }

    private fun familyLooksTextDerived(family: String): Boolean {
        val normalized = family.lowercase(Locale.getDefault())
        return listOf("fals", "premiu", "scam detectat", "link suspect").any { normalized.contains(it) }
    }

    private fun extractUrls(input: String): List<String> {
        val matcher = urlRegex.matcher(input)
        val urls = mutableListOf<String>()
        while (matcher.find()) {
            urls.add(matcher.group().trimEnd('.', ',', ';', ')', ']', '}'))
        }
        return urls
    }

    private fun isOfficialUrl(url: String): Boolean {
        val normalized = when {
            url.startsWith("http://", ignoreCase = true) || url.startsWith("https://", ignoreCase = true) -> url
            url.startsWith("www.", ignoreCase = true) -> "https://$url"
            else -> "https://$url"
        }
        val host = runCatching { URI(normalized).host?.lowercase(Locale.US)?.removePrefix("www.") }
            .getOrNull()
            ?: return false
        return officialDomains.any { official ->
            host == official || host.endsWith(".$official")
        }
    }
}
