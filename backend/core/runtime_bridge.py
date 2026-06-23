"""Compatibility bridge for runtime-shared symbols.

Modules under ``core``, ``services`` and ``routers`` consume runtime helpers via
this bridge instead of importing ``main`` directly. This keeps import layers
one-way while still supporting test-time monkey-patching on ``main``.
"""

from __future__ import annotations

import importlib
import sys


class _MainRuntimeProxy:
    """Dynamic proxy that resolves to ``main`` when available."""

    def __getattr__(self, name: str):
        module_name = "main" if "main" in sys.modules else "main_runtime"
        module = importlib.import_module(module_name)
        return getattr(module, name)

    def __dir__(self):
        module_name = "main" if "main" in sys.modules else "main_runtime"
        module = importlib.import_module(module_name)
        return sorted(set(super().__dir__() + dir(module)))


def _main_module():
    """Backward-compatible alias retained for extracted modules."""

    return _MainRuntimeProxy()
