# Pre-Capture Worker Integration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the deployable Playwright pre-capture worker to SigurScan so cached visual previews can be served quickly without making urlscan the user-facing screenshot bottleneck.

**Architecture:** The worker is a separate deployable unit under `workers/precapture`; it captures screenshots and writes fast-preview rows to Supabase. The backend remains the source of truth for verdicts and only reads fast-preview cache as a visual enhancement. urlscan remains threat-intel and can still provide its own report/screenshot asynchronously. For v1, this worker is a seed/pre-warm tool, not a live on-demand screenshot API.

**Tech Stack:** Node.js 20, Playwright Chromium, Docker, GitHub Actions, Supabase Postgres + Storage, existing Python backend.

---

## Target Placement

The ZIP from `/Users/vaduvageorge/Downloads/sigurscan_precapture_worker_v1_1_deployable.zip` should be unpacked into:

```text
/Users/vaduvageorge/AndroidStudioProjects/SigurScan/workers/precapture/
```

This keeps it separate from:

```text
/Users/vaduvageorge/AndroidStudioProjects/SigurScan/backend/
/Users/vaduvageorge/AndroidStudioProjects/SigurScan/app/
/Users/vaduvageorge/AndroidStudioProjects/SigurScan/supabase/
```

The worker must not run inside Android, inside Vercel request handling, or inside the current scan endpoint.

## Product Strategy

The deployable worker is useful, but only if we use it in the right layer.

```text
Tier 0 - Official seed previews
  Worker captures known official Romanian brands/domains on a schedule.
  Goal: legitimate/common URLs show preview instantly.
  Launch v1: YES.

Tier 1 - Shared capture-once cache
  Every user scan can benefit from cache already created by previous scans.
  In v1 this is already handled by urlscan_preview_cache, not by the custom worker.
  Goal: first user waits, later users get the same campaign preview faster.
  Launch v1: YES, via urlscan cache.

Tier 2 - Threat-feed pre-capture
  Worker can later ingest URLhaus / Phishing.Database / curated known-bad feeds.
  Goal: known scam pages also have instant visual context.
  Launch v1: OPTIONAL, after feed hygiene.

Tier 3 - Custom on-demand worker API
  Worker captures new user URLs live.
  Goal: faster screenshot than urlscan.
  Launch v1: NO. Keep urlscan for new/on-demand captures even if slower.
```

Important: fast preview is visual-only. It must never downgrade or upgrade verdicts.

For v1, cache keys remain `sha256(final_url_normalized)` because the worker only processes public official/frequent seeds. If SigurScan later captures URLs derived from real user scans with this worker, add `PREVIEW_HASH_PEPPER` / HMAC and a privacy gate before writing any original URL or alias.

## Runtime Contract

The final product should have two preview sources:

```text
1. urlscan_preview_cache
   Source: urlscan.io
   Role: threat-intel report + security sandbox screenshot
   Verdict impact: urlscan malicious can affect verdict

2. fast_preview_cache / url_preview_cache
   Source: our Playwright pre-capture worker
   Role: fast visual preview only
   Verdict impact: never decides safe/scam by itself
```

Backend preview priority:

```text
1. urlscan cache hit with screenshot/report
2. fast pre-capture cache hit with screenshot
3. urlscan async pending
4. preview unavailable
```

Launch v1 rule:

```text
If preview is missing:
  Do not block verdict.
  Show verdict and mark preview as pending/unavailable.

If preview later appears:
  Update visual card only.
  Do not recalculate verdict from the screenshot alone.
```

## Task 1: Import Worker As Separate Deployable Unit

**Files:**
- Create: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/workers/precapture/`
- Modify: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/.gitignore`

- [ ] Extract the deployable ZIP into the target folder.

Run:

```bash
mkdir -p /Users/vaduvageorge/AndroidStudioProjects/SigurScan/workers/precapture
unzip -q /Users/vaduvageorge/Downloads/sigurscan_precapture_worker_v1_1_deployable.zip \
  -d /Users/vaduvageorge/AndroidStudioProjects/SigurScan/workers/precapture
```

- [ ] Ensure local output and secrets are ignored.

Add to `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/.gitignore`:

```gitignore
workers/precapture/.env
workers/precapture/output/
workers/precapture/node_modules/
workers/precapture/playwright-report/
workers/precapture/test-results/
```

- [ ] Verify expected files exist.

Run:

```bash
ls -la /Users/vaduvageorge/AndroidStudioProjects/SigurScan/workers/precapture
```

Expected: `Dockerfile`, `docker-compose.yml`, `package.json`, `src/index.js`, `supabase/schema.sql`, `.github/workflows/precapture.yml`.

## Task 2: Align Supabase Schema With SigurScan

