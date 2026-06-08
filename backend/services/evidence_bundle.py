import hashlib
import json
import re
import urllib.parse
from typing import Any, Dict, List, Optional


KNOWN_DEEPLINK_PROVIDERS = {
    "onelink.me",
    "app.link",
    "branch.link",
    "bnc.lt",
    "go.link",
    "page.link",
    "smart.link",
    "sng.link",
}


def _safe_str(value: Any) -> str:
    return str(value or "").strip()


def _host_from_url(url: str) -> str:
    try:
        return urllib.parse.urlparse(url).hostname or ""
    except Exception:
        return ""


def _registered_domain_from_host(host: str) -> str:
    host = _safe_str(host).lower().strip(".")
    if not host:
        return ""
    parts = [part for part in host.split(".") if part]
    if len(parts) <= 2:
        return host
    return ".".join(parts[-2:])


def _is_deeplink_provider(url: str, host: Optional[str] = None) -> bool:
    candidate = (_safe_str(host) or _host_from_url(url)).lower()
    registered = _registered_domain_from_host(candidate)
    return candidate in KNOWN_DEEPLINK_PROVIDERS or registered in KNOWN_DEEPLINK_PROVIDERS


def _subdomain_matches_brand(url: str, claimed_brand: str) -> Optional[str]:
    host = _host_from_url(url).lower()
    brand = re.sub(r"[^a-z0-9]+", "", _safe_str(claimed_brand).lower())
    if not host or not brand:
        return None
    first_label = host.split(".", 1)[0]
    label = re.sub(r"[^a-z0-9]+", "", first_label)
    return claimed_brand if label and label == brand else None


