"""Provider-gate helpers extracted from ``runtime.py``."""

from __future__ import annotations

import re
import urllib.parse
from typing import Any, Dict, List, Optional

from core.serialization import _deep_copy_jsonable
from core.text_utils import _normalise_obfuscated_text
from core.url_intelligence import _data_url_contains_sensitive_form
from runtime_state import engine
from services import dns_reputation
from services.scam_atlas import BRAND_ID_TO_DISPLAY_NAME, BRAND_WARNING_RULES
from services.verdict_gate import verdict as reduce_verdict
from app_stores import brand_truth_registry
from config import DOMAIN_ESTABLISHED_AGE_DAYS, DOMAIN_SUSPICIOUS_AGE_DAYS, ENABLE_DNS_REPUTATION





def _source_status_impl(summary: Dict[str, Any], source_name: str) -> str:
    raw = summary.get(source_name)
    if not isinstance(raw, dict):
        return "missing"
    return str(raw.get("verdict") or raw.get("status") or "unknown").strip().lower()


def _source_consulted_impl(summary: Dict[str, Any], source_name: str) -> bool:
    raw = summary.get(source_name)
    return bool(isinstance(raw, dict) and raw.get("consulted", False))


def _source_ready(summary: Dict[str, Any], source_name: str) -> bool:
    return _source_ready_impl(summary, source_name)


def _source_ready_impl(summary: Dict[str, Any], source_name: str) -> bool:
    status = _source_status(summary, source_name)
    return _source_consulted(summary, source_name) and status not in {"missing", "unknown", "error"}


def _normalize_claimed_brand(raw_brand: str) -> str:
    normalized = str(raw_brand or "").strip().lower()
    if not normalized or normalized in {"nespecificat", "unknown", "none"}:
        return ""
    return normalized


def _compact_brand_match_token(raw: str) -> str:
    text = _normalise_obfuscated_text(str(raw or "")).lower()
    return re.sub(r"[^a-z0-9]+", "", text)


def _first_final_url(resolved_urls: List[Dict[str, Any]]) -> Optional[str]:
    for entry in resolved_urls:
        final_url = entry.get("final_url") or entry.get("url") or entry.get("original_url")
        if isinstance(final_url, str) and final_url.strip():
            return final_url.strip()
    return None


def _first_domain_age_days(resolved_urls: List[Dict[str, Any]]) -> Optional[int]:
    for entry in resolved_urls or []:
        if not isinstance(entry, dict):
            continue
        try:
            value = entry.get("domain_age_days")
            if value is not None:
                return int(value)
        except (TypeError, ValueError):
            continue
    return None


def _domain_reputation_from_age(age_days: Optional[int]) -> str:
    if age_days is None:
        return "unknown"
    if age_days >= DOMAIN_ESTABLISHED_AGE_DAYS:
        return "established"
    if age_days >= DOMAIN_SUSPICIOUS_AGE_DAYS:
        return "age_unknown"
    return "young"


def _official_destination_confirmed_impl(
    resolved_urls: List[Dict[str, Any]],
    claimed_brand: str,
) -> bool:
    saw_allowed_destination = False
    for entry in resolved_urls:
        reg_domain = str(entry.get("final_registered_domain") or entry.get("registered_domain") or "").lower()
        hostname = str(entry.get("final_hostname") or entry.get("hostname") or "").lower()
        final_url = str(entry.get("final_url") or entry.get("url") or "")
        if not hostname and final_url:
            hostname = urllib.parse.urlparse(final_url).hostname or ""
        normalized_claim = _normalize_claimed_brand(claimed_brand)
        if normalized_claim:
            destination_allowed = engine._is_brand_allowed_domain(
                claimed_brand,
                reg_domain,
                hostname=hostname,
                url=final_url,
            )
        else:
            destination_allowed = engine._is_context_allowed_domain(
                reg_domain,
                hostname=hostname,
                claimed_brand=None,
                url=final_url,
            )
        if destination_allowed:
            saw_allowed_destination = True
            continue

        original_hostname = str(entry.get("hostname") or "").lower()
        original_reg_domain = str(entry.get("registered_domain") or "").lower()
        original_url = str(entry.get("url") or "")
        if not original_hostname and original_url:
            original_hostname = urllib.parse.urlparse(original_url).hostname or ""
        original_is_brand_delegated = engine._is_context_allowed_domain(
            original_reg_domain,
            hostname=original_hostname,
            claimed_brand=claimed_brand,
            url=original_url,
        )
        final_url = str(entry.get("final_url") or entry.get("url") or "")
        compact_brand = _compact_brand_match_token(_normalize_claimed_brand(claimed_brand))
        compact_domain = _compact_brand_match_token(reg_domain or hostname)
        try:
            age_days = int(entry.get("domain_age_days")) if entry.get("domain_age_days") is not None else None
        except (TypeError, ValueError):
            age_days = None
        suspicious_unofficial = bool(
            entry.get("uses_shortener")
            or (age_days is not None and age_days < DOMAIN_SUSPICIOUS_AGE_DAYS)
            or reg_domain.endswith((".top", ".xyz", ".click", ".work", ".quest", ".icu", ".shop"))
            or (compact_brand and compact_brand in compact_domain)
            or any(token in final_url.lower() for token in ("login", "auth", "card", "pay", "plata", "anulare", "confirm"))
        )
        if suspicious_unofficial:
            return False
    return saw_allowed_destination


def _official_destination_confirmed(
    resolved_urls: List[Dict[str, Any]],
    claimed_brand: str,
) -> bool:
    return _official_destination_confirmed_impl(
resolved_urls,
        claimed_brand,

    )


