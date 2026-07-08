import pytest

from services.payment_destination_registry import _payment_destination_state


@pytest.mark.parametrize(
    "brand,cui,official,conflict,exp_brand,exp_safe,exp_state",
    [
        (True, True, True, False, True, True, "confirmed_safe"),
        (True, False, True, False, True, False, "verify_divergent_cui"),
        (True, False, False, False, False, False, "belongs_elsewhere"),
        (False, True, True, False, False, True, "confirmed_safe"),
        (True, True, True, True, True, False, "matched_unconfirmed"),
        (True, None, False, False, True, False, "matched_unconfirmed"),
    ],
)
def test_payment_destination_state_matrix(
    brand, cui, official, conflict, exp_brand, exp_safe, exp_state
):
    s = _payment_destination_state(
        brand_matches=brand,
        cui_matches=cui,
        destination_is_official=official,
        has_conflicting_non_safe_context=conflict,
    )
    assert s["brand_matches"] is exp_brand
    assert s["can_contribute_to_safe"] is exp_safe
    assert s["destination_state"] == exp_state
