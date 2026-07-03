import os
import sys
import bz2
import requests


sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services import url_reputation


def test_phishtank_download_falls_back_to_compressed_feed_when_csv_fails(monkeypatch):
    csv_text = (
        "phish_id,url,phish_detail_url,submission_time,verified,verification_time,online,target\n"
        "1001,https://reported-phish.example/login,https://phishtank.org/phish_detail.php?phish_id=1001,"
        "2026-06-21T10:00:00+00:00,yes,2026-06-21T10:05:00+00:00,yes,Example Bank\n"
    )
    plain_url = "https://feed.example/online-valid.csv"
    bz2_url = "https://feed.example/online-valid.csv.bz2"
    gz_url = "https://feed.example/online-valid.csv.gz"
    calls = []

    class FakeResponse:
        def __init__(self, content: bytes = b"", error: Exception | None = None):
            self.content = content
            self._error = error

        def raise_for_status(self):
            if self._error:
                raise self._error

    def fake_get(url, **kwargs):
        calls.append(url)
        if url == plain_url:
            return FakeResponse(error=requests.HTTPError("404 Not Found"))
        if url == bz2_url:
            return FakeResponse(content=bz2.compress(csv_text.encode("utf-8")))
        if url == gz_url:
            raise AssertionError("gzip fallback should not be needed after bz2 succeeds")
        raise AssertionError(f"unexpected URL: {url}")

    monkeypatch.setattr(url_reputation, "PHISHTANK_ONLINE_VALID_URL", plain_url)
    monkeypatch.setattr(url_reputation, "PHISHTANK_ONLINE_VALID_BZ2_URL", bz2_url)
    monkeypatch.setattr(url_reputation, "PHISHTANK_ONLINE_VALID_GZ_URL", gz_url)
    monkeypatch.setattr(url_reputation.requests, "get", fake_get)

    assert url_reputation._download_phishtank_feed() == csv_text
    assert calls == [plain_url, bz2_url]


def test_phishtank_online_valid_feed_marks_exact_verified_online_url_malicious(monkeypatch):
    url = "https://reported-phish.example/login"
    key = url_reputation._url_hash(url)

    csv_text = (
        "phish_id,url,phish_detail_url,submission_time,verified,verification_time,online,target\n"
        f"1001,{url},https://phishtank.org/phish_detail.php?phish_id=1001,"
        "2026-06-21T10:00:00+00:00,yes,2026-06-21T10:05:00+00:00,yes,Example Bank\n"
        "1002,https://offline-phish.example/login,https://phishtank.org/phish_detail.php?phish_id=1002,"
        "2026-06-21T11:00:00+00:00,yes,2026-06-21T11:05:00+00:00,no,Example Bank\n"
    )

    monkeypatch.setattr(url_reputation, "ENABLE_PHISHTANK", True)
    monkeypatch.setattr(url_reputation, "_PHISHTANK_CACHE", {"loaded_at": 0, "links": set(), "metadata": {}, "error": None})
    monkeypatch.setattr(url_reputation, "_download_phishtank_feed", lambda: csv_text)

    result = url_reputation._fetch_phishtank_online_valid([url])

    assert result[key]["status"] == "malicious"
    assert result[key]["threat_type"] == "phishing"
    assert result[key]["score"] >= 90
    assert result[key]["details"]["provider"] == "phishtank_online_valid"
    assert result[key]["details"]["match_type"] == "url"
    assert result[key]["details"]["target"] == "Example Bank"


def test_reputation_uses_phishtank_as_active_provider(monkeypatch, tmp_path):
    cache_path = tmp_path / "url_reputation_cache.json"
    url = "https://reported-phish.example/login"
    key = url_reputation._url_hash(url)

    monkeypatch.setattr(url_reputation, "ENABLE_URL_REPUTATION", True)
    monkeypatch.setattr(url_reputation, "ENABLE_PHISHTANK", True)
    monkeypatch.setattr(url_reputation, "REPUTATION_CACHE_PATH", cache_path)
    monkeypatch.setattr(url_reputation, "_load_cache", lambda path: {})
    monkeypatch.setattr(url_reputation, "_save_cache", lambda path, data, remote_subset=None: None)
    monkeypatch.setattr(url_reputation, "has_web_risk_key", lambda: True)
    monkeypatch.setattr(url_reputation, "check_urls_against_web_risk", lambda urls: {})
    monkeypatch.setattr(
        url_reputation,
        "_fetch_asf_investor_alerts",
        lambda urls: {
            key: {"status": "clean", "threat_type": "unknown", "score": 0, "details": {"status": "not_listed"}}
        },
    )
    monkeypatch.setattr(
        url_reputation,
        "_fetch_phishing_database",
        lambda urls: {
            key: {"status": "clean", "threat_type": "unknown", "score": 0, "details": {"status": "not_listed"}}
        },
    )
    monkeypatch.setattr(
        url_reputation,
        "_fetch_phishtank_online_valid",
        lambda urls: {
            key: {
                "status": "malicious",
                "threat_type": "phishing",
                "score": 95,
                "details": {"provider": "phishtank_online_valid", "match_type": "url"},
            }
        },
    )
    monkeypatch.setattr(
        url_reputation,
        "_fetch_urlhaus",
        lambda urls, auth_key=None: {
            key: {"status": "clean", "threat_type": "unknown", "score": 0, "details": {"status": "not_listed"}}
        },
    )

    result = url_reputation.get_reputation_for_urls([url])

    assert result[key]["sources"]["phishtank_online_valid"]["consulted"] is True
    assert result[key]["sources"]["phishtank_online_valid"]["status"] == "malicious"
    assert "phishtank_online_valid" in result[key]["active_sources"]
    assert result[key]["verdict"] == "malicious"


