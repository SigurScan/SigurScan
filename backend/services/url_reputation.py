"""URL reputation aggregation service with multi-source support.

This module performs:
- multi-source lookups (Google Web Risk, Phishing.Database, URLhaus, Scam-Blocklist NRD, PhishDestroy);
- per-source confidence scoring;
- cache-safe persistence with source metadata;
- aggregated verdict/reputation payload used by ScamAtlas.
"""

import bz2
import csv
import gzip
import hashlib
import html
import io
import json
import os
import re
import time
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, urlunparse

import requests

from services import supabase_store
from services.google_web_risk import check_urls_against_web_risk, has_web_risk_key


from services.url_reputation_config import (
    WEB_RISK_SOURCE,
    PHISHING_DATABASE_SOURCE,
    PHISHTANK_SOURCE,
    OPENPHISH_SOURCE,
    URLHAUS_SOURCE,
    SCAM_BLOCKLIST_NRD_SOURCE,
    PHISHDESTROY_SOURCE,
    ASF_INVESTOR_ALERTS_SOURCE,
    WEB_RISK_WEIGHT,
    PHISHING_DATABASE_WEIGHT,
    PHISHTANK_WEIGHT,
    OPENPHISH_WEIGHT,
    URLHAUS_WEIGHT,
    SCAM_BLOCKLIST_NRD_WEIGHT,
    PHISHDESTROY_WEIGHT,
    ASF_INVESTOR_ALERTS_WEIGHT,
    SOURCE_ORDER,
    SOURCE_WEIGHTS,
    SOURCE_STATUS_WEIGHTS,
    REPUTATION_CACHE_VERSION,
    ASF_INVESTOR_ALERTS_URL,
    PHISHING_DATABASE_DOMAINS_URL,
    PHISHING_DATABASE_LINKS_URL,
    PHISHTANK_ONLINE_VALID_BZ2_URL,
    PHISHTANK_ONLINE_VALID_GZ_URL,
    PHISHTANK_ONLINE_VALID_URL,
    OPENPHISH_FEED_URL,
    URLHAUS_API_URL,
    URLHAUS_RECENT_CSV_URL,
    SCAM_BLOCKLIST_NRD_URL,
    SCAM_BLOCKLIST_NRD_LICENSE,
    PHISHDESTROY_URL,
    PHISHDESTROY_API_URL,
    PHISHDESTROY_LICENSE,
    PHISHING_DATABASE_TIMEOUT_SECONDS,
    PHISHING_DATABASE_FEED_TTL_SECONDS,
    PHISHTANK_TIMEOUT_SECONDS,
    PHISHTANK_FEED_TTL_SECONDS,
    OPENPHISH_FEED_TTL_SECONDS,
    PHISHTANK_USER_AGENT,
    SCAM_BLOCKLIST_NRD_TIMEOUT_SECONDS,
    SCAM_BLOCKLIST_NRD_FEED_TTL_SECONDS,
    PHISHDESTROY_TIMEOUT_SECONDS,
    PHISHDESTROY_FEED_TTL_SECONDS,
    ASF_INVESTOR_ALERTS_TIMEOUT_SECONDS,
    ASF_INVESTOR_ALERTS_FEED_TTL_SECONDS,
    URLHAUS_TIMEOUT_SECONDS,
    URLHAUS_RECENT_FEED_TTL_SECONDS,
    URLHAUS_AUTH_KEY,
    ENABLE_PHISHING_DATABASE,
    ENABLE_PHISHTANK,
    ENABLE_OPENPHISH,
    ENABLE_SCAM_BLOCKLIST_NRD,
    ENABLE_PHISHDESTROY,
    ENABLE_ASF_INVESTOR_ALERTS,
    PHISHING_DATABASE_MAX_FEED_BYTES,
    PHISHTANK_MAX_FEED_BYTES,
    OPENPHISH_MAX_FEED_BYTES,
    SCAM_BLOCKLIST_NRD_MAX_FEED_BYTES,
    PHISHDESTROY_MAX_FEED_BYTES,
    ASF_INVESTOR_ALERTS_MAX_FEED_BYTES,
    URLHAUS_RECENT_MAX_FEED_BYTES,
    DEFAULT_CACHE_TTL_SECONDS,
    MAX_REPUTATION_URLS,
    REPUTATION_CACHE_MAX_ITEMS,
    DEFAULT_REPUTATION_CACHE_PATH,
    DEFAULT_LOCAL_PHISHING_LOOKALIKE_PATH,
    LOCAL_PHISHING_LOOKALIKE_PATH,
    REPUTATION_CACHE_PATH,
    REPUTATION_CACHE_TTL_SECONDS,
    ENABLE_URL_REPUTATION,
)

_PHISHING_DATABASE_CACHE: Dict[str, Any] = {
    "loaded_at": 0,
    "domains": set(),
    "links": set(),
    "link_hashes": set(),
    "error": None,
}
_PHISHTANK_CACHE: Dict[str, Any] = {
    "loaded_at": 0,
    "links": set(),
    "link_hashes": set(),
    "metadata": {},
    "metadata_by_hash": {},
    "error": None,
    "source_url": PHISHTANK_ONLINE_VALID_URL,
}
_OPENPHISH_CACHE: Dict[str, Any] = {
    "loaded_at": 0,
    "links": set(),
    "link_hashes": set(),
    "error": None,
    "source_url": OPENPHISH_FEED_URL,
}
_SCAM_BLOCKLIST_NRD_CACHE: Dict[str, Any] = {
    "loaded_at": 0,
    "domains": set(),
    "error": None,
    "source_url": SCAM_BLOCKLIST_NRD_URL,
    "license": SCAM_BLOCKLIST_NRD_LICENSE,
}
_PHISHDESTROY_CACHE: Dict[str, Any] = {
    "loaded_at": 0,
    "domains": set(),
    "error": None,
    "source_url": PHISHDESTROY_URL,
    "api_url": PHISHDESTROY_API_URL,
    "license": PHISHDESTROY_LICENSE,
}
_ASF_INVESTOR_ALERTS_CACHE: Dict[str, Any] = {
    "loaded_at": 0,
    "domains": set(),
    "error": None,
    "source_url": ASF_INVESTOR_ALERTS_URL,
    "source_publisher": "Autoritatea de Supraveghere Financiară",
}
_URLHAUS_RECENT_CACHE: Dict[str, Any] = {
    "loaded_at": 0,
    "links": set(),
    "link_hashes": set(),
    "metadata": {},
    "metadata_by_hash": {},
    "error": None,
    "source_url": URLHAUS_RECENT_CSV_URL,
}



def _normalize_url_for_key(url: str) -> str:
    return (url or "").strip()


def _url_hash(url: str) -> str:
    normalized = _normalize_url_for_key(url).encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def reputation_url_hash_variants(url: str) -> List[str]:
    """Return stable hashes for exact-feed matching without storing raw URLs."""
    hashes: set[str] = set()
    raw = _normalize_url_for_key(url)
    if raw:
        hashes.add(_url_hash(raw))
    for variant in _canonical_url_variants(raw):
        if variant:
            hashes.add(_url_hash(variant))
    return sorted(hashes)


def _normalize_lookup_hashes(values: Any) -> set[str]:
    output: set[str] = set()
    if not isinstance(values, (list, tuple, set)):
        return output
    for value in values:
        candidate = str(value or "").strip().lower()
        if re.fullmatch(r"[a-f0-9]{64}", candidate):
            output.add(candidate)
    return output


def _normalize_lookup_hash_map(values: Any) -> Dict[str, set[str]]:
    output: Dict[str, set[str]] = {}
    if not isinstance(values, dict):
        return output
    for raw_url, raw_hashes in values.items():
        url = _normalize_url_for_key(str(raw_url or ""))
        hashes = _normalize_lookup_hashes(raw_hashes)
        if url and hashes:
            output.setdefault(url, set()).update(hashes)
            for variant in _canonical_url_variants(url):
                output.setdefault(variant, set()).update(hashes)
    return output


def _lookup_hashes_for_url(
    url: str,
    lookup_hashes: set[str],
    lookup_hashes_by_url: Dict[str, set[str]],
) -> set[str]:
    output = set(lookup_hashes)
    normalized = _normalize_url_for_key(url)
    if normalized in lookup_hashes_by_url:
        output.update(lookup_hashes_by_url[normalized])
    for variant in _canonical_url_variants(normalized):
        output.update(lookup_hashes_by_url.get(variant, set()))
    return output


def _feed_link_hashes(feed: Dict[str, Any]) -> set[str]:
    cached = feed.get("link_hashes")
    if isinstance(cached, set):
        return cached
    links = feed.get("links") if isinstance(feed.get("links"), set) else set()
    hashes = {_url_hash(link) for link in links if isinstance(link, str) and link}
    feed["link_hashes"] = hashes
    return hashes


def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _clamp_int(value: Any, *, min_value: int, max_value: int, default: int = 0) -> int:
    try:
        numeric = int(value)
    except Exception:
        return default
    return max(min_value, min(max_value, numeric))


def _normalize_status(raw_status: Any) -> str:
    status = (str(raw_status).strip().lower() if raw_status is not None else "")
    if status in {"malicious", "suspicious", "clean", "error", "unknown"}:
        return status
    return "unknown"


def _normalize_source_entry(
    source_name: str,
    payload: Dict[str, Any] | None,
    *,
    consulted: bool,
    weight: int,
    fallback_status: str,
) -> Dict[str, Any]:
    payload = dict(payload or {})
    status = _normalize_status(payload.get("status", fallback_status))
    details = payload.get("details", {})

    entry: Dict[str, Any] = {
        "source": source_name,
        "status": status,
        "weight": int(weight),
        "consulted": bool(consulted),
        "risk_contribution": round(weight * SOURCE_STATUS_WEIGHTS.get(status, 0.0), 2),
        "score": _clamp_int(payload.get("score", 0), min_value=0, max_value=100),
        "threat_type": str(payload.get("threat_type", "unknown")).lower(),
    }
    if isinstance(details, dict) and details:
        entry["details"] = details
    if payload.get("error") is not None:
        entry["error"] = str(payload.get("error"))
    if payload.get("query_ms") is not None:
        entry["query_ms"] = _coerce_int(payload.get("query_ms", 0), 0)
    return entry


def _load_cache(path: Path) -> Dict[str, Any]:
    remote_cache = supabase_store.load_reputation_cache()
    if remote_cache:
        return remote_cache
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception:
        return {}
    if isinstance(payload, dict):
        return payload
    return {}


