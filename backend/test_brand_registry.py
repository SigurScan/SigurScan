import pytest

from services.brand_registry import detect_claimed_brand, match_brand, BRAND_REGISTRY
from services.iban_validator import validate_iban


class TestDetectClaimedBrand:
    def test_detect_enel_from_emitent(self):
        assert detect_claimed_brand("ENEL Energie SA", "factura curent", []) == "enel"

    def test_detect_anaf_from_text(self):
        assert detect_claimed_brand("Ministerul Finantelor", "ANAF notificare", []) == "anaf"

    def test_detect_from_link(self):
        assert detect_claimed_brand(None, "", ["https://www.enel.ro/factura"]) == "enel"

    def test_no_brand_match(self):
        assert detect_claimed_brand("SC Test SRL", "factura servicii", []) is None

    def test_detect_digi(self):
        assert detect_claimed_brand("RCS RDS", "factura internet", []) == "digi"


class TestMatchBrand:
    def test_no_claimed_brand(self):
        result = match_brand("SC Test SRL", "factura", [], "12345678", validate_iban("RO33RNCB1234567890123456"), "RO33RNCB1234567890123456")
        assert result.claimed_brand is None
        assert result.impersonation_risk is False

    def test_enel_matching_domain(self):
        result = match_brand("ENEL Energie", "factura", ["https://www.enel.ro/factura"], "14345906", validate_iban("RO33RNCB1234567890123456"), "RO33RNCB1234567890123456")
        assert result.claimed_brand == "enel"
        assert result.domain_matches is True
        assert result.cui_matches is True
        assert result.impersonation_risk is False

    def test_enel_wrong_domain_impersonation(self):
        result = match_brand("ENEL Energie", "factura", ["https://enel-facturi-usoare.ro/pay"], "14345906", validate_iban("RO33RNCB1234567890123456"), "RO33RNCB1234567890123456")
        assert result.claimed_brand == "enel"
        assert result.domain_matches is False
        assert result.impersonation_risk is True

    def test_anaf_with_commercial_iban(self):
        iban_result = validate_iban("RO33RNCB1234567890123456")
        result = match_brand("ANAF", "amenda", [], "12345678", iban_result, "RO33RNCB1234567890123456")
        assert result.claimed_brand == "anaf"
        assert result.iban_matches is False  # ANAF requires TREZ, got BCR
        assert result.impersonation_risk is True

    def test_anaf_with_trezorerie_iban(self):
        iban_result = validate_iban("RO40TREZ1234567890123456")
        result = match_brand("ANAF", "amenda", [], "12345678", iban_result, "RO40TREZ1234567890123456")
        assert result.claimed_brand == "anaf"
        assert result.iban_matches is True  # TREZ matches
        assert result.impersonation_risk is False

    def test_wrong_cui_for_brand(self):
        result = match_brand("ENEL Energie", "factura", ["https://www.enel.ro"], "99999999", validate_iban("RO33RNCB1234567890123456"), "RO33RNCB1234567890123456")
        assert result.claimed_brand == "enel"
        assert result.cui_matches is False
        assert result.impersonation_risk is True
