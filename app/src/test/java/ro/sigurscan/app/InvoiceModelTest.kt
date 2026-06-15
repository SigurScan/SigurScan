package ro.sigurscan.app

import com.google.gson.Gson
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

class InvoiceModelTest {
    @Test
    fun invoiceResponseParsesBeneficiaryNameCheckGuidance() {
        val json = """
            {
              "fields": {
                "emitent": "ATELIER DIGITAL SIBIU SRL",
                "cui": "12345678",
                "iban": "RO33RNCB1234567890123456"
              },
              "beneficiary_name_check": {
                "recommended": true,
                "method": "bank_app_beneficiary_name_check",
                "local_service_hint": "SANB/BNDS dacă banca ta îl afișează",
                "title": "Verifică numele beneficiarului în aplicația băncii",
                "reason": "Nu avem o sursă publică suficientă care să confirme proprietarul IBAN-ului.",
                "expected_beneficiary": "ATELIER DIGITAL SIBIU SRL",
                "iban_masked_for_client": "RO33...3456",
                "bank": "BCR",
                "steps": ["Începe o plată nouă.", "Verifică numele beneficiarului."],
                "privacy_note": "SigurScan nu îți cere acces la banca ta, parolă, OTP, PIN sau captură de ecran."
              }
            }
        """.trimIndent()

        val response = Gson().fromJson(json, InvoiceScanResponse::class.java)

        assertNotNull(response.beneficiaryNameCheck)
        assertEquals(true, response.beneficiaryNameCheck?.recommended)
        assertEquals("ATELIER DIGITAL SIBIU SRL", response.beneficiaryNameCheck?.expectedBeneficiary)
        assertEquals("RO33...3456", response.beneficiaryNameCheck?.ibanMaskedForClient)
        assertTrue(response.beneficiaryNameCheck?.privacyNote.orEmpty().contains("OTP"))
    }
}