def _prune_cache_for_save(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    max_items = max(0, REPUTATION_CACHE_MAX_ITEMS)
    if max_items <= 0 or len(data) <= max_items:
        return data
    now = int(time.time())
    valid_items = [
        (key, value)
        for key, value in data.items()
        if isinstance(value, dict) and _coerce_int(value.get("expires_at", 0), 0) > now
    ]
    if len(valid_items) < max_items:
        valid_items = [(key, value) for key, value in data.items() if isinstance(value, dict)]

    def sort_key(item: tuple[str, Dict[str, Any]]) -> int:
        value = item[1]
        return max(
            _coerce_int(value.get("cached_at", 0), 0),
            _coerce_int(value.get("created_at", 0), 0),
            _coerce_int(value.get("expires_at", 0), 0) - REPUTATION_CACHE_TTL_SECONDS,
        )

    kept = sorted(valid_items, key=sort_key, reverse=True)[:max_items]
    return {key: value for key, value in kept}


def _save_cache(path: Path, data: Dict[str, Any], remote_subset: Optional[Dict[str, Any]] = None) -> None:
    # Local file cache keeps the full snapshot, but Supabase must only receive
    # entries touched by this request. Upserting the entire cache for one URL
    # turns a single reputation lookup into hundreds of network writes.
    supabase_store.save_reputation_cache(remote_subset if remote_subset is not None else data)
    try:
        pruned_data = _prune_cache_for_save(data)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(pruned_data, f, ensure_ascii=False, indent=2, sort_keys=True)
    except Exception:
        # Cache persistence is best-effort only.
        return


def _load_cache_entry(cache: Dict[str, Any], url: str) -> Optional[Dict[str, Any]]:
    key = _url_hash(url)
    raw = cache.get(key)
    if not isinstance(raw, dict):
        return None
    if raw.get("version", REPUTATION_CACHE_VERSION) < 2:
        # old schema migration path: keep only what can be safely reused
        return None
    return raw


def _is_cache_entry_valid(entry: Dict[str, Any], now: int) -> bool:
    if not isinstance(entry, dict):
        return False
    if not entry.get("verdict"):
        return False
    sources = entry.get("sources")
    if isinstance(sources, dict) and any(
        isinstance(source_payload, dict) and _normalize_status(source_payload.get("status")) == "error"
        for source_payload in sources.values()
    ):
        return False
    expires_at = _coerce_int(entry.get("expires_at", 0))
    return expires_at > now


def _cache_entry_covers_requested_sources(
    entry: Dict[str, Any],
    *,
    include_asf_investor_alerts: bool,
    include_phishing_database: bool,
    include_phishtank: bool,
    include_openphish: bool,
    include_urlhaus: bool,
    include_scam_blocklist_nrd: bool,
    include_phishdestroy: bool,
    urlhaus_key: str,
    web_risk_enabled: bool,
) -> bool:
    sources = entry.get("sources")
    if not isinstance(sources, dict):
        return False

    required_sources: List[str] = []
    if web_risk_enabled:
        required_sources.append(WEB_RISK_SOURCE)
    if include_asf_investor_alerts and ENABLE_ASF_INVESTOR_ALERTS:
        required_sources.append(ASF_INVESTOR_ALERTS_SOURCE)
    if include_phishing_database and ENABLE_PHISHING_DATABASE:
        required_sources.append(PHISHING_DATABASE_SOURCE)
    if include_phishtank and ENABLE_PHISHTANK:
        required_sources.append(PHISHTANK_SOURCE)
    if include_openphish and ENABLE_OPENPHISH:
        required_sources.append(OPENPHISH_SOURCE)
    if include_urlhaus:
        required_sources.append(URLHAUS_SOURCE)
    if include_scam_blocklist_nrd and ENABLE_SCAM_BLOCKLIST_NRD:
        required_sources.append(SCAM_BLOCKLIST_NRD_SOURCE)
    if include_phishdestroy and ENABLE_PHISHDESTROY:
        required_sources.append(PHISHDESTROY_SOURCE)

    for source_name in required_sources:
        source_payload = sources.get(source_name)
        if not isinstance(source_payload, dict) or not source_payload.get("consulted"):
            return False
    return True


def _normalize_cached_entry(entry: Dict[str, Any], url: str, ttl: int) -> Dict[str, Any]:
    cached_at = _coerce_int(entry.get("cached_at", int(time.time())))
    created_at = _coerce_int(entry.get("created_at", cached_at))
    expires_at = _coerce_int(entry.get("expires_at", created_at + ttl))

    normalized: Dict[str, Any] = {
        "url": url,
        "url_hash": _url_hash(url),
        "cached": True,
        "created_at": created_at,
        "cached_at": cached_at,
        "expires_at": expires_at,
        "version": REPUTATION_CACHE_VERSION,
        "verdict": _normalize_status(entry.get("verdict", "unknown")),
        "risk_score": _clamp_int(entry.get("risk_score", 0), min_value=0, max_value=100),
        "confidence": float(entry.get("confidence", 0.0) or 0.0),
        "signals": list(entry.get("signals", [])),
        "active_sources": list(entry.get("active_sources", [])),
        "signal_count": int(entry.get("signal_count", 0)),
        "source_count": int(entry.get("source_count", 0)),
        "consulted_sources": list(entry.get("consulted_sources", [])),
        "consulted_source_count": int(entry.get("consulted_source_count", 0)),
    }

    raw_sources = entry.get("sources")
    if not isinstance(raw_sources, dict):
        raw_sources = {}
    normalized_sources: Dict[str, Any] = {}
    for source_name in SOURCE_ORDER:
        normalized_sources[source_name] = _normalize_source_entry(
            source_name=source_name,
            payload=raw_sources.get(source_name),
            consulted=bool(
                isinstance(raw_sources.get(source_name), dict)
                and raw_sources[source_name].get("consulted", False)
            ),
            weight=SOURCE_WEIGHTS.get(source_name, 0),
            fallback_status="unknown",
        )
        if not isinstance(raw_sources.get(source_name), dict):
            normalized_sources[source_name]["consulted"] = False
            normalized_sources[source_name]["status"] = "unknown"
            normalized_sources[source_name]["risk_contribution"] = 0.0

    normalized["sources"] = normalized_sources
    normalized["source_count"] = len(SOURCE_ORDER)
    normalized["consulted_sources"] = sorted(
        source for source, source_row in normalized_sources.items()
        if isinstance(source_row, dict) and source_row.get("consulted")
    )
    normalized["consulted_source_count"] = len(normalized["consulted_sources"])
    normalized["cache_metadata"] = {
        "version": int(entry.get("cache_metadata", {}).get("version", REPUTATION_CACHE_VERSION)),
        "last_saved_at": expires_at - ttl,
        "ttl_seconds": ttl,
        "source_count": len(normalized["sources"]),
        "consulted_source_count": normalized["consulted_source_count"],
        "from_cache": True,
    }

    return normalized


def get_reputation_cache_stats() -> Dict[str, Any]:
    """Return cache observability useful for production monitoring."""

    now = int(time.time())
    path = REPUTATION_CACHE_PATH
    stats = {
        "enabled": ENABLE_URL_REPUTATION,
        "cache_path": str(path),
        "ttl_seconds": REPUTATION_CACHE_TTL_SECONDS,
        "cache_version": REPUTATION_CACHE_VERSION,
        "now": now,
        "exists": path.exists(),
        "loaded": False,
        "load_error": None,
        "items": 0,
        "valid_items": 0,
        "expired_items": 0,
        "invalid_items": 0,
        "verdict_counts": {},
        "source_stats": {},
        "provider_errors": {},
        "metadata": {
            "source_entries_without_payload": 0,
            "source_entries_without_version": 0,
            "items_missing_verdict": 0,
            "items_missing_expiration": 0,
        },
        "ttl_remaining_seconds": {
            "min": None,
            "max": None,
            "avg": None,
        },
    }

    if not ENABLE_URL_REPUTATION:
        return stats

    cache = _load_cache(path)
    if not cache and not path.exists():
        return stats
    if not isinstance(cache, dict):
        stats["load_error"] = "invalid_cache_payload"
        return stats

    stats["loaded"] = True

    verdict_counts: Counter[str] = Counter()
    remaining_seconds: List[int] = []
    provider_errors: Counter[str] = Counter()

    for source in SOURCE_ORDER:
        stats["source_stats"][source] = {
            "entries": 0,
            "consulted": 0,
            "not_consulted": 0,
            "status_counts": {
                "malicious": 0,
                "suspicious": 0,
                "clean": 0,
                "unknown": 0,
                "error": 0,
            },
        }

    for raw_entry in cache.values():
        if not isinstance(raw_entry, dict):
            stats["invalid_items"] += 1
            continue

        version = _coerce_int(raw_entry.get("version", 0), 0)
        if version < REPUTATION_CACHE_VERSION:
            stats["metadata"]["source_entries_without_version"] += 1
            stats["invalid_items"] += 1
            continue

        stats["items"] += 1

        verdict = _normalize_status(raw_entry.get("verdict", "unknown"))
        verdict_counts[verdict] += 1
        if not raw_entry.get("verdict"):
            stats["metadata"]["items_missing_verdict"] += 1

        expires_at = _coerce_int(raw_entry.get("expires_at", 0), 0)
        if not expires_at:
            stats["metadata"]["items_missing_expiration"] += 1
            stats["invalid_items"] += 1
            continue

        if _is_cache_entry_valid(raw_entry, now):
            stats["valid_items"] += 1
            remaining_seconds.append(expires_at - now)
        else:
            stats["expired_items"] += 1

        sources = raw_entry.get("sources")
        if not isinstance(sources, dict):
            stats["metadata"]["source_entries_without_payload"] += 1
            continue

        for source in SOURCE_ORDER:
            source_stats = stats["source_stats"][source]
            source_stats["entries"] += 1

            source_payload = sources.get(source)
            if not isinstance(source_payload, dict):
                source_stats["not_consulted"] += 1
                source_stats["status_counts"]["unknown"] += 1
                continue

            consulted = bool(source_payload.get("consulted", False))
            if consulted:
                source_stats["consulted"] += 1
            else:
                source_stats["not_consulted"] += 1

            status = _normalize_status(source_payload.get("status", "unknown"))
            if status in source_stats["status_counts"]:
                source_stats["status_counts"][status] += 1
            else:
                source_stats["status_counts"]["unknown"] += 1

            if status == "error":
                provider_errors[source] += 1

    stats["verdict_counts"] = dict(verdict_counts)
    stats["provider_errors"] = dict(provider_errors)

    if remaining_seconds:
        stats["ttl_remaining_seconds"]["min"] = min(remaining_seconds)
        stats["ttl_remaining_seconds"]["max"] = max(remaining_seconds)
        stats["ttl_remaining_seconds"]["avg"] = int(sum(remaining_seconds) / len(remaining_seconds))

    return stats


def _build_cache_entry(url: str, reputation: Dict[str, Any], ttl: int, cache_metadata: Dict[str, Any]) -> Dict[str, Any]:
    now = int(time.time())
    verdict = _normalize_status(reputation.get("verdict", "unknown"))
    result = dict(reputation)
    result.update({
        "url": url,
        "url_hash": _url_hash(url),
        "created_at": now,
        "cached_at": now,
        "expires_at": now + ttl,
        "cached": False,
        "version": REPUTATION_CACHE_VERSION,
        "verdict": verdict,
    })
    cache_data = dict(result)
    cache_data["cache_metadata"] = dict(cache_metadata)
    return cache_data


def _parse_urlhaus_record(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {}

    query_status = (payload.get("query_status") or "").lower()
    if query_status != "ok":
        return {}

    if payload.get("url_status", "").lower() in {"online", "offline"}:
        return {
            "status": "malicious" if payload.get("url_status", "").lower() == "online" else "suspicious",
            "threat_type": str(payload.get("threat", "unknown")),
            "details": str(payload.get("comment", "")),
            "last_seen": payload.get("date_added"),
        }

    if payload.get("payload", "").strip():
        return {
            "status": "malicious",
            "threat_type": str(payload.get("threat", "unknown")),
            "details": str(payload.get("comment", "")),
            "last_seen": payload.get("date_added"),
        }
    return {}


def _download_text_feed(
    url: str,
    *,
    timeout_seconds: float = PHISHING_DATABASE_TIMEOUT_SECONDS,
    max_bytes: int = PHISHING_DATABASE_MAX_FEED_BYTES,
) -> str:
    response = requests.get(url, timeout=timeout_seconds)
    response.raise_for_status()
    content = response.content[:max_bytes + 1]
    if len(content) > max_bytes:
        raise ValueError(f"feed_too_large:{url}")
    return content.decode("utf-8", errors="ignore")


def _phishtank_feed_candidate_urls() -> List[str]:
    default_csv_url = "https://data.phishtank.com/data/online-valid.csv"
    configured_url = str(PHISHTANK_ONLINE_VALID_URL or "").strip()
    candidates: List[str] = []

    # Respect custom feeds first. For the default public feed, prefer compressed
    # formats because the plain CSV endpoint can intermittently fail behind CDN
    # redirects while the compressed variants remain available.
    if configured_url and configured_url != default_csv_url:
        candidates.append(configured_url)

    candidates.extend([
        str(PHISHTANK_ONLINE_VALID_BZ2_URL or "").strip(),
        str(PHISHTANK_ONLINE_VALID_GZ_URL or "").strip(),
        configured_url or default_csv_url,
    ])

    ordered: List[str] = []
    for url in candidates:
        if url and url not in ordered:
            ordered.append(url)
    return ordered


def _decode_phishtank_feed_payload(url: str, content: bytes) -> str:
    lower_url = url.lower()
    if lower_url.endswith(".bz2") or content.startswith(b"BZh"):
        content = bz2.decompress(content)
    elif lower_url.endswith(".gz") or content.startswith(b"\x1f\x8b"):
        content = gzip.decompress(content)
    return content.decode("utf-8-sig", errors="ignore")


def _download_phishtank_feed() -> str:
    errors: List[str] = []
    for url in _phishtank_feed_candidate_urls():
        try:
            response = requests.get(
                url,
                timeout=PHISHTANK_TIMEOUT_SECONDS,
                headers={
                    "User-Agent": PHISHTANK_USER_AGENT,
                    "Cache-Control": "no-cache",
                },
            )
            response.raise_for_status()
            content = response.content[:PHISHTANK_MAX_FEED_BYTES + 1]
            if len(content) > PHISHTANK_MAX_FEED_BYTES:
                raise ValueError(f"feed_too_large:{url}")
            return _decode_phishtank_feed_payload(url, content)
        except Exception as exc:
            errors.append(f"{url}:{type(exc).__name__}:{exc}")
            continue
    raise RuntimeError("phishtank_feed_unavailable:" + " | ".join(errors))


def _feed_lines(text: str) -> set[str]:
    values: set[str] = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("!"):
            continue
        values.add(line.lower())
    return values


def _load_local_phishing_lookalikes(path: Path | None = None) -> Dict[str, Any]:
    source_path = path or LOCAL_PHISHING_LOOKALIKE_PATH
    if not source_path.exists():
        return {"domains": set(), "metadata": {}}
    try:
        with open(source_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {"domains": set(), "metadata": {}}

    domains: set[str] = set()
    metadata: Dict[str, Dict[str, Any]] = {}
    for item in data.get("phishing_domains") or []:
        if not isinstance(item, dict):
            continue
        domain = str(item.get("domain") or "").strip(".").lower()
        if not domain or "/" in domain or "." not in domain:
            continue
        confidence = str(item.get("confidence") or "").strip().lower()
        if confidence not in {"high", "medium"}:
            continue
        domains.add(domain)
        metadata[domain] = {
            "source": "local_phishing_lookalikes",
            "source_url": item.get("source_url"),
            "source_publisher": item.get("source_publisher"),
            "reported_at": item.get("reported_at"),
            "confidence": confidence,
            "impersonates_brand": item.get("impersonates_brand"),
            "scam_type": item.get("scam_type"),
        }
    return {"domains": domains, "metadata": metadata}


def _scam_blocklist_domain_lines(text: str) -> set[str]:
    domains: set[str] = set()
    for raw_line in text.splitlines():
        line = raw_line.strip().lower()
        if not line or line.startswith("#") or line.startswith("!"):
            continue
        if line.startswith("0.0.0.0 ") or line.startswith("127.0.0.1 "):
            parts = line.split()
            line = parts[1] if len(parts) > 1 else ""
        if line.startswith("||"):
            line = line[2:]
        if line.startswith("*."):
            line = line[2:]
        line = line.rstrip("^").strip(".")
        if not line or "/" in line or "$" in line or "[" in line or "]" in line:
            continue
        if " " in line or "\t" in line or "." not in line:
            continue
        domains.add(line)
    return domains


def _load_phishing_database_feeds() -> Dict[str, Any]:
    now = int(time.time())
    cached_at = _coerce_int(_PHISHING_DATABASE_CACHE.get("loaded_at", 0), 0)
    if cached_at and now - cached_at < PHISHING_DATABASE_FEED_TTL_SECONDS:
        return _PHISHING_DATABASE_CACHE

    if not ENABLE_PHISHING_DATABASE:
        _PHISHING_DATABASE_CACHE.update({
            "loaded_at": now,
            "domains": set(),
            "links": set(),
            "link_hashes": set(),
            "error": "disabled",
        })
        return _PHISHING_DATABASE_CACHE

    local = _load_local_phishing_lookalikes()
    local_domains = local.get("domains") if isinstance(local.get("domains"), set) else set()
    local_metadata = local.get("metadata") if isinstance(local.get("metadata"), dict) else {}

    try:
        domains_text = _download_text_feed(PHISHING_DATABASE_DOMAINS_URL)
        links_text = _download_text_feed(PHISHING_DATABASE_LINKS_URL)
        remote_domains = _feed_lines(domains_text)
        remote_links: set[str] = set()
        for raw_url in _feed_lines(links_text):
            remote_links.update(_canonical_url_variants(raw_url))
        _PHISHING_DATABASE_CACHE.update({
            "loaded_at": now,
            "domains": remote_domains | local_domains,
            "local_domains": local_domains,
            "local_metadata": local_metadata,
            "links": remote_links,
            "error": None,
            "domains_url": PHISHING_DATABASE_DOMAINS_URL,
            "links_url": PHISHING_DATABASE_LINKS_URL,
        })
        _PHISHING_DATABASE_CACHE["link_hashes"] = _feed_link_hashes(_PHISHING_DATABASE_CACHE)
    except Exception as exc:
        # If a warm cache exists, keep using it; otherwise expose a provider error.
        if not _PHISHING_DATABASE_CACHE.get("domains") and not _PHISHING_DATABASE_CACHE.get("links"):
            _PHISHING_DATABASE_CACHE.update({
                "loaded_at": now,
                "domains": set(local_domains),
                "local_domains": local_domains,
                "local_metadata": local_metadata,
                "links": set(),
                "link_hashes": set(),
            })
        _PHISHING_DATABASE_CACHE["error"] = str(exc)
    return _PHISHING_DATABASE_CACHE


def _parse_phishtank_online_valid_csv(text: str) -> Dict[str, Dict[str, Any]]:
    links: Dict[str, Dict[str, Any]] = {}
    reader = csv.DictReader(io.StringIO(text or ""))
    for row in reader:
        if not isinstance(row, dict):
            continue
        if str(row.get("verified") or "").strip().lower() != "yes":
            continue
        if str(row.get("online") or "").strip().lower() != "yes":
            continue
        raw_url = str(row.get("url") or "").strip()
        if not raw_url:
            continue
        metadata = {
            "phish_id": str(row.get("phish_id") or "").strip(),
            "phish_detail_url": str(row.get("phish_detail_url") or "").strip(),
            "submission_time": str(row.get("submission_time") or "").strip(),
            "verification_time": str(row.get("verification_time") or "").strip(),
            "target": str(row.get("target") or "").strip(),
        }
        for variant in _canonical_url_variants(raw_url):
            links[variant] = metadata
    return links


def _load_phishtank_online_valid_feed() -> Dict[str, Any]:
    now = int(time.time())
    cached_at = _coerce_int(_PHISHTANK_CACHE.get("loaded_at", 0), 0)
    if cached_at and now - cached_at < PHISHTANK_FEED_TTL_SECONDS:
        return _PHISHTANK_CACHE

    if not ENABLE_PHISHTANK:
        _PHISHTANK_CACHE.update({
            "loaded_at": now,
            "links": set(),
            "link_hashes": set(),
            "metadata": {},
            "metadata_by_hash": {},
            "error": "disabled",
            "source_url": PHISHTANK_ONLINE_VALID_URL,
        })
        return _PHISHTANK_CACHE

    try:
        text = _download_phishtank_feed()
        parsed = _parse_phishtank_online_valid_csv(text)
        _PHISHTANK_CACHE.update({
            "loaded_at": now,
            "links": set(parsed.keys()),
            "link_hashes": {_url_hash(link) for link in parsed.keys()},
            "metadata": parsed,
            "metadata_by_hash": {_url_hash(link): metadata for link, metadata in parsed.items()},
            "error": None,
            "source_url": PHISHTANK_ONLINE_VALID_URL,
        })
    except Exception as exc:
        if not _PHISHTANK_CACHE.get("links"):
            _PHISHTANK_CACHE.update({
                "loaded_at": now,
                "links": set(),
                "link_hashes": set(),
                "metadata": {},
                "metadata_by_hash": {},
                "source_url": PHISHTANK_ONLINE_VALID_URL,
            })
        _PHISHTANK_CACHE["error"] = str(exc)
    return _PHISHTANK_CACHE


def _download_openphish_feed() -> str:
    return _download_text_feed(
        OPENPHISH_FEED_URL,
        timeout_seconds=PHISHING_DATABASE_TIMEOUT_SECONDS,
        max_bytes=OPENPHISH_MAX_FEED_BYTES,
    )


def _load_openphish_feed() -> Dict[str, Any]:
    now = int(time.time())
    cached_at = _coerce_int(_OPENPHISH_CACHE.get("loaded_at", 0), 0)
    if cached_at and now - cached_at < OPENPHISH_FEED_TTL_SECONDS:
        return _OPENPHISH_CACHE

    if not ENABLE_OPENPHISH:
        _OPENPHISH_CACHE.update({
            "loaded_at": now,
            "links": set(),
            "link_hashes": set(),
            "error": "disabled",
            "source_url": OPENPHISH_FEED_URL,
        })
        return _OPENPHISH_CACHE

    try:
        links: set[str] = set()
        for raw_line in _download_openphish_feed().splitlines():
            raw_url = raw_line.strip()
            if not raw_url or raw_url.startswith("#"):
                continue
            for variant in _canonical_url_variants(raw_url):
                links.add(variant)
        _OPENPHISH_CACHE.update({
            "loaded_at": now,
            "links": links,
            "link_hashes": {_url_hash(link) for link in links},
            "error": None,
            "source_url": OPENPHISH_FEED_URL,
        })
    except Exception as exc:
        if not _OPENPHISH_CACHE.get("links"):
            _OPENPHISH_CACHE.update({
                "loaded_at": now,
                "links": set(),
                "link_hashes": set(),
                "source_url": OPENPHISH_FEED_URL,
            })
        _OPENPHISH_CACHE["error"] = str(exc)
    return _OPENPHISH_CACHE


def _fetch_openphish(urls: List[str]) -> Dict[str, Dict[str, Any]]:
    output: Dict[str, Dict[str, Any]] = {}
    start = time.perf_counter()
    feed = _load_openphish_feed()
    query_ms = int((time.perf_counter() - start) * 1000)
    links = feed.get("links") if isinstance(feed.get("links"), set) else set()
    error = feed.get("error")
    source_url = str(feed.get("source_url") or OPENPHISH_FEED_URL)

    for url in urls:
        key = _url_hash(url)
        if error and not links:
            output[key] = {
                "status": "unknown" if error == "disabled" else "error",
                "consulted": False if error == "disabled" else True,
                "threat_type": "unknown" if error == "disabled" else "error",
                "score": 0,
                "details": {"status": str(error), "provider": OPENPHISH_SOURCE, "source_url": source_url},
                "query_ms": query_ms,
            }
            continue

        matched_link = next((variant for variant in _canonical_url_variants(url) if variant in links), None)
        if matched_link:
            output[key] = {
                "status": "malicious",
                "consulted": True,
                "threat_type": "phishing",
                "score": 95,
                "details": {
                    "provider": OPENPHISH_SOURCE,
                    "status": "listed_active",
                    "match_type": "url",
                    "matched_value": matched_link,
                    "links_loaded": len(links),
                    "feed_version_loaded_at": _coerce_int(feed.get("loaded_at", 0), 0),
                    "source_url": source_url,
                },
                "query_ms": query_ms,
            }
            continue

        output[key] = {
            "status": "clean",
            "consulted": True,
            "threat_type": "unknown",
            "score": 0,
            "details": {
                "status": "not_listed",
                "provider": OPENPHISH_SOURCE,
                "links_loaded": len(links),
                "source_url": source_url,
            },
            "query_ms": query_ms,
        }
    return output


def _download_urlhaus_recent_feed() -> str:
    return _download_text_feed(
        URLHAUS_RECENT_CSV_URL,
        timeout_seconds=URLHAUS_TIMEOUT_SECONDS,
        max_bytes=URLHAUS_RECENT_MAX_FEED_BYTES,
    )


def _parse_urlhaus_recent_csv(text: str) -> Dict[str, Dict[str, Any]]:
    cleaned_lines: List[str] = []
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("# id,"):
            cleaned_lines.append(line[2:])
            continue
        if line.startswith("#"):
            continue
        cleaned_lines.append(raw_line)

    links: Dict[str, Dict[str, Any]] = {}
    reader = csv.DictReader(cleaned_lines)
    for row in reader:
        if not isinstance(row, dict):
            continue
        raw_url = str(row.get("url") or "").strip()
        if not raw_url:
            continue
        status = str(row.get("url_status") or "").strip().lower()
        if status and status != "online":
            continue
        metadata = {
            "dateadded": str(row.get("dateadded") or "").strip(),
            "last_online": str(row.get("last_online") or "").strip(),
            "threat": str(row.get("threat") or "malware_or_phishing").strip(),
            "tags": str(row.get("tags") or "").strip(),
            "urlhaus_link": str(row.get("urlhaus_link") or "").strip(),
        }
        for variant in _canonical_url_variants(raw_url):
            links[variant] = metadata
    return links


def _load_urlhaus_recent_feed() -> Dict[str, Any]:
    now = int(time.time())
    cached_at = _coerce_int(_URLHAUS_RECENT_CACHE.get("loaded_at", 0), 0)
    if cached_at and now - cached_at < URLHAUS_RECENT_FEED_TTL_SECONDS:
        return _URLHAUS_RECENT_CACHE

    try:
        text = _download_urlhaus_recent_feed()
        parsed = _parse_urlhaus_recent_csv(text)
        _URLHAUS_RECENT_CACHE.update({
            "loaded_at": now,
            "links": set(parsed.keys()),
            "link_hashes": {_url_hash(link) for link in parsed.keys()},
            "metadata": parsed,
            "metadata_by_hash": {_url_hash(link): metadata for link, metadata in parsed.items()},
            "error": None,
            "source_url": URLHAUS_RECENT_CSV_URL,
        })
    except Exception as exc:
        if not _URLHAUS_RECENT_CACHE.get("links"):
            _URLHAUS_RECENT_CACHE.update({
                "loaded_at": now,
                "links": set(),
                "link_hashes": set(),
                "metadata": {},
                "metadata_by_hash": {},
                "source_url": URLHAUS_RECENT_CSV_URL,
            })
        _URLHAUS_RECENT_CACHE["error"] = str(exc)
    return _URLHAUS_RECENT_CACHE


def _load_scam_blocklist_nrd_feed() -> Dict[str, Any]:
    now = int(time.time())
    cached_at = _coerce_int(_SCAM_BLOCKLIST_NRD_CACHE.get("loaded_at", 0), 0)
    if cached_at and now - cached_at < SCAM_BLOCKLIST_NRD_FEED_TTL_SECONDS:
        return _SCAM_BLOCKLIST_NRD_CACHE

    if not ENABLE_SCAM_BLOCKLIST_NRD:
        _SCAM_BLOCKLIST_NRD_CACHE.update({
            "loaded_at": now,
            "domains": set(),
            "error": "disabled",
            "source_url": SCAM_BLOCKLIST_NRD_URL,
            "license": SCAM_BLOCKLIST_NRD_LICENSE,
        })
        return _SCAM_BLOCKLIST_NRD_CACHE

    try:
        text = _download_text_feed(
            SCAM_BLOCKLIST_NRD_URL,
            timeout_seconds=SCAM_BLOCKLIST_NRD_TIMEOUT_SECONDS,
            max_bytes=SCAM_BLOCKLIST_NRD_MAX_FEED_BYTES,
        )
        _SCAM_BLOCKLIST_NRD_CACHE.update({
            "loaded_at": now,
            "domains": _scam_blocklist_domain_lines(text),
            "error": None,
            "source_url": SCAM_BLOCKLIST_NRD_URL,
            "license": SCAM_BLOCKLIST_NRD_LICENSE,
        })
    except Exception as exc:
        if not _SCAM_BLOCKLIST_NRD_CACHE.get("domains"):
            _SCAM_BLOCKLIST_NRD_CACHE.update({
                "loaded_at": now,
                "domains": set(),
                "source_url": SCAM_BLOCKLIST_NRD_URL,
                "license": SCAM_BLOCKLIST_NRD_LICENSE,
            })
        _SCAM_BLOCKLIST_NRD_CACHE["error"] = str(exc)
    return _SCAM_BLOCKLIST_NRD_CACHE


def _load_phishdestroy_feed() -> Dict[str, Any]:
    now = int(time.time())
    cached_at = _coerce_int(_PHISHDESTROY_CACHE.get("loaded_at", 0), 0)
    if cached_at and now - cached_at < PHISHDESTROY_FEED_TTL_SECONDS:
        return _PHISHDESTROY_CACHE

    if not ENABLE_PHISHDESTROY:
        _PHISHDESTROY_CACHE.update({
            "loaded_at": now,
            "domains": set(),
            "error": "disabled",
            "source_url": PHISHDESTROY_URL,
            "api_url": PHISHDESTROY_API_URL,
            "license": PHISHDESTROY_LICENSE,
        })
        return _PHISHDESTROY_CACHE

    try:
        text = _download_text_feed(
            PHISHDESTROY_URL,
            timeout_seconds=PHISHDESTROY_TIMEOUT_SECONDS,
            max_bytes=PHISHDESTROY_MAX_FEED_BYTES,
        )
        _PHISHDESTROY_CACHE.update({
            "loaded_at": now,
            "domains": _scam_blocklist_domain_lines(text),
            "error": None,
            "source_url": PHISHDESTROY_URL,
            "api_url": PHISHDESTROY_API_URL,
            "license": PHISHDESTROY_LICENSE,
        })
    except Exception as exc:
        if not _PHISHDESTROY_CACHE.get("domains"):
            _PHISHDESTROY_CACHE.update({
                "loaded_at": now,
                "domains": set(),
                "source_url": PHISHDESTROY_URL,
                "api_url": PHISHDESTROY_API_URL,
                "license": PHISHDESTROY_LICENSE,
            })
        _PHISHDESTROY_CACHE["error"] = str(exc)
    return _PHISHDESTROY_CACHE


def _asf_investor_alert_domains_from_html(text: str) -> set[str]:
    decoded = html.unescape(text or "")
    domains: set[str] = set()
    paragraphs = re.findall(r"<p\b[^>]*>(.*?)</p>", decoded, flags=re.IGNORECASE | re.DOTALL)
    if not paragraphs:
        paragraphs = [decoded]

    def normalize_for_phrase(value: str) -> str:
        without_tags = re.sub(r"<[^>]+>", " ", value)
        folded = unicodedata.normalize("NFKD", without_tags).encode("ascii", "ignore").decode("ascii")
        return re.sub(r"\s+", " ", folded).strip().lower()

    candidate_blocks: List[str] = []
    for index, paragraph in enumerate(paragraphs):
        normalized = normalize_for_phrase(paragraph)
        if not re.search(r"\bnu\s+(este|sunt)\s+autorizat", normalized):
            continue
        if index > 0:
            candidate_blocks.append(paragraphs[index - 1])
        candidate_blocks.append(paragraph)

    for raw_url in re.findall(r"https?://[^\s<>'\")]+", "\n".join(candidate_blocks), flags=re.IGNORECASE):
        candidate = raw_url.rstrip(".,;:)]}»”")
        host = _host_from_url(candidate)
        if host and "." in host:
            domains.add(host)
    return domains


def _load_asf_investor_alerts_feed() -> Dict[str, Any]:
    now = int(time.time())
    cached_at = _coerce_int(_ASF_INVESTOR_ALERTS_CACHE.get("loaded_at", 0), 0)
    if cached_at and now - cached_at < ASF_INVESTOR_ALERTS_FEED_TTL_SECONDS:
        return _ASF_INVESTOR_ALERTS_CACHE

    if not ENABLE_ASF_INVESTOR_ALERTS:
        _ASF_INVESTOR_ALERTS_CACHE.update({
            "loaded_at": now,
            "domains": set(),
            "error": "disabled",
            "source_url": ASF_INVESTOR_ALERTS_URL,
            "source_publisher": "Autoritatea de Supraveghere Financiară",
        })
        return _ASF_INVESTOR_ALERTS_CACHE

    try:
        text = _download_text_feed(
            ASF_INVESTOR_ALERTS_URL,
            timeout_seconds=ASF_INVESTOR_ALERTS_TIMEOUT_SECONDS,
            max_bytes=ASF_INVESTOR_ALERTS_MAX_FEED_BYTES,
        )
        _ASF_INVESTOR_ALERTS_CACHE.update({
            "loaded_at": now,
            "domains": _asf_investor_alert_domains_from_html(text),
            "error": None,
            "source_url": ASF_INVESTOR_ALERTS_URL,
            "source_publisher": "Autoritatea de Supraveghere Financiară",
        })
    except Exception as exc:
        if not _ASF_INVESTOR_ALERTS_CACHE.get("domains"):
            _ASF_INVESTOR_ALERTS_CACHE.update({
                "loaded_at": now,
                "domains": set(),
                "source_url": ASF_INVESTOR_ALERTS_URL,
                "source_publisher": "Autoritatea de Supraveghere Financiară",
            })
        _ASF_INVESTOR_ALERTS_CACHE["error"] = str(exc)
    return _ASF_INVESTOR_ALERTS_CACHE


def _canonical_url_variants(url: str) -> set[str]:
    parsed = urlparse(url.strip())
    if not parsed.scheme or not parsed.netloc:
        return {url.strip().lower()}
    hostname = (parsed.hostname or "").lower()
    netloc = hostname
    try:
        port = parsed.port
    except ValueError:
        port = None
    if port:
        netloc = f"{hostname}:{port}"
    path = parsed.path or "/"
    path_variants = {path}
    if path != "/":
        path_variants.update({path.rstrip("/"), path.rstrip("/") + "/"})

    query_variants = {parsed.query}
    if parsed.query:
        query_variants.add(re.sub(r"%3d", "=", parsed.query, flags=re.IGNORECASE))

    variants = {
        urlunparse((parsed.scheme.lower(), netloc, candidate_path, "", candidate_query, "")).lower()
        for candidate_path in path_variants
        for candidate_query in query_variants
    }
    return variants


def _host_from_url(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").strip(".").lower()
    except Exception:
        return ""


def _domain_matches_feed(hostname: str, feed_domains: set[str]) -> Optional[str]:
    if not hostname:
        return None
    hostname = hostname.strip(".").lower()
    if hostname in feed_domains:
        return hostname
    labels = hostname.split(".")
    for index in range(1, max(1, len(labels) - 1)):
        candidate = ".".join(labels[index:])
        # Avoid broad false positives from shared base domains. A listed
        # three-label domain may protect its subdomains; two-label domains
        # require exact match above.
        if candidate.count(".") >= 2 and candidate in feed_domains:
            return candidate
    return None


def _fetch_phishing_database(urls: List[str]) -> Dict[str, Dict[str, Any]]:
    output: Dict[str, Dict[str, Any]] = {}
    start = time.perf_counter()
    feed = _load_phishing_database_feeds()
    query_ms = int((time.perf_counter() - start) * 1000)
    domains = feed.get("domains") if isinstance(feed.get("domains"), set) else set()
    local_domains = feed.get("local_domains") if isinstance(feed.get("local_domains"), set) else set()
    local_metadata = feed.get("local_metadata") if isinstance(feed.get("local_metadata"), dict) else {}
    links = feed.get("links") if isinstance(feed.get("links"), set) else set()
    error = feed.get("error")

    for url in urls:
        key = _url_hash(url)
        if error and not domains and not links:
            output[key] = {
                "status": "error",
                "threat_type": "error",
                "score": 0,
                "details": {"error": str(error), "provider": "phishing_database"},
                "query_ms": query_ms,
            }
            continue

        matched_link = next((variant for variant in _canonical_url_variants(url) if variant in links), None)
        hostname = _host_from_url(url)
        matched_local_domain = _domain_matches_feed(hostname, local_domains)
        matched_domain = matched_local_domain or _domain_matches_feed(hostname, domains)
        if matched_link or matched_domain:
            local_details = local_metadata.get(matched_local_domain or "") if matched_local_domain else {}
            output[key] = {
                "status": "malicious",
                "threat_type": "phishing",
                "score": 92,
                "details": {
                    "provider": "phishing_database",
                    "status": "listed",
                    "match_type": "url" if matched_link else "domain",
                    "matched_value": matched_link or matched_domain,
                    "domains_loaded": len(domains),
                    "local_domains_loaded": len(local_domains),
                    "links_loaded": len(links),
                    "feed_version_loaded_at": _coerce_int(feed.get("loaded_at", 0), 0),
                    **({"local_source": local_details} if local_details else {}),
                },
                "query_ms": query_ms,
            }
            continue

        output[key] = {
            "status": "clean",
            "threat_type": "unknown",
            "score": 0,
            "details": {
                "status": "not_listed",
                "provider": "phishing_database",
                "domains_loaded": len(domains),
                "local_domains_loaded": len(local_domains),
                "links_loaded": len(links),
            },
            "query_ms": query_ms,
        }
    return output


def _fetch_phishtank_online_valid(urls: List[str]) -> Dict[str, Dict[str, Any]]:
    output: Dict[str, Dict[str, Any]] = {}
    if not ENABLE_PHISHTANK:
        for url in urls:
            output[_url_hash(url)] = {
                "status": "unknown",
                "consulted": False,
                "threat_type": "unknown",
                "score": 0,
                "details": {
                    "status": "disabled",
                    "provider": PHISHTANK_SOURCE,
                    "source_url": PHISHTANK_ONLINE_VALID_URL,
                },
                "query_ms": 0,
            }
        return output

    start = time.perf_counter()
    feed = _load_phishtank_online_valid_feed()
    query_ms = int((time.perf_counter() - start) * 1000)
    links = feed.get("links") if isinstance(feed.get("links"), set) else set()
    metadata = feed.get("metadata") if isinstance(feed.get("metadata"), dict) else {}
    error = feed.get("error")
    source_url = str(feed.get("source_url") or PHISHTANK_ONLINE_VALID_URL)

    for url in urls:
        key = _url_hash(url)
        if error and not links:
            output[key] = {
                "status": "error",
                "threat_type": "error",
                "score": 0,
                "details": {"error": str(error), "provider": PHISHTANK_SOURCE, "source_url": source_url},
                "query_ms": query_ms,
            }
            continue

        matched_link = next((variant for variant in _canonical_url_variants(url) if variant in links), None)
        if matched_link:
            match_metadata = metadata.get(matched_link) if isinstance(metadata.get(matched_link), dict) else {}
            output[key] = {
                "status": "malicious",
                "threat_type": "phishing",
                "score": 95,
                "details": {
                    "provider": PHISHTANK_SOURCE,
                    "status": "verified_online",
                    "match_type": "url",
                    "matched_value": matched_link,
                    "links_loaded": len(links),
                    "feed_version_loaded_at": _coerce_int(feed.get("loaded_at", 0), 0),
                    "source_url": source_url,
                    **match_metadata,
                },
                "query_ms": query_ms,
            }
            continue

        output[key] = {
            "status": "clean",
            "threat_type": "unknown",
            "score": 0,
            "details": {
                "status": "not_listed",
                "provider": PHISHTANK_SOURCE,
                "links_loaded": len(links),
                "source_url": source_url,
            },
            "query_ms": query_ms,
        }
    return output


def _fetch_asf_investor_alerts(urls: List[str]) -> Dict[str, Dict[str, Any]]:
    output: Dict[str, Dict[str, Any]] = {}
    if not ENABLE_ASF_INVESTOR_ALERTS:
        for url in urls:
            output[_url_hash(url)] = {
                "status": "unknown",
                "consulted": False,
                "threat_type": "unknown",
                "score": 0,
                "details": {
                    "status": "disabled",
                    "provider": ASF_INVESTOR_ALERTS_SOURCE,
                    "source_url": ASF_INVESTOR_ALERTS_URL,
                    "source_publisher": "Autoritatea de Supraveghere Financiară",
                },
                "query_ms": 0,
            }
        return output

    start = time.perf_counter()
    feed = _load_asf_investor_alerts_feed()
    query_ms = int((time.perf_counter() - start) * 1000)
    domains = feed.get("domains") if isinstance(feed.get("domains"), set) else set()
    error = feed.get("error")
    source_url = str(feed.get("source_url") or ASF_INVESTOR_ALERTS_URL)
    source_publisher = str(feed.get("source_publisher") or "Autoritatea de Supraveghere Financiară")

    for url in urls:
        key = _url_hash(url)
        if error and not domains:
            output[key] = {
                "status": "error",
                "consulted": True,
                "threat_type": "error",
                "score": 0,
                "details": {
                    "error": str(error),
                    "provider": ASF_INVESTOR_ALERTS_SOURCE,
                    "source_url": source_url,
                    "source_publisher": source_publisher,
                },
                "query_ms": query_ms,
            }
            continue

        matched_domain = _domain_matches_feed(_host_from_url(url), domains)
        if matched_domain:
            output[key] = {
                "status": "malicious",
                "consulted": True,
                "threat_type": "unauthorized_investment_platform",
                "score": 100,
                "details": {
                    "provider": ASF_INVESTOR_ALERTS_SOURCE,
                    "status": "listed",
                    "match_type": "domain",
                    "matched_value": matched_domain,
                    "domains_loaded": len(domains),
                    "feed_version_loaded_at": _coerce_int(feed.get("loaded_at", 0), 0),
                    "source_url": source_url,
                    "source_publisher": source_publisher,
                    "authority_basis": "ASF investor alert: entity is not authorized to provide investment services.",
                },
                "query_ms": query_ms,
            }
            continue

        output[key] = {
            "status": "clean",
            "consulted": True,
            "threat_type": "unknown",
            "score": 0,
            "details": {
                "status": "not_listed",
                "provider": ASF_INVESTOR_ALERTS_SOURCE,
                "domains_loaded": len(domains),
                "source_url": source_url,
                "source_publisher": source_publisher,
            },
            "query_ms": query_ms,
        }
    return output


def _fetch_scam_blocklist_nrd(urls: List[str]) -> Dict[str, Dict[str, Any]]:
    output: Dict[str, Dict[str, Any]] = {}
    if not ENABLE_SCAM_BLOCKLIST_NRD:
        for url in urls:
            output[_url_hash(url)] = {
                "status": "unknown",
                "consulted": False,
                "threat_type": "unknown",
                "score": 0,
                "details": {
                    "status": "disabled",
                    "provider": SCAM_BLOCKLIST_NRD_SOURCE,
                    "source_url": SCAM_BLOCKLIST_NRD_URL,
                    "license": SCAM_BLOCKLIST_NRD_LICENSE,
                },
                "query_ms": 0,
            }
        return output

    start = time.perf_counter()
    feed = _load_scam_blocklist_nrd_feed()
    query_ms = int((time.perf_counter() - start) * 1000)
    domains = feed.get("domains") if isinstance(feed.get("domains"), set) else set()
    error = feed.get("error")
    source_url = str(feed.get("source_url") or SCAM_BLOCKLIST_NRD_URL)
    license_name = str(feed.get("license") or SCAM_BLOCKLIST_NRD_LICENSE)

    for url in urls:
        key = _url_hash(url)
        if error and not domains:
            output[key] = {
                "status": "error",
                "consulted": True,
                "threat_type": "error",
                "score": 0,
                "details": {
                    "error": str(error),
                    "provider": SCAM_BLOCKLIST_NRD_SOURCE,
                    "source_url": source_url,
                    "license": license_name,
                },
                "query_ms": query_ms,
            }
            continue

        matched_domain = _domain_matches_feed(_host_from_url(url), domains)
        if matched_domain:
            output[key] = {
                "status": "suspicious",
                "consulted": True,
                "threat_type": "scam_nrd",
                "score": 60,
                "details": {
                    "provider": SCAM_BLOCKLIST_NRD_SOURCE,
                    "status": "listed",
                    "match_type": "domain",
                    "matched_value": matched_domain,
                    "domains_loaded": len(domains),
                    "feed_version_loaded_at": _coerce_int(feed.get("loaded_at", 0), 0),
                    "source_url": source_url,
                    "license": license_name,
                },
                "query_ms": query_ms,
            }
            continue

        output[key] = {
            "status": "clean",
            "consulted": True,
            "threat_type": "unknown",
            "score": 0,
            "details": {
                "status": "not_listed",
                "provider": SCAM_BLOCKLIST_NRD_SOURCE,
                "domains_loaded": len(domains),
                "source_url": source_url,
                "license": license_name,
            },
            "query_ms": query_ms,
        }
    return output


def _fetch_phishdestroy(urls: List[str]) -> Dict[str, Dict[str, Any]]:
    output: Dict[str, Dict[str, Any]] = {}
    if not ENABLE_PHISHDESTROY:
        for url in urls:
            output[_url_hash(url)] = {
                "status": "unknown",
                "consulted": False,
                "threat_type": "unknown",
                "score": 0,
                "details": {
                    "status": "disabled",
                    "provider": PHISHDESTROY_SOURCE,
                    "source_url": PHISHDESTROY_URL,
                    "api_url": PHISHDESTROY_API_URL,
                    "license": PHISHDESTROY_LICENSE,
                },
                "query_ms": 0,
            }
        return output

    start = time.perf_counter()
    feed = _load_phishdestroy_feed()
    query_ms = int((time.perf_counter() - start) * 1000)
    domains = feed.get("domains") if isinstance(feed.get("domains"), set) else set()
    error = feed.get("error")
    source_url = str(feed.get("source_url") or PHISHDESTROY_URL)
    api_url = str(feed.get("api_url") or PHISHDESTROY_API_URL)
    license_name = str(feed.get("license") or PHISHDESTROY_LICENSE)

    for url in urls:
        key = _url_hash(url)
        if error and not domains:
            output[key] = {
                "status": "error",
                "consulted": True,
                "threat_type": "error",
                "score": 0,
                "details": {
                    "error": str(error),
                    "provider": PHISHDESTROY_SOURCE,
                    "source_url": source_url,
                    "api_url": api_url,
                    "license": license_name,
                },
                "query_ms": query_ms,
            }
            continue

        matched_domain = _domain_matches_feed(_host_from_url(url), domains)
        if matched_domain:
            output[key] = {
                "status": "suspicious",
                "consulted": True,
                "threat_type": "phishing_or_scam",
                "score": 60,
                "details": {
                    "provider": PHISHDESTROY_SOURCE,
                    "status": "listed",
                    "match_type": "domain",
                    "matched_value": matched_domain,
                    "domains_loaded": len(domains),
                    "feed_version_loaded_at": _coerce_int(feed.get("loaded_at", 0), 0),
                    "source_url": source_url,
                    "api_url": api_url,
                    "license": license_name,
                },
                "query_ms": query_ms,
            }
            continue

        output[key] = {
            "status": "clean",
            "consulted": True,
            "threat_type": "unknown",
            "score": 0,
            "details": {
                "status": "not_listed",
                "provider": PHISHDESTROY_SOURCE,
                "domains_loaded": len(domains),
                "source_url": source_url,
                "api_url": api_url,
                "license": license_name,
            },
            "query_ms": query_ms,
        }
    return output


def _urlhaus_auth_key() -> str:
    return URLHAUS_AUTH_KEY


def _fetch_urlhaus(urls: List[str], auth_key: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    output: Dict[str, Dict[str, Any]] = {}
    auth_key = (auth_key if auth_key is not None else _urlhaus_auth_key()).strip()

    recent_feed: Dict[str, Any] = {}
    recent_links: set[str] = set()
    recent_metadata: Dict[str, Any] = {}
    recent_query_ms = 0
    if not auth_key:
        start = time.perf_counter()
        recent_feed = _load_urlhaus_recent_feed()
        recent_query_ms = int((time.perf_counter() - start) * 1000)
        recent_links = recent_feed.get("links") if isinstance(recent_feed.get("links"), set) else set()
        recent_metadata = recent_feed.get("metadata") if isinstance(recent_feed.get("metadata"), dict) else {}

    for url in urls:
        key = _url_hash(url)
        if not auth_key:
            feed_error = recent_feed.get("error")
            source_url = str(recent_feed.get("source_url") or URLHAUS_RECENT_CSV_URL)
            if feed_error and not recent_links:
                output[key] = {
                    "status": "error",
                    "consulted": True,
                    "threat_type": "error",
                    "score": 0,
                    "details": {"error": str(feed_error), "provider": "urlhaus", "source_url": source_url},
                    "query_ms": recent_query_ms,
                }
                continue

            matched_link = next((variant for variant in _canonical_url_variants(url) if variant in recent_links), None)
            if matched_link:
                match_metadata = recent_metadata.get(matched_link) if isinstance(recent_metadata.get(matched_link), dict) else {}
                threat_type = str(match_metadata.get("threat") or "malware_or_phishing")
                output[key] = {
                    "status": "malicious",
                    "consulted": True,
                    "threat_type": threat_type,
                    "score": 85,
                    "details": {
                        "status": "listed_online",
                        "provider": "urlhaus",
                        "match_type": "recent_feed_url",
                        "matched_value": matched_link,
                        "links_loaded": len(recent_links),
                        "feed_version_loaded_at": _coerce_int(recent_feed.get("loaded_at", 0), 0),
                        "source_url": source_url,
                        **match_metadata,
                    },
                    "query_ms": recent_query_ms,
                }
                continue

            output[key] = {
                "status": "clean",
                "consulted": True,
                "threat_type": "unknown",
                "score": 0,
                "details": {
                    "status": "not_listed_recent_feed",
                    "provider": "urlhaus",
                    "links_loaded": len(recent_links),
                    "source_url": source_url,
                },
                "query_ms": recent_query_ms,
            }
            continue
        output[key] = {
            "status": "error",
            "threat_type": "error",
            "score": 0,
            "details": {"error": "not_scanned"},
            "query_ms": 0,
        }
        try:
            start = time.perf_counter()
            response = requests.post(
                URLHAUS_API_URL,
                data={"url": url},
                headers={"Auth-Key": auth_key},
                timeout=URLHAUS_TIMEOUT_SECONDS,
            )
            query_ms = int((time.perf_counter() - start) * 1000)
            if response.status_code != 200:
                output[key] = {
                    "status": "error",
                    "consulted": True,
                    "threat_type": "error",
                    "score": 0,
                    "details": {"error": f"HTTP {response.status_code}"},
                    "query_ms": query_ms,
                }
                continue

            payload = response.json()
            parsed = _parse_urlhaus_record(payload if isinstance(payload, dict) else {})
            if not parsed:
                output[key] = {
                    "status": "clean",
                    "consulted": True,
                    "threat_type": "unknown",
                    "score": 0,
                    "details": {"status": "not_listed", "provider": "urlhaus"},
                    "query_ms": query_ms,
                }
                continue

            output[key] = {
                "status": parsed.get("status", "unknown"),
                "consulted": True,
                "threat_type": parsed.get("threat_type", "unknown"),
                "score": 85 if parsed.get("status") == "malicious" else 45,
                "details": {
                    "provider": "urlhaus",
                    "status": parsed.get("status"),
                    "last_seen": parsed.get("last_seen"),
                    "comment": parsed.get("details", ""),
                },
                "query_ms": query_ms,
            }
        except Exception as exc:
            output[key] = {
                "status": "error",
                "consulted": True,
                "threat_type": "error",
                "score": 0,
                "details": {"error": str(exc), "provider": "urlhaus"},
                "query_ms": 0,
            }

    return output


def _aggregate_reputation(url: str, per_source: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    reasons: List[str] = []
    consulted_sources: List[str] = []
    source_summary: Dict[str, Dict[str, Any]] = {}

    total_weight = 0.0
    total_signal_weight = 0.0
    weighted_risk = 0.0

    for source_name in SOURCE_ORDER:
        raw_payload = per_source.get(source_name) if isinstance(per_source, dict) else None
        weight = SOURCE_WEIGHTS.get(source_name, 0)
        source_payload = _normalize_source_entry(
            source_name=source_name,
            payload=raw_payload,
            consulted=bool(raw_payload.get("consulted", True)) if isinstance(raw_payload, dict) else False,
            weight=weight,
            fallback_status="unknown",
        )
        source_summary[source_name] = source_payload

        consulted = bool(source_payload.get("consulted", False))
        if not consulted:
            continue

        consulted_sources.append(source_name)
        status = source_payload.get("status", "unknown")
        contribution = weight * SOURCE_STATUS_WEIGHTS.get(status, 0.0)
        weighted_risk += contribution
        total_weight += weight
        total_signal_weight += max(0.0, contribution)
        source_payload["risk_contribution"] = round(contribution, 2)

        if status in {"malicious", "suspicious"}:
            reasons.append(source_name)

    confidence = round(total_signal_weight / total_weight, 2) if total_weight else 0.0
    risk_score = int(min(100, round(weighted_risk)))

    consulted_count = len(consulted_sources)
    active_sources = sorted(set(reasons))

    if consulted_count == 0:
        verdict = "clean"
    elif risk_score >= 78 or confidence >= 0.75:
        verdict = "malicious"
    elif risk_score >= 38 or confidence >= 0.30 or (risk_score > 0 and consulted_count >= 2):
        verdict = "suspicious"
    else:
        verdict = "clean"

    return {
        "url": url,
        "verdict": verdict,
        "risk_score": risk_score,
        "confidence": confidence,
        "signals": active_sources,
        "signal_count": len(active_sources),
        "active_sources": active_sources,
        "sources": source_summary,
        "source_count": len(SOURCE_ORDER),
        "consulted_sources": sorted(consulted_sources),
        "consulted_source_count": consulted_count,
    }


def _provider_hash_lookup_matches(
    urls: List[str],
    *,
    lookup_hashes: set[str],
    lookup_hashes_by_url: Dict[str, set[str]],
    feed: Dict[str, Any],
    provider: str,
    status: str,
    threat_type: str,
    score: int,
    source_url: str,
    source_status: str,
    match_type: str = "url_hash",
    metadata_by_hash_key: str = "metadata_by_hash",
    query_ms: int = 0,
    extra_details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Dict[str, Any]]:
    output: Dict[str, Dict[str, Any]] = {}
    link_hashes = _feed_link_hashes(feed)
    if not link_hashes:
        return output
    metadata_by_hash = feed.get(metadata_by_hash_key) if isinstance(feed.get(metadata_by_hash_key), dict) else {}
    loaded_at = _coerce_int(feed.get("loaded_at", 0), 0)
    for url in urls:
        candidate_hashes = _lookup_hashes_for_url(url, lookup_hashes, lookup_hashes_by_url)
        matched_hash = next((value for value in sorted(candidate_hashes) if value in link_hashes), None)
        if not matched_hash:
            continue
        match_metadata = metadata_by_hash.get(matched_hash) if isinstance(metadata_by_hash.get(matched_hash), dict) else {}
        output[_url_hash(url)] = {
            "status": status,
            "consulted": True,
            "threat_type": threat_type,
            "score": score,
            "details": {
                "provider": provider,
                "status": source_status,
                "match_type": match_type,
                "matched_value_hash": matched_hash,
                "links_loaded": len(link_hashes),
                "feed_version_loaded_at": loaded_at,
                "source_url": source_url,
                **(extra_details or {}),
                **match_metadata,
            },
            "query_ms": query_ms,
        }
    return output


def get_reputation_for_urls(
    urls: List[str],
    *,
    include_asf_investor_alerts: bool = True,
    include_phishing_database: bool = True,
    include_phishtank: bool = True,
    include_openphish: bool = True,
    include_urlhaus: bool = True,
    include_scam_blocklist_nrd: bool = False,
    include_phishdestroy: bool = False,
    persist_partial: bool = False,
    lookup_url_hashes: Optional[List[str]] = None,
    lookup_url_hashes_by_url: Optional[Dict[str, List[str]]] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Return reputation info for URLs.
    Keys are SHA-256(url), for compatibility with ScamAtlas consumers.

    Fast scans may skip slower fallback sources. Partial scans can read existing
    full cache entries, but they are not persisted by default so they do not
    poison later deep reputation lookups.
    """
    if not ENABLE_URL_REPUTATION:
        return {}

    normalized_urls: List[str] = []
    for url in urls:
        clean = _normalize_url_for_key(url)
        if clean:
            normalized_urls.append(clean)
    if not normalized_urls:
        return {}

    normalized_urls = list(dict.fromkeys(normalized_urls))[:MAX_REPUTATION_URLS]
    scan_lookup_hashes = _normalize_lookup_hashes(lookup_url_hashes)
    scan_lookup_hashes_by_url = _normalize_lookup_hash_map(lookup_url_hashes_by_url)
    cache = _load_cache(REPUTATION_CACHE_PATH)
    now = int(time.time())
    results: Dict[str, Dict[str, Any]] = {}
    need_fetch: List[str] = []
    updated_cache_entries: Dict[str, Any] = {}
    web_risk_enabled = has_web_risk_key()
    urlhaus_key = _urlhaus_auth_key()

    for url in normalized_urls:
        key = _url_hash(url)
        url_specific_hashes = _lookup_hashes_for_url(url, scan_lookup_hashes, scan_lookup_hashes_by_url)
        if url_specific_hashes:
            need_fetch.append(url)
            continue
        cached_entry = _load_cache_entry(cache, url)
        if (
            cached_entry is not None
            and _is_cache_entry_valid(cached_entry, now)
            and _cache_entry_covers_requested_sources(
                cached_entry,
                include_asf_investor_alerts=include_asf_investor_alerts,
                include_phishing_database=bool(include_phishing_database),
                include_phishtank=bool(include_phishtank),
                include_openphish=bool(include_openphish),
                include_urlhaus=include_urlhaus,
                include_scam_blocklist_nrd=include_scam_blocklist_nrd,
                include_phishdestroy=include_phishdestroy,
                urlhaus_key=urlhaus_key,
                web_risk_enabled=web_risk_enabled,
            )
        ):
            results[key] = _normalize_cached_entry(cached_entry, url, REPUTATION_CACHE_TTL_SECONDS)
            continue
        need_fetch.append(url)

    if need_fetch:
        web_risk_matches = check_urls_against_web_risk(need_fetch) if web_risk_enabled else {}
        asf_investor_alerts_matches = (
            _fetch_asf_investor_alerts(need_fetch) if include_asf_investor_alerts else {}
        )
        phishing_database_matches = _fetch_phishing_database(need_fetch) if include_phishing_database else {}
        phishtank_matches = _fetch_phishtank_online_valid(need_fetch) if include_phishtank else {}
        openphish_matches = _fetch_openphish(need_fetch) if include_openphish else {}
        urlhaus_matches = _fetch_urlhaus(need_fetch, urlhaus_key) if include_urlhaus else {}
        scam_blocklist_nrd_matches = (
            _fetch_scam_blocklist_nrd(need_fetch) if include_scam_blocklist_nrd else {}
        )
        phishdestroy_matches = _fetch_phishdestroy(need_fetch) if include_phishdestroy else {}
        if scan_lookup_hashes or scan_lookup_hashes_by_url:
            if include_phishing_database:
                start = time.perf_counter()
                phishing_feed = _load_phishing_database_feeds()
                phishing_hash_matches = _provider_hash_lookup_matches(
                    need_fetch,
                    lookup_hashes=scan_lookup_hashes,
                    lookup_hashes_by_url=scan_lookup_hashes_by_url,
                    feed=phishing_feed,
                    provider=PHISHING_DATABASE_SOURCE,
                    status="malicious",
                    threat_type="phishing",
                    score=92,
                    source_url=str(phishing_feed.get("links_url") or PHISHING_DATABASE_LINKS_URL),
                    source_status="listed",
                    query_ms=int((time.perf_counter() - start) * 1000),
                )
                phishing_database_matches.update(phishing_hash_matches)
            if include_phishtank and ENABLE_PHISHTANK:
                start = time.perf_counter()
                phishtank_feed = _load_phishtank_online_valid_feed()
                phishtank_hash_matches = _provider_hash_lookup_matches(
                    need_fetch,
                    lookup_hashes=scan_lookup_hashes,
                    lookup_hashes_by_url=scan_lookup_hashes_by_url,
                    feed=phishtank_feed,
                    provider=PHISHTANK_SOURCE,
                    status="malicious",
                    threat_type="phishing",
                    score=95,
                    source_url=str(phishtank_feed.get("source_url") or PHISHTANK_ONLINE_VALID_URL),
                    source_status="verified_online",
                    query_ms=int((time.perf_counter() - start) * 1000),
                )
                phishtank_matches.update(phishtank_hash_matches)
            if include_openphish and ENABLE_OPENPHISH:
                start = time.perf_counter()
                openphish_feed = _load_openphish_feed()
                openphish_hash_matches = _provider_hash_lookup_matches(
                    need_fetch,
                    lookup_hashes=scan_lookup_hashes,
                    lookup_hashes_by_url=scan_lookup_hashes_by_url,
                    feed=openphish_feed,
                    provider=OPENPHISH_SOURCE,
                    status="malicious",
                    threat_type="phishing",
                    score=95,
                    source_url=str(openphish_feed.get("source_url") or OPENPHISH_FEED_URL),
                    source_status="listed_active",
                    query_ms=int((time.perf_counter() - start) * 1000),
                )
                openphish_matches.update(openphish_hash_matches)
            if include_urlhaus:
                start = time.perf_counter()
                urlhaus_recent_feed = _load_urlhaus_recent_feed()
                urlhaus_hash_matches = _provider_hash_lookup_matches(
                    need_fetch,
                    lookup_hashes=scan_lookup_hashes,
                    lookup_hashes_by_url=scan_lookup_hashes_by_url,
                    feed=urlhaus_recent_feed,
                    provider=URLHAUS_SOURCE,
                    status="malicious",
                    threat_type="malware_or_phishing",
                    score=85,
                    source_url=str(urlhaus_recent_feed.get("source_url") or URLHAUS_RECENT_CSV_URL),
                    source_status="listed_online",
                    match_type="recent_feed_url_hash",
                    query_ms=int((time.perf_counter() - start) * 1000),
                )
                urlhaus_matches.update(urlhaus_hash_matches)

        should_persist_results = (
            not (scan_lookup_hashes or scan_lookup_hashes_by_url)
        ) and (persist_partial or (
            (not include_asf_investor_alerts or ENABLE_ASF_INVESTOR_ALERTS)
            and
            bool(include_phishing_database)
            and bool(include_phishtank)
            and bool(include_openphish)
            and include_urlhaus
            and (not include_phishtank or ENABLE_PHISHTANK)
            and (not include_openphish or ENABLE_OPENPHISH)
            and (not include_scam_blocklist_nrd or ENABLE_SCAM_BLOCKLIST_NRD)
            and (not include_phishdestroy or ENABLE_PHISHDESTROY)
        ))

        for url in need_fetch:
            key = _url_hash(url)
            per_source: Dict[str, Dict[str, Any]] = {}

            web_risk_entry_raw = web_risk_matches.get(key) if web_risk_enabled else None
            web_risk_entry = web_risk_entry_raw if isinstance(web_risk_entry_raw, dict) else {}
            per_source[WEB_RISK_SOURCE] = {
                "status": "malicious" if web_risk_entry else "clean",
                "consulted": web_risk_enabled,
                "threat_type": web_risk_entry.get("threat_type", "unknown"),
                "details": {
                    "cache_duration": web_risk_entry.get("cache_duration", ""),
                    "provider": "google_web_risk",
                    "status": "match" if web_risk_entry else "no_match",
                },
                "score": 100 if web_risk_entry else 0,
            }

            asf_default_error = "skipped_fast_scan" if not include_asf_investor_alerts else "not_scanned"
            asf_investor_alerts_entry = asf_investor_alerts_matches.get(key, {
                "status": "unknown" if not include_asf_investor_alerts else "error",
                "threat_type": "unknown" if not include_asf_investor_alerts else "error",
                "score": 0,
                "details": {
                    "status": (
                        "disabled"
                        if include_asf_investor_alerts and not ENABLE_ASF_INVESTOR_ALERTS
                        else asf_default_error
                    ),
                    "provider": ASF_INVESTOR_ALERTS_SOURCE,
                },
                "query_ms": 0,
            })
            per_source[ASF_INVESTOR_ALERTS_SOURCE] = {
                "status": asf_investor_alerts_entry.get("status", "unknown"),
                "consulted": bool(include_asf_investor_alerts and ENABLE_ASF_INVESTOR_ALERTS),
                "threat_type": asf_investor_alerts_entry.get("threat_type", "unknown"),
                "details": asf_investor_alerts_entry.get("details", {}),
                "score": _coerce_int(asf_investor_alerts_entry.get("score", 0), 0),
                "query_ms": _coerce_int(asf_investor_alerts_entry.get("query_ms", 0), 0),
            }

            phishing_database_entry = phishing_database_matches.get(key, {
                "status": "unknown" if not include_phishing_database else "error",
                "threat_type": "unknown" if not include_phishing_database else "error",
                "score": 0,
                "details": {"status": "skipped_fast_scan" if not include_phishing_database else "not_scanned"},
                "query_ms": 0,
            })
            per_source[PHISHING_DATABASE_SOURCE] = {
                "status": phishing_database_entry.get("status", "unknown"),
                "consulted": bool(include_phishing_database and ENABLE_PHISHING_DATABASE),
                "threat_type": phishing_database_entry.get("threat_type", "unknown"),
                "details": phishing_database_entry.get("details", {}),
                "score": _coerce_int(phishing_database_entry.get("score", 0), 0),
                "query_ms": _coerce_int(phishing_database_entry.get("query_ms", 0), 0),
            }

            phishtank_entry = phishtank_matches.get(key, {
                "status": "unknown" if not include_phishtank else "error",
                "threat_type": "unknown" if not include_phishtank else "error",
                "score": 0,
                "details": {
                    "status": (
                        "disabled"
                        if include_phishtank and not ENABLE_PHISHTANK
                        else ("skipped_fast_scan" if not include_phishtank else "not_scanned")
                    ),
                    "provider": PHISHTANK_SOURCE,
                },
                "query_ms": 0,
            })
            per_source[PHISHTANK_SOURCE] = {
                "status": phishtank_entry.get("status", "unknown"),
                "consulted": bool(include_phishtank and ENABLE_PHISHTANK),
                "threat_type": phishtank_entry.get("threat_type", "unknown"),
                "details": phishtank_entry.get("details", {}),
                "score": _coerce_int(phishtank_entry.get("score", 0), 0),
                "query_ms": _coerce_int(phishtank_entry.get("query_ms", 0), 0),
            }

            openphish_entry = openphish_matches.get(key, {
                "status": "unknown" if not include_openphish else "error",
                "consulted": False if not include_openphish else bool(ENABLE_OPENPHISH),
                "threat_type": "unknown" if not include_openphish else "error",
                "score": 0,
                "details": {
                    "status": (
                        "disabled"
                        if include_openphish and not ENABLE_OPENPHISH
                        else ("skipped_fast_scan" if not include_openphish else "not_scanned")
                    ),
                    "provider": OPENPHISH_SOURCE,
                },
                "query_ms": 0,
            })
            per_source[OPENPHISH_SOURCE] = {
                "status": openphish_entry.get("status", "unknown"),
                "consulted": bool(include_openphish and openphish_entry.get("consulted", ENABLE_OPENPHISH)),
                "threat_type": openphish_entry.get("threat_type", "unknown"),
                "details": openphish_entry.get("details", {}),
                "score": _coerce_int(openphish_entry.get("score", 0), 0),
                "query_ms": _coerce_int(openphish_entry.get("query_ms", 0), 0),
            }

            urlhaus_default_error = "skipped_fast_scan" if not include_urlhaus else "not_scanned"
            urlhaus_entry = urlhaus_matches.get(key, {
                "status": "unknown" if not include_urlhaus else "error",
                "threat_type": "unknown" if not include_urlhaus else "error",
                "score": 0,
                "details": {"status": "not_configured" if include_urlhaus and not urlhaus_key else urlhaus_default_error},
                "query_ms": 0,
            })
            per_source[URLHAUS_SOURCE] = {
                "status": urlhaus_entry.get("status", "unknown"),
                "consulted": bool(include_urlhaus and urlhaus_entry.get("consulted", bool(urlhaus_key))),
                "threat_type": urlhaus_entry.get("threat_type", "unknown"),
                "details": urlhaus_entry.get("details", {}),
                "score": _coerce_int(urlhaus_entry.get("score", 0), 0),
                "query_ms": _coerce_int(urlhaus_entry.get("query_ms", 0), 0),
            }

            scam_blocklist_default_error = "skipped_fast_scan" if not include_scam_blocklist_nrd else "not_scanned"
            scam_blocklist_nrd_entry = scam_blocklist_nrd_matches.get(key, {
                "status": "unknown" if not include_scam_blocklist_nrd else "error",
                "threat_type": "unknown" if not include_scam_blocklist_nrd else "error",
                "score": 0,
                "details": {
                    "status": (
                        "disabled"
                        if include_scam_blocklist_nrd and not ENABLE_SCAM_BLOCKLIST_NRD
                        else scam_blocklist_default_error
                    ),
                    "provider": SCAM_BLOCKLIST_NRD_SOURCE,
                },
                "query_ms": 0,
            })
            per_source[SCAM_BLOCKLIST_NRD_SOURCE] = {
                "status": scam_blocklist_nrd_entry.get("status", "unknown"),
                "consulted": bool(include_scam_blocklist_nrd and ENABLE_SCAM_BLOCKLIST_NRD),
                "threat_type": scam_blocklist_nrd_entry.get("threat_type", "unknown"),
                "details": scam_blocklist_nrd_entry.get("details", {}),
                "score": _coerce_int(scam_blocklist_nrd_entry.get("score", 0), 0),
                "query_ms": _coerce_int(scam_blocklist_nrd_entry.get("query_ms", 0), 0),
            }

            phishdestroy_default_error = "skipped_fast_scan" if not include_phishdestroy else "not_scanned"
            phishdestroy_entry = phishdestroy_matches.get(key, {
                "status": "unknown" if not include_phishdestroy else "error",
                "threat_type": "unknown" if not include_phishdestroy else "error",
                "score": 0,
                "details": {
                    "status": (
                        "disabled"
                        if include_phishdestroy and not ENABLE_PHISHDESTROY
                        else phishdestroy_default_error
                    ),
                    "provider": PHISHDESTROY_SOURCE,
                },
                "query_ms": 0,
            })
            per_source[PHISHDESTROY_SOURCE] = {
                "status": phishdestroy_entry.get("status", "unknown"),
                "consulted": bool(include_phishdestroy and ENABLE_PHISHDESTROY),
                "threat_type": phishdestroy_entry.get("threat_type", "unknown"),
                "details": phishdestroy_entry.get("details", {}),
                "score": _coerce_int(phishdestroy_entry.get("score", 0), 0),
                "query_ms": _coerce_int(phishdestroy_entry.get("query_ms", 0), 0),
            }

            aggregated = _aggregate_reputation(url, per_source)
            cache_metadata = {
                "version": REPUTATION_CACHE_VERSION,
                "ttl_seconds": REPUTATION_CACHE_TTL_SECONDS,
                "requested_sources": SOURCE_ORDER,
                "consulted_sources": aggregated.get("consulted_sources", []),
                "source_count": len(SOURCE_ORDER),
                "consulted_source_count": aggregated.get("consulted_source_count", 0),
                "from_cache": False,
            }
            if should_persist_results:
                cache_entry = _build_cache_entry(url, aggregated, REPUTATION_CACHE_TTL_SECONDS, cache_metadata)
                cache_entry["sources"] = aggregated.get("sources", per_source)
                cache_entry["cache_metadata"]["provider_errors"] = [
                    source_name
                    for source_name, details in cache_entry["sources"].items()
                    if isinstance(details, dict) and details.get("status") == "error"
                ]
                cache[key] = cache_entry
                updated_cache_entries[key] = cache_entry
                results[key] = _normalize_cached_entry(cache_entry, url, REPUTATION_CACHE_TTL_SECONDS)
            else:
                results[key] = dict(aggregated, cached=False)

    if need_fetch and (persist_partial or (bool(include_phishing_database) and bool(include_phishtank) and include_urlhaus)):
        _save_cache(REPUTATION_CACHE_PATH, cache, remote_subset=updated_cache_entries)
    return results
