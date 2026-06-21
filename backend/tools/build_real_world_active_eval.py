#!/usr/bin/env python3
"""Build a live real-world SigurScan evaluation corpus from public sources.

The generated corpus is intentionally written under build/reports so active
phishing URLs are not committed to the repository. Source feeds are public
defensive feeds; reports redact dangerous URLs by default when printed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
import sys
import time
import urllib.parse
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests


REPO_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from main import _canonicalize_url  # noqa: E402
from services import url_reputation  # noqa: E402


UA = "SigurScan real-world defensive evaluation builder (sigurscan@sigurscan.com)"

MALICIOUS_FEEDS = {
    "openphish": "https://openphish.com/feed.txt",
    "urlhaus_recent": "https://urlhaus.abuse.ch/downloads/csv_recent/",
    "phishtank_online_valid": "https://data.phishtank.com/data/online-valid.csv",
    "phishing_database_active": "https://phish.co.za/latest/phishing-links-ACTIVE.txt",
}


@dataclass(frozen=True)
class UrlRecord:
    url: str
    source: str
    source_truth: str
    source_ref: str
    first_seen: str = ""
    tags: tuple[str, ...] = ()


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _fetch_text(url: str, *, timeout: int = 45) -> str:
    response = requests.get(url, timeout=timeout, headers={"User-Agent": UA})
    response.raise_for_status()
    return response.text


def _clean_url(value: Any) -> str:
    raw = str(value or "").strip().strip('"').strip("'")
    if not raw:
        return ""
    if raw.lower().startswith(("hxxp://", "hxxps://")):
        raw = "http" + raw[4:]
    canonical = _canonicalize_url(raw) or raw
    parsed = urllib.parse.urlparse(canonical)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return canonical


def _host(url: str) -> str:
    return (urllib.parse.urlparse(url).hostname or "").lower()


def _registeredish(host: str) -> str:
    parts = host.strip(".").split(".")
    if len(parts) >= 3 and parts[-2] in {"co", "com", "org", "net"} and len(parts[-1]) == 2:
        return ".".join(parts[-3:])
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host


def _is_public_http_url(url: str) -> bool:
    host = _host(url)
    if not host or host in {"localhost", "127.0.0.1", "::1"}:
        return False
    if host.endswith((".test", ".invalid", ".example", ".local")):
        return False
    return True


def _parse_openphish(text: str) -> List[UrlRecord]:
    rows = []
    for line in text.splitlines():
        url = _clean_url(line)
        if url and _is_public_http_url(url):
            rows.append(UrlRecord(url, "openphish", "listed_active_phishing", MALICIOUS_FEEDS["openphish"]))
    return rows


def _parse_phishing_database(text: str) -> List[UrlRecord]:
    rows = []
    for line in text.splitlines():
        url = _clean_url(line)
        if url and _is_public_http_url(url):
            rows.append(
                UrlRecord(
                    url,
                    "phishing_database_active",
                    "listed_active_phishing",
                    MALICIOUS_FEEDS["phishing_database_active"],
                )
            )
    return rows


def _parse_urlhaus_csv(text: str) -> List[UrlRecord]:
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("# id,"):
            lines.append(line[2:])
            continue
        if line.startswith("#"):
            continue
        lines.append(raw_line)
    cleaned = "\n".join(lines)
    if not cleaned.strip():
        return []
    reader = csv.DictReader(cleaned.splitlines())
    rows = []
    for item in reader:
        url = _clean_url(item.get("url"))
        if not url or not _is_public_http_url(url):
            continue
        status = str(item.get("url_status") or "").lower()
        if status and status != "online":
            continue
        tags = tuple(filter(None, re.split(r"[,\s]+", str(item.get("tags") or ""))))
        rows.append(
            UrlRecord(
                url,
                "urlhaus_recent",
                "listed_online_malware_or_phishing",
                MALICIOUS_FEEDS["urlhaus_recent"],
                first_seen=str(item.get("dateadded") or ""),
                tags=tags,
            )
        )
    return rows


def _parse_phishtank_csv(text: str) -> List[UrlRecord]:
    reader = csv.DictReader(text.splitlines())
    rows = []
    for item in reader:
        if str(item.get("verified") or "").lower() != "yes":
            continue
        if str(item.get("online") or "").lower() != "yes":
            continue
        url = _clean_url(item.get("url"))
        if not url or not _is_public_http_url(url):
            continue
        rows.append(
            UrlRecord(
                url,
                "phishtank_online_valid",
                "verified_online_phishing",
                MALICIOUS_FEEDS["phishtank_online_valid"],
                first_seen=str(item.get("submission_time") or ""),
            )
        )
    return rows


def _load_malicious_urls() -> tuple[List[UrlRecord], Dict[str, Any]]:
    parsers = {
        "openphish": _parse_openphish,
        "urlhaus_recent": _parse_urlhaus_csv,
        "phishtank_online_valid": _parse_phishtank_csv,
        "phishing_database_active": _parse_phishing_database,
    }
    all_rows: List[UrlRecord] = []
    summary: Dict[str, Any] = {}
    for source, url in MALICIOUS_FEEDS.items():
        started = time.time()
        try:
            text = url_reputation._download_phishtank_feed() if source == "phishtank_online_valid" else _fetch_text(url)
            rows = parsers[source](text)
            all_rows.extend(rows)
            summary[source] = {
                "url": url,
                "status": "ok",
                "rows": len(rows),
                "elapsed_sec": round(time.time() - started, 2),
            }
        except Exception as exc:
            summary[source] = {
                "url": url,
                "status": "error",
                "error": f"{type(exc).__name__}: {exc}",
                "elapsed_sec": round(time.time() - started, 2),
            }
    return all_rows, summary


def _load_official_domains(limit: int = 220) -> List[Dict[str, Any]]:
    path = BACKEND_DIR / "data" / "brand_knowledge_pack.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    registry = payload.get("brand_registry") if isinstance(payload.get("brand_registry"), dict) else {}
    source_refs_by_brand: Dict[str, List[Dict[str, Any]]] = {}
    for item in payload.get("official_registry_updates") or []:
        if not isinstance(item, dict):
            continue
        source_refs_by_brand[str(item.get("display_name") or item.get("brand_id") or "").lower()] = [
            ref for ref in item.get("source_urls") or [] if isinstance(ref, dict)
        ]

    seen: set[str] = set()
    out: List[Dict[str, Any]] = []
    for brand, domains in registry.items():
        for domain in domains or []:
            domain = str(domain or "").strip().lower()
            if not domain or domain in seen:
                continue
            seen.add(domain)
            out.append(
                {
                    "brand": brand,
                    "domain": domain,
                    "url": f"https://{domain}/",
                    "source_truth": "official_domain_registry",
                    "source_refs": source_refs_by_brand.get(str(brand).lower(), []),
                }
            )
            if len(out) >= limit:
                return out
    return out


def _probe_safe_urls(rows: List[Dict[str, Any]], *, want: int, timeout: float = 5.0) -> List[Dict[str, Any]]:
    active = []
    for item in rows:
        url = item["url"]
        status_code: Optional[int] = None
        final_url = ""
        error = ""
        try:
            response = requests.get(
                url,
                timeout=timeout,
                allow_redirects=True,
                headers={"User-Agent": UA},
                stream=True,
            )
            status_code = response.status_code
            final_url = response.url
            response.close()
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        if status_code is not None and status_code < 500:
            copied = dict(item)
            copied["status_code"] = status_code
            copied["final_url"] = final_url or url
            active.append(copied)
        elif error:
            continue
        if len(active) >= want:
            break
    return active


def _dedupe_balanced(records: Iterable[UrlRecord], *, per_source: int, total: int) -> List[UrlRecord]:
    grouped: Dict[str, List[UrlRecord]] = defaultdict(list)
    seen_url: set[str] = set()
    seen_domain_source: set[tuple[str, str]] = set()
    for record in records:
        if record.url in seen_url:
            continue
        domain = _registeredish(_host(record.url))
        key = (record.source, domain)
        if key in seen_domain_source:
            continue
        seen_url.add(record.url)
        seen_domain_source.add(key)
        grouped[record.source].append(record)

    rng = random.Random(20260621)
    selected: List[UrlRecord] = []
    for source in sorted(grouped):
        rows = grouped[source]
        rng.shuffle(rows)
        selected.extend(rows[:per_source])
    if len(selected) < total:
        leftovers = [r for rows in grouped.values() for r in rows if r not in selected]
        rng.shuffle(leftovers)
        selected.extend(leftovers[: total - len(selected)])
    rng.shuffle(selected)
    return selected[:total]


def _hash_url(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def _live_case(case_id: str, title: str, text: str, *, input_type: str, source_channel: str, refs: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "case_id": case_id,
        "title": title,
        "text": text,
        "input_type": input_type,
        "source_channel": source_channel,
        "expected_labels": ["SAFE", "SUSPECT", "DANGEROUS", "UNVERIFIED"],
        "source_refs": refs,
        "max_seconds": 120,
    }


def build(args: argparse.Namespace) -> Dict[str, Any]:
    malicious_rows, feed_summary = _load_malicious_urls()
    selected_malicious = _dedupe_balanced(malicious_rows, per_source=args.per_malicious_source, total=args.malicious_total)
    safe_candidates = _load_official_domains()
    active_safe = _probe_safe_urls(safe_candidates, want=args.safe_total)

    cases: List[Dict[str, Any]] = []
    manifest_rows: List[Dict[str, Any]] = []

    for idx, record in enumerate(selected_malicious, start=1):
        case_id = f"RW-ACTIVE-MAL-URL-{idx:03d}"
        refs = [{"source_id": record.source, "url": record.source_ref, "truth": record.source_truth}]
        cases.append(
            _live_case(
                case_id,
                f"Active malicious URL from {record.source}",
                record.url,
                input_type="url",
                source_channel="real_world_active_threat_feed",
                refs=refs,
            )
        )
        manifest_rows.append(
            {
                "case_id": case_id,
                "category": "active_malicious_url",
                "source": record.source,
                "source_truth": record.source_truth,
                "url_sha256_16": _hash_url(record.url),
                "host": _host(record.url),
                "registered_domain": _registeredish(_host(record.url)),
                "first_seen": record.first_seen,
                "tags": list(record.tags),
            }
        )

    for idx, item in enumerate(active_safe, start=1):
        case_id = f"RW-ACTIVE-SAFE-URL-{idx:03d}"
        refs = item.get("source_refs") or [{"source_id": "brand_knowledge_pack", "url": "backend/data/brand_knowledge_pack.json"}]
        cases.append(
            _live_case(
                case_id,
                f"Active official URL for {item['brand']}",
                item["final_url"] or item["url"],
                input_type="url",
                source_channel="real_world_active_official_registry",
                refs=refs,
            )
        )
        manifest_rows.append(
            {
                "case_id": case_id,
                "category": "active_official_url",
                "brand": item["brand"],
                "domain": item["domain"],
                "url_sha256_16": _hash_url(item["final_url"] or item["url"]),
                "status_code": item.get("status_code"),
                "source_truth": item.get("source_truth"),
            }
        )

    # QR payload cases use real active URLs; image generation is handled by the
    # Android/device layer when needed. Keeping payloads here avoids checking in
    # bulky PNG artifacts while preserving exact real-world payloads.
    for idx, record in enumerate(selected_malicious[: args.qr_malicious_total], start=1):
        case_id = f"RW-ACTIVE-MAL-QR-{idx:03d}"
        refs = [{"source_id": record.source, "url": record.source_ref, "truth": record.source_truth}]
        cases.append(
            _live_case(
                case_id,
                f"QR payload with active malicious URL from {record.source}",
                record.url,
                input_type="url",
                source_channel="real_world_active_qr_payload",
                refs=refs,
            )
        )
        manifest_rows.append(
            {
                "case_id": case_id,
                "category": "active_malicious_qr_payload",
                "source": record.source,
                "source_truth": record.source_truth,
                "url_sha256_16": _hash_url(record.url),
                "host": _host(record.url),
            }
        )

    return {
        "metadata": {
            "generated_at": _now_iso(),
            "purpose": "Unlabeled real-world active corpus for SigurScan live/offline evaluation.",
            "labels": "No expected verdict is embedded; source_truth is provenance, not a desired app answer.",
            "malicious_feeds": MALICIOUS_FEEDS,
            "counts": dict(Counter(row["category"] for row in manifest_rows)),
            "feed_summary": feed_summary,
        },
        "live_cases": cases,
        "manifest": manifest_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="build/reports/real_world_active_2026-06-21")
    parser.add_argument("--malicious-total", type=int, default=100)
    parser.add_argument("--per-malicious-source", type=int, default=30)
    parser.add_argument("--safe-total", type=int, default=100)
    parser.add_argument("--qr-malicious-total", type=int, default=50)
    args = parser.parse_args()

    corpus = build(args)
    out_dir = Path(args.output_dir)
    if not out_dir.is_absolute():
        out_dir = REPO_DIR / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    live_cases_path = out_dir / "real_world_active_live_cases_unlabeled.json"
    manifest_path = out_dir / "real_world_active_manifest_redacted.json"
    private_path = out_dir / "real_world_active_private_full.json"

    live_cases_path.write_text(json.dumps(corpus["live_cases"], ensure_ascii=False, indent=2), encoding="utf-8")
    manifest_path.write_text(json.dumps({"metadata": corpus["metadata"], "manifest": corpus["manifest"]}, ensure_ascii=False, indent=2), encoding="utf-8")
    private_path.write_text(json.dumps(corpus, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "generated_at": corpus["metadata"]["generated_at"],
        "counts": corpus["metadata"]["counts"],
        "feed_summary": corpus["metadata"]["feed_summary"],
        "live_cases_path": str(live_cases_path),
        "manifest_path": str(manifest_path),
        "private_full_path": str(private_path),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
