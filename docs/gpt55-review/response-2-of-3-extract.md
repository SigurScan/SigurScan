# GPT 5.5 Pro Response 2 Of 3 - Extract Pentru Spec Final

Data: 2026-06-02

Sursa: `/Users/vaduvageorge/.codex/attachments/1c0920cd-cf80-4447-b4a4-5d5a3ddf7ae6/pasted-text.txt`

Scop: extragere filtrata din raspunsul marcat `2/3`. Acesta NU este spec final si NU se implementeaza copy-paste. Este cel mai valoros material de pana acum pentru EvidenceGate, dar trebuie redus la MVP si verificat contra codului existent.

## Verdict Pe Raspunsul 2/3

Foarte bun ca arhitectura de Gate.

Ce merita pastrat aproape integral:

- invariantul central: toate sursele produc `EvidenceSignal`; numai `EvidenceGate` produce verdict;
- RAG/AI este explainer read-only si primeste deja `GateResult`;
- negative evidence nu anuleaza automat positive evidence;
- `Web Risk NO_MATCH`, `urlscan clean`, `VT no detection` nu inseamna safe absolut;
- text keywords singure nu pot da `DO_NOT_CONTINUE`;
- marketing real nu devine scam doar pentru ca are tracking, buton HTML sau limbaj comercial;
- decizia trebuie sa fie determinista pe aceleasi semnale + aceeasi versiune de policy + aceeasi versiune registry;
- introducerea lui `NO_REPLY`, foarte util pentru mesaje fara URL care cer coduri/parole/bani;
- `SourceState`, `RedactionReport`, `AsyncCompleteness`, `EvidenceConflict`;
- ordinea de forta intre surse;
- tabelul de decizie pe provenienta;
- timeout/fallback pe 3s / 8s / 30s;
- registry de brand cu domenii oficiale, parteneri si tracking domains;
- cache/TTL si lista de ce nu se cache-uieste niciodata;
- Google Play compliance foarte bun;
- test matrix cu 30 de cazuri.

Ce trebuie taiat sau amanat:

- modelele sunt prea mari pentru implementare rapida in Android v1;
- community feedback ca sursa de `DO_NOT_CONTINUE` trebuie amanat pana avem anti-abuz si volum;
- corpus exact bad URL poate da `DO_NOT_CONTINUE` doar daca este curatat/validat si are TTL;
- notificari async raman optional si nu intra in prima versiune, pentru ca am eliminat `POST_NOTIFICATIONS`;
- `rawInputStored` trebuie default false si probabil scos din MVP server-side;
- policy comun Kotlin Multiplatform este ideal, dar MVP poate fi Kotlin Android + backend policy versioned JSON/spec.

## Invariante De Pastrat In Spec Final

Acestea sunt reguli de produs, nu sugestii:

- `EvidenceGate` este singurul judecator.
- RAG nu decide, nu modifica verdictul si nu poate schimba actiunea recomandata.
- RAG poate explica doar semnalele si decizia deja luata.
- Web Risk no-match nu inseamna sigur.
- urlscan clean nu inseamna sigur daca exista formular de card/login/OTP pe domeniu neoficial.
- VirusTotal no detection nu inseamna sigur.
- Domeniul oficial reduce false positives, dar nu este whitelist absolut.
- Textul comercial sau urgent nu poate produce `DO_NOT_CONTINUE` singur.
- Linkul sub buton nu este risc in sine.
- Tracking linkul nu este risc in sine.
- Pericolul real apare din combinatie: brand pretins + domeniu neoficial + cerere de date/card/parola/OTP/plata/install APK/remote access.
- Decizia trebuie sa fie determinista si reproductibila.

## Verdicturi User-Facing De Pastrat

Raspunsul introduce `GateDecision` mai bun decat statusurile simple:

```kotlin
enum class GateDecision {
    CONTINUE_WITH_CAUTION,   // Poti continua cu prudenta
    VERIFY_OFFICIAL,         // Verifica pe canalul oficial
    NO_ENTER_DATA,           // Nu introduce date
    NO_REPLY,                // Nu raspunde
    DO_NOT_CONTINUE,         // Nu continua
    INSUFFICIENT_EVIDENCE    // Nu pot verifica suficient
}
```

De pastrat in UI:

| GateDecision | User label | Cand apare |
| --- | --- | --- |
| `DO_NOT_CONTINUE` | `Nu continua` | reputatie/sandbox/corpus exact confirmat, malware, phishing clar |
| `NO_ENTER_DATA` | `Nu introduce date` | formular card/login/OTP/date personale pe domeniu neoficial |
| `NO_REPLY` | `Nu raspunde` | mesaj fara URL care cere cod SMS, parola, bani, CNP, card |
| `VERIFY_OFFICIAL` | `Verifica pe canalul oficial` | brand mentionat, domeniu necunoscut, shortener, semnale slabe |
| `CONTINUE_WITH_CAUTION` | `Poti continua cu prudenta` | domeniu oficial/partener + fara semnale riscante |
| `INSUFFICIENT_EVIDENCE` | `Nu pot verifica suficient` | input incomplet, remote down, OCR slab, webmail shell |

Important pentru final:

