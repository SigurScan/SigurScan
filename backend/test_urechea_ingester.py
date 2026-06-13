from services import supabase_store
from fastapi.testclient import TestClient

import main as app_main
from services.campaign_intel import CampaignStore, CampaignIntel, FAMILY_TAXONOMY
from services.cfx_engine import CfxStore
from services.urechea_ingester import UrecheaIngester


def _install_endpoint_osint_state(monkeypatch):
    store = CampaignStore(seed_path="", load_remote=False)
    ingester = UrecheaIngester(store)
    cfx_store = CfxStore(load_remote=False)
    monkeypatch.setattr(app_main, "campaign_store", store)
    monkeypatch.setattr(app_main, "urechea_ingester", ingester)
    monkeypatch.setattr(app_main, "cfx_store", cfx_store)
    monkeypatch.setattr(app_main, "_INTEL_STATUS", app_main.IntelStatusData())
    monkeypatch.setattr(app_main, "REQUIRE_API_KEY", False)
    return store, ingester, cfx_store


class TestCampaignIntel:
    def test_family_taxonomy_has_12_families(self):
        assert len(FAMILY_TAXONOMY) == 12

    def test_known_family_keys(self):
        expected = {"IMP-01", "IMP-02", "IMP-03", "IMP-04", "IMP-05", "IMP-06",
                    "IMP-07", "IMP-08", "IMP-09", "OP-01", "OP-02", "OP-03"}
        assert set(FAMILY_TAXONOMY.keys()) == expected


class TestCampaignStore:
    def test_empty_store(self):
        store = CampaignStore(seed_path="", load_remote=False)
        assert len(store.all()) == 0

    def test_put_and_get(self):
        store = CampaignStore(seed_path="")
        intel = CampaignIntel(
            intel_id="test_001", family="IMP-01",
            skeleton={}, iocs={}, source={}, evidence_quality="high",
        )
        store.put(intel)
        assert store.get("test_001") is not None
        assert store.get("test_001").intel_id == "test_001"

    def test_active_filters_by_status(self):
        store = CampaignStore(seed_path="", load_remote=False)
        a = CampaignIntel(intel_id="a", family="IMP-01", skeleton={}, iocs={}, source={},
                          evidence_quality="high", status="active", moderation={"approved": True})
        b = CampaignIntel(intel_id="b", family="IMP-02", skeleton={}, iocs={}, source={},
                          evidence_quality="medium", status="inactive", moderation={})
        store.put(a)
        store.put(b)
        active = store.active()
        assert len(active) == 1
        assert active[0].intel_id == "a"

    def test_active_filters_unapproved(self):
        store = CampaignStore(seed_path="", load_remote=False)
        a = CampaignIntel(intel_id="a", family="IMP-01", skeleton={}, iocs={}, source={},
                          evidence_quality="high", status="active", moderation={"approved": False})
        b = CampaignIntel(intel_id="b", family="IMP-02", skeleton={}, iocs={}, source={},
                          evidence_quality="medium", status="active", moderation={})
        store.put(a)
        store.put(b)
        active = store.active()
        assert len(active) == 1
        assert active[0].intel_id == "b"


