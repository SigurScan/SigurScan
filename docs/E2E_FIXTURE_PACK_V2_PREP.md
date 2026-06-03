# SigurScan E2E Fixture Pack v2 Prep

Status: prepared as a separate hardening pack. It is not wired into the Android test runner yet.

## Location

- Source zip: `/Users/vaduvageorge/Downloads/nudaclick_e2e_fixtures_v2_realistic.zip`
- SHA-256: `7f8bdf060e81025ff9836329f3ae3b58b45234c63c144442f3ee76537a6eaf0e`
- Repo path: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/e2e_fixtures/sigurscan_e2e_fixtures_v2_realistic`

## Prep Applied

- Renamed root folder from `nudaclick_e2e_fixtures_v2_realistic` to `sigurscan_e2e_fixtures_v2_realistic`.
- Rebranded textual fixture metadata from `NuDaClick`/`nudaclick` to `SigurScan`/`sigurscan`.
- Renamed case prefix from `NDCR-V2` to `SIGS-V2` across text references and filenames.
- Verified that all fixture paths, provider mock paths, and expected snapshot paths resolve.
- Confirmed no textual old-brand hits remain in non-binary v2 files.

## Verified Counts

- Cases: `406`
- Verdict distribution: `DO_NOT_CONTINUE=184`, `CONTINUE_WITH_CAUTION=119`, `NO_REPLY=49`, `NO_ENTER_DATA=31`, `INSUFFICIENT_EVIDENCE=17`, `VERIFY_OFFICIAL=6`
- Fixture files: `143` email, `143` HTML, `108` SMS, `49` WhatsApp, `34` call transcripts, `39` PDF, `27` QR, `99` OCR images, `184` landing pages
- Mocks: `1218` provider mocks and `406` expected evidence snapshots

## Runner Implications

V2 does not use the v1 schema directly. The runner must read:

- `expectedDecision` instead of `expected_decision`
- `fixturePaths` instead of `fixture_path`
- `providerMocks.web_risk`, `providerMocks.urlscan`, `providerMocks.virustotal` instead of one combined mock file
- `expectedSnapshotPath` as the contract for expected evidence shape

Important: run this pack with mocks only. Do not send v2 URLs to live urlscan, Google Web Risk, or VirusTotal in CI.

## Local Validation

```bash
cd /Users/vaduvageorge/AndroidStudioProjects/SigurScan
python3 tools/validate_e2e_pack.py e2e_fixtures/sigurscan_e2e_fixtures_v2_realistic --strict-branding
```
