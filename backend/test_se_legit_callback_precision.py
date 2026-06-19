"""Precision: a legitimate bank fraud alert that tells the user to call the
number on the back of their own card (or open the official app) must NOT be
detected as a 'callback' social-engineering ask.

This is the X2 twin discriminator: "sună la numărul de pe spatele cardului" /
"deschide aplicația" is self-directed verification using a channel the user
already trusts — the opposite of "sună-ne la 0371…" / "rămâneți pe linie".
"""

from copy import deepcopy

from main import (
    _apply_provider_gate_verdict,
    _normalise_obfuscated_text,
    _social_engineering_signal_for_decision_bundle,
    engine,
)
from services.pii_redactor import redact_pii


LEGIT_BACK_OF_CARD = (
    "BCR: am blocat o tranzactie suspecta pe cardul tau. Daca nu ai facut-o tu, "
    "suna la numarul de pe spatele cardului."
)
LEGIT_OPEN_APP = (
    "Revolut: tranzactie de 240 lei pe cardul tau. Daca nu o recunosti, deschide "
    "aplicatia si blocheaza cardul."
)
SCAM_CALL_US = (
    "Departament securitate: tranzactie suspecta pe card. Suna-ne urgent la "
    "0371 00 00 00 ca sa o blocam impreuna, nu inchide."
)


def _label(text, channel="sms"):
    red = redact_pii(_normalise_obfuscated_text(text))
    a = engine.analyze(red, urls=[], external_threat_intel={})
    a.setdefault("evidence", {})["source_channel"] = channel
    fa = _apply_provider_gate_verdict(a, [], raw_text=red, pillars={})
    return fa["evidence"]["verdict_gate"]["label"]


# ── precision: legit self-directed verification ──────────────────────────────

def test_legit_back_of_card_alert_not_dangerous():
    assert _label(LEGIT_BACK_OF_CARD) != "DANGEROUS"


def test_legit_back_of_card_is_not_callback_ask():
    sig = _social_engineering_signal_for_decision_bundle(LEGIT_BACK_OF_CARD, source_channel="sms")
    assert "callback" not in sig["ask_type"]


def test_legit_open_app_alert_not_dangerous():
    assert _label(LEGIT_OPEN_APP) != "DANGEROUS"


# ── recall preserved: scam callback still detected ───────────────────────────

def test_scam_call_us_still_callback():
    sig = _social_engineering_signal_for_decision_bundle(SCAM_CALL_US, source_channel="sms")
    assert "callback" in sig["ask_type"]
