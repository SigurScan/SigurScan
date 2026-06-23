"""Backward-compatibility module for legacy ``main`` imports."""

from __future__ import annotations

import main_runtime

from config import RISK_THRESHOLD
from app import app, create_app


def __getattr__(name: str) -> Any:
    if name in {"app", "create_app"}:
        return globals()[name]
    return getattr(main_runtime, name)


def __dir__():
    return sorted(set(globals()) | set(dir(main_runtime)))

__all__ = ["app", "create_app"]
