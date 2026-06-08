# SigurScan Master Pipeline Spec

Ultima actualizare: 2026-06-08

Scop: context operational pentru pipeline-ul SigurScan.

Source of truth pentru verdict este `docs/DECISION_CONTRACT_V1.md`. Daca exista conflict intre acest document, `LAUNCH_ARCHITECTURE_FINAL.md`, `EVIDENCE_GATE_FINAL_CANDIDATE.md` sau orice logica istorica, `DECISION_CONTRACT_V1.md` castiga.

Nu mai tratam scan URL, email share, OCR, QR, Web Risk, urlscan, VirusTotal si RAG ca feature-uri separate. Ele sunt pasi intr-un singur sistem de dovezi.

## Regula centrala

SigurScan nu decide scam dintr-un singur semnal slab.

Verdictul final se decide prin:

`Extractor -> Evidence Builder -> Evidence Gate -> Decision Engine -> RAG Explanation -> User Result`

RAG-ul este consultant, nu judecator. Judecatorul este `Evidence Gate + Decision Matrix + Corpus Tests`.

## 1. Extractor

Responsabilitate: primeste input si extrage informatii. Nu decide risc.

Surse de input:

- share text/html din Gmail, Outlook, Yahoo Mail, browser, mesagerie;
- import/upload `.eml`, `.html`, `.pdf`, imagine, screenshot;
- URL manual;
- QR scan;
- OCR imagine.

Extractorul trebuie sa produca:

- text vizibil;
- HTML brut cand sistemul de share il ofera;
- linkuri vizibile;
- linkuri ascunse sub butoane, CSS, JS, form actions, redirects;
- form actions si campuri sensibile unde se poate;
- sender, subject, reply-to, return-path, headers, daca exista;
- attachment metadata;
- QR payload;
- tipul inputului: `url_only`, `message_text`, `email_html_or_eml`, `pdf`, `image_ocr`, `qr`, `unknown`.

Extractorul nu are voie sa faca:

- verdict final;
- `DANGEROUS` doar pentru link sub buton;
- `DANGEROUS` doar pentru limbaj comercial;
- brand assignment din cuvinte generice ca `voucher`, `oferta`, `promotie`, `livrare`.

## 2. Evidence Builder

Responsabilitate: construieste obiectul de dovezi care intra in gate.

Evidence minim:

- `claimed_brand`;
- `brand_confidence`;
- `visible_url`;
- `primary_url`;
- `final_url`;
- `redirect_chain`;
- `expected_official_domains`;
- `is_tracking_redirect`;
- `is_official_or_official_fallback`;
- `page_intent`: `none`, `login`, `payment`, `card`, `otp`, `identity`, `download`, `remote_access`;
- `form_action_domain`;
- `sender_domain`;
- `reply_to_domain`;
- `email_auth`: SPF/DKIM/DMARC unde exista;
- `urlscan_summary`;
- `web_risk_summary`;
- `dnsc_blacklist_summary`;
- `virus_total_summary`;
- `local_romania_signals`;
- `corpus_matches`;
- `source_conflicts`.

Evidence Builder nu decide singur. El pregateste dovezile pentru matrix.

## 3. Source Orchestration

Nu rulam tot mereu. Rulam cat trebuie pentru a obtine dovezi suficiente.

Ordine implicita:

1. Cache intern si domenii oficiale.
2. Google Web Risk.
3. Backend/local Romania rules ca semnale, nu verdict final singure.
4. urlscan pentru URL-ul principal, cu `visibility=unlisted` si URL sanitizat.
5. VirusTotal doar fallback.

VirusTotal ruleaza doar daca:

- urlscan nu este gata sau este indisponibil;
- urlscan este neclar;
- Web Risk este clean, dar exista semnale medii/puternice locale;
- domeniul este necunoscut/suspect;
- exista conflict intre surse;
- userul cere analiza extinsa.

## 4. Evidence Gate

Evidence Gate decide daca avem suficiente dovezi pentru verdict final.

Output gate:

- `HAS_ENOUGH_EVIDENCE`
- `NEEDS_MORE_INFO`
- `CONFLICTING_EVIDENCE`

Daca gate-ul nu are dovezi suficiente, userul vede:

- `Nu pot verifica suficient`
- `Verifica pe canalul oficial`, daca exista context sensibil si lipsesc datele finale.

Nu afisam `safe` si nu afisam `dangerous` fara dovezi reale.

## 5. Decision Engine

Decision Engine este determinist si se bazeaza pe `docs/EVIDENCE_GATE_MATRIX.md`.

Clase interne:

- `LOW_RISK`
- `SUSPICIOUS`
- `DANGEROUS`
- `UNKNOWN`

Actiuni user-facing:

- `Poti continua cu prudenta`
- `Nu continua`
- `Nu introduce date`
- `Nu raspunde`
- `Verifica pe canalul oficial`
- `Nu pot verifica suficient`

## 6. RAG Explanation

RAG/corpus poate:

- compara cu cazuri reale;
- explica de ce un semnal conteaza;
- sugera intrebari de clarificare;
- genera text uman pentru motive.

RAG/corpus nu poate:

- decide verdict final singur;
- transforma marketing normal in scam;
- contrazice Web Risk/urlscan/DNSC fara dovezi;
- inventa brand sau domeniu oficial.

Politica detaliata: `docs/RAG_POLICY.md`.

## 7. User Result

Userul vede deasupra fold-ului:

- decizia mare;
- 1-2 motive simple;
- domeniul final;
- preview securizat urlscan cand exista;
- actiunea recomandata.

Detaliile tehnice stau ascunse:

- VirusTotal engines;
- Web Risk raw threat types;
- urlscan raw;
- IP/server/ASN;
- redirect chain complet;
- rule IDs;
- blacklist source.

## 8. Documente sursa de adevar

- Arhitectura finala Launch Candidate v1: `docs/LAUNCH_ARCHITECTURE_FINAL.md`
- Pipeline complet: `docs/MASTER_PIPELINE_SPEC.md`
- Matrix verdict: `docs/EVIDENCE_GATE_MATRIX.md`
- Corpus schema: `docs/SCAM_FAMILY_CORPUS_SCHEMA.md`
- RAG policy: `docs/RAG_POLICY.md`
- Domenii oficiale: `docs/OFFICIAL_DOMAINS_REGISTRY.md`
- Acceptance tests Romania: `docs/ACCEPTANCE_TESTS_ROMANIA.md`
- Executie Android curenta: `docs/FINAL_ANDROID_SCAN_PIPELINE_EXECUTION.md`
