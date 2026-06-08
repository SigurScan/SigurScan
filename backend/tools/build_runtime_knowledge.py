import json
import re
import unicodedata
import urllib.parse
from pathlib import Path

import tldextract


ROOT = Path(__file__).resolve().parents[2]
ANDROID_KNOWLEDGE_PATH = ROOT / "app" / "src" / "main" / "assets" / "knowledge" / "romania_knowledge_layer_compact.json"
SEED_OUTPUT_PATH = ROOT / "backend" / "data" / "scam_atlas_ro_2025_2026_seed.json"
BRAND_PACK_OUTPUT_PATH = ROOT / "backend" / "data" / "brand_knowledge_pack.json"
KNOWLEDGE_OUTPUT_DIR = ROOT / "backend" / "data" / "knowledge"
CONTRACT_EVAL_OUTPUT_PATH = ROOT / "backend" / "data" / "eval" / "romania_decision_contract_eval_v2026_06_08.jsonl"


REQUESTED_ASSET_TERMS = {
    "card": ["card", "numar card", "număr card", "date card"],
    "cvv": ["cvv", "cvc", "cod cvv"],
    "otp": ["otp", "cod otp", "cod sms"],
    "whatsapp_code": ["whatsapp", "cod whatsapp"],
    "banking_pin": ["pin", "pin bancar"],
    "cnp": ["cnp"],
    "iban": ["iban"],
    "password": ["parola", "parolă", "password"],
    "remote_access": ["anydesk", "teamviewer", "control la distanta", "control la distanță"],
    "apk_install": ["apk", "instaleaza apk", "instalează apk"],
    "safe_account_transfer": ["cont sigur", "transfer sigur"],
}

VERDICT_LIKE_FIELDS = {
    "max_verdict_without_provider_scan",
    "max_verdict_with_provider_scan",
    "suggested_expected_verdict",
}


def _load_android_knowledge() -> dict:
    with ANDROID_KNOWLEDGE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_existing_brand_pack() -> dict:
    if not BRAND_PACK_OUTPUT_PATH.exists():
        return {}
    with BRAND_PACK_OUTPUT_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
        return data if isinstance(data, dict) else {}


def _coerce_str_list(values) -> list[str]:
    if not values:
        return []
    output: list[str] = []
    for item in values:
        raw = str(item or "").strip()
        if raw:
            output.append(raw)
    return output


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen = set()
    output: list[str] = []
    for value in values:
        normalized = str(value or "").strip()
        if not normalized:
            continue
        fingerprint = normalized.lower()
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        output.append(normalized)
    return output


def _strip_verdict_like_fields(value):
    if isinstance(value, dict):
        return {
            key: _strip_verdict_like_fields(item)
            for key, item in value.items()
            if key not in VERDICT_LIKE_FIELDS
        }
    if isinstance(value, list):
        return [_strip_verdict_like_fields(item) for item in value]
    return value


def _merge_map_of_lists(*items: dict[str, list[str]]) -> dict[str, list[str]]:
    merged: dict[str, list[str]] = {}
    for source in items:
        for key, values in source.items():
            bucket = merged.setdefault(key, [])
            bucket.extend(_coerce_str_list(values))
            merged[key] = _dedupe_preserve_order(bucket)
    return merged


def _merge_map_of_strings(*items: dict[str, str]) -> dict[str, str]:
    merged: dict[str, str] = {}
    for source in items:
        for key, value in source.items():
            raw = str(value or "").strip()
            if raw:
                merged[str(key)] = raw
    return merged


def _ascii_fold(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value or "")
    return "".join(char for char in folded if not unicodedata.combining(char))


def _normalize_host(raw: str) -> str:
    text = str(raw or "").strip()
    if not text:
        return ""
    if "://" in text:
        text = urllib.parse.urlparse(text).hostname or ""
    text = text.lower().strip().strip(".")
    if text.startswith("www."):
        text = text[4:]
    return text


def _base_label_for_host(host: str) -> str:
    normalized = _normalize_host(host)
    if not normalized:
        return ""
    extracted = tldextract.extract(normalized)
    return (extracted.domain or normalized.split(".")[0]).strip().lower()


