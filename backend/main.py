"""Backward-compatibility façade for legacy ``main`` imports."""

from __future__ import annotations

from typing import Any

try:
    import app as _runtime
except ModuleNotFoundError:
    from . import app as _runtime


def __getattr__(name: str) -> Any:
    return getattr(_runtime, name)


app = _runtime.app
__all__ = ["app", "create_app"]
create_app = _runtime.create_app
