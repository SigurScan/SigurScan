import json
from unittest.mock import MagicMock, patch

from services.hunter_io import evaluate_heavy_email_domain_intel


def test_hunter_io_skips_without_heavy_flags(monkeypatch):
    monkeypatch.setenv("HUNTER_IO_API_KEY", "test-hunter-key")
    monkeypatch.setenv("HUNTER_IO_MONTHLY_BUDGET", "50")

    with patch("services.hunter_io.requests.get", side_effect=AssertionError("Hunter must not run")):
        result = evaluate_heavy_email_domain_intel(
            text="From: facturi@furnizor-real.ro\nFactura curată.",
            claimed_vendor="Furnizor Real SRL",
            fraud_flags=[],
        )

    assert result is None


def test_hunter_io_budget_zero_skips_heavy_case(monkeypatch):
    monkeypatch.setenv("HUNTER_IO_API_KEY", "test-hunter-key")
    monkeypatch.setenv("HUNTER_IO_MONTHLY_BUDGET", "0")

    with patch("services.hunter_io.requests.get", side_effect=AssertionError("Hunter budget is exhausted")):
        result = evaluate_heavy_email_domain_intel(
            text=(
                "From: facturi@furnizor-real.ro\n"
                "Reply-To: plata@vendor-payments.example\n"
                "Cont nou pentru plata facturii."
            ),
            claimed_vendor="Furnizor Real SRL",
            fraud_flags=["BEC_REPLY_TO_ACCOUNT_CHANGE"],
        )

    assert result["status"] == "skipped"
    assert result["reason"] == "budget_exhausted"


def test_hunter_io_domain_search_uses_header_budget_and_sanitizes_response(monkeypatch):
    monkeypatch.setenv("HUNTER_IO_API_KEY", "test-hunter-key")
    monkeypatch.setenv("HUNTER_IO_MONTHLY_BUDGET", "50")
    monkeypatch.setattr("services.hunter_io.consume_hunter_io_budget", lambda: True)

    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "data": {
            "domain": "vendor-payments.example",
            "organization": "Vendor Payments LLC",
            "disposable": True,
            "webmail": False,
            "accept_all": False,
            "pattern": "{first}.{last}",
            "emails": [
                {"value": "ana.popescu@vendor-payments.example", "confidence": 88},
                {"value": "ion.ionescu@vendor-payments.example", "confidence": 72},
            ],
        }
    }

    with patch("services.hunter_io.requests.get", return_value=response) as mock_get:
        result = evaluate_heavy_email_domain_intel(
            text=(
                "From: facturi@furnizor-real.ro\n"
                "Reply-To: plata@vendor-payments.example\n"
                "Cont nou pentru plata facturii."
            ),
            claimed_vendor="Furnizor Real SRL",
            fraud_flags=["BEC_REPLY_TO_ACCOUNT_CHANGE"],
        )

    assert result["status"] == "checked"
    assert result["provider"] == "hunter_io"
    assert result["domain"] == "vendor-payments.example"
    assert result["email_count"] == 2
    assert result["max_confidence"] == 88
    assert "HUNTER_DISPOSABLE_EMAIL_DOMAIN" in result["flags"]
    assert "ana.popescu" not in json.dumps(result)
    assert mock_get.call_args.kwargs["headers"]["X-API-KEY"] == "test-hunter-key"
    assert mock_get.call_args.kwargs["params"]["limit"] == 1
