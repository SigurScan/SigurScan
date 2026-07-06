from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

CUI_PATTERN = re.compile(
    r"(?:\b(?:CUI|CIF)\s*[:\s]*(?:RO\s*)?(?P<label>\d{2,10})\b|"
    r"\bRO\s*(?P<bare>\d{5,10})\b)",
    re.IGNORECASE,
)
# Bug#9: IBAN-ul RO are lungime fixă de 24 caractere (RO + 2 cifre de control +
# 20 alfanumerice). {20,24} permitea 24-28 caractere total, capturând text de
# după IBAN ca parte din el.
IBAN_PATTERN = re.compile(r"RO\d{2}[A-Z0-9]{20}", re.IGNORECASE)
ANY_IBAN_PATTERN = re.compile(
    r"\b[A-Z]{2}[ \t-]*\d{2}(?:[ \t-]*[A-Z0-9]){11,30}\b",
    re.IGNORECASE,
)
RO_IBAN_OCR_PATTERN = re.compile(
    r"\bR[0O][ \t-]*\d{2}(?:[ \t-]*[A-Z0-9]){20}\b",
    re.IGNORECASE,
)
BENEFICIAR_PATTERN = re.compile(
    r"(?:beneficiar(?:[^\S\n]+(?:plat[ăa]|plata|cont|final))?|"
    r"titular(?:[^\S\n]*cont)?|c[ăa]tre|in[^\S\n]*contul(?:[^\S\n]*lui)?|"
    r"[iî]n[^\S\n]*contul(?:[^\S\n]*lui)?)"
    r"[^\S\n]*[:\-]?[^\S\n]*([^\n\r,;]+)",
    re.IGNORECASE,
)
# Numele băncii tipărit pe factură ("Banca: BRD", "Banca Transilvania",
# "Bank name: ..."). Folosit de bank_name_crosscheck pentru a compara banca
# afișată cu banca implicată de codul IBAN.
BANK_LABEL_PATTERN = re.compile(
    r"\b(?:banc[ăa](?:\s+(?:beneficiar(?:ului)?|emitent(?:ului)?))?|bank(?:\s+name)?)\b"
    r"\s*[:\-]?\s*([^\n\r,;]+)",
    re.IGNORECASE,
)
MONTHS = {
    "january": "01",
    "jan": "01",
    "february": "02",
    "feb": "02",
    "march": "03",
    "mar": "03",
    "april": "04",
    "apr": "04",
    "may": "05",
    "june": "06",
    "jun": "06",
    "july": "07",
    "jul": "07",
    "august": "08",
    "aug": "08",
    "september": "09",
    "sep": "09",
    "sept": "09",
    "october": "10",
    "oct": "10",
    "november": "11",
    "nov": "11",
    "december": "12",
    "dec": "12",
}
CURRENCY_SYMBOLS = {"€": "EUR", "$": "USD", "£": "GBP"}
CURRENCY_PATTERN = re.compile(r"\b(RON|LEI|EUR|USD|GBP)\b|[€$£]", re.IGNORECASE)
# Bug#1 (capătul end-to-end): un număr poate avea grupe de mii separate prin
# punct/virgulă/spațiu (1.260 / 1 500 / 1,234,567) urmate opțional de 2 zecimale.
# Vechiul `\d[\d\s]*(?:[.,]\d{1,2})?` trunchia "1.260" la "1.26" înainte ca
# _parse_ro_amount să apuce să dezambiguizeze separatorul. Întâi forma cu grupe,
# apoi forma simplă; _parse_ro_amount decide RO vs EN pe șirul complet.
_AMOUNT_NUM = r"\d+(?:[.,\s]\d{3})+(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?"
AMOUNT_VALUE_PATTERN = re.compile(
    r"(?:[€$£]\s*(" + _AMOUNT_NUM + r"))"
    r"|(?:(" + _AMOUNT_NUM + r")\s*(?:RON|LEI|lei|EUR|USD|GBP|€|\$|£))",
    re.IGNORECASE,
)
AMOUNT_PATTERN = re.compile(
    r"(?:Total|TVA|Tax|Subtotal|Amount due|Total due|Balance due|Suma|Valoare|Plata|De plata)\s*(?:factur[ai]|plat[iă]|)?[:\s]*"
    r"(" + _AMOUNT_NUM + r")",
    re.IGNORECASE,
)
AMOUNT_WITH_TVA_RATE = re.compile(
    r"(?:TVA|Tax).*?(" + _AMOUNT_NUM + r")\s*(?:RON|LEI|lei|Eur|EUR|USD|GBP|€|\$|£)", re.IGNORECASE
)
AMOUNT_FALLBACK = re.compile(r"(" + _AMOUNT_NUM + r")\s*(?:RON|LEI|lei|Eur|EUR|USD|GBP|€|\$|£)")
DATE_PATTERN = re.compile(
    r"\b(0[1-9]|[12]\d|3[01])[./](0[1-9]|1[0-2])[./](20\d{2})\b"
)
MONTH_DATE_PATTERN = re.compile(
    r"\b("
    r"Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t|tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?"
    r")\s+([0-3]?\d),\s*(20\d{2})\b",
    re.IGNOREC