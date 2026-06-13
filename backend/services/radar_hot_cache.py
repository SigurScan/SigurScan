"""Hot-cache data for Radar / call-screening surfaces.

This module is intentionally data-only. It never produces a verdict and it never
stores raw phone numbers. The verdict remains owned by ``verdict_gate``.
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional


HOT_CACHE_TTL_MINUTES = int(os.getenv("RADAR_HOT_CACHE_TTL_MINUTES", "60"))

_FAMILY_WARNINGS: Dict[str, Dict[str, str]] = {
    "CONV_BANK_SAFE_ACCOUNT": {
        "title": "Apel care pretinde banca, BNR sau Poliția",
        "body": "Nu muta banii într-un cont „sigur”. Închide și sună banca la numărul de pe card.",
    },
    "CONV_COURIER_TAX_CARD": {
        "title": "Curier fals care cere o taxă",
        "body": "Curierii reali nu cer date de card prin SMS sau apel. Verifică în aplicația oficială.",
    },
    "CONV_INVESTMENT_DEEPFAKE": {
        "title": "Investiție „garantată” cu o persoană cunoscută",
        "body": "Nu depune bani pe promisiuni de profit rapid. Verifică firma și autorizația pe canale oficiale.",
    },
    "CONV_TECH_SUPPORT_REMOTE": {
        "title": "Suport tehnic fals",
        "body": "Nu instala AnyDesk, TeamViewer sau aplicații similare la cererea unui apel.",
    },
    "CONV_FAMILY_NEW_PHONE": {
        "title": "Mesaj/apel: „am număr nou”",
        "body": "Sună persoana la numărul vechi salvat înainte să trimiți bani.",
    },
    "CONV_WHATSAPP_TAKEOVER": {
        "title": "Tentativă de preluare WhatsApp",
        "body": "Nu trimite coduri primite prin SMS. Activează verificarea în doi pași.",
    },
}

_DEFAULT_WARNING = {
    "title": "Element semnalat în campanii recente",
    "body": "Nu oferi date sau bani. Verifică pe canalul oficial înainte să continui.",
}


def hot_warning_for_family(family: Optional[str]) -> Dict[str, str]:
    return dict(_FAMILY_WARNINGS.get(family or "", _DEFAULT_WARNING))


def reputation_bucket(report_count: Any) -> str:
    """Return non-PII buckets instead of exposing exact report counts."""
    try:
        count = int(report_count)
    except (TypeError, ValueError):
        count = 0
    if count <= 0:
        return "0"
    if count <= 4:
        return "1-4"
    if count <= 24:
        return "5-24"
    if count <= 99:
        return "25-99"
    return "100+"


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def build_hot_cache(
    campaign_store: Any,
    *,
    reports: Optional[List[Dict[str, Any]]] = None,
    since: Optional[float] = None,
) -> Dict[str, Any]:
    """Build the Radar hot-cache payload from approved campaigns and hashed reports."""
    now = time.time()
    since_ts = since if since is not None else now - 7 * 86400
    active_campaigns = campaign_store.active(since=since_ts) if campaign_store is not None else []

    hot_campaigns: List[Dict[str, Any]] = []
    for intel in active_campaigns:
        iocs = intel.iocs if isinstance(intel.iocs, dict) else {}
        warning = hot_warning_for_family(intel.family)
        hot_campaigns.append(
            {
                "campaign_id": intel.intel_id,
                "family": intel.family,
                "warning_title": warning["title"],
                "warning_body": warning["body"],
                "regions": list(intel.regions_hint or ["RO"]),
                "phone_hash_prefixes": list(iocs.get("phone_hash_prefixes") or []),
                "confidence": intel.evidence_quality,
            }
        )

    number_reputation: List[Dict[str, Any]] = []
    for report in reports or []:
        target_hash = report.get("hash") or report.get("target_hash")
        if not target_hash:
            continue
        number_reputation.append(
            {
                "phone_hash": target_hash,
                "status": "reported",
                "family": report.get("family"),
                "bucket_count": reputation_bucket(report.get("report_count", 0)),
            }
        )

    return {
        "generated_at": _now_iso(),
        "ttl_minutes": HOT_CACHE_TTL_MINUTES,
        "hot_campaigns": hot_campaigns,
        "number_reputation": number_reputation,
    }