def test_reputation_does_not_turn_web_risk_budget_exhaustion_into_clean_consulted(monkeypatch, tmp_path):
    cache_path = tmp_path / "url_reputation_cache.json"
    url = "https://budget-exhausted.example/login"
    key = url_reputation._url_hash(url)

    monkeypatch.setattr(url_reputation, "ENABLE_URL_REPUTATION", True)
    monkeypatch.setattr(url_reputation, "ENABLE_PHISHTANK", False)
    monkeypatch.setattr(url_reputation, "ENABLE_OPENPHISH", False)
    monkeypatch.setattr(url_reputation, "ENABLE_PHISHING_DATABASE", False)
    monkeypatch.setattr(url_reputation, "REPUTATION_CACHE_PATH", cache_path)
    monkeypatch.setattr(url_reputation, "_load_cache", lambda path: {})
    monkeypatch.setattr(url_reputation, "_save_cache", lambda path, data, remote_subset=None: None)
    monkeypatch.setattr(url_reputation, "has_web_risk_key", lambda: True)
    monkeypatch.setattr(
        url_reputation,
        "check_urls_against_web_risk",
        lambda urls: {
            key: {
                "status": "error",
                "consulted": False,
                "threat_type": "budget_exhausted",
                "score": 0,
                "error": "budget_exhausted",
                "details": {"provider": "google_web_risk", "status": "budget_exhausted"},
            }
        },
    )

    result = url_reputation.get_reputation_for_urls(
        [url],
        include_asf_investor_alerts=False,
        include_phishing_database=False,
        include_phishtank=False,
        include_openphish=False,
        include_urlhaus=False,
        include_scam_blocklist_nrd=False,
        include_phishdestroy=False,
    )

    web_risk = result[key]["sources"]["google_web_risk"]
    assert web_risk["status"] == "error"
    assert web_risk["consulted"] is False
    assert web_risk["error"] == "budget_exhausted"
    assert web_risk["details"]["status"] == "budget_exhausted"
    assert result[key]["verdict"] == "unknown"


def test_urlhaus_recent_feed_is_used_without_auth_key(monkeypatch):
    url = "https://malware.example/path/dropper"
    key = url_reputation._url_hash(url)
    csv_text = (
        "# id,dateadded,url,url_status,last_online,threat,tags,urlhaus_link,reporter\n"
        f"1,2026-06-21 08:00:00,{url},online,2026-06-21 08:05:00,phishing,phish,"
        "https://urlhaus.abuse.ch/url/1/,researcher\n"
    )

    monkeypatch.setattr(url_reputation, "URLHAUS_AUTH_KEY", "")
    monkeypatch.setattr(url_reputation, "_urlhaus_auth_key", lambda: "")
    monkeypatch.setattr(url_reputation, "_URLHAUS_RECENT_CACHE", {"loaded_at": 0, "links": set(), "metadata": {}, "error": None})
    monkeypatch.setattr(url_reputation, "_download_urlhaus_recent_feed", lambda: csv_text)

    result = url_reputation._fetch_urlhaus([url], auth_key="")

    assert result[key]["status"] == "malicious"
    assert result[key]["threat_type"] == "phishing"
    assert result[key]["details"]["provider"] == "urlhaus"
    assert result[key]["details"]["match_type"] == "recent_feed_url"


def test_openphish_feed_marks_active_url_malicious(monkeypatch):
    url = "https://active-phish.example/login"
    key = url_reputation._url_hash(url)
    feed_text = f"{url}\nhttps://other-phish.example/login\n"

    monkeypatch.setattr(url_reputation, "_OPENPHISH_CACHE", {"loaded_at": 0, "links": set(), "error": None})
    monkeypatch.setattr(url_reputation, "_download_openphish_feed", lambda: feed_text)

    result = url_reputation._fetch_openphish([url])

    assert result[key]["status"] == "malicious"
    assert result[key]["threat_type"] == "phishing"
    assert result[key]["details"]["provider"] == "openphish"
    assert result[key]["details"]["match_type"] == "url"


