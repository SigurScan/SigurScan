#!/usr/bin/env python3
"""Measure the monotonic fraud-floor candidate without activating it.

The runner uses the existing broad offline corpus, keeps only generic cases
that contain a URL, obtains the production decision bundle, then simulates a
failed URL resolution. It compares the active gate with the guarded candidate
and writes aggregate-only JSON: no case text, URL, hostname, path, or provider
payload is persisted.
"""

from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from eval.large_offline_fixture_runner import (  # noqa: E402
    DEFAULT_ZIPS,
    _resolved_urls,
    _should_route_invoice_case,
    _source_channel,
    load_cases,
)
from main import (  # noqa: E402
    _apply_provider_gate_verdict,
    _normalise_obfuscated_text,
    engine,
)
from services.pii_redactor import redact_pii  # noqa: E402
from services.verdict_gate import verdict, verdict_monotonic_candidate  # noqa: E402


LABEL_RANK = {"SAFE": 0, "UNVERIFIED": 1, "SUSPECT": 2, "DANGEROUS": 3}


def _deduplicated_cases(downloads_dir: Path, zip_names: Iterable[str]) -> List[Dict[str, Any]]:
    seen: set[Tuple[str, str, str]] = set()
    unique: List[Dict[str, Any]] = []
    for case in load_cases(downloads_dir, zip_names):
        key = (str(case.get("source")), str(case.get("id")), str(case.get("text")))
        if key in seen:
            continue
        seen.add(key)
        unique.append(case)
    return unique


def _decision_bundle(case: Dict[str, Any]) -> Dict[str, Any] | None:
    analysis_text = _normalise_obfuscated_text(str(case.get("text") or ""))
    redacted_text = redact_pii(analysis_text)
    resolved_urls = _resolved_urls(redacted_text)
    if not resolved_urls or _should_route_invoice_case(case, analysis_text):
        return None

    analysis = engine.analyze(redacted_text, urls=resolved_urls, external_threat_intel={})
    evidence = analysis.setdefault("evidence", {})
    evidence["source_channel"] = _source_channel(case)
    final = _apply_provider_gate_verdict(
        analysis,
        resolved_urls,
        raw_text=redacted_text,
        pillars={},
    )
    final_evidence = final.get("evidence") if isinstance(final.get("evidence"), dict) else {}
    bundle = final_evidence.get("decision_bundle")
    return copy.deepcopy(bundle) if isinstance(bundle, dict) else None


