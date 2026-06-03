# SigurScan - Final GPT 5.5 Pro Handoff

Ultima actualizare: 2026-06-02

Scop: document final pentru sesiunea GPT 5.5 Pro Web. Acesta este pachetul de lucru complet: context, documente sursa, decizii deja validate, intrebari critice si prompt final.

## 1. Ce vrem de la GPT 5.5 Pro

Vrem sa actioneze ca arhitect principal de produs + backend + threat intelligence + UX pentru SigurScan.

Nu vrem idei generale. Vrem un pipeline final, implementabil, structurat, cu reguli clare si fara false-positive-uri pe marketing normal.

Livrabilul dorit:

- Master Pipeline final v1.
- Evidence Gate final.
- Decision Matrix finala.
- Pseudocode backend/orchestrator.
- Data contracts.
- RAG policy finala.
- Corpus plan final.
- UI result copy final.
- Acceptance tests.
- Lista de taskuri concrete Android/backend.

## 2. Context produs

SigurScan este o aplicatie Android de scam checking pentru Romania.

Userul poate:

- face share din email, browser sau mesagerie;
- importa/incarca linkuri, emailuri, HTML, PDF, imagini, screenshoturi, QR;
- introduce manual un link/text.

Aplicatia trebuie sa raspunda la intrebari simple:

- Pot continua?
- Pot apasa?
- Pot raspunde?
- Pot introduce card/parola/OTP/CNP/IBAN?
- Trebuie sa verific pe canalul oficial?

SigurScan nu este laborator cyber. Este un produs user-facing, light, pentru Romania.

## 3. Directia strategica

SigurScan trebuie sa fie decisiv in actiune, dar prudent in promisiuni.

User-facing corect:

- `Poti continua cu prudenta`
- `Nu continua`
- `Nu introduce date`
- `Nu raspunde`
- `Verifica pe canalul oficial`
- `Nu pot verifica suficient`

User-facing incorect:

- `100% sigur`
- `garantat legitim`
- `site sigur`
- `oferta este sigur reala`
- `detectam toate scamurile`
- `suspect`, ca raspuns final vag fara actiune.

Intern poate exista `SUSPICIOUS`, dar in UI trebuie transformat in actiune clara: `Verifica pe canalul oficial` sau `Nu apasa inca`.

## 4. Moat-ul produsului

Moat-ul SigurScan nu este VirusTotal si nu este un scor tehnic.

Moat-ul este:

`Iti aratam vizual unde te duce linkul, fara sa intri tu pe site, si iti spunem clar daca sa continui, sa raspunzi sau sa introduci date.`

urlscan preview este feature-ul central:

- sandbox;
- screenshot/preview;
- final URL;
- redirect chain;
- page/server summary in detalii tehnice.

## 5. Cei 5 piloni finali

### Pilon 1: Share/import/upload + extractor avansat

Rol: aduce datele corecte in sistem.

Include:

- Share Intent;
- HTML email parsing;
- text vizibil;
- linkuri ascunse sub butoane;
- `href`, `formaction`, `data-*`, `meta refresh`, redirect hints;
- sender, subject, reply-to, headers cand exista;
- QR/OCR;
- fisiere/atasamente unde se poate.

Nu decide verdict.

### Pilon 2: urlscan sandbox + preview securizat

Rol: moat principal.

Include:

- final URL;
- redirect chain;
- screenshot/preview;
- verdict urlscan;
- technical page summary.

Reguli:

- ruleaza default pe URL-ul principal;
- `private` preferat, `unlisted` fallback;
- niciodata `public` in produs;
- cache;
- backoff;
- sanitizare PII/tokenuri;
- fallback: `Preview indisponibil momentan`.

### Pilon 3: reputation + blacklist checks

Rol: confirmare externa rapida.

Include:

- Google Web Risk;
- blacklist Romania / DNSC / ANPCDNS doar daca exista feed/API/licenta clara;
- VirusTotal fallback;
- cache intern.

Reguli:

- Web Risk este sursa Google corecta pentru comercial.
- Google Safe Browsing API direct nu se foloseste comercial fara acord separat.
- VirusTotal nu ruleaza la fiecare scanare; ruleaza doar fallback/intaritor.

