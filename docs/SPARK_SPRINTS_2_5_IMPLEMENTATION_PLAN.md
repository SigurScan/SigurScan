# SigurScan Spark Sprints 2-5 Implementation Plan

Data: 2026-06-02

Status: handoff operational pentru Codex Spark / executie Android.

## Principiu

Acest document este pentru implementare, nu pentru reinventarea arhitecturii.

Source of truth:

- `docs/LAUNCH_ARCHITECTURE_FINAL.md`

Cod existent pe care se construieste:

- `app/src/main/java/com/example/myapplication/EvidenceGate.kt`
- `app/src/main/java/com/example/myapplication/EvidenceSignalNormalizer.kt`
- `app/src/test/java/com/example/myapplication/EvidenceGateTest.kt`
- `app/src/test/java/com/example/myapplication/EvidenceSignalNormalizerTest.kt`

Regula principala a produsului:

```text
Linkul duce unde pretinde mesajul ca duce?
```

Spark nu trebuie sa creeze:

- un al doilea gate;
- un nou sistem de scor;
- un RAG care decide verdictul;
- criterii noi de risc fara corpus + test;
- UI cu procente ca verdict principal;
- verdict hard doar din marketing, CTA, buton HTML sau tracking link.

## Contract De Lucru Pentru Spark

La inceputul fiecarui sprint:

1. Citeste `docs/LAUNCH_ARCHITECTURE_FINAL.md`.
2. Citeste fisierele cod relevante pentru sprint.
3. Verifica ce este deja implementat.
4. Continua peste implementarea existenta, nu rescrie fara motiv.
5. Adauga teste inainte sau impreuna cu implementarea.
6. Ruleaza testele.
7. Raporteaza exact fisiere modificate, teste adaugate, rezultat build/test si ce ramane.

Comanda standard de test:

```bash
JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" ./gradlew :app:testDebugUnitTest
```

Comanda recomandata la final de Sprint 5:

```bash
JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" ./gradlew :app:assembleDebug
```

## Guardrails Absolute

Aceste reguli nu se negociaza in Sprint 2-5:

- `EvidenceGate` este singurul judecator final.
- `EvidenceSignalNormalizer` transforma datele in `EvidenceSignal`, nu decide verdict.
- `RAG`, corpus similarity si AI explanation sunt read-only dupa gate.
- `finalUrl` castiga peste `primaryUrl` cand exista.
- `formActionHost` poate castiga peste `finalUrl` pentru card/login/OTP/CNP/IBAN.
- Google Web Risk include `MALWARE`, `SOCIAL_ENGINEERING`, `UNWANTED_SOFTWARE` si optional `SOCIAL_ENGINEERING_EXTENDED_COVERAGE`.
- urlscan este `private` by default.
- urlscan `public` este interzis pentru URL-uri trimise de user.
- VirusTotal Public API nu este requirement de productie Play; VT se foloseste doar daca exista licenta/flow compatibil sau ramane dezactivat/fallback.
- Nu se adauga SMS auto-read, Notification Listener, Accessibility Service, clipboard background monitoring, VPN, overlay sau broad storage.
- Nu se stocheaza raw email / raw OCR / raw document cu PII fara nevoie explicita.
- Marketing urgency, CTA, buton HTML, tracking link sau link ascuns sub buton sunt semnale slabe, niciodata hard-danger singure.

## Sprint 2 - Evidence Normalizer Audit And Completion

Scop:

Transformam toate output-urile locale si provider in `EvidenceSnapshot` coerent, astfel incat `EvidenceGate.evaluate()` sa poata decide determinist.

Important:

`EvidenceSignalNormalizer.kt` exista deja. Nu il duplica. Auditeaza-l si completeaza-l.

Fisiere de citit:

- `docs/LAUNCH_ARCHITECTURE_FINAL.md`
- `app/src/main/java/com/example/myapplication/EvidenceGate.kt`
- `app/src/main/java/com/example/myapplication/EvidenceSignalNormalizer.kt`
- `app/src/main/java/com/example/myapplication/HtmlLinkExtractor.kt`
- `app/src/main/java/com/example/myapplication/PrimaryUrlPicker.kt`
- `app/src/main/java/com/example/myapplication/ScannerViewModel.kt`
- `app/src/test/java/com/example/myapplication/EvidenceSignalNormalizerTest.kt`

Implementare asteptata:

