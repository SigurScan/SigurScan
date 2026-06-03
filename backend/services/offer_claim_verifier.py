"""Offer/claim verification provider.

This is evidence, not a verdict engine. It checks whether the concrete offer or
action claimed by a user-provided message appears on official/reputable web
sources, then returns a bounded provider payload for the gate/corpus layer.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.parse
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

try:
    import certifi
except Exception:  # pragma: no cover - optional dependency
    certifi = None

try:
    from google import genai
    from google.genai import types

    SDK_AVAILABLE = True
except Exception:  # pragma: no cover - exercised by fallback tests/envs
    SDK_AVAILABLE = False


ENABLE_OFFER_CLAIM_WEB_CHECK = os.getenv("ENABLE_OFFER_CLAIM_WEB_CHECK", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
OFFER_CLAIM_HTTP_TIMEOUT_SECONDS = float(os.getenv("OFFER_CLAIM_HTTP_TIMEOUT_SECONDS", "3.0"))
MAX_OFFER_CLAIM_OFFICIAL_PAGES = int(os.getenv("MAX_OFFER_CLAIM_OFFICIAL_PAGES", "4"))

STOPWORDS = {
    "acum",
    "acest",
    "aceasta",
    "aceste",
    "afla",
    "are",
    "bani",
    "care",
    "cateva",
    "cont",
    "din",
    "dvs",
    "este",
    "fara",
    "folosesti",
    "gratuit",
    "intra",
    "link",
    "mail",
    "mesaj",
    "minute",
    "pentru",
    "prin",
    "rapid",
    "sau",
    "sigur",
    "text",
    "transport",
    "userul",
    "valoare",
}


def verify_offer_claim(
    text: str,
    analysis: Dict[str, Any],
    resolved_urls: List[Dict[str, Any]],
    *,
    brand_registry: Dict[str, List[str]],
) -> Dict[str, Any]:
    if not ENABLE_OFFER_CLAIM_WEB_CHECK:
        return _payload("skipped", "unknown", "AI offer web check disabled.", confidence=0)

    claimed_brand = _claimed_brand(text, analysis, brand_registry)
    final_urls = _final_urls(resolved_urls)
    official_domains = _official_domains_for_claim(claimed_brand, final_urls, brand_registry)
    query = _build_claim_query(text, claimed_brand)

    if not query and not final_urls:
        return _payload("skipped", "unknown", "No concrete claim or URL to verify.", confidence=0)

    gemini_result = _verify_with_gemini_search(
        text=text,
        claimed_brand=claimed_brand,
        official_domains=official_domains,
        final_urls=final_urls,
        query=query,
    )
    if (
        gemini_result is not None
        and gemini_result.get("status") in {"confirmed", "not_found"}
        and gemini_result.get("method") != "gemini_google_search_error"
    ):
        return gemini_result

    official_result = _verify_with_official_pages(
        text=text,
        claimed_brand=claimed_brand,
        official_domains=official_domains,
        final_urls=final_urls,
        query=query,
    )

    if official_result.get("status") == "confirmed":
        return official_result

    if gemini_result is None:
        return official_result

    if gemini_result.get("status") == "inconclusive":
        return official_result

    return gemini_result


def _verify_with_gemini_search(
    *,
    text: str,
    claimed_brand: Optional[str],
    official_domains: List[str],
    final_urls: List[str],
    query: str,
) -> Optional[Dict[str, Any]]:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or not SDK_AVAILABLE:
        return None

    prompt = f"""
Verifici o afirmație/o ofertă dintr-un mesaj primit de un utilizator român.
Folosește web search. Prioritizează surse oficiale ale brandului/instituției.
Nu decide verdictul de scam. Returnează doar dovezi pentru gate.

Text primit:
{text[:4000]}

Brand pretins: {claimed_brand or "necunoscut"}
Domenii oficiale așteptate: {", ".join(official_domains) or "necunoscut"}
URL-uri finale extrase: {", ".join(final_urls) or "nu există"}
Query propus: {query or "necunoscut"}

