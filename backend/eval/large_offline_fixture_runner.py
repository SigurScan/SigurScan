#!/usr/bin/env python3
"""Run the broad local SigurScan fixture corpus through the offline provider gate.

This runner intentionally does not call live providers or cloud LLMs. It is a
local regression radar: atlas/engine analysis + production decision gate, with
URLs represented as already-resolved to themselves.
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List


BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from main import (  # noqa: E402
    _apply_provider_gate_verdict,
    _canonicalize_url,
    _normalise_obfuscated_text,
    engine,
    extract_urls,
)
from services.pii_redactor import redact_pii  # noqa: E402


DEFAULT_ZIPS = [
    "sigurscan_adversarial_negation_contrastive_ro_2026_06_17.zip",
    "sigurscan_imm_b2b_invoice_fraud_pack_2026_06_15.zip",
    "sigurscan_imm_b2b_invoice_fraud_round2_2026_06_15.zip",
    "sigurscan_imm_b2b_invoice_fraud_round3_2026_06_15.zip",
    "sigurscan_real_scam_cases_ro_2026_round1.zip",
    "sigurscan_real_scam_cases_ro_2026_round2_b2b_invoice.zip",
    "sigurscan_real_b2b_scam_cases_ro_eu_2026_round3_98_cases.zip",
    "sigurscan_novel_zero_day_holdout_ro_2026_06_18.zip",
    "sigurscan_ro_research_test_pack_2025_2026_v1.zip",
    "sigurscan_romania_minor_scam_families_addendum_2025_2026.zip",
]


def _map_expected(value: Any) -> str:
    text = str(value or "").strip().upper()
    aliases = {
        "PERICULOS": "DANGEROUS",
        "DANGEROUS": "DANGEROUS",
        "NU_PLATI": "DANGEROUS",
        "NO_REPLY": "DANGEROUS",
        "NO_ENTER_DATA": "DANGEROUS",
        "DO_NOT_CONTINUE": "DANGEROUS",
        "SIGUR": "SAFE",
        "SAFE": "SAFE",
        "CONTINUE_WITH_CAUTION": "SAFE",
        "SUSPECT": "SUSPECT",
        "NEVERIFICAT": "UNVERIFIED",
        "UNVERIFIED": "UNVERIFIED",
        "VERIFY_OFFICIAL": "SUSPECT",
        "INSUFFICIENT_EVIDENCE": "UNVERIFIED",
        "VERIFICA": "SUSPECT",
        "VERIFICĂ": "SUSPECT",
    }
    return aliases.get(text, text if text in {"SAFE", "SUSPECT", "DANGEROUS", "UNVERIFIED"} else "")


def _comparable_label(label: str) -> str:
    return "SUSPECT" if label == "UNVERIFIED" else label


def _final_label(analysis: Dict[str, Any]) -> str:
    evidence = analysis.get("evidence") if isinstance(analysis.get("evidence"), dict) else {}
    gate = evidence.get("verdict_gate") if isinstance(evidence.get("verdict_gate"), dict) else {}
    label = str(analysis.get("user_risk_label") or gate.get("label") or "").upper()
    if label:
        return label
    risk = str(analysis.get("risk_level") or "").lower()
    if risk in {"critical", "dangerous", "high"}:
        return "DANGEROUS"
    if risk in {"medium", "warning", "unknown", "pending", "info", "unverified"}:
        return "SUSPECT"
    return "SAFE"


def _case(
    cases: List[Dict[str, Any]],
    *,
    source: str,
    case_id: Any,
    text: Any,
    expected: Any = "",
    meta: Dict[str, Any] | None = None,
) -> None:
    raw_text = str(text or "").strip()
    if not raw_text:
        return
    cases.append(
        {
            "source": source,
            "id": str(case_id or f"{source}-{len(cases) + 1}"),
            "text": raw_text,
            "expected": _map_expected(expected),
            "meta": meta or {},
        }
    )


def _repo_jsonl_cases(cases: List[Dict[str, Any]]) -> None:
    for rel in (
        "backend/data/evaluation_dataset_v1.jsonl",
        "backend/data/eval_dataset.jsonl",
        "backend/data/hard_eval.jsonl",
        "backend/data/verdict_testset_ro.jsonl",
    ):
        path = REPO_DIR / rel
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            if rel.endswith("verdict_testset_ro.jsonl"):
                _case(
                    cases,
                    source=rel,
                    case_id=item.get("id"),
                    text=item.get("input"),
                    expected=item.get("label"),
                    meta={"family": item.get("family")},
                )
                continue
            expected = item.get("expected_label")
            if expected is None and "is_scam" in item:
                expected = "DANGEROUS" if item.get("is_scam") else "SAFE"
            if expected is None and "actual_is_scam" in item:
                expected = "DANGEROUS" if item.get("actual_is_scam") else "SAFE"
            _case(
                cases,
                source=rel,
                case_id=item.get("id"),
                text=item.get("text") or item.get("input") or item.get("url"),
                expected=expected,
                meta={"kind": item.get("kind"), "channel": item.get("channel")},
            )


def _web_redteam_cases(cases: List[Dict[str, Any]]) -> None:
    path = REPO_DIR / "backend/testdata/web_redteam_scam_fixtures_2026_06_16.json"
    if not path.exists():
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload if isinstance(payload, list) else payload.get("cases") or payload.get("fixtures") or []
    for item in rows:
        if not isinstance(item, dict):
            continue
        _case(
            cases,
            source=str(path.relative_to(REPO_DIR)),
            case_id=item.get("id") or item.get("case_id"),
            text=item.get("text") or item.get("input") or item.get("message"),
            expected=item.get("expected_label") or item.get("expected_final_verdict") or "DANGEROUS",
        )


def _expected_from_item(item: Dict[str, Any]) -> Any:
    expected = (
        item.get("expected_final_verdict")
        or item.get("expected_verdict")
        or item.get("expected_label")
        or item.get("expected_user_action")
    )
    if isinstance(expected, list):
        return "DANGEROUS"
    return expected


def _text_from_item(item: Dict[str, Any]) -> Any:
    return (
        item.get("sample_text")
        or item.get("input_text")
        or item.get("text")
        or item.get("input")
        or item.get("message")
        or item.get("html_mime_fragment")
    )


def _zip_cases(cases: List[Dict[str, Any]], downloads_dir: Path, zip_names: Iterable[str]) -> None:
    for zip_name in zip_names:
        zip_path = downloads_dir / zip_name
        if not zip_path.exists():
            continue
        with zipfile.ZipFile(zip_path) as archive:
            for member in archive.namelist():
                if not member.endswith(".json"):
                    continue
                try:
                    payload = json.loads(archive.read(member).decode("utf-8", "ignore"))
                except Exception:
                    continue
                source = f"{zip_name}:{member}"
                if isinstance(payload, dict) and isinstance(payload.get("pairs"), list):
                    for pair in payload["pairs"]:
                        if not isinstance(pair, dict):
                            continue
                        for side, expected in (("safe_case", "SAFE"), ("scam_case", "DANGEROUS")):
                            side_payload = pair.get(side) or {}
                            _case(
                                cases,
                                source=source,
                                case_id=f"{pair.get('id')}-{side}",
                                text=side_payload.get("input_text"),
                                expected=side_payload.get("expected_final_verdict") or expected,
                                meta={"category": pair.get("category"), "side": side},
                            )
                    continue
                if isinstance(payload, dict):
                    handled = False
                    for key in ("acceptance_tests", "test_cases", "cases", "fixtures"):
                        rows = payload.get(key)
                        if not isinstance(rows, list):
                            continue
                        for item in rows:
                            if isinstance(item, dict):
                                _case(
                                    cases,
                                    source=source,
                                    case_id=item.get("test_id") or item.get("id") or item.get("case_id"),
                                    text=_text_from_item(item),
                                    expected=_expected_from_item(item),
                                    meta={"family": item.get("family") or item.get("family_id"), "input_type": item.get("input_type")},
                                )
                        handled = True
                        break
                    if not handled and member.endswith("/answer_key/cases.json"):
                        for case_id, item in payload.items():
                            if isinstance(item, dict):
                                _case(
                                    cases,
                                    source=source,
                                    case_id=item.get("id") or case_id,
                                    text=item.get("input_text"),
                                    expected=item.get("expected_final_verdict") or "DANGEROUS",
                                    meta={"family": item.get("family")},
                                )
                elif isinstance(payload, list):
                    for item in payload:
                        if isinstance(item, dict):
                            _case(
                                cases,
                                source=source,
                                case_id=item.get("test_id") or item.get("id") or item.get("case_id"),
                                text=_text_from_item(item),
                                expected=_expected_from_item(item),
                                meta={"family": item.get("family") or item.get("family_id"), "input_type": item.get("input_type")},
                            )


def load_cases(downloads_dir: Path, zip_names: Iterable[str]) -> List[Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []
    _repo_jsonl_cases(cases)
    _web_redteam_cases(cases)
    _zip_cases(cases, downloads_dir, zip_names)

    seen: set[tuple[str, str, str]] = set()
    unique: List[Dict[str, Any]] = []
    for case in cases:
        key = (case["source"], case["id"], case["text"][:200])
        if key in seen:
            continue
        seen.add(key)
        unique.append(case)
    return unique


def _resolved_urls(text: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for url in extract_urls(text):
        canonical = _canonicalize_url(url) or url
        out.append({"url": canonical, "input_url": canonical, "final_url": canonical, "success": True, "status_code": 200})
    return out


def run(downloads_dir: Path, zip_names: Iterable[str]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for case in load_cases(downloads_dir, zip_names):
        text = redact_pii(_normalise_obfuscated_text(case["text"]))
        try:
            resolved = _resolved_urls(text)
            analysis = engine.analyze(text, urls=resolved, external_threat_intel={})
            evidence = analysis.setdefault("evidence", {})
            evidence["source_channel"] = case["meta"].get("input_type") or case["meta"].get("channel") or "offline_eval"
            final = _apply_provider_gate_verdict(analysis, resolved, raw_text=text, pillars={})
            actual = _final_label(final)
            expected = case["expected"]
            passed = (_comparable_label(actual) == _comparable_label(expected)) if expected else None
            final_evidence = final.get("evidence") if isinstance(final.get("evidence"), dict) else {}
            provider_gate = final_evidence.get("provider_gate") if isinstance(final_evidence.get("provider_gate"), dict) else {}
            verdict_gate = final_evidence.get("verdict_gate") if isinstance(final_evidence.get("verdict_gate"), dict) else {}
            rows.append(
                {
                    "source": case["source"],
                    "id": case["id"],
                    "expected": expected,
                    "actual": actual,
                    "passed": passed,
                    "risk_level": final.get("risk_level"),
                    "risk_score": final.get("risk_score"),
                    "detected_family_id": final.get("detected_family_id"),
                    "gate_reason": provider_gate.get("reason"),
                    "reason_codes": verdict_gate.get("reason_codes"),
                    "text_preview": case["text"][:240],
                }
            )
        except Exception as exc:
            rows.append(
                {
                    "source": case["source"],
                    "id": case["id"],
                    "expected": case["expected"],
                    "actual": "ERROR",
                    "passed": False,
                    "error": f"{type(exc).__name__}: {exc}",
                    "text_preview": case["text"][:240],
                }
            )

    labeled = [row for row in rows if row["expected"]]
    failures = [row for row in labeled if row["passed"] is False]
    confusion: Dict[str, Counter[str]] = defaultdict(Counter)
    for row in labeled:
        confusion[_comparable_label(row["expected"])][_comparable_label(row["actual"])] += 1

    by_source: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "labeled": 0, "failed": 0})
    for row in rows:
        bucket = by_source[row["source"]]
        bucket["total"] += 1
        bucket["labeled"] += 1 if row["expected"] else 0
        bucket["failed"] += 1 if row.get("passed") is False else 0

    return {
        "mode": "offline_provider_gate_no_live_providers_no_mistral",
        "total_cases": len(rows),
        "labeled_cases": len(labeled),
        "passed": len(labeled) - len(failures),
        "failed": len(failures),
        "actual_counts": dict(Counter(row["actual"] for row in rows)),
        "expected_counts": dict(Counter(row["expected"] for row in labeled)),
        "confusion": {key: dict(value) for key, value in confusion.items()},
        "by_source": dict(sorted(by_source.items(), key=lambda item: (-item[1]["failed"], -item[1]["total"]))),
        "top_failed_family_ids": dict(Counter(row.get("detected_family_id") or "unknown" for row in failures).most_common(30)),
        "failures_sample": failures[:200],
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run large offline SigurScan fixture corpus through provider gate.")
    parser.add_argument("--downloads-dir", default="/Users/vaduvageorge/Downloads")
    parser.add_argument("--output", default="build/reports/large_eval_2026-06-20/offline_big_provider_gate.json")
    args = parser.parse_args()

    report = run(Path(args.downloads_dir), DEFAULT_ZIPS)
    output = Path(args.output)
    if not output.is_absolute():
        output = REPO_DIR / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "mode",
                    "total_cases",
                    "labeled_cases",
                    "passed",
                    "failed",
                    "actual_counts",
                    "expected_counts",
                    "confusion",
                    "top_failed_family_ids",
                )
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
