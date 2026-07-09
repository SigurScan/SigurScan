"""R5 — injectable TTL cache store.

Replaces the ad-hoc module-level `{key: (timestamp, value)}` dicts in
invoice_orchestrator with a small, swappable abstraction. The default
`InMemoryTtlCacheStore` reproduces the previous behavior exactly (same TTL, same
expiry-on-read); a persistent backend (Redis / Supabase, with TTL) can later be
dropped in without touching the call sites, since they only depend on this
interface. Behavior-preserving: default store == the old dicts.
"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional, Protocol, Tuple


class TtlCacheStore(Protocol):
    """Minimal interface the invoice caches depend on."""

    def get(self, key: str) -> Optional[Any]:
        ...

    def set(self, key: str, value: Any) -> None:
        ...

    def clear(self) -> None:
        ...


class InMemoryTtlCacheStore:
    """Process-local TTL cache. Same semantics as the previous inline dicts:
    a value is returned only while younger than ``ttl_seconds``; an expired entry
    is evicted on read."""

    def __init__(self, ttl_seconds: float) -> None:
        self._ttl = float(ttl_seconds)
        self._data: Dict[str, Tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        entry = self._data.get(key)
        if entry is not None and (time.time() - entry[0]) < self._ttl:
            return entry[1]
        if entry is not None:
            del self._data[key]
        return None

    def set(self, key: str, value: Any) -> None:
        self._data[key] = (time.time(), value)

    def clear(self) -> None:
        self._data.clear()

    def __len__(self) -> int:
        return len(self._data)
