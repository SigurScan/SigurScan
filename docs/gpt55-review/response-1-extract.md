# GPT 5.5 Pro Response 1 - Extract Pentru Spec Final

Data: 2026-06-02

Scop: notite filtrate din primul raspuns GPT 5.5 Pro. Acesta NU este spec final si NU se implementeaza copy-paste. Este material candidat pentru sinteza finala dupa raspunsurile 2 si 3.

## Verdict Pe Raspunsul 1

Util ca structura, incomplet ca logica finala.

Ce merita pastrat:

- data models pentru `EvidenceSignal`, `EvidenceSnapshot`, `GateResult`, `UserResult`;
- separarea surselor semnalelor prin provenance;
- timeout/fallback section;
- cache/TTL section;
- Google Play compliance section;
- set de acceptance tests pentru EvidenceGate;
- ideea ca UI vede summary + recomandari, iar detaliile stau ascunse.

Ce trebuie corectat:

- nu permitem `TEXT_KEYWORD` sa dea `DANGEROUS`;
- nu permitem RAG/corpus sa decida verdict sau sa creeze brand/domeniu nou;
- nu folosim agregare simpla pe `maxCategory.ordinal`;
- nu afisam `Poti continua cu prudenta` cat timp scanarea inca proceseaza;
- nu introducem notificari automate pentru actualizari;
- evitam permisiuni suplimentare precum `FOREGROUND_SERVICE` sau storage runtime daca nu sunt absolut necesare;
- `OFFICIAL_DOMAIN` nu coboara totul la safe daca reputatia/sandbox confirma risc.

## Modele De Date De Pastrat Ca Baza

Sursele semnalelor:

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

Severitate:

```kotlin
enum class Severity {
    INFO,
    WARNING,
    DANGER
}
```

Categorie de risc:

```kotlin
enum class RiskCategory {
    SAFE,
    VERIFY_OFFICIAL,
    NO_ENTER_DATA,
    DANGEROUS
}
```

Semnal individual:

```kotlin
data class EvidenceSignal(
    val source: EvidenceSource,
    val description: String,
    val severity: Severity,
    val riskCategory: RiskCategory,
    val weight: Int,
    val ruleId: String? = null,
    val provider: String? = null
)
```

Snapshot:

```kotlin
data class EvidenceSnapshot(
    val primaryUrl: String?,
    val finalUrl: String?,
    val redirectChain: List<String>,
    val signals: List<EvidenceSignal>,
    val unavailableSources: Set<EvidenceSource> = emptySet(),
    val timestampMillis: Long
)
```

Gate result:

```kotlin
enum class GateResult {
    SAFE,
    VERIFY_OFFICIAL,
    NO_ENTER_DATA,
    DANGEROUS,
    UNKNOWN
}
```

User result:

```kotlin
data class UserResult(
    val gateResult: GateResult,
    val headline: String,
    val recommendations: List<String>,
    val topReasons: List<String>,
    val detailedSignals: List<EvidenceSignal>
)
```

## Reguli De Decizie Extrase, Dar Corectate

### Poate Da `DANGEROUS`

Acceptam:

- `REPUTATION` malicious: Google Web Risk, blacklist validata, VirusTotal relevant fallback;
- `SANDBOX` malicious: urlscan phishing/malware/brand impersonation clar;
- `STRUCTURAL` cu intent sensibil clar pe domeniu neoficial: card, CVV, OTP, parola, CNP, IBAN, login, plata;
- APK/download/remote access pe domeniu neoficial;
- user feedback doar daca este validat backend/corpus, nu doar un singur raport.

Nu acceptam:

- `TEXT_KEYWORD` singur;
- `HIDDEN_LINK` singur;
- `CORPUS` singur;
- RAG output;
- marketing urgency.

### Poate Da `NO_ENTER_DATA`

Acceptam:

- formular card/OTP/parola/login pe domeniu neoficial;
- form action catre domeniu neoficial;
- link vizibil oficial, dar href/final URL neoficial si pagina cere date;
- reputatie clean/no-match, dar structural sensibil confirmat.

