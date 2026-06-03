# SigurScan Android - final scan pipeline execution

Ultima actualizare: 2026-06-02

Scop: document de executie pentru implementarea pipeline-ului final Android/backend. Produsul trebuie sa ramana light, orientat Romania, cu preview ca moat principal si cu informatii tehnice ascunse sub capota.

## Principiul produsului

Userul nu vrea threat intelligence. Userul vrea raspuns la intrebari simple:

- Pot sa apas pe link?
- Pot sa raspund la email?
- Pot sa platesc?
- Pot sa introduc date/card/parola/OTP?
- Trebuie sa verific pe canal oficial?

Rezultatul principal trebuie sa fie o decizie actionabila, nu o lista tehnica de surse.

## Decizia afisata userului

Pastreaza patru clase user-facing, dar formulate ca actiuni, nu ca verdicte absolute.

1. `LOW_RISK`
   Text principal: `Poti continua cu prudenta`

2. `SUSPICIOUS`
   Text principal: `Verifica pe canalul oficial`

3. `DANGEROUS`
   Text principal: `Nu continua`

4. `UNKNOWN`
   Text principal: `Nu pot verifica suficient`

Pentru email/formulare/plati, textul trebuie adaptat contextual:

- `Nu raspunde la email`
- `Nu trimite date`
- `Nu introduce cardul`
- `Nu trimite coduri OTP`
- `Verifica direct in aplicatia/site-ul oficial`

Nu folosi `Sigur` ca verdict absolut. Foloseste `Risc scazut` sau `Nu am gasit semnale cunoscute de risc`.

Scorul procentual poate ramane pentru UI, dar este secundar. Actiunea principala este mai importanta decat procentul.

## UI final recomandat

### Main result card

Afiseaza maxim aceste informatii deasupra fold-ului:

- snapshot/preview securizat al paginii finale, daca exista;
- decizie mare: `Nu continua`, `Verifica pe canalul oficial`, `Nu pot verifica suficient`, `Poti continua cu prudenta`;
- scor procentual mic, doar decorativ;
- 1-2 motive in limbaj uman;
- domeniul final vizibil, ex: `Te duce catre: example.xyz`;
- CTA clar, ex: `Deschide site-ul oficial`, `Raporteaza`, `Verifica manual`, `Inapoi`.

### Informatii ascunse in Advanced details

Mutati in expandable/collapsed section:

- VirusTotal engines;
- Web Risk raw threat types;
- urlscan HTTP status, IP, country, server, ASN;
- redirect chain complet;
- technical evidence;
- rule IDs;
- backend model details.

Userul normal nu trebuie sa vada IP-uri, ASN, engine counts, JSON sau termeni tehnici ca `threat intelligence`, decat daca apasa explicit pe `Detalii tehnice`.

## Pipeline final

### 0. Input classification

Clasifica inputul inainte de scor:

- `url_only`
- `message_text`
- `email_html_or_eml`
- `pdf`
- `image_ocr`
- `qr`
- `offer_claim`
- `unknown`

Extrage:

- URL-uri vizibile;
- URL-uri ascunse in HTML;
- text vizibil;
- sender/from/reply-to, daca exista;
- brand claims posibile;
- formulare/linkuri de plata/login;
- context: SMS, email, WhatsApp, QR, PDF.

### 1. Normalize and canonicalize URLs

Pentru fiecare URL:

- normalizeaza schema si host;
- elimina trailing punctuation;
- converteste IDN/punycode;
- extrage eTLD+1/domain root;
- elimina query params sensibili inainte de sandbox cand se poate.

Query params sensibili de redactat inainte de urlscan:

- `email`
- `e-mail`
- `mail`
- `token`
- `auth`
- `session`
- `sid`
- `code`
- `otp`
- `reset`
- `uid`
- `user`
- `phone`
- `cnp`
- `iban`

Nu trimite niciodata emailul complet catre urlscan. Trimite doar URL-ul tinta sanitizat.

