# SigurScan - Codex 8PM Research Execution Result

Ultima actualizare: 2026-06-02

Scop: rezultatul meu separat, comparabil cu ce urmeaza sa dea GPT 5.5 Pro Web la 8 PM. Am citit brief-ul din `GPT55_PRO_8PM_PIPELINE_BRIEF.md`, am verificat codul Android existent si am validat directiile pe surse oficiale.

## 1. Verdict executiv

Directia corecta este deja aleasa: SigurScan trebuie sa fie un sistem de dovezi, nu un detector speriat de marketing.

Formula pe care as bloca produsul:

`Input -> Extractor -> Normalizer -> Primary URL -> Web Risk/cache -> urlscan preview -> Evidence Gate -> VT fallback daca trebuie -> RAG explanation -> User action`

Regula centrala:

- Nu marcam scam doar pentru HTML email.
- Nu marcam scam doar pentru link sub buton.
- Nu marcam scam doar pentru tracking link.
- Nu marcam scam doar pentru "voucher", "profita acum", "ultima sansa", "nu rata".
- Decidem pe destinatia reala, brand match, ce cere pagina finala, reputatie si blacklist-uri.

User-facing:

- `Poti continua cu prudenta`
- `Nu continua`
- `Nu introduce date`
- `Nu raspunde`
- `Verifica pe canalul oficial`
- `Nu pot verifica suficient`

Nu folosim ca raspuns principal:

- `suspect`
- `70% risc`
- `100% sigur`
- `garantat legitim`

## 2. Surse reale consultate si implicatii

| Sursa | Ce confirma | Implicatie pentru SigurScan |
| --- | --- | --- |
| Google Web Risk Lookup API: https://cloud.google.com/web-risk/docs/lookup-api | `uris.search` verifica URL-uri pe liste Web Risk si raspunde cu `threatTypes` plus `expireTime` cand exista match. Raspuns gol `{}` inseamna fara match cunoscut. | Web Risk este fast check puternic, dar `No Threats` nu inseamna "safe garantat". |
| Google Web Risk Lists: https://cloud.google.com/web-risk/docs/lists | Listele acopera resurse unsafe: phishing/social engineering, malware, unwanted software. | Web Risk match poate produce `Nu continua`. |
| Google Web Risk Caching: https://cloud.google.com/web-risk/docs/caching | Clientii trebuie sa mentina cache local pentru threat data, iar Lookup API cache-uieste itemii returnati pana la `expireTime`. | Am adaugat cache local Web Risk in Android; in productie trebuie mutat pe backend. |
| Google Web Risk Pricing: https://cloud.google.com/web-risk/pricing | `uris.search` are free tier pana la 100.000 call-uri/luna, apoi cost per 1.000 call-uri. | Trebuie cache si orchestration, nu scanari duplicate. |
| urlscan API: https://urlscan.io/docs/api/ | Are visibility `public`, `unlisted`, `private`; recomanda PII removal, rate-limit respect, backoff, work queue; screenshot este disponibil la `/screenshots/{uuid}.png`; Result API poate raspunde 404 pana se termina scanarea. | urlscan este moat-ul principal, dar trimitem doar URL sanitizat, nu email complet; default `unlisted`/`private`, niciodata `public` pentru user content. |
| VirusTotal URL identifiers: https://docs.virustotal.com/reference/url | URL id poate fi base64 URL-safe fara padding. | Implementarea Android de URL id este corecta ca directie. |
| Android Intent `EXTRA_HTML_TEXT`: https://developer.android.com/reference/android/content/Intent#EXTRA_HTML_TEXT | `ACTION_SEND` poate furniza HTML alternativ pentru `EXTRA_TEXT`; trebuie furnizat si `EXTRA_TEXT`. | Share-ul din Gmail/Outlook/Yahoo poate da HTML doar daca aplicatia sursa il trimite. Noi trebuie sa citim HTML cand exista si sa afisam fidelitatea inputului. |
| Google Play User Data policy: https://support.google.com/googleplay/android-developer/answer/10144311 | Security apps trebuie sa aiba privacy policy; datele sensibile trebuie tratate sigur, cu disclosure/consent cand e cazul. | Pentru release, trebuie privacy policy, data safety, explicare servicii terte si minimizare date. |
| DNSC/PNRISC blacklist: https://sigurantaonline.ro/comunicat-de-presa-directoratul-national-de-securitate-cibernetica-dnsc-simplifica-raportarea-incidentelor-cibernetice-si-lanseaza-o-platforma-publica-de-tip-blacklist-pentru-domenii-rau-intentiona/ | DNSC anunta platforma PNRISC si blacklist public de domenii rau intentionate. | Merita provider Romania, dar nu am validat un API/feed stabil accesibil automat; nu facem scraping agresiv fara termeni/API. |

