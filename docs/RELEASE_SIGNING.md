# SigurScan Android Release Signing

## Status

Release signing is configured through local ignored files:

- `release/sigurscan-upload.jks`
- `keystore.properties`

These files are intentionally ignored by git and must not be committed or shared in chat.

## Build Commands

```bash
JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" ./gradlew :app:assembleRelease
JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" ./gradlew :app:bundleRelease
```

Expected artifacts:

- `app/build/outputs/apk/release/app-release.apk`
- `app/build/outputs/bundle/release/app-release.aab`

## Play Console Notes

- Package ID: `ro.sigurscan.app`
- App label: `SigurScan`
- Keep the upload keystore backed up offline. Losing it can block future updates.
- Production API keys must stay backend-side. Release `BuildConfig` provider keys must remain empty.

## Verification

Before uploading a release:

```bash
JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" ./gradlew :app:testDebugUnitTest :app:lintDebug :app:assembleRelease :app:bundleRelease
```

Then verify signing with the Android SDK `apksigner` tool.