- Normalizeaza input-uri din text, HTML, link extras, redirect chain, final URL si threat intel.
- Pastreaza clar diferenta intre `primaryUrl`, `finalUrl`, `redirectChain` si, daca exista, `formActionHost`.
- Mapeaza Web Risk, urlscan si VT in `EvidenceCode` existente.
- Mapeaza lipsa providerilor in `ProviderState`, nu in verdict hard.
- Mapeaza HTML button / hidden link / tracking link ca weak evidence.
- Mapeaza claimed brand vs final domain mismatch ca structural evidence.
- Mapeaza cereri sensibile: card, CVV, OTP, password, login, CNP, IBAN, plata, APK, remote access.
- Mapeaza scenarii romanesti text-only: telefon stricat, WhatsApp code, accident/nepot, BNR/cont sigur, marketplace receive-money, curier taxa.
- Mapeaza domenii oficiale / delegated / approved tracker fara a crea whitelist absoluta.
- Daca `finalUrl` apare dupa verdict provizoriu, snapshot-ul nou trebuie sa permita reevaluare.

Teste obligatorii Sprint 2:

- Uber real promo HTML: `rides.sng.link` primary, `uber.com` final, CTA comercial, verdict `CONTINUE_WITH_CAUTION`.
- eMAG newsletter real: marketing urgency + domeniu oficial, verdict `CONTINUE_WITH_CAUTION`.
- Link sub buton fara final URL si fara provider: maxim `VERIFY_OFFICIAL`, nu `DO_NOT_CONTINUE`.
- Yahoo/Gmail webmail shell fara corp email util: `INSUFFICIENT_EVIDENCE`.
- Outlook Safe Links / URLDefense wrapper: wrapper nu devine hard danger singur.
- `finalUrl` neoficial diferit de primary tracker aprobat: finalul castiga.
- Form action neoficial cu card/CVV/login: `NO_ENTER_DATA` sau `DO_NOT_CONTINUE` conform gate.
- Web Risk no-match nu anuleaza formular sensibil neoficial.
- Web Risk social engineering / malware / unwanted software / extended coverage mapeaza hard evidence.
- urlscan phishing/malware mapeaza hard evidence.
- urlscan no classification / pending / timeout / rate limited nu inseamna safe.
- VT clean/no detection este non-decisive.
- VT malicious consensus este hard only daca VT este configurat/licentiat in flow.
- Marketing-only si text-only promo nu pot depasi `VERIFY_OFFICIAL`.

Definition of Done Sprint 2:

- Normalizerul produce `EvidenceSnapshot` fara network calls.
- Toate testele existente trec.
- Testele noi acopera false-positive guard pentru Uber/eMAG/FAN real.
- Nu exista al doilea gate sau scoring paralel.

## Sprint 3 - Wire Gate Into Scan Pipeline

Scop:

Conectam `EvidenceSignalNormalizer` + `EvidenceGate` la fluxul real de scanare Android, fara sa schimbam inca radical UI-ul.

Fisiere de citit:

- `app/src/main/java/com/example/myapplication/ScannerViewModel.kt`
- `app/src/main/java/com/example/myapplication/SigurScanApi.kt`
- `app/src/main/java/com/example/myapplication/ThreatIntelOrchestrator.kt`
- `app/src/main/java/com/example/myapplication/OfflineRiskPolicy.kt`
- `app/src/main/java/com/example/myapplication/MailShareInputAssembler.kt`
- `app/src/main/java/com/example/myapplication/SharedTextPayloadResolver.kt`
- `app/src/main/java/com/example/myapplication/MainActivity.kt`

Implementare asteptata:

- Dupa fiecare scanare, construieste un `EvidenceSnapshot`.
- Ruleaza `EvidenceGate.evaluate(snapshot)`.
- Pastreaza `GateResult` in state-ul ViewModel / result model.
- Pastreaza datele de preview: screenshot URL, final URL, redirect chain, server info cand exista.
- Nu mai lasa `evaluateOfflineText` sau scorurile vechi sa produca verdict user-facing hard cand backend/providerii lipsesc.
- Offline/local-only trebuie sa intoarca `INSUFFICIENT_EVIDENCE`, `VERIFY_OFFICIAL` sau `NO_REPLY`, nu hard danger din keyword marketing.
- Providerii indisponibili devin `ProviderState.TIMEOUT`, `ERROR`, `RATE_LIMITED` sau `PENDING`.
- RAG/offer checker poate explica sau adauga context, dar nu poate modifica `GateResult.action`.
- Async update: daca apare evidence nou mai grav, poate ridica verdictul. Nu cobori silent un verdict hard in aceeasi sesiune.

Teste obligatorii Sprint 3:

- Backend/provider down + eMAG newsletter real => nu `DO_NOT_CONTINUE`.
- Backend/provider down + Uber real promo => nu `DO_NOT_CONTINUE`.
- Text-only WhatsApp code request => `NO_REPLY`.
- FAN fake cu card form => `NO_ENTER_DATA` sau `DO_NOT_CONTINUE`.
- urlscan malicious venit async dupa verdict provizoriu => reevalueaza la `DO_NOT_CONTINUE`.
- urlscan pending peste timeout UX => `INSUFFICIENT_EVIDENCE` sau `VERIFY_OFFICIAL`, nu safe.
- Provider no-match + structural sensitive risk => structural risk ramane.

