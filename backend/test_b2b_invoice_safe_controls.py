import json
from pathlib import Path

import pytest

from services.b2b_invoice_signals import evaluate_b2b_invoice_signals


CONTROLS_PATH = Path(__file__).resolve().parent / "data" / "b2b_invoice_safe_controls_ro.jsonl"


@pytest.fixture(scope="module")
def safe_controls():
    items = []
    with open(CONTROLS_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def test_safe_controls_count_and_categories(safe_controls):
    assert len(safe_controls) >= 40
    categories = {item["category"] for item in safe_controls}
    expected = {
        "factura_normala_furnizor_cunoscut",
        "e_factura_xml_dovada_valida",
        "mesaj_educational_bancar",
        "reminder_plata_legitim",
        "domeniu_hosting_renewal_legitim",
        "factura_saas_legitima",
        "curier_legitim_fara_card",
        "mesaj_intern_contabil",
    }
    assert expected <= categories


def test_safe_controls_have_required_fields(safe_controls):
    required = {
        "id",
        "category",
        "input_text",
        "expected_final_verdict",
        "must_not_detect_as_fraud",
        "negative_expressions",
        "reason",
    }
    for item in safe_controls:
        assert required <= set(item.keys())
        assert item["expected_final_verdict"] in {"SAFE", "UNVERIFIED"}
        assert isinstance(item["input_text"], str) and item["input_text"].strip()
        assert isinstance(item["must_not_detect_as_fraud"], list)
        assert isinstance(item["negative_expressions"], list)


def test_safe_controls_do_not_request_sensitive_data(safe_controls):
    """Safe B2B messages must never contain hard sensitive requests (card, CVV, OTP, PIN, password)."""
    for item in safe_controls:
        result = evaluate_b2b_invoice_signals(item["input_text"])
        assert "SENSITIVE_DATA_REQUESTED" not in result.flags, (
            f"{item['id']} flagged as requesting sensitive data: {result.flags}"
        )
