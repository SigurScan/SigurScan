from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any, Iterable, Optional

from services.invoice_parser import IBAN_PATTERN, InvoiceFields, _normalize_cui, _parse_ro_amount


class EFacturaXmlError(ValueError):
    pass


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def _children_named(node: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in list(node) if _local_name(child.tag) == name]


def _descendants_named(node: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in node.iter() if _local_name(child.tag) == name]


def _first_text(nodes: Iterable[ET.Element]) -> Optional[str]:
    for node in nodes:
        value = (node.text or "").strip()
        if value:
            return value
    return None


def _first_descendant_text(node: ET.Element, *names: str) -> Optional[str]:
    wanted = set(names)
    return _first_text(child for child in node.iter() if _local_name(child.tag) in wanted)


def _first_section(root: ET.Element, name: str) -> Optional[ET.Element]:
    for child in root.iter():
        if _local_name(child.tag) == name:
            return child
    return None


def _format_xml_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    text = value.strip()
    match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", text)
    if match:
        return f"{match.group(3)}.{match.group(2)}.{match.group(1)}"
    return text


def _extract_supplier(root: ET.Element) -> tuple[Optional[str], Optional[str]]:
    supplier = _first_section(root, "AccountingSupplierParty")
    if supplier is None:
        return None, None

    name = None
    party_name = _first_section(supplier, "PartyName")
    if party_name is not None:
        name = _first_descendant_text(party_name, "Name")
    if not name:
        legal_entity = _first_section(supplier, "PartyLegalEntity")
        if legal_entity is not None:
            name = _first_descendant_text(legal_entity, "RegistrationName")

    cui = None
    for section_name in ("PartyTaxScheme", "PartyLegalEntity", "PartyIdentification"):
        section = _first_section(supplier, section_name)
        if section is None:
            continue
        raw_cui = _first_descendant_text(section, "CompanyID", "ID", "EndpointID")
        if raw_cui:
            digits = _normalize_cui(raw_cui)
            if 2 <= len(digits) <= 10:
                cui = digits
                break
    return name, cui


def _extract_payment_iban(root: ET.Element) -> Optional[str]:
    for account in _descendants_named(root, "PayeeFinancialAccount"):
        raw_iban = _first_descendant_text(account, "ID")
        if raw_iban:
            match = IBAN_PATTERN.search(raw_iban.replace(" ", ""))
            if match:
                return match.group(0).upper()

    raw_xml_text = ET.tostring(root, encoding="unicode", method="text")
    match = IBAN_PATTERN.search(raw_xml_text.replace(" ", ""))
    return match.group(0).upper() if match else None


def _extract_payable_amount(root: ET.Element) -> tuple[Optional[float], Optional[str]]:
    amount_nodes: list[ET.Element] = []
    monetary_total = _first_section(root, "LegalMonetaryTotal")
    if monetary_total is not None:
        amount_nodes.extend(_descendants_named(monetary_total, "PayableAmount"))
    amount_nodes.extend(_descendants_named(root, "PayableAmount"))

    for node in amount_nodes:
        amount = _parse_ro_amount((node.text or "").strip())
        if amount is None:
            continue
        currency = None
        for key, value in node.attrib.items():
            if _local_name(key) == "currencyID" and value:
                currency = value.upper()
                break
        return amount, currency
    return None, None


def parse_efactura_xml(xml_bytes: bytes) -> InvoiceFields:
    if not xml_bytes:
        raise EFacturaXmlError("XML-ul oficial este gol.")
    head = xml_bytes[:512].decode("utf-8", errors="ignore").lower()
    if "<!doctype" in head or "<!entity" in head:
        raise EFacturaXmlError("XML-ul conține DOCTYPE/ENTITY și nu poate fi procesat sigur.")
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise EFacturaXmlError("XML-ul oficial nu este valid.") from exc

    emitent, cui = _extract_supplier(root)
    total, currency = _extract_payable_amount(root)
    invoice_id = _first_text(_children_named(root, "ID")) or _first_descendant_text(root, "ID")
    issue_date = _format_xml_date(_first_text(_children_named(root, "IssueDate")))
    due_date = _format_xml_date(_first_text(_children_named(root, "DueDate")))
    iban = _extract_payment_iban(root)

    return InvoiceFields(
        emitent=emitent,
        cui=cui,
        nr_factura=invoice_id,
        data_emitere=issue_date,
        scadenta=due_date,
        total=total,
        currency=currency,
        iban=iban,
        all_ibans=[iban] if iban else [],
        raw_text=ET.tostring(root, encoding="unicode", method="text"),
    )


def _norm_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return re.sub(r"\s+", " ", str(value).strip()).upper() or None


def _norm_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    text = value.strip()
    match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", text)
    if match:
        return f"{match.group(3)}.{match.group(2)}.{match.group(1)}"
    return text


def _field_dict(fields: InvoiceFields) -> dict[str, Any]:
    return {
        "emitent": fields.emitent,
        "cui": fields.cui,
        "nr_factura": fields.nr_factura,
        "data_emitere": fields.data_emitere,
        "scadenta": fields.scadenta,
        "iban": fields.iban,
        "total": fields.total,
        "currency": fields.currency,
    }


def compare_invoice_to_official_xml(invoice: InvoiceFields, official: InvoiceFields) -> dict[str, Any]:
    comparisons = {
        "cui": ("high", lambda left, right: _normalize_cui(str(left)) == _normalize_cui(str(right))),
        "iban": ("high", lambda left, right: _norm_text(left) == _norm_text(right)),
        "total": ("high", lambda left, right: abs(float(left) - float(right)) <= 0.01),
        "nr_factura": ("medium", lambda left, right: _norm_text(left) == _norm_text(right)),
        "data_emitere": ("medium", lambda left, right: _norm_date(str(left)) == _norm_date(str(right))),
        "scadenta": ("medium", lambda left, right: _norm_date(str(left)) == _norm_date(str(right))),
    }
    mismatches: list[dict[str, Any]] = []
    matched_fields: list[str] = []
    missing_official_fields: list[str] = []

    for field, (severity, comparator) in comparisons.items():
        invoice_value = getattr(invoice, field, None)
        official_value = getattr(official, field, None)
        if official_value in (None, ""):
            missing_official_fields.append(field)
            continue
        if invoice_value in (None, ""):
            continue
        try:
            matches = comparator(invoice_value, official_value)
        except Exception:
            matches = False
        if matches:
            matched_fields.append(field)
        else:
            mismatches.append(
                {
                    "field": field,
                    "invoice_value": invoice_value,
                    "official_value": official_value,
                    "severity": severity,
                }
            )

    has_high_mismatch = any(item["severity"] == "high" for item in mismatches)
    status = "mismatch" if mismatches else "match" if matched_fields else "insufficient_data"
    return {
        "provided": True,
        "status": status,
        "risk_flag": "EFACTURA_OFFICIAL_DOCUMENT_MISMATCH" if has_high_mismatch else None,
        "mismatches": mismatches,
        "matched_fields": matched_fields,
        "missing_official_fields": missing_official_fields,
        "official_fields": _field_dict(official),
    }
