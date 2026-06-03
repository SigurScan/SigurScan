package ro.sigurscan.app

import java.util.regex.Pattern

internal object UrlTextExtractor {
    private val explicitUrlRegex = Pattern.compile(
        "(?:https?://|www\\.)[\\w\\-.~:/?#\\[\\]@!$&'()*+,;=%]+",
        Pattern.CASE_INSENSITIVE
    )

    private val bareDomainRegex = Pattern.compile(
        "(?<![@\\w.-])(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\\.)+(?:ro|com|org|net|eu|info|online|shop|xyz|top|click|biz|site|fun|app|link|me|space|delivery|gov|io|co|uk|de|fr|it|es|nl|be|pl|hu|bg|md)(?:/[\\w\\-.~:/?#\\[\\]@!$&'()*+,;=%]*)?",
        Pattern.CASE_INSENSITIVE
    )

    fun extract(input: String): List<String> {
        if (input.isBlank()) return emptyList()
        val urls = linkedSetOf<String>()
        collectMatches(explicitUrlRegex, input, urls)
        collectMatches(bareDomainRegex, input, urls)
        return urls.toList()
    }

    fun normalizeCandidate(raw: String?): String? {
        if (raw.isNullOrBlank()) return null
        val cleaned = raw
            .trim()
            .trimEnd('.', ',', ';', ':', ')', ']', '}', '"', '\'', '`')
            .takeIf { it.contains('.') }
            ?: return null
        val withoutTrailingSlashNoise = cleaned.trim()
        return when {
            withoutTrailingSlashNoise.startsWith("http://", ignoreCase = true) ||
                withoutTrailingSlashNoise.startsWith("https://", ignoreCase = true) -> withoutTrailingSlashNoise
            withoutTrailingSlashNoise.startsWith("//") -> "https:$withoutTrailingSlashNoise"
            else -> "https://$withoutTrailingSlashNoise"
        }
    }

    private fun collectMatches(pattern: Pattern, input: String, output: MutableSet<String>) {
        val matcher = pattern.matcher(input)
        while (matcher.find()) {
            val normalized = normalizeCandidate(matcher.group()) ?: continue
            output.add(normalized)
        }
    }
}
