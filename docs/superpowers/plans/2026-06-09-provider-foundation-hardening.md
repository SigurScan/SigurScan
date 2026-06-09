# SigurScan Provider Foundation Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the current no-VT provider stack production-grade: urlscan correct, Phishing.Database cached, URLhaus active, RDAP/domain age visible to the gate, and live message tests reproducible.

**Architecture:** Keep one final deterministic gate. Providers produce evidence, domain infrastructure produces identity context, Tier1/atlas/Mistral calibrate semantic false positives, and the gate emits one user label: `SIGUR`, `SUSPECT`, or `PERICULOS`. Preview remains urlscan-backed and non-blocking for safety, but urlscan verdict can still upgrade risk.

**Tech Stack:** FastAPI backend on Vercel, Supabase persistence/cache, Android native client, Google Web Risk, Phishing.Database, URLhaus, urlscan.io, RDAP/ROTLD/Cloudflare DoH, local Tier1 classifier.

---

## Current State Confirmed

- `backend/services/url_reputation.py` has `google_web_risk`, `phishing_database`, and `urlhaus`.
- `backend/services/redirect_resolver.py` already uses valid RDAP and Cloudflare MX URLs and runs domain age + MX in parallel.
- `backend/services/verdict_gate.py` already reads `identity.domain_age_days` / `identity.domain_reputation` and promotes clean established unknown domains to `SIGUR`.
- `backend/services/tier1_classifier.py` already exists and calibrates legit marketing / official notices without deciding the final verdict.
- Live `/health` still reports the older `virustotal` provider, so the current local provider stack must be pushed/deployed before live conclusions.

---

## Task 1: Provider Runtime Truth

**Files:**
- Modify: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/backend/main.py`
- Test: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/backend/test_backend.py`

- [ ] **Step 1: Verify health reports the active provider stack**

Run:

```bash
python3 -m pytest backend/test_backend.py::test_health_reports_provider_config_without_secrets -q
```

Expected:

```text
1 passed
```

- [ ] **Step 2: Confirm health has no VirusTotal in local runtime**

Run:

```bash
rg -n "virustotal|VirusTotal|VIRUSTOTAL|VIRUS_TOTAL" backend/main.py backend/services backend/.env.example -S
```

Expected: no runtime matches in backend production files.

- [ ] **Step 3: Confirm Vercel env names**

Required Vercel environment variables:

```bash
GOOGLE_WEB_RISK_API_KEY=...
SIGURSCAN_URLSCAN_API_KEY=...
URLHAUS_AUTH_KEY=...
ENABLE_PHISHING_DATABASE=true
PHISHING_DATABASE_FEED_TTL_SECONDS=3600
DOMAIN_ESTABLISHED_AGE_DAYS=365
DOMAIN_SUSPICIOUS_AGE_DAYS=30
ENABLE_MISTRAL_SEMANTIC_PILLAR=true
MISTRAL_SEMANTIC_API_KEY=...
```

- [ ] **Step 4: Deploy and verify live health**

Run after deploy:

```bash
curl -sS https://nudaclick-backend.vercel.app/health | python3 -m json.tool
```

Expected live provider config must show `phishing_database`, not `virustotal`, and must not expose secrets.

---

## Task 2: Phishing.Database Cache Quality

**Files:**
- Modify: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/backend/services/url_reputation.py`
- Test: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/backend/test_backend.py`

- [ ] **Step 1: Run existing cache tests**

Run:

```bash
python3 -m pytest \
  backend/test_backend.py::test_reputation_uses_phishing_database_feed_as_active_provider \
  backend/test_backend.py::test_phishing_database_marks_active_domain_malicious \
  backend/test_backend.py::test_phishing_database_clean_when_not_listed \
  backend/test_backend.py::test_local_reputation_cache_is_lru_capped \
  backend/test_backend.py::test_supabase_reputation_cache_uses_single_batch_upsert \
  -q
```

Expected:

```text
5 passed
```

- [ ] **Step 2: Confirm feed is bounded**

Inspect these constants:

```bash
rg -n "PHISHING_DATABASE_FEED_TTL_SECONDS|PHISHING_DATABASE_MAX_FEED_BYTES|_PHISHING_DATABASE_CACHE" backend/services/url_reputation.py -S
```

Expected: feed TTL is configured, max feed bytes is configured, and in-memory cache exists.

- [ ] **Step 3: Live smoke one safe and one reserved malicious fixture**

Safe live check should be a real URL like `https://www.hipo.ro/ADT_TM`.

Malicious test must use a mocked/unit test or reserved fixture, not send fake `.test` domains to live providers.

Expected:

- safe URL: Phishing.Database `clean/not_listed`
- feed hit fixture: Phishing.Database `malicious`

---

## Task 3: URLhaus Activation

**Files:**
- Modify: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/backend/services/url_reputation.py`
- Modify: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/backend/main.py`
- Test: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/backend/test_backend.py`

- [ ] **Step 1: Run URLhaus tests**

Run:

```bash
python3 -m pytest \
  backend/test_backend.py::test_reputation_cache_refetches_when_configured_source_was_not_consulted \
  backend/test_backend.py::test_urlhaus_without_auth_key_is_not_consulted \
  backend/test_backend.py::test_urlhaus_uses_auth_key_header_and_form_payload \
  backend/test_backend.py::test_orchestrated_resolved_stage_collects_fast_reputation_without_urlhaus \
  -q
