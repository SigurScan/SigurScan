import json
from pathlib import Path

from services.scam_atlas import ScamAtlasEngine


ROOT = Path(__file__).resolve().parent
SEED_PATH = ROOT / "data" / "scam_atlas_ro_2025_2026_seed.json"
VERDICT_LIKE_FIELDS = {
    "max_verdict_without_provider_scan",
    "max_verdict_with_provider_scan",
    "suggested_expected_verdict",
}


def _raw_families() -> list[dict]:
    payload = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    return payload["scam_families"]


def test_runtime_seed_has_all_three_atlas_blocks():
    ids = [str(item.get("id") or "") for item in _raw_families()]

    assert len(ids) == 63
    assert sum(item.startswith("RO_SCN_") for item in ids) == 20
    assert sum(item.startswith("F") and item[1:].isdigit() for item in ids) == 25
    assert sum(item.startswith("MINOR_") for item in ids) == 18


def test_runtime_seed_excludes_verdict_like_oracle_fields():
    def assert_clean(value):
        if isinstance(value, dict):
            assert VERDICT_LIKE_FIELDS.isdisjoint(value)
            for item in value.values():
                assert_clean(item)
        elif isinstance(value, list):
            for item in value:
                assert_clean(item)

    assert_clean(_raw_families())


def test_runtime_loader_normalizes_every_family_to_semantic_contract():
    families = ScamAtlasEngine().families

    assert len(families) == 63
    for family in families:
        assert family["id"]
        assert family["family"]
        assert family["hook"]
        for field in ("asks_for", "safe_actions", "channels", "requested_asset", "signals", "sources", "examples"):
            assert isinstance(family[field], list)
        assert VERDICT_LIKE_FIELDS.isdisjoint(family)
