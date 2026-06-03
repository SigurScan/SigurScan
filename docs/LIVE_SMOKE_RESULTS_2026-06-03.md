# Live Smoke Results - 2026-06-03

Scope: controlled live smoke for the star pipeline pieces: message intake, URL extraction, Web Risk / VT / urlscan provider calls, final-page preview, and claim verifier behavior.

## Cases

### YOXO buyback SMS

Input summary: user-provided SMS mentioning YOXO buy-back and `buyback.yoxo.ro`.

Observed:
- `/v1/scan/text` returned HTTP 200.
- Extracted URL: `https://buyback.yoxo.ro/`.
- Final URL from urlscan: `https://buyback.yoxo.ro/?r=1`.
- Web Risk was consulted.
- VirusTotal was consulted.
- urlscan completed with `No malicious classification`, score `0`.
- Initial generic urlscan screenshot was a loader-only page.
- Re-running urlscan with Romania + Android mobile persona produced a real page preview.
- Saved preview: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/tmp_live_smoke/yoxo_mobile_ro.png`.

Gate expectation covered by test:
- Clean Web Risk + clean VT + clean urlscan + official final domain + no sensitive form => `Sigur`.
- Claim verifier may be inconclusive without blocking `Sigur` when technical evidence is clean and destination is official.

### iDroid service SMS

Input summary: user-provided SMS with service status link `https://idroid.ro/verificare-status`.

Observed:
- `/v1/scan/text` returned HTTP 200.
- Extracted URL: `https://idroid.ro/verificare-status`.
- Final URL from urlscan: `https://idroid.ro/verifica-status/`.
- Web Risk was consulted.
- VirusTotal was consulted.
- urlscan completed with `No malicious classification`, score `0`.
- Screenshot was non-empty and showed the real service-status page.
- Saved preview: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/tmp_live_smoke/idroid_service_sms.png`.

Gate expectation covered by test:
- Clean providers + official claim confirmation + official final domain + no sensitive form => `Sigur`.

## Fixes Added From Smoke

- Backend urlscan sandbox now supports `country` and `customagent`.
- Android sends a Romania + Android mobile persona for urlscan sandbox preview.
- Backend no longer falls back to `verify=False` on TLS failures.
- Backend public branding was changed to SigurScan while keeping legacy env aliases for deploy compatibility.

## Remaining Real Risk

- Gemini returned HTTP 429 quota errors during live smoke. Backend falls back safely, but AI claim verification is not reliably live until quota/billing/provider fallback is handled.
- urlscan screenshots can still be delayed or visually incomplete for heavily dynamic sites. Mobile/RO persona improves YOXO, but this remains an operational risk to monitor.

## Verification Commands

Android:

```bash
JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" ./gradlew :app:testDebugUnitTest
JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" ./gradlew :app:assembleDebug :app:assembleRelease :app:lintDebug
```

Backend:

```bash
./venv/bin/python -m pytest test_backend.py
```
