"""Classification taxonomy constants for the verdict gate.

Label sets, sensitive-request/channel/identity taxonomies, provider-status
buckets, navigation input types and known URL shorteners — extracted from
verdict_gate.py to separate the static taxonomy from the gating logic.
"""

INTERNAL_LABELS = {"DANGEROUS", "SUSPECT", "UNVERIFIED", "SAFE"}
USER_LABELS = {"DANGEROUS", "SUSPECT", "UNVERIFIED", "SAFE"}

HARD_SENSITIVE_REQUESTS = {"card", "cvv", "otp", "password", "pin", "banking_pin", "cnp", "iban", "crypto", "remote", "apk", "id_document"}
MONEY_OR_VALUE_REQUESTS = {"transfer"}
WRONG_CHANNELS = {"reply", "whatsapp", "unofficial_site", "phone", "sms", "telegram", "messenger", "social_dm"}
BAD_IDENTITY = {"lookalike", "unrelated"}
TRUSTED_IDENTITY = {"official", "delegated", "coherent", "official_match"}
DANGEROUS_SOCIAL_ENGINEERING_INTENTS = {
    "credential_theft",
    "payment_redirection",
    "remote_access",
    "investment_fraud",
    "recovery_scam",
}
BUILDUP_SOCIAL_ENGINEERING_INTENTS = DANGEROUS_SOCIAL_ENGINEERING_INTENTS | {"impersonation"}
DANGEROUS_SEMANTIC_FAMILIES = {
    "hidden_click_payment_or_confirm_cta",
    "qr_wifi_captive_payment_pretext",
    "official_poster_payment_qr_overlay",
}
PROVIDER_MALICIOUS = {"malicious", "phishing", "malware", "dangerous", "blacklisted"}
PROVIDER_SUSPICIOUS = {"suspicious"}
PROVIDER_CLEAN = {"clean", "no_match", "safe"}
PROVIDER_ERROR = {"error"}
PROVIDER_PENDING = {"pending", "running", "queued", "scanning"}
INCOMPLETE_RESOLUTION = {"failed", "partial", "pending", "unknown", ""}
ESTABLISHED_DOMAIN_AGE_DAYS = 365
CAMPAIGN_MATCH_HIGH_CONFIDENCE_THRESHOLD = 0.82
PUBLIC_NAVIGATION_INPUT_TYPES = {
    "qr",
    "qr_scan",
    "android_qr_scan",
    "url",
    "url_scan",
    "android_url_scan",
    "manual_url_scan",
}
PUBLIC_URL_TEXT_INPUT_TYPES = {"android_native", "text", "visible_text", "share_text"}


KNOWN_SHORTENER_DOMAINS = {
    "bit.ly", "bitly.com", "tinyurl.com", "t.ly", "shorturl.at", "is.gd",
    "t.co", "tiny.cc", "ow.ly", "rb.gy", "cutt.ly", "rebrand.ly", "buff.ly",
    "goo.gl", "shorte.st", "adf.ly", "bl.ink", "lnkd.in", "tr.im", "soo.gd",
}
