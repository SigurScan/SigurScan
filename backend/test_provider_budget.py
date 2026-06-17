from datetime import datetime, timezone

from services.provider_budget import consume_monthly_budget, reset_memory_budgets


def test_monthly_budget_allows_until_limit_then_denies(monkeypatch):
    monkeypatch.delenv("UPSTASH_REDIS_REST_URL", raising=False)
    monkeypatch.delenv("UPSTASH_REDIS_REST_TOKEN", raising=False)
    reset_memory_budgets()
    now = datetime(2026, 6, 17, tzinfo=timezone.utc)

    first = consume_monthly_budget("openapi_ro_company", limit=2, now=now)
    second = consume_monthly_budget("openapi_ro_company", limit=2, now=now)
    third = consume_monthly_budget("openapi_ro_company", limit=2, now=now)

    assert first.allowed is True
    assert second.allowed is True
    assert third.allowed is False
    assert third.used == 2
    assert third.limit == 2
    assert third.period == "2026-06"
    assert third.backend == "memory_best_effort"
