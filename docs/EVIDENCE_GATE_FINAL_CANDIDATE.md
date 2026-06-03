# SigurScan EvidenceGate Final Candidate

Data: 2026-06-02

Status: candidate spec, nu source of truth final. Pentru Launch Candidate v1, documentul reconciliat este `docs/LAUNCH_ARCHITECTURE_FINAL.md`. Acest document ramane baza tehnica detaliata si input pentru implementare/teste.

Surse de sinteza:

- `docs/PRODUCT_CORE_LINK_TRUTH.md`
- `docs/gpt55-review/response-1-extract.md`
- `docs/gpt55-review/response-2-extract.md`
- `docs/gpt55-review/response-2-of-3-extract.md`
- `docs/gpt55-review/gemini-extract.md`
- `docs/gpt55-review/sonnet-extract.md`
- `docs/ROMANIA_SCAM_SCENARIO_CORPUS.md`
- `/Users/vaduvageorge/.codex/attachments/c472802d-0eda-4a4c-b812-2c57c6bf31b2/pasted-text.txt`
- `/Users/vaduvageorge/.codex/attachments/6d5623d5-179b-44fb-b21b-19b5a9438a53/pasted-text.txt`

## Verdict Brutal

Directia combinata este buna si implementabila.

Ce ramane:

- un singur `EvidenceGate` determinist;
- toate sursele produc `EvidenceSignal`, nu verdict;
- RAG explica, nu decide;
- fara procente in UI;
- scanare doar la actiunea userului;
- `urlscan` ca moat vizual: final URL, redirect chain, preview/sandbox;
- Google Web Risk ca reputatie rapida;
- VirusTotal doar fallback selectiv si doar cu licenta/policy potrivita pentru productie;
- Official Registry cu domenii oficiale, delegated providers si tracking domains;
- fiecare semnal are provenance, cap si eligibility;
- default fara dovezi verificabile: `INSUFFICIENT_EVIDENCE`;
- default cu artifact analizabil dar neconcludent: `VERIFY_OFFICIAL`.

Corectie fata de promptul combinat:

- text-only care cere OTP/parola/card/bani prin raspuns poate produce `DO_NOT_REPLY` ca actiune principala, chiar daca nu exista URL;
- text-only nu produce `DANGEROUS`;
- `CONTINUE_WITH_CAUTION` nu apare daca lipseste final URL necesar, registry valid sau daca scanarea e redacted/incompleta;
- source "clean/no-match/no-detections" este suport slab, nu safe.

## Principiu Central

Intrebarea produsului:

```text
Linkul duce unde pretinde mesajul ca duce?
```

Regula de aur:

```text
Claimed brand != final official/partner domain
+ user is asked to act
= Nu continua / Verifica oficial, dupa severitate
```

Regula stricta:

```text
Claimed brand != final official/partner domain
+ asks for card / OTP / password / login / payment / CNP / IBAN / APK / remote access
= Nu introduce date sau Nu continua
```

## Pipeline

```text
User action explicita
-> local extractor: text / HTML / URL / QR / OCR / file
-> PrimaryUrlPicker
-> PII Redaction
-> Official Registry
-> Web Risk
-> urlscan private sandbox + preview
-> VirusTotal fallback selectiv
-> Corpus / feedback curated
-> EvidenceSnapshot
-> EvidenceGate
-> GateResult
-> RAG explainer read-only
-> UserResult fara procente
```

Nu exista monitorizare automata de SMS, notificari, WhatsApp, clipboard continuu sau alte aplicatii.

## Verdicturi User-Facing

