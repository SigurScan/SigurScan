package ro.sigurscan.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Test

class ResultMappingTest {
    @Test
    fun finalUnverifiedAssessmentNeverFallsThroughToSafeCopy() {
        val assessment = assessment(riskLevel = "unknown")
        val riskUi = mapRiskDisplayState(assessment)

        val decision = mapUserActionDecision(assessment, riskUi)

        assertEquals("Neverificat", riskUi.level)
        assertEquals("Neverificat", decision.headline)
        assertNotEquals("Poți continua.", decision.nextBestAction)
    }

    @Test
    fun onlyExplicitSafeRiskLevelGetsSafeCopy() {
        val assessment = assessment(riskLevel = "safe")
        val riskUi = mapRiskDisplayState(assessment)

        val decision = mapUserActionDecision(assessment, riskUi)

        assertEquals("Sigur", decision.headline)
        assertEquals("Poți continua.", decision.nextBestAction)
    }

    private fun assessment(riskLevel: String) = OfflineAssessment(
        family = "Audio",
        riskScore = 0,
        riskLevel = riskLevel,
        reasons = emptyList(),
        safeActions = emptyList(),
        keyDangers = emptyList()
    )
}
