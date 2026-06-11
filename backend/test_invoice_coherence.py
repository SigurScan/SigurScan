import pytest

from services.invoice_coherence import check_coherence


def test_totals_match_perfect():
    result = check_coherence(subtotal=100.0, tva=19.0, total=119.0, data_emitere="2026-05-01", scadenta="2026-06-01")
    assert result.totals_match is True
    assert result.all_ok is True


def test_totals_match_with_tolerance():
    result = check_coherence(subtotal=100.0, tva=19.0, total=119.03, data_emitere="2026-05-01", scadenta="2026-06-01")
    assert result.totals_match is True


def test_totals_mismatch():
    result = check_coherence(subtotal=100.0, tva=19.0, total=150.0, data_emitere="2026-05-01", scadenta="2026-06-01")
    assert result.totals_match is False
    assert result.all_ok is False


def test_tva_rate_19():
    result = check_coherence(subtotal=100.0, tva=19.0, total=119.0, data_emitere="2026-05-01", scadenta="2026-06-01")
    assert result.tva_rate_plausible is True


def test_tva_rate_9():
    result = check_coherence(subtotal=100.0, tva=9.0, total=109.0, data_emitere="2026-05-01", scadenta="2026-06-01")
    assert result.tva_rate_plausible is True


def test_tva_rate_implausible():
    result = check_coherence(subtotal=100.0, tva=37.0, total=137.0, data_emitere="2026-05-01", scadenta="2026-06-01")
    assert result.tva_rate_plausible is False


def test_dates_plausible():
    result = check_coherence(subtotal=100.0, tva=19.0, total=119.0, data_emitere="2026-05-01", scadenta="2026-06-01")
    assert result.dates_plausible is True


def test_dates_implausible():
    result = check_coherence(subtotal=100.0, tva=19.0, total=119.0, data_emitere="2026-06-01", scadenta="2026-05-01")
    assert result.dates_plausible is False


def test_missing_subtotal_and_total():
    result = check_coherence(subtotal=None, tva=None, total=None, data_emitere="2026-05-01", scadenta="2026-06-01")
    assert result.totals_match is True
    assert result.all_ok is True


def test_missing_dates():
    result = check_coherence(subtotal=100.0, tva=19.0, total=119.0, data_emitere=None, scadenta=None)
    assert result.dates_plausible is True
    assert result.all_ok is True


def test_ro_date_format():
    result = check_coherence(subtotal=100.0, tva=19.0, total=119.0, data_emitere="01.05.2026", scadenta="01.06.2026")
    assert result.dates_plausible is True
    assert result.all_ok is True


def test_tva_zero():
    result = check_coherence(subtotal=100.0, tva=0.0, total=100.0, data_emitere="2026-05-01", scadenta="2026-06-01")
    assert result.tva_rate_plausible is True
    assert result.totals_match is True
