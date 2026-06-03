package ro.sigurscan.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ScamKnowledgeLayerTest {
    @Test
    fun fanCourierLockerWithWhatsappCodeAndCardEmitsCorpusBrandWarningAndCourierScenario() {
        val signals = ScamKnowledgeLayer.evaluate(
            ScamKnowledgeInput(
                rawText = "FAN Courier: coletul tau este asociat cu acest numar. Alege lockerul si introdu codul WhatsApp, numarul cardului si CVV.",
                claimedBrandIds = setOf("fanCourier"),
                targetHost = "fan-locker.example.test",
                targetIsOfficial = false,
                targetIsApprovedTracker = false,
                sensitiveCodes = setOf(EvidenceCode.CARD_REQUEST, EvidenceCode.CVV_REQUEST, EvidenceCode.OTP_REQUEST),
                hasTarget = true
            )
        )

        assertSignal(signals, EvidenceSource.CORPUS, EvidenceCode.CORPUS_BRAND_WARNING, "fanCourier")
        assertSignal(signals, EvidenceSource.ROMANIA_SCENARIO, EvidenceCode.COURIER_UNOFFICIAL_DOMAIN, "fanCourier")
        assertSignal(signals, EvidenceSource.ROMANIA_SCENARIO, EvidenceCode.PARCEL_TAX, "fanCourier")
        assertTrue(signals.any { it.attrs["neverAskFor"]?.contains("CARD_DATA") == true })
        assertTrue(signals.any { it.attrs["scenario"] == "fan_courier_whatsapp_takeover" })
    }

    @Test
    fun voteazaPeAdelineEmitsWhatsappTakeoverCorpusSignals() {
        val signals = ScamKnowledgeLayer.evaluate(
            ScamKnowledgeInput(
                rawText = "Voteaza pe Adeline in acest sondaj, are nevoie de voturi. Intra pe link si confirma cu codul primit pe WhatsApp.",
                claimedBrandIds = setOf("whatsapp"),
                sensitiveCodes = setOf(EvidenceCode.OTP_REQUEST)
            )
        )

        assertSignal(signals, EvidenceSource.ROMANIA_SCENARIO, EvidenceCode.WHATSAPP_CODE_REQUEST, "whatsapp")
        assertSignal(signals, EvidenceSource.CORPUS, EvidenceCode.CORPUS_SIMILARITY, "whatsapp")
        assertTrue(signals.any { it.attrs["scenario"] == "whatsapp_voteaza_pe_adeline" })
    }

    @Test
    fun bnrSafeAccountAndFraudulentCreditEmitsOfficialPhoneScenario() {
        val signals = ScamKnowledgeLayer.evaluate(
            ScamKnowledgeInput(
                rawText = "Sunt de la politie. A fost accesat un credit fraudulos pe numele tau. BNR recomanda sa transferi banii intr-un cont sigur.",
                claimedBrandIds = setOf("cardAndBanks"),
                sensitiveCodes = setOf(EvidenceCode.PERSONAL_DATA_REQUEST)
            )
        )

        assertSignal(signals, EvidenceSource.ROMANIA_SCENARIO, EvidenceCode.BNR_SAFE_ACCOUNT, "cardAndBanks")
        assertSignal(signals, EvidenceSource.ROMANIA_SCENARIO, EvidenceCode.FRAUDULENT_CREDIT_AUTHORITY_CHAIN, "cardAndBanks")
    }

    @Test
    fun marketplaceReceiveMoneyWithCardEmitsMarketplaceEscrowScenario() {
        val signals = ScamKnowledgeLayer.evaluate(
            ScamKnowledgeInput(
                rawText = "OLX: ca sa primesti banii pentru produs, introdu cardul si codul SMS primit.",
                claimedBrandIds = setOf("marketplace"),
                sensitiveCodes = setOf(EvidenceCode.CARD_REQUEST, EvidenceCode.OTP_REQUEST)
            )
        )

        assertSignal(signals, EvidenceSource.ROMANIA_SCENARIO, EvidenceCode.MARKETPLACE_RECEIVE_MONEY, "marketplace")
        assertSignal(signals, EvidenceSource.CORPUS, EvidenceCode.CORPUS_BRAND_WARNING, "marketplace")
    }

    private fun assertSignal(
        signals: List<ScamKnowledgeSignal>,
        source: EvidenceSource,
        code: EvidenceCode,
        brandId: String
    ) {
        assertTrue(
            "Missing $source/$code/$brandId in $signals",
            signals.any { it.source == source && it.code == code && it.brandId == brandId }
        )
    }
}