```kotlin
enum class MachineVerdict {
    CONTINUE_WITH_CAUTION,
    VERIFY_OFFICIAL,
    NO_ENTER_DATA,
    DO_NOT_REPLY,
    DANGEROUS,
    UNKNOWN
}

enum class UserAction {
    CONTINUE_WITH_CAUTION, // Poti continua cu prudenta
    DO_NOT_CONTINUE,       // Nu continua
    DO_NOT_ENTER_DATA,     // Nu introduce date
    DO_NOT_REPLY,          // Nu raspunde
    VERIFY_OFFICIAL,       // Verifica pe canalul oficial
    INSUFFICIENT_EVIDENCE  // Nu pot verifica suficient
}
```

Mapping:

| MachineVerdict | UserAction | User label |
| --- | --- | --- |
| `DANGEROUS` | `DO_NOT_CONTINUE` | `Nu continua` |
| `NO_ENTER_DATA` | `DO_NOT_ENTER_DATA` | `Nu introduce date` |
| `DO_NOT_REPLY` | `DO_NOT_REPLY` | `Nu raspunde` |
| `VERIFY_OFFICIAL` | `VERIFY_OFFICIAL` | `Verifica pe canalul oficial` |
| `CONTINUE_WITH_CAUTION` | `CONTINUE_WITH_CAUTION` | `Poti continua cu prudenta` |
| `UNKNOWN` | `INSUFFICIENT_EVIDENCE` | `Nu pot verifica suficient` |

Nu folosim:

- `safe`;
- procente;
- scor vizibil;
- "100% sigur";
- "protectie garantata".

## Data Models Minime

### Input

```kotlin
enum class InputKind {
    URL,
    TEXT,
    HTML_EMAIL,
    IMAGE_OCR,
    QR,
    FILE_IMPORT,
    UNKNOWN
}

enum class ScanMode {
    SHARE,
    IMPORT,
    UPLOAD,
    PASTE,
    QR_SCAN,
    OCR_SCAN
}
```

### Provenance / Source

```kotlin
enum class Provenance {
    TEXT_KEYWORD,
    HIDDEN_LINK,
    STRUCTURAL,
    REPUTATION,
    OFFICIAL_DOMAIN,
    SANDBOX,
    USER_FEEDBACK,
    CORPUS
}

enum class SourceName {
    LOCAL_EXTRACTOR,
    PRIMARY_URL_PICKER,
    OFFICIAL_REGISTRY,
    WEB_RISK,
    URLSCAN,
    VIRUSTOTAL,
    USER_FEEDBACK_SERVICE,
    CORPUS_SERVICE,
    OFFLINE_POLICY,
    RAG_EXPLAINER
}

enum class SourceStatus {
    NOT_RUN,
    OK,
    CLEAN_NO_MATCH,
    MATCH,
    UNAVAILABLE,
    TIMEOUT,
    RATE_LIMITED,
    ERROR,
    STALE_CACHE,
    PENDING,
    SKIPPED_PRIVACY,
    SKIPPED_POLICY
}
```

`RAG_EXPLAINER` is never decision-eligible.

### Signal Cap

```kotlin
enum class SignalLevel {
    INFO,
    WEAK,
    MODERATE,
    STRONG,
    CRITICAL
}

enum class GateCap {
    NONE,
    MAX_CONTINUE_WITH_CAUTION,
    MAX_VERIFY_OFFICIAL,
    MAX_NO_ENTER_DATA
}
```

### Observable

```kotlin
enum class ObservableType {
    URL,
    FINAL_URL,
    HOST,
    DOMAIN,
    TEXT,
    PHONE,
    EMAIL,
    FILE_HASH,
    APK_PACKAGE,
    UNKNOWN
}

data class Observable(
    val type: ObservableType,
    val valueHash: String,
    val displayValueRedacted: String?,
    val normalizedValue: String?,
    val eTldPlusOne: String? = null,
    val host: String? = null
)
```

Hash-ul trebuie sa fie stabil si privacy-safe, preferabil HMAC/cryptographic hash. Nu folosim Kotlin `hashCode()`.

### EvidenceSignal

