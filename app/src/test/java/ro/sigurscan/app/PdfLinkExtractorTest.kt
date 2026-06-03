package ro.sigurscan.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class PdfLinkExtractorTest {

    @Test
    fun testExtractPdfHexAnnotationLink() {
        val hexLink = "68747470733a2f2f6578616d706c652e636f6d2f7061796c6f6164"
        val pdfContent = """
            %PDF-1.7
            1 0 obj
            << /Type /Annot /Subtype /Link /A << /S /URI /URI <$hexLink> >>
            endobj
        """.trimIndent().toByteArray(Charsets.ISO_8859_1)

        val extracted = PdfLinkExtractor.extractPdfAnnotationLinks(pdfContent)

        assertTrue(extracted.contains("https://example.com/payload"))
    }

    @Test
    fun testExtractPdfLiteralAnnotationLink() {
        val pdfContent = """
            %PDF-1.7
            1 0 obj
            << /Type /Annot /Subtype /Link /A << /S /URI /URI (https://example.org/login) >>
            endobj
        """.trimIndent().toByteArray(Charsets.ISO_8859_1)

        val extracted = PdfLinkExtractor.extractPdfAnnotationLinks(pdfContent)

        assertEquals(setOf("https://example.org/login"), extracted)
    }

    @Test
    fun testDecodePdfLiteralString() {
        val decoded = PdfLinkExtractor.decodePdfLiteralString("http\\072\\057\\057example.net\\057verify")
        assertEquals("http://example.net/verify", decoded)
    }

    @Test
    fun testDecodePdfLinkCandidatePercentEncoded() {
        val decoded = PdfLinkExtractor.decodePdfLinkCandidate("(https%3A%2F%2Fexample.net%2Freset%2Ftoken)")
            .firstOrNull { it.contains("https://example.net/reset/token") }

        assertEquals("https://example.net/reset/token", decoded)
    }
}
