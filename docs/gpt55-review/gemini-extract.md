# Gemini EvidenceGate Notes - Extract Pentru Spec Final

Data: 2026-06-02

Sursa: `/Users/vaduvageorge/.codex/attachments/bf665528-6428-401a-b502-124c1b8a2e6d/pasted-text.txt`

Scop: extragere filtrata din completarea propusa de Gemini. Acesta NU este spec final si NU se implementeaza copy-paste. Materialul este util ca lista de functii lipsa, dar are cateva riscuri de logica.

## Verdict Pe Materialul Gemini

Util pentru:

- lista concreta de functii utilitare care lipseau;
- ideea de execution trace determinist;
- helperi pentru `recommendedActions()`, `buildPath()`, `defaultReason()`;
- `detectConflicts()` ca punct de plecare;
- `OfficialContext.from()` ca reminder ca trebuie definit contextul oficial;
- separarea surselor externe vs locale.

Nu este suficient pentru implementare directa.

Probleme importante:

- `isContinueWithCaution()` este prea permisiv;
- default-ul final spre `CONTINUE_WITH_CAUTION` este periculos;
- `OfficialContext` este prea sarac si nu include `registryStatus`, brand, domain, mismatch reasons;
- conflict detection acopera doar 2 conflicte, mult prea putin;
- `safeMarketing` bazat pe `activeSignals.none { strength >= MEDIUM }` poate rata semnale relevante;
- `targetHash = normalizedUrl.hashCode().toString()` nu este acceptabil pentru privacy/audit; trebuie HMAC/hash stabil, nu `hashCode()`;
- `recommendedForDangerous()` adauga prea putine actiuni;
- afirmatia "protectie totala" trebuie eliminata din orice document/store copy.

## Ce Pastram Ca Lista De Functii Obligatorii

Gemini confirma ca spec-ul final trebuie sa defineasca explicit:

- `shouldReturnInsufficient()`;
- `isContinueWithCaution()`;
- `detectConflicts()`;
- `suppressedByDanger()`;
- `recommendedForDangerous()`;
- `recommendedActions()`;
- `buildPath()`;
- `defaultReason()`;
- `OfficialContext.from()`;
- `externalSources`;
- `localSources`.

Aceste functii trebuie sa aiba contracte si teste. Nu le lasam ca pseudocod vag.

## shouldReturnInsufficient - Ce Pastram

Logica buna:

- fara primary URL + fara text riscant -> `INSUFFICIENT_EVIDENCE`;
- cloud disabled / privacy skipped + only weak signals -> `INSUFFICIENT_EVIDENCE`;
- all remote failed + no strong local -> `INSUFFICIENT_EVIDENCE`.

Corectii pentru spec final:

- daca exista `NO_REPLY` risk, nu returnam insufficient doar pentru ca nu exista URL;
- OCR slab trebuie inclus explicit;
- webmail shell only trebuie inclus explicit;
- privacy skipped din cauza token/magic link trebuie sa produca local-only verdict sau insufficient, niciodata safe.

## isContinueWithCaution - Nu Folosim Copy-Paste

Problema Gemini:

```kotlin
val hasBlockers = signals.any {
    it.strength >= SignalStrength.HIGH || it.canEscalateToDangerous
}
if (hasBlockers) return false

if (official.isExactOfficial || official.isOfficialPartner) {
    return true
}
```

De ce e insuficient:

- official exact/partner nu inseamna safe daca exista Web Risk/urlscan/VT malicious;
- `strength >= HIGH` nu este singurul blocker;
- `canEscalateToDangerous` poate fi false pentru structural important;
- nu verifica `registryStatus`;
- nu verifica final URL cunoscut;
- nu verifica daca registry este stale/invalid;
- nu verifica daca scanarea este finala sau provizorie.

Regula corecta pentru `CONTINUE_WITH_CAUTION`:

- registry valid;
- final URL cunoscut;
- official exact/partner/tracking valid;
- fara sensitive ask;
- fara structural high/critical;
- fara reputation/sandbox/corpus exact dangerous;
- daca sandbox este required si pending, verdictul este provisional sau `VERIFY_OFFICIAL`, nu caution final;
- Web Risk no-match singur nu este suficient.

## detectConflicts - Ce Pastram Si Ce Lipseste

Gemini acopera:

- Web Risk clean + urlscan malicious;
- official match + reputation hit.

Trebuie extins cu:

- urlscan clean + structural card/login/OTP form;
- official exact + VT low/stale hit;
- old cache clean + fresh sandbox malicious;
- final URL differs from displayed/claimed brand;
- user feedback conflicts with technical evidence;
- registry stale/invalid conflicts;
- Web Risk no-match + VT high malicious;
- URL shortener final official vs final unknown.

Regula:

`detectConflicts()` nu decide verdict singur. Produce `EvidenceConflict`, iar Gate aplica precedenta.

## OfficialContext - Gemini E Prea Subtire

Gemini propune:

```kotlin
private data class OfficialContext(
    val isExactOfficial: Boolean,
    val isOfficialPartner: Boolean,
    val isOfficialTrackingDomain: Boolean,
    val isSafeMarketingContext: Boolean
)
```

Pentru noi, asta nu ajunge.

