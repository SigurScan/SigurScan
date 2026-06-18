#!/usr/bin/env python3
"""Fail CI if secret-bearing local config files are tracked by git."""

from __future__ import annotations

import fnmatch
import subprocess
import sys
from pathlib import Path


ALLOWLIST = {
    "backend/.env.example",
    "workers/precapture/.env.example",
}

DENY_PATTERNS = (
    ".env",
    ".env.*",
    "*/.env",
    "*/.env.*",
    "local.properties",
    "*/local.properties",
    "keystore.properties",
    "*/keystore.properties",
    "*.jks",
    "*.keystore",
    "*service*account*.json",
    "*credential*.json",
    "*credentials*.json",
)


def _normalized(path: str) -> str:
    return path.strip().replace("\\", "/").lstrip("./")


def _is_denied_tracked_path(path: str) -> bool:
    normalized = _normalized(path)
    if normalized in ALLOWLIST or normalized.endswith("/.env.example"):
        return False
    name = Path(normalized).name
    return any(
        fnmatch.fnmatch(normalized, pattern) or fnmatch.fnmatch(name, pattern)
        for pattern in DENY_PATTERNS
    )


def _tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    offenders = [path for path in _tracked_files() if _is_denied_tracked_path(path)]
    if offenders:
        print("Tracked secret-bearing files are forbidden:", file=sys.stderr)
        for path in offenders:
            print(f" - {path}", file=sys.stderr)
        return 1
    print("No tracked secret-bearing local config files found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