def _provider_summary(evidence: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    summary = evidence.get("external_intel_summary")
    if not isinstance(summary, dict):
        return {}

    providers: Dict[str, Dict[str, Any]] = {}
    for name, raw_details in summary.items():
        if not isinstance(raw_details, dict):
            continue
        providers[str(name)] = {
            "status": raw_details.get("status"),
            "verdict": raw_details.get("verdict"),
            "severity": raw_details.get("severity"),
            "consulted": raw_details.get("consulted"),
            "report_url": raw_details.get("report_url"),
            "details": raw_details.get("details"),
        }
    return providers


def _url_entry(item: Dict[str, Any], claimed_brand: str) -> Dict[str, Any]:
    raw_url = (
        item.get("original_url")
        or item.get("raw_url")
        or item.get("input_url")
        or item.get("url")
        or item.get("final_url")
    )
    final_url = item.get("final_url") or item.get("url") or raw_url
    final_host = item.get("final_hostname") or item.get("final_host") or _host_from_url(final_url)
    final_registered = (
        item.get("final_registered_domain")
        or item.get("registered_domain")
        or _registered_domain_from_host(final_host)
    )
    raw_host = _host_from_url(raw_url)
    raw_registered = _registered_domain_from_host(raw_host)

    return {
        "raw": raw_url,
        "raw_host": raw_host,
        "raw_registered_domain": raw_registered,
        "final": final_url,
        "final_host": final_host,
        "final_registered_domain": final_registered,
        "success": item.get("success", True),
        "redirect_count": int(item.get("redirect_count") or 0),
        "shortener_count": int(item.get("shortener_count") or 0),
        "is_known_deeplink_provider": _is_deeplink_provider(raw_url, raw_host),
        "subdomain_matches_brand": _subdomain_matches_brand(raw_url, claimed_brand),
    }


def _stable_hash(payload: Dict[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_evidence_bundle(
    *,
    input_type: str,
    redacted_text: str,
    analysis: Dict[str, Any],
    resolved_urls: List[Dict[str, Any]],
    scan_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a stable, privacy-safe fact bundle for shadow adjudication.

    This intentionally records facts and the deterministic gate outcome. It does
    not make a new verdict and never contains the unredacted user input.
    """

    scan_payload = scan_payload if isinstance(scan_payload, dict) else {}
    analysis = analysis if isinstance(analysis, dict) else {}
    evidence = analysis.get("evidence") if isinstance(analysis.get("evidence"), dict) else {}
    provider_gate = evidence.get("provider_gate") if isinstance(evidence.get("provider_gate"), dict) else {}
    decision_bundle = evidence.get("decision_bundle") if isinstance(evidence.get("decision_bundle"), dict) else {}
    claimed_brand = _safe_str(analysis.get("claimed_brand") or "Nespecificat")

    bundle: Dict[str, Any] = {
        "schema": "sigurscan_evidence_bundle_v2",
        "schema_version": "sigurscan_evidence_bundle_v1",
        "decision_bundle": decision_bundle,
        "input": {
            "type": input_type or "unknown",
            "lang": "ro",
            "text_redacted": _safe_str(redacted_text)[:4000],
        },
        "urls": [
            _url_entry(item, claimed_brand)
            for item in (resolved_urls or [])
            if isinstance(item, dict)
        ],
        "providers": _provider_summary(evidence),
        "brand": {
            "claimed": claimed_brand,
            "mismatch": bool(evidence.get("has_domain_mismatch")),
            "mismatched_domain": evidence.get("mismatched_domain"),
            "official_destination": bool(provider_gate.get("official_destination")),
            "brand_warning_triggered": bool(
                (evidence.get("brand_warning") or {}).get("triggered")
                if isinstance(evidence.get("brand_warning"), dict)
                else False
            ),
        },
        "text_signals": {
            "direct_sensitive_request": bool(provider_gate.get("direct_sensitive_request")),
            "sensitive_url_path": bool(provider_gate.get("sensitive_url_path")),
            "brand_warning_triggered": bool(
                (evidence.get("brand_warning") or {}).get("triggered")
                if isinstance(evidence.get("brand_warning"), dict)
                else False
            ),
            "passive_payment_mention": bool(
                re.search(r"\b(card|plata|abonament|factur[ăa]|sold)\b", _safe_str(redacted_text), re.IGNORECASE)
            )
            and not bool(provider_gate.get("direct_sensitive_request")),
            "urgency": bool(
                re.search(r"\b(urgent|24\s*de\s*ore|azi|acum|ultima|expir[ăa])\b", _safe_str(redacted_text), re.IGNORECASE)
            ),
            "apk_or_remote_access": bool(
                re.search(r"\b(apk|anydesk|teamviewer|remote access|control la distan[țt][ăa])\b", _safe_str(redacted_text), re.IGNORECASE)
            ),
        },
        "rag": {
            "matched_scam_family": analysis.get("detected_family_id"),
            "matched_scam_family_name": analysis.get("detected_family"),
            "matched_legit_template": evidence.get("matched_legit_template"),
        },
        "gate": {
            "risk_level": scan_payload.get("risk_level") or analysis.get("risk_level"),
            "risk_score": scan_payload.get("risk_score") if scan_payload.get("risk_score") is not None else analysis.get("risk_score"),
            "user_risk_label": scan_payload.get("user_risk_label"),
            "detected_family_id": analysis.get("detected_family_id"),
            "reasons": list(analysis.get("reasons") or [])[:8],
            "provider_gate": provider_gate,
        },
    }
    bundle["evidence_hash"] = _stable_hash(bundle)
    return bundle


def build_evidence_bundle_v2(
    *,
    input_type: str,
    redacted_text: str,
    analysis: Dict[str, Any],
    resolved_urls: List[Dict[str, Any]],
    scan_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Return the normalized v2 decision bundle when the pipeline produced it.

    This keeps callers honest: v2 is the adjudication contract, while
    build_evidence_bundle() remains a backward-compatible telemetry envelope.
    """

    analysis = analysis if isinstance(analysis, dict) else {}
    evidence = analysis.get("evidence") if isinstance(analysis.get("evidence"), dict) else {}
    decision_bundle = evidence.get("decision_bundle") if isinstance(evidence.get("decision_bundle"), dict) else None
    if isinstance(decision_bundle, dict) and decision_bundle.get("schema") == "sigurscan_evidence_bundle_v2":
        payload = json.loads(json.dumps(decision_bundle, ensure_ascii=False))
        payload.setdefault("input", {})
        payload["input"]["type"] = payload["input"].get("type") or input_type or "unknown"
        payload["input"]["redacted_text"] = _safe_str(redacted_text)[:4000]
        payload["evidence_hash"] = _stable_hash(payload)
        return payload

    fallback = build_evidence_bundle(
        input_type=input_type,
        redacted_text=redacted_text,
        analysis=analysis,
        resolved_urls=resolved_urls,
        scan_payload=scan_payload,
    )
    return {
        "schema": "sigurscan_evidence_bundle_v2",
        "input": {
            "type": input_type or "unknown",
            "redacted_text": _safe_str(redacted_text)[:4000],
        },
        "resolution": {"status": "partial", "completeness": False, "final_url": None},
        "providers": {"verdict": "pending", "hits": [], "completeness": False},
        "identity": {
            "claimed_brand": claimed_brand if (claimed_brand := _safe_str(analysis.get("claimed_brand"))) else None,
            "status": "unknown",
            "tld_suspicious": False,
            "completeness": False,
        },
        "request": {"sensitive": "none", "channel": "unknown", "completeness": False},
        "context": fallback.get("text_signals", {}),
        "semantic_review": {"status": "pending", "completeness": False},
        "evidence_hash": fallback.get("evidence_hash"),
    }