Răspunde strict JSON:
{{
  "status": "confirmed | not_found | inconclusive",
  "summary": "o propoziție scurtă în română",
  "evidence_urls": ["https://..."],
  "official_source_found": true,
  "confidence": 0
}}
Reguli:
- confirmed doar dacă găsești oferta/acțiunea pe domeniu oficial sau sursă reputabilă.
- not_found dacă ai căutat și nu găsești nimic oficial/reputabil.
- inconclusive dacă sursele sunt insuficiente, blocate, ambigue sau query-ul nu este concret.
"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=os.getenv("OFFER_CLAIM_GEMINI_MODEL", "gemini-2.5-flash"),
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
            ),
        )
        raw = _extract_json_text(response.text or "")
        data = json.loads(raw)
        status = _normalize_status(data.get("status"))
        evidence_urls = _clean_urls(data.get("evidence_urls") or [])
        confidence = _clamp_int(data.get("confidence"), 0, 100)
        summary = str(data.get("summary") or "").strip()[:500]
        return _payload(
            status,
            _severity_for_status(status),
            summary or _default_summary(status),
            confidence=confidence,
            claimed_brand=claimed_brand,
            official_domains=official_domains,
            query=query,
            evidence_urls=evidence_urls,
            method="gemini_google_search",
            official_source_found=bool(data.get("official_source_found")),
        )
    except Exception as exc:
        if "SSL" in str(exc) or "certificate" in str(exc).lower():
            return _payload(
                "inconclusive",
                "unknown",
                f"AI web search certificate issue: {type(exc).__name__}.",
                confidence=0,
                claimed_brand=claimed_brand,
                official_domains=official_domains,
                query=query,
                evidence_urls=[],
                method="gemini_google_search_error",
            )
        return _payload(
            "inconclusive",
            "unknown",
            "AI web search temporarily unavailable.",
            confidence=0,
            claimed_brand=claimed_brand,
            official_domains=official_domains,
            query=query,
            evidence_urls=[],
            method="gemini_google_search_error",
        )


def _extract_json_text(value: str) -> str:
    raw = value.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?", "", raw, flags=re.IGNORECASE).strip()
        raw = re.sub(r"```$", "", raw).strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        return raw[start : end + 1]
    return raw


def _verify_with_official_pages(
    *,
    text: str,
    claimed_brand: Optional[str],
    official_domains: List[str],
    final_urls: List[str],
    query: str,
) -> Dict[str, Any]:
    terms = _claim_terms(text, claimed_brand)
    candidate_urls = _official_candidate_urls(official_domains, final_urls)
    if not candidate_urls:
        return _payload(
            "inconclusive",
            "unknown",
            "No official domain was available for claim verification.",
            confidence=0,
            claimed_brand=claimed_brand,
            official_domains=official_domains,
            query=query,
            method="official_page_fetch",
        )

    checked: List[str] = []
    for url in candidate_urls[:MAX_OFFER_CLAIM_OFFICIAL_PAGES]:
        page_text = _fetch_page_text(url)
        checked.append(url)
        if not page_text:
            continue
        if _terms_match(page_text, terms):
            return _payload(
                "confirmed",
                "low",
                "Claim terms were found on an official destination/page.",
                confidence=70,
                claimed_brand=claimed_brand,
                official_domains=official_domains,
                query=query,
                evidence_urls=[url],
                method="official_page_fetch",
                official_source_found=True,
            )

    return _payload(
        "inconclusive",
        "unknown",
        "Official pages checked, but the exact offer/action was not confirmed.",
        confidence=25,
        claimed_brand=claimed_brand,
        official_domains=official_domains,
        query=query,
        evidence_urls=checked,
        method="official_page_fetch",
    )


def _payload(
    status: str,
    severity: str,
    summary: str,
    *,
    confidence: int,
    claimed_brand: Optional[str] = None,
    official_domains: Optional[List[str]] = None,
    query: str = "",
    evidence_urls: Optional[List[str]] = None,
    method: str = "none",
    official_source_found: bool = False,
) -> Dict[str, Any]:
    status = _normalize_status(status)
    return {
        "provider": "ai_offer_web_check",
        "status": status,
        "verdict": status,
        "severity": severity,
        "summary": summary,
        "details": summary,
        "confidence": int(confidence),
        "claimed_brand": claimed_brand or "Nespecificat",
        "official_domains": official_domains or [],
        "query": query,
        "evidence_urls": evidence_urls or [],
        "method": method,
        "official_source_found": bool(official_source_found),
        "checked_at": int(time.time()),
    }


def _claimed_brand(text: str, analysis: Dict[str, Any], brand_registry: Dict[str, List[str]]) -> Optional[str]:
    claimed = str(analysis.get("claimed_brand") or "").strip()
    if claimed and claimed.lower() not in {"nespecificat", "unknown", "none"}:
        return claimed
    lowered = (text or "").lower()
    for brand in brand_registry.keys():
        if brand.lower() in lowered:
            return brand
    return None


