"""D7 — 'too good to be true' price vs market median.

FP-focused: the signal must fire only on an implausibly cheap, well-known,
high-value product priced in RON, and it must never on its own push an offer to
'high' (DANGEROUS) — only to 'medium' (SUSPECT / verify).
"""

import pytest

from services import price_median_check as pmc
from services import offer_signals as S
from services.offer_evidence_gate_mapper import _semantic_risk
from services.offer_entity_verifier import OfferEntityResult
from services.offer_parser import OfferFields


@pytest.fixture(autouse=True)
def _enable(monkeypatch):
    monkeypatch.setenv("D7_PRICE_MEDIAN", "1")


# --- too_cheap_signal ---

def test_implausibly_cheap_iphone_fires():
    sig = pmc.too_cheap_signal("iPhone 15 sigilat, pret 500 lei, doar azi!", 500, "RON")
    assert sig and sig["offered_ron"] == 500 and sig["offered_ron"] < sig["floor_ron"]


def test_price_near_median_no_signal():
    assert pmc.too_cheap_signal("iPhone 15, pret 3200 lei", 3200, "RON") is None


def test_legit_discount_above_floor_no_signal():
    # 2000 RON is a discount but well above the conservative floor -> not flagged.
    assert pmc.too_cheap_signal("iPhone 15, reducere 2000 lei", 2000, "RON") is None


def test_unknown_product_no_signal():
    assert pmc.too_cheap_signal("Bicicleta second hand, 300 lei", 300, "RON") is None


def test_non_ron_currency_no_signal():
    assert pmc.too_cheap_signal("iPhone 15, 500 euro", 500, "EUR") is None


def test_zero_or_missing_price_no_signal():
    assert pmc.too_cheap_signal("iPhone 15 gratis", 0, "RON") is None
    assert pmc.too_cheap_signal("iPhone 15", None, "RON") is None


def test_multiple_matches_use_lowest_median():
    # "iphone 15 pro" also matches "iphone"; the lowest median (most lenient floor)
    # is used, minimising false positives.
    sig = pmc.too_cheap_signal("iPhone 15 Pro, 500 lei", 500, "RON")
    assert sig["product"] == "iphone_generic"


def test_disabled_by_default_no_signal(monkeypatch):
    monkeypatch.setenv("D7_PRICE_MEDIAN", "0")
    assert pmc.too_cheap_signal("iPhone 15 la 500 lei", 500, "RON") is None


# --- wiring into the offer signals + severity ---

def _offer(text, amount, currency="RON"):
    f = OfferFields()
    f.raw_text = text
    f.total_amount = amount
    f.currency = currency
    return f


def test_derive_offer_signals_emits_code_when_cheap():
    from services.offer_signals import derive_offer_signals
    signals = derive_offer_signals(_offer("PS5 nou sigilat, 400 lei urgent!", 400))
    assert S.OFFER_PRICE_BELOW_MARKET_MEDIAN in signals


def test_derive_offer_signals_silent_when_off(monkeypatch):
    monkeypatch.setenv("D7_PRICE_MEDIAN", "0")
    from services.offer_signals import derive_offer_signals
    signals = derive_offer_signals(_offer("PS5 nou sigilat, 400 lei urgent!", 400))
    assert S.OFFER_PRICE_BELOW_MARKET_MEDIAN not in signals


def test_price_signal_alone_is_medium_not_high():
    # The cardinal-sin guard: a too-cheap price on a benign entity is SUSPECT,
    # never DANGEROUS on its own.
    risk = _semantic_risk([S.OFFER_PRICE_BELOW_MARKET_MEDIAN], OfferEntityResult(), None, None, 0.0)
    assert risk == "medium"
