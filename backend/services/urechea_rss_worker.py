"""Bounded RSS worker for PR-3 Urechea OSINT ingestion.

The worker is intentionally thin: it reuses CampaignStore persistence and CFX
seeding, so the same data path is exercised whether intel comes from the API or
from a scheduled job.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from typing import Dict, Iterable, List, Optional


if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.campaign_intel import CampaignStore
from services.cfx_engine import CfxStore
from services.urechea_ingester import UrecheaIngester


logger = logging.getLogger("urechea_rss_worker")


def _source_names(ingester: UrecheaIngester, requested: Optional[Iterable[str]]) -> List[str]:
    if requested:
        names: List[str] = []
        for raw_name in requested:
            names.extend(name.strip() for name in str(raw_name).split(",") if name.strip())
        return [name for name in names if name in ingester.sources]
    return [
        name
        for name, source in ingester.sources.items()
        if source.enabled and source.fetch_strategy == "rss"
    ]


def run(source_names: Optional[Iterable[str]] = None, *, max_entries_per_source: int = 10) -> Dict[str, object]:
    started_at = time.time()
    store = CampaignStore()
    cfx_store = CfxStore()
    ingester = UrecheaIngester(store)
    sources = _source_names(ingester, source_names)

    ingested = 0
    errors: List[Dict[str, str]] = []
    per_source: Dict[str, int] = {}

    for source_name in sources:
        try:
            source = ingester.sources[source_name]
            entries = ingester.fetch_source(source_name)[:max_entries_per_source]
            count = 0
            for entry in entries:
                intel = ingester.ingest_raw(
                    title=entry.get("title", ""),
                    body=entry.get("body", ""),
                    source_url=entry.get("link", source.feed_url or ""),
                    source_kind=source.kind,
                    evidence_quality=source.confidence,
                )
                cfx_store.seed_from_campaigns([intel])
                count += 1
            per_source[source_name] = count
            ingested += count
        except Exception as exc:  # pragma: no cover - defensive worker logging
            logger.warning("Urechea worker failed for %s: %s", source_name, exc)
            errors.append({"source": source_name, "error": str(exc)[:160]})

    return {
        "status": "ok" if not errors else "partial",
        "started_at": started_at,
        "finished_at": time.time(),
        "sources": sources,
        "entries_ingested": ingested,
        "per_source": per_source,
        "errors": errors,
        "campaign_count": len(store.all()),
        "fingerprint_count": len(cfx_store.all()),
    }


def main(argv: Optional[List[str]] = None) -> int:
    logging.basicConfig(level=os.getenv("URECHEA_LOG_LEVEL", "INFO"))
    args = list(argv if argv is not None else sys.argv[1:])
    result = run(args or None)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] in {"ok", "partial"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