### Pilon 4: context Romania + scam families + domenii oficiale

Rol: detectie locala si false-positive prevention.

Include:

- FAN Courier fake;
- ANAF/SPV fake;
- Posta Romana fake;
- banci/card/OTP;
- OLX/marketplace;
- Revolut;
- WhatsApp takeover;
- remote access fraud;
- eMAG fake;
- lista domeniilor oficiale.

Regula critica:

Brandul nu se decide din keywords generice.

Acestea nu sunt suficiente pentru brand/scam family:

- `voucher`;
- `promotie`;
- `reducere`;
- `colet`;
- `livrare`;
- `plata`;
- `cod`;
- `profita acum`;
- `ultima sansa`;
- `nu rata`.

### Pilon 5: offer checker + RAG explainer + user decision

Rol: explica dovezile si produce raspuns simplu.

Offer checker:

- nu spune automat `oferta e falsa`;
- spune `Nu am gasit confirmare oficiala`;
- spune `Oferta cere date pe domeniu neoficial`;
- spune `Verifica direct in aplicatia/site-ul oficial`.

RAG:

- este consultant, nu judecator;
- explica dovezile;
- compara cu corpusul;
- nu decide verdictul final.

Judecatorul este:

`Evidence Gate + Decision Matrix + Corpus Tests`

## 6. Regula centrala de risc

SigurScan decide pe baza de dovezi reale:

- destinatia finala;
- brand match;
- ce cere pagina finala;
- reputatie externa;
- blacklist-uri;
- sender/auth cand exista;
- form action;
- visible URL vs actual href;
- domenii oficiale.

SigurScan nu decide risc mare doar pentru:

- HTML email;
- link sub buton;
- tracking link;
- newsletter;
- limbaj comercial;
- `voucher`;
- `profita acum`;
- `ultima sansa`;
- `promotie`;
- `nu rata`.

Acestea sunt semnale slabe. Pot declansa analiza, dar nu verdict `DANGEROUS`.

## 7. Dovezi puternice

Pot produce `Nu continua` sau `Nu introduce date`:

- Web Risk confirma malware/phishing/social engineering;
- DNSC/ANPCDNS/blacklist match, daca sursa este verificata;
- urlscan malicious;
- VirusTotal malicious relevant, in fallback;
- brand mismatch clar;
- final URL neoficial cere card/OTP/parola/CNP/IBAN/login/plata;
- form action trimite date catre domeniu dubios/neoficial;
- link vizibil promite domeniu oficial, dar href/final URL duce in alta parte si cere date;
- sender/from/reply-to/auth nu corespund brandului, cand avem headers;
- download APK sau remote access neoficial.

## 8. Decizii de cercetare deja validate

### Web Risk

Surse:

- `https://cloud.google.com/web-risk/docs/lookup-api`
- `https://cloud.google.com/web-risk/pricing`
- `https://docs.cloud.google.com/web-risk/docs/caching`
- `https://docs.cloud.google.com/web-risk/docs/lists`

Fapte:

- `uris.search` verifica un URL/request;
- raspuns `{}` inseamna no known match, nu safe absolut;
- match include `threatTypes` si `expireTime`;
- cache pe `expireTime`;
- free tier: 100.000 calls/luna;
- dupa free tier: `$0.50 / 1,000 calls`.

Decizie:

- Web Risk ruleaza devreme, cu cache;
- Web Risk match este strong signal;
- Web Risk clean nu inseamna automat safe.

### Safe Browsing direct

Sursa:

- `https://developers.google.com/safe-browsing/terms`

Fapte:

- uz comercial interzis fara acord separat cu Google.

Decizie:

- nu folosim Safe Browsing API direct in release comercial;
- folosim Web Risk.

### urlscan

Sursa:

- `https://urlscan.io/docs/api/`

Fapte:

