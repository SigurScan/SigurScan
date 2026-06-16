package ro.sigurscan.app

import org.junit.Assert.assertEquals
import org.junit.Test

class FileImportClassifierTest {
    @Test
    fun classifiesSupportedDocumentInputs() {
        assertEquals(FileImportKind.PDF, FileImportClassifier.classify("factura.pdf", "application/octet-stream"))
        assertEquals(FileImportKind.PDF, FileImportClassifier.classify("download", "application/pdf"))
        assertEquals(FileImportKind.HTML, FileImportClassifier.classify("mail.html", "text/plain"))
        assertEquals(FileImportKind.HTML, FileImportClassifier.classify("download", "text/html; charset=utf-8"))
        assertEquals(FileImportKind.EMAIL, FileImportClassifier.classify("mesaj.eml", "application/octet-stream"))
        assertEquals(FileImportKind.EMAIL, FileImportClassifier.classify("download", "message/rfc822"))
        assertEquals(FileImportKind.TEXT, FileImportClassifier.classify("sms.txt", "application/octet-stream"))
        assertEquals(FileImportKind.TEXT, FileImportClassifier.classify("download", "text/plain"))
        assertEquals(FileImportKind.AUDIO, FileImportClassifier.classify("voice-note.m4a", "application/octet-stream"))
        assertEquals(FileImportKind.AUDIO, FileImportClassifier.classify("whatsapp.opus", "audio/ogg"))
        assertEquals(FileImportKind.AUDIO, FileImportClassifier.classify("download", "audio/mpeg"))
    }

    @Test
    fun rejectsFormatsThatDoNotHaveAProvenExtractor() {
        assertEquals(FileImportKind.OUTLOOK_MSG_UNSUPPORTED, FileImportClassifier.classify("outlook.msg", "application/vnd.ms-outlook"))
        assertEquals(FileImportKind.UNSUPPORTED, FileImportClassifier.classify("contract.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))
        assertEquals(FileImportKind.UNSUPPORTED, FileImportClassifier.classify("archive.zip", "application/zip"))
        assertEquals(FileImportKind.UNSUPPORTED, FileImportClassifier.classify("payload.bin", null))
    }
}
