from copy import deepcopy

from services import verdict_gate


def _bundle(
    *,
    resolution_status: str = "failed",
    resolution_complete: bool = False,
    providers_verdict: str = "clean",
    provider_complete: bool = True,
    identity_status: str = "unknown",
    semantic_risk: str = "high",
    semantic_status: str = "done",
    matched_family: str = "hidden_click_payment_or_confirm_cta",
    known_family: bool = True,
    safety_education: bool = False,
) -> dict:
    reason_codes = ["semantic:high"]
    matched_template = None
    if safety_education:
        reason_codes.append("semantic:safety_education_scope")
        matched_template = "safety_education"

    return {
        "schema": "sigurscan_evidence_bundle_v2",
        "input": {
            "type": "url",
            "redacted_text": "Destinație redactată",
        },
        "resolution": {
            "status": resolution_status,
            "completeness": resolution_complete,
        },
        "providers": {
            "verdict": providers_verdict,
            "completeness": provider_complete,
        },
        "identity": {
            "status": identity_status,
            "completeness": True,
        },
        "request": {
            "sensitive": "none",
            "channel": "unknown",
            "positive_action_request": not safety_education,
            "protective_warning": safety_education,
            "completeness": True,
        },
        "semantic_review": {
            "status": semantic_status,
            "risk_class": semantic_risk,
            "confidence": 0.92,
            "matched_family": matched_family,
            "matched_template": matched_template,
            "claim_matches_known_scam_family": known_family,
            "reason_codes": reason_codes,
            "completeness": True,
        },
    }


def test_monotonic_fraud_floor_flag_defaults_off():
    assert verdict_gate.VERDICT_GATE_MONOTONIC_FRAUD_FLOOR_DEFAULT is False


def test_active_gate_stays_unchanged_while_flag_is_off(monkeypatch):
    bundle = _bundle()
    monkeypatch.setattr(verdict_gate, "VERDICT_GATE_MONOTONIC_FRAUD_FLOOR", False)

    result = verdict_gate.verdict(bundle)

    assert result["label"] == "UNVERIFIED"
    assert result["reason_codes"] == ["insufficient_evidence"]


def test_monotonic_candidate_preserves_dangerous_structural_semantic_evidence():
    bundle = _bundle()
    original = deepcopy(bundle)

    result = verdict_gate.verdict_monotonic_candidate(bundle)

    assert result["label"] == "DANGEROUS"
    assert "semantic_high_structural_hidden_action" in result["reason_codes"]
    assert "incomplete_evidence_fraud_floor_preserved" in result["reason_codes"]
    assert bundle == original


def test_monotonic_candidate_preserves_suspect_known_family_floor():
    result = verdict_gate.verdict_monotonic_candidate(
        _bundle(matched_family="impersonation_delivery_notice")
    )

    assert result["label"] == "SUSPECT"
    assert "semantic_high_family_match" in result["reason_codes"]
    assert "incomplete_evidence_fraud_floor_preserved" in result["reason_codes"]


def test_monotonic_candidate_cannot_promote_incomplete_positive_provenance_to_safe():
    bundle = _bundle(
        identity_status="official",
        semantic_risk="benign",
        matched_family="",
        known_family=False,
    )

    result = verdict_gate.verdict_monotonic_candidate(bundle)

    assert result["label"] == "UNVERIFIED"
    assert result["reason_codes"] == ["insufficient_evidence"]


def test_monotonic_candidate_keeps_safety_education_non_dangerous():
    result = verdict_gate.verdict_monotonic_candidate(_bundle(safety_education=True))

    assert result["label"] == "UNVERIFIED"
    assert result["reason_codes"] == ["safety_education_not_action_request"]


def test_monotonic_candidate_without_positive_fraud_signal_remains_unverified():
    bundle = _bundle(
        semantic_risk="unknown",
        semantic_status="pending",
        matched_family="",
        known_family=False,
    )

    result = verdict_gate.verdict_monotonic_candidate(bundle)

    assert result["label"] == "UNVERIFIED"
    assert result["reason_codes"] == ["insufficient_evidence"]


def test_monotonic_candidate_does_not_escalate_official_promo_without_positive_request():
    bundle = _bundle(
        identity_status="official",
        semantic_risk="medium",
        matched_family="RO_SCN_019_ALTEXT_EMAG_PROMO_GUARD",
    )
    bundle["request"].update(
        sensitive="transfer",
        channel="official",
        positive_action_request=False,
    )
    bundle["semantic_review"].update(
        confidence_class="medium",
        confidence=0.49,
        family_confidence=0.49,
    )

    result = verdict_gate.verdict_monotonic_candidate(bundle)

    assert result["label"] == "UNVERIFIED"
    assert result["reason_codes"] == ["insufficient_evidence"]