- visibility: `public`, `unlisted`, `private`;
- `public` apare public;
- `unlisted` nu apare public, dar poate fi vizibil pentru security researchers/security companies in urlscan Pro;
- `private` este vizibil doar contului tau sau celor cu scan ID;
- recomandare urlscan: remove PII sau foloseste unlisted/private;
- respecta HTTP 429, backoff, work queue;
- result poate fi 404 pana scanarea se termina;
- screenshot endpoint: `/screenshots/{uuid}.png`.

Decizie:

- urlscan este moat UX;
- folosim `private` daca avem plan, altfel `unlisted`;
- nu trimitem email complet, doar URL sanitizat;
- cache si backoff obligatorii;
- maxim un primary URL default.

### VirusTotal

Surse:

- `https://docs.virustotal.com/reference/overview`
- `https://docs.virustotal.com/docs/consumption-quotas-handled`

Fapte:

- API v3 are URL/domain/IP/file reports;
- reputatie din multe motoare/blocklists;
- quotas per minute, daily, monthly;
- API v3 raspunde 429 la quota limit.

Decizie:

- VT este fallback/intaritor;
- nu este moat;
- nu ruleaza by default daca urlscan/Web Risk/gate sunt suficiente;
- ruleaza prin backend, cu cache/rate limit.

### DNSC / blacklist Romania

Observatie:

- nu avem confirmat inca un feed/API public stabil in aceasta sesiune;
- accesul automat la DNSC a raspuns 403.

Decizie:

- provider modular;
- fara scraping agresiv;
- fara claim de afiliere oficiala;
- acceptam feed/API doar cu sursa/licenta clara.

## 9. Documente sursa existente

Aceste documente exista deja in proiect si trebuie folosite ca baza:

- `docs/MASTER_PIPELINE_SPEC.md`
- `docs/EVIDENCE_GATE_MATRIX.md`
- `docs/RAG_POLICY.md`
- `docs/SCAM_FAMILY_CORPUS_SCHEMA.md`
- `docs/OFFICIAL_DOMAINS_REGISTRY.md`
- `docs/ACCEPTANCE_TESTS_ROMANIA.md`
- `docs/FINAL_ANDROID_SCAN_PIPELINE_EXECUTION.md`
- `docs/GPT55_PRO_8PM_PIPELINE_BRIEF.md`
- `docs/SPARK_PIPELINE_IMPLEMENTATION_CHECKLIST.md`
- `docs/OPENCODE_MASTER_PIPELINE_FINAL_DRAFT.md`

## 10. Ce trebuie sa faca GPT 5.5 Pro

GPT trebuie sa citeasca contextul si sa produca o versiune finala, mai buna decat draftul OpenCode.

Trebuie sa faca explicit:

1. Sa critice arhitectura existenta.
2. Sa gaseasca gauri de false-positive/false-negative.
3. Sa confirme sau sa corecteze cei 5 piloni.
4. Sa rafineze Evidence Gate.
5. Sa rafineze Decision Matrix.
6. Sa rafineze cand ruleaza urlscan/Web Risk/VT/blacklist/RAG/offer checker.
7. Sa dea pseudocode final.
8. Sa dea data contracts finale.
9. Sa dea UI copy final.
10. Sa dea lista de taskuri concrete pentru Spark/Android/backend.

## 11. Intrebari critice la care trebuie sa raspunda

1. Cand avem voie sa afisam `Poti continua cu prudenta`?
2. Cand avem voie sa afisam `Nu continua`?
3. Cand avem voie sa afisam `Nu introduce date`?
4. Cand avem voie sa afisam `Nu raspunde`?
5. Cand afisam `Verifica pe canalul oficial` in loc de `Nu continua`?
6. Cand afisam `Nu pot verifica suficient`?
7. Daca urlscan este clean, dar pagina cere card pe domeniu neoficial, ce verdict alegem?
8. Daca Web Risk este clean, dar brand mismatch + form action dubios exista, ce verdict alegem?
9. Daca emailul are tracking link legitim catre domeniu oficial, ce verdict alegem?
10. Daca exista doar `voucher/profita acum/nu rata`, ce verdict maxim este permis?
11. Cand ruleaza VT si cand il sarim?
12. Ce date tehnice ascundem implicit in UI?
13. Cum prevenim cazul Uber real clasificat gresit ca eMAG scam?
14. Cum definim scam families fara keyword-only classification?
15. Cum folosim RAG fara sa il lasam sa decida verdictul?

