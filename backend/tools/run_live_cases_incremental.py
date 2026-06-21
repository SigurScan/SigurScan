#!/usr/bin/env python3
"""Run live SigurScan cases incrementally and persist progress after each case."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List


REPO_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from eval.live_provider_smoke_runner import (  # noqa: E402
    API_KEY_ENV,
    RUN_ENV,
    _load_cases_from_file,
    _run_case,
)


def _write_report(path: Path, rows: List[Dict[str, Any]], *, base_url: str) -> None:
    passed = sum(1 for row in rows if row.get("passed") is True)
    failed = sum(1 for row in rows if row.get("passed") is False)
    report = {
        "base_url": base_url,
        "total": len(rows),
        "passed": passed,
        "failed": failed,
        "actual_counts": dict(Counter(str(row.get("actual_label") or "ERROR") for row in rows)),
        "rows": rows,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://api.sigurscan.com")
    parser.add_argument("--cases-file", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--poll-interval", type=float, default=3.0)
    parser.add_argument("--timeout", type=float, default=75.0)
    parser.add_argument("--start", type=int, default=0, help="Zero-based case index to start from.")
    parser.add_argument("--limit", type=int, default=0, help="Maximum number of cases to run; 0 means all.")
    args = parser.parse_args()

    if os.getenv(RUN_ENV) != "1":
        print(f"Set {RUN_ENV}=1 to run live provider cases.", file=sys.stderr)
        return 2
    if not os.getenv(API_KEY_ENV):
        print(f"Set {API_KEY_ENV} before running live provider cases.", file=sys.stderr)
        return 2

    cases = _load_cases_from_file(args.cases_file)
    selected = cases[args.start :]
    if args.limit > 0:
        selected = selected[: args.limit]

    output = Path(args.output)
    if not output.is_absolute():
        output = REPO_DIR / output

    rows: List[Dict[str, Any]] = []
    if output.exists():
        try:
            existing = json.loads(output.read_text(encoding="utf-8"))
            rows = list(existing.get("rows") or [])
        except Exception:
            rows = []

    completed_ids = {str(row.get("id") or "") for row in rows}
    total = len(selected)
    for offset, case in enumerate(selected, start=1):
        if case.case_id in completed_ids:
            continue
        row = _run_case(args.base_url.rstrip("/"), case, args.poll_interval, args.timeout)
        rows.append(row)
        _write_report(output, rows, base_url=args.base_url.rstrip("/"))
        print(
            json.dumps(
                {
                    "progress": f"{offset}/{total}",
                    "id": row.get("id"),
                    "label": row.get("actual_label"),
                    "passed": row.get("passed"),
                    "gate": row.get("provider_gate_reason"),
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    _write_report(output, rows, base_url=args.base_url.rstrip("/"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
