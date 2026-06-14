package ro.sigurscan.app

import com.google.gson.Gson
import org.junit.Assert.assertTrue
import org.junit.Test

class ActionPlanRequestTest {
    @Test
    fun actionPlanRequestSerializesBackendImpactContract() {
        val json = Gson().toJson(
            ActionPlanRequest(
                verdict = "DANGEROUS",
                family = "CONV_BANK_SAFE_ACCOUNT",
                impacts = listOf("shared_card", "paid_transfer"),
                targetType = "url",
                targetRedacted = "https://example.test"
            )
        )

        assertTrue(json.contains("\"verdict\":\"DANGEROUS\""))
        assertTrue(json.contains("\"impacts\":[\"shared_card\",\"paid_transfer\"]"))
        assertTrue(json.contains("\"target_type\":\"url\""))
        assertTrue(json.contains("\"target_redacted\":\"https://example.test\""))
    }
}