```kotlin
data class EvidenceSignal(
    val id: String,
    val provenance: Provenance,
    val source: SourceName,
    val code: SignalCode,
    val level: SignalLevel,
    val cap: GateCap,
    val observable: Observable,
    val status: SourceStatus,
    val observedAt: Instant,
    val ttlExpiresAt: Instant? = null,
    val facts: Map<String, String> = emptyMap(),
    val userVisibleEvidence: String,
    val redactionState: RedactionState = RedactionState.REDACTED,
    val sourceLatencyMs: Long? = null,
    val adapterVersion: String
) {
    fun isExpired(now: Instant): Boolean =
        ttlExpiresAt != null && ttlExpiresAt.isBefore(now)

    fun isUsableAt(now: Instant): Boolean =
        status !in setOf(SourceStatus.ERROR, SourceStatus.UNAVAILABLE) &&
        !isExpired(now) &&
        source != SourceName.RAG_EXPLAINER
}
```

### EvidenceSnapshot

```kotlin
data class EvidenceSnapshot(
    val scanId: String,
    val scanMode: ScanMode,
    val inputKind: InputKind,
    val createdAt: Instant,
    val policyVersion: String,
    val gateVersion: String,
    val registryVersion: RegistryVersion?,
    val primaryUrl: UrlEvidence?,
    val finalUrl: UrlEvidence?,
    val redirectChain: List<RedirectHop>,
    val urlCandidates: List<UrlEvidence>,
    val brandClaims: List<BrandClaim>,
    val sourceStates: Map<SourceName, SourceRunState>,
    val cacheSummary: CacheSummary,
    val signals: List<EvidenceSignal>,
    val piiRedaction: PiiRedactionSummary,
    val rawContentStored: Boolean = false,
    val backendReachable: Boolean,
    val asyncJobs: List<AsyncJobRef> = emptyList()
)
```

Production rule:

- `rawContentStored` default false;
- raw email/text/OCR image is not stored server-side;
- query tokens and PII are removed before third-party submission.

## Signal Families

### Hard danger

Can produce `DANGEROUS`:

- `WEB_RISK_MATCH_MALWARE`;
- `WEB_RISK_MATCH_SOCIAL_ENGINEERING`;
- `WEB_RISK_MATCH_UNWANTED_SOFTWARE`;
- `URLSCAN_VERDICT_MALICIOUS`;
- `URLSCAN_BRAND_IMPERSONATION` with unofficial domain and secret collection;
- `URLSCAN_APK_DOWNLOAD` with sideload/remote access context;
- `VT_MALICIOUS_QUORUM`;
- `CORPUS_CONFIRMED_SCAM_URL`;
- `CORPUS_CONFIRMED_SCAM_DOMAIN`;
- `CORPUS_CONFIRMED_SCAM_CONTACT`;
- `USER_REPORT_VERIFIED_CLUSTER`, only after anti-abuse/review.

### Secret collection

Can produce `NO_ENTER_DATA`, and can produce `DANGEROUS` when combined with brand impersonation/unofficial domain:

- card/CVV form;
- OTP form;
- password/login form;
- CNP/IBAN/personal data form;
- payment request on unofficial domain;
- final domain differs from visible/claimed brand.

### Weak/capped

Max `VERIFY_OFFICIAL` alone:

- promo language;
- urgency;
- voucher;
- commercial text;
- HTML email;
- hidden link under button;
- tracking link;
- newsletter structure;
- unsubscribe link;
- shortener unresolved;
- corpus similarity-only;
- raw user report;
- RAG output;
- Web Risk no-match;
- VT no detections;
- urlscan clean.

### Text-only reply risk

Important correction:

- text-only request for OTP/card/password/money does not become `DANGEROUS`;
- if it asks the user to reply/send code/money/data, it can become `DO_NOT_REPLY`;
- if no explicit reply path/contact is present, cap at `VERIFY_OFFICIAL`;
- if phone/email/IBAN/contact is confirmed bad in corpus, can become `DO_NOT_REPLY` or `DANGEROUS` depending on policy and evidence.

