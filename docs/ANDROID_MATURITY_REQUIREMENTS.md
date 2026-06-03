# SigurScan Android - audit maturitate 100%

Ultima analiza: 2026-06-01

Update implementat 2026-06-01:

- `HttpLoggingInterceptor` a fost trecut pe `Level.NONE`, ca mesajele/linkurile scanate sa nu mai fie expuse in Logcat.
- `android:allowBackup` a fost setat la `false`.
- `backup_rules.xml` si `data_extraction_rules.xml` exclud shared preferences, databases, files si external storage.
- Pipeline-ul are acum model `ThreatIntelSourceResult` si campuri in `OfflineAssessment` pentru threat intel si raport sandbox.
- Rezultatul parseaza `external_intel_summary` din backend si il afiseaza ca surse threat intelligence.
- urlscan.io parseaza acum sumarul raportului: verdict, severitate, HTTP status, IP, tara, server si link catre raportul complet.
- UI-ul rezultatului are sectiune `Threat Intelligence` cu surse si status.
- Cast-urile nesigure din parsing-ul evidence au fost reduse prin helper dedicat.
- Parserul HTML pentru linkuri ascunse a fost separat în `HtmlLinkExtractor` și extins pentru butoane, evenimente JS (`onclick`/`onsubmit`), `formaction`, `data-*`, redirecturi `location`/`window.open`, `atob`, `decodeURIComponent` și redirecturi din `meta refresh`.
- Au fost adăugate teste unitare noi pentru scenarii reale de fraudă prin linkuri ascunse (buton+JS, form action, data-href, base64, self.location, meta refresh).
- Am adăugat integrarea directă `VirusTotal` + `Google Web Risk` în pipeline-ul Android.
- Cheile externe nu sunt hardcodate în cod; se iau din `BuildConfig` (configurable prin `local.properties`).
- Build verificat: `BUILD SUCCESSFUL`.

Scop: stabilim exact ce functionalitati reale exista in Android si ce trebuie facut ca aplicatia sa nu mai fie MVP, ci produs matur, real, cap-coada.

## Verdict executiv

Android are baza buna, dar nu este inca produs matur 100%. Are scanare backend reala, share intents, OCR/QR parțial, urlscan real mai bine integrat, radar cu hartă embedded parțial, istoric local si UI functional. Au fost intarite primele zone de securitate si threat-intel display. Inca lipsesc family cloud/push real, storage criptat si arhitectura modulara.

## 1. Ce este real acum

### Backend scanare

Status: real, dar modelare fragila.

Implementat:

- `POST /v1/scan/url`
- `POST /v1/scan/text`
- `POST /v1/scan/image`
- `POST /v1/scan/email`
- `POST /v1/scan/pdf`
- `GET /v1/community/campaigns`
- `GET /v1/evaluation/readiness`
- `GET /v1/feedback/quality`
- `GET /v1/feedback/samples`
- `GET /v1/reputation/cache/stats`

Fisier:

- `app/src/main/java/com/example/myapplication/SigurScanApi.kt`

Probleme pentru maturitate:

- `ScanResponse` foloseste multe `Map<String, Any>`, deci decodarea e fragila.
- Nu exista handling centralizat pentru status code, timeout, retry, rate limit, erori backend.
- logging BODY a fost eliminat; trebuie pastrat asa si in release.
- `applicationId` final Android: `ro.sigurscan.app`.

Trebuie:

- modele Kotlin stricte pentru `ScanResult`, `Evidence`, `ResolvedUrl`, `EmailAuth`, `EmailButton`, `ExternalIntelSummary`.
- interceptor cu redaction pentru date sensibile.
- error model comun: `NetworkError`, `ApiError`, `Timeout`, `RateLimit`, `DecodeError`.
- timeout-uri explicite si retry controlat.
- package final si release config.

## 2. Scanare URL/text

Status: real, dar incomplet fata de iOS si produs matur.

Implementat:

- text/link manual.
- URL simplu merge pe `/v1/scan/url`.
- text merge pe `/v1/scan/text`.
- fallback local prin `ScamRules.OFFLINE_RULES` daca backend-ul esueaza.
- salveaza rezultat in istoric local.
- ruleaza urlscan dupa URL final sau primul URL extras.

Probleme:

- nu exista pipeline clar cu pasi vizibili: backend, local, sandbox, reputation, intel.
- fallback local are doar 7 reguli, iOS are mai multe familii.
- scorurile locale sunt euristice si pot produce false positive/false negative.
- nu exista validare completa pentru URL-uri cu trailing punctuation, IDN/punycode, obfuscation, shorteners avansate.