def _collect_infrastructure_flags_impl(
    analysis: Dict[str, Any],
    resolved_urls: List[Dict[str, Any]],
    *,
    official_destination: bool = False,
) -> Dict[str, Any]:
    evidence = analysis.get("evidence", {}) if isinstance(analysis.get("evidence"), dict) else {}
    lexical_evidence = evidence.get("url_lexical") if isinstance(evidence.get("url_lexical"), dict) else {}
    lexical_text = " ".join(str(item) for item in lexical_evidence.get("reasons", []) if item).lower()
    extracted_urls = evidence.get("extracted_urls") if isinstance(evidence.get("extracted_urls"), list) else resolved_urls
    url_behaviour = evidence.get("url_behaviour") if isinstance(evidence.get("url_behaviour"), dict) else {}
    url_transport = evidence.get("url_transport") if isinstance(evidence.get("url_transport"), dict) else {}

    age_days = []
    for item in extracted_urls or []:
        if not isinstance(item, dict):
            continue
        value = item.get("domain_age_days")
        try:
            if value is not None:
                age_days.append(int(value))
        except (TypeError, ValueError):
            continue

    youngest_domain_age_days = min(age_days) if age_days else None
    domain_signals = evidence.get("domain_signals") if isinstance(evidence.get("domain_signals"), dict) else {}
    rdap_age = domain_signals.get("domain_age_days")
    if rdap_age is not None and youngest_domain_age_days is None:
        youngest_domain_age_days = rdap_age

    terminal_host_unreachable = bool(
        domain_signals.get("unreachable")
        and (
            not official_destination
            or domain_signals.get("dns_nxdomain")
            or domain_signals.get("rdap_404")
        )
    )
    lexical_typosquat = (
        "typosquatting" in lexical_text
        or "lookalike" in lexical_text
        or "mismatch critic" in lexical_text
    )

    return {
        "typosquat": bool(lexical_typosquat and not official_destination),
        "homoglyph": "homoglif" in lexical_text or "homoglyph" in lexical_text,
        "punycode": "punycode" in lexical_text or "idn/punycode" in lexical_text,
        "dga_entropy": "entropie ridicat" in lexical_text or "entropie mare" in lexical_text or "entropy" in lexical_text or "dga" in lexical_text,
        "very_new_domain": youngest_domain_age_days is not None and youngest_domain_age_days < 7,
        "suspicious_domain_age": youngest_domain_age_days is not None and youngest_domain_age_days < DOMAIN_SUSPICIOUS_AGE_DAYS,
        "established_domain": youngest_domain_age_days is not None and youngest_domain_age_days >= DOMAIN_ESTABLISHED_AGE_DAYS,
        "url_behaviour": bool(url_behaviour),
        "url_transport": bool(url_transport),
        "youngest_domain_age_days": youngest_domain_age_days,
        "rdap_inexistent": bool(domain_signals.get("rdap_404")),
        "domain_young": bool(domain_signals.get("domain_young")),
        "ssl_invalid": bool(domain_signals.get("ssl_valid") is False),
        "cert_very_young": bool(domain_signals.get("cert_young")),
        "host_unreachable": terminal_host_unreachable,
    }


def _collect_infrastructure_flags(
    analysis: Dict[str, Any],
    resolved_urls: List[Dict[str, Any]],
    *,
    official_destination: bool = False,
) -> Dict[str, Any]:
    return _collect_infrastructure_flags_impl(
analysis,
        resolved_urls,
        official_destination=official_destination,

    )


def _augment_summary_with_infra_flags_impl(summary: Dict[str, Any], infra_flags: Dict[str, Any]) -> None:
    lexical_labels: List[str] = []
    if infra_flags.get("homoglyph"):
        lexical_labels.append("homoglyph")
    if infra_flags.get("punycode"):
        lexical_labels.append("punycode")
    if infra_flags.get("typosquat"):
        lexical_labels.append("typosquatting")
    if infra_flags.get("dga_entropy"):
        lexical_labels.append("entropy")
    if lexical_labels:
        summary["sigurscan_lexical"] = {
            "status": "suspicious",
            "verdict": ",".join(lexical_labels),
            "severity": "high" if any(label in {"homoglyph", "punycode", "typosquat"} for label in lexical_labels) else "medium",
            "consulted": True,
            "details": "signals=" + ",".join(lexical_labels),
        }

    youngest_domain_age_days = infra_flags.get("youngest_domain_age_days")
    if youngest_domain_age_days is not None and infra_flags.get("suspicious_domain_age"):
        summary["infra_domain_age"] = {
            "status": "suspicious",
            "verdict": "very_new_domain" if infra_flags.get("very_new_domain") else "new_domain",
            "severity": "high" if infra_flags.get("very_new_domain") else "medium",
            "consulted": True,
            "details": f"domain_age_days={youngest_domain_age_days}",
        }
    elif youngest_domain_age_days is not None and infra_flags.get("established_domain"):
        summary["infra_domain_age"] = {
            "status": "clean",
            "verdict": "established_domain",
            "severity": "low",
            "consulted": True,
            "details": f"domain_age_days={youngest_domain_age_days}",
        }

    if infra_flags.get("url_behaviour"):
        summary["infra_url_behaviour"] = {
            "status": "suspicious",
            "verdict": "url_behaviour",
            "severity": "medium",
            "consulted": True,
            "details": "backend url_behaviour flags present",
        }

    if infra_flags.get("url_transport"):
        summary["infra_url_transport"] = {
            "status": "suspicious",
            "verdict": "url_transport",
            "severity": "medium",
            "consulted": True,
            "details": "backend url_transport flags present",
        }

    if infra_flags.get("rdap_inexistent"):
        summary["infra_rdap"] = {
            "status": "suspicious",
            "verdict": "inexistent_domain",
            "severity": "medium",
            "consulted": True,
            "details": "Domeniul nu apare în registrul RDAP (404).",
        }

    if infra_flags.get("ssl_invalid"):
        summary["infra_ssl"] = {
            "status": "suspicious",
            "verdict": "invalid_ssl",
            "severity": "medium",
            "consulted": True,
            "details": "SSL invalid detectat.",
        }