### 2. Fast verdict sources

Aceste surse pot da verdict rapid:

- backend `/v1/scan/url` sau `/v1/scan/text`;
- reguli locale/backend pentru Romania;
- Web Risk Lookup;
- cache intern/domain memory;
- DNSC blacklist, daca se poate integra.

Web Risk este sursa Google comerciala pentru verdict rapid. Safe Browsing API direct nu trebuie folosit in produs comercial fara acord separat.

### 3. Preview moat via urlscan

Preview-ul este feature-ul central.

Regula principala:

- pentru `url_only`, ruleaza preview pentru URL-ul principal;
- pentru email/text cu mai multe URL-uri, ruleaza preview doar pentru URL-ul principal ales;
- pentru restul URL-urilor, ofera buton `Analizeaza toate linkurile`, nu rula automat urlscan pe toate.

Privacy si legal:

- foloseste `unlisted` sau `private`, nu `public`;
- sanitizeaza URL-ul inainte de submit;
- nu trimite continutul emailului catre urlscan;
- nu promite ca preview-ul este infailibil, pentru ca site-urile pot face cloaking.

Cost control:

- maxim 1 urlscan submit per scanare user default;
- cache pe `normalizedUrl`, `finalUrl`, `domain`, `screenshotHash`;
- nu resubmite acelasi URL daca exista rezultat recent;
- foloseste polling cu backoff;
- daca preview-ul nu e gata, afiseaza verdictul rapid si actualizeaza async.

### 4. VirusTotal standby

VirusTotal nu este pilon obligatoriu pentru fiecare scanare.

Ruleaza VT doar daca:

- Web Risk nu gaseste nimic, dar scorul local/backend este `SUSPICIOUS` sau `DANGEROUS`;
- urlscan este indisponibil;
- domeniul este nou/dubios;
- userul cere analiza extinsa;
- avem nevoie de confirmare suplimentara in cazuri incoerente.

VT trebuie sa fie backend/proxy, cu cache si rate limiting. Nu baza produsul pe cheia client-side.

### 5. DNSC blacklist

Integrarea DNSC este foarte valoroasa pentru Romania.

Tinta:

- verifica domain root si URL normalizat in blacklist-ul DNSC, daca exista endpoint sau feed accesibil;
- daca nu exista API stabil, pastreaza integrarea ca modul backend `dnsc_blacklist_provider` cu configuratie separata;
- nu face scraping agresiv al platformei DNSC.

In UI, daca DNSC confirma:

- `Domeniul apare intr-o lista publica de risc DNSC.`

Nu afirma afiliere oficiala cu DNSC daca nu exista parteneriat.

### 6. Offer verification

Nu numi feature-ul `verificam daca oferta este adevarata`.

Nume recomandat:

- `Semnale de oferta inselatoare`
- `Verificare oferta pe surse oficiale`

Important:

- cuvinte precum `azi doar`, `revendica`, `oferta limitata`, `voucher` sunt marketing normal si nu trebuie sa ridice singure scorul;
- acestea sunt semnale slabe;
- devin puternice doar impreuna cu domeniu neoficial, cerere de card/parola/OTP, plata mica pentru premiu/colet, brand mismatch sau reputatie negativa.

Pipeline oferta:

- extrage brandul pretins;
- extrage promisiunea: voucher, premiu, reducere, rambursare, livrare, investitie;
- compara domeniul linkului cu domeniul oficial;
- daca userul cere verificare sau riscul este neclar, ruleaza search controlat prin API, nu scraping haotic;
- cauta intai surse oficiale ale brandului;
- daca oferta nu apare pe surse oficiale, verdictul este `Nu am gasit confirmare oficiala`, nu `Fals`.

Output corect:

- `Oferta este confirmata pe sursa oficiala: emag.ro/...`
- `Nu am gasit aceasta oferta pe sursa oficiala. Verifica direct in aplicatia/site-ul brandului.`
- `Oferta cere card/date pe un domeniu neoficial. Nu introduce date.`