**Files:**
- Create: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/supabase/migrations/<timestamp>_create_fast_preview_cache.sql`
- Review: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/workers/precapture/supabase/schema.sql`

- [ ] Create a SigurScan migration for a dedicated fast preview table.

Use this table name to avoid confusing it with urlscan:

```sql
create table if not exists public.fast_preview_cache (
  url_hash text primary key,
  original_url text,
  final_url text not null,
  redirect_chain jsonb not null default '[]'::jsonb,
  http_status integer,
  page_title text,
  screenshot_path text,
  captured_at timestamptz not null default now(),
  expires_at timestamptz not null default now() + interval '7 days',
  source_email_id jsonb,
  reachable boolean not null default false,
  error text,
  provider text not null default 'precapture_worker',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.fast_preview_alias_cache (
  original_url_hash text primary key,
  final_url_hash text not null references public.fast_preview_cache(url_hash) on delete cascade,
  original_url text,
  final_url text,
  captured_at timestamptz not null default now(),
  expires_at timestamptz not null default now() + interval '7 days'
);

alter table public.fast_preview_cache enable row level security;
alter table public.fast_preview_alias_cache enable row level security;

revoke all on table public.fast_preview_cache from anon, authenticated;
revoke all on table public.fast_preview_alias_cache from anon, authenticated;

create index if not exists idx_fast_preview_cache_expires_at
on public.fast_preview_cache (expires_at);

create index if not exists idx_fast_preview_alias_cache_final_url_hash
on public.fast_preview_alias_cache (final_url_hash);
```

- [ ] Create a private Supabase Storage bucket named `previews` if it does not already exist.

- [ ] Keep writes service-role only. Android must never write directly to this cache.

## Task 3: Make Worker Write To SigurScan Table Names

**Files:**
- Modify: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/workers/precapture/.env.example`
- Modify: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/workers/precapture/.github/workflows/precapture.yml`
- Modify: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/workers/precapture/HOSTING_GUIDE.md`

- [ ] Set default table names to the SigurScan contract.

Use:

```bash
CACHE_TABLE=fast_preview_cache
ALIAS_TABLE=fast_preview_alias_cache
STORAGE_BUCKET=previews
```

- [ ] Keep `SUPABASE_SERVICE_KEY` only in server-side env/secrets.

Never commit `.env`.

## Task 3A: Harden Worker Before Any Hosted Run

**Files:**
- Modify: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/workers/precapture/src/index.js`
- Modify: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/workers/precapture/docker-compose.yml`
- Modify: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/workers/precapture/Dockerfile`
- Modify: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/workers/precapture/docs/SECURITY_NOTES.md`

- [ ] Add a max screenshot height / viewport clip guard.

Reason: `fullPage: true` can explode memory on hostile infinite-scroll pages.

Recommended v1 behavior:

```text
Capture viewport or capped full-page height.
Default max height: 5000px.
Do not attempt infinite-scroll.
```

- [ ] Reconcile `screenshot_path` with Supabase object key.

Current worker uploads object key:

```text
<hash>.png
```

But row may store:

```text
previews/<hash>.png
```

Backend must know whether `screenshot_path` is a bucket-relative object key or a decorated path. Pick one:

```text
screenshot_path = <hash>.png
storage_bucket = previews
```

- [ ] Test Chromium sandbox behavior in Docker.

If `chromiumSandbox: true` fails under hardened Docker flags, use container isolation plus:

```text
chromiumSandbox: false
```

Do not silently ship a worker that only works locally.

- [ ] Document DNS rebinding limitation.

The worker blocks private IPs per request, but Chromium may still re-resolve names internally. Hosted runs must use network egress restrictions where possible. This is a deployment requirement, not only an application-code requirement.

## Task 4: Add Backend Read Path For Fast Preview Cache

**Files:**
- Modify: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/backend/services/supabase_store.py`
- Modify: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/backend/main.py`
- Test: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/backend/test_backend.py`

- [ ] Add Supabase readers:

```python
load_fast_preview_cache(url_hash: str) -> dict | None
load_fast_preview_alias_cache(original_url_hash: str) -> dict | None
```

- [ ] Add a backend normalizer that maps rows to UI preview payload:

```json
{
  "status": "ready",
  "source": "precapture_worker",
  "image_path": "previews/<hash>.png",
  "final_url": "https://example.ro/",
  "page_title": "Example",
  "captured_at": "2026-06-09T..."
}
```

- [ ] Add cache lookup after `primary_final_url` is known and before urlscan submit.

Expected behavior:

```text
If fast preview cache exists:
  preview.status = ready
  preview.source = precapture_worker
  verdict remains unchanged
  urlscan can still run async for threat-intel if needed
```