def _simulate_resolution_failure(bundle: Dict[str, Any]) -> Dict[str, Any]:
    candidate = copy.deepcopy(bundle)
    candidate["resolution"] = {
        "status": "failed",
        "completeness": False,
    }
    return candidate


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_DIR,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def run(downloads_dir: Path, zip_names: Iterable[str]) -> Dict[str, Any]:
    cases = _deduplicated_cases(downloads_dir, zip_names)
    transitions: Counter[str] = Counter()
    expected_counts: Counter[str] = Counter()
    active_counts: Counter[str] = Counter()
    candidate_counts: Counter[str] = Counter()
    candidate_reasons: Counter[str] = Counter()
    expected_transitions: Counter[str] = Counter()
    changed_reasons_by_expected: Dict[str, Counter[str]] = defaultdict(Counter)
    by_source: Dict[str, Counter[str]] = defaultdict(Counter)
    skipped = Counter()
    evaluated = 0
    labeled = 0
    false_safe = 0
    safe_escalations = 0
    dangerous_recoveries = 0
    dangerous_recovered_to_floor = 0
    dangerous_remaining_below = 0
    suspect_recoveries = 0
    suspect_over_escalations = 0
    unverified_escalations = 0

    for case in cases:
        try:
            bundle = _decision_bundle(case)
        except Exception:
            skipped["pipeline_error"] += 1
            continue
        if bundle is None:
            skipped["not_generic_url_case"] += 1
            continue

        incomplete = _simulate_resolution_failure(bundle)
        active = verdict(incomplete)
        candidate = verdict_monotonic_candidate(incomplete)
        active_label = str(active.get("label") or "UNVERIFIED").upper()
        candidate_label = str(candidate.get("label") or "UNVERIFIED").upper()
        expected = str(case.get("expected") or "").upper()
        source = str(case.get("source") or "unknown")

        evaluated += 1
        active_counts[active_label] += 1
        candidate_counts[candidate_label] += 1
        transitions[f"{active_label}->{candidate_label}"] += 1
        by_source[source][f"{active_label}->{candidate_label}"] += 1
        candidate_reasons.update(str(code) for code in candidate.get("reason_codes") or [])

        if not expected:
            continue
        labeled += 1
        expected_counts[expected] += 1
        expected_transitions[f"{expected}:{active_label}->{candidate_label}"] += 1
        if active_label != candidate_label:
            changed_reasons_by_expected[expected].update(
                str(code) for code in candidate.get("reason_codes") or []
            )
        if candidate_label == "SAFE":
            false_safe += 1
        if (
            expected == "SAFE"
            and LABEL_RANK[active_label] < LABEL_RANK["SUSPECT"]
            and LABEL_RANK[candidate_label] >= LABEL_RANK["SUSPECT"]
        ):
            safe_escalations += 1
        elif expected == "DANGEROUS":
            if active_label != "DANGEROUS" and candidate_label == "DANGEROUS":
                dangerous_recoveries += 1
            if LABEL_RANK[active_label] < LABEL_RANK["SUSPECT"] <= LABEL_RANK[candidate_label]:
                dangerous_recovered_to_floor += 1
            if candidate_label != "DANGEROUS":
                dangerous_remaining_below += 1
        elif expected == "SUSPECT":
            if LABEL_RANK[active_label] < LABEL_RANK["SUSPECT"] <= LABEL_RANK[candidate_label]:
                suspect_recoveries += 1
            if LABEL_RANK[active_label] < LABEL_RANK["DANGEROUS"] == LABEL_RANK[candidate_label]:
                suspect_over_escalations += 1
        elif expected == "UNVERIFIED" and LABEL_RANK[candidate_label] >= LABEL_RANK["SUSPECT"]:
            unverified_escalations += 1

    changed = sum(count for transition, count in transitions.items() if transition.split("->")[0] != transition.split("->")[1])
    return {
        "schema": "sigurscan_verdict_gate_monotonic_measurement_v1",
        "base_commit": _git_commit(),
        "mode": "offline_existing_pipeline_bundle_with_resolution_failure_simulation",
        "privacy": "Aggregate counts only; no text, URL, hostname, path, case id, or provider payload is stored.",
        "corpus": {
            "deduplicated_case_count": len(cases),
            "evaluated_generic_url_cases": evaluated,
            "labeled_cases": labeled,
            "skipped": dict(skipped),
            "expected_counts": dict(expected_counts),
        },
        "results": {
            "active_counts": dict(active_counts),
            "candidate_counts": dict(candidate_counts),
            "transitions": dict(transitions),
            "expected_transitions": dict(expected_transitions),
            "changed_cases": changed,
            "false_safe_candidates": false_safe,
            "safe_to_suspect_or_dangerous": safe_escalations,
            "dangerous_recovered_to_dangerous": dangerous_recoveries,
            "dangerous_recovered_to_at_least_suspect": dangerous_recovered_to_floor,
            "dangerous_remaining_below_dangerous": dangerous_remaining_below,
            "suspect_recovered_to_at_least_suspect": suspect_recoveries,
            "suspect_over_escalated_to_dangerous": suspect_over_escalations,
            "unverified_escalated_to_suspect_or_dangerous": unverified_escalations,
            "candidate_reason_counts": dict(candidate_reasons),
            "changed_reason_counts_by_expected": {
                expected: dict(counts)
                for expected, counts in sorted(changed_reasons_by_expected.items())
            },
        },
        "by_source_transitions": {
            source: dict(counts)
            for source, counts in sorted(by_source.items())
            if any(before != after for before, after in (key.split("->") for key in counts))
        },
        "decision": {
            "active_flag_default": False,
            "activation_authorized": False,
            "requires_manual_fp_fn_review": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--downloads-dir", default="/Users/vaduvageorge/Downloads")
    parser.add_argument(
        "--output",
        default="build/reports/verdict_gate_monotonic_2026-07-17/measurement.json",
    )
    args = parser.parse_args()

    report = run(Path(args.downloads_dir), DEFAULT_ZIPS)
    output = Path(args.output)
    if not output.is_absolute():
        output = REPO_DIR / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
