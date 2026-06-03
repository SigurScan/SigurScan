package ro.sigurscan.app

import java.net.URLDecoder
import java.nio.charset.Charset
import java.nio.charset.StandardCharsets

object PdfLinkExtractor {
    fun extractPdfAnnotationLinks(rawPdfBytes: ByteArray): Set<String> {
        val content = runCatching { rawPdfBytes.toString(Charsets.ISO_8859_1) }.getOrNull()
            ?: return emptySet()

        val candidates = linkedSetOf<String>()
        val patterns = listOf(
            Regex("""(?is)/A\s*<<[^>]*?/S\s*/URI[^>]*?/URI\s*(?<url><[^>]+>|\([^)]*\))"""),
            Regex("""(?is)/URI\s*(?<url><[^>]+>|\([^)]*\))""")
        )

        patterns.forEach { pattern ->
            pattern.findAll(content).forEach { match ->
                match.groupValues.getOrNull(1)?.takeIf { it.isNotBlank() }?.let { raw ->
                    candidates += decodePdfLinkCandidate(raw)
                }
            }
        }

        return candidates.toSet()
    }

    fun decodePdfLinkCandidate(rawCandidate: String): Set<String> {
        if (rawCandidate.isBlank()) return emptySet()

        val value = rawCandidate.trim()
        val decodedValue = when {
            value.startsWith("<") && value.endsWith(">") -> decodePdfHexUrl(value.substring(1, value.length - 1))
            value.startsWith("(") && value.endsWith(")") -> decodePdfLiteralString(value.substring(1, value.length - 1))
            else -> value
        }

        val percentDecoded = runCatching {
            URLDecoder.decode(decodedValue, StandardCharsets.UTF_8.name())
        }.getOrNull() ?: decodedValue

        return linkedSetOf(decodedValue, percentDecoded).filter { it.isNotBlank() }.toSet()
    }

    fun decodePdfHexUrl(rawHex: String): String {
        val cleaned = rawHex.replace(Regex("\\s"), "")
        if (cleaned.isBlank()) return ""

        val bytes = ByteArray(cleaned.length / 2)
        var index = 0
        var pointer = 0
        while (pointer + 1 < cleaned.length && index < bytes.size) {
            val byteAsString = cleaned.substring(pointer, pointer + 2)
            bytes[index++] = runCatching { byteAsString.toInt(16).toByte() }.getOrNull() ?: 0
            pointer += 2
        }

        return if (index == 0) "" else String(bytes, 0, index, Charset.forName("UTF-8"))
    }

    fun decodePdfLiteralString(rawValue: String): String {
        val builder = StringBuilder()
        var i = 0
        while (i < rawValue.length) {
            val current = rawValue[i]
            if (current != '\\' || i + 1 >= rawValue.length) {
                builder.append(current)
                i++
                continue
            }

            val next = rawValue[i + 1]
            if (next in '0'..'7') {
                var octal = ""
                var step = 0
                var pos = i + 1
                while (step < 3 && pos < rawValue.length) {
                    val candidate = rawValue[pos]
                    if (candidate !in '0'..'7') break
                    octal += candidate
                    pos++
                    step++
                }
                val decoded = runCatching { octal.toInt(8).toChar() }.getOrNull()
                builder.append(decoded ?: '\\')
                i = pos
                continue
            }

            when (next) {
                'n' -> builder.append('\n')
                'r' -> builder.append('\r')
                't' -> builder.append('\t')
                'b' -> builder.append('\b')
                'f' -> builder.append('\u000c')
                '(' -> builder.append('(')
                ')' -> builder.append(')')
                '\\' -> builder.append('\\')
                else -> builder.append(next)
            }
            i += 2
        }

        return builder.toString()
    }

}
