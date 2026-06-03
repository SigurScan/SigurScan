# GPT 5.5 Pro Response 2 - Extract Pentru Spec Final

Data: 2026-06-02

Sursa: `/Users/vaduvageorge/.codex/attachments/ed7c264d-f3e0-46d9-9bec-a596267e877f/pasted-text.txt`

Scop: notite filtrate din al doilea material primit. Acesta NU este spec final si NU se implementeaza copy-paste. Este material candidat pentru sinteza finala dupa raspunsurile 2 si 3.

## Verdict Pe Raspunsul 2

Util ca inventar si structura de proiect, dar inca prea permisiv cu verdicturi mari din semnale slabe.

Ce merita pastrat:

- lista de `EvidenceSource` cu provenance clar;
- ideea de `EvidenceSnapshot` si `UserResult`;
- explicitarea starii `UNKNOWN`;
- sectiunea de conflict resolution;
- timeout/fallback ca flow operational;
- cache/TTL per provider;
- sectiunea Google Play compliance;
- lista de acceptance tests;
- sectiunea de false positives / false negatives;
- ideea de health monitoring pentru Web Risk, urlscan si VirusTotal.

Ce trebuie corectat:

- nu folosim agregare simpla pe scoruri pentru verdict final;
- `TEXT_KEYWORD` nu poate da `DANGEROUS`, nici cu limbaj foarte agresiv;
- `HIDDEN_LINK` singur nu poate da `NO_ENTER_DATA` sau `DANGEROUS` fara destinatie/final URL/intent sensibil;
- nu afisam `Poti continua cu prudenta` la 3-8 secunde daca urlscan/final URL/reputatia nu sunt gata;
- nu trimitem notificari automate pentru schimbari asincrone; actualizam in-app/history;
- `OFFICIAL_DOMAIN` nu este antidot universal; nu poate anula reputatie sau sandbox malicious;
- user feedback nu poate ridica la `DANGEROUS` fara validare backend sau corelare puternica;
- evitam permisiuni Android suplimentare in prima versiune daca nu sunt necesare: `FOREGROUND_SERVICE`, storage larg, notification listener, accessibility, SMS.

## Elemente De Pastrat In Modelul De Date

Surse utile:

```kotlin
enum class EvidenceSource {
    TEXT_KEYWORD,
    HIDDEN_LINK,
    STRUCTURAL,
    REPUTATION,
    OFFICIAL_DOMAIN,
    SANDBOX,
    USER_FEEDBACK,
    CORPUS
}
```

Recomandare pentru spec final: adaugam status pe provider, nu doar semnale.

```kotlin
enum class ProviderStatus {
    NOT_NEEDED,
    PENDING,
    AVAILABLE,
    TIMEOUT,
    RATE_LIMITED,
    ERROR
}
```

Motiv: `UNKNOWN` trebuie sa stie daca lipseste informatie pentru ca nu exista URL, pentru ca providerul e cazut, sau pentru ca analiza inca ruleaza.

Snapshot recomandat pentru spec final:

```kotlin
data class EvidenceSnapshot(
    val primaryUrl: String?,
    val finalUrl: String?,
    val redirectChain: List<String>,
    val signals: List<EvidenceSignal>,
    val providerStatus: Map<EvidenceSource, ProviderStatus>,
    val unavailableReasons: List<String>,
    val timestampMillis: Long
)
```

User result recomandat:

```kotlin
enum class AnalysisStage {
    IN_PROGRESS,
    PRELIMINARY,
    FINAL,
    INSUFFICIENT_EVIDENCE
}

data class UserResult(
    val gateResult: GateResult,
    val stage: AnalysisStage,
    val headline: String,
    val recommendations: List<String>,
    val topReasons: List<String>,
    val detailedSignals: List<EvidenceSignal>
)
```

Motiv: userul nu trebuie sa confunde un verdict preliminar cu verdict final.

## Reguli De Decizie De Pastrat, Corectate

### Hard Evidence

Poate da `DANGEROUS`:

- Google Web Risk confirma phishing/malware/social engineering;
- urlscan confirma phishing/malware/brand impersonation clar;
- blacklist validata Romania / DNSC / feed intern validat;
- VirusTotal fallback confirma detectii relevante;
- pagina finala sau formularul cere credentiale/card/OTP/CNP/IBAN pe domeniu neoficial si exista confirmare reputationala/sandbox sau semnal tehnic puternic.

### Structural Evidence

Poate da `NO_ENTER_DATA`:

- formular de card/CVV/OTP/parola/login pe domeniu neoficial;
- form action catre domeniu diferit de brandul pretins;
- link vizibil oficial, dar href/final URL neoficial si pagina cere date;
- redirect chain dubios + destinatie necunoscuta + intent sensibil.

