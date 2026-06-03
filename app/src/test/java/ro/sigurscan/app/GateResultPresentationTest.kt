package ro.sigurscan.app

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class GateResultPresentationTest {

    @Test
    fun everyGateActionHasPlainLanguageCopyAndRecommendedActions() {
        GateAction.entries.forEach { action ->
            val result = gateResult(action)

            assertTrue(result.userLabel.isNotBlank())
            assertTrue(GateResultPresentation.supportText(result).isNotBlank())
            assertTrue(GateResultPresentation.primaryAction(result).isNotBlank())
            assertTrue(GateResultPresentation.reasonText(result, null).isNotBlank())
            assertTrue(GateResultPresentation.recommendedActions(result).size >= 2)
        }
    }

    @Test
    fun continueWithCautionDoesNotClaimTheLinkIsSafeOrCertain() {
        val result = gateResult(GateAction.CONTINUE_WITH_CAUTION)
        val copy = listOf(
            result.userLabel,
            GateResultPresentation.supportText(result),
            GateResultPresentation.primaryAction(result)
        )
            .plus(GateResultPresentation.recommendedActions(result))
            .joinToString(" ")
            .lowercase()

        assertFalse(copy.contains("100%"))
        assertFalse(copy.contains("sigur"))
        assertFalse(copy.contains("safe"))
        assertTrue(copy.contains("prudenta") || copy.contains("prudență"))
    }

    @Test
    fun insufficientEvidenceCopyDoesNotSoundLikeAThreatVerdict() {
        val result = gateResult(GateAction.INSUFFICIENT_EVIDENCE, unknownReason = "PROVIDERS_UNAVAILABLE")
        val copy = listOf(
            result.userLabel,
            GateResultPresentation.supportText(result),
            GateResultPresentation.reasonText(result, null),
            GateResultPresentation.primaryAction(result)
        )
            .plus(GateResultPresentation.recommendedActions(result))
            .joinToString(" ")
            .lowercase()

        assertTrue(copy.contains("verifica") || copy.contains("verifică"))
        assertTrue(copy.contains("oficial"))
        assertFalse(copy.contains("phishing confirmat"))
        assertFalse(copy.contains("malware confirmat"))
        assertFalse(copy.contains("nu continua"))
    }

    @Test
    fun dangerousCopyTellsTheUserWhatToDoWithoutTechnicalRawDetails() {
        val result = gateResult(
            GateAction.DO_NOT_CONTINUE,
            reasonCodes = listOf("SANDBOX_VERDICT")
        )
        val copy = listOf(
            result.userLabel,
            GateResultPresentation.reasonText(result, null),
            GateResultPresentation.primaryAction(result)
        )
            .plus(GateResultPresentation.recommendedActions(result))
            .joinToString(" ")
            .lowercase()

        assertTrue(copy.contains("nu"))
        assertTrue(copy.contains("apasa") || copy.contains("continua"))
        assertFalse(copy.contains("json"))
        assertFalse(copy.contains("http 200"))
        assertFalse(copy.contains("asn"))
    }

    private fun gateResult(
        action: GateAction,
        reasonCodes: List<String> = listOf("UNIT_TEST_REASON"),
        unknownReason: String? = null
    ): GateResult {
        return GateResult(
            action = action,
            finality = GateFinality.FINAL,
            reasonCodes = reasonCodes,
            decisiveSignalIds = listOf("sig-test"),
            unknownReason = unknownReason
        )
    }
}