def _augment_summary_with_infra_flags(summary: Dict[str, Any], infra_flags: Dict[str, Any]) -> None:
    return _augment_summary_with_infra_flags_impl(
summary,
        infra_flags,

    )


def _has_integration_context_impl(raw_text: str) -> bool:
    normalized = _normalise_obfuscated_text(raw_text or "").lower()
    if not normalized:
        return False
    return False


def _has_explicit_user_directed_action_impl(raw_text: str) -> bool:
    return False


def _looks_like_descriptive_or_status_context(raw_text: str) -> bool:
    return _has_integration_context_impl(raw_text)


def _brand_warning_rule_for_claimed_brand_impl(claimed_brand: str) -> Optional[Dict[str, Any]]:
    normalized = _normalize_claimed_brand(claimed_brand)
    if not normalized:
        return None
    for brand_id, display_name in BRAND_ID_TO_DISPLAY_NAME.items():
        if normalized == str(display_name).strip().lower():
            return BRAND_WARNING_RULES.get(brand_id)
    for brand_id, display_name in BRAND_ID_TO_DISPLAY_NAME.items():
        dn = str(display_name).strip().lower()
        if normalized in {dn, brand_id.lower(), brand_id.replace("_", " ").lower()}:
            return BRAND_WARNING_RULES.get(brand_id)
        if normalized in dn:
            return BRAND_WARNING_RULES.get(brand_id)
    return None


def _brand_warning_matches_text_impl(claimed_brand: str, raw_text: str) -> Dict[str, Any]:
    rule = _brand_warning_rule_for_claimed_brand(claimed_brand)
    if not isinstance(rule, dict):
        return {"triggered": False, "matched_assets": [], "brand_id": None}

    never_ask_for = rule.get("never_ask_for")
    if not isinstance(never_ask_for, dict):
        return {"triggered": False, "matched_assets": [], "brand_id": rule.get("brand_id")}

    combined = _normalise_obfuscated_text(raw_text or "").lower()
    matched_assets: List[str] = []

    def _hit_card_request() -> bool:
        if "card" not in combined:
            return False
        benign_card_context = (
            "ai suficienti bani pe card",
            "ai suficienți bani pe card",
            "bani pe card",
            "plata abonamentului",
            "se va efectua automat plata",
            "plata se va efectua automat",
            "plată se va efectua automat",
        )
        if any(token in combined for token in benign_card_context) and not re.search(
            r"(?:introdu|completeaz[aă]|completeaza|trimite|actualiz|verific[aă]|valideaz[aă]|confirm[aă])"
            r"(?:\W+\w+){0,8}\W+(?:date(?:le)?\s+(?:de\s+)?card|num[aă]r(?:ul)?\s+(?:de\s+)?card|cardul|cvv|cvc)",
            combined,
            re.IGNORECASE,
        ):
            return False
        return bool(
            re.search(
                r"(?:introdu|completeaz[aă]|completeaza|trimite|actualiz|verific[aă]|valideaz[aă]|confirm[aă])"
                r"(?:\W+\w+){0,8}\W+(?:date(?:le)?\s+(?:de\s+)?card|num[aă]r(?:ul)?\s+(?:de\s+)?card|cardul|cvv|cvc)",
                combined,
                re.IGNORECASE,
            )
            or re.search(
                r"(?:date(?:le)?\s+(?:de\s+)?card|num[aă]r(?:ul)?\s+(?:de\s+)?card|cvv|cvc)"
                r"(?:\W+\w+){0,8}\W+(?:introdu|completeaz[aă]|completeaza|trimite|actualiz|verific[aă]|valideaz[aă]|confirm[aă])",
                combined,
                re.IGNORECASE,
            )
        )

    detectors = {
        "card_number": _hit_card_request,
        "cvv": lambda: "cvv" in combined or "cvc" in combined,
        "otp": lambda: (
            "otp" in combined
            or "cod otp" in combined
            or "cod sms" in combined
            or "codul de verificare" in combined
            or ("trimite" in combined and "cod" in combined)
            or ("introdu" in combined and "cod" in combined)
        ),
        "whatsapp_code": lambda: "whatsapp" in combined and "cod" in combined,
        "banking_pin": lambda: " pin" in f" {combined}" or "cod pin" in combined,
        "password": lambda: "parola" in combined or "parolă" in combined or "password" in combined,
        "cnp": lambda: "cnp" in combined,
        "iban": lambda: "iban" in combined,
        "remote_access": lambda: any(token in combined for token in ("anydesk", "teamviewer", "rustdesk", "control la distanta", "control la distanță", "asistenta la distanta", "asistență la distanță", "remote access")),
        "apk_install": lambda: "apk" in combined or ("instale" in combined and "aplic" in combined) or ("descarca" in combined and "aplic" in combined) or ("descarcă" in combined and "aplic" in combined),
        "safe_account_transfer": lambda: "cont sigur" in combined or "transfer sigur" in combined,
        "crypto_atm_deposit": lambda: any(token in combined for token in ("crypto atm", "bitcoin atm", "depunere crypto")),
    }

    for asset, enabled in never_ask_for.items():
        if not enabled:
            continue
        detector = detectors.get(str(asset))
        if detector and detector():
            matched_assets.append(str(asset))

    matched_assets = sorted(set(matched_assets))
    return {
        "triggered": bool(matched_assets),
        "matched_assets": matched_assets,
        "brand_id": rule.get("brand_id"),
        "source_url": rule.get("source_url"),
        "summary": rule.get("exact_official_statement_summary"),
        "signal": rule.get("evidence_gate_signal_suggested"),
    }


