#!/usr/bin/env python3
"""Evaluate Romania contract fixtures through the pure Verdict Gate v2.

The JSONL records are evidence-contract fixtures, not live scans. This runner
normalizes their mocked providers, targets, and corpus signals into Evidence
Bundle v2 without reading expected_contract_label, then compares the pure gate
projection with the expected label.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.scam_atlas import BRAND_DOMAIN_EXCEPTIONS, BRAND_REGISTRY, ScamAtlasEngine  # noqa: E402
from services.verdict_gate import verdict  # noqa: E402


DEFAULT_DATASET = BACKEND_DIR / "data" / "eval" / "romania_decision_contract_eval_v2026_06_08.jsonl"
RESERVED_SUFFIXES = (".test", ".invalid", ".example")
HARD_SENSITIVE_MARKERS = {
    "APK_INSTALL_REQUEST": "remote",
    "BANK_NEVER_ASK_ING_SECURITY_DATA_OR_APP": "password",
    "CARD_OR_BANKING_REQUEST": "card",
    "CARD_OR_ID_REQUEST": "card",
    "CREDENTIAL_REQUEST": "password",
    "MARKETPLACE_CARD_TO_RECEIVE_MONEY": "card",
    "OTP_REQUEST": "otp",
    "PASSWORD_REQUEST": "password",
    "REMOTE_ACCESS_APP_REQUEST": "remote",
    "TAX_REFUND_FORM_CARD": "card",
    "WHATSAPP_VERIFICATION_CODE_REQUEST": "otp",
}
VALUE_MARKERS = {
    "SAFE_ACCOUNT_TRANSFER_REQUEST",
    "URGENT_CASH_REQUEST",
    "MONEY_TRANSFER_REQUEST",
}
BENIGN_MARKERS = {
    "OFFICIAL_DOMAIN_EXACT_MATCH",
    "OTP_LEGIT_INFORMATIONAL",
}
HIGH_SEMANTIC_MARKERS = {
    "ACCIDENT_CLAIM",
    "APK_INSTALL_REQUEST",
    "CARD_OR_BANKING_REQUEST",
    "CARD_OR_ID_REQUEST",
    "CREDENTIAL_REQUEST",
    "CRYPTO_PAYMENT_REQUEST",
    "FAKE_AUTHORITY_DOCUMENT",
    "GUARANTEED_RETURN_PROMISE",
    "MARKETPLACE_CARD_TO_RECEIVE_MONEY",
    "REMOTE_ACCESS_APP_REQUEST",
    "SAFE_ACCOUNT_TRANSFER_REQUEST",
    "URGENT_CASH_REQUEST",
    "WHATSAPP_VERIFICATION_CODE_REQUEST",
}


def _load_cases(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _targets(case: dict[str, Any]) -> list[str]:
    output = []
    for value in case.get("expected_extracted_targets") or []:
        target = str(value or "").strip().lower()
        if not target or target == "none":
            continue
        target = re.sub(r"^https?://", "", target).split("/", 1)[0].strip(".")
        if target:
            output.append(target)
    return output


def _provider_verdict(case: dict[str, Any], has_url: bool) -> tuple[str, bool]:
    values = " ".join(str(value or "").lower() for value in (case.get("mocked_provider_results") or {}).values())
    if any(token in values for token in ("malicious", "phishing", "malware", "blacklist")):
        return "malicious", True
    if any(token in values for token in ("pending", "timeout", "rate_limit", "404")):
        return "pending", False
    if not has_url:
        return "unknown", True
    if any(token in values for token in ("no_match", "no match", "clean", "forms=", "screenshot", "final_url=")):
        return "clean", True
    return "pending", False


def _official_hosts() -> set[str]:
    hosts = set()
    for mapping in (BRAND_REGISTRY, BRAND_DOMAIN_EXCEPTIONS):
        for values in mapping.values():
            hosts.update(str(value).strip().lower() for value in values if str(value).strip())
    return hosts


OFFICIAL_HOSTS = _official_hosts()


def _identity_status(case: dict[str, Any], targets: list[str], claimed_brand: str | None) -> str:
    signals = {str(value).strip().upper() for value in case.get("expected_corpus_signals") or []}
    if "OFFICIAL_DOMAIN_EXACT_MATCH" in signals:
        return "official"
    if any(any(target == host or target.endswith(f".{host}") for host in OFFICIAL_HOSTS) for target in targets):
        return "official"
    if targets and claimed_brand and any(target.endswith(RESERVED_SUFFIXES) for target in targets):
        return "unrelated"
    return "unknown"


def _request(case: dict[str, Any], identity_status: str) -> tuple[str, str]:
    signals = {str(value).strip().upper() for value in case.get("expected_corpus_signals") or []}
    text = str(case.get("text") or "").lower()
    sensitive = "none"
    for marker, value in HARD_SENSITIVE_MARKERS.items():
        if marker in signals:
            sensitive = value
            break
    if sensitive == "none" and signals.intersection(VALUE_MARKERS):
        sensitive = "transfer"
    if sensitive == "none":
        if re.search(r"\b(anydesk|teamviewer|rustdesk|apk)\b", text):
            sensitive = "remote"
        elif re.search(r"\b(cvv|cvc|date(?:le)? de card|num[aă]r(?:ul)? de card)\b", text):
            sensitive = "card"
        elif re.search(r"\b(otp|cod whatsapp|codul primit|cod sms)\b", text):
            sensitive = "otp"
        elif re.search(r"\b(cont sigur|transfer|iban|trimite.{0,20}(?:bani|lei))\b", text):
            sensitive = "transfer"

    kind = str(case.get("kind") or "").lower()
    if identity_status == "official":
        channel = "official"
    elif _targets(case):
        channel = "unofficial_site"
    elif "whatsapp" in kind or "messenger" in kind or "telegram" in kind or "chat" in kind:
        channel = "whatsapp"
    elif "phone" in kind or "call" in kind:
        channel = "phone"
    else:
        channel = "reply"
    return sensitive, channel


def _semantic_review(case: dict[str, Any], identity_status: str) -> dict[str, Any]:
    signals = {str(value).strip().upper() for value in case.get("expected_corpus_signals") or []}
    if identity_status == "official" or signals.intersection(BENIGN_MARKERS):
        risk_class = "benign"
    elif signals.intersection(HIGH_SEMANTIC_MARKERS):
        risk_class = "high"
    elif signals:
        risk_class = "medium"
    else:
        risk_class = "unknown"
    return {
        "status": "done",
        "risk_class": risk_class,
        "claim_matches_known_scam_family": risk_class in {"high", "medium"},
        "claim_matches_legit_template": risk_class == "benign",
        "reason_codes": sorted(signals),
        "completeness": True,
    }


def bundle_from_case(case: dict[str, Any]) -> dict[str, Any]:
    targets = _targets(case)
    text = str(case.get("text") or "")
    claimed_brand = ScamAtlasEngine().detect_claimed_brand(text)
    identity_status = _identity_status(case, targets, claimed_brand)
    sensitive, channel = _request(case, identity_status)
    provider_status, provider_complete = _provider_verdict(case, bool(targets))
    resolution_status = "resolved" if targets else "not_required"
    return {
        "schema": "sigurscan_evidence_bundle_v2",
        "input": {"type": case.get("kind") or "unknown", "redacted_text": text},
        "resolution": {
            "final_url": f"https://{targets[0]}/" if targets else None,
            "status": resolution_status,
            "completeness": True,
        },
        "providers": {"verdict": provider_status, "hits": [], "completeness": provider_complete},
        "identity": {
            "claimed_brand": claimed_brand,
            "status": identity_status,
            "tld_suspicious": bool(targets and targets[0].endswith(RESERVED_SUFFIXES)),
            "completeness": True,
        },
        "request": {"sensitive": sensitive, "channel": channel, "completeness": True},
        "semantic_review": _semantic_review(case, identity_status),
    }


def run(dataset: Path) -> dict[str, Any]:
    rows = []
    for case in _load_cases(dataset):
        actual = verdict(bundle_from_case(case))
        expected = str(case.get("expected_contract_label") or "").upper()
        rows.append(
            {
                "id": case.get("id"),
                "expected": expected,
                "actual": actual["label"],
                "passed": actual["label"] == expected,
                "reason_codes": actual.get("reason_codes") or [],
            }
        )
    failures = [row for row in rows if not row["passed"]]
    return {
        "dataset": str(dataset),
        "total": len(rows),
        "passed": len(rows) - len(failures),
        "failed": len(failures),
        "expected_counts": dict(Counter(row["expected"] for row in rows)),
        "actual_counts": dict(Counter(row["actual"] for row in rows)),
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Romania evidence-contract fixtures through Verdict Gate v2.")
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--output")
    parser.add_argument("--max-failures", type=int, default=0)
    args = parser.parse_args()

    report = run(Path(args.dataset))
    if args.output:
        output = Path(args.output)
        if not output.is_absolute():
            output = REPO_DIR / output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({key: report[key] for key in ("dataset", "total", "passed", "failed", "expected_counts", "actual_counts")}, ensure_ascii=False, indent=2))
    return 1 if report["failed"] > args.max_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