```

Expected:

```text
4 passed
```

- [ ] **Step 2: Confirm orchestration calls URLhaus after fast reputation**

Run:

```bash
rg -n "urlhaus_ready|include_urlhaus=True|include_urlhaus=False" backend/main.py -S
```

Expected: initial reputation may skip URLhaus for speed, but `urlhaus_ready` must call `include_urlhaus=True`.

- [ ] **Step 3: Live verify consulted flag**

Run a live orchestrated scan and inspect the final payload:

```bash
curl -sS -X POST "https://nudaclick-backend.vercel.app/v1/scan/orchestrated" \
  -H "Content-Type: application/json" \
  -d '{"text":"Hipo iti recomanda evenimentul Angajatori de TOP. Inscrie-te https://www.hipo.ro/ADT_TM","source_channel":"sms"}'
```

Poll the returned `scan_id` until complete. Expected in final evidence:

```json
{
  "urlhaus": {
    "consulted": true
  }
}
```

---

## Task 4: RDAP / Domain Age Gate Wiring

**Files:**
- Modify: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/backend/services/redirect_resolver.py`
- Modify: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/backend/main.py`
- Modify: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/backend/services/verdict_gate.py`
- Test: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/backend/test_backend.py`
- Test: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/backend/test_verdict_gate.py`

- [ ] **Step 1: Verify RDAP and MX URL construction**

Run:

```bash
python3 -m pytest \
  backend/test_backend.py::test_rdap_domain_age_uses_valid_url_without_literal_braces \
  backend/test_backend.py::test_mx_lookup_uses_valid_cloudflare_doh_url_without_literal_braces \
  -q
```

Expected:

```text
2 passed
```

- [ ] **Step 2: Verify domain age reaches provider gate**

Run:

```bash
python3 -m pytest backend/test_backend.py::test_provider_gate_exposes_established_domain_as_positive_context -q
```

Expected:

```text
1 passed
```

- [ ] **Step 3: Verify clean established unknown domain becomes safe**

Run:

```bash
python3 -m pytest backend/test_verdict_gate.py::test_unknown_clean_established_domain_is_safe_without_manual_registry -q
```

Expected:

```text
1 passed
```

- [ ] **Step 4: Verify new/young domains do not get safe by accident**

Run:

```bash
python3 -m pytest backend/test_backend.py::test_provider_gate_does_not_mark_new_first_party_domain_as_low_risk -q
```

Expected:

```text
1 passed
```

---

## Task 5: urlscan Correctness

**Files:**
- Modify: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/backend/main.py`
- Test: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/backend/test_backend.py`

- [ ] **Step 1: Verify urlscan is non-blocking for screenshot**

Run:

```bash
python3 -m pytest backend/test_backend.py::test_urlscan_finished_without_screenshot_is_reputation_ok_not_error -q
```

Expected:

```text
1 passed
```

- [ ] **Step 2: Verify late urlscan malicious can upgrade verdict**

Run:

```bash
python3 -m pytest backend/test_backend.py::test_orchestrated_urlscan_late_risk_upgrades_provisional_safe_verdict -q
```

Expected:

```text
1 passed
```

- [ ] **Step 3: Live smoke urlscan preview**

Run a real safe marketing URL and poll until urlscan finishes or times out.

Expected:

- verdict can finish without screenshot if blocking pillars are clean
- `preview.report_url` appears once urlscan accepts the scan
- `preview.screenshot_url` appears only when urlscan screenshot is ready
- urlscan malicious status must still feed `provider_malicious`

---

## Task 6: Real Message Live Suite

**Files:**
- Create or update: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/backend/eval/live_provider_smoke_runner.py`
- Add report output to ignored local files only.

- [ ] **Step 1: Use these real safe messages**

```text
Hipo iti recomanda evenimentul Angajatori de TOP. Inscrie-te https://www.hipo.ro/ADT_TM si vino pe 13-14 Octombrie la Centrul Regional de Afaceri Timisoara.
```

```text
In data de 07-06-2026 s-a emis factura ta Orange in valoare de 32.32 lei. Descarca factura aici https://orange.ro/r/KK5IMyT si afla informatii de interes despre contul tau.
```

```text
Buna! Estimatul de livrare a comenzii este azi. Ai optiuni la delivery2.sameday.ro/4Af6SMi6FtC9MCsd6
```

Expected: `SIGUR` when providers are clean, destination is official/delegated/coherent or established, and no direct request for card/OTP/password/remote access exists.

- [ ] **Step 2: Use these dangerous controls**

```text
FanCourier: Coletul dvs. nu a putut fi livrat — taxa vamala neachitata 3,50 RON. Reprogramati livrarea: https://fancurier-relivrare.com/plata
```

```text
BNR: pentru siguranta contului, transfera banii intr-un cont sigur si contacteaza operatorul pe WhatsApp.
```

Expected: `PERICULOS`.

- [ ] **Step 3: Use phishing control**

Use Google Web Risk test URL only as a controlled security-provider test.

Expected: `PERICULOS` through `google_web_risk`, independent of semantic/corpus.

- [ ] **Step 4: Capture timings**

Record:

- time to `scan_id`
- time to final user verdict
- time to urlscan report
- time to screenshot
- providers consulted
- final URL
- reason codes

Expected product target:

- scan ID under 2 seconds
- user verdict usually 5-15 seconds
- preview/report best effort, often 30-120 seconds on urlscan

---

## Definition of Done

- Backend tests pass:

```bash
python3 -m pytest backend/test_backend.py backend/test_verdict_gate.py -q
```

- Android tests/build pass:

```bash
JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" ./gradlew :app:testDebugUnitTest :app:assembleDebug
```

- Live `/health` reports the new provider stack, not VirusTotal.
- URLhaus final live payload shows `consulted: true`.
- Phishing.Database feed hit hard-blocks.
- Clean established unknown domains can become `SIGUR`.
- New/young domains and lookalikes do not become `SIGUR`.
- urlscan screenshot never blocks the verdict, but malicious urlscan can upgrade risk.
- Live safe Romanian messages produce `SIGUR` when evidence supports it.
