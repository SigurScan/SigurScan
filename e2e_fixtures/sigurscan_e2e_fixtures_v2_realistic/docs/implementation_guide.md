# SigurScan v2 Fixture Pack - Implementation Guide

## Assertions per case

For each entry in `test_cases.json` assert:

1. Extractor output:
   - hidden links are found in `.eml` and HTML fixtures;
   - OCR images return enough text to detect scenario patterns;
   - PDFs are accepted by import/upload flow;
   - QR images extract the encoded URL.

2. PrimaryUrlPicker:
   - chooses `primaryUrl` when present;
   - does not choose unsubscribe/privacy/footer links in marketing emails;
   - chooses hidden CTA href over visible text when they differ;
   - returns null for text-only family/phone scams.

3. PII redaction:
   - removes OTP, email query params, tokens, CNP-like strings, card-like strings;
   - sets provider status `SKIPPED_PRIVACY` when unsafe.

4. Provider mocks:
   - load `mocks/providers/web_risk/{id}_web_risk.json`;
   - load `mocks/providers/urlscan/{id}_urlscan.json`;
   - load `mocks/providers/virustotal/{id}_virustotal.json`.

5. EvidenceGate:
   - expected final decision equals `expectedDecision`;
   - RAG/AI is not allowed to alter the decision;
   - positive cases must not become `DO_NOT_CONTINUE` unless the mock explicitly says high-confidence malicious.

## Hard false-positive guards

The positive cases intentionally include:

- marketing words: ofertă, reducere, voucher;
- legitimate tracking links;
- official courier and invoice notices;
- bank security messages mentioning OTP/CVV/PIN as warnings;
- official public-sector notifications that tell the user to open the official portal manually.

These should generally result in `CONTINUE_WITH_CAUTION` or safe `NO_REPLY` for OTP-only messages, not `DO_NOT_CONTINUE`.

## Text-only social scam guards

Cases in Senior family scam and Official phone spoofing often have no URL. The expected result is normally `NO_REPLY`.
Do not return `INSUFFICIENT_EVIDENCE` just because no URL exists if the message asks for money/codes or impersonates family/institutions.
