"""Static redirect/shortener detection constants.

Dangerous MIME types, known URL shorteners, meta-refresh / JS redirect patterns,
local-host blocklist and the DoH endpoint — extracted from redirect_resolver.py
to separate static detection data from the resolution logic.
"""

import re


DANGEROUS_MIMES = [
    "application/octet-stream",
    "application/x-msdownload",  # .exe, .dll
    "application/x-sh",
    "application/x-ms-shortcut", # .lnk
    "application/zip",
    "application/x-tar",
    "application/x-rar-compressed",
    "application/x-debian-package",
    "application/vnd.android.package-archive" # .apk
]

# Known URL shortener domains — any link through these is suspicious in a cold message
KNOWN_SHORTENERS = {
    "bit.ly", "bitly.com", "tinyurl.com", "t.ly", "shorturl.at", "is.gd",
    "goo.gl", "ow.ly", "cutt.ly", "rebrand.ly", "bl.ink", "short.io",
    "tiny.cc", "lnkd.in", "buff.ly", "clck.ru", "rb.gy", "v.gd",
    "qr.ae", "adf.ly", "bc.vc", "j.mp", "surl.li", "s.id", "postis.io", "t.postis.io",
    "rotf.lol", "1url.com", "hyperurl.co", "urlzs.com", "u.to",
    "shrtco.de", "lmy.de", "shorturl.asia", "link.ac", "urlz.fr"
}

# Regex to extract meta-refresh redirect URLs from HTML
# Matches: <meta http-equiv="refresh" content="0; url=https://example.com">
META_REFRESH_RE = re.compile(
    r'<meta\s+[^>]*?http-equiv\s*=\s*["\']?refresh["\']?\s+[^>]*?content\s*=\s*["\']?\d+\s*;\s*url\s*=\s*([^"\'\s>]+)',
    re.IGNORECASE
)

# Regex to detect JavaScript-based redirects in HTML body
# Matches: window.location = "...", window.location.href = "...",
# location.replace("..."), document.location = "..."
JS_REDIRECT_PATTERNS = [
    re.compile(r'(?:window\.)?location(?:\.href)?\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE),
    re.compile(r'(?:window\.)?location\.replace\s*\(\s*["\']([^"\']+)["\']', re.IGNORECASE),
    re.compile(r'document\.location\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE),
    re.compile(r'window\.open\s*\(\s*["\']([^"\']+)["\']', re.IGNORECASE),
]

# Maximum bytes of HTML body to read when scanning for meta/JS redirects
# Keeps things safe — we only look at the first 32KB of text/html responses
MAX_HTML_SCAN_BYTES = 32 * 1024

LOCAL_HOST_BLOCKLIST = {
    "localhost",
    "localhost.localdomain",
    "local",
    "localdomain",
}

CF_DNS_API_URL = "https://cloudflare-dns.com/dns-query"
