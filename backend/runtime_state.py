"""Runtime state containers for backend shared process memory."""

from typing import Any, Dict

# Shared in-memory caches for quick preview lookups.
_URLSCAN_PREVIEW_CACHE: Dict[str, Dict[str, Any]] = {}
_FAST_PREVIEW_CACHE: Dict[str, Dict[str, Any]] = {}