## Verdict merge logic

Scorul final trebuie sa fie determinist si explicabil.

Semnale foarte puternice:

- Web Risk match `MALWARE` sau `SOCIAL_ENGINEERING`;
- DNSC blacklist match;
- urlscan verdict malicious/phishing;
- pagina finala cere card/parola/OTP pe domeniu neoficial;
- brand claim clar + domeniu real neoficial;
- form action extern suspect;
- link ascuns in HTML catre domeniu diferit de textul vizibil.

Semnale medii:

- VT malicious/suspicious engines;
- domeniu foarte nou;
- shortener/redirect chain complex;
- expeditor/reply-to mismatch;
- URL cu IDN/confusables;
- pagina fara brand consistency;
- text primit nesolicitat.

Semnale slabe:

- `azi doar`;
- `oferta limitata`;
- `revendica`;
- `voucher`;
- `promotie`;
- ton urgent generic.

Regula critica:

- semnalele slabe nu pot produce singure `DANGEROUS`;
- semnalele slabe pot creste scorul doar daca exista minimum un semnal mediu sau puternic.

## Fix pentru false positives de brand

Problema observata: email real de la Uber clasificat ca scam eMAG.

Regula noua:

- Nu asigna familie/brand doar din cuvinte generice de marketing.
- `voucher`, `promotie`, `oferta`, `livrare`, `reducere` nu inseamna eMAG.
- Brandul trebuie confirmat prin evidenta concreta.

Brand evidence acceptata:

- brandul apare explicit in text vizibil sau subiect;
- domeniul senderului contine domeniul oficial;
- linkul final este pe domeniu oficial;
- logo/text/HTML mentioneaza clar brandul;
- backend trimite `claimed_brand` cu confidence suficient.

Brand confidence recomandat:

- `high`: sender official + domain official + text brand consistent;
- `medium`: text mentioneaza brand + link catre domeniu apropiat/neoficial;
- `low`: doar keyword generic sau context slab.

Nu permite `low confidence brand` sa schimbe familia in UI.

Daca brandul este neclar:

- foloseste `Oferta suspecta`, `Mesaj promotional`, `Link extern`, `Email nesolicitat`;
- nu inventa brand.

Exemplu corect:

- email Uber de la domeniu Uber, cu oferta Uber: `LOW_RISK` sau `SUSPICIOUS` daca exista alta problema, brand `Uber`;
- nu il marca `eMAG scam`.

## Data model recomandat

Backend sau ViewModel trebuie sa produca un model final simplu:

```kotlin
data class UserDecision(
    val actionClass: ActionClass,
    val headline: String,
    val riskScore: Int,
    val confidence: String,
    val shortReason: String,
    val nextBestAction: String,
    val finalDomain: String?,
    val preview: PreviewResult?,
    val sourceSummary: List<HumanSourceSummary>,
    val technicalDetails: TechnicalDetails?
)

enum class ActionClass {
    LOW_RISK,
    SUSPICIOUS,
    DANGEROUS,
    UNKNOWN
}
```

`sourceSummary` trebuie sa fie uman, nu raw:

- `Google Web Risk nu a gasit semnale cunoscute.`
- `Preview-ul duce catre un domeniu diferit de brandul pretins.`
- `Domeniul apare in blacklist DNSC.`
- `VirusTotal are semnale de reputatie negative.`

`technicalDetails` ramane collapsed.

## UI copy obligatoriu

Foloseste:

- `Nu apasa`
- `Nu introduce date`
- `Nu raspunde la email`
- `Verifica pe site-ul oficial`
- `Nu am gasit semnale cunoscute de risc`
- `Nu pot verifica suficient`
- `Preview-ul securizat arata unde duce linkul fara sa intri tu pe site`

Evita:

- `100% sigur`
- `site sigur`
- `garantat legitim`
- `oferta este sigur reala`
- `detectam toate scamurile`
- `oficial DNSC/Politie/ANAF`, fara parteneriat.

