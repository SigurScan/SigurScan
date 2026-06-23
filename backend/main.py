"""Backward-compatibility module for legacy ``main`` imports."""

from __future__ import annotations

from app import app, create_app
import main_runtime as _main_runtime

# Keep the canonical FastAPI application object from `app.py` (not the compatibility
# shim app that also exists inside `main_runtime`).
app = app
create_app = create_app

for _name, _value in vars(_main_runtime).items():
    if _name.startswith("__"):
        continue
    if _name in {"app", "create_app"}:
        continue
    globals()[_name] = _value

del _main_runtime
