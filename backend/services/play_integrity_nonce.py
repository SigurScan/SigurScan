"""Distributed, single-use nonce store for Play Integrity."""

import hashlib
import os
import secrets
from typing import Any, Dict, List

import requests

UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL", "").strip().rstrip("/")
UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "").strip()
UPSTASH_TIMEOUT_SECONDS = float(os.getenv("UPSTASH_TIMEOUT_SECONDS", "1.5"))
PLAY_INTEGRITY_NONCE_TTL_SECONDS = int(os.getenv("PLAY_INTEGRITY_NONCE_TTL_SECONDS", "120"))


def is_configured() -> bool:
    return bool(UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN)


def backend_mode() -> str:
    return "upstash" if is_configured() else "unavailable"


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _client_binding(api_key: str) -> str:
    return _digest(api_key.strip())


def _nonce_key(nonce: str) -> str:
    return f"sigurscan:play-integrity:nonce:{_digest(nonce.strip())}"


def _run_upstash_command(command: List[str]) -> Dict[str, Any]:
    response = requests.post(
        UPSTASH_REDIS_REST_URL,
        json=command,
        headers={"Authorization": f"Bearer {UPSTASH_REDIS_REST_TOKEN}"},
        timeout=UPSTASH_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


def issue_nonce(api_key: str) -> Dict[str, Any]:
    if not api_key or not api_key.strip():
        return {"status": "invalid_client"}
    if not is_configured():
        return {"status": "store_unavailable"}

    for _ in range(3):
        nonce = secrets.token_urlsafe(32)
        try:
            reply = _run_upstash_command(
                [
                    "SET",
                    _nonce_key(nonce),
                    _client_binding(api_key),
                    "EX",
                    str(PLAY_INTEGRITY_NONCE_TTL_SECONDS),
                    "NX",
                ]
            )
        except Exception:
            return {"status": "store_unavailable"}
        if reply.get("result") == "OK":
            return {
                "status": "issued",
                "nonce": nonce,
                "expires_in_seconds": PLAY_INTEGRITY_NONCE_TTL_SECONDS,
            }
    return {"status": "collision"}


def consume_nonce(nonce: str, api_key: str) -> Dict[str, Any]:
    if not nonce or not nonce.strip() or not api_key or not api_key.strip():
        return {"status": "invalid_request"}
    if not is_configured():
        return {"status": "store_unavailable"}
    try:
        reply = _run_upstash_command(["GETDEL", _nonce_key(nonce)])
    except Exception:
        return {"status": "store_unavailable"}

    stored_binding = reply.get("result")
    if stored_binding is None:
        return {"status": "missing_or_replayed"}
    if stored_binding != _client_binding(api_key):
        return {"status": "client_mismatch"}
    return {"status": "consumed"}