Disclaimer scurt in rezultat:

`SigurScan ofera o estimare automata de risc. Scamurile noi sau personalizate pot sa nu fie detectate. Verifica datele importante direct pe site-ul sau in aplicatia oficiala.`

## Legal si privacy guardrails

- Foloseste Web Risk pentru comercial, nu Safe Browsing API direct.
- Daca avertizarea vine din Web Risk, include attribution conform Google doar pentru avertizarea Google.
- Declara in privacy policy ca URL-uri/text/imagini/emailuri pot fi trimise catre backend si servicii terte pentru scanare.
- urlscan trebuie `unlisted` sau `private`, nu `public`.
- Cheile API trebuie sa stea pe backend sau in configuratie securizata, nu hardcodate in APK.
- Nu face screenshot local din alte aplicatii si nu ocoli `FLAG_SECURE`.
- Nu cere SMS/Call Log permissions pentru versiunea light.
- Nu folosi Accessibility API pentru interceptare mesaje.

## Prioritate de implementare pentru Spark

1. Introdu `UserDecision` si maparea UI pe actiuni clare.
2. Simplifica ecranul de rezultat: preview + actiune + 1-2 motive + domeniu final.
3. Ascunde informatiile tehnice in `Detalii tehnice` collapsed.
4. Inlocuieste Google Safe Browsing direct cu Web Risk prin backend/proxy.
5. Configureaza urlscan ca `unlisted/private`, cu sanitizare PII si cache.
6. Ruleaza urlscan default doar pe URL-ul principal, nu pe toate linkurile.
7. Pune VirusTotal in fallback/async, nu ca pas obligatoriu.
8. Adauga provider pentru DNSC blacklist daca exista API/feed stabil.
9. Repara brand classification: fara brand/family din keywords generice.
10. Redenumeste offer checker in `Semnale de oferta inselatoare`.

## Acceptance tests obligatorii

### Test 1: Web Risk malware test

Input: URL de test malware Google.

Expected:

- `DANGEROUS`
- headline: `Nu continua`
- motiv: `Google Web Risk a identificat risc de malware/social engineering.`

### Test 2: Example.com

Input: `https://example.com`

Expected:

- `LOW_RISK` sau `UNKNOWN`, in functie de preview/cache;
- nu afisa `Sigur 100%`;
- nu crea familie scam.

### Test 3: Email Uber legitim

Input: email promotional Uber de pe domeniu oficial Uber.

Expected:

- brand `Uber`, nu `eMAG`;
- fara familie eMAG;
- daca linkurile sunt oficiale, `LOW_RISK` sau `UNKNOWN`;
- daca exista link extern de tracking legitim, explica prudent, nu marca automat scam.

### Test 4: FAN Courier fake SMS

Input: mesaj cu `FAN Courier`, livrare blocata, link catre domeniu neoficial si cere update date.

Expected:

- `DANGEROUS`
- headline: `Nu continua`
- motiv: `Pretinde FAN Courier, dar linkul nu duce catre domeniul oficial.`

### Test 5: Oferta reala cu urgency marketing

Input: oferta reala pe domeniu oficial al magazinului, cu text `azi doar`.

Expected:

- cuvantul `azi doar` nu ridica singur verdictul la scam;
- verdict bazat pe domeniu, reputatie si continut.

### Test 6: Preview indisponibil

Input: URL valid, urlscan fail/rate limit.

Expected:

- nu marca automat safe;
- afiseaza `Nu pot verifica suficient` sau verdict rapid bazat pe celelalte surse;
- mesaj: `Preview indisponibil momentan.`

## Definitia finala a moat-ului

Moat-ul SigurScan nu este VirusTotal si nu este un scor tehnic.

Moat-ul este:

`Iti aratam vizual unde te duce linkul, fara sa intri tu pe site, si iti spunem clar daca sa apesi, sa raspunzi sau sa platesti.`
