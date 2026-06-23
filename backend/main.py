"""Legacy compatibility shim for imports/tests.

Runtime implementation lives in ``backend/main_runtime.py``.
This module keeps the historical ``main`` module surface alive for existing
code while avoiding import-time cycles during startup.
"""

from __future__ import annotations

import importlib
from typing import Any


_runtime = None


def _get_runtime():
    global _runtime
    if _runtime is None:
        _runtime = importlib.import_module("main_runtime")
    return _runtime


def __getattr__(name: str) -> Any:
    return getattr(_get_runtime(), name)


app = _get_runtime().app
globals().update(_get_runtime().__dict__)
