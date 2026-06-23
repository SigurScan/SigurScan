"""Compatibility module for legacy ``main`` imports."""

from __future__ import annotations

from app import app, create_app
from importlib import import_module

_legacy_runtime = import_module("main_runtime")

for _name in dir(_legacy_runtime):
    if _name.startswith("__"):
        continue
    if _name in {"app", "create_app"}:
        continue
    globals()[_name] = getattr(_legacy_runtime, _name)

__all__ = ["app", "create_app"] + [
    _name
    for _name in globals()
    if _name not in {"app", "create_app", "_legacy_runtime", "import_module", "importlib", "annotations"}
    and not _name.startswith("__")
]

del _legacy_runtime
