package ro.sigurscan.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class OfflineRiskPolicyTest {

    private fun highRiskTextAssessment(family: String = "eMAG fals / Premiu fals") = OfflineAssessment(
        family = family,
        riskScore = 95,
        riskLevel = "high",
        reasons = listOf("Textul conține ofertă, voucher sau urgență."),
        safeActions = listOf("Nu accesați linkul."),
        keyDangers = listOf("Posibilă campanie frauduloasă.")
    )

    @Test
    fun trustedOfficialMarketingOfflineCannotStayDangerous() {
        val result = OfflineRiskPolicy.applyEvidenceCap(
            current = highRiskTextAssessment(),
            scannedText = "eMAG: Nu rata voucherul de weekend. Vezi oferta: https://www.emag.ro/oferta"
        )

        assertEquals("low", result.riskLevel)
        assertTrue(result.riskScore <= 30)
        assertFalse(result.family.contains("fals", ignoreCase = true))
        assertTrue(result.reasons.any { it.contains("domeniu oficial", ignoreCase = true) })
    }

    @Test
    fun marketingTextOnlyOfflineIsCappedAtVerifyOfficial() {
        val result = OfflineRiskPolicy.applyEvidenceCap(
            current = highRiskTextAssessment(),
            scannedText = "eMAG: Ai câștigat un voucher. Profită acum, oferta expiră azi."
        )

        assertEquals("medium", result.riskLevel)
        assertTrue(result.riskScore <= 60)
        assertFalse(result.family.contains("fals", ignoreCase = true))
        assertTrue(result.safeActions.any { it.contains("canalul oficial", ignoreCase = true) })
    }

    @Test
    fun explicitSensitiveDataOfflineCanRemainHigh() {
        val result = OfflineRiskPolicy.applyEvidenceCap(
            current = highRiskTextAssessment("Furt date card / OTP"),
            scannedText = "Completează cardul, CVV și codul OTP aici: https://secure-pay.example.net"
        )

        assertEquals("high", result.riskLevel)
        assertTrue(result.riskScore >= 70)
    }
}
