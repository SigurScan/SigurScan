import pytest

from services.b2b_invoice_signals import evaluate_b2b_invoice_signals
from services.cross_scan_knowledge import evaluate_cross_scan_knowledge
from services.invoice_orchestrator import evaluate_invoice_verdict, scan_invoice


@pytest.fixture(autouse=True)
def _clean_state(monkeypatch):
    monkeypatch.setenv("INVOICE_CACHE_HMAC_KEY", "testkey")
    from services import invoice_orchestrator as io
    from services import vendor_memory

    io._verdict_cache.clear()
    io._cui_cache.clear()
    vendor_memory._memory.clear()
    yield
    io._verdict_cache.clear()
    vendor_memory._memory.clear()


def test_b2b_signal_detector_finds_reply_to_mismatch_and_bec_combo():
    result = evaluate_b2b_invoice_signals(
        "From: facturi@furnizor-real.ro\n"
        "Reply-To: plata-furnizor@gmail.com\n"
        "Factura TEST SRL CUI RO12345678. Contul nou este RO33RNCB1234567890123456."
    )

    assert "REPLY_TO_MISMATCH" in result.flags
    assert "BEC_REPLY_TO_ACCOUNT_CHANGE" in result.flags
    assert result.metadata["from_domain"] == "furnizor-real.ro"
    assert result.metadata["reply_to_domain"] == "gmail.com"


@pytest.mark.asyncio
async def test_reply_to_mismatch_plus_new_bank_account_is_dangerous():
    result = await scan_invoice(
        "From: facturi@furnizor-real.ro\n"
        "Reply-To: plata-furnizor@gmail.com\n"
        "Furnizor: TEST SRL\nCUI RO12345678\n"
        "Am schimbat contul bancar. Noul IBAN este RO33RNCB1234567890123456.\n"
        "Total 4800 RON"
    )
    verdict = evaluate_invoice_verdict(result, result.raw_text, source_channel="email")

    assert {"REPLY_TO_MISMATCH", "BEC_REPLY_TO_ACCOUNT_CHANGE", "ACCOUNT_CHANGE_LANGUAGE"} <= set(result.fraud_flags)
    assert verdict["gate"]["label"] == "DANGEROUS"


@pytest.mark.asyncio
async def test_ceo_confidential_payment_instruction_is_dangerous():
    result = await scan_invoice(
        "Directorul cere confidențialitate, nu suna și nu discuta cu nimeni. "
        "Plătește urgent în IBAN RO33RNCB1234567890123456 suma 12500 RON."
    )
    verdict = evaluate_invoice_verdict(result, result.raw_text, source_channel="email")

    assert "CEO_CONFIDENTIAL_PAYMENT" in result.fraud_flags
    assert verdict["gate"]["label"] == "DANGEROUS"


@pytest.mark.asyncio
async def test_unknown_payment_link_with_card_request_is_dangerous():
    result = await scan_invoice(
        "Factura restantă TEST SRL. Plătește aici https://pay-factura-secure.example/checkout "
        "și reconfirmă datele cardului, CVV și codul OTP."
    )
    verdict = evaluate_invoice_verdict(result, result.raw_text, source_channel="email")

    assert "PAYMENT_LINK_UNKNOWN_PSP" in result.fraud_flags
    assert "SENSITIVE_DATA_REQUESTED" in result.fraud_flags
    assert verdict["gate"]["label"] == "DANGEROUS"


@pytest.mark.asyncio
async def test_efactura_claim_without_xml_proof_blocks_safe_but_not_hard_dangerous():
    result = await scan_invoice(
        "Furnizor: TEST SRL CUI RO12345678\n"
        "Factura este în e-Factura/SPV. Plătiți IBAN RO33RNCB1234567890123456.\n"
        "Total 100 RON"
    )
    verdict = evaluate_invoice_verdict(result, result.raw_text, source_channel="android_native")

    assert "EFACTURA_CLAIM_WITHOUT_DOCUMENT" in result.fraud_flags
    assert verdict["gate"]["label"] in {"SUSPECT", "UNVERIFIED"}


def test_cross_scan_exports_b2b_invoice_signals_for_non_invoice_text():
    result = evaluate_cross_scan_knowledge(
        text=(
            "From: contabilitate@firma-real.ro\n"
            "Reply-To: plata-firma@gmail.com\n"
            "Contul nou pentru factura este RO33RNCB1234567890123456."
        ),
        claimed_brand=None,
        cui="12345678",
        source_channel="email",
    )

    assert "REPLY_TO_MISMATCH" in result["fraud_flags"]
    assert "BEC_REPLY_TO_ACCOUNT_CHANGE" in result["b2b_invoice_signals"]["flags"]