Nu acceptam:

- link sub buton fara pagina/form/intent sensibil;
- text despre oferta/voucher/factura fara URL/final URL clar.

### Max `VERIFY_OFFICIAL`

Acestea sunt capped:

- `TEXT_KEYWORD`;
- `HIDDEN_LINK` fara intent sensibil confirmat;
- `CORPUS`/similarity fara reputatie/structural;
- user feedback neconfirmat;
- sender/reply-to mismatch fara pagina sensibila;
- marketing urgency;
- tracking link nevalidat.

### `SAFE`

Acceptam doar cand:

- final URL cunoscut;
- domeniu oficial sau tracking legitim cu fallback oficial;
- fara Web Risk/blacklist/urlscan/VT malicious;
- fara formular sensibil pe domeniu neoficial;
- brand/context coerent.

### `UNKNOWN`

Acceptam cand:

- nu exista URL/final URL;
- Web Risk/urlscan/VT indisponibile si nu avem dovezi structurale;
- webmail shell fara corp real;
- semnale contradictorii fara strong signal;
- input vag.

## Conflict Resolution De Pastrat

Precedenta recomandata:

1. `REPUTATION` malicious sau `SANDBOX` malicious bate domeniu oficial.
2. Web Risk clean/no-match nu anuleaza structural sensibil pe domeniu neoficial.
3. User feedback neconfirmat + reputatie clean ramane `VERIFY_OFFICIAL`.
4. `OFFICIAL_DOMAIN` poate cobori semnale slabe la `SAFE` sau `VERIFY_OFFICIAL`, dar nu poate anula reputatie/sandbox malicious.

## Timeout/Fallback - Ce Păstrăm

Stari UX recomandate, corectate:

| Timp | UI | Background |
| --- | --- | --- |
| `<3s` | `Analizăm linkul...` | extractor, primary URL, cache, Web Risk |
| `3-8s` | `Încă verificăm destinația reală...` | urlscan submitted, Web Risk result may arrive |
| `8-30s` | verdict preliminar daca gate are dovezi; altfel `Nu pot verifica suficient încă` | polling urlscan, VT fallback daca policy cere |
| `>30s` | `Nu pot verifica suficient` sau verdict bazat pe dovezi disponibile | async update in app/history, fara notificari automate |

Important:

- nu afisam `Poti continua cu prudenta` cat timp lipseste final URL sau reputatie;
- urlscan 404/429/timeout nu inseamna safe;
- VT ruleaza fallback doar cand Web Risk/urlscan/gate nu sunt suficiente;
- actualizarile se fac in app/history, nu prin notificari automate.

## Cache/TTL - Ce Păstrăm

Candidate TTLs:

| Sursa | TTL recomandat |
| --- | --- |
| Web Risk positive | pana la `expireTime` |
| Web Risk no-match | scurt, de ordinul minutelor/orelor, nu dovada de siguranta |
| urlscan malicious | 12h |
| urlscan clean/no malicious | 6h |
| VirusTotal malicious | 24h |
| VirusTotal clean/not found | 12h sau mai putin |
| Official domains registry | versionat, update periodic |
| Local structural/text signals | nu cache-uim |
| User feedback | 90 zile, apoi anonimizare/stergere |

De rafinat in final:

- TTL exact pentru Web Risk no-match trebuie verificat cu API/contract; nu inventam `negativeExpireTime` daca endpointul folosit nu il ofera.
- cache-ul final trebuie pe backend, nu in APK.

## Google Play - Ce Păstrăm

Permisiuni ok pentru prima versiune:

- `INTERNET`;
- `CAMERA` doar pentru QR/OCR, ceruta la runtime;
- share/import via Android intents si system picker.

Permisiuni de evitat:

- `READ_SMS`;
- `RECEIVE_SMS`;
- `BIND_NOTIFICATION_LISTENER_SERVICE`;
- `BIND_ACCESSIBILITY_SERVICE`;
- storage broad permissions daca putem folosi picker/share URI.

Privacy Policy trebuie sa spuna:

- scanarea este exclusiv user-initiated;
- app-ul nu monitorizeaza notificari/SMS/alte aplicatii;
- URL-urile pot fi trimise la backend, urlscan.io, Google Web Risk, VirusTotal;
- PII/tokenurile sunt redactate inainte de urlscan cand este posibil;
- datele nu sunt folosite pentru marketing;
- RAG/AI primeste doar evidence summary/redacted input, daca este folosit.

Data Safety trebuie sa includa:

- app activity pentru scan events;
- diagnostics pentru erori;
- URL-uri/redacted content ca data folosita pentru security/fraud prevention;
- third-party sharing cu urlscan/Web Risk/VT/backend/AI provider, daca activ.

Listing Play trebuie sa spuna:

- app de verificare/educatie anti-scam;
- nu este serviciu financiar;
- nu intermediaza plati;
- nu monitorizeaza userul;
- scaneaza doar la share/import/paste/QR/OCR ales de user.

## Acceptance Tests De Păstrat Si Corectat

### Dangerous

1. ANAF fake cu reputatie malicious + formular card => `DANGEROUS`.
2. FAN fake taxa + OTP/form neoficial => `NO_ENTER_DATA` sau `DANGEROUS`, in functie de reputatie/sandbox.
3. Revolut OTP phishing cu hidden link + structural sensibil => `NO_ENTER_DATA` sau `DANGEROUS`.
4. APK remote access cu VT/urlscan malicious => `DANGEROUS`.
5. Web Risk phishing + urlscan clean => `DANGEROUS`.
6. Web Risk clean + urlscan phishing => `DANGEROUS`.

### False Positive Guards

7. Uber promo real cu domeniu/fallback oficial => `SAFE`.
8. eMAG newsletter real => `SAFE`.
9. FAN tracking real => `SAFE`.
10. Domeniu oficial + marketing urgency => `SAFE` sau `VERIFY_OFFICIAL`, niciodata `DANGEROUS`.
11. Text marketing generic fara URL => `VERIFY_OFFICIAL` sau `UNKNOWN`, nu `DANGEROUS`.

### Unknown/Fallback

12. Webmail shell fara corp real => `UNKNOWN`.
13. urlscan down + Web Risk unavailable + text/hide-link slab => `UNKNOWN`.
14. urlscan down + structural sensibil => `NO_ENTER_DATA`.
15. input vag fara URL => `UNKNOWN`.

### Conflict/Cap

16. User feedback scam, reputatie clean, fara alte dovezi => `VERIFY_OFFICIAL`.
17. Corpus similar scam, reputatie clean, fara structural => `VERIFY_OFFICIAL`.
18. Hidden link + reputation clean, fara sensitive intent => `VERIFY_OFFICIAL`, nu `NO_ENTER_DATA` default.
19. Pagina login pe domeniu necunoscut => `NO_ENTER_DATA`.
20. Semnale multiple slabe text/link => `VERIFY_OFFICIAL`.

## Elemente Din Răspunsul 1 Pe Care Nu Le Folosim

- `TEXT_KEYWORD -> DANGEROUS`;
- `CORPUS/model RAG a determinat scam clar`;
- `maxCategory.ordinal` ca algoritm final;
- agregare prin scor fara cap pe source;
- `Poti continua cu prudenta` in 3-8s cand scanarea nu e gata;
- notificare automata cand scanarea se actualizeaza;
- `FOREGROUND_SERVICE` ca permisie recomandata by default;
- storage permissions broad by default;
- orice formulare care sugereaza ca app-ul monitorizeaza notificari/SMS.

## Nota Pentru Sinteza Finala

Raspunsul 1 are structura buna, dar trebuie combinat cu regulile noastre stricte:

- `EvidenceGate` este precedence/cap based, nu score-only.
- RAG si corpus sunt consultative.
- Text-only si marketing-only sunt capped.
- Reputatie/sandbox malicious sunt hard evidence.
- Structural sensibil pe domeniu neoficial protejeaza userul cu `NO_ENTER_DATA`.
- Play Store release trebuie sa ramana user-initiated, fara notificari/SMS/accessibility.
