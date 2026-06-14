"""Pilon — Registru NEGATIV de IBAN-uri (catâri/complici raportați).

Răspunsul determinist la „firmă reală + IBAN al unui complice": whitelist-ul nu
te ajută (firma nu pretinde un brand), dar dacă IBAN-ul a mai lovit pe altcineva,
îl prinzi la prima scanare a VICTIMEI #2. Alimentat din alerte DNSC + rapoarte
comunitare (Radar `/v1/report`). E un PILON de semnal — verdictul îl dă verdict_gate.

Privacy: în producție IBAN-urile pot fi stocate hash-uite (HMAC). Aici comparăm pe
forma normalizată; feed-ul decide formatul. Seed-ul pornește gol (zero fals-pozitive).
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import List, Set

from services.iban_validator import normalize_iban, validate_iban

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_PATH = os.path.join(_BACKEND_DIR, "data", "negative_iban_registry_v1.json")


def _path() -> str:
    return os.getenv("NEGATIVE_IBAN_REGISTRY_PATH") or _DEFAULT_PATH


# Set in-memory de IBAN-uri raportate la runtime (din ingest moderator/DNSC sau
# rapoarte comunitare). Persistă best-effort în Supabase; rămâne valid și fără el.
_runtime_reported: Set[str] = set()


@lru_cache(maxsize=1)
def _seed_registry() -> Set[str]:
    """IBAN-uri din seed-ul JSON (DNSC), normalizate. Lipsă/corupt → gol."""
    path = _path()
    if not os.path.isfile(path):
        return set()
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return set()
    out: Set[str] = set()
    for raw in (data.get("reported_ibans") or []):
        norm = normalize_iban(str(raw))
        if norm:
            out.add(norm)
    return out


def reload_registry() -> None:
    """Reîncarcă seed-ul + golește runtime-ul (după update de feed sau în teste)."""
    _seed_registry.cache_clear()
    _runtime_reported.clear()


def is_reported_fraud(iban: str) -> bool:
    norm = normalize_iban(iban or "")
    return bool(norm) and (norm in _seed_registry() or norm in _runtime_reported)


def report_fraud_iban(iban: str, *, source: str = "manual", family: Optional[str] = None) -> bool:
    """Raportează un IBAN ca fraudă (ingest moderator/DNSC/comunitate). Adaugă în
    memorie + persistă best-effort în Supabase (no-op fără chei). Întoarce True dacă
    IBAN-ul e valid și a fost adăugat."""
    norm = normalize_iban(iban or "")
    if not norm or not validate_iban(iban).valid_structure:
        return False
    _runtime_reported.add(norm)
    try:
        from services import supabase_store
        supabase_store.save_negative_iban(norm, source=source, family=family)
    except Exception:
        pass
    return True


def load_supabase_reports() -> int:
    """Încarcă best-effort IBAN-urile raportate din Supabase în memoria runtime.
    Întoarce câte au fost adăugate (0 fără Supabase). De apelat la pornire/refresh."""
    try:
        from services import supabase_store
        ibans = supabase_store.load_negative_ibans()
    except Exception:
        return 0
    added = 0
    for raw in ibans or []:
        norm = normalize_iban(str(raw))
        if norm and norm not in _runtime_reported:
            _runtime_reported.add(norm)
            added += 1
    return added


def reported_fraud_ibans(ibans: List[str]) -> List[str]:
    """Subsetul de IBAN-uri din listă care apar în registrul negativ (seed ∪ runtime)."""
    seen: Set[str] = set()
    out: List[str] = []
    for raw in ibans or []:
        norm = normalize_iban(raw or "")
        if norm and norm not in seen and is_reported_fraud(norm):
            seen.add(norm)
            out.append(norm)
    return out
