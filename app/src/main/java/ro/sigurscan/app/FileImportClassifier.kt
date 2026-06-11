package ro.sigurscan.app

import java.util.Locale

internal enum class FileImportKind {
    TEXT,
    HTML,
    EMAIL,
    PDF,
    OUTLOOK_MSG_UNSUPPORTED,
    UNSUPPORTED
}

internal object FileImportClassifier {
    fun classify(fileName: String, mimeType: String?): FileImportKind {
        val lowerName = fileName.lowercase(Locale.getDefault())
        val lowerMime = mimeType.orEmpty().lowercase(Locale.getDefault())

        return when {
            lowerName.endsWith(".pdf") || lowerMime.startsWith("application/pdf") -> FileImportKind.PDF
            lowerName.endsWith(".html") || lowerName.endsWith(".htm") || lowerMime.startsWith("text/html") -> FileImportKind.HTML
            lowerName.endsWith(".eml") || lowerMime == "message/rfc822" -> FileImportKind.EMAIL
            lowerName.endsWith(".msg") -> FileImportKind.OUTLOOK_MSG_UNSUPPORTED
            lowerName.endsWith(".txt") || lowerMime == "text/plain" -> FileImportKind.TEXT
            else -> FileImportKind.UNSUPPORTED
        }
    }
}