def _alias_candidates(
    brand_id: str,
    display_name: str,
    official_domains: list[str],
    partner_domains: list[str],
) -> list[str]:
    aliases = [
        display_name,
        _ascii_fold(display_name),
        brand_id.replace("_", " "),
        _ascii_fold(brand_id.replace("_", " ")),
    ]

    for separator in ("/", "|"):
        if separator in display_name:
            aliases.extend(part.strip() for part in display_name.split(separator) if part.strip())
            aliases.extend(_ascii_fold(part.strip()) for part in display_name.split(separator) if part.strip())

    for host in official_domains + partner_domains:
        base = _base_label_for_host(host)
        if base:
            aliases.append(base)

    cleaned_aliases = []
    for alias in aliases:
        raw = re.sub(r"\s+", " ", str(alias or "").strip())
        if raw:
            cleaned_aliases.append(raw)
    return _dedupe_preserve_order(cleaned_aliases)


def _trusted_labels_for_domains(domains: list[str], aliases: list[str]) -> list[str]:
    labels = []
    for host in domains:
        base = _base_label_for_host(host)
        if base:
            labels.append(base)
    for alias in aliases:
        normalized = re.sub(r"[^0-9a-z]+", "", _ascii_fold(alias).lower())
        if normalized and len(normalized) >= 3:
            labels.append(normalized)
        if " " not in alias:
            lowered = _ascii_fold(alias).lower().strip()
            if lowered and len(lowered) >= 3:
                labels.append(lowered)
    return _dedupe_preserve_order(labels)


def _hook_for(entry: dict) -> str:
    parts = []
    parts.extend(entry.get("names_used_in_romania") or [])
    parts.extend(entry.get("typical_text_patterns") or [])
    parts.append(entry.get("claimed_brand_or_role") or "")
    return " | ".join(part.strip() for part in parts if str(part).strip())


def _asks_for_for(entry: dict) -> list[str]:
    asks = []
    for asset in entry.get("requested_asset") or []:
        key = str(asset).strip().lower()
        mapped = REQUESTED_ASSET_TERMS.get(key)
        if mapped:
            asks.extend(mapped)
        elif key:
            asks.append(key.replace("_", " "))
    deduped = []
    seen = set()
    for ask in asks:
        normalized = ask.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            deduped.append(ask)
    return deduped


def _safe_actions_for(entry: dict) -> list[str]:
    brand = entry.get("claimed_brand_or_role") or "instituția invocată"
    requested = {str(asset).strip().lower() for asset in (entry.get("requested_asset") or [])}
    actions = [
        "Nu accesați linkul și nu răspundeți înainte de verificare.",
        f"Contactați {brand} doar pe canalul oficial, introdus manual.",
    ]
    if requested.intersection({"card", "cvv", "otp", "banking_pin", "password", "cnp", "iban"}):
        actions.insert(1, "Nu introduceți date bancare, parole, coduri OTP sau date personale.")
    if requested.intersection({"remote_access", "apk_install"}):
        actions.insert(1, "Nu instalați aplicații și nu permiteți control la distanță.")
    return actions


def build_seed_payload(knowledge: dict) -> dict:
    families = []
    for entry in knowledge.get("scenario_corpus", []):
        families.append(
            {
                "id": entry.get("scenario_id"),
                "title": entry.get("title"),
                "family": f"{entry.get('family', 'unknown')} / {entry.get('claimed_brand_or_role', 'unknown')}",
                "hook": _hook_for(entry),
                "asks_for": _asks_for_for(entry),
                "safe_actions": _safe_actions_for(entry),
                "channels": entry.get("channels") or [],
                "claimed_brand_or_role": entry.get("claimed_brand_or_role"),
                "requested_asset": entry.get("requested_asset") or [],
                "signals": entry.get("signals") or [],
                "sources": entry.get("sources") or entry.get("source_ids") or [],
                "examples": _strip_verdict_like_fields(entry.get("examples") or []),
                "acceptance_test_idea": entry.get("acceptance_test_idea"),
            }
        )
    return {
        "metadata": {
            "generated_from": str(ANDROID_KNOWLEDGE_PATH.relative_to(ROOT)),
            "generator": "backend/tools/build_runtime_knowledge.py",
            "role": "semantic knowledge only; verdict-like oracle fields are excluded",
        },
        "scam_families": families,
    }


