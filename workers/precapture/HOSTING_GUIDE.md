# SigurScan Pre-Capture Worker — Hosting Guide

This worker must be hosted as a background job/container, not inside the Android app and not as the main API request path.

## Recommended production topology

Android / backend asks cache:
`GET /preview?url_hash=...`

Supabase stores:
- `fast_preview_cache` table
- optional `fast_preview_alias_cache` table, so original/tracking URLs can resolve instantly to the final-url preview
- `previews` storage bucket

Pre-capture worker runs separately:
- daily official-domain seed job
- batch job for uploaded `.eml` exports
- optional queue job for URLs seen frequently but missing preview

## Option A — Local / dev

```bash
npm install
npx playwright install --with-deps chromium
cp .env.example .env
node src/index.js --email-source ./samples/official_preview_targets.ro.json --out-dir ./output/official --concurrency 1
```

Without Supabase env vars it writes:
- `output/official/manifest.json`
- `output/official/screenshots/*.png`

## Option B — Docker local

```bash
mkdir -p input output
cp samples/official_preview_targets.ro.json input/targets.json
cp .env.example .env

docker compose up --build
```

## Option C — Supabase + Docker

1. Run `supabase/schema.sql` in Supabase SQL editor.
2. Create private bucket `previews`.
3. Fill `.env`:

```bash
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_KEY=...
STORAGE_BUCKET=previews
CACHE_TABLE=fast_preview_cache
ALIAS_TABLE=fast_preview_alias_cache
```

4. Run Docker or Cloud Run Job.

## Option D — Cloud Run Job

Use `deploy/cloud-run-job.md`.

## Option E — GitHub Actions schedule

Use `.github/workflows/precapture.yml`. Add repository secrets:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`

This is good for official-domain seed previews and low-frequency smoke jobs. For production queueing, use Cloud Run/Fly/Render/Railway worker.

## Do not

- Do not run this inside Supabase Edge Functions.
- Do not run it directly from an end-user scan request.
- Do not expose it without auth/rate-limit.
- Do not run high concurrency against official sites.
- Do not store raw email content unless explicitly needed and protected.
