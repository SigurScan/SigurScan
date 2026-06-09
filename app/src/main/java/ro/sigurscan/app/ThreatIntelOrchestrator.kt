package ro.sigurscan.app

import java.net.URI
import java.net.URLDecoder
import java.net.URLEncoder
import java.nio.charset.StandardCharsets
import java.util.Locale
import kotlin.math.max

internal object ThreatIntelOrchestrator {
    private val sensitiveQueryKeys = setOf(
        "email",
        "e-mail",
        "mail",
        "phone",
        "telefon",
        "user",
        "username",
        "name",
        "full_name",
        "firstname",
        "first_name",
        "lastname",
        "last_name",
        "nume",
        "cnp",
        "iban",
        "card",
        "cvv",
        "cvc",
        "otp",
        "code",
        "cod",
        "token",
        "auth",
        "session",
        "sid",
        "sig",
        "signature",
        "reset",
        "password",
        "parola",
        "uid",
        "bid",
        "pcid",
        "u_action_id",
        "customer",
        "~customer_keyword",
        "gclid",
        "fbclid",
        "msclkid"
    )
    private val emailValueRegex = Regex("""(?i)[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}""")
    private val longTokenValueRegex = Regex("""(?i)^[a-z0-9_\-=]{28,}$""")

    fun buildUrlscanSubmissionBody(
        url: String,
        visibility: String = "private",
        country: String? = null,
        customAgent: String? = null
    ): String {
        val safeVisibility = when (visibility.lowercase(Locale.US)) {
            "private" -> "private"
            "unlisted" -> "unlisted"
            else -> "private"
        }
        val parts = mutableListOf(
            "\"url\":\"${escapeJson(sanitizeUrlForSandbox(url))}\"",
            "\"visibility\":\"$safeVisibility\""
        )
        country?.trim()?.lowercase(Locale.US)?.take(2)?.takeIf { it.isNotBlank() }?.let {
            parts.add("\"country\":\"${escapeJson(it)}\"")
        }
        customAgent?.trim()?.take(512)?.takeIf { it.isNotBlank() }?.let {
            parts.add("\"customagent\":\"${escapeJson(it)}\"")
        }
        return "{${parts.joinToString(",")}}"
    }

    fun sanitizeUrlForSandbox(url: String): String {
        val cleaned = url.trim()
        val normalized = when {
            cleaned.startsWith("http://", ignoreCase = true) || cleaned.startsWith("https://", ignoreCase = true) -> cleaned
            cleaned.startsWith("www.", ignoreCase = true) -> "https://$cleaned"
            else -> cleaned
        }

        return runCatching {
            val uri = URI(normalized)
            val query = uri.rawQuery ?: return@runCatching normalized
            val keptParams = query.split('&')
                .mapNotNull { pair ->
                    if (pair.isBlank()) return@mapNotNull null
                    val rawKey = pair.substringBefore('=')
                    val rawValue = pair.substringAfter('=', missingDelimiterValue = "")
                    val key = decode(rawKey).lowercase(Locale.US)
                    val decodedValue = decode(rawValue)
                    if (
                        key.startsWith("utm_") ||
                        key in sensitiveQueryKeys ||
                        isSensitiveQueryValue(decodedValue)
                    ) return@mapNotNull null
                    if (rawValue.isBlank()) encode(key) else "${encode(key)}=${encode(decodedValue)}"
                }

            val sanitizedQuery = keptParams.takeIf { it.isNotEmpty() }?.joinToString("&")
            URI(
                uri.scheme,
                uri.authority,
                uri.path,
                sanitizedQuery,
                null
            ).toString()
        }.getOrElse { normalized }
    }

    fun shouldRunDeepReputation(
        riskLevel: String,
        existingThreatIntel: List<ThreatIntelSourceResult>,
        webRisk: ThreatIntelSourceResult?
    ): Boolean {
        if (webRisk?.severity.equals("high", ignoreCase = true)) return false

        val normalizedRisk = riskLevel.lowercase(Locale.US)
        val localRiskNeedsFallback = normalizedRisk in listOf("medium", "high", "critical")
        val unclearOrSuspiciousEvidence = existingThreatIntel.any { item ->
            item.severity.equals("medium", ignoreCase = true) ||
                item.verdict.contains("suspicious", ignoreCase = true) ||
                item.verdict.contains("unknown", ignoreCase = true) ||
                item.verdict.contains("not found", ignoreCase = true) ||
                item.details?.contains("informații limitate", ignoreCase = true) == true
        }
        val webRiskUnavailable = webRisk == null

        return localRiskNeedsFallback || unclearOrSuspiciousEvidence || (webRiskUnavailable && normalizedRisk != "low")
    }

    fun applyThreatIntelEvidence(
        current: OfflineAssessment,
        threatIntel: List<ThreatIntelSourceResult>
    ): OfflineAssessment {
        val strongest = threatIntel.firstOrNull { item ->
            item.severity.equals("high", ignoreCase = true) &&
                listOf("Google Web Risk", "urlscan.io", "Phishing.Database", "phishing_database", "URLhaus").any { source ->
                    item.source.equals(source, ignoreCase = true)
                }
        } ?: return current.copy(threatIntel = threatIntel)

        val reason = "Scanarea online a confirmat risc ridicat pentru linkul verificat."

        return current.copy(
            family = if (current.family == "Necunoscut" || current.family == "Analiză Link Extern" || current.family == "Link cu risc scăzut") {
                "Risc confirmat de reputație"
            } else {
                current.family
            },
            riskScore = max(current.riskScore, 90),
            riskLevel = "high",
            reasons = (current.reasons + reason).distinct(),
            keyDangers = (
                current.keyDangers +
                    "Scanarea indică risc real pentru linkul verificat."
                ).distinct(),
            safeActions = (
                current.safeActions +
                    listOf(
                        "Nu apăsa pe link.",
                        "Nu introduce date, card, parolă sau cod OTP pe pagina respectivă.",
                        "Verifică manual în aplicația sau site-ul oficial."
                    )
                ).distinct(),
            threatIntel = threatIntel
        )
    }

    private fun decode(value: String): String {
        return runCatching {
            URLDecoder.decode(value, StandardCharsets.UTF_8.name())
        }.getOrElse { value }
    }

    private fun isSensitiveQueryValue(value: String): Boolean {
        val trimmed = value.trim()
        if (trimmed.isBlank()) return false
        if (emailValueRegex.containsMatchIn(trimmed)) return true
        if (longTokenValueRegex.matches(trimmed) && trimmed.any(Char::isDigit) && trimmed.any(Char::isLetter)) return true
        return false
    }

    private fun encode(value: String): String {
        return URLEncoder.encode(value, StandardCharsets.UTF_8.name())
            .replace("+", "%20")
    }

    private fun escapeJson(value: String): String {
        return buildString {
            value.forEach { char ->
                when (char) {
                    '\\' -> append("\\\\")
                    '"' -> append("\\\"")
                    '\n' -> append("\\n")
                    '\r' -> append("\\r")
                    '\t' -> append("\\t")
                    else -> append(char)
                }
            }
        }
    }
}
