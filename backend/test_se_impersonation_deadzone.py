"""Red->green guard for the social-engineering impersonation dead zone.

`impersonation` is only a build-up intent (-> SUSPECT) and the build-up branch
requires ask_present=False. So an authority/fear impersonation that makes a
concrete ask (fake Police/ANAF demanding identity data) lands in a dead zone:
not actionable (impersonation not in DANGEROUS_SOCIAL_ENGINEERING_INTENTS) and
not build-up (ask is present) -> no escalation. This file pins the fix:
impersonation + ask_present + authority/fear lever + confidence>=0.78 escalates,
while leaving the existing build-up branch untouched.
"""

from services.verdict_gate import (
    _is_actionable_social_engineering,
    _is_social_engineering_build_up,
)


def _se(intent, ask_present, *, confidence=0.92, levers=("authority", "fear"), ask_type=("personal_data",)):
    return {
        "status": "done",
        "intent": intent,
        "ask_present": ask_present,
        "confidence": confidence,
        "ask_type": list(ask_type),
        "levers": list(levers),
    }


def test_impersonation_with_authority_ask_is_actionable():
    # The fix: fake-authority impersonation that MAKES a concrete ask escalates.
    assert _is_actionable_social_engineering(_se("impersonation", True)) is True


def test_impersonation_buildup_branch_unchanged():
    # Build-up (no ask) must stay SUSPECT-level: actionable False, build_up True.
    no_ask = _se("impersonation", False)
    assert _is_actionable_social_engineering(no_ask) is False
    assert _is_social_engineering_build_up(no_ask) is True


def test_impersonation_ask_without_authority_lever_not_actionable():
    # Only authority/fear impersonations escalate; a bare impersonation ask with
    # no authority/fear lever must NOT become actionable (keeps the gate tight).
    weak = _se("impersonation", True, levers=("liking",), ask_type=("none",))
    assert _is_actionable_social_engineering(weak) is False


def test_impersonation_ask_below_confidence_not_actionable():
    low = _se("impersonation", True, confidence=0.5)
    assert _is_actionable_social_engineering(low) is False


def test_existing_dangerous_intents_still_actionable():
    # Regression: the pre-existing dangerous intents must keep escalating.
    assert _is_actionable_social_engineering(_se("credential_theft", True)) is True
    assert _is_actionable_social_engineering(_se("payment_redirection", True)) is True
