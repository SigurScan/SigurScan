# NuDaClick E2E Fixture Pack v1

Pachet de testare pentru EvidenceGate, extractori HTML/email, PrimaryUrlPicker, PII redaction, Web Risk/urlscan/VT adapters mocked, Official Domains Registry si UI user-facing.

Generated: 2026-06-03T00:00:00+00:00
Policy: gate-1.0.0
Registry seed: ro-brands-2026.06.03

## Important safety
- Toate scam URL-urile folosesc domenii rezervate `.test`, `.invalid`, `.example`; nu sunt linkuri reale de phishing.
- Nu trimite fixture-urile ca emailuri reale.
- Pentru testele E2E folosește provider mocks din `mocks/providers/`; nu submita automat aceste URL-uri la servicii externe.
- Fixture-urile sunt sintetice, dar bazate pe tipare publice documentate pentru România.

## Conținut
- `test_cases.json` - sursa de adevăr pentru runner.
- `test_cases.csv` - index rapid.
- `fixtures/sms/*.txt` - SMS/paste/share text.
- `fixtures/whatsapp/*.txt` - mesaje WhatsApp / familie / OTP.
- `fixtures/call_transcripts/*.txt` - descrieri/transcrieri user-initiated pentru vishing; aplicația nu monitorizează apeluri.
- `fixtures/email/*.eml` - emailuri HTML cu linkuri ascunse, butoane, multiple linkuri, legit marketing.
- `fixtures/pdf/*.pdf` - PDF-uri cu text/link annotations.
- `fixtures/qr/*.png` - QR-uri cu URL-uri safe pentru test.
- `fixtures/ocr_images/*.png` - capturi simulate pentru OCR local.
- `registry/official_domains_seed.json` - registry minim pentru teste.
- `corpus/scam_scenario_corpus_seed.json` - corpus de scenarii sociale.
- `mocks/providers/*.json` - stări mocked pentru Web Risk, urlscan, VirusTotal.

## Total cazuri
143 cazuri.

### Pe decizie
- `CONTINUE_WITH_CAUTION`: 32
- `DO_NOT_CONTINUE`: 50
- `INSUFFICIENT_EVIDENCE`: 14
- `NO_ENTER_DATA`: 16
- `NO_REPLY`: 16
- `VERIFY_OFFICIAL`: 15

### Pe grup
- `call_transcript_user_initiated`: 4
- `conflict_resolution`: 8
- `dangerous_url_sms`: 20
- `email_hidden_link`: 4
- `email_legit_marketing`: 2
- `email_primary_picker`: 1
- `false_positive_legit`: 10
- `legit_false_positive_guard`: 10
- `no_enter_data`: 10
- `no_reply_social`: 10
- `ocr_image`: 10
- `pdf_upload`: 12
- `qr_scan`: 10
- `timeout_fallback`: 8
- `unknown`: 8
- `unknown_input`: 1
- `verify_official_capped`: 10
- `whatsapp_takeover`: 5


## Contract minimal runner
Pentru fiecare test:
1. Încarcă fișierul din `fixture_path`.
2. Simulează input-ul indicat de `input_type`.
3. Rulează extractorii locali + EvidenceGate local.
4. Injectează mock-ul providerului din `provider_mock_path` în backend/adapters.
5. Verifică:
   - `expected_decision`
   - `expected_user_label`
   - `primary_url_expected` dacă există
   - `expected_signal_kinds` subset în EvidenceSnapshot
   - `should_submit_external` respectat de PII redaction/privacy gate
6. Pentru cazurile `timeout_fallback`, verifică UI la 3s/8s/30s conform policy-ului tău.

## Recomandare de naming în test suite
- Android instrumented tests: `NuDaClickE2E_<CASE_ID>()`
- Backend contract tests: `EvidenceGateContract_<CASE_ID>()`
- Parser unit tests: `ExtractorFixture_<CASE_ID>()`
