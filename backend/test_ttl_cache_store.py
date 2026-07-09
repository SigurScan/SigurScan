"""R5 — injectable TTL cache store (behavior-preserving default)."""

from services.ttl_cache_store import InMemoryTtlCacheStore


def test_get_set_roundtrip():
    s = InMemoryTtlCacheStore(3600)
    assert s.get("k") is None
    s.set("k", {"a": 1})
    assert s.get("k") == {"a": 1}


def test_expired_entry_is_evicted_on_read():
    s = InMemoryTtlCacheStore(0)  # everything is immediately stale
    s.set("k", 1)
    assert s.get("k") is None
    assert len(s) == 0  # evicted on read, same as the old dict


def test_clear_empties_the_store():
    s = InMemoryTtlCacheStore(3600)
    s.set("a", 1)
    s.set("b", 2)
    s.clear()
    assert s.get("a") is None
    assert len(s) == 0


def test_invoice_orchestrator_caches_are_injectable_stores():
    from services import invoice_orchestrator as io

    for store in (io._cui_cache, io._verdict_cache):
        # the call sites depend only on get/set/clear -> swappable for a
        # persistent backend without touching invoice_orchestrator.
        assert hasattr(store, "get")
        assert hasattr(store, "set")
        assert hasattr(store, "clear")


def test_cui_cache_roundtrip_through_orchestrator_wrappers():
    from services import invoice_orchestrator as io

    io._cui_cache.clear()
    assert io._get_cached_cui("12345678") is None
    io._set_cached_cui("12345678", {"denumire": "X SRL"})
    assert io._get_cached_cui("12345678") == {"denumire": "X SRL"}
    io._cui_cache.clear()
