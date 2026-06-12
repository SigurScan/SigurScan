# SigurScan Freeze Proof - 2026-06-12

Status: in progress. This document is proof-led: an item is not green unless the evidence below can be rerun.

## Source Of Truth

- Repository: `vaduvel/SigurScan`
- Local repo: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan`
- Current branch: `main`
- Verified code commit: `17dcfc7`
- Deployed code commit: `17dcfc7`
- Documentation may advance past the deployed code commit with proof-only updates.
- Cloud Run project: `project-20f225c0-d756-4cba-864`
- Cloud Run service: `sigurscan-api`
- Cloud Run region: `europe-west1`
- Official API domain: `https://api.sigurscan.com`

## Zone 1 - Google Cloud Run

### Verified

- Cloud Run service exists in `europe-west1`.
  Evidence: `gcloud run services describe sigurscan-api --project project-20f225c0-d756-4cba-864 --region europe-west1`.
- Latest ready revision is `sigurscan-api-00020-xvd`.
- Traffic is `100%` to `sigurscan-api-00020-xvd`.
- Deployed image is `europe-west1-docker.pkg.dev/project-20f225c0-d756-4cba-864/sigurscan/sigurscan-api:17dcfc7`.
- Cloud Build deployment proof:
  - build id: `8d7baef8-3a79-482c-be3c-c7d4e0823ef8`
  - status: `SUCCESS`
  - service URL: `https://sigurscan-api-357849228072.europe-west1.run.app`
- Request timeout is `300s`.
- Container concurrency is `40`.
- CPU/memory are `1 CPU` / `1Gi`.
- Min instances is `1`; max instances is `5`.
- CPU throttling is `true`, preserving request-based CPU billing rather than always-allocated CPU.
- Startup CPU boost is enabled.
- Provider secrets are injected through Secret Manager references, including Supabase, Gemini, Vision, Web Risk, Mistral, urlscan, URLhaus, Upstash, app API keys, admin API keys, and `invoice-cache-hmac-key`.
- Invoice cache HMAC uses only `INVOICE_CACHE_HMAC_KEY` from Secret Manager/env.
  - Legacy fallback string `sigurscan-cache-key-v1` has been removed from runtime code.
  - `gcloud secrets list` confirms `invoice-cache-hmac-key` exists in Secret Manager.
  - `gcloud secrets list` does not show a separate `sigurscan-cache-key-v1` secret.
  - Cloud Run injects `INVOICE_CACHE_HMAC_KEY=invoice-cache-hmac-key:latest`.
  - Test proof: `test_invoice_cache_key_requires_env_secret` fails without env and passes with the test fixture env.
- Health check returns `HTTP 200` through Cloudflare on `https://api.sigurscan.com/health`.
  - Post-deploy health after `21a6943`: `HTTP 200`, `0.361590s`.
  - Post-deploy health after `17dcfc7`: `HTTP 200`, `0.336330s`.
- API protection is active:
  - unauthenticated `POST /v1/scan/orchestrated` returns `401`.
  - authenticated `POST /v1/scan/orchestrated` returns `200` and creates a scan.
- Cloud Billing budget guard exists for this project:
  - billing account: `018B56-5DF133-D4A772`
  - budget id: `95a50d26-6008-4a9b-84f7-22d36d786ff5`
  - display name: `SigurScan Cloud Run Guard`
  - amount: `20 USD` monthly
  - project filter: `projects/357849228072`
  - thresholds: `50% current`, `100% current`, `100% forecasted`
- Authenticated smoke scan through official domain completed:
  - scan id: `orch_1781267052_627619ad`
  - poll 1: `SUSPECT`, `is_final=false`, `1.532s`
  - poll 2: `SUSPECT`, `is_final=true`, `4.262s`
- Live provider smoke after commit `cf842d2` passed:
  - report: `build/reports/live_provider_smoke_after_upfront_fee_fix_2026-06-12.json`
  - result: `5/5 passed`.
- Offer latency re-check through `https://api.sigurscan.com` with Android UA:
  - 4 consecutive OP-08 scans.
  - POST range: `0.487s` - `1.320s`.
  - Polls to provisional verdict: under `0.91s`.
  - Final poll range: `3.341s` - `3.546s`.
  - No `29s` poll reproduced in this run.
  - Captured scan ids: `orch_1781268026_47cf2e9a`, `orch_1781268035_bd224992`, `orch_1781268043_411c19b7`, `orch_1781268051_94f80036`.
- Warm Cloud Run smoke after `17dcfc7` through `https://api.sigurscan.com` with Android UA:
  - input: benign DNSC official URL smoke.
  - POST: `HTTP 200`, `1.434s`, scan created.
  - poll 1: `HTTP 200`, `4.382s`, total `5.815s`, `SIGUR`, `risk=low`, `is_final=false`, preview `ready`.
  - poll 2: `HTTP 200`, `4.307s`, total `11.131s`, `SIGUR`, `risk=low`, `is_final=true`, preview `ready`.
- Cloud Build log audit for build `8d7baef8-3a79-482c-be3c-c7d4e0823ef8` found no build failures/errors; only two standard Docker `pip as root` warnings.
- Authenticated lightweight concurrency probe through `https://api.sigurscan.com/health` with Android UA:
  - 20 requests, 10 workers.
  - result: `20/20 HTTP 200`, `0` errors.
  - total wall time: `5.577s`.
  - latency: min `0.150s`, p50 `0.224s`, p95 `0.300s`, max `5.343s`.