def build_brand_pack_payload(knowledge: dict, existing_pack: dict) -> dict:
    generated_registry: dict[str, list[str]] = {}
    generated_exceptions: dict[str, list[str]] = {}
    generated_aliases: dict[str, list[str]] = {}
    generated_trusted: dict[str, str] = {}

    for entry in knowledge.get("official_registry_updates", []):
        brand_id = str(entry.get("brand_id") or "").strip()
        display_name = str(entry.get("display_name") or brand_id or "").strip()
        if not display_name:
            continue

        official_domains = _dedupe_preserve_order(
            [_normalize_host(host) for host in entry.get("official_domains") or [] if _normalize_host(host)]
        )
        partner_domains = _dedupe_preserve_order(
            [_normalize_host(host) for host in entry.get("approved_tracking_or_partner_domains") or [] if _normalize_host(host)]
        )

        generated_registry[display_name] = official_domains
        if partner_domains:
            generated_exceptions[display_name] = partner_domains

        aliases = _alias_candidates(brand_id, display_name, official_domains, partner_domains)
        generated_aliases[display_name] = aliases

        for label in _trusted_labels_for_domains(official_domains + partner_domains, aliases):
            generated_trusted[label] = display_name

    metadata = {
        "pack": "sigurscan_runtime_knowledge_v2",
        "generated_from": str(ANDROID_KNOWLEDGE_PATH.relative_to(ROOT)),
        "generator": "backend/tools/build_runtime_knowledge.py",
        "preserves_existing_operational_entries": True,
    }

    return {
        "metadata": metadata,
        "brand_registry": _merge_map_of_lists(
            generated_registry,
            existing_pack.get("brand_registry", {}),
        ),
        "brand_domain_exceptions": _merge_map_of_lists(
            generated_exceptions,
            existing_pack.get("brand_domain_exceptions", {}),
        ),
        "trusted_base_names": _merge_map_of_strings(
            generated_trusted,
            existing_pack.get("trusted_base_names", {}),
        ),
        "brand_aliases": _merge_map_of_lists(
            generated_aliases,
            existing_pack.get("brand_aliases", {}),
        ),
        "brand_warnings": knowledge.get("brand_warnings", []),
        "claim_verifier_targets": knowledge.get("claim_verifier_targets", []),
        "official_registry_updates": knowledge.get("official_registry_updates", []),
        "false_positive_guards": knowledge.get("false_positive_guards", []),
        "signal_mapping": knowledge.get("signal_mapping", []),
        "sources": knowledge.get("sources", {}),
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def _coerce_json_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _contract_label_to_is_scam(label: str | None) -> bool | None:
    normalized = str(label or "").strip().upper()
    if normalized == "PERICULOS":
        return True
    if normalized == "SIGUR":
        return False
    return None


def build_contract_eval_records(knowledge: dict) -> list[dict]:
    records: list[dict] = []
    for entry in knowledge.get("acceptance_tests", []):
        if not isinstance(entry, dict):
            continue
        test_id = str(entry.get("test_id") or "").strip()
        sample_text = str(entry.get("sample_text") or "").strip()
        if not test_id or not sample_text:
            continue
        expected_label = str(entry.get("expected_final_verdict") or "").strip().upper()
        records.append(
            {
                "id": test_id,
                "kind": str(entry.get("input_type") or "text").strip().lower(),
                "text": sample_text,
                "family_id": entry.get("family_id"),
                "expected_contract_label": expected_label,
                "is_scam": _contract_label_to_is_scam(expected_label),
                "expected_extracted_targets": _coerce_json_list(entry.get("expected_extracted_targets")),
                "mocked_provider_results": entry.get("mocked_provider_results") or {},
                "expected_corpus_signals": _coerce_json_list(entry.get("expected_corpus_signals")),
                "reason": entry.get("reason"),
                "source": "romania_scam_atlas_compact_2025_2026",
                "decision_contract_note": (
                    "This is a contract/evidence fixture. SUSPECT and PENDING labels are not binary "
                    "scam labels for precision/recall and must be evaluated by the pure reducer."
                ),
            }
        )
    return records


def write_normalized_knowledge_files(knowledge: dict) -> None:
    payloads = {
        "official_registry_v2026_06_08.json": {
            "metadata": {
                "generated_from": str(ANDROID_KNOWLEDGE_PATH.relative_to(ROOT)),
                "decision_contract": "docs/DECISION_CONTRACT_V1.md",
                "role": "identity registry candidates, not verdict authority",
            },
            "official_registry_updates": knowledge.get("official_registry_updates", []),
            "sources": knowledge.get("sources", {}),
        },
        "brand_warnings_v2026_06_08.json": {
            "metadata": {
                "generated_from": str(ANDROID_KNOWLEDGE_PATH.relative_to(ROOT)),
                "decision_contract": "docs/DECISION_CONTRACT_V1.md",
                "role": "channel-aware/asset-aware warning candidates, not regex verdicts",
            },
            "brand_warnings": knowledge.get("brand_warnings", []),
            "sources": knowledge.get("sources", {}),
        },
        "romania_scam_families_v2026_06_08.json": {
            "metadata": {
                "generated_from": str(ANDROID_KNOWLEDGE_PATH.relative_to(ROOT)),
                "decision_contract": "docs/DECISION_CONTRACT_V1.md",
                "role": "corpus/RAG context and acceptance-test source, not verdict authority",
            },
            "scenario_corpus": knowledge.get("scenario_corpus", []),
            "false_positive_guards": knowledge.get("false_positive_guards", []),
            "signal_mapping": knowledge.get("signal_mapping", []),
            "sources": knowledge.get("sources", {}),
        },
        "claim_verifier_targets_v2026_06_08.json": {
            "metadata": {
                "generated_from": str(ANDROID_KNOWLEDGE_PATH.relative_to(ROOT)),
                "decision_contract": "docs/DECISION_CONTRACT_V1.md",
                "role": "claim web-check targets; confirmed claims support evidence but do not decide alone",
            },
            "claim_verifier_targets": knowledge.get("claim_verifier_targets", []),
            "sources": knowledge.get("sources", {}),
        },
    }
    for filename, payload in payloads.items():
        _write_json(KNOWLEDGE_OUTPUT_DIR / filename, payload)


def main() -> None:
    knowledge = _load_android_knowledge()
    existing_pack = _load_existing_brand_pack()

    seed_payload = build_seed_payload(knowledge)
    brand_pack_payload = build_brand_pack_payload(knowledge, existing_pack)
    contract_eval_records = build_contract_eval_records(knowledge)

    _write_json(SEED_OUTPUT_PATH, seed_payload)
    _write_json(BRAND_PACK_OUTPUT_PATH, brand_pack_payload)
    write_normalized_knowledge_files(knowledge)
    _write_jsonl(CONTRACT_EVAL_OUTPUT_PATH, contract_eval_records)

    print(f"Wrote {SEED_OUTPUT_PATH} with {len(seed_payload['scam_families'])} scam families")
    print(
        f"Wrote {BRAND_PACK_OUTPUT_PATH} with "
        f"{len(brand_pack_payload['brand_registry'])} brands, "
        f"{len(brand_pack_payload.get('brand_warnings', []))} warnings and "
        f"{len(brand_pack_payload.get('claim_verifier_targets', []))} claim targets"
    )
    print(f"Wrote {KNOWLEDGE_OUTPUT_DIR} normalized knowledge files")
    print(f"Wrote {CONTRACT_EVAL_OUTPUT_PATH} with {len(contract_eval_records)} contract fixtures")


if __name__ == "__main__":
    main()
