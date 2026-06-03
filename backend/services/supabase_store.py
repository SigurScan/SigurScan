import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests


SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
SUPABASE_TIMEOUT_SECONDS = float(os.getenv("SUPABASE_TIMEOUT_SECONDS") or "4.0")


def is_supabase_enabled() -> bool:
    return bool(SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY)


def _headers(prefer: Optional[str] = None) -> Dict[str, str]:
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def _table_url(table: str) -> str:
    return f"{SUPABASE_URL}/rest/v1/{table}"


def _ts_to_iso(value: Any) -> Optional[str]:
    try:
        ts = int(value)
    except Exception:
        return None
    if ts <= 0:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _iso_to_ts(value: Any) -> Optional[int]:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        return int(datetime.fromisoformat(normalized).timestamp())
    except Exception:
        return None


def _post_json(table: str, payload: Dict[str, Any], prefer: str = "return=minimal") -> None:
    if not is_supabase_enabled():
        return
    try:
        requests.post(
            _table_url(table),
            headers=_headers(prefer),
            json=payload,
            timeout=SUPABASE_TIMEOUT_SECONDS,
        ).raise_for_status()
    except Exception:
        return


def _get_json(table: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not is_supabase_enabled():
        return []
    try:
        response = requests.get(
            _table_url(table),
            headers=_headers(),
            params=params,
            timeout=SUPABASE_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
    except Exception:
        return []
    return data if isinstance(data, list) else []


def log_scan_event(payload: Dict[str, Any]) -> None:
    row = {
        "scan_id": payload.get("scan_id"),
        "event_type": payload.get("event_type", "scan_completed"),
        "input_type": payload.get("input_type", "unknown"),
        "source_channel": payload.get("source_channel"),
        "risk_score": payload.get("risk_score", 0),
        "risk_level": payload.get("risk_level"),
        "user_risk_level": payload.get("user_risk_level"),
        "user_risk_label": payload.get("user_risk_label"),
        "detected_family_id": payload.get("detected_family_id"),
        "detected_family": payload.get("detected_family"),
        "claimed_brand": payload.get("claimed_brand"),
        "predicted_is_scam": payload.get("predicted_is_scam"),
        "signal_ids": payload.get("signal_ids") or [],
        "url_count": payload.get("url_count", 0),
        "urls": payload.get("urls") or [],
        "redacted_text_snippet": payload.get("redacted_text_snippet"),
        "evidence": payload.get("evidence") or {},
        "metadata": payload.get("metadata") or {},
    }
    created_at = _ts_to_iso(payload.get("timestamp"))
    if created_at:
        row["created_at"] = created_at
    if row["scan_id"]:
        _post_json("scan_events", row, "resolution=merge-duplicates,return=minimal")


def log_feedback_event(payload: Dict[str, Any]) -> None:
    row = {
        "scan_id": payload.get("scan_id"),
        "feedback": payload.get("feedback"),
        "actual_is_scam": payload.get("actual_is_scam"),
        "predicted_is_scam": payload.get("predicted_is_scam"),
        "predicted_risk_score": payload.get("predicted_risk_score"),
        "risk_level": payload.get("risk_level"),
        "signal_ids": payload.get("signal_ids") or [],
        "source_channel": payload.get("source_channel"),
        "notes": payload.get("notes"),
        "metadata": payload.get("metadata") or {},
    }
    created_at = _ts_to_iso(payload.get("timestamp"))
    if created_at:
        row["created_at"] = created_at
    if row["scan_id"] and row["feedback"]:
        _post_json("scan_feedback", row)


def load_scan_records(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {"select": "*", "order": "created_at.desc"}
    if isinstance(limit, int) and limit > 0:
        params["limit"] = str(limit)
    rows = _get_json("scan_events", params)
    output = []
    for row in reversed(rows):
        normalized = dict(row)
        normalized.setdefault("event_type", "scan_completed")
        ts = _iso_to_ts(normalized.get("created_at"))
        if ts:
            normalized["timestamp"] = ts
        output.append(normalized)
    return output


def load_feedback_records() -> List[Dict[str, Any]]:
    rows = _get_json("scan_feedback", {"select": "*", "order": "created_at.asc"})
    output = []
    for row in rows:
        normalized = dict(row)
        normalized.setdefault("event_type", "scan_feedback")
        ts = _iso_to_ts(normalized.get("created_at"))
        if ts:
            normalized["timestamp"] = ts
        output.append(normalized)
    return output


def load_reputation_cache() -> Dict[str, Any]:
    rows = _get_json("url_reputation_cache", {"select": "*"})
    cache: Dict[str, Any] = {}
    now = int(time.time())
    for row in rows:
        url_hash = row.get("url_hash")
        details = row.get("details") if isinstance(row.get("details"), dict) else {}
        if not url_hash or not details:
            continue
        cache[url_hash] = details
        cache[url_hash].setdefault("cached_at", now)
    return cache


def save_reputation_cache(cache: Dict[str, Any]) -> None:
    if not is_supabase_enabled() or not isinstance(cache, dict):
        return
    for url_hash, entry in cache.items():
        if not isinstance(entry, dict):
            continue
        expires_at = _ts_to_iso(entry.get("expires_at"))
        row = {
            "url_hash": url_hash,
            "canonical_url": entry.get("url"),
            "registered_domain": entry.get("registered_domain"),
            "verdict": entry.get("verdict", "unknown"),
            "risk_score": entry.get("risk_score", 0),
            "confidence": entry.get("confidence", 0),
            "sources": entry.get("sources") or {},
            "details": entry,
        }
        if expires_at:
            row["expires_at"] = expires_at
        _post_json("url_reputation_cache", row, "resolution=merge-duplicates,return=minimal")


def save_scan_job(job: Dict[str, Any]) -> None:
    if not is_supabase_enabled() or not isinstance(job, dict):
        return
    scan_id = job.get("scan_id")
    if not scan_id:
        return
    expires_at = _ts_to_iso(job.get("expires_at"))
    row = {
        "scan_id": scan_id,
        "status": job.get("status", "scanning"),
        "input_type": job.get("input_type", "unknown"),
        "source_channel": job.get("source_channel"),
        "payload": job,
    }
    if expires_at:
        row["expires_at"] = expires_at
    _post_json("scan_jobs", row, "resolution=merge-duplicates,return=minimal")


def load_scan_job(scan_id: str) -> Optional[Dict[str, Any]]:
    if not scan_id or not is_supabase_enabled():
        return None
    rows = _get_json(
        "scan_jobs",
        {
            "select": "payload",
            "scan_id": f"eq.{scan_id}",
            "limit": "1",
        },
    )
    if not rows:
        return None
    payload = rows[0].get("payload")
    return payload if isinstance(payload, dict) else None
