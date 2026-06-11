from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

# Standard RO VAT rates (including reduced and exempt).
PLAUSIBLE_VAT_RATES = {0, 5, 9, 11, 19, 21}

TOTAL_TOLERANCE = 0.05


@dataclass
class CoherenceResult:
    totals_match: bool
    tva_rate_plausible: bool
    dates_plausible: bool
    all_ok: bool


def check_coherence(
    subtotal: float | None,
    tva: float | None,
    total: float | None,
    data_emitere: str | None,
    scadenta: str | None,
) -> CoherenceResult:
    totals_match = _check_totals(subtotal, tva, total)
    tva_rate_plausible = _check_tva_rate(subtotal, tva) if subtotal is not None and tva is not None else True
    dates_plausible = _check_dates(data_emitere, scadenta)
    return CoherenceResult(
        totals_match=totals_match,
        tva_rate_plausible=tva_rate_plausible,
        dates_plausible=dates_plausible,
        all_ok=totals_match and tva_rate_plausible and dates_plausible,
    )


def _check_totals(subtotal: float | None, tva: float | None, total: float | None) -> bool:
    if subtotal is None and total is None:
        return True
    if subtotal is not None and total is not None and tva is not None:
        return abs(subtotal + tva - total) <= TOTAL_TOLERANCE
    if subtotal is not None and total is not None:
        return total >= subtotal
    return True


def _check_tva_rate(subtotal: float, tva: float) -> bool:
    if subtotal == 0:
        return True
    rate = round((tva / subtotal) * 100, 1)
    return any(abs(rate - r) <= 1.5 for r in PLAUSIBLE_VAT_RATES)


def _parse_iso(value: str | None) -> date | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def _check_dates(data_emitere: str | None, scadenta: str | None) -> bool:
    if data_emitere is None and scadenta is None:
        return True
    emitere = _parse_iso(data_emitere)
    scad = _parse_iso(scadenta)
    if emitere is not None and scad is not None:
        return emitere <= scad
    return True