def _official_domains_for_claim(
    claimed_brand: Optional[str],
    final_urls: List[str],
    brand_registry: Dict[str, List[str]],
) -> List[str]:
    domains: List[str] = []
    if claimed_brand and claimed_brand in brand_registry:
        domains.extend(brand_registry[claimed_brand])
    for url in final_urls:
        host = urllib.parse.urlparse(url).hostname or ""
        if host:
            domains.append(host.lower().removeprefix("www."))
    return list(dict.fromkeys(domains))


def _final_urls(resolved_urls: List[Dict[str, Any]]) -> List[str]:
    urls: List[str] = []
    for entry in resolved_urls or []:
        final_url = entry.get("final_url") or entry.get("url") or entry.get("original_url")
        if isinstance(final_url, str) and final_url.strip():
            urls.append(final_url.strip())
    return list(dict.fromkeys(urls))


def _build_claim_query(text: str, claimed_brand: Optional[str]) -> str:
    terms = _claim_terms(text, claimed_brand)
    parts = [claimed_brand] if claimed_brand else []
    parts.extend(terms[:8])
    return " ".join(part for part in parts if part)


def _claim_terms(text: str, claimed_brand: Optional[str]) -> List[str]:
    normalized = re.sub(r"[^0-9A-Za-zĂÂÎȘȚăâîșț%-]+", " ", text or "").lower()
    raw_terms = [term for term in normalized.split() if len(term) >= 4]
    brand_tokens = set((claimed_brand or "").lower().split())
    terms: List[str] = []
    for term in raw_terms:
        if term in STOPWORDS or term in brand_tokens:
            continue
        if term not in terms:
            terms.append(term)
    priority = [
        term
        for term in terms
        if term in {"buyback", "buy", "back", "voucher", "reducere", "oferta", "cursa", "campanie", "black", "friday"}
            or term.isdigit()
    ]
    rest = [term for term in terms if term not in priority]
    return (priority + rest)[:12]


def _official_candidate_urls(official_domains: List[str], final_urls: List[str]) -> List[str]:
    urls: List[str] = []
    official_set = set(official_domains)
    for url in final_urls:
        host = (urllib.parse.urlparse(url).hostname or "").lower().removeprefix("www.")
        if any(host == domain or host.endswith(f".{domain}") for domain in official_set):
            urls.append(url)
    for domain in official_domains:
        urls.append(f"https://{domain}/")
    return list(dict.fromkeys(urls))


def _fetch_page_text(url: str) -> str:
    verify_settings = [True]
    if certifi is not None:
        verify_settings.append(certifi.where())

    try:
        for verify in verify_settings:
            try:
                response = requests.get(
                    url,
                    timeout=OFFER_CLAIM_HTTP_TIMEOUT_SECONDS,
                    headers={"User-Agent": "SigurScan claim verifier (+https://sigurscan.ro)"},
                    allow_redirects=True,
                    verify=verify,
                )
                if response.status_code >= 400:
                    continue
                soup = BeautifulSoup(response.text[:200_000], "html.parser")
                for tag in soup(["script", "style", "noscript"]):
                    tag.decompose()
                return soup.get_text(" ", strip=True).lower()
            except requests.exceptions.SSLError:
                continue
        return ""
    except Exception:
        return ""


def _terms_match(page_text: str, terms: List[str]) -> bool:
    if not terms:
        return False
    matches = sum(1 for term in terms[:8] if term in page_text)
    return matches >= max(1, min(2, len(terms[:8]) // 3))


def _clean_urls(values: List[Any]) -> List[str]:
    output: List[str] = []
    for value in values:
        raw = str(value or "").strip()
        if raw.startswith("http://") or raw.startswith("https://"):
            output.append(raw)
    return list(dict.fromkeys(output))[:6]


def _normalize_status(status: Any) -> str:
    normalized = str(status or "").strip().lower()
    if normalized in {"confirmed", "not_found", "inconclusive", "skipped"}:
        return normalized
    return "inconclusive"


def _severity_for_status(status: str) -> str:
    if status == "not_found":
        return "medium"
    if status == "confirmed":
        return "low"
    return "unknown"


def _default_summary(status: str) -> str:
    if status == "confirmed":
        return "The claim appears on an official/reputable source."
    if status == "not_found":
        return "No official/reputable source confirmed the claim."
    return "Claim verification was inconclusive."


def _clamp_int(value: Any, minimum: int, maximum: int) -> int:
    try:
        numeric = int(value)
    except Exception:
        numeric = 0
    return max(minimum, min(maximum, numeric))
