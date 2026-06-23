"""Compatibility bridge to runtime module.

Modules that need runtime globals/helpers use this single helper instead of importing
`main` directly.
"""

from __future__ import annotations

import importlib


def get_runtime_module():
    """Return the shared runtime module as a single import point."""

    return importlib.import_module("main_runtime")


def _main_module():
    """Backward-compatible alias retained for extracted modules."""

    return get_runtime_module()
