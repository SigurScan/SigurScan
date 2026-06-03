# Verification report - SigurScan E2E Fixtures v2 realistic

Generated/verified: 2026-06-03T05:00:14.329872+00:00

## Validation

- Cases loaded from `test_cases.json`: 406
- Missing fixture/mock/snapshot paths: 0
- Provider mock triplets generated per case: yes
- PDF sample render check: passed for representative PDFs using `render_pdf.py` at 120 DPI
- EML subject leakage check: no fixture email subjects contain `fals`, `false`, `legitim`, `conflict`, `unknown`, `fixture`, or `scam`
- Scam URLs: reserved/non-operational `.test` / `.invalid` domains
- Positive cases: may include real official domains for false-positive guarding; use mocks in CI

## Decision distribution

- DO_NOT_CONTINUE: 184
- CONTINUE_WITH_CAUTION: 119
- NO_REPLY: 49
- NO_ENTER_DATA: 31
- INSUFFICIENT_EVIDENCE: 17
- VERIFY_OFFICIAL: 6

## Fixture kind distribution

- landing: 248
- email: 143
- sms: 108
- ocr: 99
- whatsapp: 49
- pdf: 39
- call: 34
- qr: 27

## Channel distribution

- email: 145
- sms: 129
- whatsapp: 81
- call: 26
- ocr: 6
- share: 6
- pdf: 5
- paste: 5
- qr: 3

## Notes

The fixtures are intentionally realistic and do not include visible `simulation/test` disclaimers inside user-facing email/PDF/SMS bodies. Safety and ground-truth metadata are kept in JSON/docs/mocks.