def test_openphish_hash_match_marks_privacy_collapsed_url_malicious(monkeypatch, tmp_path):
    raw_url = "https://active-phish.example/reset/ana.popescu%40gmail.com/token"
    safe_url = "https://active-phish.example/"
    safe_key = url_reputation._url_hash(safe_url)
    feed_text = f"{raw_url}\n"
    saved_cache = []

    monkeypatch.setattr(url_reputation, "ENABLE_URL_REPUTATION", True)
    monkeypatch.setattr(url_reputation, "ENABLE_OPENPHISH", True)
    monkeypatch.setattr(url_reputation, "REPUTATION_CACHE_PATH", tmp_path / "url_reputation_cache.json")
    monkeypatch.setattr(url_reputation, "_load_cache", lambda path: {})
    monkeypatch.setattr(url_reputation, "_save_cache", lambda path, data, remote_subset=None: saved_cache.append(dict(data)))
    monkeypatch.setattr(url_reputation, "has_web_risk_key", lambda: False)
    monkeypatch.setattr(url_reputation, "_OPENPHISH_CACHE", {"loaded_at": 0, "links": set(), "link_hashes": set(), "error": None})
    monkeypatch.setattr(url_reputation, "_download_openphish_feed", lambda: feed_text)

    result = url_reputation.get_reputation_for_urls(
        [safe_url],
        include_asf_investor_alerts=False,
        include_phishing_database=False,
        include_phishtank=False,
        include_openphish=True,
        include_urlhaus=False,
        lookup_url_hashes_by_url={safe_url: url_reputation.reputation_url_hash_variants(raw_url)},
    )

    serialized = str(result)
    assert result[safe_key]["verdict"] == "malicious"
    assert result[safe_key]["sources"]["openphish"]["status"] == "malicious"
    assert result[safe_key]["sources"]["openphish"]["details"]["match_type"] == "url_hash"
    assert "matched_value_hash" in result[safe_key]["sources"]["openphish"]["details"]
    assert raw_url not in serialized
    assert "ana.popescu" not in serialized
    assert saved_cache == []


def test_phishtank_hash_match_marks_privacy_collapsed_url_malicious(monkeypatch, tmp_path):
    raw_url = "https://reported-phish.example/reset/ana.popescu%40gmail.com/token"
    safe_url = "https://reported-phish.example/"
    safe_key = url_reputation._url_hash(safe_url)
    csv_text = (
        "phish_id,url,phish_detail_url,submission_time,verified,verification_time,online,target\n"
        f"1001,{raw_url},https://phishtank.org/phish_detail.php?phish_id=1001,"
        "2026-06-21T10:00:00+00:00,yes,2026-06-21T10:05:00+00:00,yes,Example Bank\n"
    )
    saved_cache = []

    monkeypatch.setattr(url_reputation, "ENABLE_URL_REPUTATION", True)
    monkeypatch.setattr(url_reputation, "ENABLE_PHISHTANK", True)
    monkeypatch.setattr(url_reputation, "REPUTATION_CACHE_PATH", tmp_path / "url_reputation_cache.json")
    monkeypatch.setattr(url_reputation, "_load_cache", lambda path: {})
    monkeypatch.setattr(url_reputation, "_save_cache", lambda path, data, remote_subset=None: saved_cache.append(dict(data)))
    monkeypatch.setattr(url_reputation, "has_web_risk_key", lambda: False)
    monkeypatch.setattr(url_reputation, "_PHISHTANK_CACHE", {"loaded_at": 0, "links": set(), "link_hashes": set(), "metadata": {}, "metadata_by_hash": {}, "error": None})
    monkeypatch.setattr(url_reputation, "_download_phishtank_feed", lambda: csv_text)

    result = url_reputation.get_reputation_for_urls(
        [safe_url],
        include_asf_investor_alerts=False,
        include_phishing_database=False,
        include_phishtank=True,
        include_openphish=False,
        include_urlhaus=False,
        lookup_url_hashes_by_url={safe_url: url_reputation.reputation_url_hash_variants(raw_url)},
    )

    serialized = str(result)
    assert result[safe_key]["verdict"] == "malicious"
    assert result[safe_key]["sources"]["phishtank_online_valid"]["status"] == "malicious"
    assert result[safe_key]["sources"]["phishtank_online_valid"]["details"]["match_type"] == "url_hash"
    assert result[safe_key]["sources"]["phishtank_online_valid"]["details"]["target"] == "Example Bank"
    assert raw_url not in serialized
    assert "ana.popescu" not in serialized
    assert saved_cache == []
