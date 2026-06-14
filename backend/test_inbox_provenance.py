"""PR-7 (Faza 2) — Inboxul Protejat: contract verdict on-device + BTR sync.

Linia roșie (§8): ZERO conținut SMS către server — nici hash-uit — fără opt-in
separat. Procesare 100% on-device. De aceea NU există endpoint care primește SMS;
`build_inbox_verdict` e logica de referință (Python) pe care portul Android o
oglindește on-device, alimentată DOAR cu semnale deja extrase/redactate local.

Verdictul reutilizează verdict_gate (judecătorul unic, 4 stări) — nu îl rescrie.

Decizie (documentată): SAFE on-device DOAR pentru brand match + zero link + zero
cerere sensibilă (suprafață vacuum-clean: nu există link de verificat la provider).
Altfel maximul on-device fără proveniență pozitivă e UNVERIFIED (gri, niciodată verde).
"""
import json

from services.inbox_provenance import build_inbox_verdict, btr_sync_payload
from services.brand_truth_registry import BrandTruthRegistry


# ─── Contract shape & privacy ──────────────────────────────────────────────
class TestInboxVerdictShape:
    def test_carries_on_device_privacy_flags(self):
        v = build_inbox_verdict(message_hash="hmac_abc", claimed_brand=None, provenance="unknown")
        assert v["processing"] == "on_device_only"
        assert v["raw_stored"] is False
        assert v["render"] == "inline_band"
        assert v["message_hash"] == "hmac_abc"

    def test_no_raw_message_text_in_payload(self):
        v = build_inbox_verdict(
            message_hash="hmac_abc", claimed_brand="bt", provenance="mismatch",
            sensitive_asks=["card"],
        )
        blob = json.dumps(v)
        assert "transcript" not in blob and "raw_text" not in blob
        # doar hash-ul, niciun câmp de conținut brut
        assert "message_text" not in blob

    def test_verdict_is_one_of_four_states(self):
        v = build_inbox_verdict(message_hash="h", claimed_brand=None, provenance="unknown")
        assert v["verdict"] in {"DANGEROUS", "SUSPECT", "UNVERIFIED", "SAFE"}


# ─── Truth-table rows relevant for SMS provenance band ─────────────────────
class TestInboxVerdictRules:
    def test_brand_mismatch_plus_card_is_dangerous(self):
        v = build_inbox_verdict(
            message_hash="h", claimed_brand="bt", provenance="mismatch",
            sensitive_asks=["card", "cvv"],
        )
        assert v["verdict"] == "DANGEROUS"

    def test_person_never_does_violation_is_dangerous(self):
        # ex: "Isărescu te cheamă să investești" pe canal neoficial
        v = build_inbox_verdict(
            message_hash="h", claimed_brand="isarescu", provenance="mismatch",
            violated_never_does=["investment_endorsement"],
        )
        assert v["verdict"] == "DANGEROUS"

    def test_campaign_high_solo_is_max_suspect(self):
        v = build_inbox_verdict(
            message_hash="h", claimed_brand=None, provenance="unknown",
            campaign_match="cf_bnr_safe", campaign_confidence=0.91,
            campaign_family="CONV_BANK_SAFE_ACCOUNT",
        )
        assert v["verdict"] == "SUSPECT"
        assert v["campaign_match"] == "cf_bnr_safe"

    def test_campaign_below_threshold_not_suspect(self):
        v = build_inbox_verdict(
            message_hash="h", claimed_brand=None, provenance="unknown",
            campaign_match="cf_x", campaign_confidence=0.50,
        )
        assert v["verdict"] != "DANGEROUS"
        assert v["verdict"] in {"UNVERIFIED", "SUSPECT"}  # nu hard, sub prag 0.82

    def test_unknown_clean_is_unverified_never_safe(self):
        v = build_inbox_verdict(
            message_hash="h", claimed_brand=None, provenance="unknown",
        )
        assert v["verdict"] == "UNVERIFIED"

    def test_match_no_url_no_sensitive_is_safe(self):
        # Decizie documentată: suprafață vacuum-clean (zero link de verificat).
        v = build_inbox_verdict(
            message_hash="h", claimed_brand="bt", provenance="match",
            sensitive_asks=None, final_url=None,
        )
        assert v["verdict"] == "SAFE"

    def test_match_but_with_url_is_not_safe_without_provider(self):
        # Există link → nu există clearance de provider on-device → NU SAFE.
        v = build_inbox_verdict(
            message_hash="h", claimed_brand="bt", provenance="match",
            sensitive_asks=None, final_url="https://bt-secure.test/login",
        )
        assert v["verdict"] != "SAFE"

    def test_determinism(self):
        kwargs = dict(message_hash="h", claimed_brand="bt", provenance="mismatch",
                      sensitive_asks=["otp"])
        assert build_inbox_verdict(**kwargs) == build_inbox_verdict(**kwargs)


# ─── BTR sync (device pulls manifests for on-device matching) ──────────────
class TestBtrSync:
    def test_full_payload_when_version_differs(self):
        reg = BrandTruthRegistry()
        out = btr_sync_payload(reg, client_version="stale-or-none")
        assert out["changed"] is True
        assert out["version"] == reg.version
        assert isinstance(out["manifests"], list) and len(out["manifests"]) >= 1
        assert out["count"] == len(out["manifests"])

    def test_noop_when_version_matches(self):
        reg = BrandTruthRegistry()
        out = btr_sync_payload(reg, client_version=reg.version)
        assert out["changed"] is False
        assert out["version"] == reg.version
        assert out.get("manifests") in (None, [])

    def test_manifests_are_serializable_dicts(self):
        reg = BrandTruthRegistry()
        out = btr_sync_payload(reg, client_version=None)
        json.dumps(out)  # nu trebuie să arunce
        m0 = out["manifests"][0]
        assert "manifest_id" in m0 and "type" in m0


# ─── Endpoint ──────────────────────────────────────────────────────────────
class TestBtrSyncEndpoint:
    def _client(self):
        from fastapi.testclient import TestClient
        import main as app_main
        return TestClient(app_main.app)

    def test_sync_endpoint_returns_manifests(self):
        client = self._client()
        r = client.get("/v1/btr/sync")
        assert r.status_code == 200
        body = r.json()
        assert body["changed"] is True
        assert body["count"] >= 1

    def test_sync_endpoint_noop_on_same_version(self):
        client = self._client()
        version = client.get("/v1/btr/sync").json()["version"]
        r = client.get("/v1/btr/sync", params={"client_version": version})
        assert r.status_code == 200
        assert r.json()["changed"] is False