def test_monotonic_candidate_does_not_trust_low_confidence_semantic_identity_mismatch():
    bundle = _bundle(
        identity_status="unrelated",
        matched_family="F23",
    )
    bundle["request"].update(
        channel="unofficial_site",
        positive_action_request=False,
    )
    bundle["semantic_review"].update(
        confidence_class="medium",
        confidence=0.37,
        family_confidence=0.37,
    )

    result = verdict_gate.verdict_monotonic_candidate(bundle)

    assert result["label"] == "UNVERIFIED"
    assert result["reason_codes"] == ["insufficient_evidence"]


def test_monotonic_candidate_does_not_escalate_official_payment_on_medium_semantic_confidence():
    bundle = _bundle(
        identity_status="official",
        matched_family="IMP-06",
    )
    bundle["request"].update(
        sensitive="transfer",
        channel="official",
        positive_action_request=True,
    )
    bundle["semantic_review"].update(
        confidence_class="medium",
        confidence=0.48,
        family_confidence=0.48,
    )

    result = verdict_gate.verdict_monotonic_candidate(bundle)

    assert result["label"] == "UNVERIFIED"
    assert result["reason_codes"] == ["insufficient_evidence"]


def test_monotonic_candidate_does_not_override_uncontradicted_official_provenance():
    bundle = _bundle(
        identity_status="official",
        matched_family="bank_credential_update_phish",
    )
    bundle["providers"].update(verdict="pending", completeness=False)
    bundle["request"].update(
        sensitive="password",
        channel="official",
        positive_action_request=True,
    )
    bundle["provenance"] = {
        "official_domain_match": True,
        "provenance": "match",
    }

    result = verdict_gate.verdict_monotonic_candidate(bundle)

    assert result["label"] == "UNVERIFIED"
    assert result["reason_codes"] == ["insufficient_evidence"]


def test_monotonic_candidate_requires_explicit_action_for_semantic_family_floor():
    bundle = _bundle(matched_family="support_tech_remote_access")
    bundle["request"].pop("positive_action_request")

    result = verdict_gate.verdict_monotonic_candidate(bundle)

    assert result["label"] == "UNVERIFIED"
    assert result["reason_codes"] == ["insufficient_evidence"]


def test_monotonic_candidate_requires_explicit_action_for_value_request_floor():
    bundle = _bundle(
        identity_status="official",
        semantic_risk="medium",
        matched_family="supplier_account_change",
    )
    bundle["request"].update(sensitive="transfer", channel="official")
    bundle["request"].pop("positive_action_request")
    bundle["semantic_review"].update(
        confidence_class="medium",
        confidence=0.55,
        family_confidence=0.55,
    )
    bundle["provenance"] = {"official_email_match": True, "provenance": "match"}

    result = verdict_gate.verdict_monotonic_candidate(bundle)

    assert result["label"] == "UNVERIFIED"
    assert result["reason_codes"] == ["insufficient_evidence"]


def test_monotonic_candidate_leaves_invoice_inputs_to_invoice_truth_reducer():
    bundle = _bundle(
        identity_status="unknown",
        semantic_risk="medium",
        matched_family="",
        known_family=False,
    )
    bundle["input"]["type"] = "invoice"
    bundle["request"].update(sensitive="transfer", channel="invoice")

    result = verdict_gate.verdict_monotonic_candidate(bundle)

    assert result["label"] == "UNVERIFIED"
    assert result["reason_codes"] == ["insufficient_evidence"]


def test_monotonic_candidate_caps_subthreshold_high_semantic_combo_at_suspect():
    bundle = _bundle(
        identity_status="unrelated",
        matched_family="RO_SCN_001_FAN_LOCKER_WHATSAPP",
    )
    bundle["request"].update(
        channel="reply",
        positive_action_request=True,
    )
    bundle["semantic_review"].update(
        confidence_class="high",
        confidence=0.61,
        family_confidence=0.61,
    )

    result = verdict_gate.verdict_monotonic_candidate(bundle)

    assert result["label"] == "SUSPECT"
    assert "semantic_high_risk_incomplete_floor" in result["reason_codes"]
    assert "incomplete_evidence_fraud_floor_preserved" in result["reason_codes"]


def test_monotonic_candidate_keeps_high_confidence_semantic_combo_dangerous():
    bundle = _bundle(
        identity_status="unrelated",
        matched_family="IMP-01",
    )
    bundle["request"].update(
        channel="unofficial_site",
        positive_action_request=True,
    )
    bundle["semantic_review"].update(
        confidence_class="high",
        confidence=0.73,
        family_confidence=0.73,
    )

    result = verdict_gate.verdict_monotonic_candidate(bundle)

    assert result["label"] == "DANGEROUS"
    assert "semantic_high_risk_match" in result["reason_codes"]
    assert "incomplete_evidence_fraud_floor_preserved" in result["reason_codes"]


def test_enabled_flag_uses_monotonic_candidate_without_changing_default(monkeypatch):
    bundle = _bundle()
    monkeypatch.setattr(verdict_gate, "VERDICT_GATE_MONOTONIC_FRAUD_FLOOR", True)

    result = verdict_gate.verdict(bundle)

    assert result["label"] == "DANGEROUS"
    assert "incomplete_evidence_fraud_floor_preserved" in result["reason_codes"]
