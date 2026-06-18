import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.invoice_parser import InvoiceFields
from services.efactura_xml import compare_invoice_to_official_xml, parse_efactura_xml
import services.efactura_xml as efactura_xml


EFACTURA_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cbc:ID>MGH 0013</cbc:ID>
  <cbc:IssueDate>2022-04-06</cbc:IssueDate>
  <cbc:DueDate>2022-04-07</cbc:DueDate>
  <cac:AccountingSupplierParty>
    <cac:Party>
      <cac:PartyName><cbc:Name>MARKETING GROWTH HUB S.R.L.</cbc:Name></cac:PartyName>
      <cac:PartyTaxScheme><cbc:CompanyID>RO45758405</cbc:CompanyID></cac:PartyTaxScheme>
    </cac:Party>
  </cac:AccountingSupplierParty>
  <cac:PaymentMeans>
    <cac:PayeeFinancialAccount><cbc:ID>RO49AAAA1B31007593840000</cbc:ID></cac:PayeeFinancialAccount>
  </cac:PaymentMeans>
  <cac:LegalMonetaryTotal>
    <cbc:PayableAmount currencyID="RON">200.00</cbc:PayableAmount>
  </cac:LegalMonetaryTotal>
</Invoice>
"""

EFACTURA_XML_MATCHING_IBAN = EFACTURA_XML.replace(
    b"RO49AAAA1B31007593840000",
    b"RO42INGB0000999912242622",
)


def test_parse_efactura_xml_extracts_supplier_payment_and_total():
    fields = parse_efactura_xml(EFACTURA_XML)

    assert fields.emitent == "MARKETING GROWTH HUB S.R.L."
    assert fields.cui == "45758405"
    assert fields.nr_factura == "MGH 0013"
    assert fields.data_emitere == "06.04.2022"
    assert fields.scadenta == "07.04.2022"
    assert fields.iban == "RO49AAAA1B31007593840000"
    assert fields.total == 200.0
    assert fields.currency == "RON"


def test_efactura_xml_uses_defusedxml_parser():
    assert efactura_xml.ET.__name__ == "defusedxml.ElementTree"


def test_compare_invoice_to_official_xml_flags_decisive_mismatches():
    scanned = InvoiceFields(
        emitent="MARKETING GROWTH HUB S.R.L.",
        cui="45758405",
        nr_factura="MGH 0013",
        data_emitere="06.04.2022",
        scadenta="07.04.2022",
        iban="RO42INGB0000999912242622",
        total=200.0,
        currency="RON",
    )
    official = parse_efactura_xml(EFACTURA_XML)

    check = compare_invoice_to_official_xml(scanned, official)

    assert check["provided"] is True
    assert check["status"] == "mismatch"
    assert check["risk_flag"] == "EFACTURA_OFFICIAL_DOCUMENT_MISMATCH"
    assert {
        "field": "iban",
        "invoice_value": "RO42INGB0000999912242622",
        "official_value": "RO49AAAA1B31007593840000",
        "severity": "high",
    } in check["mismatches"]
    assert "cui" in check["matched_fields"]


def test_compare_invoice_to_official_xml_matching_document_has_no_risk_flag():
    scanned = InvoiceFields(
        emitent="MARKETING GROWTH HUB S.R.L.",
        cui="45758405",
        nr_factura="MGH 0013",
        data_emitere="06.04.2022",
        scadenta="07.04.2022",
        iban="RO42INGB0000999912242622",
        total=200.0,
        currency="RON",
    )
    official = parse_efactura_xml(EFACTURA_XML_MATCHING_IBAN)

    check = compare_invoice_to_official_xml(scanned, official)

    assert check["status"] == "match"
    assert check["risk_flag"] is None
    assert check["mismatches"] == []
    assert {"cui", "iban", "total", "nr_factura", "data_emitere", "scadenta"} <= set(check["matched_fields"])
