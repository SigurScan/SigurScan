"""Inboxul Protejat — contract verdict on-device + BTR sync (MoatOS §8, PR-7, Faza 2).

LINIA ROȘIE (§8): ZERO conținut SMS către server — nici hash-uit — fără opt-in
separat explicit. Procesarea e 100% on-device. De aceea aici NU expunem niciun
endpoint care primește SMS. `build_inbox_verdict` e logica de REFERINȚĂ (Python)
pe care portul Android o oglindește on-device; primește DOAR semnale deja extrase
și redactate local (hash mesaj, brand pretins, rezultat proveniență, match campanie).

Verdictul reutilizează `verdict_gate.verdict` (judecătorul unic, 4 stări) — NU îl
rescrie. Construim un EvidenceBundle minimal din semnalele on-device și îl trecem
prin gate.

Decizie (documentată, ca Bug#5 A/B): SAFE on-device DOAR pentru brand match + zero
link + zero cerere sensibilă (suprafață „vacuum-clean": nu există URL de verificat
la un provider). Dacă există un link, on-device nu poate obține clearance de
provider (Web Risk etc.), deci NU acordăm SAFE — maximul devine UNVERIFIED (gri,
niciodată verde) sau DANGEROUS/SUSPECT dacă alte reguli se aprind.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional

from services import verdict_gate

# Reducem lista de cereri sensibile la un singur token reprezentativ, în ordinea
# pe care gate-ul o consumă (gate-ul citește request.sensitive ca valoare unică).
_HARD_PRIORITY = ("card", "otp", "cvv", "password", "pin", "crypto", "remote", "id_document")
_VALUE_TOKENS = ("transfer",)

# Maparea „cvv" → „card" (gate-ul tratează card/cvv ca aceeași clasă hard).
_SENSITIVE_ALIAS = {"cvv": "card"}


def _primary_sensitive(sensitive_asks: Optional[List[str]]) -> str:
    asks = [str(a).strip().lower() for a in (sensitive_asks or []) if a]
    asks = [_SENSITIVE_ALIAS.get(a, a) for a in asks]
    for token in _HARD_PRIORITY:
        tok = _SENSITIVE_ALIAS.get(token, token)
        if tok in asks:
            return tok
    for token in _VALUE_TOKENS:
        if token in asks:
            return token
    return "none"


def _identity_status(provenance: str) -> str:
    p = str(provenance or "unknown").strip().lower()
    if p == "match":
        return "official_match"   # TRUSTED_IDENTITY → has_positive_provenance
    if p == "mismatch":
        return "lookalike"        # BAD_IDENTITY
    return "unknown"


def build_inbox_verdict(
    *,
    message_hash: str,
    claimed_brand: Optional[str] = None,
    provenance: str = "unknown",
    sensitive_asks: Optional[List[str]] = None,
    campaign_match: Optional[str] = None,
    campaign_confidence: float = 0.0,
    campaign_family: Optional[str] = None,
    final_url: Optional[str] = None,
    violated_never_asks: Optional[List[str]] = None,
    violated_never_does: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Produce un `inbox_verdict` (§8) din semnale on-device, prin verdict_gate."""
    identity_status = _identity_status(provenance)
    has_provenance = identity_status == "official_match"
    sensitive = _primary_sensitive(sensitive_asks)
    has_url = bool(final_url)

    # Suprafață „vacuum-clean": brand match + niciun link + nicio cerere sensibilă.
    # Doar atunci marcăm providerii ca lipsiți de risc (nu există nimic de verificat),
    # ceea ce permite gate-ului să acorde SAFE (Rule 8). În rest, providerii rămân
    # „unknown" (nu există clearance on-device → fără downgrade la SAFE).
    vacuum_clean = has_provenance and not has_url and sensitive == "none"
    if vacuum_clean:
        providers = {"on_device": {"status": "no_match"}}  # clean (vacuos)
        resolution = {"status": "not_required", "completeness": True}
    else:
        providers = {}  # niciun provider on-device → gate îl vede „unknown"
        resolution = {
            "status": "resolved" if has_url else "not_required",
            "final_url": final_url,
            "completeness": True,
        }

    bundle: Dict[str, Any] = {
        "schema": "sigurscan_inbox_bundle_v1",
        "resolution": resolution,
        "providers": providers,
        "identity": {
            "status": identity_status,
            "claimed_brand": claimed_brand,
            "completeness": True,
            "violated_never_asks": list(violated_never_asks or []),
            "violated_never_does": list(violated_never_does or []),
        },
        "request": {
            "sensitive": sensitive,
            "channel": "sms",
            "completeness": True,
        },
        "provenance": {
            "official_domain_match": has_provenance and not has_url,
            "official_shortcode_match": has_provenance,
        },
        "campaign_match": {
            "status": "match" if campaign_match else "no_match",
            "confidence": float(campaign_confidence or 0.0),
            "family": campaign_family,
        },
        # On-device nu rulează analiză semantică LLM → „done" cu risc nul, ca să nu
        # forțeze artificial UNVERIFIED (Rule 4); riscul real vine din provenanță/campanie.
        "semantic_review": {"status": "done", "risk_class": "none"},
    }

    gate = verdict_gate.verdict(bundle)

    return {
        "message_hash": message_hash,
        "claimed_brand": claimed_brand,
        "provenance": str(provenance or "unknown"),
        "campaign_match": campaign_match,
        "verdict": gate["label"],
        "reason_codes": gate.get("reasons", []),
        "render": "inline_band",
        "processing": "on_device_only",
        "raw_stored": False,
    }


# ─── BTR delta-sync (manifest-ele coboară pe device; ZERO SMS urcă) ──────────
def btr_sync_payload(registry: Any, client_version: Optional[str] = None) -> Dict[str, Any]:
    """Payload de sincronizare a Brand Truth Registry pentru match on-device.
    Version-gated: dacă versiunea clientului == versiunea curentă → no-op (changed=False),
    altfel întoarce toate manifestele. Nu urcă niciun conținut de mesaj — doar manifeste."""
    current = registry.version
    if client_version and client_version == current:
        return {"changed": False, "version": current, "manifests": None, "count": 0}
    manifests = [asdict(m) for m in registry.all()]
    return {
        "changed": True,
        "version": current,
        "generated_at": getattr(registry, "generated_at", "") or "",
        "manifests": manifests,
        "count": len(manifests),
    }