Definition of Done Sprint 3:

- Pipeline-ul real foloseste `EvidenceGate.evaluate()`.
- Output-ul scanarii contine `GateResult`.
- Scorurile vechi nu mai sunt verdict principal.
- Testele unitare trec.

## Sprint 4 - Parser, Share Intent, Final URL Preview Hardening

Scop:

Facem parsarea pentru mail/share cat mai reala si robusta, mai ales pentru linkuri ascunse sub butoane, fara false-positive pe marketing legitim.

Fisiere de citit:

- `app/src/main/java/com/example/myapplication/HtmlLinkExtractor.kt`
- `app/src/main/java/com/example/myapplication/MailShareInputAssembler.kt`
- `app/src/main/java/com/example/myapplication/SharedTextPayloadResolver.kt`
- `app/src/main/java/com/example/myapplication/EmailMessageParser.kt`
- `app/src/main/java/com/example/myapplication/PdfLinkExtractor.kt`
- `app/src/main/java/com/example/myapplication/ScannerViewModel.kt`
- `app/src/main/AndroidManifest.xml`

Implementare asteptata pentru Share Intent:

- Citeste `Intent.EXTRA_TEXT`.
- Citeste `Intent.EXTRA_HTML_TEXT`.
- Citeste `intent.clipData` pentru text/html/uri cand aplicatia sursa il pune acolo.
- Citeste stream-uri user-selected doar prin flow user-initiated.
- Marcheaza in model daca input-ul primit este `HTML complet`, `text vizibil`, `URL direct`, `fisier`, `imagine/OCR`, `webmail shell`.
- Arata intern/diagnostic daca putem detecta linkuri ascunse sau doar text vizibil.

Implementare asteptata pentru HTML parser:

- Extrage `href`.
- Extrage linkuri din butoane si CTA.
- Extrage `form action`.
- Extrage `formaction`.
- Extrage `data-url`, `data-href`, `data-link`, `data-target` cand contin URL.
- Extrage `meta refresh`.
- Extrage redirecturi JS simple: `window.location`, `location.href`, `window.open`.
- Decodeaza HTML entities si percent encoding unde e sigur.
- Decodeaza cazuri simple `atob(...)` si `decodeURIComponent(...)` cu limita de iteratii.
- Extrage CSS `url(...)` doar ca evidence slaba/resource, nu ca primary hard by default.
- Extrage SVG `href` / `xlink:href` cand exista.
- Detecteaza dar nu supra-penalizeaza tracking links legitime.
- Evita sa confunde webmail shell, reclame, analytics si resource links cu corpul emailului.

Implementare asteptata pentru preview:

- Preview-ul se leaga de `finalUrl` cand exista.
- Daca avem doar `primaryUrl`, preview-ul este provizoriu sau nu se afiseaza ca final.
- Screenshot-ul este evidence vizual pentru user, nu dovada unica de safe.
- Daca urlscan este pending/rate limited/timeout, UI trebuie sa spuna clar ca preview-ul nu este inca disponibil.
- PII redaction inainte de provider public/extern.
- urlscan `private` default.

Teste obligatorii Sprint 4:

- Uber button HTML real: extrage href-ul din `Comanda o cursa`.
- Buton `<a>` cu text oficial si href neoficial: extrage href-ul real.
- `<button onclick="window.location.href='...'">`: extrage destinatia.
- `data-url` pe button: extrage URL.
- `meta refresh`: extrage URL.
- `atob('aHR0cHM6Ly8...')`: extrage URL cu limita.
- Outlook Safe Links: extrage wrapper si, daca poate, destinatia din query.
- `google.com/url?q=...`, `facebook.com/l.php?u=...`, `urldefense.com`, `safelinks.protection.outlook.com`: recunoaste redirectorii.
- CSS/SVG resource links nu devin hard danger singure.
- Yahoo/Gmail shell fara corp real: nu produce `HIDDEN_LINK_PRESENT` ca si cum ar fi mailul.
- HTML marketing real cu CTA si tracking final oficial: nu devine scam.

Definition of Done Sprint 4:

- Share email flow este testabil fara copy-paste manual de HTML.
- Parserul scoate linkul real de sub buton cand HTML-ul este primit.
- Cand primim doar text vizibil, modelul spune explicit ca HTML-ul nu a fost disponibil.
- Preview-ul urmareste final URL si nu minte userul.
- Testele unitare trec.

## Sprint 5 - User Result UI Action-First And Transparency

Scop:

Userul non-tehnic trebuie sa inteleaga imediat ce sa faca, de ce, si ce link real a fost analizat.

