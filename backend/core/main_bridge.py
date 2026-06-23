"""Centralized compatibility bridge to legacy ``main`` module exports.

All extracted modules should resolve runtime globals through this helper instead of
repeating ``import main as _main`` blocks.
"""

from __future__ import annotations

import importlib


def get_main_module():
    """Return the main compatibility module as a single import point."""

    return importlib.import_module("main")


def _main_module():
    """Backward-compatible alias retained for extracted modules."""

    return get_main_module()