## 3. Ce exista deja in Android

Implementat si verificat in cod:

- Share Intent citeste `EXTRA_HTML_TEXT`, `EXTRA_TEXT`, `EXTRA_STREAM` si `ClipData`.
- App-ul poate marca sursa ca `Continut HTML partajat`, `Continut text partajat`, `Continut HTML din ClipData`.
- `HtmlLinkExtractor` are parsing avansat: `href`, CSS `url(...)`, data URI HTML/SVG/text, redirect wrappers, `safelinks`, `google.com/url`, `facebook/l.php`, `urldefense`, `sng.link`, `app.link`, `branch.link`, `bnc.lt`.
- Parserul face normalizare anti-obfuscation de baza: comentarii HTML, zero-width/invisible chars, soft hyphen, bidi controls.
- `MailEvidenceGate` previne false positive pe marketing normal: Uber real cu `rides.sng.link` + fallback `uber.com` nu devine `Mail cu link ascuns`.
- `ThreatIntelOrchestrator` trimite urlscan cu `visibility=unlisted` si sanitizeaza query params sensibili/tracking.
- Web Risk ruleaza inainte de VirusTotal.
- VirusTotal ruleaza doar fallback cand riscul local/evidence-ul este neclar sau ridicat.
- Sursa externa high severity, precum Web Risk/urlscan/VT, poate escalada verdictul la risc ridicat.
- UI-ul foloseste raspunsuri action-first: `Nu continua`, `Verifica oficial`, `Nu pot verifica`, `Poti continua`.

Modificari executate acum de mine:

- Am adaugat cache local Web Risk in `ScannerViewModel`.
- Cache-ul respecta `expireTime` cand Web Risk returneaza threat.
- Pentru `No Threats`, cache-ul este scurt, doar pentru cost/retry guard, nu ca dovada absoluta de siguranta.
- Am extins testul de sanitizare urlscan pentru `reset`, `uid`, `bid`, `pcid`, `u_action_id`.

## 4. Ce NU este inca 100% client-ready

Acestea sunt gap-uri reale, nu cosmetica:

- Cheile Web Risk/urlscan/VirusTotal inca ajung prin `BuildConfig` in client. Pentru productie trebuie backend/proxy.
- Evidence-ul este inca imprastiat in `ScannerViewModel` si modele partiale. Trebuie `EvidenceSnapshot` strict.
- `EvidenceGate` exista partial (`MailEvidenceGate` + `ThreatIntelOrchestrator`), dar nu este inca gate unic pentru toate sursele.
- urlscan ruleaza direct din Android. Pentru privacy, cache, rate-limit si API key protection trebuie backend.
- Web Risk ruleaza direct din Android. Cache local ajuta, dar backend ramane varianta corecta.
- DNSC/PNRISC trebuie provider modular, nu scraping.
- Offer checker/RAG trebuie sa fie explicator si evidence source, nu judecator liber.
- Nu exista inca corpus runner complet pentru toate acceptance tests cu expected verdict si false-positive tracking.
- Lipseste schema finala backend pentru feedback loop user-driven: false positive, false negative, wrong brand, wrong action.

## 5. Orchestrarea recomandata finala

### Pasul 1: Intake

Primim:

- text simplu;
- HTML share;
- ClipData HTML/text/URI;
- stream/atasament;
- imagine/QR/OCR;
- fisier email, daca userul il are;
- link direct.

Nu decidem aici.

### Pasul 2: Extractor

Extragem:

