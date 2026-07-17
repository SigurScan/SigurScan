"""Canonical shadow projection of URL resolution and reputation evidence."""

from __future__ import annotations

from typing import Any, Dict, Mapping, Sequence


THREAT_ENRICHMENT_SCHEMA = "sigurscan_threat_enrichment_v1"
MALICIOUS_STATUSES = {"malicious", "phishing", "malware", "dangerous", "blacklisted"}
SUSPICIOUS_STATUSES = {"suspicious"}
CLEAN_STATUSES = {"clean", "safe", "no_match", "no-match"}
ERROR_STATUSES = {"error", "timeout", "rate_limited", "unavailable", "budget_exhausted"}
PENDING_STATUSES = {"pending", "queued", "running", "unknown", "missing", ""}


def _status(details: Mapping[str, Any]) -> str:
    return str(details.get("status") or details.get("verdict") or "unknown").strip().lower()


def _provider_verdict(provider_statuses: Mapping[str, str]) -> str:
    statuses = set(provider_statuses.values())
    if statuses & MALICIOUS_STATUSES:
        return "malicious"
    if statuses & SUSPICIOUS_STATUSES:
        return "suspicious"
    if statuses and statuses <= CLEAN_STATUSES:
        return "clean"
    if statuses & ERROR_STATUSES:
        return "error"
    return "pending"


def build_threat_enrichment(
    *,
    artifact_envelope: Mapping[str, Any],
    resolved_urls: Sequence[Mapping[str, Any]],
    provider_summary: Mapping[str, Any],
) -> Dict[str, Any]:
    """Normalize existing threat evidence without making a new verdict.

    The projection is intentionally shadow-only. `missing_evidence_blocks_safe`
    describes the future monotonic contract, but no current gate reads it.
    """

    urls_section = artifact_envelope.get("urls")
    urls_section = urls_section if isinstance(urls_section, Mapping) else {}
    url_count = int(urls_section.get("count") or 0)
    artifact_type = str(artifact_envelope.get("artifact_type") or "unknown")

    if url_count == 0:
        return {
            "schema": THREAT_ENRICHMENT_SCHEMA,
            "shadow_only": True,
            "artifact_type": artifact_type,
            "status": "not_required",
            "url_count": 0,
            "resolved_url_count": 0,
            "provider_verdict": "not_required",
            "provider_statuses": {},
            "malicious_providers": [],
            "suspicious_providers": [],
            "error_providers": [],
            "unconsulted_providers": [],
            "has_positive_threat_evidence": False,
            "missing_evidence_blocks_safe": False,
        }

    provider_statuses: Dict[str, str] = {}
    malicious_providers = []
    suspicious_providers = []
    error_providers = []
    pending_providers = []
    unconsulted_providers = []
    for name, raw_details in (provider_summary or {}).items():
        if not isinstance(raw_details, Mapping):
            continue
        normalized = _status(raw_details)
        provider_name = str(name)
        provider_statuses[provider_name] = normalized
        if not bool(raw_details.get("consulted", False)):
            unconsulted_providers.append(provider_name)
        if normalized in MALICIOUS_STATUSES:
            malicious_providers.append(provider_name)
        elif normalized in SUSPICIOUS_STATUSES:
            suspicious_providers.append(provider_name)
        elif normalized in ERROR_STATUSES:
            error_providers.append(provider_name)
        elif normalized in PENDING_STATUSES:
            pending_providers.append(provider_name)

    resolved_count = sum(
        1
        for item in resolved_urls or []
        if isinstance(item, Mapping)
        and bool(item.get("success", True))
        and bool(item.get("final_url") or item.get("url"))
    )
    providers_complete = (
        bool(provider_statuses)
        and not error_providers
        and not pending_providers
        and not unconsulted_providers
    )
    resolution_complete = resolved_count >= url_count
    status = "complete" if providers_complete and resolution_complete else "partial" if provider_statuses or resolved_count else "pending"
    provider_verdict = _provider_verdict(provider_statuses)

    return {
        "schema": THREAT_ENRICHMENT_SCHEMA,
        "shadow_only": True,
        "artifact_type": artifact_type,
        "status": status,
        "url_count": url_count,
        "resolved_url_count": resolved_count,
        "provider_verdict": provider_verdict,
        "provider_statuses": provider_statuses,
        "malicious_providers": sorted(malicious_providers),
        "suspicious_providers": sorted(suspicious_providers),
        "error_providers": sorted(error_providers),
        "unconsulted_providers": sorted(unconsulted_providers),
        "has_positive_threat_evidence": bool(malicious_providers or suspicious_providers),
        "missing_evidence_blocks_safe": not (providers_complete and resolution_complete),
    }
