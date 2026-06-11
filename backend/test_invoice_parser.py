import pytest

from services.invoice_parser import parse_invoice, _normalize_cui, _parse_ro_amount


class TestNormalizeCui:
    def test_strips_ro_prefix(self):
        assert _normalize_cui("RO12345678") == "12345678"

    def test_strips_ro_with_space(self):
        assert _normalize_cui("RO 12345678") == "12345678"

    def test_already_digits(self):
        assert _normalize_cui("12345678") == "12345678"

    def test_removes_letters(self):
        assert _normalize_cui("RO12A345") == "12345"


class TestParseRoAmount:
    def test_comma_decimal(self):
        assert _parse_ro_amount("119,99") == 119.99

    def test_dot_thousands_comma_decimal(self):
        assert _parse_ro_amount("1.234,56") == 1234.56

    def test_dot_decimal(self):
        assert _parse_ro_amount("119.99") == 119.99

    def test_no_decimals(self):
        assert _parse_ro_amount("119") == 119.0

    def test_with_currency(self):
        assert _parse_ro_amount("119,99 RON") == 119.99

    def test_empty(self):
        assert _parse_ro_amount("") is None

    def test_invalid(self):
        assert _parse_ro_amount("abc") is None


class TestParseInvoice:
    def test_basic_invoice(self):
        text = """
        Furnizor: SC TEST SRL
        CUI: RO12345678
        Factura nr: INV-001
        Data: 01.05.2026
        Scadenta: 01.06.2026
        Total: 119,00 RON
        TVA: 19,00 RON
        Subtotal: 100,00 RON
        IBAN: RO33RNCB1234567890123456
        """
        result = parse_invoice(text)
        assert result.emitent == "SC TEST SRL"
        assert result.cui == "12345678"
        assert result.nr_factura == "INV-001"
        assert result.data_emitere == "2026-05-01"
        assert result.scadenta == "2026-06-01"
        assert result.total == 119.0
        assert result.tva == 19.0
        assert result.subtotal == 100.0
        assert result.iban == "RO33RNCB1234567890123456"

    def test_enel_invoice(self):
        text = """
        Furnizor: ENEL ENERGIE SA
        CUI: 14345906
        Factura: EF-2026-05-001
        Data factura: 15.05.2026
        Scadenta: 15.06.2026
        Total plata: 245,80 lei
        TVA: 39,25 lei
        Valoare: 206,55 lei
        IBAN: RO57BTRL1234567890123456
        """
        result = parse_invoice(text)
        assert result.cui == "14345906"
        assert result.total == 245.80
        assert result.tva == 39.25
        assert result.subtotal == 206.55
        assert result.scadenta == "2026-06-15"

    def test_no_cui(self):
        text = "Total: 100 RON"
        result = parse_invoice(text)
        assert result.cui is None
        assert result.total == 100.0

    def test_no_iban(self):
        text = "CUI: 12345678 Total: 100 RON"
        result = parse_invoice(text)
        assert result.cui == "12345678"
        assert result.iban is None

    def test_empty_text(self):
        result = parse_invoice("")
        assert result.cui is None
        assert result.iban is None
        assert result.raw_text == ""

    def test_with_links(self):
        text = "CUI: 12345678 Total: 100 RON"
        result = parse_invoice(text, pdf_links=["https://enel.ro/factura"], qr_payloads=["https://platibancar.ro"])
        assert result.links == ["https://enel.ro/factura"]
        assert result.qr_payloads == ["https://platibancar.ro"]

    def test_anaf_impersonation_text(self):
        text = """
        Ministerul Finantelor - ANAF
        Amenzi si penalitati
        CUI: 12345678
        Total: 500 RON
        IBAN: RO33RNCB1234567890123456
        """
        result = parse_invoice(text)
        assert result.cui == "12345678"
        assert result.iban == "RO33RNCB1234567890123456"

    def test_emitent_fallback_first_line(self):
        result = parse_invoice("ENEL Energie SA\nCUI: 14345906\nTotal: 100 RON")
        assert result.emitent == "ENEL Energie SA"

    def test_emitent_fallback_skips_date(self):
        result = parse_invoice("15.05.2026\nENEL Energie\nCUI: 14345906\nTotal: 100 RON")
        assert result.emitent == "ENEL Energie"

    def test_nr_factura_seria_slash_nr(self):
        result = parse_invoice("Factura seria FDB25 / nr. 39486801\nTotal: 100 RON")
        assert result.nr_factura == "39486801"

    def test_nr_factura_seria_nr(self):
        result = parse_invoice("Seria ABC Nr. 999\nTotal: 100 RON")
        assert result.nr_factura == "999"