- Post-deploy latency re-check after `21a6943`:
  - Existing scan `orch_1781268789_c6e92ca2` returned `HTTP 200` in `4.008s` and was already `complete`, `SUSPECT`, `is_final=true`.
  - New offer scan `orch_1781269113_5074e703`:
    - POST: `HTTP 200`, `0.548s`
    - poll 1: `HTTP 200`, `0.807s`, still scanning
    - poll 2: `HTTP 200`, `0.755s`, `SUSPECT`, `is_final=false`
    - poll 3: `HTTP 200`, `3.407s`, `SUSPECT`, `is_final=true`
  - Cloud Run request logs for `orch_1781269113_5074e703` show server-side GET latencies of `0.501767931s`, `0.517308680s`, and `3.180505344s`.
  - A previous local `urllib` poll timeout was not reproduced with `requests`; Cloud Run logs for that scan showed quick server responses. Treat remaining risk as edge/client-path observability, not a confirmed backend handler latency defect.

### Not Yet Green

- Cold-start test after 15 minutes idle has not been run.
- Full scan concurrency/load test has not been run; only lightweight health concurrency is proven.
- Cloud Logging structured-error proof has not been captured.
- Latency outlier root-cause is not fully closed: a prior live run had one `29s` poll. The latest 4-run probe and the post-`21a6943` probe did not reproduce it, and Cloud Run logs show sub-4s server-side poll latency for the latest scan, so this remains a watch item rather than a confirmed code defect.
- Rollback has not been tested end-to-end.

### Immediate Fixes

1. Add/confirm Cloud Logging alerting for poll latency outliers, for example any `GET /v1/scan/orchestrated/{id}` over `8s` or any component duration over provider timeout.
2. Document rollback command and test it against the previous ready revision, or run a non-destructive dry-run proof if we do not want to move production traffic.
3. Run a controlled scan concurrency test with provider-safe fixtures/mocks or a very small live sample.

## Zone 2 - Cloudflare Official Domain

### Verified

- `https://api.sigurscan.com/health` responds with `HTTP/2 200`.
- Response headers show Cloudflare in the path:
  - `server: cloudflare`
  - `cf-cache-status: DYNAMIC`
  - `x-sigurscan-edge: cloudflare`
  - `cache-control: no-store`
- Official domain health body reports:
  - `rate_limit_enabled=true`
  - `rate_limit_backend=upstash`
  - `api_key_required=true`
  - configured providers: urlscan, Google Web Risk, Phishing.Database, URLhaus, Mistral/Gemini explanation, offer claim verifier.
- Cloudflare user-agent behavior is explicit:
  - Default `curl` UA: `HTTP 200` on `/health`.
  - `Python-urllib/3.14`: `HTTP 403` at the Cloudflare edge.
  - Android-style UA `okhttp/4.12.0 SigurScan/1.0 Android`: `HTTP 200`.
  - Android app now sends a stable `User-Agent: SigurScan/1.0 Android OkHttp` through `ApiKeyInterceptor`.
  - Post-`21a6943` proof:
    - `Python-urllib/3.14`: `HTTP 403`, `0.103618s`
    - `SigurScan/1.0 Android OkHttp`: `HTTP 200`, `0.184060s`
    - authenticated Android UA health: `HTTP 200`, `0.164287s`
  - This is a Cloudflare/WAF user-agent rule, not CORS. QA scripts and legitimate non-Android clients must send an app-like UA or be allowlisted intentionally.

### Not Yet Green

- TLS chain screenshot/proof not captured.
- HTTP to HTTPS redirect not tested.
- Cloudflare cache bypass/rate-limit rules for `/v1/*` not fully audited.
- Cloudflare timeout behavior for long scans not tested.
- Android mobile-network test on 4G/5G not recorded.

## Zone 7 - Main Consolidation Snapshot

### Verified

- `main` contains the freeze integration, invoice HMAC config, upfront-fee offer fix, secret fallback removal, and Android UA hardening:
  - `4bbbc88 feat: integrate freeze offer knowledge and invoice pipeline`
  - `789d497 chore: wire invoice HMAC secret into Cloud Run deploy`
  - `cf842d2 fix: flag upfront fee offer scams`
  - `21a6943 fix: close freeze secret and edge UA gaps`
- `origin/main` includes deployed code commit `17dcfc7`; later proof-only documentation commits do not require a backend redeploy.
- Cloud Run intentionally remains on code image `17dcfc7` until the next code deploy.

### Not Yet Green

- Need a final branch audit for unmerged feature branches before deleting anything.
- Need one full backend + Android test run after any remaining Cloud Run config fixes.

## Current Verdict

Freeze is not complete yet.

The backend is live and healthy on Cloud Run behind `api.sigurscan.com`, with provider smoke green, API auth active, invoice HMAC secret fallback removed, Android UA hardening deployed, reproducible min instances enabled, request-based CPU billing preserved, a Cloud Billing budget guard created, build log audited, and lightweight concurrency proven. The next blocking items are latency alerting, rollback proof, and a controlled scan-concurrency probe.