- `CONTINUE_WITH_CAUTION` nu inseamna garantie.
- `INSUFFICIENT_EVIDENCE` nu inseamna safe si nu inseamna scam.
- `NO_REPLY` trebuie tratat ca first-class verdict, pentru ca multe scamuri pe SMS/WhatsApp nu au link, ci cer cod/bani.

## Modele De Date De Pastrat Ca Directie

### InputType

```kotlin
enum class InputType {
    PASTE_TEXT,
    SHARE_TEXT,
    SHARE_HTML_EMAIL,
    IMPORT_FILE,
    UPLOAD_IMAGE,
    QR_SCAN,
    OCR_IMAGE
}
```

### EvidenceProvenance

```kotlin
enum class EvidenceProvenance {
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

### EvidenceSource

```kotlin
enum class EvidenceSource {
    LOCAL_EXTRACTOR,
    PRIMARY_URL_PICKER,
    PII_REDACTOR,
    OFFLINE_POLICY,
    OFFICIAL_DOMAINS_REGISTRY,
    GOOGLE_WEB_RISK,
    URLSCAN,
    VIRUSTOTAL,
    USER_REPORTS,
    SCAM_CORPUS,
    RAG_EXPLANATION
}
```

Nota pentru spec final:

- `RAG_EXPLANATION` poate exista doar pentru audit/UI, dar `isDecisionEligible` trebuie sa intoarca false.
- `USER_REPORTS` si `SCAM_CORPUS` trebuie tinute sub control strict ca sa nu devina surse de false positives.

### SourceRunStatus

Foarte util pentru `UNKNOWN` si timeout:

```kotlin
enum class SourceRunStatus {
    NOT_RUN,
    SKIPPED_LOW_RISK,
    SKIPPED_PRIVACY,
    SKIPPED_USER_DISABLED_CLOUD,
    PENDING,
    SUCCESS,
    PARTIAL,
    TIMEOUT,
    RATE_LIMITED,
    UNAVAILABLE,
    ERROR
}
```

### SignalStrength

```kotlin
enum class SignalStrength {
    INFO,
    LOW,
    MEDIUM,
    HIGH,
    CRITICAL
}
```

### EvidenceSignal

Campurile cele mai importante:

```kotlin
data class EvidenceSignal(
    val id: String,
    val provenance: EvidenceProvenance,
    val source: EvidenceSource,
    val kind: SignalKind,
    val targetType: EvidenceTargetType,
    val targetHash: String?,
    val normalizedHost: String? = null,
    val registeredDomain: String? = null,
    val claimedBrand: String? = null,
    val strength: SignalStrength,
    val confidence: Int,
    val observedAt: Instant,
    val expiresAt: Instant? = null,
    val canEscalateToDangerous: Boolean,
    val maxDecisionIfAlone: GateDecision,
    val userSafeSummary: String,
    val technicalSummary: String,
    val policyVersion: String
)
```

Campurile de pastrat obligatoriu in spirit:

- `provenance`;
- `source`;
- `kind`;
- `strength`;
- `confidence`;
- `expiresAt`;
- `canEscalateToDangerous`;
- `maxDecisionIfAlone`;
- `policyVersion`;
- `targetHash`, nu raw PII.

### EvidenceSnapshot

Versiune recomandata pentru spec final:

```kotlin
data class EvidenceSnapshot(
    val scanId: String,
    val inputType: InputType,
    val createdAt: Instant,
    val updatedAt: Instant,
    val rawInputStored: Boolean = false,
    val rawInputHash: String? = null,
    val primaryUrl: UrlCandidate?,
    val allUrls: List<UrlCandidate>,
    val finalUrl: UrlCandidate? = null,
    val redirectChain: List<RedirectHop> = emptyList(),
    val claimedBrands: List<String> = emptyList(),
    val sourceStates: Map<EvidenceSource, SourceState>,
    val signals: List<EvidenceSignal>,
    val conflicts: List<EvidenceConflict> = emptyList(),
    val redactionReport: RedactionReport,
    val officialRegistryRef: RegistryRef,
    val asyncCompleteness: AsyncCompleteness,
    val policyVersion: String
)
```

MVP simplificat poate scoate temporar:

- `rawInputStored`;
- `technicalDecisionPath`;
- `RegistryRef.signatureValid`;
- `EvidenceCard.technicalDetails`;
- comunitate/user reports.

## SignalKind - Ce Merita Pastrat In MVP

Nu trebuie toate din prima. Pentru MVP de parser/email/share + Gate:

### Text

- `URGENCY_LANGUAGE`;
- `FEAR_OR_PRESSURE`;
- `MONEY_REQUEST`;
- `OTP_REQUEST`;
- `PASSWORD_REQUEST`;
- `CARD_DATA_REQUEST`;
- `CNP_OR_ID_REQUEST`;
- `REPLY_REQUEST`;
- `INSTALL_APP_REQUEST`;
- `REMOTE_ACCESS_APP_REFERENCE`;
- `FAMILY_OR_AUTHORITY_IMPERSONATION`.

### Hidden Link

- `DISPLAY_TEXT_HIDES_DIFFERENT_HREF`;
- `BUTTON_LINK_DOMAIN_MISMATCH`;
- `DISPLAYED_DOMAIN_DIFFERS_FROM_HREF_DOMAIN`;
- `HIDDEN_LINK_TO_SHORTENER`;
- `HIDDEN_LINK_TO_UNOFFICIAL_BRAND_DOMAIN`.

### Structural

- `LOOKALIKE_DOMAIN`;
- `PUNYCODE_OR_HOMOGLYPH`;
- `NEW_OR_UNKNOWN_DOMAIN`;
- `URL_SHORTENER`;
- `IP_LITERAL_URL`;
- `SUSPICIOUS_TLD`;
- `HTTP_NOT_HTTPS`;
- `QUERY_CONTAINS_TOKEN_OR_EMAIL`;
- `REDIRECT_CHAIN_SUSPICIOUS`;
- `APK_DOWNLOAD`;
- `FORM_LOGIN_DETECTED`;
- `FORM_CARD_DETECTED`;
- `FORM_OTP_DETECTED`;
- `FORM_PERSONAL_DATA_DETECTED`.

### Reputation

- `WEB_RISK_SOCIAL_ENGINEERING`;
- `WEB_RISK_MALWARE`;
- `WEB_RISK_UNWANTED_SOFTWARE`;
- `WEB_RISK_NO_MATCH`;
- `VT_MULTI_ENGINE_MALICIOUS`;
- `VT_SINGLE_OR_LOW_ENGINE_HIT`;
- `VT_NO_DETECTION`;
- `VT_STALE_REPORT`.

### Sandbox

- `SANDBOX_FINAL_URL_OBSERVED`;
- `SANDBOX_SCREENSHOT_AVAILABLE`;
- `SANDBOX_BRAND_IMPERSONATION`;
- `SANDBOX_CREDENTIAL_FORM_ON_UNOFFICIAL_DOMAIN`;
- `SANDBOX_CARD_FORM_ON_UNOFFICIAL_DOMAIN`;
- `SANDBOX_OTP_FORM_ON_UNOFFICIAL_DOMAIN`;
- `SANDBOX_APK_DOWNLOAD_OBSERVED`;
- `SANDBOX_REMOTE_ACCESS_FLOW`;
- `SANDBOX_REDIRECT_TO_DANGEROUS`;
- `SANDBOX_NO_VISIBLE_RISK`;
- `SANDBOX_SCAN_REJECTED`.

## Decision Table - Pastram Pentru EvidenceGate

### Poate Da `DO_NOT_CONTINUE` Singur

- Web Risk social engineering/malware/unwanted software valid si neexpirat;
- VT high-confidence: malicious >= 5 sau malicious >= 3 + phishing/malware category;
- urlscan/sandbox observa credential/card/OTP form pe domeniu neoficial;
- sandbox observa APK sau remote access flow;
- corpus exact bad URL/domain activ si validat;
- confirmed active community campaign, dar doar dupa anti-abuz/manual/tehnic validation.

### Nu Poate Da `DO_NOT_CONTINUE` Singur

- orice `TEXT_KEYWORD`;
- hidden link fara cerere de date sau reputatie/sandbox;
- URL shortener;
- domeniu nou/necunoscut;
- HTTP not HTTPS;
- suspicious TLD;
- VT 1-2 engines;
- user single report;
- corpus similar template;
- urlscan no visible risk;
- Web Risk no-match.

### Poate Da `NO_ENTER_DATA`

- form/card/login/OTP detectat pe domeniu neoficial;
- hidden link mismatch + sensitive data request;
- Web Risk clean + structural high risk;
- remote sources unavailable + local high structural risk;
- brand claim + official domain mismatch + cerere de date.

### Poate Da `NO_REPLY`

- fara primary URL;
- mesajul cere OTP/parola/card/CNP/bani;
- mesajul cere raspuns direct sau mimeaza familie/autoritate/institutie;
- exemplu: "Sunt de la Revolut, spune codul primit".

### Poate Da `VERIFY_OFFICIAL`

- brand claimed + domain unknown/not official + fara sensitive ask;
- urgency/fear only;
- shortener unresolved;
- single user report only;
- similar corpus template;
- hidden link only fara cerere de date;
- non-resolvable host + text de plata, fara provider confirmation.

### Poate Da `CONTINUE_WITH_CAUTION`

- official exact sau official partner;
- no sensitive data request;
- no dangerous reputation;
- no dangerous sandbox behavior;
- tracking domain allowed + final URL official;
- marketing language + official domain + fara card/parola/OTP/install.

### `INSUFFICIENT_EVIDENCE`

- no primary URL + no risky text request;
- redaction unsafe + local evidence weak;
- all remote sources failed + local evidence weak;
- OCR confidence too low;
- doar webmail shell links;
- input vag.

## Source Precedence

Ordinea de forta recomandata:

1. Web Risk / VT high-confidence positive / confirmed blocklist.
2. Sandbox observed behavior.
3. Confirmed corpus exact match.
4. Confirmed active community campaign.
5. Official domain exact / partner registry.
6. Structural signals.
7. Hidden link signals.
8. Text keywords.
9. Single user feedback.
10. Negative/no-match reputation evidence.

Regula centrala:

`Positive high-confidence evidence wins over negative evidence. Negative evidence only lowers/caps weak signals.`

## Conflict Resolution

Pastram explicit:

- Web Risk clean + urlscan malicious -> `DO_NOT_CONTINUE`;
- Web Risk clean + sandbox card form unofficial -> `NO_ENTER_DATA` sau `DO_NOT_CONTINUE` daca brand impersonation e clar;
- urlscan clean + structural dangerous -> `NO_ENTER_DATA`;
- official exact + VT 1 engine stale -> `CONTINUE_WITH_CAUTION` + conflict log;
- official exact + Web Risk malware -> `DO_NOT_CONTINUE`;
- old cache clean + fresh sandbox malicious -> fresh sandbox castiga.

## False Positive Policy Pentru Marketing Real

Reguli bune:

- newsletter real cu tracking nu este scam doar pentru redirect;
- Uber promo real nu e scam doar pentru "promo", "reducere", "cod";
- FAN tracking real nu e suspicious doar pentru "colet";
- email HTML cu buton nu e dangerous doar pentru hidden link;
- domeniu nou nu e dangerous singur;
- single user report nu e dangerous;
- VT 1 engine hit vechi nu e dangerous.

Conditia pentru `CONTINUE_WITH_CAUTION` in marketing:

- final domain oficial/partener/tracking permis;
- fara cerere de card/parola/OTP/CNP/install;
- fara Web Risk/urlscan/VT malicious;
- brand/context coerent.

## Official Domains Registry - De Pastrat

Modelul este foarte bun pentru anti-false-positive:

```kotlin
data class BrandRegistryEntry(
    val brandId: String,
    val displayName: String,
    val officialDomains: Set<String>,
    val officialSubdomains: Set<String>,
    val allowedTrackingDomains: Set<PartnerDomain>,
    val allowedPartnerDomains: Set<PartnerDomain>,
    val neverAskFor: Set<NeverAskFor>,
    val riskyActions: Set<RiskyAction>,
    val verifiedChannels: List<VerifiedChannel>,
    val updatedAt: Instant,
    val sourceRefs: List<String>
)
```

Reguli:

- official exact + no sensitive form + no dangerous reputation -> `CONTINUE_WITH_CAUTION`;
- official tracking domain + final URL official + no sensitive form -> `CONTINUE_WITH_CAUTION`;
- official tracking domain + final URL unknown + asks login/card -> `NO_ENTER_DATA`;
- claimed brand + domain not official/partner + asks data/card/OTP -> `DO_NOT_CONTINUE` daca avem sandbox/reputatie sau combo foarte clar, altfel `NO_ENTER_DATA`;
- claimed brand + domain not official/partner + no ask -> `VERIFY_OFFICIAL`.

MVP registry trebuie sa contina macar:

- eMAG;
- Uber;
- FAN Courier;
- Posta Romana;
- ANAF;
- Revolut;
- BT;
- BCR;
- ING;
- OLX;
- Bolt/Glovo/Tazz, daca apar in corpus.

## Timeout Si Fallback

### 0-3 secunde

Ruleaza:

- local extraction;
- primary URL picker;
- PII redaction;
- official registry;
- offline policy;
- cache lookup;
- fast Web Risk daca disponibil.

UI posibil:

- Web Risk/cache/corpus exact dangerous -> `Nu continua`;
- local high risk hidden link + brand mismatch + cere card/OTP -> `Nu introduce date` sau `Nu continua`, dupa combo;
- official exact + fara risc -> `Poti continua cu prudenta`;
- semnale slabe + remote pending -> `Nu pot verifica suficient inca`;
- brand mentionat + domeniu necunoscut -> `Verifica pe canalul oficial`.

### 8 secunde

Ar trebui sa avem:

- Web Risk;
- urlscan submit status;
- eventual urlscan result rapid;
- VT cached report daca policy cere.

UI:

- urlscan form/card/final malicious -> upgrade;
- urlscan pending + Web Risk clean + structural suspect -> ramane `Nu introduce date`;
- urlscan 429 + Web Risk unavailable + local weak -> `Nu pot verifica suficient`;
- VT puternic -> `Nu continua`;
- tot clean + official/partner -> `Poti continua cu prudenta`.

### 30 secunde

Inchidem experienta activa:

- verdict final clar -> final;
- sandbox pending -> verdict provizoriu + "sandbox indisponibil/intarziat";
- toate remote au picat -> `Nu pot verifica suficient` sau `Verifica oficial`;
- local high-risk remote down -> `Nu introduce date`;
- local low-risk remote down -> `Nu pot verifica suficient`.

### Async updates

Pentru v1:

- daca app-ul e deschis, actualizam cardurile inline/history;
- daca app-ul e inchis, nu trimitem notificare in MVP;
- daca vom adauga notificari mai tarziu, mesajul trebuie sa fie neutru si fara URL/text sensibil.

## VT Fallback Policy

Ruleaza VT cand:

- Web Risk unavailable/timeout;
- urlscan unavailable/timeout/429;
- structural risk >= MEDIUM;
- hidden link detected;
- brand claimed + official domain mismatch;
- APK / remote access / install flow;
- sandbox conflict;
- user apasa explicit "Analiza avansata";
- cached VT report exista in TTL.

Sari peste VT cand:

- Web Risk deja dangerous;
- urlscan deja dangerous;
- URL official exact + fara sensitive ask + local low risk;
- input fara URL;
- `redactionReport.safeForExternalSubmission == false`;
- userul a dezactivat cloud checks;
- URL are magic/reset/auth token care nu poate fi redacted sigur.

Thresholds:

- malicious >= 5 -> `DO_NOT_CONTINUE`;
- malicious >= 3 + phishing/malware category -> `DO_NOT_CONTINUE`;
- malicious 1-2 + official exact -> `CONTINUE_WITH_CAUTION` + conflict;
- malicious 1-2 + structural suspicious -> `NO_ENTER_DATA`;
- 0 malicious + structural high -> nu scade sub `NO_ENTER_DATA`;
- stale report -> weak evidence, nu final.

## Cache / TTL

### Web Risk

- match -> `expireTime` din response;
- no-match exact URL -> 15 min;
- no-match domeniu oficial exact -> 60 min;
- no-match shortener/unknown domain -> 5 min.

Nota: no-match cache este optimizare de trafic, nu dovada de siguranta.

### urlscan

- malicious/phishing observed -> 24h exact URL, 7 zile domain indicator;
- card/login/OTP form unofficial -> 24h exact URL, 48h domain;
- APK/remote access -> 24h exact URL, 7 zile domain;
- clean/no visible risk -> 4h exact URL, nu domain-wide safe;
- DNS rejected -> 1h, nu dangerous singur;
- 429/timeout -> nu cache-ui ca verdict.

### VirusTotal

- high-confidence malicious -> 24h exact URL, 7 zile domain weak indicator;
- low engine hit -> 6h;
- no detection -> 6h exact URL;
- stale report > 7 zile -> weak only;
- no report -> 1h;
- timeout/rate limited -> nu cache-ui ca verdict.

### Official Registry

- signed JSON;
- app cache 7 zile;
- backend update zilnic;
- stale dupa 14 zile;
- signature invalid -> registry ignorat pentru reducerea riscului;
- daca registry stale, nu mai poate produce `CONTINUE_WITH_CAUTION` singur.

### Nu Se Cache-uieste Niciodata

- raw SMS/email/text user-provided pe server;
- imagini OCR brute pe server, daca nu e absolut necesar;
- tokeni reset/magic links;
- OTP;
- CNP;
- IBAN;
- card/CVV/CVC;
- auth/session tokens;
- query params sensibili;
- mapping original inainte/dupa redaction;
- RAG explanation ca evidence;
- notificari sau conversatii.

Local history:

- verdict + hash URL + timestamp + evidence summary;
- raw input local off by default;
- daca raw local on: criptat + stergere manuala.

## Google Play Compliance - Pastram Aproape Integral

Permisiuni OK pentru v1:

- `INTERNET`;
- `ACCESS_NETWORK_STATE`;
- `CAMERA` runtime pentru QR/OCR;
- Android Photo Picker pentru imagini;
- Share Intent / Android Sharesheet.

Nu cerem in v1:

- `READ_SMS`;
- `RECEIVE_SMS`;
- `SEND_SMS`;
- `READ_CALL_LOG`;
- `WRITE_CALL_LOG`;
- `READ_PHONE_STATE`;
- `READ_PHONE_NUMBERS`;
- `BIND_NOTIFICATION_LISTENER_SERVICE`;
- `BIND_ACCESSIBILITY_SERVICE`;
- `SYSTEM_ALERT_WINDOW`;
- `QUERY_ALL_PACKAGES`;
- `MANAGE_EXTERNAL_STORAGE`;
- `READ_MEDIA_IMAGES` / `READ_MEDIA_VIDEO` daca Photo Picker e suficient;
- `READ_CONTACTS`;
- `RECORD_AUDIO`;
- `POST_NOTIFICATIONS` in MVP.

Privacy Policy trebuie sa spuna:

- app-ul verifica doar continut trimis explicit de user: share, paste, import, upload, QR, OCR;
- nu citeste automat SMS-uri;
- nu monitorizeaza WhatsApp;
- nu citeste notificari;
- nu asculta apeluri;
- nu ruleaza in fundal pentru colectare conversatii;
- nu vinde date personale;
- trimite URL-uri/text redacted catre backend/provideri doar pentru analiza;
- PII redaction pentru email, telefon, CNP, IBAN, card, OTP, auth/reset tokens;
- third parties: backend SigurScan, Google Web Risk, urlscan, VirusTotal, AI/RAG provider daca exista;
- retention clara si delete request.

Store listing:

- nu promitem protectie 100%;
- nu spunem ca blocam toate scamurile;
- nu pretindem afiliere cu ANAF/FAN/eMAG/banci;
- nu spunem antivirus complet;
- nu spunem monitorizare automata.

## Backend Flow De Pastrat

Endpoint recomandat:

- `POST /v1/scan`;
- `GET /v1/scan/{scanId}`.

Flow:

1. persist minimal scan record;
2. ruleaza Web Risk;
3. check corpus/cache;
4. submit urlscan doar daca `safeForExternalSubmission`;
5. ruleaza VT selectiv;
6. normalizeaza toate outputurile in `EvidenceSignal`;
7. reconstruieste `EvidenceSnapshot`;
8. ruleaza `EvidenceGate`;
9. stocheaza `GateResult`.

Important:

- providerii nu intorc verdict user-facing;
- providerii intorc doar semnale;
- nu stocam output brut provider fara filtrare;
- extragem doar threat type, final URL, redirect domains, screenshot ref, certificate summary, DOM form indicators, ASN/country summary, source status/error.

## Acceptance Tests De Pastrat

Aceste 30 de cazuri trebuie sa devina corpus/test matrix:

1. Uber promo real -> `CONTINUE_WITH_CAUTION`.
2. eMAG newsletter real -> `CONTINUE_WITH_CAUTION`.
3. FAN tracking real -> `CONTINUE_WITH_CAUTION`.
4. Marketing cu shortener dar final official -> `CONTINUE_WITH_CAUTION`.
5. Promo real cu `premiu` pe domeniu oficial -> `CONTINUE_WITH_CAUTION`.
6. ANAF fake refund + card form -> `DO_NOT_CONTINUE`.
7. FAN fake taxa/card -> `DO_NOT_CONTINUE`.
8. Revolut OTP fara URL, cere cod -> `NO_REPLY`.
9. APK remote access -> `DO_NOT_CONTINUE`.
10. AnyDesk/TeamViewer flow pentru banca -> `DO_NOT_CONTINUE`.
11. BCR lookalike + login form -> `DO_NOT_CONTINUE`.
12. Punycode/homoglyph bank + password form -> `DO_NOT_CONTINUE`.
13. Web Risk positive -> `DO_NOT_CONTINUE`.
14. VT high malicious -> `DO_NOT_CONTINUE`.
15. urlscan down + brand unknown/no form -> `VERIFY_OFFICIAL`.
16. All remote down weak marketing -> `INSUFFICIENT_EVIDENCE`.
17. Webmail shell only -> `INSUFFICIENT_EVIDENCE`.
18. OCR slab, URL incomplet -> `INSUFFICIENT_EVIDENCE`.
19. WebRisk clean + urlscan malicious -> `DO_NOT_CONTINUE`.
20. urlscan clean + structural card form unofficial -> `NO_ENTER_DATA`.
21. Official exact + VT 1 engine old -> `CONTINUE_WITH_CAUTION`.
22. Hidden link only -> `VERIFY_OFFICIAL`.
23. Single user report -> `VERIFY_OFFICIAL`.
24. Confirmed active campaign -> `DO_NOT_CONTINUE`.
25. Unofficial domain asks CNP -> `NO_ENTER_DATA`.
26. Query token sensitive / unsafe redaction -> `INSUFFICIENT_EVIDENCE` sau local-only verdict.
27. Non-resolvable host + payment text -> `VERIFY_OFFICIAL`.
28. Shortener unresolved -> `VERIFY_OFFICIAL`.
29. Official partner payment -> `CONTINUE_WITH_CAUTION`.
30. Official mismatch + no sensitive ask -> `VERIFY_OFFICIAL`.

## Implementare - Ordinea Corecta

### Android

1. Definim modelele comune minimale.
2. Generam local signals din text/html/share intent.
3. PrimaryUrlPicker returneaza `UrlCandidate` cu motive.
4. PII Redaction devine hard gate pentru cloud submission.
5. EvidenceGate local ruleaza imediat cu semnale locale/cache.
6. UI suporta provisional/final/advanced pending/privacy skipped.
7. Fara background monitoring.

### Backend

1. Scan orchestrator.
2. Adapters: Web Risk, urlscan, VT, corpus.
3. Provider output normalizer -> `EvidenceSignal`.
4. EvidenceGate backend cu aceeasi policy version.
5. Cache service.
6. Async scan updates in history.
7. Audit fara raw input.

## Ce Nu Folosim Direct Din Raspunsul 2/3

Nu folosim direct:

- implementarea completa cu toate enum-urile din prima iteratie, pentru ca e prea mare pentru MVP;
- notificari async in v1;
- community feedback ca hard evidence fara validare serioasa;
- corpus confirmed bad domain ca dangerous fara TTL/provenance/manual hygiene;
- `rawInputStored` server-side;
- `CONTINUE_WITH_CAUTION` bazat doar pe Web Risk no-match;
- KMP policy ca blocant pentru prima implementare;
- orice stocare de raw email/SMS/text in backend.

## Gaps De Completat In Spec Final

Acestea sunt observatii critice si trebuie rezolvate inainte de implementarea finala a Gate-ului.

### Contracte Lipsa Pentru Functiile Din Pseudocod

Spec-ul mentioneaza functii care trebuie definite explicit:

- `detectConflicts()`;
- `OfficialContext.from()`;
- `isContinueWithCaution()`;
- `suppressedByDanger()`;
- `buildPath()`;
- `recommendedActions()`;
- `defaultReason()`.

Nu le lasam ca detaliu de implementare. In spec final, fiecare functie trebuie sa aiba:

- input exact;
- output exact;
- reguli de precedenta;
- ce logheaza;
- ce nu are voie sa faca;
- teste minimale.

### OfficialContext Este Gap Major

`OfficialContext` este una dintre piesele cele mai importante pentru anti-false-positive. Trebuie definit inainte de cod.

Contract minim:

```kotlin
data class OfficialContext(
    val claimedBrands: List<String>,
    val isExactOfficial: Boolean,
    val isOfficialPartner: Boolean,
    val isOfficialTrackingDomain: Boolean,
    val isSafeMarketingContext: Boolean,
    val registryStatus: RegistryStatus,
    val matchedBrandId: String?,
    val matchedDomain: String?,
    val mismatchReasons: List<String>
)

