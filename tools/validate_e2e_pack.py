#!/usr/bin/env python3
"""Validate a SigurScan E2E fixture pack without running live providers."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


TEXT_SUFFIXES = {".csv", ".eml", ".html", ".htm", ".json", ".md", ".txt"}
OLD_BRAND_TOKENS = ("NuDaClick", "nudaclick", "NuDa", "NDCR-V2")


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _case_id(case: dict[str, Any]) -> str:
    return str(case.get("id") or case.get("case_id") or "<missing-id>")


def _fixture_paths(case: dict[str, Any]) -> list[str]:
    return [str(path) for path in _as_list(case.get("fixturePaths") or case.get("fixture_path"))]


def _provider_paths(case: dict[str, Any]) -> list[str]:
    provider_mocks = case.get("providerMocks")
    if isinstance(provider_mocks, dict):
        return [str(path) for path in provider_mocks.values() if path]
    return [str(path) for path in _as_list(case.get("provider_mock_path")) if path]


def _snapshot_paths(case: dict[str, Any]) -> list[str]:
    return [str(path) for path in _as_list(case.get("expectedSnapshotPath")) if path]


def _expected_decision(case: dict[str, Any]) -> str:
    return str(case.get("expectedDecision") or case.get("expected_decision") or "<missing>")


def _channel(case: dict[str, Any]) -> str:
    return str(case.get("channel") or case.get("input_type") or "<missing>")


def _fixture_kinds(case: dict[str, Any]) -> list[str]:
    kinds = case.get("fixtureKinds")
    if isinstance(kinds, list):
        return [str(kind) for kind in kinds]
    first_path = next(iter(_fixture_paths(case)), "")
    suffix = Path(first_path).suffix.lower().lstrip(".")
    return [suffix or "<missing>"]


def validate_pack(root: Path, strict_branding: bool) -> int:
    cases_path = root / "test_cases.json"
    if not cases_path.is_file():
        print(f"ERROR: missing {cases_path}")
        return 1

    cases = json.loads(cases_path.read_text())
    if not isinstance(cases, list):
        print("ERROR: test_cases.json must be a JSON array")
        return 1

    missing_refs: list[str] = []
    for case in cases:
        cid = _case_id(case)
        for rel_path in _fixture_paths(case) + _provider_paths(case) + _snapshot_paths(case):
            if not (root / rel_path).is_file():
                missing_refs.append(f"{cid}: {rel_path}")

    old_brand_hits: list[str] = []
    if strict_branding:
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            text = path.read_text(errors="ignore")
            if any(token in text for token in OLD_BRAND_TOKENS):
                old_brand_hits.append(str(path.relative_to(root)))
        for path in root.rglob("*"):
            if any(token in path.name for token in OLD_BRAND_TOKENS):
                old_brand_hits.append(str(path.relative_to(root)))

    verdicts = Counter(_expected_decision(case) for case in cases)
    channels = Counter(_channel(case) for case in cases)
    fixture_kinds = Counter(kind for case in cases for kind in _fixture_kinds(case))

    print(f"root: {root}")
    print(f"cases: {len(cases)}")
    print(f"verdicts: {dict(verdicts)}")
    print(f"channels: {dict(channels)}")
    print(f"fixtureKinds: {dict(fixture_kinds)}")
    print(f"missing_refs: {len(missing_refs)}")
    if missing_refs:
        print("\n".join(missing_refs[:80]))
    if strict_branding:
        print(f"old_brand_hits: {len(old_brand_hits)}")
        if old_brand_hits:
            print("\n".join(old_brand_hits[:80]))

    return 1 if missing_refs or old_brand_hits else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, help="Fixture pack root containing test_cases.json")
    parser.add_argument("--strict-branding", action="store_true")
    args = parser.parse_args()
    return validate_pack(args.root, args.strict_branding)


if __name__ == "__main__":
    raise SystemExit(main())
