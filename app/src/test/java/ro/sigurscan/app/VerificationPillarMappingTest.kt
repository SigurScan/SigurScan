package ro.sigurscan.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class VerificationPillarMappingTest {
    @Test
    fun everyBackendPillarIsPreservedForDisplay() {
        val raw = linkedMapOf(
            "final_url" to OrchestratedPillarState("ok", true, "resolved", "final-ref"),
            "google_web_risk" to OrchestratedPillarState("ok", true, "clean", null),
            "asf_investor_alerts" to OrchestratedPillarState("not_required", false, null, null),
            "phishing_database" to OrchestratedPillarState("ok", true, "not listed", null),
            "phishtank_online_valid" to OrchestratedPillarState("timeout", false, "timed out", null),
            "openphish" to OrchestratedPillarState("rate_limited", false, "quota", null),
            "urlscan" to OrchestratedPillarState("pending", false, "preview pending", "scan-ref"),
            "claim_verifier" to OrchestratedPillarState("error", false, "unavailable", null),
            "semantic_review" to OrchestratedPillarState("ok", true, "done", null)
        )

        val pillars = verificationPillarsFromOrchestrated(raw)

        assertEquals(raw.keys.sorted(), pillars.map { it.id })
        assertEquals(VerificationPillarStatus.TIMEOUT, pillars.first { it.id == "phishtank_online_valid" }.status)
        assertEquals(VerificationPillarStatus.RATE_LIMITED, pillars.first { it.id == "openphish" }.status)
        assertEquals("scan-ref", pillars.first { it.id == "urlscan" }.reference)
        assertTrue(pillars.first { it.id == "semantic_review" }.required)
    }
}
