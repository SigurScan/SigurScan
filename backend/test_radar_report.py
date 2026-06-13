import json
import re
import time

from services.campaign_intel import CampaignIntel, CampaignStore
from services.radar_hot_cache import build_hot_cache, reputation_bucket
from services.report_builder import REPORT_DISCLAIMER, build_report_package


def _store_with(*intels) -> CampaignStore:
    store = CampaignStore.__new__(CampaignStore)
    store._intels = {}
    for intel in intels:
        store._intels[intel.intel_id] = intel
    return store


def _intel(
    intel_id: str,
    family: str,
    *,
    status: str = "active",
    last_seen_at: float | None = None,
) -> CampaignIntel:
    return CampaignIntel(
        intel_id=intel_id,
        family=family,
        skeleton={"claimed_identity": "BNR", "ask": "transfer", "channel": "sms"},
        iocs={"phone_hash_prefixes": ["hmacpfx0001"]},
        source={"kind": "official_alert", "url": "https://dnsc.ro/"},
        evidence_quality="high",
        status=status,
        regions_hint=["RO"],
        last_seen_at=last_seen_at if last_seen_at is not None else time.time(),
    )


def test_reputation_bucket_is_coarse_and_non_pii():
    assert reputation_bucket(0) == "0"
    assert reputation_bucket(1) == "1-4"
    assert reputation_bucket(4) == "1-4"
    assert reputation_bucket(5) == "5-24"
    assert reputation_bucket(24) == "5-24"
    assert reputation_bucket(25) == "25-99"
    assert reputation_bucket(99) == "25-99"
    assert reputation_bucket(100) == "100+"


def test_hot_cache_contains_campaign_warnings_and_excludes_stale_or_inactive():
    old = _intel("ci_old", "CONV_COURIER_TAX_CARD", last_seen_at=time.time() - 30 * 86400)
    inactive = _intel("ci_dead", "CONV_BANK_SAFE_ACCOUNT", status="stale")
    fresh = _intel("ci_new", "CONV_BANK_SAFE_ACCOUNT")

    out = build_hot_cache(_store_with(old, inactive, fresh), reports=[], since=time.time() - 7 * 86400)

    assert out["ttl_minutes"] > 0
    ids = {campaign["campaign_id"] for campaign in out["hot_campaigns"]}
    assert ids == {"ci_new"}
    campaign = out["hot_campaigns"][0]
    assert campaign["warning_title"]
    assert campaign["phone_hash_prefixes"] == ["hmacpfx0001"]


def test_hot_cache_uses_hashes_and_never_raw_phone_numbers():
    out = build_hot_cache(
        _store_with(),
        reports=[
            {"hash": "hmac_aaa", "report_count": 7, "family": "CONV_BANK_SAFE_ACCOUNT"},
            {"hash": "hmac_bbb", "report_count": 1, "family": "CONV_COURIER_TAX_CARD"},
        ],
    )

    reputation = {item["phone_hash"]: item for item in out["number_reputation"]}
    assert reputation["hmac_aaa"]["bucket_count"] == "5-24"
    assert reputation["hmac_bbb"]["bucket_count"] == "1-4"
    blob = json.dumps(out, ensure_ascii=False)
    assert "+407" not in blob
    assert "0712345678" not in blob


def test_report_package_is_deterministic_and_prepared_not_sent():
    args = {
        "target": {"type": "url", "value_redacted": "fan-livrare[.]test"},
        "family": "CONV_COURIER_TAX_CARD",
        "verdict": "DANGEROUS",
    }

    first = build_report_package(**args)
    second = build_report_package(**args)

    assert first == second
    assert first["disclaimer"] == REPORT_DISCLAIMER
    assert any(channel["name"] == "DNSC" for channel in first["channels"])
    assert any("PNRISC" in channel["name"] for channel in first["channels"])


def test_report_package_does_not_emit_raw_financial_or_identity_data():
    package = build_report_package(
        target={"type": "iban", "value_redacted": "RO** **** 3456"},
        family="DOC_BEC_IBAN_CHANGE",
        verdict="SUSPECT",
    )

    blob = json.dumps(package, ensure_ascii=False)
    assert not re.search(r"\bRO\d{22}\b", blob)
    assert not re.search(r"\b\d{13}\b", blob)


def test_radar_and_report_endpoints_are_available():
    from fastapi.testclient import TestClient
    import main as app_main

    client = TestClient(app_main.app)

    hot = client.get("/v1/radar/hot-iocs")
    assert hot.status_code == 200
    assert set(hot.json()) >= {"generated_at", "ttl_minutes", "hot_campaigns", "number_reputation"}

    report = client.post(
        "/v1/report",
        json={
            "target_type": "url",
            "target_redacted": "fan-livrare[.]test",
            "family": "CONV_COURIER_TAX_CARD",
            "verdict": "DANGEROUS",
        },
    )
    assert report.status_code == 200
    assert any(channel["name"] == "DNSC" for channel in report.json()["channels"])