def _brand_warning_rule_for_claimed_brand(claimed_brand: str) -> Optional[Dict[str, Any]]:
    return _brand_warning_rule_for_claimed_brand_impl(
claimed_brand,

    )


def _brand_warning_matches_text(claimed_brand: str, raw_text: str) -> Dict[str, Any]:
    return _brand_warning_matches_text_impl(
claimed_brand,
        raw_text,

    )


def _looks_like_official_safety_education_impl(raw_text: str) -> bool:
    normalized = _normalise_obfuscated_text(raw_text or "").lower()
    if not normalized:
        return False
    scope_trick = (
        r"\b("
        r"doar\s+(?:aici|acest(?:ui)?\s+agent|codul)|"
        r"doar\s+(?:primele|ultimele|\d+)|"
        r"(?:introdu|introduce|trimite)[-\s]?(?:l|le)?\s+doar|"
        r"doar\s+(?:[îi]n|in)\s+(?:caseta|formularul|c[âa]mpul)\b|"
        r"(?:[îi]n|in)\s+afar[ăa]\s+de|"
        r"folose[șs]te\s+noul\s+cont|"
        r"nu\s+(?:suna|sun[aă]|verifica|face\s+callback|[îi]nchide|inchide)|"
        r"r[ăa]m[aâ]ne[țt]i\s+la\s+telefon"
        r")\b"
    )
    if re.search(scope_trick, normalized, re.IGNORECASE):
        return False
    action_after_warning = (
        r"(?:pentru\s+a\s+(?:demonstra|confirma|verifica)|ca\s+s[ăa]\s+(?:demonstrezi|confirmi|verifici)|"
        r"simulator|test\s+de\s+(?:siguran[țt][ăa]|securitate))"
        r".{0,140}\b(?:autentific[ăa][-\s]?te|logheaz[ăa][-\s]?te|login|introdu|completeaz[ăa]|"
        r"trimite|cod|otp|parol[ăa]|date(?:le)?\s+(?:de\s+)?card)\b"
    )
    if re.search(action_after_warning, normalized, re.IGNORECASE):
        return False
    sensitive_terms = (
        r"(?:cnp|pin|cvv|cvc|otp|cod(?:ul|uri?)?(?:\s+sms)?|parol[ăa]|date\s+de\s+card|date(?:le)?\s+bancare|"
        r"datele\s+cardului|num[aă]r(?:ul)?\s+(?:de\s+)?card|iban|cont\s+(?:nou|sigur|temporar|seif)|"
        r"conturi\s+(?:noi|sigure|temporare|seif)|"
        r"acces(?:ul)?\s+la\s+(?:dispozitiv|telefon|calculator)|"
        r"transfer(?:[ăa]|a)?\s+bani|transfer\s+preventiv|bani|crypto\s+atm|usdt|tax(?:[ăa]|e)\s+de\s+retragere|profit\s+garantat|"
        r"obliga[țt]ii?\s+de\s+plat[ăa]|schimbare\s+de\s+iban|"
        r"copie\s+(?:ci|act)|ci\s+fa[țt][ăa][-\s]?verso|act(?:ul)?\s+(?:de\s+)?identitate|"
        r"carduri?\s+cadou|gift\s*card|voucher|autentificare\s+bancar[ăa]|actualizarea\s+parolei|link\s+primit|home.?bank|logare|login|"
        r"anydesk|teamviewer|rustdesk|control\s+la\s+distan[țt][ăa]|asisten[țt][ăa]\s+la\s+distan[țt][ăa]|remote\s+access|"
        r"aplica[țt]i[ei]?\s+(?:de\s+)?(?:(?:acces|asisten[țt][ăa])\s+la\s+distan[țt][ăa]|remote)"
    )
    if re.search(
        sensitive_terms,
        normalized,
        re.IGNORECASE,
    ):
        return True
    return False


def _looks_like_official_safety_education(raw_text: str) -> bool:
    return _looks_like_official_safety_education_impl(
raw_text,

    )


def _has_direct_sensitive_request_impl(raw_text: str) -> bool:
    if _data_url_contains_sensitive_form(raw_text):
        return True
    normalized = _normalise_obfuscated_text(raw_text or "").lower()
    if not normalized or _looks_like_official_safety_education(normalized):
        return False
    if _looks_like_descriptive_or_status_context(normalized) and not _has_explicit_user_directed_action(normalized):
        return False
    verbs = (
        r"(?:introdu\w*|completeaz\w*|trimite\w*|r[ăa]spunde\w*|spune\w*|comunic\w*|"
        r"d[ăa](?:[-\s]?(?:mi|ne))?|da[țt]i(?:[-\s]?(?:mi|ne))?|dati(?:[-\s]?(?:mi|ne))?|"
        r"furnizeaz\w*|ofer[ăa]\w*|cite[șs]te|citeste|captur\w*|poz[ăa]|screenshot|"
        r"confirm\w*|valideaz\w*|verific\w*|"
        r"logheaz[ăa][-\s]?te|autentific[ăa][-\s]?te)"
    )
    sensitive = (
        r"(?:parol[ăa]|password|otp|cod(?:ul)?(?:\s+(?:pe\s+)?(?:sms|whatsapp)|"
        r"\s+de\s+(?:verificare|confirmare|autorizare|autentificare)|\s+3ds)?|cod(?:ul)?\s+unic|"
        r"cod(?:ul)?.{0,40}aplica[țt]ia\s+bancar[ăa]|"
        r"(?:prima|a\s+treia|a\s+cincea|ultima|ultimele).{0,50}(?:cifr[ăa]|cifre).{0,50}cod|"
        r"(?:cod\s+qr|qr).{0,40}(?:esim|e-sim|profil(?:ul)?\s+sim)|"
        r"(?:esim|e-sim|profil(?:ul)?\s+sim).{0,40}(?:cod\s+qr|qr)|"
        r"pin(?:-ul|ul)?|cvv|cvc|date(?:le)?\s+(?:de\s+)?card(?:ului)?|datele\s+cardului|"
        r"num[aă]r(?:ul)?\s+(?:de\s+)?card(?:ului)?|"
        r"ultimele\s+\d+\s+cifre\s+(?:ale\s+)?card(?:ului)?|"
        r"cnp|iban|copie\s+(?:ci|act)|act(?:ul)?\s+(?:de\s+)?identitate)"
    )
    return bool(
        re.search(verbs + r"(?:\W+\w+){0,8}\W+" + sensitive, normalized, re.IGNORECASE)
        or re.search(sensitive + r"(?:\W+\w+){0,8}\W+" + verbs, normalized, re.IGNORECASE)
    )


