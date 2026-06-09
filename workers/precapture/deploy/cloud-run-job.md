# Cloud Run Job deploy notes

Recommended production shape: run this as a Cloud Run Job, not as a user-facing request handler.
The job starts, captures a batch, uploads previews to Supabase, then exits.

## Build and push

```bash
PROJECT_ID="your-gcp-project"
REGION="europe-west1"
IMAGE="gcr.io/$PROJECT_ID/sigurscan-precapture:1.1.0"

gcloud builds submit --tag "$IMAGE"
```

## Create/update job

```bash
gcloud run jobs deploy sigurscan-precapture \
  --image "$IMAGE" \
  --region "$REGION" \
  --memory 2Gi \
  --cpu 2 \
  --task-timeout 1800 \
  --set-env-vars STORAGE_BUCKET=previews,CACHE_TABLE=fast_preview_cache,CACHE_TTL_DAYS=14,CONCURRENCY=1 \
  --set-secrets SUPABASE_URL=supabase-url:latest,SUPABASE_SERVICE_KEY=supabase-service-key:latest \
  --args="--email-source","./samples/official_preview_targets.ro.json","--out-dir","./output","--concurrency","1","--nav-timeout-seconds","20"
```

## Execute manually

```bash
gcloud run jobs execute sigurscan-precapture --region "$REGION" --wait
```

## Scheduling
Use Cloud Scheduler to execute the job via IAM-authenticated call, or keep scheduling in GitHub Actions for simple daily runs.
