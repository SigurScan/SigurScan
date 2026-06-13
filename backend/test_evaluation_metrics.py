from __future__ import annotations

from collections import Counter, defaultdict

from services.verdict_gate import verdict
from tools.build_evaluation_dataset import build_cases


def _bundle_from_case(case: dict) -> dict:
    provenance = {flag: True for flag in case.get("provenance", [])}
    return {
        "schema": "sigurscan_evidence_bundle_v2",
        "input": {
            "type": case.get("channel", "unknown"),
            "redacted_text": case.get("text", ""),
        },
        "resolution": {
            "status": case.get("resolution_status", "resolved"),
            "completeness": True,
        },
        "providers": {
            "verdict": case.get("provider_verdict", "clean"),
            "hits": [],
            "completeness": True,
        },
        "identity": {
            "status": case.get("identity_status", "unknown"),
            "tld_suspicious": bool(case.get("tld_suspicious", False)),
            "domain_age_days": case.get("domain_age_days"),
            "ssl_invalid": bool(case.get("ssl_invalid", False)),
            "violated_never_asks": case.get("violated_never_asks", []),
            "violated_never_does": case.get("violated_never_does", []),
            "completeness": True,
        },
        "request": {
            "sensitive": case.get("sensitive", "none"),
            "channel": case.get("channel", "official"),
            "completeness": True,
        },
        "semantic_review": {
            "status": case.get("semantic_status", "done"),
            "risk_class": case.get("semantic_risk", "unknown"),
            "claim_matches_known_scam_family": False,
            "claim_matches_legit_template": False,
            "completeness": True,
        },
        "provenance": provenance,
        "campaign_match": {
            "status": "match" if float(case.get("campaign_confidence") or 0.0) > 0 else "none",
            "confidence": case.get("campaign_confidence", 0.0),
        },
        "community": {
            "reports": case.get("community_reports", 0),
        },
    }


def test_gate_evaluation_dataset_exact_labels():
    cases = build_cases()
    expected_counts = Counter(case["expected_label"] for case in cases)
    assert len(cases) == 350
    assert expected_counts == {
        "SAFE": 100,
        "DANGEROUS": 200,
        "SUSPECT": 25,
        "UNVERIFIED": 25,
    }

    failures = []
    actual_counts: Counter[str] = Counter()
    confusion: dict[str, Counter[str]] = defaultdict(Counter)

    for case in cases:
        result = verdict(_bundle_from_case(case))
        actual = result["label"]
        expected = case["expected_label"]
        actual_counts[actual] += 1
        confusion[expected][actual] += 1
        if actual != expected:
            failures.append(
                {
                    "id": case["id"],
                    "expected": expected,
                    "actual": actual,
                    "reason_codes": result["reason_codes"],
                }
            )

    print(f"\nEvaluation dataset: {len(cases)} cases")
    print(f"Expected: {dict(sorted(expected_counts.items()))}")
    print(f"Actual:   {dict(sorted(actual_counts.items()))}")
    print("Confusion:")
    for expected in sorted(confusion):
        print(f"  {expected}: {dict(sorted(confusion[expected].items()))}")

    assert not failures, failures[:20]


def test_gate_evaluation_dataset_safety_invariants():
    cases = build_cases()
    safe_cases = [case for case in cases if case["expected_label"] == "SAFE"]
    non_safe_cases = [case for case in cases if case["expected_label"] != "SAFE"]

    for case in safe_cases:
        result = verdict(_bundle_from_case(case))
        assert result["label"] == "SAFE", case["id"]

    for case in non_safe_cases:
        result = verdict(_bundle_from_case(case))
        assert result["label"] != "SAFE", case["id"]

    for case in cases:
        if case["provider_verdict"] in {"error", "pending"}:
            result = verdict(_bundle_from_case(case))
            assert result["label"] in {"SUSPECT", "UNVERIFIED"}, case["id"]
