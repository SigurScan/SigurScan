# SigurScan — Production Handoff to Claude Code

> **Purpose of this file.** You (Claude Code) are taking over an anti-scam detection service ("SigurScan") and must drive it to a **production deploy on Google Cloud Run**, starting from the current state of `main`. This document is the complete, self-contained plan: current state, a known deploy blocker you must fix first, hard safety constraints you must never violate, the full test + deploy sequence, and the definition of done.

> Author context: the previous agent (Notion AI) could read the repo and make MCP-based GitHub writes, but **could not** run the live test battery, build Docker images, or run `gcloud`. That is your job. Everything below was verified against `main` at commit `012bd5d8...` on 2026-06-24.

---

## 0. TL;DR — order of operations

1. **FIX THE DEPLOY BLOCKER** (Section 3): the Dockerfile does not copy `config.py`, `core/`, and `runtime_state.py`. The current image will crash on boot. This is the single thing standing between us and a working deploy.
2. **Verify locally** the image actually boots and imports (Section 4).
3. **Run the full offline test battery** (Section 5). Must be green.
4. **Run the live-providers battery** (Section 6) with real API keys.
5. **Build & deploy to Cloud Run** (Section 7).
6. **Post-deploy smoke + rollback readiness** (Section 8).
7. **Branch cleanup** (Section 9) — optional housekeeping.
8. Confirm the **Definition of Done** checklist (Section 11).

**Golden rule:** never merge / deploy on red CI, and never "invent" new detection logic. If a fix is needed in decision logic, consult the existing `main` `.py` first and keep changes minimal. See Section 2.

---

## 1. Current state (where we are)

