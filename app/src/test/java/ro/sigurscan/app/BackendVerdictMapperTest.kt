package ro.sigurscan.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.util.Locale

class BackendVerdictMapperTest {

    @Test
    fun finalBackendLabelsRemainAuthoritativeOnAndroid() {
        assertEquals(
            GateAction.CONTINUE_WITH_CAUTION,
            backendGateResult(scanResponse(label = "SAFE", riskLevel = "low")).action
        )
        assertEquals(
            GateAction.VERIFY_OFFICIAL,
            backendGateResult(scanResponse(label = "SUSPECT", riskLevel = "medium")).action
        )
        assertEquals(
            GateAction.DO_NOT_CONTINUE,
            backendGateResult(scanResponse(label = "DANGEROUS", riskLevel = "high")).action
        )
    }

    @Test
    fun backendLabelsAreLocaleIndependent() {
        val previous = Locale.getDefault()
        Locale.setDefault(Locale.forLanguageTag("tr-TR"))
        try {
            val result = backendGateResult(scanResponse(label = "safe", riskLevel = "low"))

            assertEquals(GateAction.CONTINUE_WITH_CAUTION, result.action)
            assertEquals(GateFinality.FINAL, result.finality)
        } finally {
            Locale.setDefault(previous)
        }
    }

    @Test
    fun nonFinalBackendResultNeverShowsAProvisionalVerdict() {
        val result = backendGateResult(
            scanResponse(label = "SAFE", riskLevel = "low", isFinal = false)
        )

        assertEquals(GateAction.INSUFFICIENT_EVIDENCE, result.action)
        assertEquals(GateFinality.PROVISIONAL, result.finality)
        assertTrue(result.asyncExpected)
    }

    @Test
    fun orchestratedResponseWithoutBackendResultStaysProvisional() {
        val result = backendGateResult(
            OrchestratedScanResponse(
                scanId = "orch-pending",
                status = "scanning",
                result = null
            )
        )

        assertEquals(GateAction.INSUFFICIENT_EVIDENCE, result.action)
        assertEquals(GateFinality.PROVISIONAL, result.finality)
        assertTrue(result.asyncExpected)
        assertEquals("BACKEND_SCAN_IN_PROGRESS", result.unknownReason)
    }

    @Test
    fun orchestratedResponseWithFinalBackendResultUsesBackendLabel() {
        val result = backendGateResult(
            OrchestratedScanResponse(
                scanId = "orch-final",
                status = "complete",
                result = scanResponse(label = "DANGEROUS", riskLevel = "high", isFinal = true)
            )
        )

        assertEquals(GateAction.DO_NOT_CONTINUE, result.action)
        assertEquals(GateFinality.FINAL, result.finality)
    }

    @Test
    fun finalUnverifiedBackendResultIsRecognizedAsFinalLimitedVerification() {
        val result = backendGateResult(
            scanResponse(label = "UNVERIFIED", riskLevel = "info", isFinal = true)
        )

        assertEquals(GateAction.UNVERIFIED, result.action)
        assertEquals(GateFinality.FINAL, result.finality)
        assertEquals("BACKEND_UNVERIFIED", result.unknownReason)
        assertTrue(result.reasonCodes.contains("BACKEND_UNVERIFIED"))
    }

    @Test
    fun exactBackendGateReasonsArePreservedVerbatim() {
        val result = backendGateResult(
            scanResponse(
                label = "DANGEROUS",
                riskLevel = "high",
                evidence = mapOf(
                    "verdict_gate" to mapOf(
                        "label" to "DANGEROUS",
                        "reason_codes" to listOf(
                            "provider_malicious",
                            "incomplete_evidence_fraud_floor_preserved"
                        ),
                        "is_final" to true
                    )
                )
            )
        )

        assertEquals(
            listOf("provider_malicious", "incomplete_evidence_fraud_floor_preserved"),
            result.reasonCodes
        )
        assertTrue("Generic Android reasons must not replace backend provenance.",
            "BACKEND_ORCHESTRATED_VERDICT" !in result.reasonCodes)
    }

    @Test
    fun evidenceGateLabelIsUsedWhenLegacyTopLevelLabelIsMissing() {
        val result = backendGateResult(
            scanResponse(
                label = null,
                riskLevel = "high",
                evidence = mapOf(
                    "verdict_gate" to mapOf(
                        "label" to "DANGEROUS",
                        "reason_codes" to listOf("sensitive_wrong_channel")
                    )
                )
            )
        )

        assertEquals(GateAction.DO_NOT_CONTINUE, result.action)
        assertEquals(listOf("sensitive_wrong_channel"), result.reasonCodes)
    }

    @Test
    fun missingFinalBackendLabelDoesNotTriggerAnotherLocalJudge() {
        val result = backendGateResult(
            scanResponse(label = null, riskLevel = "low", isFinal = true)
        )

        assertEquals(GateAction.INSUFFICIENT_EVIDENCE, result.action)
        assertEquals(GateFinality.FINAL, result.finality)
        assertEquals("BACKEND_FINAL_LABEL_MISSING", result.unknownReason)
    }

    private fun scanResponse(
        label: String?,
        riskLevel: String,
        isFinal: Boolean = true,
        evidence: Map<String, Any>? = null
    ) = ScanResponse(
        scanId = "backend-verdict",
        riskScore = 10,
        riskLevel = riskLevel,
        isFinal = isFinal,
        userRiskLabel = label,
        evidence = evidence
    )
}
