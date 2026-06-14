"""Pilon DNS reputation — gratis, fără cheie, Play-safe.

Două întrebări, prin DNS-over-HTTPS către resolvere publice (NU vizitează site-ul):
1. Rezolvă domeniul pe un DNS normal, dar e BLOCAT de un DNS de securitate
   (Cloudflare 1.1.1.2 / Quad9)? → bloc autoritar de malware/phishing → terminal.
2. E pe nameservere de suspendare (ex. Tucows trs-dns.com) sau nu rezolvă nicăieri
   (NXDOMAIN)? → semnal de abuz/takedown, ponderat (medium), niciodată terminal solo.

Clasificatorul (`classify_dns`) e PUR și testabil offline; wrapper-ul de rețea
(`check_dns_reputation`) primește un `doh_get` injectabil. Mapping-ul respectă
filozofia codebase-ului: semnal hard = status „malicious" (prins de mecanismul
existent de provideri); semnal ponderat = status „suspicious" + severity „medium".
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple
from urllib.parse import urlparse

# Resolvere publice (DoH JSON). Cel „security" blochează domenii malware/phishing.
_NORMAL_RESOLVER = "https://cloudflare-dns.com/dns-query"
_SECURITY_RESOLVER = "https://security.cloudflare-dns.com/dns-query"

# IP-uri „sentinelă" cu care unele resolvere de securitate semnalează un bloc.
_BLOCK_SENTINEL_IPS = {"0.0.0.0", "::"}

# Markere de nameservere de suspendare la registrar (domeniu pe „hold" de abuz).
_SUSPENSION_NS_MARKERS = ("trs-dns", "suspended-domain", "suspension", "suspendedfor")

# rcode DNS: 0 = NOERROR, 3 = NXDOMAIN.
_NXDOMAIN = 3
_NOERROR = 0


@dataclass
class DnsReputation:
    status: str           # blocked | suspended | nxdomain | resolves | unknown
    reason_codes: List[str]
    severity: str         # high | medium | low


def classify_dns(
    *,
    normal_status: int,
    normal_ips: List[str],
    security_status: int,
    security_ips: List[str],
    ns_hosts: List[str],
) -> DnsReputation:
    """Pur: clasifică pe baza răspunsurilor DNS deja obținute."""
    ns_blob = " ".join(str(h).lower() for h in (ns_hosts or []))
    suspended = any(marker in ns_blob for marker in _SUSPENSION_NS_MARKERS)

    normal_resolves = normal_status == _NOERROR and bool(normal_ips)
    security_blocks = (
        security_status == _NXDOMAIN
        or (security_status == _NOERROR and not security_ips)
        or any(ip in _BLOCK_SENTINEL_IPS for ip in (security_ips or []))
    )

    # 1) Bloc autoritar: rezolvă normal, dar DNS-ul de securitate îl refuză.
    if normal_resolves and security_blocks:
        return DnsReputation("blocked", ["security_dns_blocked"], "high")
    # 2) Suspendare la registrar (NS de hold) — semnal de abuz, ponderat.
    if suspended:
        return DnsReputation("suspended", ["registrar_suspension_ns"], "medium")
    # 3) Nu rezolvă deloc — posibil luat jos, ponderat.
    if normal_status == _NXDOMAIN:
        return DnsReputation("nxdomain", ["domain_nxdomain"], "medium")
    # 4) Rezolvă curat.
    if normal_resolves:
        return DnsReputation("resolves", [], "low")
    return DnsReputation("unknown", [], "low")


def dns_summary_entry(rep: DnsReputation) -> Optional[dict]:
    """Doar semnalul HARD (`blocked`) intră ca provider autoritar (status malicious),
    ca să fie tratat terminal prin mecanismul existent. Restul → None aici."""
    if rep.status == "blocked":
        return {
            "status": "malicious",
            "verdict": "security_dns_blocked",
            "severity": "high",
            "consulted": True,
            "details": "Domeniul rezolvă pe DNS normal dar e blocat de DNS-ul de securitate (malware/phishing).",
        }
    return None


def dns_infra_entry(rep: DnsReputation) -> Optional[dict]:
    """Semnalele ponderate (`suspended`/`nxdomain`) → status suspicious, severity
    medium (niciodată terminal solo, ca infra_rdap)."""
    if rep.status == "suspended":
        return {
            "status": "suspicious", "verdict": "registrar_suspended", "severity": "medium",
            "consulted": True,
            "details": "Domeniul e pe nameservere de suspendare la registrar (semnal de abuz).",
        }
    if rep.status == "nxdomain":
        return {
            "status": "suspicious", "verdict": "nxdomain", "severity": "medium",
            "consulted": True,
            "details": "Domeniul nu rezolvă (NXDOMAIN) — posibil luat jos; semnal ponderat.",
        }
    return None


def domain_from_url(url: str) -> str:
    """Extrage hostul dintr-un URL (sau acceptă direct un domeniu)."""
    raw = str(url or "").strip()
    if not raw:
        return ""
    if "://" not in raw:
        raw = "http://" + raw
    host = (urlparse(raw).hostname or "").strip().lower()
    return host


def _default_doh_get(resolver: str, name: str, qtype: str, timeout: float) -> Tuple[int, List[str]]:
    import requests  # import local: pilonul rămâne importabil fără rețea

    r = requests.get(
        resolver, params={"name": name, "type": qtype},
        headers={"accept": "application/dns-json"}, timeout=timeout,
    )
    data = r.json()
    status = int(data.get("Status", 2))
    want = 1 if qtype == "A" else (2 if qtype == "NS" else None)
    records = [
        str(a.get("data", "")).rstrip(".")
        for a in data.get("Answer", []) + data.get("Authority", [])
        if want is None or a.get("type") == want or qtype == "NS"
    ]
    return status, [rec for rec in records if rec]


DohGet = Callable[[str, str, str, float], Tuple[int, List[str]]]


def check_dns_reputation(
    domain: str,
    *,
    doh_get: DohGet = _default_doh_get,
    timeout: float = 3.0,
) -> DnsReputation:
    """Wrapper de rețea (best-effort). `doh_get` injectabil pentru teste/offline."""
    host = domain_from_url(domain)
    if not host:
        return DnsReputation("unknown", [], "low")
    normal_status, normal_ips = doh_get(_NORMAL_RESOLVER, host, "A", timeout)
    security_status, security_ips = doh_get(_SECURITY_RESOLVER, host, "A", timeout)
    _, ns_hosts = doh_get(_NORMAL_RESOLVER, host, "NS", timeout)
    return classify_dns(
        normal_status=normal_status, normal_ips=normal_ips,
        security_status=security_status, security_ips=security_ips,
        ns_hosts=ns_hosts,
    )