## Romania Scam Scenario Corpus

This is required for Romania. Without it, SigurScan catches URL phishing but misses text/call/social-engineering scams such as `Telefonul stricat`, `Accidentul`, `BNR/cont sigur`, WhatsApp takeover, marketplace escrow and fake investments.

Canonical spec:

- `docs/ROMANIA_SCAM_SCENARIO_CORPUS.md`

Scenario families:

- `URGENCY_BIG`: nepot/accident/imprumut/WhatsApp/telefon stricat/petitie;
- `OFFICIAL_PHONE`: credit/colet/BNR/legitimatie;
- `OVERNIGHT_GAIN`: Hidroelectrica/broker/crypto/aplicatie bancara/marketplace/investitii AI/loterie;
- `DELIVERY_PHISHING`: locker/adresa/taxa/colet;
- `ACCOUNT_TAKEOVER`: WhatsApp code/device linking;
- `MARKETPLACE_ESCROW`: `ca sa primesti banii`, card/cod SMS;
- `TEXT_ONLY_FAMILY_SCAM`: ruda/copil/nepot + urgenta + bani.

Scenario signals do not replace `Link Truth`; they cover scams where the dangerous action is reply/transfer/install, not only URL click.

Rules:

- `FAMILY_NEW_PHONE` + money request -> `DO_NOT_REPLY`;
- `ACCIDENT_OR_NEPHEW_AI_VOICE` + urgent money -> `DO_NOT_REPLY`;
- WhatsApp code/device-link request -> `DO_NOT_REPLY`;
- WhatsApp vote/petition + link + code request -> `DANGEROUS`;
- courier claim + unofficial domain + card/CVV/OTP/WhatsApp code -> `DANGEROUS`;
- courier claim + unofficial domain without sensitive ask -> `VERIFY_OFFICIAL`;
- BNR/police/bank safe-account/credit scenario -> `DO_NOT_REPLY`;
- official authority claim + unofficial URL + banking/card form -> `DANGEROUS`;
- investment/crypto/Hidroelectrica hook + personal/card/transfer request -> `NO_ENTER_DATA`;
- investment hook + AnyDesk/TeamViewer/RDP/APK/sideload -> `DANGEROUS`;
- marketplace `receive money` + card/OTP -> `NO_ENTER_DATA` or `DANGEROUS` with unofficial URL/form.

Reliability:

- official campaigns and brand official warnings can create curated scenario/corpus signals;
- curated Reddit/community cases are useful for tests and discovery, but cannot block alone;
- raw user/community reports remain capped until verified.

## EvidenceGate Decision Order

```text
G00 no analyzable artifact -> UNKNOWN
G10 hard malicious evidence -> DANGEROUS
G20 APK / remote access / sideload compound -> DANGEROUS
G30 brand impersonation + unofficial/lookalike domain + secret collection -> DANGEROUS
G32 Romanian scenario with URL + sensitive/unofficial destination -> DANGEROUS / NO_ENTER_DATA
G35 text-only direct reply secret/money request -> DO_NOT_REPLY
G40 secret collection on untrusted/unofficial domain -> NO_ENTER_DATA
G50 known bad reply contact -> DO_NOT_REPLY
G60 text-only high-risk with no reply/contact evidence -> VERIFY_OFFICIAL
G70 low-confidence reputation + high-risk context -> NO_ENTER_DATA
G80 recognized official/delegated marketing flow -> CONTINUE_WITH_CAUTION
G90 only capped weak signals -> VERIFY_OFFICIAL
G95 critical sources failed and no local evidence -> UNKNOWN
G99 default with analyzable artifact -> VERIFY_OFFICIAL
```

Default split:

- no artifact / no URL / no brand / no contact / OCR unusable -> `UNKNOWN`;
- artifact exists but evidence is not enough -> `VERIFY_OFFICIAL`;
- never default to `CONTINUE_WITH_CAUTION`.

