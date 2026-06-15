from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse


FREE_EMAIL_DOMAINS = {
    "gmail.com",
    "googlemail.com",
    "yahoo.com",
    "yahoo.ro",
    "outlook.com",
    "hotmail.com",
    "live.com",
    "icloud.com",
    "proton.me",
    "protonmail.com",
}

KNOWN_PAYMENT_OR_PSP_DOMAINS = {
    "stripe.com",
    "checkout.stripe.com",
    "paypal.com",
    "www.paypal.com",
    "euplatesc.ro",
    "secure.euplatesc.ro",
    "mobilpay.ro",
    "netopia-payments.com",
    "payu.ro",
    "payu.com",
    "revolut.com",
    "business.revolut.com",
    "bancatransilvania.ro",
    "www.bancatransilvania.ro",
    "ghiseul.ro",
    "www.ghiseul.ro",
}

EMAIL_HEADER_RE = re.compile(
    r"(?im)^\s*(?P<label>from|reply-to|return-path|expeditor|raspunde(?:ti)?\s*la|r[ăa]spunde(?:[țt]i)?\s*la)\s*[:\-]\s*(?P<value>.+)$"
)
EMAIL_RE = re.compile(r"[\w.+%-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
URL_RE = re.compile(r"https?://[^\s<>()\"']+", re.IGNORECASE)
ANCHOR_RE = re.compile(
    r"""<a\b[^>]*\bhref=["'](?P<href>https?://[^"']+)["'][^>]*>(?P<label>.*?)</a>""",
    re.IGNORECASE | re.DOTALL,
)
ACCOUNT_CHANGE_RE = re.compile(
    r"(cont(?:ul)?\s+(?:nou|modificat|actualizat|schimbat)|iban(?:ul)?\s+(?:nou|modificat|actualizat|schimbat)|"
    r"schimbat\s+cont(?:ul)?|modificat\s+cont(?:ul)?|actualizat\s+cont(?:ul)?|"
    r"new\s+(?:bank\s+)?account|changed\s+(?:bank\s+)?account)",
    re.IGNORECASE,
)
CONFIDENTIAL_PAYMENT_RE = re.compile(
    r"(?=.*\b(?:ceo|director(?:ul)?|administrator(?:ul)?|manager(?:ul)?|patron(?:ul)?|sef(?:ul)?|șef(?:ul)?)\b)"
    r"(?=.*\b(?:confiden[țt]ial|secret|nu\s+suna|nu\s+m[ăa]\s+contacta|nu\s+discuta|discret)\b)"
    r"(?=.*\b(?:plat[ăa]|pl[ăa]te[șs]te|transfer|iban|cont|virament)\b)",
    re.IGNORECASE | re.DOTALL,
)
REMOTE_ACCESS_RE = re.compile(
    r"\b(?:anydesk|any\s*desk|teamviewer|team\s*viewer|rustdesk|remote\s*access|"
    r"acces\s*la\s*distan[țt][ăa]|control\s+la\s+distan[țt][ăa])\b",
    re.IGNORECASE,
)
EF_ACTURA_CLAIM_RE = re.compile(r"\b(?:e[-\s]?factura|spv|xml)\b", re.IGNORECASE)
EF_ACTURA_PROOF_RE = re.compile(
    r"\b(?:xml\s+(?:ata[șs]at|atasat|semnat|validat)|hash\s+xml|id\s+(?:incarcare|încărcare)|"
    r"sigiliu|semn[ăa]tur[ăa]\s+electronic[ăa])\b",
    re.IGNORECASE,
)
ARCHIVE_OR_MACRO_RE = re.compile(
    r"\.(?:zip|rar|7z|exe|scr|js|vbs|bat|cmd|docm|xlsm)\b|\bmacro(?:uri)?\b",
    re.IGNORECASE,
)
PAYMENT_LINK_RE = re.compile(r"\b(?:achit[ăa]|pl[ăa]te[șs]te|payment|checkout|pay|link\s+de\s+plat[ăa])\b", re.IGNORECASE)
PAYMENT_OR_INVOICE_CONTEXT_RE = re.compile(
    r"\b(?:factur[ăa]|pl[ăa]t|achit|transfer|iban|cont|virament|proform[ăa])\b",
    re.IGNORECASE,
)
COMPANY_MARKER_RE = re.compile(r"\b(?:s\.?\s?r\.?\s?l|s\.?\s?a|pfa|i\.?\s?i|cui|cif|factur[ăa])\b", re.IGNORECASE)


@dataclass
class B2BSignalResult:
    flags: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


def _add(result: B2BSignalResult, flag: str, warning: Optional[str] = None) -> None:
    if flag not in result.flags:
        result.flags.append(flag)
    if warning and warning not in result.warnings:
        result.warnings.append(warning)


def _domain_from_email(raw: str) -> Optional[str]:
    match = EMAIL_RE.search(raw or "")
    return match.group(1).lower() if match else None


def _header_domains(text: str) -> dict[str, str]:
    domains: dict[str, str] = {}
    for match in EMAIL_HEADER_RE.finditer(text or ""):
        label = match.group("label").lower()
        value = match.group("value")
        domain = _domain_from_email(value)
        if not domain:
            continue
        if label in {"reply-to", "raspunde la", "raspundeti la", "răspunde la", "răspundeți la"}:
            domains["reply_to_domain"] = domain
        elif label in {"from", "expeditor"}:
            domains["from_domain"] = domain
        elif label == "return-path":
            domains["return_path_domain"] = domain
    return domains


def _host(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower().removeprefix("www.")
    except Exception:
        return ""


def _domain_like_url(text: str) -> Optional[str]:
    match = URL_RE.search(text or "")
    return _host(match.group(0)) if match else None


def _looks_unknown_payment_link(text: str) -> Optional[str]:
    for raw_url in URL_RE.findall(text or ""):
        host = _host(raw_url)
        if not host or host in {d.removeprefix("www.") for d in KNOWN_PAYMENT_OR_PSP_DOMAINS}:
            continue
        url_context = raw_url.lower()
        surrounding = text[max(0, text.find(raw_url) - 80) : text.find(raw_url) + len(raw_url) + 80]
        if PAYMENT_LINK_RE.search(url_context) or PAYMENT_LINK_RE.search(surrounding):
            return host
    return None


def _anchor_display_mismatch(text: str) -> Optional[dict]:
    for match in ANCHOR_RE.finditer(text or ""):
        href_host = _host(match.group("href"))
        label_host = _domain_like_url(re.sub(r"<[^>]+>", "", match.group("label")))
        if href_host and label_host and href_host != label_host:
            return {"href_host": href_host, "label_host": label_host}
    return None


def evaluate_b2b_invoice_signals(text: str, *, claimed_vendor: Optional[str] = None) -> B2BSignalResult:
    result = B2BSignalResult()
    raw = text or ""
    domains = _header_domains(raw)
    result.metadata.update(domains)

    from_domain = domains.get("from_domain")
    reply_to_domain = domains.get("reply_to_domain")
    if from_domain and reply_to_domain and from_domain != reply_to_domain:
        _add(
            result,
            "REPLY_TO_MISMATCH",
            "Reply-To diferă de domeniul expeditorului; confirmă plata pe un canal cunoscut.",
        )

    looks_company = bool(COMPANY_MARKER_RE.search(raw) or claimed_vendor)
    if looks_company and from_domain in FREE_EMAIL_DOMAINS:
        _add(
            result,
            "FREE_EMAIL_FOR_COMPANY_INVOICE",
            "Factura pretinde firmă, dar expeditorul este un domeniu gratuit de e-mail.",
        )

    if CONFIDENTIAL_PAYMENT_RE.search(raw):
        _add(
            result,
            "CEO_CONFIDENTIAL_PAYMENT",
            "Mesajul combină autoritate, confidențialitate și cerere de plată.",
        )

    if REMOTE_ACCESS_RE.search(raw) and PAYMENT_OR_INVOICE_CONTEXT_RE.search(raw):
        _add(
            result,
            "REMOTE_ACCESS_REQUEST",
            "Factura/mesajul cere acces la distanță; nu instala și nu permite controlul dispozitivului.",
        )

    if EF_ACTURA_CLAIM_RE.search(raw) and not EF_ACTURA_PROOF_RE.search(raw):
        _add(
            result,
            "EFACTURA_CLAIM_WITHOUT_DOCUMENT",
            "Textul invocă e-Factura/SPV, dar nu conține dovadă XML/semnătură verificabilă.",
        )

    if ARCHIVE_OR_MACRO_RE.search(raw):
        _add(
            result,
            "INVOICE_ATTACHMENT_EXECUTABLE",
            "Atașamentul menționat este arhivă/executabil/macro, risc ridicat pentru facturi false.",
        )

    unknown_payment_host = _looks_unknown_payment_link(raw)
    if unknown_payment_host:
        result.metadata["unknown_payment_host"] = unknown_payment_host
        _add(
            result,
            "PAYMENT_LINK_UNKNOWN_PSP",
            "Linkul de plată nu aparține unui procesator sau canal cunoscut.",
        )

    mismatch = _anchor_display_mismatch(raw)
    if mismatch:
        result.metadata["anchor_mismatch"] = mismatch
        _add(
            result,
            "PHISHING_LINK_IN_INVOICE_EMAIL",
            "Linkul afișat și destinația reală din e-mail nu coincid.",
        )

    if ACCOUNT_CHANGE_RE.search(raw) and reply_to_domain and from_domain and reply_to_domain != from_domain:
        _add(
            result,
            "BEC_REPLY_TO_ACCOUNT_CHANGE",
            "Schimbare de cont bancar plus Reply-To diferit: tipar puternic de fraudă BEC.",
        )

    return result
