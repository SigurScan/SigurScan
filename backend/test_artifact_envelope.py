import asyncio
import json

import pytest

from api_models import OrchestratedScanRequest
from services.artifact_envelope import build_artifact_envelope
from services.orchestrated_scan import orchestrated_engine
from services.threat_enrichment import build_threat_enrichment


def test_artifact_envelope_preserves_provenance_without_raw_qr_or_email_identity():
    envelope = build_artifact_envelope(
        artifact_type="email",
        analysis_input_type="email",
        source_channel="share",
        redacted_text="Confirmă plata pentru [EMAIL_REDACTED].",
        external_urls=[
            "https://pay.example/verify/opaque-secret-token-1234567890",
            "https://pay.example/login?otp=123456&campaign=summer",
        ],
        qr_payloads=["otpauth://totp/Alice?secret=TOPSECRET"],
        hidden_url_visibility=True,
        has_html=True,
        email_auth={
            "auth_strength": "fail",
            "sender_auth_confidence": "low",
            "auth_status": {"spf": "fail", "dkim": "pass", "dmarc": "fail"},
            "from_domain": "private-sender.example",
            "reply_to_domain": "attacker.example",
        },
        extraction_warning="OCR warning contained Alice and TOPSECRET",
    )

    serialized = json.dumps(envelope, ensure_ascii=False)
    assert envelope["schema"] == "sigurscan_artifact_envelope_v1"
    assert envelope["artifact_type"] == "email"
    assert envelope["analysis_input_type"] == "email"
    assert envelope["source_channel"] == "share"
    assert envelope["content"]["has_html"] is True
    assert envelope["urls"]["count"] == 2
    assert envelope["urls"]["items"] == [
        "https://pay.example/",
        "https://pay.example/login?campaign=summer",
    ]
    assert envelope["qr"] == {"count": 1, "url_count": 0, "hidden_url_visibility": True}
    assert envelope["email_auth"] == {
        "present": True,
        "auth_strength": "fail",
        "sender_auth_confidence": "low",
        "spf": "fail",
        "dkim": "pass",
        "dmarc": "fail",
    }
    assert envelope["extraction"] == {"status": "warning", "has_warning": True}
    assert "TOPSECRET" not in serialized
    assert "Alice" not in serialized
    assert "private-sender.example" not in serialized
    assert "attacker.example" not in serialized
    assert "123456" not in serialized


@pytest.mark.parametrize(
    ("artifact_type", "analysis_input_type"),
    [
        ("url", "url"),
        ("offer", "offer"),
        ("invoice", "invoice"),
        ("audio", "text"),
        ("qr", "text"),
    ],
)
def test_artifact_envelope_contract_is_shared_by_all_scan_types(artifact_type, analysis_input_type):
    envelope = build_artifact_envelope(
        artifact_type=artifact_type,
        analysis_input_type=analysis_input_type,
        source_channel="android_native",
        redacted_text="Conținut redactat",
        external_urls=["https://example.com/path"],
    )

    assert envelope["artifact_type"] == artifact_type
    assert envelope["analysis_input_type"] == analysis_input_type
    assert envelope["urls"]["items"] == ["https://example.com/path"]


def test_extracted_image_keeps_image_provenance_while_analysis_remains_text(monkeypatch):
    persisted = []

    with monkeypatch.context() as patched:
        patched.setattr(
            orchestrated_engine,
            "_persist_orchestrated_job",
            lambda candidate: persisted.append(candidate) or candidate,
        )
        patched.setattr(orchestrated_engine, "_emit_orchestrated_telemetry", lambda *args, **kwargs: None)

        response = asyncio.run(
            orchestrated_engine._start_orchestrated_from_extraction(
                {
                    "input_type": "image_ocr",
                    "source_channel": "share_image",
                    "redacted_text": "Scanează codul QR.",
                    "extracted_urls": ["https://example.com/verify?token=secret-value"],
                    "qr_payloads": ["https://example.com/verify?token=secret-value"],
                    "hidden_url_visibility": True,
                    "warning": None,
                },
                fallback_label="imagine",
                default_input_type="image_ocr",
                source_channel="share_image",
            )
        )

    job = persisted[-1]
    assert response["scan_id"] == job["scan_id"]
    assert job["input_type"] == "text"
    assert job["artifact_envelope"]["artifact_type"] == "image_ocr"
    assert job["artifact_envelope"]["analysis_input_type"] == "text"
    assert job["artifact_envelope"]["qr"]["count"] == 1
    assert job["artifact_envelope"]["qr"]["url_count"] == 1
    assert job["artifact_envelope"]["urls"]["items"] == ["https://example.com/verify"]