## Conditions For Continue With Caution

`CONTINUE_WITH_CAUTION` is allowed only when all are true:

- final URL is known or official/delegated relation is strong enough;
- registry is valid, not stale/invalid;
- domain is official, delegated provider, official tracking domain, or verified partner;
- no secret collection on unofficial domain;
- no APK/sideload/remote access;
- no reputation/sandbox/corpus malicious;
- redaction did not materially break scan fidelity;
- if sandbox is required for the risk profile and still pending, result is provisional or stays `VERIFY_OFFICIAL`.

`WEB_RISK_NO_MATCH`, `URLSCAN_VERDICT_CLEAN` or `VT_NO_DETECTIONS` cannot produce `CONTINUE_WITH_CAUTION` alone.

## Conflict Resolution

| Conflict | Resolution |
| --- | --- |
| Web Risk no-match + urlscan malicious | `DANGEROUS` |
| Web Risk no-match + card/OTP/password on unofficial domain | `NO_ENTER_DATA` |
| urlscan clean + structural secret collection | `NO_ENTER_DATA` |
| official registry match + Web Risk/urlscan malicious | `DANGEROUS` + review |
| official registry match + VT 1 weak/stale hit | caution/verify + conflict, not dangerous |
| hidden link mismatch + final official | no block, likely tracking/delegation |
| hidden link mismatch + final unofficial + login/card | `NO_ENTER_DATA` or `DANGEROUS` if impersonation clear |
| corpus similarity-only + clean reputation | max `VERIFY_OFFICIAL` |
| raw user report + clean sources | max `VERIFY_OFFICIAL` |
| old cache clean + fresh malicious signal | fresh malicious wins |

Clean/no-match/no-detection is negative evidence only. It cannot erase positive high-risk evidence.

## UNKNOWN / Insufficient Evidence

Return `UNKNOWN` / `Nu pot verifica suficient` when:

- no URL/domain/contact/file/hash can be checked;
- webmail shell only;
- OCR confidence too low;
- QR invalid/unparseable;
- backend down and only weak local signals;
- urlscan/Web Risk/VT unavailable with no cache and neutral structure;
- URL is tokenized/private and redaction blocks third-party submission;
- no final URL and no enough local context.

UNKNOWN is not safe and not scam.

## Marketing False Positive Policy

Do not block for:

- HTML email;
- hidden button link;
- tracking link;
- unsubscribe link;
- newsletter layout;
- promo language;
- shortener alone;
- redirect alone.

Judge by:

- final URL;
- brand claim;
- official/delegated registry;
- sensitive intent;
- reputation/sandbox/corpus.

Official Registry must include:

```kotlin
data class OfficialDomainEntry(
    val brandKey: String,
    val displayName: String,
    val officialDomains: Set<String>,
    val delegatedProviders: List<DelegatedProvider>,
    val allowedTrackingDomains: Set<String>,
    val allowedPaymentProviders: Set<String>,
    val validFrom: Instant,
    val validTo: Instant?,
    val sourceRefs: List<String>,
    val confidence: RegistryConfidence
)

data class DelegatedProvider(
    val providerDomain: String,
    val relationType: DelegationType,
    val allowedPathPrefixes: Set<String> = emptySet(),
    val notes: String
)
```

Without delegated providers, real Uber/eMAG/FAN/payment flows will be false positives.

## Provider Policy

### Web Risk

- match -> can produce `DANGEROUS`;
- no-match -> never safe by itself;
- positive cache by provider `expireTime`;
- no-match cache short and used only for performance/supporting evidence.

### urlscan

- use Private by default;
- 404 result can mean pending, not failure;
- handle 429 with backoff/circuit breaker;
- collect final URL, redirect chain, screenshot/preview, DOM form indicators;
- clean result is not safe absolute;
- malicious/suspicious/form/impersonation can be hard evidence.

### VirusTotal

