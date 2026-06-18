from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

import requests


UPSTASH_TIMEOUT_SECONDS = float(os.getenv("UPSTASH_TIMEOUT_SECONDS", "1.5"))

_memory_lock = threading.Lock()
_memory_counts: dict[tuple[str, str], int] = {}
_LOCAL_USAGE = _memory_counts


@dataclass(frozen=True)
class ProviderBudgetDecision:
    allowed: bool
    provider: str
    period: str
    used: int
    limit: int
    backend: str
    reason: str = ""


def monthly_limit_from_env(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return int(default)
    try:
        return max(0, int(raw))
    except Exception:
        return int(default)


def consume_monthly_budget(
    provider: str,
    *,
    limit: int,
    now: Optional[datetime] = None,
) -> ProviderBudgetDecision:
    return _consume_budget_for_period(provider, _monthly_period(now), limit, now=now)


def try_consume_monthly_budget(
    provider: str,
    *,
    env_name: str,
    default_limit: int,
    month_key: Optional[str] = None,
) -> bool:
    decision = _consume_budget_for_period(
        provider,
        month_key or _monthly_period(),
        monthly_limit_from_env(env_name, default_limit),
    )
    return decision.allowed


def reset_memory_budgets() -> None:
    with _memory_lock:
        _memory_counts.clear()


def _consume_budget_for_period(
    provider: str,
    period: str,
    limit: int,
    *,
    now: Optional[datetime] = None,
) -> ProviderBudgetDecision:
    safe_provider = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in provider.strip().lower())
    safe_limit = max(0, int(limit or 0))
    if not safe_provider:
        return ProviderBudgetDecision(False, provider, period, 0, safe_limit, "invalid", "invalid_provider")
    if safe_limit <= 0:
        return ProviderBudgetDecision(False, safe_provider, period, 0, safe_limit, "disabled", "budget_disabled")

    supabase_decision = _consume_supabase_budget(safe_provider, period, safe_limit)
    if supabase_decision is not None:
        return supabase_decision

    if _upstash_configured():
        try:
            return _consume_upstash_budget(safe_provider, period, safe_limit, now=now)
        except Exception:
            return ProviderBudgetDecision(False, safe_provider, period, 0, safe_limit, "upstash", "budget_store_error")

    return _consume_memory_budget(safe_provider, period, safe_limit)


def _monthly_period(now: Optional[datetime] = None) -> str:
    candidate = now or datetime.now(timezone.utc)
    if candidate.tzinfo is None:
        candidate = candidate.replace(tzinfo=timezone.utc)
    return candidate.astimezone(timezone.utc).strftime("%Y-%m")


def _consume_supabase_budget(provider: str, period: str, limit: int) -> ProviderBudgetDecision | None:
    try:
        from services import supabase_store

        if not supabase_store.is_supabase_enabled():
            return None
        allowed = supabase_store.try_consume_provider_budget(provider, period, limit)
        if allowed is True:
            return ProviderBudgetDecision(True, provider, period, 0, limit, "supabase")
        if allowed is False:
            return ProviderBudgetDecision(False, provider, period, limit, limit, "supabase", "budget_exhausted")
        return ProviderBudgetDecision(False, provider, period, 0, limit, "supabase", "budget_store_error")
    except Exception:
        try:
            from services import supabase_store

            if supabase_store.is_supabase_enabled():
                return ProviderBudgetDecision(False, provider, period, 0, limit, "supabase", "budget_store_error")
        except Exception:
            pass
        return None


def _upstash_configured() -> bool:
    return bool(_upstash_url() and _upstash_token())


def _upstash_url() -> str:
    return os.getenv("UPSTASH_REDIS_REST_URL", "").strip().rstrip("/")


def _upstash_token() -> str:
    return os.getenv("UPSTASH_REDIS_REST_TOKEN", "").strip()


def _seconds_until_next_month(now: Optional[datetime] = None) -> int:
    candidate = now or datetime.now(timezone.utc)
    if candidate.tzinfo is None:
        candidate = candidate.replace(tzinfo=timezone.utc)
    current = candidate.astimezone(timezone.utc)
    if current.month == 12:
        next_month = current.replace(year=current.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        next_month = current.replace(month=current.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return max(3600, int((next_month - current).total_seconds()))


def _consume_memory_budget(provider: str, period: str, limit: int) -> ProviderBudgetDecision:
    key = (provider, period)
    with _memory_lock:
        current = _memory_counts.get(key, 0)
        if current >= limit:
            return ProviderBudgetDecision(False, provider, period, current, limit, "memory_best_effort", "budget_exhausted")
        current += 1
        _memory_counts[key] = current
    return ProviderBudgetDecision(True, provider, period, current, limit, "memory_best_effort")


def _upstash_pipeline(commands: list[list[Any]]) -> list[dict[str, Any]]:
    response = requests.post(
        f"{_upstash_url()}/pipeline",
        json=commands,
        headers={"Authorization": f"Bearer {_upstash_token()}"},
        timeout=UPSTASH_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list):
        raise ValueError("unexpected Upstash pipeline response")
    return data


def _consume_upstash_budget(
    provider: str,
    period: str,
    limit: int,
    *,
    now: Optional[datetime] = None,
) -> ProviderBudgetDecision:
    key = f"sigurscan:provider_budget:{provider}:{period}"
    ttl_seconds = _seconds_until_next_month(now)
    results = _upstash_pipeline([["INCR", key], ["EXPIRE", key, str(ttl_seconds)]])
    used = int((results[0] or {}).get("result") or 0)
    if used > limit:
        try:
            _upstash_pipeline([["DECR", key], ["EXPIRE", key, str(ttl_seconds)]])
        except Exception:
            pass
        return ProviderBudgetDecision(False, provider, period, limit, limit, "upstash", "budget_exhausted")
    return ProviderBudgetDecision(True, provider, period, used, limit, "upstash")
