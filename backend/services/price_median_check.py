"""D7 — 'too good to be true' price check vs a static market-median dataset.

Classic scam tell: a high-value product (iPhone, PS5, Dyson, ...) offered far
below its street price. This matches the offered product against a small, curated
median dataset and flags an implausibly low price as a SOFT signal (contributes to
SUSPECT / verify, never a standalone DANGEROUS — see offer_evidence_gate_mapper).

Conservative by design:
- only well-known high-value products (broad categories omitted, so legit
  discounts on ordinary goods are never flagged);
- on multiple matches, uses the LOWEST median (most lenient floor) to minimise FP;
- RON only; needs a positive price; hard-gated by D7_PRICE_MEDIAN (default OFF).
Best-effort: any error yields None, never raises.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

_BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_PATH = _BACKEND_DIR / "data" / "market_medians_ro_v1.json"


def is_enabled() -> bool:
    return os.getenv("D7_PRICE_MEDIAN", "0").strip().lower() in {"1", "true", "yes", "on"}


def _dataset_path() -> Path:
    override = os.getenv("D7_MEDIAN_DATASET_PATH")
    return Path(override) if override else DEFAULT_DATASET_PATH


@lru_cache(maxsize=2)
def _load(path_str: str) -> Dict[str, Any]:
    return json.loads(Path(path_str).read_text(encoding="utf-8"))


def _match_lowest_median(text_lower: str, dataset: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    best: Optional[Dict[str, Any]] = None
    default_ratio = float(dataset.get("default_floor_ratio") or 0.35)
    for product in dataset.get("products") or []:
        patterns = product.get("patterns") or []
        if any(p in text_lower for p in patterns):
            if best is None or float(product["median_ron"]) < float(best["median_ron"]):
                best = {
                    "key": product.get("key"),
                    "median_ron": float(product["median_ron"]),
                    "floor_ratio": float(product.get("floor_ratio") or default_ratio),
                }
    return best


def too_cheap_signal(text: Optional[str], total_amount: Any, currency: Optional[str]) -> Optional[Dict[str, Any]]:
    """Return {product, median_ron, floor_ron, offered_ron} when the price is
    implausibly below the matched product's median, else None."""
    if not is_enabled() or not text:
        return None
    try:
        if str(currency or "RON").strip().upper() != "RON":
            return None
        price = float(total_amount)
        if price <= 0:
            return None
        dataset = _load(str(_dataset_path()))
        match = _match_lowest_median(str(text).lower(), dataset)
        if not match:
            return None
        floor = match["median_ron"] * match["floor_ratio"]
        if price < floor:
            return {
                "product": match["key"],
                "median_ron": match["median_ron"],
                "floor_ron": round(floor, 2),
                "offered_ron": price,
            }
    except Exception:
        return None
    return None
