"""Static configuration and environment-derived settings for backend."""

import os
import re

URLSCAN_VISIBILITY_DEFAULT = os.getenv("URLSCAN_VISIBILITY_DEFAULT", "private").strip().lower() or "private"
URLSCAN_COUNTRY_DEFAULT = os.getenv("URLSCAN_COUNTRY_DEFAULT", "").strip().lower()
URLSCAN_CUSTOM_AGENT_DEFAULT = os.getenv("URLSCAN_CUSTOM_AGENT", "").strip()

EXPOSE_API_DOCS = os.getenv("EXPOSE_API_DOCS", "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_PDF_BYTES = 12 * 1024 * 1024
MAX_XML_BYTES = 2 * 1024 * 1024
MAX_TEXT_CHARS = int(os.getenv("MAX_TEXT_CHARS", "12000"))
MAX_URLS_PER_SCAN = int(os.getenv("MAX_URLS_PER_SCAN", "15"))
RISK_THRESHOLD = int(os.getenv("RISK_THRESHOLD", "50"))
PRIVACY_SAFE_MODE = (
    os.getenv("SIGURSCAN_SAFE_MODE")
    or os.getenv("NUDACLICK_SAFE_MODE")
    or "false"
).strip().lower() in {"1", "true", "yes", "on"}
ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_PDF_MIME_TYPES = {"application/pdf", "application/x-pdf"}
ALLOWED_PDF_EXTS = {".pdf"}
ALLOWED_XML_MIME_TYPES = {"application/xml", "text/xml", "application/octet-stream"}
ALLOWED_XML_EXTS = {".xml"}
ALLOWED_MOCK_OCR = os.getenv("ALLOW_MOCK_OCR", "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

# Plain-text URL extraction noise list:
# Some short Romanian tokens include a dot and can be wrongly matched as URLs by regex.
REQUIRE_API_KEY = os.getenv("REQUIRE_API_KEY", "false").strip().lower() in {"1", "true", "yes", "on"}
ALLOWED_API_KEYS = {
    key.strip()
    for key in (
        os.getenv("SIGURSCAN_API_KEYS")
        or os.getenv("NUDACLICK_API_KEYS")
        or ""
    ).split(",")
    if key.strip()
}

# Operator-only keys.
ADMIN_API_KEYS = {
    key.strip()
    for key in (os.getenv("SIGURSCAN_ADMIN_API_KEYS") or "").split(",")
    if key.strip()
}
INTERNAL_WORKER_TOKEN = (
    os.getenv("SIGURSCAN_INTERNAL_WORKER_TOKEN")
    or os.getenv("INTERNAL_WORKER_TOKEN")
    or ""
).strip()

ADMIN_ONLY_PATHS = {
    "/v1/orchestration/dashboard",
    "/v1/orchestration/telemetry",
    "/v1/feedback/summary",
    "/v1/adjudication/shadow",
    "/v1/adjudication/dashboard",
    "/v1/intel/ingest",
    "/v1/intel/moderate",
    "/v1/intel/moderation-queue",
    "/v1/intel/sources",
    "/v1/urechea/run",
    "/v1/campaign/active",
    "/v1/campaign/families",
    "/v1/campaign/match",
    "/v1/evaluation/feedback",
    "/v1/evaluation/run",
    "/v1/feedback/samples",
    "/v1/feedback/quality",
    "/v1/evaluation/feedback/trend",
    "/v1/evaluation/readiness",
}

PUBLIC_PATHS = {
    "/",
    "/health",
    "/healthz",
    "/health/security",
    "/privacy",
    "/privacy-policy",
    "/terms",
    "/terms-of-service",
}

# GET-only screenshot proxy consumed by image loaders (Coil) that cannot attach
# auth headers. Unguessable urlscan UUID in the path; rate limiting still applies.
_SCREENSHOT_PROXY_PATH_RE = re.compile(r"^/v1/sandbox/urlscan/[^/]+/screenshot$")

# Scan intake routes covered by Play Integrity once it leaves "off" mode.
_INTEGRITY_GUARDED_PREFIXES = ("/v1/scan/", "/v1/extract/", "/v1/sandbox/urlscan")
PLAY_INTEGRITY_NONCE_PATH = "/v1/security/play-integrity/nonce"
CLIENT_INSTANCE_HEADER = "X-SigurScan-Client-Instance"

ENABLE_RATE_LIMIT = os.getenv("ENABLE_RATE_LIMIT", "true").strip().lower() in {"1", "true", "yes", "on"}
# Pilon DNS reputation (gratis, fără cheie). Free-first: OPT-IN, implicit OFF.
ENABLE_DNS_REPUTATION = os.getenv("ENABLE_DNS_REPUTATION", "false").strip().lower() in {"1", "true", "yes", "on"}
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
RATE_LIMIT_WINDOW_SECONDS = 60

URLSCAN_API_KEY = (
    os.getenv("SIGURSCAN_URLSCAN_API_KEY")
    or os.getenv("NUDACLICK_URLSCAN_API_KEY")
    or os.getenv("URLSCAN_API_KEY")
    or ""
).strip()
URLSCAN_TIMEOUT_SECONDS = float(os.getenv("URLSCAN_TIMEOUT_SECONDS", "8.0"))

ENABLE_CLOUD_AI_EXPLANATION = os.getenv("ENABLE_CLOUD_AI_EXPLANATION", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
AI_EXPLANATION_TIMEOUT_SECONDS = float(os.getenv("AI_EXPLANATION_TIMEOUT_SECONDS", "2.5"))
AI_OFFER_CLAIM_TIMEOUT_SECONDS = float(os.getenv("AI_OFFER_CLAIM_TIMEOUT_SECONDS", "5.0"))
ENABLE_MISTRAL_SEMANTIC_PILLAR = os.getenv("ENABLE_MISTRAL_SEMANTIC_PILLAR", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
MISTRAL_SEMANTIC_API_KEY = os.getenv("MISTRAL_API_KEY", "").strip()
MISTRAL_SEMANTIC_MODEL = (
    os.getenv("MISTRAL_SEMANTIC_MODEL")
    or os.getenv("MISTRAL_MODEL")
    or "mistral-small-2503"
).strip()
MISTRAL_SEMANTIC_TIMEOUT_SECONDS = float(os.getenv("MISTRAL_SEMANTIC_TIMEOUT_SECONDS", "3.0"))

FAST_REPUTATION_MODE = os.getenv("FAST_REPUTATION_MODE", "true").strip().lower() in {"1", "true", "yes", "on"}
FAST_REPUTATION_INCLUDE_URLHAUS = os.getenv("FAST_REPUTATION_INCLUDE_URLHAUS", "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
ENABLE_DEEP_REPUTATION_FALLBACK = os.getenv("ENABLE_DEEP_REPUTATION_FALLBACK", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
DOMAIN_SUSPICIOUS_AGE_DAYS = int(os.getenv("DOMAIN_SUSPICIOUS_AGE_DAYS", "30"))
DOMAIN_ESTABLISHED_AGE_DAYS = int(os.getenv("DOMAIN_ESTABLISHED_AGE_DAYS", "365"))

DEFAULT_ALLOWED_ORIGINS = (
    "https://sigurscan.ro,"
    "https://www.sigurscan.ro,"
    "https://sigurscan-backend.vercel.app"
)
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS).split(",")
    if origin.strip()
]
if not ALLOWED_ORIGINS:
    ALLOWED_ORIGINS = DEFAULT_ALLOWED_ORIGINS.split(",")
ALLOWED_CORS_METHODS = ["GET", "POST", "OPTIONS"]
ALLOWED_CORS_HEADERS = [
    "Authorization",
    "Content-Type",
    "X-API-KEY",
    "X-Play-Integrity-Token",
    "X-SigurScan-Client-Instance",
]
SIGURSCAN_PUBLIC_API_BASE_URL = (
    os.getenv("SIGURSCAN_PUBLIC_API_BASE_URL", "https://api.sigurscan.com").strip().rstrip("/")
)

CLOUD_TASKS_PROJECT = (
    os.getenv("CLOUD_TASKS_PROJECT")
    or os.getenv("GOOGLE_CLOUD_PROJECT")
    or os.getenv("GCP_PROJECT")
    or ""
).strip()
CLOUD_TASKS_LOCATION = os.getenv("CLOUD_TASKS_LOCATION", "").strip()
CLOUD_TASKS_QUEUE = os.getenv("CLOUD_TASKS_QUEUE", "").strip()
ORCHESTRATED_CLOUD_TASKS_ENABLED = os.getenv(
    "ORCHESTRATED_CLOUD_TASKS_ENABLED",
    "false",
).strip().lower() in {"1", "true", "yes", "on"}
CLOUD_TASKS_METADATA_TOKEN_URL = os.getenv(
    "CLOUD_TASKS_METADATA_TOKEN_URL",
    "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token",
).strip()
CLOUD_TASKS_REQUEST_TIMEOUT_SECONDS = float(os.getenv("CLOUD_TASKS_REQUEST_TIMEOUT_SECONDS", "4.0"))
ORCHESTRATED_CLOUD_TASKS_CONTINUE_DELAY_SECONDS = int(
    os.getenv("ORCHESTRATED_CLOUD_TASKS_CONTINUE_DELAY_SECONDS", "3")
)
_LEGACY_SCREENSHOT_PROXY_HOSTS = {
    "nudaclick-backend.vercel.app",
    "sigurscan-backend.vercel.app",
}

ORCHESTRATED_JOB_TTL_SECONDS = int(os.getenv("ORCHESTRATED_JOB_TTL_SECONDS", "900"))
ORCHESTRATED_URLSCAN_PENDING_TIMEOUT_SECONDS = int(
    os.getenv("ORCHESTRATED_URLSCAN_PENDING_TIMEOUT_SECONDS", "120")
)
ORCHESTRATED_REQUIRED_PILLAR_TIMEOUT_SECONDS = int(
    os.getenv("ORCHESTRATED_REQUIRED_PILLAR_TIMEOUT_SECONDS", "90")
)
ORCHESTRATED_URLSCAN_SUBMIT_RESERVATION_TIMEOUT_SECONDS = int(
    os.getenv("ORCHESTRATED_URLSCAN_SUBMIT_RESERVATION_TIMEOUT_SECONDS", "30")
)
URLSCAN_SCREENSHOT_UNAVAILABLE_DETAILS = (
    "Raportul de verificare izolata este disponibil, dar captura paginii nu a fost publicata de provider. "
    "Verdictul final ramane bazat pe sursele de risc."
)
# Publish the verdict as soon as the required pillars are terminal, with
# is_final=false while the urlscan report is still pending.
ORCHESTRATED_EARLY_VERDICT = (
    os.getenv("ORCHESTRATED_EARLY_VERDICT", "true").strip().lower() in {"1", "true", "yes", "on"}
)
# Ship the first publishable verdict with the deterministic fallback
# explanation and attach the cloud explanation on a later poll.
ORCHESTRATED_DEFER_AI_EXPLANATION = (
    os.getenv("ORCHESTRATED_DEFER_AI_EXPLANATION", "true").strip().lower() in {"1", "true", "yes", "on"}
)
URLSCAN_PREVIEW_CACHE_TTL_SECONDS = int(os.getenv("URLSCAN_PREVIEW_CACHE_TTL_SECONDS", str(7 * 24 * 60 * 60)))
URLSCAN_PREVIEW_CACHE_MAX_ENTRIES = int(os.getenv("URLSCAN_PREVIEW_CACHE_MAX_ENTRIES", "512"))
FAST_PREVIEW_CACHE_MAX_ENTRIES = int(os.getenv("FAST_PREVIEW_CACHE_MAX_ENTRIES", "512"))
FAST_PREVIEW_SIGNED_URL_TTL_SECONDS = int(os.getenv("FAST_PREVIEW_SIGNED_URL_TTL_SECONDS", "900"))
ORCHESTRATED_REFRESH_LOCK_TTL_SECONDS = int(os.getenv("ORCHESTRATED_REFRESH_LOCK_TTL_SECONDS", "90"))

# URLSCAN/OA route internals
_ORCHESTRATED_STAGE_RANK = {
    "queued": 0,
    "resolved": 10,
    "urlhaus_ready": 15,
    "reputation_ready": 20,
    "semantic_ready": 25,
    "claim_ready": 28,
    "analysis_ready": 30,
    "urlscan_submitting": 35,
    "urlscan_submitted": 40,
    "done": 100,
}

_VERDICT_SEVERITY_RANK = {"SAFE": 0, "UNVERIFIED": 1, "SUSPECT": 2, "DANGEROUS": 3}