def test_direct_request_job_gets_artifact_envelope_without_changing_public_status(monkeypatch):
    with monkeypatch.context() as patched:
        patched.setattr(orchestrated_engine, "_persist_orchestrated_job", lambda candidate: candidate)
        patched.setattr(orchestrated_engine, "_emit_orchestrated_telemetry", lambda *args, **kwargs: None)
        job = asyncio.run(
            orchestrated_engine._create_orchestrated_job(
                OrchestratedScanRequest(
                    input_type="offer",
                    text="Oferta este la https://example.com/deal",
                    source_channel="share_text",
                )
            )
        )

    public_status = orchestrated_engine._orchestrated_status_payload(job)
    assert job["artifact_envelope"]["artifact_type"] == "offer"
    assert job["artifact_envelope"]["urls"]["items"] == ["https://example.com/deal"]
    assert "artifact_envelope" not in public_status
    assert public_status["status"] == "scanning"


def test_threat_enrichment_is_monotonic_shadow_evidence():
    envelope = build_artifact_envelope(
        artifact_type="invoice",
        analysis_input_type="invoice",
        source_channel="android_native",
        redacted_text="Factura include un cod QR.",
        external_urls=["https://billing.example/pay"],
    )
    enrichment = build_threat_enrichment(
        artifact_envelope=envelope,
        resolved_urls=[
            {
                "url": "https://billing.example/pay",
                "final_url": "https://billing.example/pay",
                "success": True,
            }
        ],
        provider_summary={
            "google_web_risk": {
                "status": "malicious",
                "verdict": "phishing",
                "consulted": True,
                "malicious_hit_count": 1,
            },
            "urlhaus": {
                "status": "error",
                "verdict": "error",
                "consulted": False,
            },
        },
    )

    assert enrichment["schema"] == "sigurscan_threat_enrichment_v1"
    assert enrichment["artifact_type"] == "invoice"
    assert enrichment["status"] == "partial"
    assert enrichment["provider_verdict"] == "malicious"
    assert enrichment["has_positive_threat_evidence"] is True
    assert enrichment["missing_evidence_blocks_safe"] is True
    assert enrichment["malicious_providers"] == ["google_web_risk"]
    assert enrichment["error_providers"] == ["urlhaus"]


def test_threat_enrichment_without_urls_is_explicitly_not_required():
    envelope = build_artifact_envelope(
        artifact_type="text",
        analysis_input_type="text",
        source_channel="manual",
        redacted_text="Salut.",
        external_urls=[],
    )

    enrichment = build_threat_enrichment(
        artifact_envelope=envelope,
        resolved_urls=[],
        provider_summary={},
    )

    assert enrichment["status"] == "not_required"
    assert enrichment["provider_verdict"] == "not_required"
    assert enrichment["missing_evidence_blocks_safe"] is False


def test_clean_provider_that_was_not_consulted_cannot_complete_enrichment():
    envelope = build_artifact_envelope(
        artifact_type="offer",
        analysis_input_type="offer",
        source_channel="share",
        redacted_text="Oferta este aici.",
        external_urls=["https://offer.example/deal"],
    )

    enrichment = build_threat_enrichment(
        artifact_envelope=envelope,
        resolved_urls=[
            {
                "url": "https://offer.example/deal",
                "final_url": "https://offer.example/deal",
                "success": True,
            }
        ],
        provider_summary={
            "google_web_risk": {
                "status": "clean",
                "verdict": "clean",
                "consulted": False,
            }
        },
    )

    assert enrichment["provider_verdict"] == "clean"
    assert enrichment["status"] == "partial"
    assert enrichment["unconsulted_providers"] == ["google_web_risk"]
    assert enrichment["missing_evidence_blocks_safe"] is True
