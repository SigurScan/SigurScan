# SigurScan Sprint S+1 Execution Report - 2026-06-04

Scope: Detection Quality + Observability + cleanup #67 on top of commit `6a05c64`, delivered on `main` through `dda1b92` plus current follow-up changes.

## Definition Of Done Status

| Item | Status | Evidence |
| --- | --- | --- |
| Detection wiring flagged and covered by tests | Done | Backend provider gate tests cover VT decisive risk, urlscan malicious propagation, homoglyph/typosquat/registry/official-domain behavior and false-positive guards. |
| Eval dataset + threshold sweep | Done for small calibration set | `backend/data/eval_dataset.jsonl` has 8 labeled rows. Best threshold `5` produced precision `1.000`, recall `1.000`, F1 `1.000`, FP `0`, FN `0`. |
| Orchestrated telemetry dashboard + alerts | Done | `/v1/orchestration/telemetry` returns metrics/alerts. `/v1/orchestration/dashboard` renders a minimal HTML dashboard over `scan_events`. |
| #67 technical debt | Done | Reclaim expiry test, bounded conflict-merge retry, TTL `ORCHESTRATED_URLSCAN_SUBMIT_RESERVATION_TIMEOUT_SECONDS=30`. |
| No regressions | Done locally | Backend, Android debug/unit, v2 fixture runner, v1 historical runner all verified. Live smoke runner is opt-in and must be rerun after deploy. |

## Threshold Sweep

Command:

```bash
python3 backend/eval/evaluate.py --disable-redirects --disable-reputation --sweep --sweep-start 0 --sweep-end 100 --sweep-step 5 --sweep-metric f1 --output build/reports/threshold_sweep_2026-06-04.json
```

Baseline/current selected threshold after sweep: `5`.

Confusion matrix at recommended threshold:

- TP: 5
- FP: 0
- FN: 0
- TN: 3

Metrics:

- Precision: 1.000
- Recall: 1.000
- F1: 1.000
- Accuracy: 1.000

Important limitation: this is a small calibration dataset, not the main launch-grade corpus. Launch regression quality is primarily guarded by the mocked E2E fixture runner, especially v2 realistic/brutal.

## E2E Regression Evidence

- v2 realistic/brutal: 406/406 passed, 0 FP guard failures, 0 false negatives.
- v1 historical: 138/143 passed with 5 documented differences, 0 FP guard failures, 0 false negatives.

Reports:

- `docs/E2E_FIXTURE_EVAL_RESULTS_2026-06-04.md`
- `build/reports/e2e_v2_full.json`
- `build/reports/e2e_v1_full.json`

## Observability Evidence

Implemented:

- Poll count to verdict.
- Stage duration buckets.
- urlscan reclaim count.
- reservation guard hits.
- urlscan pending-to-timeout rate.
- conflict merge events and retry failures.
- anomaly alerts in telemetry payload.
- minimal HTML dashboard endpoint.

Endpoints:

- `GET /v1/orchestration/telemetry`
- `GET /v1/orchestration/dashboard`

## Live Smoke

Live provider smoke remains intentionally capped and opt-in:

```bash
python3 backend/eval/live_provider_smoke_runner.py --dry-run
SIGURSCAN_RUN_LIVE_PROVIDER_SMOKE=1 python3 backend/eval/live_provider_smoke_runner.py --output build/reports/live_provider_smoke.json
```

Do not run fixture packs through live providers. Do not send `.test`, `.invalid`, or `.example` domains to provider APIs.

## Remaining Work After This Sprint

- Expand the labeled threshold dataset beyond 8 rows with real reviewed feedback.
- Run live smoke again after deploy of the latest commit.
- If observability usage grows, move the dashboard behind auth/internal access.