## 12. Acceptance cases care nu se negociaza

- Uber real email cu `rides.sng.link` si fallback `uber.com` nu devine eMAG scam.
- eMAG newsletter real nu devine scam doar pentru voucher/promotie.
- FAN Courier fake cu domeniu neoficial si plata/card devine `Nu continua` sau `Nu introduce date`.
- FAN Courier real nu devine scam doar pentru `colet`, `AWB`, `livrare`.
- ANAF fake cu link extern si login/plata/date devine `Nu continua`.
- Web Risk malware/phishing devine `Nu continua`.
- urlscan indisponibil devine `Nu pot verifica suficient` daca final URL nu este clar.
- Link vizibil oficial, dar href/final URL neoficial care cere OTP/card devine `Nu introduce date`.
- Tracking link legitim cu fallback oficial nu devine `Nu continua` doar pentru tracking.
- Webmail shell HTML fara corpul real al emailului devine `Nu pot verifica suficient`, nu scam.

## 13. Prompt final pentru GPT 5.5 Pro

```text
Vreau sa actionezi ca arhitect principal pentru SigurScan, o aplicatie Android de scam checking pentru Romania.

Ai de revizuit un pachet de documente deja pregatit:
- MASTER_PIPELINE_SPEC.md
- EVIDENCE_GATE_MATRIX.md
- RAG_POLICY.md
- SCAM_FAMILY_CORPUS_SCHEMA.md
- OFFICIAL_DOMAINS_REGISTRY.md
- ACCEPTANCE_TESTS_ROMANIA.md
- FINAL_ANDROID_SCAN_PIPELINE_EXECUTION.md
- GPT55_PRO_8PM_PIPELINE_BRIEF.md
- SPARK_PIPELINE_IMPLEMENTATION_CHECKLIST.md
- OPENCODE_MASTER_PIPELINE_FINAL_DRAFT.md

Context produs:
SigurScan permite userului sa faca share/import/upload de linkuri, emailuri, HTML email, fisiere, imagini, screenshoturi, QR sau texte suspecte. Aplicatia trebuie sa extraga datele, sa ruleze scanari pe piloni in cascada si dependent, apoi sa afiseze userului o decizie concreta si simpla.

Moat principal:
urlscan sandbox + preview securizat. Vrem sa aratam vizual unde duce linkul fara ca userul sa intre pe site.

Surse/intaritoare:
- Google Web Risk pentru reputatie comerciala rapida.
- DNSC/ANPCDNS/blacklist Romania doar daca exista feed/API/licenta clara.
- VirusTotal doar fallback/intaritor, nu default la fiecare scanare.
- RAG doar explicator/consultant, nu judecator.

Principiu critic:
SigurScan NU marcheaza scam doar pentru:
- HTML email;
- link sub buton;
- tracking link;
- newsletter;
- limbaj comercial;
- `profita acum`;
- `ultima sansa`;
- `nu rata`;
- `voucher`;
- `promotie`;
- `reducere`.

Acestea sunt semnale slabe. Marketingul legitim le foloseste. Ele pot declansa analiza, dar nu verdict periculos.

Verdictul trebuie sa se bazeze pe dovezi reale:
- final URL;
- brand match;
- ce cere pagina finala;
- Web Risk;
- urlscan;
- blacklist;
- VirusTotal fallback;
- sender/from/reply-to/auth cand exista;
- form action;
- visible URL vs actual href;
- official domains registry;
- corpus tests.

User-facing final trebuie sa fie actiune clara, nu threat intelligence:
- `Poti continua cu prudenta`
- `Nu continua`
- `Nu introduce date`
- `Nu raspunde`
- `Verifica pe canalul oficial`
- `Nu pot verifica suficient`

Nu folosi promisiuni absolute:
- nu `100% sigur`;
- nu `garantat legitim`;
- nu `site sigur`;
- nu `detectam toate scamurile`.

Te rog sa livrezi o versiune finala structurata care include:
1. Critica documentelor existente si punctele care trebuie corectate.
2. Arhitectura finala: Extractor, Normalizer, Evidence Builder, Scan Orchestrator, Evidence Gate, Decision Engine, RAG Explainer, User Result.
3. Cei 5 piloni finali si rolul fiecaruia.
4. Orchestrarea exacta: cand ruleaza urlscan, Web Risk, blacklist, VT, RAG si offer checker.
5. Evidence Gate final: weak/medium/strong signals si ce verdicturi permit.
6. Decision Matrix finala cu output user-facing.
7. Pseudocode pentru orchestrator si gate.
8. Data contracts finale pentru ScanInput, ExtractedPayload, EvidenceSnapshot, SourceResult, GateResult, UserResult.
9. Schema finala pentru corpus si official domains registry.
10. RAG policy finala: ce are voie si ce nu are voie RAG-ul.
11. UI final: ce vede userul above the fold si ce intra in detalii tehnice.
12. Acceptance tests obligatorii si false-positive guards.
13. Privacy/legal/cost control guardrails.
14. Lista concreta de taskuri Android/backend pentru Spark.

Raspunde explicit la aceste intrebari:
1. Cand afisam `Poti continua cu prudenta`?
2. Cand afisam `Nu continua`?
3. Cand afisam `Nu introduce date`?
4. Cand afisam `Nu raspunde`?
5. Cand afisam `Verifica pe canalul oficial`?
6. Cand afisam `Nu pot verifica suficient`?
7. Daca urlscan este clean, dar pagina cere card pe domeniu neoficial, ce verdict alegem?
8. Daca Web Risk este clean, dar brand mismatch + form action dubios exista, ce verdict alegem?
9. Daca emailul are tracking link legitim catre domeniu oficial, ce verdict alegem?
10. Daca exista doar `voucher/profita acum/nu rata`, ce verdict maxim este permis?
11. Cand ruleaza VT si cand il sarim?
12. Ce date tehnice ascundem implicit in UI?

Acceptance cases nenegociabile:
- Uber real email cu `rides.sng.link` si fallback `uber.com` nu devine eMAG scam.
- eMAG newsletter real nu devine scam doar pentru voucher/promotie.
- FAN Courier fake cu domeniu neoficial si plata/card devine `Nu continua` sau `Nu introduce date`.
- ANAF fake cu link extern si login/plata/date devine `Nu continua`.
- Web Risk malware/phishing devine `Nu continua`.
- urlscan indisponibil devine `Nu pot verifica suficient` daca final URL nu este clar.
- Link vizibil oficial, dar href/final URL neoficial care cere OTP/card devine `Nu introduce date`.
- Tracking link legitim cu fallback oficial nu devine `Nu continua` doar pentru tracking.
- Webmail shell HTML fara corpul real al emailului devine `Nu pot verifica suficient`, nu scam.

Important:
Vreau un pipeline final, implementabil, disciplinat. Nu vreau o lista de idei. Daca exista tradeoff-uri, spune-le explicit si alege varianta recomandata.

Output format dorit:
- Titluri clare.
- Tabele unde ajuta.
- Pseudocode concret.
- Reguli deterministe.
- Taskuri implementabile.
```

## 14. Cum evaluam raspunsul GPT 5.5 Pro

Raspunsul lui este bun doar daca:

- pastreaza urlscan preview ca moat principal;
- nu transforma marketingul normal in scam;
- nu lasa RAG-ul sa decida verdictul;
- da gate determinist;
- raspunde clar la toate intrebarile critice;
- include taskuri Android/backend;
- respecta legal/cost/privacy;
- rezolva false-positive Uber/eMAG;
- ascunde detaliile tehnice in UI;
- foloseste actiuni user-facing clare.

Raspunsul este slab daca:

- recomanda sa rulam toate serviciile mereu;
- foloseste `suspect` ca verdict final vag;
- foloseste `safe/100% sigur`;
- spune ca `voucher/profit acum/link sub buton` este suficient pentru scam;
- lasa VT ca moat principal;
- ignora urlscan privacy;
- ignora Web Risk vs Safe Browsing comercial;
- nu produce pseudocode.
