# SigurScan - GPT 5.5 Pro 8PM Master Pipeline Brief

Ultima actualizare: 2026-06-02

Scop: prompt/handoff pentru sesiunea GPT 5.5 Pro Web. Foloseste acest document impreuna cu fisierele sursa din `docs/` ca sa obtii un pipeline final, disciplinat si implementabil.

## Context produs

SigurScan este o aplicatie Android de scam checking pentru Romania. Userul poate incarca, importa sau face share catre aplicatie din email, browser, mesagerie, fisiere, imagini sau QR.

Produsul nu trebuie sa fie laborator cyber. Produsul trebuie sa raspunda simplu la intrebarea userului:

- pot continua?
- pot apasa?
- pot raspunde?
- pot introduce date?
- trebuie sa verific pe canalul oficial?

Moat-ul principal este preview-ul securizat: aratam vizual unde duce linkul fara ca userul sa intre pe site.

## Directia de produs

SigurScan trebuie sa fie decisiv in actiune, dar prudent in promisiuni.

Corect:

- `Nu continua`
- `Nu apasa`
- `Nu introduce date`
- `Nu raspunde`
- `Verifica pe canalul oficial`
- `Poti continua cu prudenta`
- `Nu pot verifica suficient`

Incorect:

- `100% sigur`
- `garantat legitim`
- `site sigur`
- `oferta este sigur reala`
- `detectam toate scamurile`

Intern poate exista `SUSPICIOUS`, dar UI-ul final nu trebuie sa lase userul blocat cu un raspuns vag. Daca riscul este intermediar, user-facing trebuie sa fie o actiune clara: `Verifica pe canalul oficial`.

## Flow dorit

1. Userul incarca/importa/face share prin metodele existente.
2. Aplicatia extrage text, HTML, linkuri vizibile, linkuri ascunse, butoane, `href`, `formaction`, redirect hints, sender, subject, reply-to, QR si atasamente unde se poate.
3. Aplicatia normalizeaza URL-urile si alege URL-ul principal.
4. Aplicatia ruleaza pilonii in cascada si dependent, nu toate serviciile mereu.
5. `urlscan.io` ruleaza pentru URL-ul principal si produce preview, final URL, redirect chain si verdict sandbox.
6. Google Web Risk si blacklist-urile sunt verificari rapide/puternice.
7. VirusTotal ruleaza doar ca fallback/intaritor cand sursele sunt neclare sau contradictorii.
8. Contextul Romania, lista domeniilor oficiale, scam families, offer checker si RAG-ul explica si completeaza contextul.
9. Evidence Gate decide daca avem suficiente dovezi pentru verdict.
10. UI afiseaza snapshot/preview + decizie concreta + 1-2 motive simple.
11. Detaliile tehnice apar doar la cerere.

## Ce nu trebuie sa produca verdict periculos singur

Acestea sunt semnale slabe. Ele pot declansa analiza, dar nu verdict `DANGEROUS`:

- HTML email;
- link sub buton;
- tracking link;
- link scurt fara alta dovada;
- `profita acum`;
- `ultima sansa`;
- `nu rata`;
- `voucher`;
- `promotie`;
- `reducere`;
- `oferta limitata`;
- newsletter marketing.

Marketingul legitim foloseste aceste patternuri. SigurScan trebuie sa scaneze destinatia reala, nu sa acuze limbajul comercial.

## Dovezi care pot decide risc real

Semnale puternice:

- Web Risk confirma malware/phishing/social engineering;
- DNSC/ANPCDNS/blacklist match;
- urlscan verdict malicious;
- VirusTotal malicious cu motoare relevante, mai ales cand alte surse sunt neclare;
- brand mismatch clar;
- final URL neoficial cere card, OTP, parola, CNP, IBAN, login sau plata;
- form action trimite date catre domeniu dubios/neoficial;
- link vizibil zice un domeniu oficial, dar final URL duce in alta parte;
- sender/from/reply-to/auth nu corespund brandului, daca avem email headers;
- domeniul final nu este in lista domeniilor oficiale pentru brandul pretins si cere date sensibile.