def _has_direct_sensitive_request(raw_text: str) -> bool:
    return _has_direct_sensitive_request_impl(
raw_text,

    )


def _has_sensitive_url_path_impl(resolved_urls: List[Dict[str, Any]]) -> bool:
    sensitive_path_tokens = (
        "card", "cvv", "cvc", "otp", "cod", "login", "auth", "parola", "password", "date",
        "formular", "form", "identitate", "pay", "plata", "plată", "checkout", "achita",
        "securitate", "security", "update", "install", "session",
    )
    for entry in resolved_urls or []:
        url = str(entry.get("final_url") or entry.get("url") or "")
        parsed = urllib.parse.urlparse(url)
        target = urllib.parse.unquote(f"{parsed.path or ''}?{parsed.query or ''}").lower()
        if any(token in target for token in sensitive_path_tokens):
            return True
    return False


def _has_sensitive_url_path(resolved_urls: List[Dict[str, Any]]) -> bool:
    return _has_sensitive_url_path_impl(
resolved_urls,

    )


def _claim_verifier_required_impl(analysis: Dict[str, Any]) -> bool:
    claimed = str(analysis.get("claimed_brand") or "").strip().lower()
    if claimed and claimed not in {"nespecificat", "unknown", "none"}:
        return True
    evidence = analysis.get("evidence", {}) if isinstance(analysis.get("evidence"), dict) else {}
    if evidence.get("has_domain_mismatch"):
        return True
    family_text = " ".join(
        str(value).lower()
        for value in (analysis.get("detected_family_id"), analysis.get("detected_family"))
        if value
    )
    markers = (
        "ofert",
        "promo",
        "voucher",
        "campanie",
        "catalog",
        "curier",
        "colet",
        "anaf",
        "banc",
        "otp",
        "card",
        "plata",
        "plată",
        "cont",
    )
    return any(marker in family_text for marker in markers)


def _claim_verifier_required(analysis: Dict[str, Any]) -> bool:
    return _claim_verifier_required_impl(
analysis,

    )


def _attach_brand_warning_summary_impl(summary: Dict[str, Any], brand_warning: Dict[str, Any]) -> None:
    if not isinstance(summary, dict):
        return
    if not isinstance(brand_warning, dict) or not brand_warning.get("triggered"):
        summary.pop("brand_warning_corpus", None)
        return

    matched_assets = list(brand_warning.get("matched_assets") or [])
    high_risk_assets = {"card_number", "cvv", "otp", "whatsapp_code", "banking_pin", "password", "remote_access", "apk_install"}
    severity = "high" if any(asset in high_risk_assets for asset in matched_assets) else "medium"
    summary["brand_warning_corpus"] = {
        "status": "triggered",
        "verdict": "brand_warning",
        "severity": severity,
        "summary": brand_warning.get("summary", ""),
        "details": brand_warning.get("summary", ""),
        "brand_id": brand_warning.get("brand_id"),
        "matched_assets": matched_assets,
        "source_url": brand_warning.get("source_url"),
        "signal": brand_warning.get("signal"),
    }


def _attach_brand_warning_summary(summary: Dict[str, Any], brand_warning: Dict[str, Any]) -> None:
    return _attach_brand_warning_summary_impl(
summary,
        brand_warning,

    )


def _source_status(summary: Dict[str, Any], source_name: str) -> str:
    return _source_status_impl(
summary,
        source_name,

    )


def _source_consulted(summary: Dict[str, Any], source_name: str) -> bool:
    return _source_consulted_impl(
summary,
        source_name,

    )


def _request_sensitivity_from_signals_impl(
    *,
    raw_text: str,
    brand_warning: Dict[str, Any],
    direct_sensitive_request: bool,
    sensitive_url_path: bool,
    official_destination: bool,
    resolved_urls: List[Dict[str, Any]],
) -> str:
    "none"


def _request_sensitivity_from_signals(
    *,
    raw_text: str,
    brand_warning: Dict[str, Any],
    direct_sensitive_request: bool,
    sensitive_url_path: bool,
    official_destination: bool,
    resolved_urls: List[Dict[str, Any]],
) -> str:
    return _request_sensitivity_from_signals_impl(
raw_text=raw_text,
        brand_warning=brand_warning,
        direct_sensitive_request=direct_sensitive_request,
        sensitive_url_path=sensitive_url_path,
        official_destination=official_destination,
        resolved_urls=resolved_urls,

    )


