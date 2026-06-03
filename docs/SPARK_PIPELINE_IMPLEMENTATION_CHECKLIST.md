# SigurScan - Spark Pipeline Implementation Checklist

Ultima actualizare: 2026-06-02

Scop: checklist practic pentru transformarea master pipeline-ului in implementare Android/backend. Acest document nu inlocuieste `MASTER_PIPELINE_SPEC.md`; il operationalizeaza.

## 0. Regula de lucru

Nu implementa reguli noi de risc fara:

- caz in corpus;
- expected verdict;
- test/fixture;
- verificare false-positive pe Uber/eMAG/FAN real.

## 1. Extractor

Status dorit:

- Share Intent citeste text simplu.
- Share Intent citeste HTML cand este primit.
- Share Intent citeste stream/atasament cand sistemul il ofera.
- HTML parser extrage `href`, linkuri vizibile, butoane, `formaction`, `data-*`, redirect hints, `meta refresh`, JS basic redirect.
- Webmail shell links sunt ignorate cand nu reprezinta corpul emailului.

Acceptance:

- email Uber real: extrage butonul `Comanda o cursa` si URL-ul `rides.sng.link`.
- Yahoo/Gmail shell fara corp real: nu produce `Mail cu link ascuns`.
- text simplu cu URL: pastreaza URL-ul principal.

## 2. Normalizer and Primary URL Picker

Status dorit:

- normalizeaza URL-uri cu/without schema;
- elimina punctuation final;
- converteste host case-insensitive;
- redacteaza query params sensibili pentru sandbox;
- alege URL-ul principal dupa context: CTA principal, link vizibil, final URL potential, brand claim.

Acceptance:

- daca exista un singur link in buton principal, acela devine `primary_url`.
- daca exista multe resource links webmail, acestea nu devin `primary_url`.
- daca linkul vizibil difera de `href`, marcheaza mismatch ca evidence, nu verdict direct.

## 3. Scan Orchestrator

Ordine recomandata:

1. Cache intern.
2. Official domains registry.
3. Web Risk.
4. Blacklist/DNSC/ANPCDNS provider, daca exista feed stabil.
5. urlscan pentru URL-ul principal.
6. VT fallback doar daca gate-ul nu are destule dovezi sau exista conflict.
7. RAG explainer dupa verdict intern sau `UNKNOWN`.

Acceptance:

- daca Web Risk confirma malware/phishing, poate opri devreme cu `DANGEROUS`, dar urlscan preview poate continua async pentru UX.
- daca urlscan este clar si Web Risk/blacklist nu contrazic, VT nu ruleaza default.
- daca urlscan nu este gata si contextul este sensibil, VT poate rula fallback.

## 4. urlscan Preview

Status dorit:

- ruleaza default doar pe `primary_url`;
- foloseste `unlisted/private`;
- sanitizeaza PII/tokenuri;
- cache pe URL normalizat/final URL;
- polling cu backoff;
- UI arata preview cand exista si fallback cand lipseste.

Acceptance:

- preview indisponibil nu inseamna `safe`.
- preview indisponibil fara alte dovezi suficiente inseamna `Nu pot verifica suficient`.
- urlscan malicious inseamna semnal puternic.

## 5. Evidence Builder

Trebuie sa produca minimum:

- `input_type`;
- `claimed_brand`;
- `brand_confidence`;
- `primary_url`;
- `final_url`;
- `redirect_chain`;
- `visible_vs_actual_mismatch`;
- `official_domain_match`;
- `page_intent`;
- `form_action_domain`;
- `sender_domain` si `reply_to_domain`, daca exista;
- `web_risk_summary`;
- `urlscan_summary`;
- `blacklist_summary`;
- `vt_summary`, daca a rulat;
- `weak_signals`, `medium_signals`, `strong_signals`;
- `source_conflicts`.

## 6. Evidence Gate

Reguli obligatorii:

- weak signals singure nu dau `DANGEROUS`;
- marketing urgency singur nu da `DANGEROUS`;
- tracking link legitim cu fallback oficial nu da `DANGEROUS`;
- brand mismatch + cerere date sensibile poate da `DANGEROUS`;
- blacklist/Web Risk/urlscan malicious pot da `DANGEROUS`;
- lipsa final URL duce la `UNKNOWN` sau `Nu pot verifica suficient`, nu verdict final ferm.

Acceptance:

- Uber real promo nu devine eMAG scam.
- eMAG real newsletter nu devine eMAG fake doar pentru voucher/promotie.
- FAN fake cu domeniu neoficial + plata/card devine `DANGEROUS`.
- ANAF fake cu link extern + login/plata/date devine `DANGEROUS`.

## 7. Decision Engine

Mapare interna -> user-facing:

- `LOW_RISK` -> `Poti continua cu prudenta`.
- `DANGEROUS` + page intent data/payment -> `Nu introduce date`.
- `DANGEROUS` + link/social engineering -> `Nu continua` sau `Nu apasa`.
- `DANGEROUS` + email asking reply/data -> `Nu raspunde`.
- `SUSPICIOUS` -> `Verifica pe canalul oficial`.
- `UNKNOWN` -> `Nu pot verifica suficient`.

Nu folosi `suspect` ca raspuns final principal pentru user.

## 8. RAG Explainer

RAG primeste:

- verdict intern;
- evidence summary;
- corpus snippets;
- missing evidence.

RAG nu primeste:

- tokenuri/session IDs;
- date card/parole/OTP;
- email complet cu PII fara redaction.

RAG produce:

- 1-2 motive simple;
- explicatie extinsa optionala;
- cazuri similare pentru suport intern.

RAG nu produce:

- verdict final nou;
- scor nou;
- domenii oficiale inventate;
- promisiuni absolute.

## 9. UI Result

Above the fold:

- preview securizat;
- decizie concreta;
- domeniul final;
- 1-2 motive simple;
- actiunea recomandata.

Hidden by default:

- VirusTotal engines;
- Web Risk raw;
- urlscan raw;
- IP/server/ASN;
- redirect chain complet;
- rule IDs;
- blacklist source.

## 10. Test Pack Minim

Ruleaza pe fixture/corpus:

- Uber real promo tracking;
- Uber fake card;
- eMAG real newsletter;
- eMAG fake premiu/card;
- FAN real tracking;
- FAN fake taxa;
- ANAF fake SPV;
- Revolut visible link mismatch;
- Web Risk malware test;
- example.com;
- urlscan unavailable;
- marketing urgency benign.

## 11. Release Guardrails

- Cheile API nu raman hardcodate in APK.
- Web Risk preferat pentru comercial, nu Safe Browsing v4 direct.
- urlscan `unlisted/private`.
- Privacy Policy declara serviciile terte.
- Nu promite `100% sigur`.
- Nu cere permisiuni SMS/Call Log/Accessibility in versiunea light.
