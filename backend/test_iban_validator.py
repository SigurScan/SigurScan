import pytest

from services.iban_validator import validate_iban, normalize_iban, RO_BANK_CODES


def test_valid_ro_iban_bcr():
    result = validate_iban("RO33RNCB1234567890123456")
    assert result.valid_structure is True
    assert result.bank_code == "RNCB"
    assert result.bank_name == "BCR"
    assert result.is_trezorerie is False


def test_valid_ro_iban_bt():
    result = validate_iban("RO57BTRL1234567890123456")
    assert result.valid_structure is True
    assert result.bank_code == "BTRL"
    assert result.bank_name == "Banca Transilvania"
    assert result.is_trezorerie is False


def test_trezorerie_iban():
    result = validate_iban("RO40TREZ1234567890123456")
    assert result.valid_structure is True
    assert result.bank_code == "TREZ"
    assert result.bank_name == "Trezoreria Statului"
    assert result.is_trezorerie is True


def test_iban_too_short():
    result = validate_iban("RO12BTRL1234")
    assert result.valid_structure is False


def test_iban_invalid_checksum():
    result = validate_iban("RO66RNCB0000000000000001")
    assert result.valid_structure is False


def test_iban_normalize_removes_spaces():
    result = validate_iban("RO33 RNCB 1234 5678 9012 3456")
    assert result.valid_structure is True
    assert result.bank_code == "RNCB"


def test_iban_empty():
    result = validate_iban("")
    assert result.valid_structure is False


def test_iban_none():
    result = validate_iban("  ")
    assert result.valid_structure is False


def test_non_ro_iban():
    result = validate_iban("DE89370400440532013000")
    assert result.valid_structure is True
    assert result.bank_code is None  # not in RO registry
    assert result.is_trezorerie is False


def test_unknown_bank_code():
    result = validate_iban("RO84ZZZZ1234567890123456")
    assert result.valid_structure is True
    assert result.bank_code == "ZZZZ"
    assert result.bank_name is None  # not in RO_BANK_CODES
    assert result.is_trezorerie is False


def test_normalize_iban():
    assert normalize_iban("RO66 RNCB 1234 5678 9012 3456") == "RO66RNCB1234567890123456"
    assert normalize_iban("ro66rncb1234567890123456") == "RO66RNCB1234567890123456"
    assert normalize_iban("") is None
    assert normalize_iban("   ") is None
