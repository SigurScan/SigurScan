import copy
import json
from pathlib import Path

from tools.build_impersonation_knowledge import (
    FORBIDDEN_RUNTIME_FIELDS,
    build_impersonation_knowledge,
    load_research_inputs,
)


ROOT = Path(__file__).resolve().parent.parent
ZIP_PATH = ROOT / "docs" / "fable_handoff" / "sigurscan_op_impersonare_atlas_2026.zip"
REPORT_PATH = ROOT / "docs" / "fable_handoff" / "raport-cercetare-aprofundată (2).md"
SEED_PATH = ROOT / "backend" / "data" / "scam_atlas_impersonation_seed.json"


def _assert_no_forbidden_fields(value):
    if isinstance(value, dict):
        assert FORBIDDEN_RUNTIME_FIELDS.isdisjoint(value)
        for item in value.values():
            _assert_no_forbidden_fields(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_forbidden_fields(item)


def test_impersonation_research_loader_combines_both_research_packs():
    research = load_research_inputs(ZIP_PATH, REPORT_PATH)
    families = {family["code"]: family for family in research["families"]}

    assert len(research["families"]) == 13
    assert len(research["signals"]) == 60
    assert len(research["fixtures"]) == 139
    assert len(research["source_index"]) >= 60
    assert len(research["verification_sources"]) >= 25
    assert "qr" in families["IMP-01"]["common_channels"]
    assert {"src-anaf", "igpr_gov_impersonation"}.issubset(
        families["IMP-01"]["source_refs"]
    )


def test_impersonation_builder_is_idempotent_and_strips_verdict_oracles():
    seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    research = load_research_inputs(ZIP_PATH, REPORT_PATH)

    first = build_impersonation_knowledge(copy.deepcopy(seed), research)
    second = build_impersonation_knowledge(copy.deepcopy(first["runtime_seed"]), research)

    assert first == second
    assert len(first["runtime_seed"]["scam_families"]) == 13
    assert len(first["fixtures"]["fixtures"]) == 139
    _assert_no_forbidden_fields(first["runtime_seed"])


def test_impersonation_builder_keeps_high_value_official_sources_auditable():
    seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    research = load_research_inputs(ZIP_PATH, REPORT_PATH)
    result = build_impersonation_knowledge(seed, research)
    source_ids = {
        source["source_id"]
        for family in result["runtime_seed"]["scam_families"]
        for source in family.get("source_refs", [])
    }

    assert {
        "src-anaf",
        "src-bnr-registre",
        "src-bcr-phishing",
        "src-raiffeisen-sec-online",
        "src-posta-phishing-sms",
        "fan_smishing",
        "apple_social_engineering",
        "whatsapp_security",
    }.issubset(source_ids)


def test_impersonation_builder_routes_research_verification_sources_to_runtime_families():
    seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    research = load_research_inputs(ZIP_PATH, REPORT_PATH)
    result = build_impersonation_knowledge(seed, research)
    families = {
        family["id"]: family
        for family in result["runtime_seed"]["scam_families"]
    }

    assert {"ANAF", "DNSC", "Poliția/MAI/IGPR"}.issubset(
        {source["name"] for source in families["IMP-01"]["verification_sources"]}
    )
    assert {"BNR", "Banca Transilvania", "BCR", "ING", "Revolut"}.issubset(
        {source["name"] for source in families["IMP-02"]["verification_sources"]}
    )
    assert {"FAN Courier", "Poșta Română", "Sameday", "DHL"}.issubset(
        {source["name"] for source in families["IMP-03"]["verification_sources"]}
    )
    assert {"Orange", "Vodafone", "Digi"}.issubset(
        {source["name"] for source in families["IMP-13"]["verification_sources"]}
    )

    runtime_verification_names = {
        source["name"]
        for family in families.values()
        for source in family["verification_sources"]
    }
    research_verification_names = {
        source.get("entity") or source.get("name") or source.get("brand")
        for source in research["verification_sources"]
    }
    assert research_verification_names.issubset(runtime_verification_names)


def test_impersonation_builder_routes_every_research_signal_into_runtime_match_material():
    seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    research = load_research_inputs(ZIP_PATH, REPORT_PATH)
    result = build_impersonation_knowledge(seed, research)

    runtime_signal_slugs = {
        signal["signal_slug"]
        for family in result["runtime_seed"]["scam_families"]
        for signal in family["structured_signals"]
    }
    assert {signal["signal_slug"] for signal in research["signals"]}.issubset(
        runtime_signal_slugs
    )
