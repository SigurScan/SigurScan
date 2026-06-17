from __future__ import annotations

import os
import re
from typing import Any, Optional

import requests

from services.provider_budget import consume_monthly_budget, monthly_limit_from_env


HUNTER_IO_DOMAIN_SEARCH_URL = "https://api.hunter.io/v2/domain-search"
HUNTER_IO_TIMEOUT_SECONDS = float(os.getenv("HUNTER_IO_TIMEOUT_SECONDS", "2.5"))
HUNTER_IO_MONTHLY_BUDGET_DEFAULT = 50

EMAIL_RE = re.compile(r"[\w.+%-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
HEADER_RE = re.compile(
    r"(?im)^\s*(?P<label>from|reply-to|return-path|expeditor|raspunde(?:ti)?\s*la|r[ăa]spunde(?:[țt]i)?\s*la)\s*[:\-]\s*(?P<value>.+)$"
)
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
HEAVY_FLAGS = {
    "ACCOUNT_CHANGE_LANGUAGE",
    "BENEFICIARY_PERSON_MISMATCH",
    "BEC_REPLY_TO_ACCOUNT_CHANGE",
    "CEO_CONFIDENTIAL_PAYMENT",
    "FOREIGN_IBAN",
    "HUNTER_DISPOSABLE_EMAIL_DOMAIN",
    "INVOICE_ATTACHMENT_EXECUTABLE",
    "LEGAL_DEMAND_PAYMENT_TO_NEW_IBAN",
    "PAYMENT_DIVERSION_HOLD_INSTRUCTIONS",
    "PAYMENT_LINK_UNKNOWN_PSP",
    "PHISHING_LINK_IN_INVOICE_EMAIL",
    "REMOTE_ACCESS_REQUEST",
    "SENSITIVE_DATA_REQUESTED",
    "URGENT_PAYMENT_OVERRIDE_NO_TICKET",
}


def hunter_io_monthly_budget() -> int:
    return monthly_limit_from_env("HUNTER_IO_MONTHLY_BUDGET", HUNTER_IO_MONTHLY_BUDGET_DEFAULT)


def hunter_io_configured() -> bool:
    return bool(os.getenv("HUNTER_IO_API_KEY", "").strip())


def consume_hunter_io_budget() -> bool:
    decision = consume_monthly_budget(
        "hunter_io_domain_search",
        limit=hunter_io_monthly_budget(),
    )
    return decision.allowed


def evaluate_heavy_email_domain_intel(
    *,
    text: str,
    claimed_vendor: Optional[str] = None,
    fraud_flags: Optional[list[str]] = None,
) -> Optional[dict[str, Any]]:
    flags = set(fraud_flags or [])
    if not (flags & HEAVY_FLAGS):
        return None
    domains = _header_domains(text)
    target_domain = _choose_domain_for_hunter(domains)
    if not target_domain:
        return None
    api_key = os.getenv("HUNTER_IO_API_KEY", "").strip()
    if not api_key:
        return {"provider": "hunter_io", "status": "skipped", "reason": "not_configured"}
    if not consume_hunter_io_budget():
        return {"provider": "hunter_io", "status": "skipped", "reason": "budget_exhausted"}

    try:
        response = requests.get(
            HUNTER_IO_DOMAIN_SEARCH_URL,
            params={"domain": target_domain, "limit": 1},
            headers={"Accept": "application/json", "X-API-KEY": api_key},
            timeout=HUNTER_IO_TIMEOUT_SECONDS,
        )
        if response.status_code in {401, 403}:
            return {"provider": "hunter_io", "status": "error", "reason": "auth_failed", "domain": target_domain}
        if response.status_code == 429:
            return {"provider": "hunter_io", "status": "rate_limited", "domain": target_domain}
        if response.status_code != 200:
            return {"provider": "hunter_io", "status": "error", "reason": "http_error", "domain": target_domain}
        payload = response.json()
    except Exception:
        return {"provider": "hunter_io", "status": "error", "reason": "request_failed", "domain": target_domain}

    return _sanitize_domain_search_payload(payload, target_domain, claimed_vendor=claimed_vendor)


def _domain_from_email(raw: str) -> Optional[str]:
    match = EMAIL_RE.search(raw or "")
    return match.group(1).lower() if match else None


def _header_domains(text: str) -> dict[str, str]:
    domains: dict[str, str] = {}
    for match in HEADER_RE.finditer(text or ""):
        label = match.group("label").lower()
        domain = _domain_from_email(match.group("value"))
        if not domain:
            continue
        if label == "reply-to" or "raspunde" in label or "răspunde" in label:
            domains["reply_to_domain"] = domain
        elif label in {"from", "expeditor"}:
            domains["from_domain"] = domain
        elif label == "return-path":
            domains["return_path_domain"] = domain
    return domains


def _choose_domain_for_hunter(domains: dict[str, str]) -> Optional[str]:
    reply_to = domains.get("reply_to_domain")
    from_domain = domains.get("from_domain")
    if reply_to and reply_to != from_domain and reply_to not in FREE_EMAIL_DOMAINS:
        return reply_to
    if from_domain and from_domain not in FREE_EMAIL_DOMAINS:
        return from_domain
    return None


def _sanitize_domain_search_payload(
    payload: Any,
    domain: str,
    *,
    claimed_vendor: Optional[str] = None,
) -> dict[str, Any]:
    data = payload.get("data") if isinstance(payload, dict) else {}
    data = data if isinstance(data, dict) else {}
    emails = data.get("emails") if isinstance(data.get("emails"), list) else []
    confidences = [
        int(item.get("confidence"))
        for item in emails
        if isinstance(item, dict) and isinstance(item.get("confidence"), int)
    ]
    result_flags: list[str] = []
    warnings: list[str] = []
    if bool(data.get("disposable")):
        result_flags.append("HUNTER_DISPOSABLE_EMAIL_DOMAIN")
        warnings.append("Domeniul de e-mail are semnal de domeniu disposable în Hunter.io.")
    if bool(data.get("webmail")) and domain not in FREE_EMAIL_DOMAINS:
        result_flags.append("HUNTER_WEBMAIL_EMAIL_DOMAIN")
        warnings.append("Domeniul de e-mail pare webmail, deși factura pretinde firmă.")

    return {
        "provider": "hunter_io",
        "status": "checked",
        "domain": str(data.get("domain") or domain).lower(),
        "organization": _safe_text(data.get("organization")),
        "disposable": bool(data.get("disposable")),
        "webmail": bool(data.get("webmail")),
        "accept_all": bool(data.get("accept_all")),
        "pattern_present": bool(data.get("pattern")),
        "email_count": len(emails),
        "max_confidence": max(confidences) if confidences else None,
        "claimed_vendor_present": bool(claimed_vendor),
        "flags": result_flags,
        "warnings": warnings,
    }


def _safe_text(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped[:120] if stripped else None
