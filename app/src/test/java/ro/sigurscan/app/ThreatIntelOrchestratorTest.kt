package ro.sigurscan.app

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ThreatIntelOrchestratorTest {

    private fun lowRiskAssessment() = OfflineAssessment(
        family = "Analiză Link Extern",
        riskScore = 25,
        riskLevel = "low",
        reasons = listOf("Nu au fost detectate semnale evidente de risc."),
        safeActions = listOf("Poți continua."),
        keyDangers = emptyList()
    )

    @Test
    fun virusTotalIsSkippedForLowRiskWhenWebRiskIsClean() {
        val shouldRun = ThreatIntelOrchestrator.shouldRunVirusTotal(
            riskLevel = "low",
            existingThreatIntel = emptyList(),
            webRisk = ThreatIntelSourceResult(
                source = "Google Web Risk",
                verdict = "No Threats",
                severity = "low"
            )
        )

        assertFalse(shouldRun)
    }

    @Test
    fun virusTotalRunsWhenLocalRiskIsHighEvenIfWebRiskIsClean() {
        val shouldRun = ThreatIntelOrchestrator.shouldRunVirusTotal(
            riskLevel = "high",
            existingThreatIntel = emptyList(),
            webRisk = ThreatIntelSourceResult(
                source = "Google Web Risk",
                verdict = "No Threats",
                severity = "low"
            )
        )

        assertTrue(shouldRun)
    }

    @Test
    fun virusTotalRunsWhenExistingEvidenceIsUnclearOrSuspicious() {
        val shouldRun = ThreatIntelOrchestrator.shouldRunVirusTotal(
            riskLevel = "low",
            existingThreatIntel = listOf(
                ThreatIntelSourceResult(
                    source = "urlscan.io",
                    verdict = "Suspicious score 1",
                    severity = "medium"
                )
            ),
            webRisk = ThreatIntelSourceResult(
                source = "Google Web Risk",
                verdict = "No Threats",
                severity = "low"
            )
        )

        assertTrue(shouldRun)
    }

    @Test
    fun virusTotalIsSkippedWhenWebRiskAlreadyConfirmsThreat() {
        val shouldRun = ThreatIntelOrchestrator.shouldRunVirusTotal(
            riskLevel = "high",
            existingThreatIntel = emptyList(),
            webRisk = ThreatIntelSourceResult(
                source = "Google Web Risk",
                verdict = "Threats Detected",
                severity = "high"
            )
        )

        assertFalse(shouldRun)
    }

    @Test
    fun urlscanSubmissionBodyUsesPrivateVisibilityAndSanitizedUrl() {
        val body = ThreatIntelOrchestrator.buildUrlscanSubmissionBody(
            "https://example.com/path?utm_source=newsletter&email=client@example.com&a=1&token=secret&reset=abc&uid=42&bid=campaign&pcid=promo&u_action_id=click"
        )

        assertTrue(body.contains("\"visibility\":\"private\""))
        assertTrue(body.contains("\"url\":\"https://example.com/path?a=1\""))
        assertFalse(body.contains("client@example.com"))
        assertFalse(body.contains("utm_source"))
        assertFalse(body.contains("token=secret"))
        assertFalse(body.contains("reset=abc"))
        assertFalse(body.contains("uid=42"))
        assertFalse(body.contains("bid=campaign"))
        assertFalse(body.contains("pcid=promo"))
        assertFalse(body.contains("u_action_id=click"))
    }

    @Test
    fun urlscanSanitizerDropsUnknownEmailAndLongSessionLikeValues() {
        val body = ThreatIntelOrchestrator.buildUrlscanSubmissionBody(
            "https://invoice.example.com/pay?ref=user@gmail.com&campaign=summer&state=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9abcdef1234567890"
        )

        assertTrue(body.contains("\"visibility\":\"private\""))
        assertTrue(body.contains("\"url\":\"https://invoice.example.com/pay?campaign=summer\""))
        assertFalse(body.contains("user@gmail.com"))
        assertFalse(body.contains("eyJhbGciOiJIUzI1Ni"))
    }

    @Test
    fun urlscanSubmissionBodyAllowsOnlyPrivateOrUnlistedVisibility() {
        val fallbackBody = ThreatIntelOrchestrator.buildUrlscanSubmissionBody(
            "https://example.com/path?email=client@example.com",
            visibility = "unlisted"
        )
        val unsafeBody = ThreatIntelOrchestrator.buildUrlscanSubmissionBody(
            "https://example.com/path?email=client@example.com",
            visibility = "public"
        )

        assertTrue(fallbackBody.contains("\"visibility\":\"unlisted\""))
        assertFalse(fallbackBody.contains("client@example.com"))
        assertTrue(unsafeBody.contains("\"visibility\":\"private\""))
        assertFalse(unsafeBody.contains("\"visibility\":\"public\""))
    }

    @Test
    fun urlscanSubmissionBodyCanIncludeRomaniaMobilePersona() {
        val body = ThreatIntelOrchestrator.buildUrlscanSubmissionBody(
            url = "https://buyback.yoxo.ro/",
            visibility = "private",
            country = "ro",
            customAgent = "Mozilla/5.0 (Linux; Android 15) Chrome/120 Mobile Safari/537.36"
        )

        assertTrue(body.contains("\"country\":\"ro\""))
        assertTrue(body.contains("\"customagent\":\"Mozilla/5.0 (Linux; Android 15) Chrome/120 Mobile Safari/537.36\""))
    }

    @Test
    fun confirmedWebRiskThreatEscalatesVisibleVerdict() {
        val result = ThreatIntelOrchestrator.applyThreatIntelEvidence(
            current = lowRiskAssessment(),
            threatIntel = listOf(
                ThreatIntelSourceResult(
                    source = "Google Web Risk",
                    verdict = "Threats Detected",
                    severity = "high",
                    details = "Tipuri: SOCIAL_ENGINEERING."
                )
            )
        )

        assertTrue(result.riskScore >= 90)
        assertTrue(result.riskLevel == "high" || result.riskLevel == "critical")
        assertTrue(result.safeActions.any { it.contains("Nu apăsa", ignoreCase = true) })
    }
}
