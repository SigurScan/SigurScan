package ro.sigurscan.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class MailEvidenceGateTest {

    private fun lowRiskAssessment() = OfflineAssessment(
        family = "Analiză Link Extern",
        riskScore = 25,
        riskLevel = "low",
        reasons = listOf("Nu au fost detectate semnale evidente de risc."),
        safeActions = listOf("Verifică expeditorul dacă nu îl recunoști."),
        keyDangers = emptyList()
    )

    @Test
    fun uberTrackingButtonWithOfficialFallbackDoesNotBecomeHiddenLinkScam() {
        val rawHtml = """
            <html>
              <body>
                <p>Te așteptăm cu drag înapoi. Economisește 50% la următoarele două curse.</p>
                <a href="https://rides.sng.link/Aw5zn/hw3r?_dl=uber%3A%2F%2F&amp;_fallback_redirect=https%3A%2F%2Fwww.uber.com&amp;partner=crm">
                  Comandă o cursă
                </a>
              </body>
            </html>
        """.trimIndent()
        val assembledInput = MailShareInputAssembler.buildMailScanInput(
            rawText = rawHtml,
            links = HtmlLinkExtractor.extractHtmlLinks(rawHtml),
            sourceLabel = "Conținut HTML partajat"
        )

        val result = MailEvidenceGate.apply(lowRiskAssessment(), assembledInput)

        assertEquals("low", result.riskLevel)
        assertEquals(25, result.riskScore)
        assertFalse(result.family.contains("Mail cu link ascuns"))
        assertTrue(assembledInput.contains("https://www.uber.com"))
    }

    @Test
    fun hiddenButtonToSensitiveUntrustedDomainCanRaiseSuspicious() {
        val rawHtml = """
            <html>
              <body>
                <p>Uber: confirmă oferta pentru cursa ta.</p>
                <a href="https://uber-promo-login.example.net/card/verify">Comandă o cursă</a>
              </body>
            </html>
        """.trimIndent()
        val assembledInput = MailShareInputAssembler.buildMailScanInput(
            rawText = rawHtml,
            links = HtmlLinkExtractor.extractHtmlLinks(rawHtml),
            sourceLabel = "Conținut HTML partajat"
        )

        val result = MailEvidenceGate.apply(lowRiskAssessment(), assembledInput)

        assertEquals("medium", result.riskLevel)
        assertTrue(result.riskScore >= 55)
        assertEquals("Mail cu link ascuns", result.family)
        assertTrue(result.reasons.any { it.contains("domeniu neoficial", ignoreCase = true) })
    }

    @Test
    fun marketingLanguageAloneDoesNotEscalateMailRisk() {
        val rawHtml = """
            <html>
              <body>
                <p>Promoție azi doar. Nu rata oferta limitată.</p>
                <a href="https://www.uber.com/ro/ride/">Vezi oferta</a>
              </body>
            </html>
        """.trimIndent()
        val assembledInput = MailShareInputAssembler.buildMailScanInput(
            rawText = rawHtml,
            links = HtmlLinkExtractor.extractHtmlLinks(rawHtml),
            sourceLabel = "Conținut HTML partajat"
        )

        val result = MailEvidenceGate.apply(lowRiskAssessment(), assembledInput)

        assertEquals("low", result.riskLevel)
        assertEquals(25, result.riskScore)
        assertFalse(result.family.contains("Mail cu link ascuns"))
    }
}
