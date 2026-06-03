# SigurScan E2E Emulator Results - 2026-06-03

## Scope

Device/emulator validation for the SigurScan native Android app using:

- `e2e_fixtures/sigurscan_e2e_fixtures_v1`
- `e2e_fixtures/sigurscan_e2e_fixtures_v2_realistic`

The tests run on the Android emulator against the native Android runtime and call the deterministic `EvidenceGate`.
They use mocked provider responses from the fixture packs. They do not call live urlscan, Google Web Risk, or VirusTotal.

## Commands

```bash
JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" ./gradlew :app:testDebugUnitTest :app:assembleDebugAndroidTest :app:installDebug :app:installDebugAndroidTest

ADB=/Users/vaduvageorge/Library/Android/sdk/platform-tools/adb
$ADB shell am instrument -w -r \
  -e fixtureRoot /data/user/0/ro.sigurscan.app/files/e2e \
  -e class ro.sigurscan.app.SigurScanFixturePackDeviceE2ETest \
  ro.sigurscan.app.test/androidx.test.runner.AndroidJUnitRunner
```

## Build / Unit Status

- Debug unit tests: passed.
- Debug APK install: passed.
- Android test APK build/install: passed.

## Device E2E Results

### v1

- Total cases: 143
- Passed: 141
- Failed exact-match assertions: 2

Remaining mismatches:

- `QR005`: expected `INSUFFICIENT_EVIDENCE`, actual `VERIFY_OFFICIAL`.
  - Reason: provider mocks found a final URL and clean/no-form review, so the gate gives a useful "verify official" style action instead of "cannot verify".
- `VERIFY007`: expected `VERIFY_OFFICIAL`, actual `NO_ENTER_DATA`.
  - Reason: the fixture includes `FORM_PERSONAL_DATA_DETECTED`; SigurScan now treats personal-data collection on a non-official/unknown target as "Nu introduce date".

Assessment: these two mismatches are policy disagreements, not emulator/setup failures.

### v2

- Total cases: 406
- Passed: 370
- Failed exact-match assertions: 36

Remaining mismatch buckets:

- 25 cases: expected `NO_ENTER_DATA`, actual `DO_NOT_CONTINUE`.
  - Reason: `SANDBOX_VERDICT`; mocked urlscan verdict is phishing/malicious.
  - Final policy says urlscan malicious is hard evidence, so `DO_NOT_CONTINUE` is intentional.
- 11 cases: expected `NO_REPLY`, actual `DO_NOT_CONTINUE`.
  - Reason: `REMOTE_ACCESS_OR_APK`.
  - Final policy says remote-access/APK request is hard danger, so `DO_NOT_CONTINUE` is intentional.

Assessment: v2 remaining failures are stricter final-policy outcomes than the fixture expected decisions. They should be reviewed as fixture-policy alignment issues, not as product false positives.

## Fixes Applied During This Run

- Added device-side report generation for fixture pack tests.
- Fixed the emulator runner mapping so clean/no-form urlscan reviews emit `NO_SENSITIVE_FORM`.
- Fixed runner signal mapping:
  - Locker/address update no longer maps to payment request.
  - Generic investment/fast-gain text is weak marketing pressure, not payment by itself.
  - OTP present in a legitimate context maps to "do not reply/share code".
- Added `PERSONAL_DATA_REQUEST` to `EvidenceGate` so unknown/non-official forms asking for personal data can produce `NO_ENTER_DATA` without pretending the signal is CNP/IBAN.

## Current Honest Status

The emulator path works and the fixture packs are readable from app-private storage.
The Android runtime EvidenceGate is stable under both packs.

Not all exact fixture assertions are green yet:

- v1 exact: 141/143.
- v2 exact: 370/406.

The remaining deltas need a policy decision:

- Keep SigurScan's stricter final policy and update fixture expected decisions.
- Or relax the gate, which is not recommended for urlscan malicious or remote-access/APK cases.
