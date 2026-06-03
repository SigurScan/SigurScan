# SigurScan E2E Fixture Pack Integration

Ultima actualizare: 2026-06-03

## Fixture pack

Pachetul v1 este extras local aici:

`/Users/vaduvageorge/Desktop/SigurScan/e2e_fixtures/sigurscan_e2e_fixtures_v1`

Zip sursa:

`/Users/vaduvageorge/Downloads/sigurscan_e2e_fixtures_v1.zip`

SHA-256:

`25f43aa42f0a96b4e1c009ee37f55b48e14073076a961ee5aeb1d14e289cb0a4`

## Ce ruleaza automat in JVM unit tests

Test nou:

`app/src/test/java/com/example/myapplication/SigurScanFixturePackE2ETest.kt`

Acopera:

- integrity pentru toate cele 143 cazuri;
- existenta fixture/mock pentru toate cazurile;
- safe-domain guard pentru URL-uri;
- contract EvidenceGate pentru cele 110 cazuri text si HTML/email care pot rula fara emulator;
- provider mocks pentru Web Risk, urlscan si VirusTotal, fara apeluri externe reale.

Comanda:

```bash
JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" ./gradlew :app:testDebugUnitTest --tests ro.sigurscan.app.SigurScanFixturePackE2ETest
```

## Ce nu pretinde testul JVM

PDF/QR/OCR sunt validate ca fixture pack si ca mock contract, dar imaginile/PDF-urile nu sunt scanate efectiv in JVM. Scanarea reala a binarelor necesita instrumented tests/emulator sau un runner separat cu ML Kit/PDF extractor.

Nu trimite fixture-urile catre urlscan/Web Risk/VirusTotal in CI. Se folosesc doar `mocks/providers`.