def _detect_person_never_does_violations_impl(raw_text: str, effective_channel: str, result, violated_never_does: list) -> None:
    None


def _enrich_with_btr_provenance_impl(
    analysis: Dict[str, Any],
    claimed_brand: str,
    raw_text: str,
    resolved_urls: List[Dict[str, Any]],
) -> None:
    evidence = analysis.setdefault("evidence", {})
    if evidence.get("provenance"):
        return
    first_url = _first_final_url(resolved_urls)
    observed_domain = None
    if first_url:
        try:
            parsed = urllib.parse.urlparse(first_url)
            observed_domain = parsed.hostname
        except Exception:
            pass
    official_destination = _official_destination_confirmed(resolved_urls, claimed_brand)
    sensitive = _request_sensitivity_from_signals(
        raw_text=raw_text,
        brand_warning=evidence.get("brand_warning") or {"triggered": False, "matched_assets": []},
        direct_sensitive_request=evidence.get("direct_sensitive_request") or False,
        sensitive_url_path=_has_sensitive_url_path(resolved_urls),
        official_destination=official_destination,
        resolved_urls=resolved_urls,
    )
    effective_channel = "official_website" if official_destination else str(evidence.get("source_channel") or "unknown")
    sensitive_asks = []
    if sensitive and sensitive != "none":
        sensitive_asks.append(sensitive)
    result = brand_truth_registry.provenance_check(
        claimed_brand=claimed_brand if claimed_brand != "Nespecificat" else None,
        observed_channel=effective_channel,
        observed_domain=observed_domain,
        observed_phone_e164=None,
        sensitive_asks=sensitive_asks,
        payment_method=None,
        final_url=first_url,
    )
    violated_never_does = list(result.violated_never_does)
    _detect_person_never_does_violations_impl(
        raw_text,
        effective_channel,
        result,
        violated_never_does,
    )
    evidence["provenance"] = {
        "official_domain_match": result.official_match,
        "manifest_id": result.manifest_id,
        "manifest_version": brand_truth_registry.version,
        "provenance": result.provenance,
        "identity_status": result.identity_status,
        "violated_never_asks": result.violated_never_asks,
        "violated_never_does": result.violated_never_does,
        "evidence_power": result.evidence_power,
        "reason_codes": result.reason_codes,
    }
    if result.violated_never_asks:
        analysis["violated_never_asks"] = result.violated_never_asks
    if violated_never_does:
        analysis["violated_never_does"] = violated_never_does


def _enrich_with_btr_provenance(
    analysis: Dict[str, Any],
    claimed_brand: str,
    raw_text: str,
    resolved_urls: List[Dict[str, Any]],
) -> None:
    return _enrich_with_btr_provenance_impl(
analysis,
        claimed_brand,
        raw_text,
        resolved_urls,

    )


def _maybe_add_dns_reputation(summary: Dict[str, Any], resolved_urls: List[Dict[str, Any]]) -> None:
    """Pilon DNS reputation (gratis, fără cheie). Opt-in prin ENABLE_DNS_REPUTATION;
    implicit OFF → fără rețea/latență. `blocked` → provider hard (dns_security);
    `suspended`/`nxdomain` → semnal ponderat (infra_dns). Best-effort, nu aruncă."""
    if not ENABLE_DNS_REPUTATION or not resolved_urls:
        return
    from services import dns_reputation

    domain = ""
    for entry in resolved_urls:
        if isinstance(entry, dict):
            domain = dns_reputation.domain_from_url(entry.get("final_url") or entry.get("url") or "")
            if domain:
                break
    if not domain:
        return
    try:
        rep = dns_reputation.check_dns_reputation(domain)
    except Exception:
        return
    hard = dns_reputation.dns_summary_entry(rep)
    if hard:
        summary["dns_security"] = hard
    weak = dns_reputation.dns_infra_entry(rep)
    if weak:
        summary["infra_dns"] = weak


