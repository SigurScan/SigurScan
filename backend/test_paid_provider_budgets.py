"""Tests for the paid-provider monthly budget gates (#82)."""

from services import provider_budget
from services.paid_provider_budgets import (
    consume_gemini,
    consume_google_vision,
    consume_mistral,
    consume_web_risk,
)


def setup_function(_function):
    provider_budget.reset_memory_budgets()


def test_vision_budget_allows_until_limit(monkeypatch):
    monkeypatch.setenv("GOOGLE_VISION_MONTHLY_BUDGET", "2")
    assert consume_google_vision() is True
    assert consume_google_vision() is True
    assert consume_google_vision() is False


def test_web_risk_budget_allows_until_limit(monkeypatch):
    monkeypatch.setenv("WEB_RISK_MONTHLY_BUDGET", "1")
    assert consume_web_risk() is True
    assert consume_web_risk() is False


def test_zero_budget_disables_provider(monkeypatch):
    monkeypatch.setenv("MISTRAL_MONTHLY_BUDGET", "0")
    assert consume_mistral() is False


def test_default_budget_allows_normal_usage(monkeypatch):
    monkeypatch.delenv("GEMINI_MONTHLY_BUDGET", raising=False)
    assert consume_gemini() is True


def test_budgets_are_tracked_per_provider(monkeypatch):
    monkeypatch.setenv("GOOGLE_VISION_MONTHLY_BUDGET", "1")
    monkeypatch.setenv("MISTRAL_MONTHLY_BUDGET", "1")
    assert consume_google_vision() is True
    # Vision exhausted must not exhaust Mistral.
    assert consume_google_vision() is False
    assert consume_mistral() is True