- text vizibil;
- link vizibil;
- `href` real;
- butoane/CTA;
- CSS URL;
- data URI;
- JS redirect hints simple;
- meta refresh;
- form action;
- sender/subject/reply-to daca exista `.eml`;
- QR/OCR links.

### Pasul 3: Normalizer + Primary URL Picker

Alegem URL-ul principal:

- CTA principal;
- linkul pe care userul ar apasa;
- final URL posibil din wrapper;
- domeniu legat de brand claim.

Eliminam:

- tracking pur;
- resource links de webmail shell;
- query params cu PII/tokenuri.

### Pasul 4: Fast reputation

Ruleaza:

- cache intern;
- official domains registry;
- Web Risk;
- blacklist provider Romania, daca avem feed verificat.

Daca Web Risk/blacklist confirma risc, putem da rapid `Nu continua`, iar urlscan poate continua async ca preview.

### Pasul 5: urlscan preview

Ruleaza pe `primary_url` sanitizat.

Produce:

- screenshot;
- final URL;
- redirect chain;
- verdict;
- report URL;
- server/IP/country doar in detalii tehnice.

Preview indisponibil nu inseamna safe.

### Pasul 6: Evidence Gate

Gate-ul decide daca avem dovezi suficiente.

Nu permite `DANGEROUS` doar din:

- HTML;
- link sub buton;
- tracking;
- marketing urgency;
- short link fara alta dovada.

### Pasul 7: VirusTotal fallback

Ruleaza doar daca:

- urlscan nu e gata/nu raspunde;
- Web Risk e clean, dar avem brand mismatch + context sensibil;
- final domain necunoscut cere card/OTP/parola/CNP/IBAN/login;
- sursele se contrazic;
- userul cere analiza extinsa.

### Pasul 8: RAG/offer checker

Ruleaza dupa evidence:

- explica dovezile;
- compara cu corpus;
- spune daca oferta nu are confirmare oficiala;
- nu inventeaza domenii oficiale;
- nu schimba verdictul singur.

## 6. Evidence Gate matrix

### `Nu continua`

Afisam cand exista:

- Web Risk match malware/social engineering/phishing;
- blacklist Romania match verificat;
- urlscan malicious;
- VT malicious relevant in fallback;
- brand mismatch clar + pagina cere actiune riscanta;
- link vizibil oficial, dar final URL neoficial si intent sensibil;
- download APK/remote access neoficial.

### `Nu introduce date`

Afisam cand pagina cere:

- card;
- CVV/CVC;
- OTP;
- parola/PIN;
- CNP;
- IBAN;
- login;
- plata;

si domeniul final/form action nu este oficial pentru brandul pretins.

### `Nu raspunde`

Afisam cand mesajul cere prin reply:

- coduri;
- date personale;
- date card;
- poza document;
- transfer bani;
- instalare aplicatie remote.

### `Verifica pe canalul oficial`

Afisam cand:

- avem semnale medii, dar nu strong evidence;
- brand mentionat + link neoficial, fara formular sensibil confirmat;
- oferta nu poate fi confirmata;
- sender/reply-to mismatch;
- tracking/fallback nu poate fi validat;
- context sensibil banca/ANAF/curier, dar sursele sunt incomplete.

### `Nu pot verifica suficient`

Afisam cand:

- nu exista URL/final URL;
- urlscan/Web Risk nu pot rula;
- webmail share a trimis doar shell-ul, nu corpul emailului;
- sursele sunt conflictuale;
- inputul are doar text vag.

### `Poti continua cu prudenta`

Afisam doar cand:

- final URL este cunoscut;
- domeniul final este oficial sau tracking legitim cu fallback oficial;
- Web Risk nu are match;
- nu exista blacklist match;
- urlscan nu este malicious daca a rulat;
- nu cere date sensibile pe domeniu neoficial;
- brandul si contextul sunt coerente.

## 7. Raspunsuri explicite la intrebarile din brief

1. Cand avem voie `Poti continua cu prudenta`?
   Doar dupa benign coherence set: final URL cunoscut, domeniu oficial/tracking legitim, reputatie fara match, fara intent sensibil neoficial.

2. Cand avem voie `Nu continua`?
   Cand exista strong signal: Web Risk/blacklist/urlscan/VT malicious sau brand mismatch cu intent real de fraudare.