- fallback only;
- do not use Public API for production commercial flow without compatible license/contract;
- run only for high-risk/conflict/remote unavailable cases;
- no raw sensitive upload;
- high-confidence quorum can produce `DANGEROUS`;
- low-confidence hits can support `NO_ENTER_DATA` but not block alone.

### RAG

- receives only GateResult + redacted evidence chips + rule ids + conflicts;
- does not receive raw email body, raw URL query, OTP, card, CNP;
- cannot mutate verdict/action;
- if RAG is down, show rule-based explanation.

## Timeout / Fallback

| Time | Work | UI |
| --- | --- | --- |
| `0-1s` | extractor, PrimaryUrlPicker, redaction, cache, registry | `Verificam...` |
| `<=3s` | Web Risk, local structural, cache/urlscan cache | hard result if available, otherwise interim |
| `<=8s` | urlscan submit/poll, reputation complete, optional cached VT | provisional/final result |
| `<=30s` | final urlscan polling, VT fallback if justified | final or `FINAL_WITH_ASYNC_PENDING` |
| `>30s` | async jobs only for user-initiated scan | update scan history; notifications only opt-in later |

Important:

- no automatic background monitoring;
- no sensitive URL/text in notifications;
- if redaction reduces fidelity, never show final `CONTINUE_WITH_CAUTION` based only on redacted scan.

## Cache / TTL

| Artifact | TTL | Gate usage |
| --- | --- | --- |
| Web Risk match | provider `expireTime` | can produce `DANGEROUS` |
| Web Risk no-match | 5-15 min | supporting only |
| urlscan malicious | 24h strong exact URL, 7d history | can produce `DANGEROUS`, revalidate if old |
| urlscan clean | 6h exact URL | supporting only |
| urlscan render incomplete | 1h | missing/weak evidence |
| VT malicious quorum | 24h exact URL, 7d weak domain | can produce `DANGEROUS` |
| VT low suspicious | 6-24h | max `NO_ENTER_DATA` in context |
| VT no detection | 6h exact URL | supporting only |
| Official Registry | refresh daily; stale 14d; hard stale 30d | registry stale cannot produce strong caution |
| Corpus confirmed URL | 14d | can produce `DANGEROUS` |
| Corpus confirmed domain/contact | 30d | can produce `DANGEROUS` with decay |
| Raw feedback | aggregate only, 30d | max `VERIFY_OFFICIAL` until verified |

Never cache server-side:

- raw email HTML/body;
- raw pasted text;
- raw OCR image;
- URL query params with token/email/phone/session/auth;
- OTP/card/CVV/password/CNP/IBAN;
- screenshot/DOM with PII;
- user IP as evidence;
- raw RAG explanation with user content.

## Android V1 Requirements

Manifest:

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
<uses-permission android:name="android.permission.CAMERA" />
```

Avoid:

- SMS permissions;
- notification listener;
- accessibility service;
- contacts;
- usage stats;
- installed apps;
- broad media access;
- `MANAGE_EXTERNAL_STORAGE`;
- location;
- VPN;
- overlay.

Entry points:

- `ACTION_SEND` text/html/url;
- `ACTION_PROCESS_TEXT`;
- explicit paste;
- QR scan;
- OCR/import via user picker;
- file import via `ACTION_OPEN_DOCUMENT`;
- Android Photo Picker for images.

Local extraction:

- parse text/html/email;
- extract anchors and hidden button links;
- detect visible text vs href mismatch;
- run PrimaryUrlPicker;
- run PII redaction;
- compute normalized URL hash;
- mark if redaction reduced fidelity.

UI:

- no percentages;
- no `safe`;
- show label, 2-4 evidence chips, 1-3 next steps;
- show provisional/final state;
- if async pending: `Verificarea sandbox poate actualiza rezultatul.`

History:

- local scanId, verdict, redacted domain, timestamp;
- no raw email/text/OCR stored by default.

## Backend V1 Requirements

Services:

- `scan-api`;
- `evidence-normalizer`;
- `official-registry-service`;
- `web-risk-adapter`;
- `urlscan-adapter`;
- `virustotal-adapter`;
- `corpus-service`;
- `feedback-service`;
- `evidence-gate-service`;
- `rag-explainer-service`.

Adapter contract:

```kotlin
interface EvidenceAdapter {
    val sourceName: SourceName
    suspend fun collect(request: ScanRequest, context: AdapterContext): AdapterResult
}