## Cei 5 piloni SigurScan

### 1. Share/import/upload + extractor avansat

Rol: aduce datele corecte in sistem.

Include:

- Share Intent;
- HTML email parsing;
- linkuri ascunse sub butoane;
- text vizibil;
- QR/OCR;
- fisiere/atasamente unde se poate.

Nu decide verdict.

### 2. urlscan sandbox + preview securizat

Rol: moat principal.

Include:

- final URL;
- redirect chain;
- screenshot/preview;
- verdict urlscan;
- server/page summary.

Trebuie folosit cost-aware:

- un singur URL principal default;
- cache;
- `unlisted/private`;
- sanitizare PII/tokenuri;
- fallback `Preview indisponibil momentan`.

### 3. Reputation and blacklist checks

Rol: confirmare externa rapida.

Include:

- Google Web Risk;
- DNSC/ANPCDNS/blacklist daca exista feed stabil;
- VirusTotal fallback;
- cache intern.

VT nu se ruleaza la fiecare scanare daca urlscan/Web Risk/gate sunt suficiente.

### 4. Context Romania + scam families + official domains

Rol: reduce false positives si detecteaza cazuri locale.

Include:

- FAN Courier fake;
- ANAF/SPV fake;
- Poșta Romana fake;
- banci/OTP/card;
- OLX/marketplace;
- WhatsApp takeover;
- remote access fraud;
- eMAG fake;
- lista domeniilor oficiale.

Regula critica: brandul nu se decide din keywords generice. `voucher`, `livrare`, `colet`, `promotie`, `plata`, `cod` nu sunt suficiente pentru familie/brand.

### 5. Offer checker + RAG explainer + user decision

Rol: explica si transforma dovezile intr-un raspuns clar.

Offer checker nu spune automat `oferta e falsa`. Spune:

- `Nu am gasit confirmare oficiala`;
- `Oferta cere date pe domeniu neoficial`;
- `Verifica direct in aplicatia/site-ul oficial`;
- `Semnale de oferta inselatoare`.

RAG-ul este consultant, nu judecator. Verdictul vine din Evidence Gate + Decision Matrix + corpus tests.

## Documente deja pregatite

GPT 5.5 Pro trebuie sa citeasca si sa revizuiasca aceste fisiere:

- `docs/MASTER_PIPELINE_SPEC.md`
- `docs/EVIDENCE_GATE_MATRIX.md`
- `docs/RAG_POLICY.md`
- `docs/SCAM_FAMILY_CORPUS_SCHEMA.md`
- `docs/OFFICIAL_DOMAINS_REGISTRY.md`
- `docs/ACCEPTANCE_TESTS_ROMANIA.md`
- `docs/FINAL_ANDROID_SCAN_PIPELINE_EXECUTION.md`

## Cerere exacta pentru GPT 5.5 Pro Web

Foloseste promptul de mai jos:

```text
Vreau sa revizuiesti si sa perfectionezi pipeline-ul SigurScan pentru Android/backend.

Citeste contextul din acest brief si trateaza urmatoarele documente ca drafturi sursa:
- MASTER_PIPELINE_SPEC.md
- EVIDENCE_GATE_MATRIX.md
- RAG_POLICY.md
- SCAM_FAMILY_CORPUS_SCHEMA.md
- OFFICIAL_DOMAINS_REGISTRY.md
- ACCEPTANCE_TESTS_ROMANIA.md
- FINAL_ANDROID_SCAN_PIPELINE_EXECUTION.md

Obiectiv:
Construieste un Master Pipeline final pentru o aplicatie de scam checking din Romania care primeste input prin share/import/upload, extrage date, ruleaza scanari pe piloni in cascada si dependent, foloseste urlscan preview ca moat principal, Web Risk/blacklist ca verificari puternice, VT doar fallback, RAG doar ca explicator, iar UI-ul afiseaza o decizie concreta si simpla.

Principii obligatorii:
1. Nu marca scam doar pentru HTML email, link sub buton, tracking link sau limbaj comercial.
2. Marketingul legitim foloseste expresii ca `profita acum`, `ultima sansa`, `voucher`, `nu rata`, `promotie`.
3. Verdictul trebuie sa se bazeze pe destinatia reala, brand match, ce cere pagina finala, reputatie si blacklist-uri.
4. Userul nu trebuie sa vada detalii tehnice implicit.
5. Userul trebuie sa primeasca o actiune clara: continua, nu continua, nu introduce date, verifica oficial, nu pot verifica suficient.
6. Nu folosi promisiuni absolute precum `100% sigur` sau `garantat legitim`.
7. RAG-ul nu decide verdictul. RAG-ul explica dovezile decise de gate.

Te rog sa livrezi:
1. Arhitectura finala: Extractor, Normalizer, Evidence Builder, Scan Orchestrator, Evidence Gate, Decision Engine, RAG Explainer, User Result.
2. Cei 5 piloni finali si rolul fiecaruia.
3. Orchestrarea exacta: cand ruleaza urlscan, Web Risk, blacklist, VT, RAG si offer checker.
4. Evidence Gate final: strong/medium/weak signals si ce verdicturi permit.
5. Decision Matrix finala cu output user-facing.
6. Pseudocode pentru orchestrator si gate.
7. Schema finala pentru corpus si official domains registry.
8. Acceptance tests obligatorii, inclusiv false-positive cases.
9. Recomandari privacy/legal/cost control.
10. O lista de schimbari concrete de implementare pentru Android/backend.

Important:
Vreau un pipeline perfect structurat, nu o lista de idei. Daca exista tradeoff-uri, spune-le explicit si alege varianta recomandata.
```

## Intrebari la care GPT 5.5 Pro trebuie sa raspunda explicit

1. Cand avem voie sa afisam `Poti continua cu prudenta`?
2. Cand avem voie sa afisam `Nu continua`?
3. Cand trebuie sa afisam `Verifica pe canalul oficial` in loc de `Nu continua`?
4. Cand trebuie sa afisam `Nu pot verifica suficient`?
5. Daca urlscan este clean, dar pagina cere card pe domeniu neoficial, ce verdict alegem?
6. Daca Web Risk este clean, dar brand mismatch + form action dubios exista, ce verdict alegem?
7. Daca emailul are tracking link legitim catre domeniu oficial, ce verdict alegem?
8. Daca doar exista `voucher/profita acum/nu rata`, ce verdict maxim este permis?
9. Cand ruleaza VT si cand il sarim?
10. Ce date tehnice ascundem implicit in UI?

## Acceptance cases care nu se negociaza

- Uber real email cu `rides.sng.link` si fallback `uber.com` nu devine eMAG scam.
- eMAG newsletter real nu devine scam doar pentru voucher/promotie.
- FAN Courier fake cu domeniu neoficial si plata/card devine `Nu continua`.
- ANAF fake cu link extern si login/plata/date devine `Nu continua`.
- Web Risk malware/phishing devine `Nu continua`.
- urlscan indisponibil devine `Nu pot verifica suficient` daca final URL nu este clar.
- Link vizibil oficial, dar href/final URL neoficial care cere OTP/card devine `Nu introduce date`.
- Tracking link legitim cu fallback oficial nu devine `Nu continua` doar pentru tracking.

## Rezultatul ideal

Un sistem disciplinat:

`Input -> Extractor -> Normalizer -> Evidence Builder -> Cascaded Scans -> Evidence Gate -> Decision Engine -> RAG Explanation -> User Result`

Cu un UI simplu:

- snapshot/preview securizat;
- decizie clara;
- 1-2 motive simple;
- domeniul final;
- actiune recomandata;
- detalii tehnice doar la cerere.