3. Cand folosim `Verifica pe canalul oficial` in loc de `Nu continua`?
   Cand dovezile sunt medii, nu puternice: mismatch contextual, oferta neconfirmata, sender dubios, tracking nevalidat, dar fara formular sensibil sau reputatie malicious.

4. Cand folosim `Nu pot verifica suficient`?
   Cand lipseste final URL sau sursele tehnice nu au dat date suficiente.

5. Daca urlscan e clean, dar pagina cere card pe domeniu neoficial?
   `Nu introduce date`. Intentul si domeniul bat un sandbox clean.

6. Daca Web Risk e clean, dar brand mismatch + form action dubios exista?
   `Nu introduce date` sau `Nu continua`. Web Risk clean inseamna doar fara match cunoscut.

7. Daca emailul are tracking link legitim catre domeniu oficial?
   `Poti continua cu prudenta`, daca nu exista alta dovada de risc.

8. Daca exista doar `voucher/profita acum/nu rata`?
   Maxim `Verifica pe canalul oficial` daca contextul e sensibil; niciodata `Nu continua` doar din cuvinte.

9. Cand ruleaza VT?
   Numai fallback: conflict, urlscan indisponibil, Web Risk clean dar semnale locale puternice, domeniu necunoscut cu intent sensibil.

10. Ce ascundem implicit?
    VT raw engines, Web Risk raw threat types, urlscan raw JSON, IP/ASN/server/country, redirect chain complet, rule IDs, provider errors, RAG internals.

## 8. Corpus minim pentru Romania

Fiecare caz trebuie sa aiba:

- `case_id`;
- `input_type`;
- `raw_input_redacted`;
- `html_available`;
- `visible_text`;
- `extracted_urls`;
- `primary_url`;
- `final_url`;
- `claimed_brand`;
- `official_expected_domains`;
- `page_intent`;
- `external_reputation`;
- `expected_internal_verdict`;
- `expected_user_action`;
- `false_positive_guard`;
- `reason`.

Cazuri obligatorii:

- Uber real promo cu `rides.sng.link` si fallback `uber.com`.
- Uber fake cu card/OTP pe domeniu neoficial.
- eMAG real newsletter.
- eMAG fake premiu/card.
- FAN real AWB.
- FAN fake taxa/card.
- ANAF fake SPV/login/plata.
- Revolut visible link mismatch.
- Web Risk malware test.
- example.com.
- urlscan unavailable.
- Yahoo/Gmail shell HTML fara corp real.
- marketing urgency benign.

## 9. Implementare recomandata dupa aceasta runda

Ordinea pragmatica:

1. Mutam Web Risk/urlscan/VT in backend/proxy.
2. Definim `EvidenceSnapshot`, `GateResult`, `UserResult`.
3. Facem `PrimaryUrlPicker` separat.
4. Facem `EvidenceGate` unic, nu reguli imprastiate.
5. Facem corpus runner pentru acceptance tests.
6. Adaugam provider modular DNSC/PNRISC doar daca avem feed/API clar.
7. Legam feedback user: `wrong_verdict`, `false_positive`, `false_negative`, `wrong_brand`, `preview_failed`.
8. RAG ramane doar explicator dupa gate.

## 10. Comparatie asteptata cu GPT 5.5 Pro

Daca GPT 5.5 Pro da o lista foarte avansata, dar nu raspunde la aceste patru intrebari, nu e suficient:

- Ce dovezi sunt suficiente pentru `Nu continua`?
- Cand nu avem voie sa spunem `Nu continua`?
- Cand rulam VT si cand il sarim?
- Cum prevenim cazul Uber real clasificat eMAG scam?

Pentru produsul nostru, raspunsul bun este disciplinat, nu grandios.

Verdictul meu:

SigurScan Android are deja scheletul corect pentru share HTML + hidden link extraction + urlscan preview + Web Risk + VT fallback. Nu este inca 100% client-ready pentru productie larga pana nu mutam orchestration/API keys/cache/corpus pe backend si pana nu avem EvidenceGate unic + corpus runner. Pentru demo si test controlat, directia este buna.