Trebuie:

- pipeline matur: normalize URL -> classify input -> backend scan -> local fallback -> external intel -> merge verdict -> persist.
- reguli offline aliniate cu iOS toate familiile.
- normalizare URL robusta: IDN, punycode, redirect shorteners, IP, TLD, Unicode lookalikes.
- teste unitare pentru fiecare familie scam.

## 3. urlscan.io

Status: real, dar partial.

Implementat:

- trimite URL la `https://urlscan.io/api/v1/scan/`.
- polling la `https://urlscan.io/api/v1/result/{uuid}/`.
- preview screenshot `https://urlscan.io/screenshots/{uuid}.png`.

Fisier:

- `ScannerViewModel.kt`

Probleme:

- API key hardcodat in APK.
- `visibility: unlisted` este setat in client; ramane recomandata mutarea pe backend/proxy si cache.
- parseaza sumarul principal urlscan, dar nu inca raportul complet ca iOS.
- foloseste verdict, HTTP status, IP, tara si server; mai lipsesc ASN, TLS, certificate, resources si verdicturi detaliate.
- nu are retry/backoff matur.

Trebuie:

- cheile mutate pe backend sau remote config securizat.
- preferabil scanari private/unlisted daca planul permite.
- model `SandboxScanResult` similar iOS.
- afisare completa: verdict, IP, ASN, country, server, TLS, redirect chain, screenshot, link raport.
- salvare in history a sandbox data, nu doar state temporar.

## 4. VirusTotal

Status: implementat pe Android cu BuildConfig/local setup.

Implementat:

- URL lookup către `https://www.virustotal.com/api/v3/urls/{id}`.
- parsare `last_analysis_stats` și verdict `Clean / Suspicious / Malicious`.
- agregare top-engine flags din `last_analysis_results`.
- integrare în `ThreatIntelSourceResult` pentru afișare în rezultat.

Ce mai rămâne:

- ideal: mutarea cheilor pe backend/proxy (actual: `BuildConfig` din `local.properties`)
- model dedicat strict tipizat pentru răspunsul VT.

## 5. Google Web Risk

Status: implementat pe Android cu BuildConfig/local setup.

Implementat:

- apel la `uris:search` pe `https://webrisk.googleapis.com/v1/uris:search`.
- lookup URL cu threat types: `MALWARE`, `SOCIAL_ENGINEERING`, `UNWANTED_SOFTWARE`, `SOCIAL_ENGINEERING_EXTENDED_COVERAGE`.
- afișare threat intel cu `No Threats` / `Threats Detected`.
- integrare în `ThreatIntelSourceResult` pentru afișare în rezultat.

Ce mai rămâne:

- recomandat: endpoint backend/proxy pentru a evita expunerea cheilor.

## 6. OCR imagine

Status: real, dar folosit ca fallback.

Implementat:

- upload imagine la backend `/v1/scan/image`.
- daca backend esueaza, ruleaza ML Kit Text Recognition local.
- textul OCR local este scanat ca text.

Probleme:

- OCR local apare doar dupa esec cloud, nu ca pas standard.
- nu se afiseaza text OCR extras.
- nu exista detectare screenshot cu link ascuns separat de text vizibil.

Trebuie:

- OCR local ca pas explicit si afisat.
- upload imagine + OCR local combinate, nu mutually exclusive.
- parsare URL din OCR.
- test cu screenshots reale WhatsApp/SMS/email.

## 7. QR scan

Status: real + aproape complet pentru MVP.

Implementat:

- CameraX `PreviewView` + `ImageAnalysis` cu ML Kit Barcode Scanner live.
- cerere de permisiune CAMERĂ + fallback la „scanează din poză”.
- overlay live de ghidare a cadrului QR.
- buton torch/lanternă cu detectare a disponibilității.
- debouncing pentru a evita scanări duplicate.

Îmbunătățiri rămase:

- optimizare UX pentru mesaje de stare/eroare (text clar la timeout/lipsă lumină).
- testare pe multiple dispozitive (camera front/back, low light).

## 8. PDF/email/files

Status: real la upload, 1:1 mai apropiat pe fallback local.

Implementat:

- upload PDF la `/v1/scan/pdf`.
- upload email la `/v1/scan/email`.
- text/html/eml citite local ca text si URL-uri extrase.
- HTML link extraction exista, dar simplificat/custom.
- parser MIME Android basic pentru EML (text/plain + multipart, base64/quoted-printable) este implementat.

Probleme:

- PDF fallback local foloseste `PdfRenderer` + OCR local (ML Kit), plus extracție avansată din `PdfAnnotation`/`/URI` când există (cu parser separat `PdfLinkExtractor`), apoi extrage linkuri din textul rezultat.
- parser MIME matur (headers + attachment filtering + caractere speciale) mai are nevoie de hardening.
- `uriToFile` include cleanup robust pentru fisiere temporare din cache dupa upload.
- exista limitare upload 25MB pentru fișierele trimise spre cloud.

Trebuie:

- Extracție avansată din PDF annotations dacă sunt prezente (în paralel cu OCR). ✅ (implementat)
- parser EML robust + extra metadata headers (From/To/Subject, return-path etc.).
- limit size si error UI clar.

## 9. Share Android

Status: real, dar trebuie intarit.

Implementat:

- `ACTION_SEND` si `ACTION_SEND_MULTIPLE`.
- text/plain, text/html, message/rfc822, image, pdf.
- deep link `sigurscan://scan`.
- share-uri din text/HTML au acum preview înainte de scanare (banner + acțiune manuală).
- pentru share-uri de fișier, Android acum pune în coadă fișierele și permite scanare manuală pe fiecare item (nu mai are scanare automată imediată).

 Probleme rămase:

- intent filters foarte largi cu `*/*`.
- încă nu avem ecran dedicat de share ca iOS Share Extension (cu UI separat și persistare explicită).
- nu există filtrare SMS (echivalent direct SMS Filter iOS).

Trebuie:

- Share/import screen dedicat.
- tratare multipla: toate fisierele sau selectie.
- restrictii MIME mai curate.
- telemetry privacy-safe pentru sursa inputului.

Actualizare 2026-06-01:
- partajarea text/HTML are acum preview in-app înainte de scanare (banner de confirmare + acțiune manuală),
- procesarea automată imediată pe share pentru text/plain și text/html a fost eliminată,
- fluxul de fișiere nu mai scanează „din mers”; fiecare fișier poate fi confirmat manual.

## 10. Radar scam-uri

Status: real, harta embedded adăugată.

Implementat:

- campanii din backend `/v1/community/campaigns`.
- fallback local cand backend esueaza.
- fara Supabase Realtime direct din client; aplicatia citeste campaniile prin backend.
- poate deschide locatie in Google Maps/app externa.

Lipsesc:

 - clustering/zoom (opțional).

Trebuie:

- harta embedded (WebView + Leaflet) se poate inlocui ulterior cu Google Maps Compose, dar este funcțională acum.
- markers și bottom card la selectare (implementate).
- refresh manual prin buton (implementat) + auto refresh periodic opțional.
- fallback vizual fara a induce ca datele fallback sunt live.
- RLS Supabase hardening: anon nu trebuie sa aiba acces la telemetry/device/feedback/community reports brute.

## 11. Notification Listener

Status: local/demo, nu protectie reala.

Implementat:

- citeste notificari WhatsApp/SMS-like.
- extrage URL-uri.
- evalueaza risc local.
- scrie doar in Logcat.

Nu face:

- nu notifica userul.
- nu blocheaza.
- nu trimite spre backend.
- nu salveaza eveniment.
- nu are UI de alerte reale.

Trebuie:

- clarificat daca vrem aceasta functionalitate in produs, din cauza sensibilitatii Play Store/privacy.
- daca da: consent explicit, privacy screen, local-only processing, notificare de alerta in app, istoric alerte, opt-out.
- nu promitem blocare daca nu putem bloca.

## 12. Family protection

Status: local-only/demo functional.

Implementat:

- adaugare membru local.
- toggle protected.
- alerte locale generate din scanarea curenta.
- scor local calculat simplu.

Nu este real cloud:

- nu trimite alerte catre alt dispozitiv.
- nu are invite/pairing.
- nu are push.
- nu are backend family graph.

Trebuie:

- backend/Supabase tables pentru members, guardians, invites, alerts.
- flow invitatie cu cod/link.
- push notification real catre membru/guardian.
- confirmare livrare alerta.
- privacy si consimtamant.

## 13. Istoric si persistenta

Status: real local, dar nesecurizat.

Implementat:

- SharedPreferences `nudaclick_prefs` (migrare la EncryptedSharedPreferences dacă platforma suportă `security-crypto`).
- history, triage state, education state, family members, family alerts.

Probleme:

- fallback necriptat posibil pe anumite medii în lipsa infrastructurii AndroidX Security.
- backup activ poate include date sensibile.
- nu exista schema versioning.
- nu exista cleanup cache.

Trebuie:

- Room pentru istoric scanari.
- EncryptedSharedPreferences/DataStore pentru settings sensibile.
- backup exclude pentru istoric/scan payloads.
- data retention: limita, clear all, export optional.

## 14. Educatie

Status: real local, continut incomplet.

Implementat:

- 3 lectii hardcodate.
- quiz.
- progres persistat.

Trebuie:

- 6 lectii ca iOS minimum.
- daily tip.
- progres vizual complet.
- continut versionat, eventual remote-config/backend.
- analytics privacy-safe pentru lectii completate.

## 15. Triage/Urgenta

Status: real local, destul de bun.

Implementat:

- 4 categorii.
- checklist persistat.
- apel DNSC 1911.

Trebuie:

- continut aliniat 1:1 cu iOS si validat legal/operational.
- export/partajare checklist incident.
- optiuni rapide: banca, DNSC, schimbare parole, dezinstalare remote apps.

## 16. Readiness/Rapoarte

Status: real partial, mai mult intern/admin.

Implementat:

- readiness, quality, feedback samples, reputation stats din backend.

Probleme:

- utilitatea pentru user final este discutabila.
- modele `Map<String, Any>` fragile.
- nu exista cache/error UI matur.

Trebuie:

- clarificat daca ramane in app public sau dev/admin.
- daca ramane: traducere user-friendly, nu metrici brute.
- modele stricte si loading/error states.

## 17. Contrast checker

Status: real, dar minimal.

Implementat:

- calculeaza contrast ratio pentru cateva perechi.

Trebuie:

- catalog complet `SigurColors`.
- filtre AA/AAA.
- ColorPicker interactiv.
- teste automate pentru WCAG.

## 18. Securitate/API keys

Status: controlat pentru v1, cu providerii prin backend si Supabase direct scos din client.

Configurare:

- urlscan.io/VirusTotal/Google Web Risk keys sunt backend-side pentru release.
- Supabase service role este server-only.
- APK-ul nu trebuie sa contina Supabase anon/service key.

Probleme:

- verificarea remote trebuie sa confirme ca Vercel are variabilele corecte si RLS migration este aplicata.

Ce a fost făcut:

- `HttpLoggingInterceptor` este pe `Level.NONE`.
- `SupabaseManager` direct din Android a fost eliminat.
- device registration automat pe `ANDROID_ID` a fost eliminat.
- feedback/community reports merg prin backend.

Trebuie:

- aplicare remote a migrarii RLS de hardening in Supabase.
- eliminare BODY logging in release.
- secret scanning si CI checks.

## 19. Testare si build

Status: insuficient pentru produs matur.

Exista:

- teste sample Android Studio.
- un test ScannerViewModel, dar nu acopera produsul complet.

Trebuie:

- unit tests pentru offline rules.
- API contract tests cu mock server.
- UI tests pentru scan/share/history/triage.
- integration tests pentru ML Kit OCR/QR cu fixtures.
- regression tests pentru parsing HTML/EML/PDF.
- build release cu minify/proguard activ.

## Ordine recomandata de executie

1. Stabilizam arhitectura: separare `MainActivity.kt` in screens/components/services/models.
2. Modele stricte pentru scan result, evidence, email auth, external intel.
3. Securitate: scoatem logging BODY, backup pentru date sensibile, storage criptat.
4. Portam VirusTotal + Google Web Risk prin backend proxy.
5. QR live CameraX.
6. urlscan complet: model complet + UI complet + privacy visibility.
7. PDF fallback local avansat (annotations) + EML parser matur.
8. Radar embedded (WebView + Leaflet, eventual upgrade Google Maps Compose).
9. Family cloud + push real.
10. Educatie completa 1:1 cu iOS.
11. Teste automate si release hardening.

## Concluzie

Android nu mai trebuie tratat ca MVP. Pentru versiune matura, trebuie transformat intr-o aplicatie cu pipeline real de threat intelligence, storage securizat, servicii externe prin backend, UI modular si teste. Cele mai urgente gap-uri functionale sunt QR live, harta radar, family cloud/push si EML parser matur.