## Task 5: Test The Worker Locally Without Supabase

**Files:**
- Read: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/workers/precapture/samples/official_preview_targets.ro.json`

- [ ] Install worker dependencies.

Run:

```bash
cd /Users/vaduvageorge/AndroidStudioProjects/SigurScan/workers/precapture
npm install
npm run install-browsers
```

- [ ] Run dry-run.

Run:

```bash
npm run dry-run
```

Expected: `output/dry/dry_run_urls.json`.

- [ ] Run local sample capture.

Run:

```bash
npm run sample:local
```

Expected: `output/official/manifest.json` and `output/official/screenshots/*.png`.

## Task 6: Test Supabase Write Path On A Small Seed

**Files:**
- Use: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/workers/precapture/.env`

- [ ] Create `.env` locally with service-role credentials.

Required keys:

```bash
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...
STORAGE_BUCKET=previews
CACHE_TABLE=fast_preview_cache
ALIAS_TABLE=fast_preview_alias_cache
```

- [ ] Run one small seed capture.

Run:

```bash
cd /Users/vaduvageorge/AndroidStudioProjects/SigurScan/workers/precapture
node src/index.js \
  --email-source ./samples/official_preview_targets.ro.json \
  --out-dir ./output/official \
  --concurrency 1 \
  --nav-timeout-seconds 20
```

- [ ] Verify Supabase contains rows in `fast_preview_cache` and `fast_preview_alias_cache`.

## Task 7: Deployment Choice

Use one of these, in order:

```text
1. GitHub Actions schedule
   Best for daily official previews and low traffic.

2. Oracle Free + Coolify
   Best for a real worker service and more frequent captures.

3. Google Cloud Run Job
   Good technically, but watch free-tier/credit usage.
```

For launch, start with:

```text
GitHub Actions daily official seed + manual workflow_dispatch
```

Then move to:

```text
Oracle Free + Coolify only if we later need more frequent scheduled captures or feed-based captures.
```

Do not build custom on-demand capture API for launch v1. For cache misses, let urlscan handle visual preview asynchronously.

## Task 8: Optional Threat Feed Pre-Capture

**Files:**
- Create: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/workers/precapture/samples/threat_feed_preview_targets.example.json`
- Modify: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/workers/precapture/HOSTING_GUIDE.md`

- [ ] Keep this optional until the official seed path is stable.

- [ ] Only feed safe, vetted URLs from sources already approved in the backend.

Potential sources:

```text
URLhaus
Phishing.Database
curated internal campaign URLs already seen by SigurScan
```

- [ ] Never capture unlimited feeds. Enforce:

```text
daily max URLs
per-domain max URLs
timeout
dead URL skip
TTL
```

## Task 9: V1.1 Crowd-Cache Readiness

Do not implement this for launch v1 unless the product explicitly moves to worker-based user URL capture.

- [ ] Add `fast_preview_capture_runs` for operational audit.
- [ ] Add `PREVIEW_HASH_PEPPER` and HMAC cache keys for URLs derived from user scans.
- [ ] Add URL privacy gate before alias writes from user-derived URLs.
- [ ] Add cleanup for expired DB rows and Storage objects.
- [ ] Add egress firewall/network policy to the hosted worker runtime.

## Acceptance Tests

- [ ] Backend tests pass:

```bash
cd /Users/vaduvageorge/AndroidStudioProjects/SigurScan
python3 -m pytest backend/test_backend.py
```

- [ ] Android tests/build pass:

```bash
cd /Users/vaduvageorge/AndroidStudioProjects/SigurScan
JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" ./gradlew :app:testDebugUnitTest :app:assembleDebug
```

- [ ] A cached official URL returns preview in under 5 seconds.

- [ ] A non-cached URL still returns verdict normally and shows preview as pending/unavailable.

- [ ] A fast preview cache hit never changes `SIGUR` / `SUSPECT` / `PERICULOS`.

- [ ] A fast preview cache hit for an official seed URL returns `preview.source = "precapture_worker"` and does not suppress urlscan threat-intel when urlscan is already available.

- [ ] A urlscan cache hit for a user-scanned campaign URL still wins over fast preview when it includes a report URL and screenshot.

- [ ] A cache miss returns verdict normally and leaves `preview.status` as `pending` or `unavailable`.

## Non-Negotiables

- The worker does not decide verdict.
- The worker does not run in Android.
- The worker does not run inside a Vercel scan request.
- The worker does not run as a custom on-demand API in launch v1.
- The worker does not receive raw mailbox access.
- The worker only processes user-provided exports, seed lists, or backend-approved queue jobs.
- Supabase service-role key stays server-side only.
- urlscan remains the on-demand screenshot/threat-intel provider for new user URLs.
