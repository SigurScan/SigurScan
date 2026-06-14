"""Audio async / Vishing — contract verdict (MoatOS §14, PR-9, Faza 2/3).

LINIA ROȘIE (§13/§14.5): audio = semnal de ANALIST, niciodată pilon de verdict.
ZERO endpoint nou de audio pe server, ZERO audio brut pe server; procesarea e
on-device (VAD + ASR RO + clasificator arc). De aceea aici NU expunem niciun
endpoint — `build_audio_case_verdict` e logica de REFERINȚĂ (Python) pe care portul
Android o oglindește on-device, alimentată DOAR cu transcript redactat + semnale
deja extrase local (arc, cerere sensibilă, identitate pretinsă, match campanie).

Verdictul reutilizează `verdict_gate.verdict` (judecătorul unic, 4 stări) — NU îl
rescrie. Reguli pinuite (§14.6 DoD):
- STT singur, fără combo → max SUSPECT (STT nu e pilon de verdict).
- Arc „cont sigur" + cerere OTP/transfer + identitate bancă/poliție → DANGEROUS.
- Apel legit de la număr necunoscut, fără cerere sensibilă → NU DANGEROUS
  (max UNVERIFIED/SUSPECT).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from services import verdict_gate

# Reuse aceeași reducere ca în inbox: un singur token sensibil reprezentativ.
_HARD_PRIORITY = ("card", "otp", "cvv", "password", "pin", "crypto", "remote", "id_document")
_VALUE_TOKENS = ("transfer",)
_SENSITIVE_ALIAS = {"cvv": "card"}


def _primary_sensitive(sensitive_asks: Optional[List[str]]) -> str:
    asks = [_SENSITIVE_ALIAS.get(str(a).strip().lower(), str(a).strip().lower())
            for a in (sensitive_asks or []) if a]
    for token in _HARD_PRIORITY:
        tok = _SENSITIVE_ALIAS.get(token, token)
        if tok in asks:
            return tok
    for token in _VALUE_TOKENS:
        if token in asks:
            return token
    return "none"


def _identity_status(identity_provenance: str, claimed_identity: Optional[str]) -> str:
    """O identitate pretinsă (bancă/poliție/BNR) pe un apel telefonic NU e dovedibilă
    prin canal — implicit „mismatch" dacă e pretinsă fără proveniență pozitivă."""
    p = str(identity_provenance or "").strip().lower()
    if p == "match":
        return "official_match"
    if p == "mismatch":
        return "lookalike"
    # identitate pretinsă pe apel, fără proveniență → tratată ca neoficială (lookalike)
    if claimed_identity:
        return "lookalike"
    return "unknown"


def build_audio_case_verdict(
    *,
    transcript_redacted: Optional[str] = None,
    claimed_identity: Optional[str] = None,
    sensitive_asks: Optional[List[str]] = None,
    arc_family: Optional[str] = None,
    identity_provenance: str = "unknown",
    campaign_match: Optional[str] = None,
    campaign_confidence: float = 0.0,
) -> Dict[str, Any]:
    """Produce verdictul pentru un caz audio (vishing) din semnale on-device,
    prin verdict_gate. Niciun audio brut; doar semnale + transcript redactat."""
    sensitive = _primary_sensitive(sensitive_asks)
    identity_status = _identity_status(identity_provenance, claimed_identity)

    # „STT solo": singurul semnal e clasificarea ASR (arc/campanie), fără cerere
    # sensibilă concretă extrasă ȘI fără identitate pretinsă neoficială. În acest
    # caz NU se poate produce DANGEROUS (STT nu e pilon de verdict).
    stt_only = (
        sensitive == "none"
        and identity_status not in {"lookalike"}
    )

    bundle: Dict[str, Any] = {
        "schema": "sigurscan_audio_bundle_v1",
        "resolution": {"status": "not_required", "completeness": True},
        "providers": {},  # niciun provider pe apel → gate îl vede „unknown"
        "identity": {
            "status": identity_status,
            "claimed_brand": claimed_identity,
            "completeness": True,
        },
        "request": {
            "sensitive": sensitive,
            "channel": "phone",   # apel telefonic = canal greșit pt cereri sensibile
            "completeness": True,
        },
        "provenance": {"official_phone_match": identity_status == "official_match"},
        "campaign_match": {
            "status": "match" if campaign_match else "no_match",
            "confidence": float(campaign_confidence or 0.0),
            "family": arc_family,
        },
        "semantic_review": {"status": "done", "risk_class": "none"},
    }

    gate = verdict_gate.verdict(bundle)
    label = gate["label"]
    reasons = list(gate.get("reasons", []))

    # Apărare în adâncime pentru DoD „STT solo → max SUSPECT": dacă gate-ul ar da
    # cumva DANGEROUS doar din semnale ASR (fără cerere sensibilă / identitate
    # neoficială), coboară la SUSPECT. (Cu semnalele de mai sus nu se întâmplă —
    # e o plasă de siguranță explicită, aliniată §13.)
    if stt_only and label == "DANGEROUS":
        label = "SUSPECT"
        reasons = ["stt_only_capped_suspect"]

    return {
        "input_type": "audio",
        "claimed_identity": claimed_identity,
        "arc_family": arc_family,
        "campaign_match": campaign_match,
        "verdict": label,
        "reason_codes": reasons,
        "stt_only": stt_only,
        "processing": "on_device_only",
        "raw_audio_stored": False,
        "transcript_redacted": bool(transcript_redacted),  # doar flag, nu textul
    }