enum class RegistryStatus {
    VALID,
    STALE,
    SIGNATURE_INVALID,
    MISSING,
    BRAND_NOT_FOUND
}
```

Reguli obligatorii:

- `VALID` registry poate sustine `CONTINUE_WITH_CAUTION`.
- `STALE` registry nu poate produce `CONTINUE_WITH_CAUTION` singur; maxim `VERIFY_OFFICIAL`.
- `SIGNATURE_INVALID` inseamna ca registry-ul este ignorat pentru reducerea riscului.
- `MISSING` sau `BRAND_NOT_FOUND` nu inseamna scam; inseamna lipsa de confirmare.
- official exact nu anuleaza reputatie/sandbox malicious.

### NO_REPLY Trebuie Largit Sau Documentat

Logica propusa era prea ingusta:

`hasNoPrimaryUrl && directReplyRisk.isNotEmpty() && asksToReply`

Problema: daca mesajul are si URL, dar cere si cod OTP prin reply, `NO_REPLY` poate fi ratat.

Regula recomandata:

- daca mesajul cere raspuns direct cu OTP/parola/card/CNP/bani, `NO_REPLY` trebuie emis ca actiune de siguranta indiferent daca exista URL;
- daca exista si URL riscant, Gate poate alege verdict mai sever (`NO_ENTER_DATA` sau `DO_NOT_CONTINUE`), dar actiunea `DO_NOT_REPLY_WITH_CODE` ramane in `recommendedActions`;
- `NO_REPLY` este verdict principal doar cand nu exista dovezi URL mai severe.

### Contract VT Intre Adapter Si Gate

Riscul: policy spune `vtDangerousMinEngines = 5`, dar Gate verifica doar `strength >= HIGH && confidence >= 80`. Daca adapter-ul seteaza gresit `strength/confidence`, Gate poate decide gresit.

Solutia recomandata:

- Gate citeste din `details` valorile brute: `maliciousCount`, `phishingCategory`, `lastAnalysisDate`;
- Gate aplica pragurile din `GatePolicy`;
- adapter-ul poate propune `strength`, dar Gate nu se bazeaza exclusiv pe el.

Campuri minime in `EvidenceSignal.details` pentru VT:

- `maliciousCount`;
- `suspiciousCount`;
- `harmlessCount`;
- `undetectedCount`;
- `category`;
- `lastAnalysisDate`;
- `reportAgeDays`.

Teste obligatorii:

- VT malicious 5 -> `DO_NOT_CONTINUE`;
- VT malicious 3 + phishing category -> `DO_NOT_CONTINUE`;
- VT malicious 1-2 + official exact -> `CONTINUE_WITH_CAUTION` + conflict;
- VT stale high count -> nu se foloseste fara revalidare/policy.

### Registry Stale / Invalid Fallback

Spec final trebuie sa spuna exact ce se intampla cand registry-ul este expirat sau semnatura invalida.

Reguli:

- `signatureValid == false`: nu folosim registry-ul ca dovada de official/partner.
- `expiresAt` depasit sub 14 zile: registry poate explica, dar nu poate da safe singur.
- `expiresAt` depasit peste 14 zile: registry este tratat ca missing.
- daca registry invalid si avem doar marketing/link tracking, verdictul devine `VERIFY_OFFICIAL` sau `INSUFFICIENT_EVIDENCE`, nu `CONTINUE_WITH_CAUTION`.
- registry invalid nu ridica risc singur; doar elimina protectia anti-false-positive.

### Upgrade Tardiv De Verdict

Problema: userul poate primi verdict provizoriu la 3 secunde, poate iesi din app, iar la 8-30 secunde sandbox-ul poate intoarce `DO_NOT_CONTINUE`.

Pentru v1:

- nu promitem protectie dupa ce userul paraseste app-ul;
- UI trebuie sa spuna clar la verdict provizoriu: `Analiza avansata inca ruleaza. Nu introduce date pana se termina.`;
- daca app-ul ramane deschis, cardul se actualizeaza inline;
- daca app-ul este inchis, in MVP nu trimitem notificare;
- daca vom activa notificari mai tarziu, mesajul trebuie sa fie neutru si fara URL/text sensibil.

Text UI recomandat:

`Verdict provizoriu. Nu introduce date pana terminam verificarea avansata.`

### Rate Limiting Si Abuse Prevention

Inainte de launch, backend-ul trebuie sa protejeze quota pentru urlscan/VT/Web Risk.

Minim necesar:

- token bucket per device/install id;
- token bucket per IP;
- limita per URL/domain pentru rescan;
- cache-before-provider: verificam cache inainte de a consuma quota externa;
- VT doar fallback selectiv, nu pe orice scanare;
- urlscan submit queue cu backoff si retry-after;
- blocare temporara pentru clienti care trimit volum anormal;
- audit fara raw input.

Regula de produs:

- un user paranoic nu trebuie sa poata consuma quota pentru toti;
- un client rau-intentionat nu trebuie sa poata transforma SigurScan in proxy gratuit pentru urlscan/VT.

### JSON Ruleset Versionat Este Preferat Pentru Policy

Observatie de arhitectura: pentru policy, JSON ruleset semnat este mai pragmatic decat Kotlin Multiplatform in prima faza.

De ce:

- poate fi actualizat server-side rapid;
- poate fi semnat ca registry-ul;
- poate fi testat independent;
- nu blocheaza update-urile de securitate de release-ul din Google Play;
- permite rollback controlat.

Recomandare:

- Android are un fallback local minimal;
- backend foloseste policy JSON semnat si versionat;
- fiecare verdict logheaza `policyVersion` si `registryVersion`;
- corpus tests ruleaza impotriva policy-ului in CI.

## Addendum - Romania Scam Scenario Corpus

Completarea 2/3 adauga o piesa importanta: EvidenceGate nu trebuie sa fie doar URL-centric. Pentru Romania 2026, produsul trebuie sa detecteze si scenarii sociale fara URL.

Document central:

- `/Users/vaduvageorge/AndroidStudioProjects/SigurScan/docs/ROMANIA_SCAM_SCENARIO_CORPUS.md`

Surse relevante verificate:

- SigurantaOnline / campania `Uniti impotriva escrocheriilor`;
- DNSC / Politia Romana / ARB / Mastercard;
- avertismente oficiale de brand, ex. FAN Courier pentru SMS-uri cu locker/link fals;
- Reddit/comunitati doar ca sursa slaba pentru spețe si teste, nu hard evidence.

Scenarii care intra in corpus:

- `Telefonul stricat`;
- `Nepotul la ananghie`;
- `Accidentul`;
- WhatsApp takeover: `Voteaza pe Adeline`, petitie, cod WhatsApp;
- curier/colet/locker/adresa/taxa;
- BNR/politie/banca/credit fraudulos/cont sigur;
- investitii false: Hidroelectrica, broker, cripto, AI investment;
- marketplace/OLX: `ca sa primesti banii`, card/cod SMS;
- loterie/bonus/casino app;
- remote access / AnyDesk / TeamViewer / RDP / APK.

Impact major:

- `NO_REPLY` devine verdict principal, nu doar recommended action;
- text-only family/bank/BNR/WhatsApp scams pot returna `NO_REPLY`;
- marketplace/investitii pot returna `NO_ENTER_DATA`;
- URL + scenariu + domeniu neoficial + date sensibile poate returna `DANGEROUS`;
- `contextul pare real`, ex. asteptam colet, nu reduce riscul.

Reguli candidate:

```text
familie/ruda/copil/nepot + telefon stricat/accident/urgenta + cere bani
=> DO_NOT_REPLY