class TestUrecheaIngester:
    def test_sources_loaded(self, store: CampaignStore | None = None):
        _store = store or CampaignStore(seed_path="", load_remote=False)
        ingester = UrecheaIngester(_store)
        assert len(ingester.sources) >= 8

    def test_ingest_raw_high_quality_auto_approved(self):
        store = CampaignStore(seed_path="", load_remote=False)
        ingester = UrecheaIngester(store)
        intel = ingester.ingest_raw(
            title="Alertă DNSC: Campanie de smishing FAN Courier",
            body="DNSC avertizează asupra unei campanii de smishing care folosește numele FAN Courier. "
                 "Mesajele cer plata unei taxe vamale și introducerea datelor cardului.",
            source_url="https://www.dnsc.ro/alerta",
            source_kind="official_alert",
            claimed_identity="FAN Courier",
            evidence_quality="high",
        )
        assert intel.family == "IMP-03"
        assert intel.moderation.get("approved") is True
        assert intel.status == "active"
        assert intel.source["kind"] == "official_alert"

    def test_ingest_raw_medium_quality_queues_moderation(self):
        store = CampaignStore(seed_path="", load_remote=False)
        ingester = UrecheaIngester(store)
        intel = ingester.ingest_raw(
            title="Posibilă campanie nouă",
            body="Am primit un mesaj suspect despre o oportunitate de investiții cu randament garantat.",
            source_url="",
            source_kind="press_context",
            claimed_identity="BNR",
            evidence_quality="medium",
        )
        assert intel.family == "IMP-02"
        assert intel.moderation.get("approved") is False
        assert intel.moderation.get("required_for") == "dangerous"
        assert len(ingester.moderation_queue) == 1

    def test_ingest_unknown_family_goes_to_draft(self):
        store = CampaignStore(seed_path="", load_remote=False)
        ingester = UrecheaIngester(store)
        intel = ingester.ingest_raw(
            title="Știre generală",
            body="Astăzi a avut loc un eveniment important în oraș.",
            source_url="https://stiri.ro/eveniment",
            source_kind="press_context",
            evidence_quality="low",
        )
        assert intel.family == "UNKNOWN"
        assert intel.status == "draft"

    def test_approve_intel(self):
        store = CampaignStore(seed_path="", load_remote=False)
        ingester = UrecheaIngester(store)
        intel = ingester.ingest_raw(
            title="Test", body="Test", source_url="", source_kind="press_context",
            claimed_identity="BNR", evidence_quality="medium",
        )
        assert ingester.approve_intel(intel.intel_id, "moderator") is True
        stored = store.get(intel.intel_id)
        assert stored is not None
        assert stored.moderation["approved"] is True
        assert stored.moderation["approved_by"] == "moderator"
        assert len(ingester.moderation_queue) == 0

    def test_reject_intel(self):
        store = CampaignStore(seed_path="", load_remote=False)
        ingester = UrecheaIngester(store)
        intel = ingester.ingest_raw(
            title="Test", body="Test", source_url="", source_kind="press_context",
            claimed_identity="OLX", evidence_quality="medium",
        )
        assert ingester.reject_intel(intel.intel_id) is True
        stored = store.get(intel.intel_id)
        assert stored is not None
        assert stored.status == "rejected"

    def test_classify_imp01_bank_safe_account(self):
        store = CampaignStore(seed_path="", load_remote=False)
        ingester = UrecheaIngester(store)
        intel = ingester.ingest_raw(
            title="SMS cont sigur", body="Transferă fondurile în contul nostru sigur. Sună la banca.",
            source_url="", source_kind="press_context", claimed_identity="Banca Transilvania",
            evidence_quality="low",
        )
        assert intel.family == "IMP-01"

    def test_classify_imp03_courier_tax(self):
        store = CampaignStore(seed_path="", load_remote=False)
        ingester = UrecheaIngester(store)
        intel = ingester.ingest_raw(
            title="SMS curier", body="Ai o taxă vamală de plată pentru coletul tău FAN Courier.",
            source_url="", source_kind="press_context", claimed_identity="FAN Courier",
            evidence_quality="low",
        )
        assert intel.family == "IMP-03"

    def test_classify_op01_bec_iban_change(self):
        store = CampaignStore(seed_path="", load_remote=False)
        ingester = UrecheaIngester(store)
        intel = ingester.ingest_raw(
            title="Email IBAN schimbat",
            body="Factura ANAF: IBAN-ul nostru s-a schimbat. Vă rugăm să faceți plata în noul cont.",
            source_url="", source_kind="vendor_advisory", claimed_identity="ANAF",
            evidence_quality="medium",
        )
        assert intel.family == "OP-01"

    def test_by_family(self):
        store = CampaignStore(seed_path="", load_remote=False)
        ingester = UrecheaIngester(store)
        ingester.ingest_raw("A", "cont sigur", "", "press_context", claimed_identity="BT", evidence_quality="high")
        ingester.ingest_raw("B", "cont sigur", "", "press_context", claimed_identity="BCR", evidence_quality="high")
        results = store.by_family("IMP-01")
        assert len(results) == 2

    def test_store_loads_persisted_campaign_intel(self, monkeypatch):
        monkeypatch.setattr(
            supabase_store,
            "load_campaign_intel",
            lambda: [
                {
                    "intel_id": "remote_001",
                    "family": "IMP-03",
                    "skeleton": {"claimed_identity": "FAN Courier", "ask": "taxa colet", "channel": "sms"},
                    "iocs": {},
                    "source": {"kind": "official_alert"},
                    "evidence_quality": "high",
                    "status": "active",
                    "regions_hint": ["national"],
                    "moderation": {"approved": True},
                    "created_at": 1.0,
                    "last_seen_at": 2.0,
                }
            ],
        )

        store = CampaignStore(seed_path="")

        assert store.get("remote_001") is not None
        assert store.get("remote_001").family == "IMP-03"

    def test_store_persists_campaign_intel_on_put(self, monkeypatch):
        captured = {}
        monkeypatch.setattr(supabase_store, "load_campaign_intel", lambda: [])
        monkeypatch.setattr(supabase_store, "save_campaign_intel", lambda entry: captured.setdefault("entry", entry))
        store = CampaignStore(seed_path="", load_remote=False)
        intel = CampaignIntel(
            intel_id="persist_001",
            family="IMP-01",
            skeleton={"ask": "cont sigur"},
            iocs={},
            source={},
            evidence_quality="high",
        )

        store.put(intel)

        assert captured["entry"]["intel_id"] == "persist_001"

    def test_ingest_endpoint_seeds_cfx_and_updates_status(self, monkeypatch):
        store, _ingester, cfx_store = _install_endpoint_osint_state(monkeypatch)
        client = TestClient(app_main.app)

        response = client.post(
            "/v1/intel/ingest",
            json={
                "title": "Alerta DNSC FAN Courier",
                "body": (
                    "DNSC avertizeaza asupra unei campanii de smishing FAN Courier. "
                    "Mesajele cer taxa vamala si date card."
                ),
                "source_url": "https://dnsc.ro/alerta",
                "source_kind": "official_alert",
                "claimed_identity": "FAN Courier",
                "evidence_quality": "high",
                "regions_hint": ["national"],
            },
        )

        assert response.status_code == 200
        intel_id = response.json()["intel_id"]
        assert store.get(intel_id) is not None
        assert cfx_store.get(f"cf_{intel_id}") is not None

        status = client.get("/v1/urechea/status")
        assert status.status_code == 200
        data = status.json()
        assert data["entries_ingested"] == 1
        assert data["last_source"] == "official_alert"
        assert data["campaign_count"] == 1
        assert data["fingerprint_count"] == 1

    def test_reject_endpoint_removes_cfx_fingerprint(self, monkeypatch):
        store, _ingester, cfx_store = _install_endpoint_osint_state(monkeypatch)
        client = TestClient(app_main.app)
        response = client.post(
            "/v1/intel/ingest",
            json={
                "title": "Alerta DNSC FAN Courier",
                "body": (
                    "DNSC avertizeaza asupra unei campanii de smishing FAN Courier. "
                    "Mesajele cer taxa vamala si date card."
                ),
                "source_url": "https://dnsc.ro/alerta",
                "source_kind": "official_alert",
                "claimed_identity": "FAN Courier",
                "evidence_quality": "high",
            },
        )
        assert response.status_code == 200
        intel_id = response.json()["intel_id"]
        assert cfx_store.get(f"cf_{intel_id}") is not None

        response = client.post(
            "/v1/intel/moderate",
            json={"intel_id": intel_id, "action": "reject"},
        )

        assert response.status_code == 200
        assert cfx_store.get(f"cf_{intel_id}") is None
        assert store.get(intel_id).status == "rejected"