Fisiere de citit:

- `app/src/main/java/com/example/myapplication/MainActivity.kt`
- `app/src/main/java/com/example/myapplication/ScannerViewModel.kt`
- `app/src/main/java/com/example/myapplication/EvidenceGate.kt`
- `docs/LAUNCH_ARCHITECTURE_FINAL.md`

Implementare asteptata:

- UI afiseaza `GateResult.userLabel` ca verdict principal.
- Nu afiseaza procent ca mesaj principal.
- Nu foloseste `safe`, `100% sigur`, `garantat`, `suspect` ca verdict final vag.
- Afiseaza domeniul final analizat.
- Afiseaza claimed brand cand exista.
- Afiseaza screenshot/preview securizat cand exista.
- Afiseaza clar cand preview-ul lipseste sau este pending.
- Afiseaza 1-3 motive simple, non-tehnice.
- Afiseaza 1-3 actiuni recomandate.
- Ascunde detaliile tehnice intr-o zona expandabila.
- Arata clar `PROVISIONAL` vs `FINAL` fara jargon.
- Cand input-ul a fost doar text vizibil, spune: `Am primit doar textul vizibil. Nu pot vedea linkuri ascunse sub butoane.`
- Cand input-ul a fost HTML complet, spune: `Am primit structura HTML si am verificat linkurile ascunse.`

Copy user-facing recomandat:

- `Nu continua`
- `Nu introduce date`
- `Nu raspunde`
- `Verifica pe canalul oficial`
- `Poti continua cu prudenta`
- `Nu pot verifica suficient`

Motive simple recomandate:

- `Linkul final nu pare sa apartina brandului mentionat.`
- `Pagina cere date sensibile pe un domeniu nevalidat.`
- `Serviciul de reputatie a raportat phishing/malware.`
- `Am gasit doar limbaj promotional, dar nu dovezi tehnice de frauda.`
- `Nu am primit HTML-ul complet, deci nu pot vedea linkuri ascunse sub butoane.`
- `Linkul trece printr-un tracker aprobat si ajunge pe domeniul oficial.`

Actiuni recomandate:

- `Nu apasa linkul.`
- `Nu introduce card, parola sau cod OTP.`
- `Deschide aplicatia oficiala sau site-ul oficial manual.`
- `Suna la numarul oficial, nu la numarul din mesaj.`
- `Daca ai introdus date, contacteaza banca imediat.`

Teste obligatorii Sprint 5:

- Fiecare `GateAction` are copy user-facing clar.
- `CONTINUE_WITH_CAUTION` nu spune `safe`.
- `INSUFFICIENT_EVIDENCE` nu arata ca eroare tehnica inutila.
- Preview final URL apare cand exista screenshot.
- Preview pending este afisat ca pending, nu ca failure.
- Technical details sunt ascunse default.
- HTML complet vs text vizibil este comunicat.

Definition of Done Sprint 5:

- UI foloseste `GateResult`.
- Userul vede decizie, domeniu final, preview si actiune recomandata.
- Nu exista jargon tehnic in zona principala.
- Testele unitare trec.
- `:app:assembleDebug` trece.

## Acceptance Final Sprint 2-5

La final, produsul Android trebuie sa treaca aceste scenarii fara false-positive grav:

- Uber promo real cu buton si tracking legitim -> `Poti continua cu prudenta`.
- eMAG newsletter real cu marketing urgency -> `Poti continua cu prudenta`.
- FAN Courier real cu domeniu oficial/delegat -> `Poti continua cu prudenta`.
- Link sub buton fara final URL -> `Verifica pe canalul oficial`, nu hard danger.
- Yahoo/Gmail shell fara HTML real -> `Nu pot verifica suficient`.
- Web Risk no-match + formular card neoficial -> `Nu introduce date`.
- urlscan phishing -> `Nu continua`.
- Web Risk malware/social engineering -> `Nu continua`.
- ANAF fake + domeniu neoficial + login/plata -> `Nu introduce date` sau `Nu continua`.
- Marketplace `ca sa primesti banii` + card/OTP -> `Nu introduce date`.
- WhatsApp code request text-only -> `Nu raspunde`.
- Telefon stricat / numar nou + bani -> `Nu raspunde`.
- Provider down + marketing real -> nu `Nu continua`.
- VT disabled/unlicensed -> nu blocheaza pipeline-ul.

## Raport Final Cerut De La Spark

La finalul fiecarui sprint, Spark trebuie sa raspunda in formatul:

```text
Sprint X Done / Partial / Blocked

Files changed:
- ...

Tests added:
- ...

Verification:
- Command: ...
- Result: ...

What now works:
- ...

What remains:
- ...

Risks:
- ...
```

Nu accepta raspuns de tip `pare ok` fara comanda de test si rezultat.

