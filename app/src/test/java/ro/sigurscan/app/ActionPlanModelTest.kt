package ro.sigurscan.app

import com.google.gson.Gson
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Test

class ActionPlanModelTest {
    @Test
    fun scanResponseParsesBackendActionPlan() {
        val json = """
            {
              "scan_id": "orch_test",
              "risk_score": 80,
              "risk_level": "high",
              "user_risk_label": "DANGEROUS",
              "detected_family": "Scam bancar",
              "reasons": ["cere card"],
              "safe_actions": ["Nu introduce date"],
              "action_plan": {
                "label": "Plan de acțiune",
                "verdict": "DANGEROUS",
                "family": "CONV_BANK_SAFE_ACCOUNT",
                "impacts": ["shared_card"],
                "steps": [
                  {
                    "order": 1,
                    "urgency": "now",
                    "title": "Blochează cardul acum",
                    "detail": "Sună banca pe numărul de pe card.",
                    "channel": "Banca + Biroul de Credit",
                    "legal_card_id": "law-instrumente-plata-311"
                  }
                ],
                "report_package": {
                  "channels": [
                    {
                      "name": "DNSC",
                      "contact": "1911",
                      "for": "incidente cyber",
                      "prefilled_subject": "Raportare tentativă de fraudă online"
                    }
                  ]
                },
                "disclaimer": "Plan orientativ de remediere, nu sfat juridic personalizat."
              }
            }
        """.trimIndent()

        val response = Gson().fromJson(json, ScanResponse::class.java)

        assertNotNull(response.actionPlan)
        assertEquals("Plan de acțiune", response.actionPlan?.label)
        assertEquals("now", response.actionPlan?.steps?.firstOrNull()?.urgency)
        assertEquals("Blochează cardul acum", response.actionPlan?.steps?.firstOrNull()?.title)
        assertEquals("DNSC", response.actionPlan?.reportPackage?.channels?.firstOrNull()?.name)
        assertEquals("incidente cyber", response.actionPlan?.reportPackage?.channels?.firstOrNull()?.purpose)
    }
}