data class AdapterResult(
    val source: SourceName,
    val status: SourceStatus,
    val signals: List<EvidenceSignal>,
    val retryAfter: Instant? = null,
    val asyncJob: AsyncJobRef? = null,
    val latencyMs: Long
)
```

No adapter returns a final verdict.

## Compliance Checklist

Privacy Policy must disclose:

- user-initiated scans only;
- no automatic SMS/WhatsApp/notification/clipboard monitoring;
- data sent to backend: redacted URLs/text/features/statuses;
- third parties: Google Web Risk, urlscan, VirusTotal, AI provider if used;
- urlscan private scans and screenshot/DOM metadata;
- VirusTotal fallback and commercial/license constraints;
- retention;
- deletion request;
- TLS/encryption/access control;
- no data sale;
- no advertising profiling.

Data Safety:

- declare off-device URL/text/image/file processing if implemented;
- declare diagnostics/crash logs if used;
- declare third-party sharing;
- mark purpose as app functionality, security/fraud prevention, diagnostics;
- do not claim "no data collected" if backend/provider checks exist.

Store listing:

- "verifica linkuri si mesaje suspecte";
- "scanarea porneste doar cand alegi tu";
- no "100% protection";
- no "detects all scams";
- no fake affiliation with ANAF/FAN/eMAG/banks;
- no financial service claims.

## Acceptance Tests

Minimum corpus tests:

1. Uber real promo -> `CONTINUE_WITH_CAUTION`.
2. eMAG newsletter real -> `CONTINUE_WITH_CAUTION`.
3. FAN real tracking -> `CONTINUE_WITH_CAUTION`.
4. Newsletter bank real -> `CONTINUE_WITH_CAUTION`.
5. Tracking link no final resolved -> `VERIFY_OFFICIAL`.
6. Promo text-only without URL -> `VERIFY_OFFICIAL` or `UNKNOWN`, never dangerous.
7. ANAF fake payment/card form -> `DANGEROUS`.
8. FAN fake tax/card -> `DANGEROUS`.
9. Revolut fake OTP/login form on unofficial domain -> `DANGEROUS`.
10. APK remote access -> `DANGEROUS`.
11. Web Risk malware -> `DANGEROUS`.
12. Web Risk social engineering -> `DANGEROUS`.
13. urlscan malicious + Web Risk no-match -> `DANGEROUS`.
14. VT malicious quorum fallback -> `DANGEROUS`.
15. VT 1 suspicious engine + official domain -> not dangerous.
16. urlscan clean + card form unofficial -> `NO_ENTER_DATA`.
17. Web Risk no-match + structural suspicious -> `NO_ENTER_DATA`.
18. Hidden button link only -> `VERIFY_OFFICIAL`.
19. Hidden/tracking link final official -> `CONTINUE_WITH_CAUTION`.
20. Raw user report only -> `VERIFY_OFFICIAL`.
21. Corpus similarity-only -> `VERIFY_OFFICIAL`.
22. RAG says scam only -> max `VERIFY_OFFICIAL`; Gate ignores RAG.
23. urlscan down + Web Risk unavailable + neutral local -> `UNKNOWN`.
24. Webmail shell only -> `UNKNOWN`.
25. OCR low confidence -> `UNKNOWN`.
26. Web Risk clean + urlscan malicious conflict -> `DANGEROUS`.
27. Official domain + Web Risk malicious conflict -> `DANGEROUS` + review.
28. Delegated payment provider verified -> `CONTINUE_WITH_CAUTION`.
29. Unknown payment provider -> `NO_ENTER_DATA`.
30. Shortener only no final -> `VERIFY_OFFICIAL`.
31. Text-only asks OTP by reply -> `DO_NOT_REPLY`.
32. Text-only vague OTP/card keyword without reply/contact -> `VERIFY_OFFICIAL`.
33. Telefon stricat + numar nou + cere bani -> `DO_NOT_REPLY`.
34. Accident/nepot la ananghie + cere bani urgent -> `DO_NOT_REPLY`.
35. WhatsApp `Voteaza pe Adeline` + cod WhatsApp -> `DANGEROUS`.
36. Petitie WhatsApp + cod verificare -> `DANGEROUS`.
37. FANBOX/locker + domeniu neoficial fara date -> `VERIFY_OFFICIAL`.
38. FANBOX/locker + domeniu neoficial + card/CVV -> `DANGEROUS`.
39. BNR/politie/banca + `cont sigur` -> `DO_NOT_REPLY`.
40. Hidroelectrica/investitii + formular date/card -> `NO_ENTER_DATA`.
41. Broker/crypto + AnyDesk/remote access -> `DANGEROUS`.
42. Marketplace/OLX `ca sa primesti banii` + card/OTP -> `NO_ENTER_DATA` or `DANGEROUS` if URL/form unofficial.

## Sprint Plan

### Sprint 1 - Gate Core

1. Add data models.
2. Implement `EvidenceGate` pure function.
3. Add `SignalCode -> cap/verdict eligibility` in `GatePolicy`.
4. Add 30+ acceptance tests.
5. Add Romania scenario tests from `ROMANIA_SCAM_SCENARIO_CORPUS.md`.
6. Ensure RAG cannot influence verdict.

### Sprint 2 - Source Adapters

1. Normalize all adapters into `EvidenceSignal`.
2. Web Risk TTL/cache.
3. urlscan private submit/poll, 404 pending, 429/backoff, form detector.
4. VT fallback with license guard.
5. Official Registry signed version with delegated providers.

### Sprint 3 - UI/UX

1. Provisional/final states.
2. 3s/8s/30s behavior.
3. Evidence chips, no percentages.
4. Copy for all 6 actions.
5. Scan history async update.

### Sprint 4 - Compliance

1. Manifest permission audit.
2. Privacy Policy public URL.
3. In-app privacy screen.
4. Data Safety form.
5. Store listing without absolute claims.
6. Third-party sharing disclosures.

### Sprint 5 - Observability / Feedback

1. Log ruleId/source status/latency/conflicts.
2. Dashboard for FP/FN and UNKNOWN rate.
3. urlscan timeout/429 monitoring.
4. Web Risk match/no-match ratio.
5. VT fallback rate.
6. Review queue for official-vs-malicious conflicts and registry candidates.

## Open Decisions Before Code

1. Exact `SignalCode` enum names should align with existing Android code.
2. Whether backend and Android share policy through signed JSON ruleset or Kotlin code.
3. Exact VT license/API path for production.
4. Whether `DO_NOT_REPLY` should be a full MachineVerdict in Android UI now or mapped to existing status first.
5. First registry scope: recommended brands are ANAF, FAN, Posta Romana, eMAG, OLX, Revolut, BT, BCR, ING, Uber, Bolt, Glovo/Tazz.
6. urlscan Private availability/cost/limits.
7. Whether OCR happens local-only in v1 or can be sent to backend.

## Final Decision

This candidate is implementation-ready only after reconciliation with current code and tests.

Core law:

```text
EvidenceGate is the judge.
Every signal has provenance and cap.
RAG, marketing language, hidden links, raw feedback and no-match reputation cannot block alone.
Link truth + final domain + sensitive intent + hard reputation/sandbox decide the serious verdicts.
```