Spec final trebuie sa includa:

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
    val finalRegisteredDomain: String?,
    val mismatchReasons: List<String>
)
```

`isSafeMarketingContext` trebuie sa fie true doar cand:

- registry este valid;
- brand/context coerent;
- final URL este oficial/partner/tracking permis;
- nu exista sensitive ask;
- nu exista reputatie/sandbox dangerous;
- nu exista form/card/login/OTP pe domeniu neoficial;
- nu exista registry stale/invalid.

## recommendedActions - Ce Pastram

Bun:

- `DO_NOT_CONTINUE` -> `DO_NOT_OPEN`;
- `NO_ENTER_DATA` -> `DO_NOT_ENTER_CARD` / `DO_NOT_ENTER_PASSWORD` / `VERIFY_IN_OFFICIAL_APP`;
- `NO_REPLY` -> `DO_NOT_REPLY_WITH_CODE` / `CALL_OFFICIAL_CHANNEL`;
- `VERIFY_OFFICIAL` -> `VERIFY_IN_OFFICIAL_APP` / `CALL_OFFICIAL_CHANNEL`;
- `CONTINUE_WITH_CAUTION` -> `CONTINUE_MANUALLY_WITH_CAUTION`.

De completat:

- daca exista `FORM_OTP_DETECTED` sau `OTP_REQUEST`, adauga `DO_NOT_REPLY_WITH_CODE`;
- daca exista APK/remote access, adauga actiune: `DO_NOT_INSTALL_APP`;
- daca exista payment/bank transfer, adauga `DO_NOT_TRANSFER_MONEY`;
- daca exista insufficient evidence, actiunea principala este `VERIFY_IN_OFFICIAL_APP`, nu doar `CALL_OFFICIAL_CHANNEL`;
- `REPORT_TO_COMMUNITY` este optional si nu trebuie sa fie prima actiune pentru user normal.

## buildPath - Ce Pastram

Bun:

- path trace deterministic;
- include policy path;
- include signal kinds si conflicts resolved.

Corectii:

- nu logam URL brut;
- includem `policyVersion`;
- includem `registryVersion`;
- includem `sourceStates`;
- includem doar signal ids / hashes / summaries safe;
- path-ul este pentru audit intern, nu UI.

## Execution Trace Determinist - De Pastrat

Gemini are o idee buna:

```text
EvidenceSnapshot
-> Filtrare semnale expirate / RAG
-> Sortare stricta
-> Evaluare conflicte
-> Ierarhie gated
-> GateResult
```

Pastram ordinea:

1. elimina semnale expirate si RAG decision-ineligible;
2. sorteaza stabil dupa provenance/source/kind/id;
3. construieste `OfficialContext`;
4. detecteaza conflicte;
5. cauta `DO_NOT_CONTINUE`;
6. cauta `NO_REPLY`;
7. cauta `NO_ENTER_DATA`;
8. evalueaza `INSUFFICIENT_EVIDENCE`;
9. cauta `VERIFY_OFFICIAL`;
10. evalueaza strict `CONTINUE_WITH_CAUTION`;
11. default final: `INSUFFICIENT_EVIDENCE`, nu `CONTINUE_WITH_CAUTION`.

Corectie majora:

- Gemini pune default `CONTINUE_WITH_CAUTION`. Noi nu folosim asta.
- Default sigur este `INSUFFICIENT_EVIDENCE`.

## Default Reason - Ce Pastram

Mesaje utile, dar de rescris mai simplu pentru user roman non-tehnic:

- `DO_NOT_CONTINUE`: "Acest link are semnale clare de risc."
- `NO_ENTER_DATA`: "Pagina cere date sensibile si nu putem confirma ca este oficiala."
- `NO_REPLY`: "Mesajul cere coduri, bani sau date pe care nu trebuie sa le trimiti prin raspuns."
- `VERIFY_OFFICIAL`: "Nu putem confirma identitatea expeditorului sau destinatia."
- `CONTINUE_WITH_CAUTION`: "Nu am gasit semnale clare de frauda, dar verifica in continuare cu atentie."
- `INSUFFICIENT_EVIDENCE`: "Nu avem destule informatii ca sa verificam corect."

Nu folosim formulari absolute:

- "garanteaza";
- "protectie totala";
- "100% sigur";
- "amenintari confirmate" daca sursa este doar soft evidence.

## Ce Nu Folosim Din Gemini

Nu folosim:

- `default -> CONTINUE_WITH_CAUTION`;
- `hashCode()` pentru target hash;
- `OfficialContext` fara registry status;
- `isContinueWithCaution()` bazat doar pe official exact/partner;
- conflict detection minimal ca implementare finala;
- "motor 100% determinist" in copy user-facing;
- "protectie totala" sau "garantie" in orice document public;
- source state success ca dovada de clean fara semnale negative explicite;
- `REPORT_TO_COMMUNITY` ca actiune default pentru orice dangerous.

## Concluzie Pentru Sinteza Finala

Gemini este util ca lista de helperi si execution trace, dar nu ca policy finala.

Cel mai valoros lucru extras:

`EvidenceGate` trebuie sa aiba functii mici, testabile, cu default conservator.

Corectia brutal de importanta:

Default-ul nu este `Poti continua cu prudenta`. Default-ul este `Nu pot verifica suficient`.