Poate urca la `DANGEROUS` doar cand este combinat cu reputatie/sandbox/blacklist sau intent malware foarte clar.

### Soft Evidence

Maxim `VERIFY_OFFICIAL`:

- cuvinte comerciale: voucher, reducere, promotie, nu rata, ultima sansa;
- limbaj de urgenta fara dovada tehnica;
- RAG/corpus similarity;
- hidden link sub buton fara analiza destinatiei;
- tracking link normal;
- user feedback neconfirmat.

### Official Domain

`OFFICIAL_DOMAIN` este semnal de coerenta, nu garantie absoluta.

Poate cobori semnale slabe la `SAFE` sau `VERIFY_OFFICIAL` daca:

- final URL este cunoscut;
- domeniul si brandul sunt coerente;
- Web Risk/urlscan/cache nu contrazic;
- nu exista formular sensibil pe domeniu neoficial;
- redirecturile sunt explicabile.

Nu poate anula:

- Web Risk malicious;
- urlscan malicious;
- blacklist validata;
- final URL neoficial cu cerere de date sensibile.

## UNKNOWN / Insufficient Evidence

Pastra ideea de `UNKNOWN`, dar in UI o formulam ca `Nu pot verifica suficient`.

`UNKNOWN` cand:

- nu avem URL/final URL;
- share-ul a adus doar shell de webmail, nu corpul emailului;
- Web Risk/urlscan/VT sunt timeout/rate limited si nu avem dovezi structurale suficiente;
- exista doar text promotional;
- exista conflict intre surse fara hard signal;
- inputul este prea vag.

Recomandare UI:

- headline: `Nu pot verifica suficient`;
- actiune: `Verifica direct in aplicatia/site-ul oficial`;
- nu spunem `safe`;
- nu spunem `scam` fara dovezi.

## Timeout/Fallback - Corectat

Pastram flow-ul pe timp, dar corectam mesajele:

| Timp | UI corect | Background |
| --- | --- | --- |
| `0-3s` | `Analizam linkul...` | extractie, primary URL, cache, Web Risk |
| `3-8s` | `Inca verificam destinatia reala...` | urlscan submit/poll, redirect/final URL |
| `8-30s` | verdict preliminar doar daca Gate are dovezi reale; altfel `Nu pot verifica suficient inca` | urlscan poll, VT fallback daca policy cere |
| `>30s` | `Nu pot verifica suficient` sau verdict pe dovezi disponibile | actualizare in-app/history cand apar rezultate |

Nu folosim:

- `Poti continua cu prudenta` inainte sa avem final URL/reputatie suficiente;
- notificare automata dupa scanare, pentru ca produsul este user-initiated si fara notification permission;
- interpretarea `urlscan timeout` ca safe.

VT fallback ruleaza doar cand:

- Web Risk nu da verdict;
- urlscan este neclar, timeout sau rate-limited;
- exista structural evidence mediu/puternic;
- domeniul este necunoscut sau conflictual;
- userul cere scanare extinsa.

## Cache/TTL De Pastrat Ca Directie

Candidate TTLs pentru spec final:

| Sursa | Positive / malicious | Negative / clean | Observatie |
| --- | --- | --- | --- |
| Web Risk | `expireTime` din API | TTL scurt conform policy | no-match nu este garantie de safe |
| urlscan | 12h pentru malicious | 1-6h pentru clean | paginile de phishing se schimba rapid |
| VirusTotal | 24h positive | 6-12h negative | fallback, nu sursa primara |
| Official domains registry | update saptamanal/versionat | N/A | lista versionata, review manual |
| User feedback | 90 zile brut, apoi agregat/anonimizat | N/A | fara PII in analytics |

Adaugare necesara:

- cache key trebuie sa foloseasca URL sanitizat/hash, nu URL cu token/email;
- cache-ul trebuie sa stocheze si `finalUrl`, `provider`, `observedAt`, `expiresAt`, `verdict`, `sourceRawStatus`;
- un `clean` vechi nu trebuie sa blocheze o rescanare cand semnalele locale sunt puternice.

## Google Play - Ce Pastram

Pastra:

- scanare doar la actiunea explicita a userului: share/import/paste/QR/OCR;
- declaratie clara ca app-ul nu monitorizeaza notificari, SMS-uri sau conversatii;
- Privacy Policy cu third parties: backend intern, urlscan, Google Web Risk, VirusTotal, provider AI/RAG daca exista;
- Data Safety: App Activity, Diagnostics, URL-uri/redirecturi/pseudonimizate, scop securitate/fraud prevention;
- HTTPS si PII redaction inainte de urlscan unde se poate;
- Store listing ca instrument anti-scam/educational, nu serviciu financiar.

Corectii:

- nu cerem `READ_SMS`, `RECEIVE_SMS`, notification listener, accessibility service;
- nu cerem storage larg daca share intents / Android picker rezolva importul;
- nu cerem `POST_NOTIFICATIONS` pentru update async in prima versiune;
- `CAMERA` e ok pentru QR/OCR doar cu explicatie si runtime permission.

## Acceptance Tests De Pastrat, Dar Corectate

Testele valoroase de pastrat in corpus:

- ANAF fake cu formular card si reputatie/sandbox malicious -> `DANGEROUS`;
- FAN fake taxa + OTP pe domeniu neoficial -> `NO_ENTER_DATA` sau `DANGEROUS` daca reputatia confirma;
- Revolut OTP phishing cu final URL neoficial -> `NO_ENTER_DATA` / `DANGEROUS` dupa provider;
- APK remote access / malware link -> `DANGEROUS` daca reputatie/sandbox confirma;
- urlscan down + Web Risk unavailable + fara structural strong -> `UNKNOWN`;
- webmail shell fara corp de mail -> `UNKNOWN`;
- Web Risk clean + urlscan phishing -> `DANGEROUS`;
- Web Risk phishing + urlscan clean -> `DANGEROUS`;
- Uber promo real cu domeniu/tracking coerent -> `SAFE` sau `VERIFY_OFFICIAL`, nu scam;
- eMAG newsletter real -> `SAFE` sau `VERIFY_OFFICIAL`, nu scam;
- FAN tracking real -> `SAFE` sau `VERIFY_OFFICIAL`, nu scam;
- link sub buton + reputatie clean + fara intent sensibil -> maxim `VERIFY_OFFICIAL`;
- formular login pe domeniu necunoscut -> `NO_ENTER_DATA`;
- text generic promo fara URL -> `VERIFY_OFFICIAL` sau `UNKNOWN`, nu `DANGEROUS`;
- user feedback neconfirmat + reputatie clean -> `VERIFY_OFFICIAL`;
- urlscan intarziat -> stage `IN_PROGRESS` / `PRELIMINARY`, apoi update in-app;
- newsletter cu buton `profita acum` pe domeniu oficial -> `SAFE` sau `VERIFY_OFFICIAL`.

Corectii la tabelul original:

- `TEXT_KEYWORD -> DANGER` nu se foloseste;
- `HIDDEN_LINK -> DANGEROUS` nu se foloseste singur;
- `OFFICIAL_DOMAIN + STRUCTURAL` nu devine automat safe; depinde daca domeniul final este oficial si daca cererea de date este legitima/contextuala;
- `CORPUS` nu poate decide verdictul.

## False Positives / False Negatives - Luam Pentru Final

False positives prioritare:

- marketing legitim care suna agresiv;
- butoane cu link in emailuri reale;
- tracking links si redirectori legitimi;
- subdomenii reale de campanie;
- newslettere reale Uber/eMAG/FAN/Glovo/Bolt/booking/airlines.

False negatives prioritare:

- domenii noi, inca necunoscute de Web Risk/VT;
- phishing cu pagina dinamica sau cloaking;
- redirect chain care ascunde final URL;
- formular sensibil generat dupa delay;
- APK/remote-access download mascat ca factura/curier.

Imbunatatiri utile:

- brand/domain mismatch engine;
- WHOIS/domain age ca semnal structural, dar nu verdict singur;
- health monitoring pentru providerii externi;
- corpus romanesc cu expected verdict;
- template/visual brand check pe termen lung, dupa ce avem preview/sandbox stabil.

## Elemente Din Raspunsul 2 Pe Care Nu Le Folosim Direct

Nu folosim direct:

- pseudocodul cu scoruri agregate ca judecator final;
- `scores[DANGEROUS] > 0 -> DANGEROUS` fara cap pe provenance;
- `TEXT_KEYWORD` cu severitate mare care poate ajunge la `DANGEROUS`;
- `Hidden link pe domeniu suspect -> NO_ENTER_DATA` fara analiza final URL/pagina;
- `3-8s -> Poti continua cu prudenta`;
- notificari automate pentru verdicturi intarziate;
- user feedback `>=3 raportari -> DANGEROUS` fara validare anti-abuz;
- `FOREGROUND_SERVICE`/storage larg ca permisiuni implicite.

## Concluzie Pentru Sinteza Finala

Raspunsul 2 este bun pentru structura operationala si compliance, dar EvidenceGate final trebuie sa fie precedence/cap-based, nu score-based.

Formula care ramane:

`Extractor -> Evidence Snapshot cu provider status -> Evidence Gate cu provenance caps -> Decision Engine determinist -> RAG Explainer read-only -> UI simplu`

Principiul central:

`DANGEROUS` are nevoie de dovezi tehnice/reputationale/sandbox clare. Textul comercial, RAG-ul, corpusul si linkurile ascunse sunt context, nu verdict.