- **Repo:** `vaduvel/SigurScan`, default branch `main`, current HEAD `012bd5d87ec189ee1ea12672eb4b6dc99f382fc1`.
- **What it is:** FastAPI anti-scam engine localized for Romania (2025–2026). Android client package `ro.sigurscan.app`. Verdicts: `SAFE` / `SUSPECT` / `DANGEROUS` / `UNVERIFIED`.
- **Recent work, already merged into `main`:**
  - **Refactor (#62/#63):** `backend/app.py` now exposes `create_app()` and a module-level `app`. Config extracted to `backend/config.py`. Shared internals extracted to `backend/core/` (`click_intelligence`, `email_auth`, `identity`, `request_security`, `scan_context`, `serialization`, `text_utils`, `url_intelligence`). `backend/main.py` is now a **backward-compat shim** that re-exports symbols for legacy imports/tests. `services/verdict_gate.py` was **not** changed by the refactor.
  - **Regex fix (#64):** executable-extension detection boundary fixed in `verdict_gate.py`. It is live on `main`.
- **Investigation status (resolved):** a large differential eval produced ~150 flagged items. Final triage: **0 real regressions**. Breakdown: 79 = stale dataset labels (in the protected cluster — do NOT "fix" by relabeling), 15 = known real bugs (already characterized; 3 intentional, correct downgrades), 35 = offline-only artifacts caused by providers being OFF in CI (env artifacts, not logic bugs). **Main logic is sound.**
- **CI:** `.github/workflows/backend-ci.yml`. Jobs: `build` + `test` (`cd backend && python -m pytest -q`). Runs in the full source tree (so it does NOT catch the Docker COPY bug in Section 3). Total tests in battery ≈ 2294 (≈2250 labeled).

### Backend layout (top-level of `backend/`)
```
app.py              # FastAPI entrypoint -> create_app(); module-level `app`
main.py             # compat shim, re-exports (legacy `from main import ...`)
config.py           # all config/env (14.9 KB)   <-- NOT copied by Dockerfile (BUG)
runtime_state.py    # engine + caches singletons  <-- NOT copied by Dockerfile (BUG)
app_config.py       # small app metadata
app_stores.py       # brand_truth_registry, urechea_ingester
api_models.py       # pydantic models
core/               # extracted internals          <-- NOT copied by Dockerfile (BUG)
routers/            # FastAPI routers (registered in app.py)
services/           # detection pipeline, verdict_gate.py, providers
data/               # datasets / registries
eval/               # offline fixture runners
Dockerfile  vercel.json  requirements.lock  conftest.py  test_*.py
```

---

## 2. HARD CONSTRAINTS — do not violate

These come directly from the product owner. Breaking any of them is worse than doing nothing.

1. **Never deploy/merge on red CI.** Owner quote: "imi strica prea mult deja in app si imi corupe logica care am construit cu greu." Stability > speed.
2. **Do NOT touch or downgrade the protected verdict clusters:** BEC / IBAN-change / payroll-diversion / ANAF / OSIM / high-value-payment ("value") families. These must keep firing `DANGEROUS`/`SUSPECT` as they do now.
3. **Move, don't rewrite.** If decision logic needs a fix: consult the existing `main` `.py`, reuse it, keep the change minimal. Do **not** invent new heuristics. Owner quote: "sa nu inventeze logica noua, ci sa se consulte cu mainul .py din main."
4. **Rejected approach (do not implement):** any rule of the form "trust Mistral when benign > 0.8" (or any LLM-confidence auto-trust that can suppress a dangerous verdict). Explicitly rejected.
5. **Never trust a tool/model self-report over the real diff/test output.** Always verify against actual `git diff` and actual test runs.
6. **Two backup branches already exist** (`backup/main-pre-refactor-2026-06-24`, `codex/main-snapshot-2026-06-23`). No third backup needed, but do not delete these two.

---

## 3. 🔴 CRITICAL FIX FIRST — Dockerfile missing modules (deploy blocker)

**Symptom you would hit if you skip this:** the Cloud Run revision builds, then **crashes on boot** with `ModuleNotFoundError: No module named 'config'` (and then `core`, `runtime_state`). CI is green because pytest runs in the full tree, not in the built image — so CI will not warn you.

**Root cause:** `uvicorn app:app` imports `app.py`, which does `import config` and `from core.request_security import security_guard`; `main.py` and the engine do `from runtime_state import ...`. The Dockerfile's `COPY` allow-list never copies `config.py`, the `core/` directory, or `runtime_state.py` (these were introduced/renamed by refactor #62, and the Dockerfile was not updated — same class of bug previously fixed in #47 for `api_models.py`/`app_config.py`).

**Current `backend/Dockerfile` COPY block:**
```dockerfile
COPY main.py app.py api_models.py app_config.py app_stores.py ./
COPY routers ./routers
COPY services ./services
COPY data ./data
COPY eval ./eval
```

**Replace it with:**
```dockerfile
COPY main.py app.py api_models.py app_config.py app_stores.py config.py runtime_state.py ./
COPY core ./core
COPY routers ./routers
COPY services ./services
COPY data ./data
COPY eval ./eval
```

**After editing, sanity-check that nothing else is missing** (catch any other top-level module imported at runtime but not copied):
```bash
cd backend
# list top-level local modules imported by the app graph vs. what the Dockerfile copies
python - <<'PY'
import ast, pathlib
local = {p.stem for p in pathlib.Path('.').glob('*.py')} | {d.name for d in pathlib.Path('.').iterdir() if d.is_dir() and (d/'__init__.py').exists()}
print('local top-level modules:', sorted(local))
PY
grep -nE '^COPY ' Dockerfile
```
Ensure every local top-level module/package that is imported at runtime (not just in tests) appears in a `COPY`. `data/` and `eval/` are already copied; `testdata/`, `tools/`, `scripts/`, `docs/`, and `test_*.py` are intentionally NOT in the image.

> Do not change application logic in this step — only the Dockerfile COPY lines. Commit as e.g. `fix(docker): copy config.py, core/, runtime_state.py into image`.

---

## 4. Verify the image locally (before any deploy)

```bash
cd backend
docker build -t sigurscan-api:handoff .

# 1) Import smoke INSIDE the image (this is what CI cannot do):
docker run --rm sigurscan-api:handoff python -c "import app; import main; from app import app as a; print('import OK', type(a))"

# 2) Boot smoke: container should start and answer health/docs:
docker run --rm -p 8080:8080 -e PORT=8080 sigurscan-api:handoff &
sleep 5
curl -fsS http://localhost:8080/openapi.json >/dev/null && echo "BOOT OK"
# (If EXPOSE_API_DOCS is disabled in prod config, hit a known router path instead.)
```
If the import smoke fails, a module is still missing from the image — go back to Section 3.

---

## 5. Offline test battery (must be green)

Run the full suite exactly as CI does, with providers OFF (offline/deterministic mode):
```bash
cd backend
export PRIVACY_SAFE_MODE=false \
       ENABLE_CLOUD_AI_EXPLANATION=false \
       ENABLE_MISTRAL_SHADOW_ADJUDICATION=false \
       ENABLE_DNS_REPUTATION=false \
       INVOICE_CACHE_HMAC_KEY=ci-test-hmac-key
python -m pytest -q
```
- Expected: full suite green (~2294 tests). 
- The 35 "offline_only" diffs from the earlier investigation are **env artifacts** (providers off) — they are expected and are NOT failures of the suite. Do not "fix" them by editing logic.
- If anything in the protected clusters (Section 2) goes from DANGEROUS/SUSPECT to SAFE, STOP — that is a regression, not a fix.

---

## 6. Live-providers battery

Same suite/behaviour but with external providers enabled and real keys present. Flip the flags on and supply secrets (see Section 7 for where prod secrets live):
```bash
cd backend
export ENABLE_CLOUD_AI_EXPLANATION=true \
       ENABLE_MISTRAL_SHADOW_ADJUDICATION=true \
       ENABLE_DNS_REPUTATION=true
# plus the real keys (examples; use the project's actual secret names):
#   MISTRAL_SEMANTIC_API_KEY, URLSCAN_API_KEY, Google Vision creds, Gemini key, Supabase keys, etc.
python -m pytest -q -m "live or smoke"   # adjust marker to the repo's live markers
# Also exercise the dedicated live smoke runner if present:
python -m pytest -q backend/test_live_provider_smoke_runner.py
```
- Watch the known real-bug IDs to confirm they still behave correctly (7× IBAN-change BEC `B2B-R2-T0xx`, `B2B-PAYROLL-02`, `B2B-ANAF-EFACTURA-06`, `OSIM-03`, plus the 3 intentional downgrades `BRASOV-01`, `SEX-02`, `ROV-05`).
- Never wire any auto-trust of a benign LLM score (Section 2.4).

---

## 7. Build & deploy to Google Cloud Run

> Values in «angle quotes» must be confirmed against the project's actual GCP config before running. Use Secret Manager for all keys — never bake secrets into the image or env literals in source.

```bash
PROJECT=«gcp-project-id»
REGION=«europe-west1-or-actual»          # confirm the project's region
SERVICE=«sigurscan-api»                  # confirm the Cloud Run service name
AR_REPO=«artifact-registry-repo»         # confirm Artifact Registry repo
IMAGE="$REGION-docker.pkg.dev/$PROJECT/$AR_REPO/$SERVICE:$(git rev-parse --short HEAD)"

# 1) Build & push (Cloud Build) — context is backend/
gcloud builds submit backend --tag "$IMAGE"

# 2) Deploy. Map every provider secret from Secret Manager (do NOT inline values):
gcloud run deploy "$SERVICE" \
  --image "$IMAGE" \
  --region "$REGION" \
  --platform managed \
  --port 8080 \
  --set-env-vars "ENABLE_CLOUD_AI_EXPLANATION=true,ENABLE_MISTRAL_SHADOW_ADJUDICATION=true,ENABLE_DNS_REPUTATION=true" \
  --set-secrets "MISTRAL_SEMANTIC_API_KEY=«mistral-key»:latest,URLSCAN_API_KEY=«urlscan-key»:latest,INVOICE_CACHE_HMAC_KEY=«invoice-hmac»:latest" \
  # add: Gemini/Vision/Supabase + any others the app reads at runtime
  --no-allow-unauthenticated   # confirm desired auth posture for the public API
```
- Confirm CPU/memory/concurrency/min-instances against expected load before going live.
- `vercel.json` exists (legacy/preview path → `app.py`). Cloud Run is the production target; keep them consistent on `app:app`.

---

## 8. Post-deploy smoke + rollback

```bash
URL=$(gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)')
curl -fsS "$URL/openapi.json" >/dev/null && echo "PROD BOOT OK"
# Run 2–3 representative scans against the live URL: one clearly SAFE, one known DANGEROUS
# (e.g. an IBAN-change BEC sample), one UNVERIFIED. Confirm verdicts match offline expectations.
```
Rollback if anything regresses:
```bash
gcloud run services update-traffic "$SERVICE" --region "$REGION" --to-revisions «PREVIOUS_REVISION»=100
```
Prefer a canary split (e.g. 10% → 100%) if the project supports it. Do not send 100% traffic to a new revision until the live smoke passes.

---

## 9. Branch cleanup (housekeeping — optional)

41 branches exist. **Keep:** `main`, `backup/main-pre-refactor-2026-06-24`, `codex/main-snapshot-2026-06-23`, and the open-PR branches `chore/infra-p0-hardening` (#56), `codex/release-candidate-scan-audit-2026-06-22` (#57), `codex/android-invoice-safe-copy-2026-06-23` (#60).

**Safe to delete (merged or closed-and-decided):**
```bash
git push origin --delete \
  fix/executable-extension-regex-boundary fix/text-pipeline-privacy-hardening \
  fix/brace-url-bugs fix/invoice-cui-suppresses-brand-mismatch \
  fix/invoice-soft-semantic-override codex/live-smoke-input-types-2026-06-20 \
  codex/offline-eval-invoice-route-2026-06-20 codex/invoice-iban-research \
  codex/opus-se-callback-precision-clean codex/romania-research-2026-06-16 \
  feature/moatos-pr0-pr4-clean-2026-06-13 feature/real-scam-cases-2026-06 \
  fix/relabel-stale-eval-v1 fix/share-intent-production-hardening ai-write-test
```
**Decide manually:** `fix/scan-pipeline-hardening-2026-06-13` (#10, had unmerged fixes), `fix/urlscan-preview-deadline` (#59, superseded). 
**~19 no-PR experimental branches:** verify with `git branch -r --merged main` before deleting.

---

## 10. Reference

### Runtime env flags (read by the app)
`PRIVACY_SAFE_MODE`, `ENABLE_CLOUD_AI_EXPLANATION`, `ENABLE_MISTRAL_SHADOW_ADJUDICATION`, `ENABLE_DNS_REPUTATION`, `INVOICE_CACHE_HMAC_KEY`, `MISTRAL_SEMANTIC_API_KEY`, `URLSCAN_API_KEY`, `EXPOSE_API_DOCS`, plus Gemini/Vision/Supabase/Cloud Tasks settings (see `config.py` and `.env.example`).

### Decision logic (do not rewrite — Section 2)
- `services/verdict_gate.py`: deterministic 4-state `verdict(bundle)`. Provider-malicious fires DANGEROUS first; then identity-spoof, young-domain/invalid-SSL, sensitive-wrong-channel / high-value-request, insufficient-evidence, social-engineering, campaign match, semantic high-risk, then SAFE, then residual.
- `verdict_gate_constants.py`: `HARD_SENSITIVE_REQUESTS` (card, cvv, otp, password, pin, cnp, iban, crypto, remote, apk, id_document), `WRONG_CHANNELS`, `DANGEROUS_SEMANTIC_FAMILIES`, `ESTABLISHED_DOMAIN_AGE_DAYS=365`, `CAMPAIGN_MATCH_HIGH_CONFIDENCE_THRESHOLD=0.82`.
- Invoice orchestration: `HIGH_VALUE_UNCONFIRMED_PAYMENT_RON=5000` (foreign 1000).

### Datasets
Primary: `backend/data/evaluation_dataset_v1.jsonl` (fields: `id, text, brand, channel, expected_label, identity_status, sensitive, actual_is_scam`). Other (some stale): `verdict_testset_ro.jsonl`, `hard_eval.jsonl`, `minor_scam_families_addendum.json`, `web_redteam_scam_fixtures.json`, plus zipped corpora. `RO00TEST*` fixtures are test placeholders (low-priority cleanup).

### Known follow-ups (not blockers)
- **#56**: CI runner Python 3.11 → 3.12 bump + eval-gate wiring (needs `workflows` permission).
- Optional: rewrite `RO00TEST*` fixtures; GTM/monetization docs.

---

## 11. Definition of Done (production-ready)

- [ ] Dockerfile fix applied; image builds and **imports/boots** (Section 4).
- [ ] Offline battery green (~2294) with providers OFF (Section 5).
- [ ] Live-providers battery green with real keys; protected clusters still DANGEROUS/SUSPECT (Section 6).
- [ ] Image pushed to Artifact Registry; Cloud Run revision deployed with secrets via Secret Manager (Section 7).
- [ ] Post-deploy live smoke passes (SAFE / DANGEROUS / UNVERIFIED samples correct); rollback path confirmed (Section 8).
- [ ] No constraint from Section 2 violated; no new detection heuristics invented; CI green at the deployed commit.
- [ ] (Optional) Branch cleanup done (Section 9).

When all boxes above are checked, SigurScan is production-ready on Cloud Run.
