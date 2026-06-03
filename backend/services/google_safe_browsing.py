import hashlib
import os
from typing import Dict, List

import requests

SAFE_BROWSING_API_URL = "https://safebrowsing.googleapis.com/v4/threatMatches:find"


def has_safe_browsing_key() -> bool:
    return bool(os.getenv("GOOGLE_SAFE_BROWSING_API_KEY"))


def check_urls_against_safe_browsing(urls: List[str]) -> Dict[str, Dict[str, str]]:
    """
    Checks up to 500 URLs against Google Safe Browsing API.
    Returns a dict keyed by SHA-256(url):
    {"<sha256>": {"url": str, "threat_type": str, "platform": str, "cache_duration": str}}
    """
    if not has_safe_browsing_key() or not urls:
        return {}

    unique_urls = list(dict.fromkeys(urls))[:500]
    if not unique_urls:
        return {}

    api_key = os.getenv("GOOGLE_SAFE_BROWSING_API_KEY")
    if not api_key:
        return {}

    payload = {
        "client": {
            "clientId": "sigurscan",
            "clientVersion": "1.0",
        },
        "threatInfo": {
            "threatTypes": [
                "MALWARE",
                "SOCIAL_ENGINEERING",
                "UNWANTED_SOFTWARE",
                "POTENTIALLY_HARMFUL_APPLICATION",
            ],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url} for url in unique_urls],
        },
    }

    endpoint = f"{SAFE_BROWSING_API_URL}?key={api_key}"

    try:
        response = requests.post(endpoint, json=payload, timeout=4.0)
        if response.status_code != 200:
            return {}

        data = response.json()
    except (requests.RequestException, ValueError):
        return {}

    matches = data.get("matches", []) if isinstance(data, dict) else []
    if not isinstance(matches, list):
        return {}

    results: Dict[str, Dict[str, str]] = {}
    for match in matches:
        threat = match.get("threat") if isinstance(match, dict) else None
        if not isinstance(threat, dict):
            continue

        match_url = threat.get("url", "")
        if not match_url:
            continue

        key = hashlib.sha256(match_url.encode("utf-8")).hexdigest()
        results[key] = {
            "url": match_url,
            "threat_type": str(match.get("threatType", "UNKNOWN")),
            "platform": str(match.get("platformType", "UNKNOWN")),
            "cache_duration": str(match.get("cacheDuration", "")),
        }

    return results
