"""R2 — emitter-zone-aware CUI extraction for multi-CUI invoices.

Conservative: only changes behavior when there are MULTIPLE CUIs AND one sits in
a clear emitter zone. Single-CUI invoices, ambiguous layouts, and the flag being
OFF all keep the current 'first CUI' behavior -- so it can't regress the common
case.
"""

import importlib

import services.invoice_parser as ip

# Client block first (CUI 22222222), then emitter block (CIF 11111111).
CLIENT_FIRST = """Factura seria X nr 5
Client: BETA COMERT SRL
CUI: 22222222
Adresa client: Str. Foo 1

Furnizor: ALFA DISTRIBUTIE SRL
CIF: 11111111
IBAN: RO49 AAAA 1B31 0075 9384 0000
Total: 200 RON
"""

# Emitter first (normal layout).
EMITTER_FIRST = """Furnizor: ALFA DISTRIBUTIE SRL
CIF: 11111111
Client: BETA COMERT SRL
CUI: 22222222
Total: 200 RON
"""

# Two CUIs but no emitter/client zone labels at all.
NO_ZONE = "Factura\nCUI 22222222\nceva\nCIF 11111111\nTotal 50"

SINGLE = "Furnizor: ALFA SRL\nCIF: 11111111\nTotal 100"


def _cui(text, flag, monkeypatch):
    if flag is None:
        monkeypatch.delenv("INVOICE_ZONE_CUI", raising=False)
    else:
        monkeypatch.setenv("INVOICE_ZONE_CUI", flag)
    importlib.reload(ip)
    try:
        return ip._extract_cui_zone_aware(text)
    finally:
        monkeypatch.delenv("INVOICE_ZONE_CUI", raising=False)
        importlib.reload(ip)


def test_off_keeps_first_cui_behavior(monkeypatch):
    assert _cui(CLIENT_FIRST, None, monkeypatch) == "22222222"  # first = client (unchanged)


def test_on_prefers_emitter_zone_cui(monkeypatch):
    assert _cui(CLIENT_FIRST, "1", monkeypatch) == "11111111"  # emitter zone


def test_emitter_first_layout_unchanged_both_modes(monkeypatch):
    assert _cui(EMITTER_FIRST, None, monkeypatch) == "11111111"
    assert _cui(EMITTER_FIRST, "1", monkeypatch) == "11111111"


def test_single_cui_identical_both_modes(monkeypatch):
    assert _cui(SINGLE, None, monkeypatch) == "11111111"
    assert _cui(SINGLE, "1", monkeypatch) == "11111111"


def test_no_zone_labels_falls_back_to_first(monkeypatch):
    # Ambiguous: two CUIs, no emitter/client labels -> conservative first-CUI.
    assert _cui(NO_ZONE, "1", monkeypatch) == _cui(NO_ZONE, None, monkeypatch)
