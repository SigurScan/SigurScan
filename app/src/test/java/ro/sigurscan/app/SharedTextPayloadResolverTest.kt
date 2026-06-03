package ro.sigurscan.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class SharedTextPayloadResolverTest {

    @Test
    fun resolvesHtmlBeforePlainTextWhenBothAreAvailable() {
        val resolved = SharedTextPayloadResolver.resolve(
            listOf(
                SharedTextCandidate(
                    text = "Apasa aici",
                    kind = SharedTextCandidateKind.PLAIN_TEXT,
                    sourceLabel = "Conținut text partajat"
                ),
                SharedTextCandidate(
                    text = """<a href="https://hidden.example.net/pay">Apasa aici</a>""",
                    kind = SharedTextCandidateKind.HTML,
                    sourceLabel = "Conținut HTML partajat"
                )
            )
        )

        assertEquals(SharedContentFidelity.FULL_HTML, resolved?.fidelity)
        assertTrue(resolved?.preserveHtml == true)
        assertEquals("""<a href="https://hidden.example.net/pay">Apasa aici</a>""", resolved?.text)
    }

    @Test
    fun resolvesClipDataHtmlAsFullHtml() {
        val resolved = SharedTextPayloadResolver.resolve(
            listOf(
                SharedTextCandidate(
                    text = """<button data-link="https://clip.example.net/claim">Premiu</button>""",
                    kind = SharedTextCandidateKind.HTML,
                    sourceLabel = "Conținut HTML din ClipData"
                )
            )
        )

        assertEquals("Conținut HTML din ClipData", resolved?.sourceLabel)
        assertEquals(SharedContentFidelity.FULL_HTML, resolved?.fidelity)
        assertTrue(resolved?.preserveHtml == true)
    }

    @Test
    fun resolvesPlainTextAsVisibleTextOnly() {
        val resolved = SharedTextPayloadResolver.resolve(
            listOf(
                SharedTextCandidate(
                    text = "OLX: plata este blocata. Apasa aici.",
                    kind = SharedTextCandidateKind.PLAIN_TEXT,
                    sourceLabel = "Conținut text partajat"
                )
            )
        )

        assertEquals(SharedContentFidelity.PLAIN_TEXT_ONLY, resolved?.fidelity)
        assertFalse(resolved?.preserveHtml == true)
    }
}
