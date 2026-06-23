"""Backward-compatibility module for legacy ``main`` imports."""

from __future__ import annotations

from typing import Any

from config import RISK_THRESHOLD
from app import app, create_app


def __getattr__(name: str) -> Any:
    if name in {"app", "create_app"}:
        return globals()[name]
    import importlib

    runtime = importlib.import_module("main_runtime")
    return getattr(runtime, name)


def __dir__():
    import importlib

    runtime = importlib.import_module("main_runtime")
    return sorted(set(globals()) | set(dir(runtime)))

__all__ = ["app", "create_app"]
