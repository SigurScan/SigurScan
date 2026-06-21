"""Community report + push registration routes.

Self-contained: write-through to Supabase (best-effort) plus push-device upsert.
Extracted from main.py.
"""

import re
import logging
from datetime import datetime, timezone

import requests
from fastapi import APIRouter, HTTPException

from services import supabase_store
from api_models import CommunityReportRequest, PushRegisterRequest

router = APIRouter()
logger = logging.getLogger("sigurscan.community")


@router.post("/v1/community/report")
def community_report(payload: CommunityReportRequest):
    normalized_hash = payload.hash.strip().lower()
    normalized_target_type = payload.target_type.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", normalized_hash):
        raise HTTPException(status_code=400, detail="hash must be a SHA-256 hex digest.")
    if normalized_target_type not in {"phone", "url", "text", "email", "iban", "unknown"}:
        raise HTTPException(status_code=400, detail="invalid target_type.")

    has_supabase = supabase_store.is_supabase_enabled()
    if not has_supabase:
        return {"status": "accepted", "stored": False, "note": "supabase not configured"}

    try:
        existing = supabase_store._get_json(
            "community_reports",
            {"hash": f"eq.{normalized_hash}", "target_type": f"eq.{normalized_target_type}"},
        )
        if existing:
            row_id = existing[0]["id"]
            requests.patch(
                supabase_store._table_url("community_reports") + f"?id=eq.{row_id}",
                headers=supabase_store._headers("return=minimal"),
                json={
                    "report_count": existing[0].get("report_count", 0) + 1,
                    "last_reported_at": datetime.now(timezone.utc).isoformat(),
                },
                timeout=supabase_store.SUPABASE_TIMEOUT_SECONDS,
            )
        else:
            supabase_store._post_json("community_reports", {
                "hash": normalized_hash,
                "risk_level": payload.risk_level,
                "family": payload.family,
                "source": payload.source,
                "target_type": normalized_target_type,
            })
        supabase_store.save_reputation_observation({
            "target_type": normalized_target_type,
            "target_hash": normalized_hash,
            "source": payload.source,
            "risk_level": payload.risk_level,
            "family": payload.family,
            "report_count": 1,
        })
    except Exception as exc:
        logger.warning(
            "community_report: storage failed target_type=%s source=%s error=%s",
            normalized_target_type,
            payload.source,
            exc.__class__.__name__,
        )
        raise HTTPException(status_code=503, detail="report storage unavailable")
    return {"status": "ok", "stored": True}


@router.get("/v1/community/campaigns")
def community_campaigns(status: str = "active", limit: int = 20):
    has_supabase = supabase_store.is_supabase_enabled()
    if not has_supabase:
        logger.warning("community_campaigns: supabase not enabled")
        return []

    _status_map = {
        "active": "activă",
        "confirmed": "confirmată",
        "watch": "monitorizare",
    }

    try:
        params: Dict[str, Any] = {"select": "*", "order": "last_seen.desc"}
        if status:
            mapped = _status_map.get(status, status)
            params["status"] = f"eq.{mapped}"
        if limit > 0:
            params["limit"] = str(limit)
        rows = supabase_store._get_json("scam_campaigns", params)
        logger.info(f"community_campaigns: got {len(rows)} rows for status={status}")
        if not rows:
            logger.warning(f"community_campaigns: empty result. url={supabase_store.SUPABASE_URL}")
            try:
                debug_resp = requests.get(
                    supabase_store._table_url("scam_campaigns"),
                    headers=supabase_store._headers(),
                    params={"select": "count", "limit": "1"},
                    timeout=supabase_store.SUPABASE_TIMEOUT_SECONDS,
                )
                logger.warning(f"community_campaigns debug: status={debug_resp.status_code} body={debug_resp.text[:200]}")
            except Exception as e:
                logger.warning(f"community_campaigns debug error: {e}")
        return [
            {
                "id": r.get("id", ""),
                "title": r.get("title", ""),
                "brand": r.get("brand", ""),
                "riskLevel": r.get("risk_level", "dangerous"),
                "region": r.get("region"),
                "lat": r.get("lat"),
                "lon": r.get("lon"),
                "scanCount": r.get("scan_count", 0),
                "firstSeen": r.get("first_seen", ""),
                "lastSeen": r.get("last_seen", ""),
                "status": r.get("status", "activă"),
                "description": r.get("description", ""),
                "safeAction": r.get("safe_action", ""),
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"community_campaigns error: {e}")
        return []


@router.post("/v1/push/register")
def push_register(payload: PushRegisterRequest):
    if not supabase_store.is_supabase_enabled():
        return {"status": "ok", "note": "supabase not configured"}

    try:
        supabase_store._post_json("push_devices", {
            "token": payload.token,
            "platform": payload.platform,
            "locale": payload.locale,
            "last_seen_at": datetime.now(timezone.utc).isoformat(),
        }, prefer="resolution=merge-duplicates,return=minimal")
    except Exception:
        pass
    return {"status": "ok"}
