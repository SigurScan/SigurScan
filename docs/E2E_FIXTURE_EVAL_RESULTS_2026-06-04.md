# E2E Fixture Evaluation Results - 2026-06-04

Scope: SigurScan backend provider gate + Romania corpus + official registry, evaluated with mocked provider pillars. No live URLScan, Google Web Risk, or VirusTotal calls were made for fixture packs.

## Results

| Pack | Cases | Passed | Failed | Pass rate | Danger precision | Danger recall | FP guards | FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| v1 | 143 | 138 | 5 | 96.50% | 96.39% | 97.56% | 0 | 0 |
| v2 realistic/brutal | 406 | 406 | 0 | 100.00% | 100.00% | 100.00% | 0 | 0 |

## Remaining v1 Differences

These are not counted as production blockers for the current sprint because v2 is the stricter launch-grade pack and backend/Android verification is green.

- `OCR003`, `OCR006`: runner limitation. The Python/JVM fixture runner does not perform OCR because local `tesseract` is unavailable; Android OCR/provider flow must cover these at device/integration level.
- `TIMEOUT001`, `VERIFY001`, `VERIFY004`: policy difference. v1 expects `VERIFY_OFFICIAL`, while the current SigurScan gate returns `PERICULOS` for neoficial courier/postal lookalike domains with tracking/status claims. This is intentionally stricter and aligns with the newer anti-false-positive/anti-false-negative policy.

## Changes Validated By This Run

- Official registry expanded for realistic positive brands used in v2: Bolt, Fashion Days, Mega Image, DPD, Netflix, Spotify, Electrica.
- Official safety education is no longer treated as a scam signal when the destination is official and provider pillars are clean.
- Direct sensitive requests on official domains remain `SUSPECT` instead of being incorrectly marked safe.
- Unknown/nonofficial destinations with sensitive paths such as `/card`, `/cod`, `/date`, `/form`, `/login`, or `/identitate` are escalated.
- Text-only Romania social scams can be escalated by corpus/gate when there is no URL to scan.

## Verification Commands

```bash
python3 backend/eval/e2e_fixture_runner.py --pack e2e_fixtures/sigurscan_e2e_fixtures_v1 --output build/reports/e2e_v1_full.json
python3 backend/eval/e2e_fixture_runner.py --pack e2e_fixtures/sigurscan_e2e_fixtures_v2_realistic --output build/reports/e2e_v2_full.json
cd backend && pytest -q
JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" ./gradlew :app:testDebugUnitTest :app:assembleDebug
```

For strict launch regression, v2 must remain zero-failure:

```bash
python3 backend/eval/e2e_fixture_runner.py --pack e2e_fixtures/sigurscan_e2e_fixtures_v2_realistic --output build/reports/e2e_v2_full.json
```

For the historical v1 pack, the five known differences above can be kept as report-only while still failing on false-positive guard failures or false negatives:

```bash
python3 backend/eval/e2e_fixture_runner.py --pack e2e_fixtures/sigurscan_e2e_fixtures_v1 --output build/reports/e2e_v1_full.json --max-failures 5
```