def _apply_provider_gate_verdict(
    analysis: Dict[str, Any],
    resolved_urls: List[Dict[str, Any]],
    *,
    raw_text: str = "",
    pillars: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    evidence = analysis.setdefault("evidence", {})
    summary = evidence.get("external_intel_summary")
    if not isinstance(summary, dict):
        summary = {}
    claimed_brand = str(analysis.get("claimed_brand") or "Nespecificat")
    official_destination = _official_destination_confirmed(resolved_urls, claimed_brand)
    infra_flags = _collect_infrastructure_flags(
        analysis,
        resolved_urls,
        official_destination=official_destination,
    )
    _augment_summary_with_infra_flags(summary, infra_flags)
    _maybe_add_dns_reputation(summary, resolved_urls)
    evidence["external_intel_summary"] = summary

    source_channel = evidence.get("source_channel") if isinstance(evidence, dict) else None
    existing_cross_scan = evidence.get("cross_scan_knowledge") if isinstance(evidence.get("cross_scan_knowledge"), dict) else {}
    try:
        from services.cross_scan_knowledge import evaluate_cross_scan_knowledge

        computed_cross_scan = evaluate_cross_scan_knowledge(
            text=raw_text,
            claimed_brand=None if claimed_brand == "Nespecificat" else claimed_brand,
            source_channel=source_channel,
        )
    except Exception:
        computed_cross_scan = {}
    if existing_cross_scan:
        merged_cross_scan = dict(computed_cross_scan or {})
        merged_cross_scan.update(existing_cross_scan)
        computed_flags = list((computed_cross_scan or {}).get("fraud_flags") or [])
        for flag in existing_cross_scan.get("fraud_flags") or []:
            if flag not in computed_flags:
                computed_flags.append(flag)
        if computed_flags:
            merged_cross_scan["fraud_flags"] = computed_flags
        evidence["cross_scan_knowledge"] = merged_cross_scan
    else:
        evidence["cross_scan_knowledge"] = computed_cross_scan or {}
    has_urls = bool(resolved_urls)
    offer = evidence.get("offer_claim_verification")
    offer_status = str(offer.get("status", "")).lower() if isinstance(offer, dict) else ""
    web_risk_consulted = _source_ready(summary, "google_web_risk")
    asf_investor_alerts_consulted = _source_ready(summary, "asf_investor_alerts")
    phishing_database_consulted = _source_ready(summary, "phishing_database")
    phishtank_consulted = _source_ready(summary, "phishtank_online_valid")
    openphish_consulted = _source_ready(summary, "openphish")
    urlscan_consulted = any(_source_ready(summary, name) for name in ("urlscan", "urlscan.io"))
    sensitive_url_path = _has_sensitive_url_path(resolved_urls)
    brand_warning = _brand_warning_matches_text(claimed_brand, raw_text)
    official_safety_education = _looks_like_official_safety_education(raw_text)
    direct_sensitive_request = _has_direct_sensitive_request(raw_text)
    if official_safety_education:
        brand_warning = {"triggered": False, "matched_assets": []}
    evidence["brand_warning"] = brand_warning
    _attach_brand_warning_summary(summary, brand_warning)
    claim_required = _claim_verifier_required(analysis)
    claim_consulted = (not claim_required) or offer_status in {"confirmed", "not_found", "inconclusive", "skipped"}
    missing_required_pillars = []
    if has_urls and not web_risk_consulted:
        missing_required_pillars.append("Google Web Risk")
    if has_urls and not claim_consulted:
        missing_required_pillars.append("verificare oferta/claim")
    consulted_sources = [
        name
        for name in (
            "google_web_risk",
            "asf_investor_alerts",
            "phishing_database",
            "phishtank_online_valid",
            "openphish",
            "urlscan",
            "urlscan.io",
            "urlhaus",
            "infra_dns",
            "infra_domain_age",
            "infra_rdap",
            "infra_ssl",
            "infra_url_behaviour",
            "infra_url_transport",
            "sigurscan_lexical",
            "scam_blocklist_nrd",
            "phishdestroy_destroylist",
        )
        if _source_ready(summary, name)
    ]
    consulted_sources = sorted(set(consulted_sources))
    consulted_count = len(consulted_sources)

    provider_gate = {
        "version": "verdict_gate_v2",
        "official_destination": official_destination,
        "web_risk_consulted": web_risk_consulted,
        "asf_investor_alerts_consulted": asf_investor_alerts_consulted,
        "phishing_database_consulted": phishing_database_consulted,
        "phishtank_consulted": phishtank_consulted,
        "openphish_consulted": openphish_consulted,
        "urlscan_consulted": urlscan_consulted,
        "claim_required": claim_required,
        "claim_consulted": claim_consulted,
        "missing_required_pillars": missing_required_pillars,
        "consulted_sources": consulted_sources,
        "consulted_count": consulted_count,
        "offer_status": offer_status or "unknown",
        "infrastructure_flags": infra_flags,
        "brand_warning": brand_warning,
        "official_safety_education": official_safety_education,
        "direct_sensitive_request": direct_sensitive_request,
        "sensitive_url_path": sensitive_url_path,
    }

    _enrich_with_btr_provenance(analysis, claimed_brand, raw_text, resolved_urls)

    decision_bundle = _build_decision_evidence_bundle(
        analysis,
        resolved_urls,
        raw_text=raw_text,
        pillars=pillars,
        summary=summary,
        infra_flags=infra_flags,
        brand_warning=brand_warning,
        official_destination=official_destination,
        direct_sensitive_request=direct_sensitive_request,
        sensitive_url_path=sensitive_url_path,
    )
    gate_result = reduce_verdict(decision_bundle)
    return _apply_decision_contract_result(analysis, decision_bundle, gate_result, provider_gate)


def _project_provider_gate_verdict(
    analysis: Dict[str, Any],
    resolved_urls: List[Dict[str, Any]],
    *,
    raw_text: str = "",
    pillars: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Pure projection of the provider gate decision over a snapshot of evidence.

    The orchestrator can call this in tests or diagnostics without mutating the
    live scan job. It intentionally reuses the same gate implementation on deep
    copies so the projection cannot drift from the production path.
    """
    analysis_copy = _deep_copy_jsonable(analysis if isinstance(analysis, dict) else {})
    resolved_copy = _deep_copy_jsonable(resolved_urls if isinstance(resolved_urls, list) else [])
    pillars_copy = _deep_copy_jsonable(pillars) if isinstance(pillars, dict) else None
    projected = _apply_provider_gate_verdict(
        analysis_copy,
        resolved_copy,
        raw_text=raw_text,
        pillars=pillars_copy,
    )
    evidence = projected.get("evidence") if isinstance(projected.get("evidence"), dict) else {}
    return {
        "risk_level": projected.get("risk_level"),
        "risk_score": projected.get("risk_score"),
        "detected_family": projected.get("detected_family"),
        "detected_family_id": projected.get("detected_family_id"),
        "reasons": list(projected.get("reasons") or []),
        "safe_actions": list(projected.get("safe_actions") or []),
        "provider_gate": _deep_copy_jsonable(evidence.get("provider_gate") or {}),
        "external_intel_summary": _deep_copy_jsonable(evidence.get("external_intel_summary") or {}),
        "brand_warning": _deep_copy_jsonable(evidence.get("brand_warning") or {}),
    }


def _build_decision_evidence_bundle(
    analysis: Dict[str, Any],
    resolved_urls: List[Dict[str, Any]],
    *,
    raw_text: str = "",
    pillars: Optional[Dict[str, Dict[str, Any]]] = None,
    summary: Optional[Dict[str, Any]] = None,
    infra_flags: Optional[Dict[str, Any]] = None,
    brand_warning: Optional[Dict[str, Any]] = None,
    official_destination: Optional[bool] = None,
    direct_sensitive_request: Optional[bool] = None,
    sensitive_url_path: Optional[bool] = None,
    request_sensitivity: Optional[str] = None,
    **_: Any,
) -> Dict[str, Any]:
    def _fallback(
        analysis: Dict[str, Any],
        resolved_urls: List[Dict[str, Any]],
        *,
        raw_text: str = "",
        pillars: Optional[Dict[str, Dict[str, Any]]] = None,
        summary: Optional[Dict[str, Any]] = None,
        infra_flags: Optional[Dict[str, Any]] = None,
        brand_warning: Optional[Dict[str, Any]] = None,
        official_destination: Optional[bool] = None,
        direct_sensitive_request: Optional[bool] = None,
        sensitive_url_path: Optional[bool] = None,
        request_sensitivity: Optional[str] = None,
        **_: Any,
    ) -> Dict[str, Any]:
        return {
            "schema": "sigurscan_evidence_bundle_v2",
            "input": {
                "type": "unknown",
                "redacted_text": str(raw_text or "")[:2000],
            },
            "resolution": {
                "final_url": _first_final_url(resolved_urls),
                "status": "resolved" if resolved_urls else "not_required",
                "completeness": not bool(resolved_urls) or bool(_first_final_url(resolved_urls)),
            },
            "providers": {
                "verdict": "unknown",
                "hits": [],
                "completeness": True,
            },
            "identity": {
                "status": "unknown",
                "completeness": True,
            },
            "request": {
                "sensitive": "none",
                "channel": "unknown",
                "positive_action_request": False,
                "protective_warning": False,
                "descriptive_context": False,
                "completeness": True,
            },
            "provenance": {
                "official_domain_match": False,
            },
            "context": {
                "urgency": False,
                "passive_payment": False,
                "apk_or_remote_mention": False,
                "non_http_deeplink": False,
            },
            "semantic_review": {
                "status": "done",
                "risk_class": "unknown",
                "matched_family": "",
            },
            "social_engineering": {
                "status": "done",
                "intent": "unknown",
                "ask_present": False,
                "ask_type": ["none"],
            },
            "evidence_hash": "sha256:0000",
        }

    if summary is None:
        summary = analysis.get("evidence", {}).get("external_intel_summary") if isinstance(analysis.get("evidence"), dict) else None
    return _fallback(
        analysis,
        resolved_urls,
        raw_text=raw_text,
        pillars=pillars,
        summary=summary,
        infra_flags=infra_flags,
        brand_warning=brand_warning,
        official_destination=official_destination,
        direct_sensitive_request=direct_sensitive_request,
        sensitive_url_path=sensitive_url_path,
        request_sensitivity=request_sensitivity or "",
    )


def _apply_decision_contract_result(
    analysis: Dict[str, Any],
    decision_bundle: Dict[str, Any],
    gate_result: Dict[str, Any],
    provider_gate: Dict[str, Any],
) -> Dict[str, Any]:
    def _fallback(
        analysis: Dict[str, Any],
        decision_bundle: Dict[str, Any],
        gate_result: Dict[str, Any],
        provider_gate: Dict[str, Any],
    ) -> Dict[str, Any]:
        evidence = analysis.setdefault("evidence", {})
        provider_gate = dict(provider_gate)
        provider_gate.update(
            {
                "version": "verdict_gate_v2",
                "decision_contract": "sigurscan_evidence_bundle_v2",
                "risk_level": gate_result.get("risk_level"),
                "risk_score": gate_result.get("risk_score"),
                "reason": ", ".join(gate_result.get("reason_codes") or []),
                "label": gate_result.get("label"),
            }
        )
        evidence["provider_gate"] = provider_gate
        evidence["decision_bundle"] = decision_bundle
        evidence["verdict_gate"] = gate_result

        label = str(gate_result.get("label") or "UNVERIFIED").upper()
        reasons = {
            "SAFE": ["Proveniența pozitivă confirmată, fără semnale suplimentare."],
            "SUSPECT": ["Verifică contextul prin canalul oficial înainte de acțiune."],
            "DANGEROUS": ["Există indicii de risc ridicat; nu continua."],
            "UNVERIFIED": ["Lipsesc suficiente dovezi de verificare."],
        }.get(label, ["Verifică pe canalul oficial înainte de acțiune."])

        analysis["risk_level"] = gate_result.get("risk_level")
        analysis["risk_score"] = gate_result.get("risk_score")
        analysis["detected_family"] = provider_gate.get("detected_family") or "Verificare"
        analysis["detected_family_id"] = provider_gate.get("detected_family_id") or "provider-gate-residual"
        analysis["reasons"] = reasons
        analysis["safe_actions"] = (
            ["Poți continua cu prudență."]
            if label == "SAFE"
            else ["Verifică mesajul prin aplicația oficială.", "Nu introduce date."]
        )
        return analysis

    return _fallback(analysis, decision_bundle, gate_result, provider_gate)


def _skipped_offer_claim_payload_impl(reason: str) -> Dict[str, Any]:
    return {
        "provider": "ai_offer_web_check",
        "status": "skipped",
        "verdict": "skipped",
        "severity": "unknown",
        "summary": reason,
        "details": reason,
        "confidence": 0,
        "evidence_urls": [],
        "method": "skipped",
    }


def _skipped_offer_claim_payload(reason: str) -> Dict[str, Any]:
    return _skipped_offer_claim_payload_impl(reason)