WhatsApp code/device linking request
=> DO_NOT_REPLY

WhatsApp vote/petition + link + cod WhatsApp
=> DO_NOT_CONTINUE

curier + domeniu neoficial + card/CVV/OTP/WhatsApp code
=> DO_NOT_CONTINUE

banca/politie/BNR + credit fraudulos/cont sigur + transfer/date/install
=> DO_NOT_REPLY

investitie/crypto/Hidroelectrica + date/card/transfer
=> NO_ENTER_DATA

investitie/crypto + remote access/APK/sideload
=> DO_NOT_CONTINUE

marketplace/OLX + "primeste banii" + card/OTP
=> NO_ENTER_DATA sau DO_NOT_CONTINUE daca exista URL/form neoficial
```

Acceptance tests noi obligatorii:

- telefon stricat + cere bani -> `DO_NOT_REPLY`;
- accident/nepot + bani urgent -> `DO_NOT_REPLY`;
- Voteaza pe Adeline + cod WhatsApp -> `DO_NOT_CONTINUE`;
- FANBOX neoficial fara date -> `VERIFY_OFFICIAL`;
- FANBOX neoficial + card/CVV -> `DO_NOT_CONTINUE`;
- BNR/politie/banca + cont sigur -> `DO_NOT_REPLY`;
- Hidroelectrica investitii + date/card -> `NO_ENTER_DATA`;
- broker/crypto + AnyDesk -> `DO_NOT_CONTINUE`;
- OLX/marketplace primeste bani + card/OTP -> `NO_ENTER_DATA` / `DO_NOT_CONTINUE`.

## Concluzie Pentru Sinteza Finala

Acest raspuns este cea mai buna baza pentru EvidenceGate final.

Formula finala de pastrat:

`Extractorii gasesc date -> Sursele externe aduc dovezi -> Registry-ul reduce false positives -> EvidenceGate decide determinist -> RAG explica -> UI spune omului ce sa faca`

Principiul brutal:

SigurScan nu este un AI care ghiceste daca ceva "suna a scam". SigurScan este un sistem de dovezi care decide doar cand dovezile sunt destul de bune.

Pentru Romania, asta este exact ce ne trebuie: sa nu speriem userii cu newslettere reale si sa nu dam safe doar pentru ca Web Risk/urlscan inca nu au prins un scam nou.
