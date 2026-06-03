# SigurScan E2E Fixtures v2 - realistic hard pack

Generated: 2026-06-03T04:59:06.476332+00:00

This package contains synthetic but highly realistic Romanian scam-checking fixtures for SigurScan.
It includes both scam-like negative cases and legitimate positive/false-positive-guard cases.

## Safety constraints

- Scam URLs use reserved/non-operational domains such as `.test`, `.invalid`, and `.example`.
- Positive cases may contain real official brand domains for false-positive testing. Use provider mocks in CI.
- Do not submit these fixtures to live urlscan/Web Risk/VirusTotal during automated tests.
- The content intentionally mimics real scam pressure patterns, but it is generated for defensive testing only.
- No real logos, images, credentials, cards, CNPs, OTPs, or live phishing infrastructure are included.

## Counts

- Total cases: 406
- Decisions: {'DO_NOT_CONTINUE': 184, 'NO_ENTER_DATA': 31, 'NO_REPLY': 49, 'CONTINUE_WITH_CAUTION': 119, 'INSUFFICIENT_EVIDENCE': 17, 'VERIFY_OFFICIAL': 6}
- Channels: {'email': 145, 'sms': 129, 'whatsapp': 81, 'call': 26, 'qr': 3, 'pdf': 5, 'ocr': 6, 'share': 6, 'paste': 5}
- Categories: top 20 shown in docs/case_index.md

## Important files

- `test_cases.json` - primary runner index
- `test_cases.csv` - quick review table
- `registry/official_domains_seed_realistic_v2.json`
- `corpus/scam_scenario_corpus_seed_realistic_v2.json`
- `mocks/providers/*` - deterministic provider mocks per case
- `docs/implementation_guide.md`
- `docs/case_index.md`
- `docs/source_basis.md`
- `docs/test_runner_contract.md`

## Intended E2E flow

1. Load fixture file from `fixturePaths`.
2. Run SigurScan extractor/PrimaryUrlPicker/PII redaction.
3. Use provider mocks by `case.id`, not live services.
4. Normalize provider outputs into EvidenceSignals.
5. Evaluate EvidenceGate.
6. Assert `expectedDecision`, key `expectedSignals`, and `expectedUserLabel`.
