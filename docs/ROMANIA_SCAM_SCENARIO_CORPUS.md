# Romania Scam Scenario Corpus

Data: 2026-06-02

Status: candidate corpus pentru EvidenceGate. Nu este RAG si nu este verdict direct. Este taxonomie determinista pentru scamuri romanesti, folosita ca semnale de scenariu in `EvidenceGate`.

## Surse Verificate

Surse oficiale / semi-oficiale relevante:

- SigurantaOnline - campania `Uniti impotriva escrocheriilor`: https://sigurantaonline.ro/uniti-impotriva-escrocheriilor/
- SigurantaOnline - lansare campanie Politia Romana / DNSC / ARB / Mastercard: https://sigurantaonline.ro/politia-romana-dnsc-arb-si-mastercard-lanseaza-campania-nationala-uniti-impotriva-escrocheriilor/
- FAN Courier - tentativa de phishing prin SMS: https://www.fancourier.ro/atentie-tentativa-de-phishing-prin-sms/
- FAN Courier - alerta de smishing: https://www.fancourier.ro/alerta-de-smishing/
- DNSC via Digi24 - `Voteaza pe Adeline` / WhatsApp takeover: https://www.digi24.ro/stiri/actualitate/vot-pentru-adeline-o-noua-tentativa-de-frauda-ce-vizeaza-conturile-de-whatsapp-ale-utilizatorilor-romani-3083411

Observatie: Reddit/comunitatile sunt utile pentru spețe si acceptance tests, dar nu sunt sursa autoritativa de verdict.

## De Ce Avem Nevoie De Asta

Pipeline-ul `Link Truth` prinde phishing-ul bazat pe URL: brand pretins, final URL, domeniu oficial, formular sensibil.

Romania are insa multe scamuri fara URL sau cu URL secundar:

- telefon stricat;
- accidentul / nepotul la ananghie;
- WhatsApp takeover;
- BNR / politie / cont sigur;
- credit fraudulos;
- investitii false;
- marketplace / "ca sa primesti banii";
- colet / locker / taxa livrare;
- loterie / bonus / casino app.

Acestea trebuie detectate ca scenarii, nu ca RAG liber.

## Familii Oficiale De Scenarii

SigurantaOnline grupeaza scenariile in 3 familii mari:

| Familie | Scenarii |
| --- | --- |
| `URGENCY_BIG` | Nepotul la ananghie, Accidentul, Imprumutul, WhatsApp, Telefon stricat, Petitia |
| `OFFICIAL_PHONE` | Creditul, Coletul, BNR, Legitimatia |
| `OVERNIGHT_GAIN` | Hidroelectrica, Broker, Cripto, Aplicatia bancara, Marketplace, Investitii cu AI, Loteria Romana |

In SigurScan extindem cu subfamilii operationale:

- `DELIVERY_PHISHING`;
- `ACCOUNT_TAKEOVER`;
- `MARKETPLACE_ESCROW`;
- `REMOTE_ACCESS_INVESTMENT`;
- `TEXT_ONLY_FAMILY_SCAM`.

## Model De Date

```kotlin
enum class ScamScenarioFamily {
    URGENCY_BIG,
    OFFICIAL_PHONE,
    OVERNIGHT_GAIN,
    DELIVERY_PHISHING,
    ACCOUNT_TAKEOVER,
    MARKETPLACE_ESCROW,
    TEXT_ONLY_FAMILY_SCAM,
    UNKNOWN
}

enum class ScamScenarioKind {
    FAMILY_NEW_PHONE,
    FAMILY_EMERGENCY_MONEY,
    ACCIDENT_OR_NEPHEW_AI_VOICE,
    WHATSAPP_TAKEOVER_VOTE,
    WHATSAPP_TAKEOVER_PETITION,
    COURIER_LOCKER_OR_ADDRESS_UPDATE,
    BNR_SAFE_ACCOUNT,
    FAKE_CREDIT_AUTHORITY_CHAIN,
    HIDROELECTRICA_INVESTMENT,
    CRYPTO_BROKER_INVESTMENT,
    MARKETPLACE_RECEIVE_MONEY,
    LOTTERY_BONUS_DEPOSIT,
    REMOTE_ACCESS_APP_INSTALL,
    APK_OR_SIDELOAD
}

enum class CorpusReliability {
    OFFICIAL_CAMPAIGN,
    BRAND_OFFICIAL,
    AUTHORITY_WARNING,
    CURATED_MEDIA_REPORT,
    CURATED_REDDIT_CASE,
    USER_REPORT_UNVERIFIED
}

enum class RequestedAsset {
    MONEY_TRANSFER,
    CARD_DATA,
    CVV,
    OTP_CODE,
    WHATSAPP_CODE,
    BANK_LOGIN,
    PERSONAL_DATA,
    CNP,
    IBAN,
    REMOTE_ACCESS,
    APK_INSTALL,
    CRYPTO_ATM_DEPOSIT,
    QR_PAYMENT
}

enum class ImpersonatedRole {
    CHILD,
    NEPHEW,
    FAMILY_MEMBER,
    BANK,
    POLICE,
    BNR,
    ANAF,
    COURIER,
    BROKER,
    MARKETPLACE_BUYER,
    LOTTERY,
    PUBLIC_COMPANY
}

data class ScenarioEvidence(
    val scenarioFamily: ScamScenarioFamily,
    val scenarioKind: ScamScenarioKind,
    val reliability: CorpusReliability,
    val matchedPhrases: List<String>,
    val requestedAssets: Set<RequestedAsset>,
    val impersonatedRole: ImpersonatedRole?,
    val maxDecisionIfTextOnly: MachineVerdict
)
```

## Noi SignalCode / SignalKind Necesare

Pentru Gate-ul nou, adaugam aceste semnale in familia `STRUCTURAL` / `TEXT_KEYWORD` / `CORPUS`, dupa caz:

```kotlin
enum class ScenarioSignalCode {
    FAMILY_NEW_NUMBER_CLAIM,
    FAMILY_PHONE_BROKEN_CLAIM,
    FAMILY_EMERGENCY_CLAIM,
    FAMILY_MONEY_REQUEST,
    TRANSFER_TO_FRIEND_ACCOUNT,
    AVOIDS_VOICE_VERIFICATION,

    WHATSAPP_VERIFICATION_CODE_REQUEST,
    WHATSAPP_DEVICE_LINKING_REQUEST,
    VOTE_CONTEST_HOOK,
    PETITION_HOOK,

    DELIVERY_LOCKER_SELECTION_REQUEST,
    DELIVERY_ADDRESS_UPDATE_REQUEST,
    DELIVERY_SMALL_FEE_REQUEST,
    AWB_MISMATCH,

    OFFICIAL_AUTHORITY_CHAIN,
    FRAUDULENT_CREDIT_CLAIM,
    SAFE_ACCOUNT_TRANSFER_REQUEST,
    FAKE_LEGITIMATION_DOCUMENT,
    CONFIDENTIALITY_PRESSURE,

    INVESTMENT_FAST_GAIN_PROMISE,
    PUBLIC_COMPANY_INVESTMENT_IMPERSONATION,
    WITHDRAWAL_TAX_REQUEST,
    REMOTE_ACCESS_APP_REQUEST,
    CRYPTO_ATM_QR_REQUEST,

    MARKETPLACE_RECEIVE_MONEY_LINK,
    CARD_REQUIRED_TO_RECEIVE_MONEY,

    LOTTERY_BONUS_DEPOSIT_REQUEST
}
```

## Reguli De Decizie

### Text-Only Scenarios

Aceste scenarii pot produce `DO_NOT_REPLY` sau `NO_ENTER_DATA`, dar nu `DANGEROUS` fara URL/contact/corpus confirmat.

```kotlin
fun scenarioTextOnlyDecision(s: ScenarioEvidence): MachineVerdict {
    return when (s.scenarioKind) {
        ScamScenarioKind.FAMILY_NEW_PHONE,
        ScamScenarioKind.FAMILY_EMERGENCY_MONEY,
        ScamScenarioKind.ACCIDENT_OR_NEPHEW_AI_VOICE,
        ScamScenarioKind.BNR_SAFE_ACCOUNT,
        ScamScenarioKind.FAKE_CREDIT_AUTHORITY_CHAIN -> MachineVerdict.DO_NOT_REPLY

        ScamScenarioKind.WHATSAPP_TAKEOVER_VOTE,
        ScamScenarioKind.WHATSAPP_TAKEOVER_PETITION -> {
            if (RequestedAsset.WHATSAPP_CODE in s.requestedAssets) {
                MachineVerdict.DO_NOT_REPLY
            } else {
                MachineVerdict.VERIFY_OFFICIAL
            }
        }

        ScamScenarioKind.MARKETPLACE_RECEIVE_MONEY -> {
            if (
                RequestedAsset.CARD_DATA in s.requestedAssets ||
                RequestedAsset.OTP_CODE in s.requestedAssets
            ) {
                MachineVerdict.NO_ENTER_DATA
            } else {
                MachineVerdict.VERIFY_OFFICIAL
            }
        }

        ScamScenarioKind.HIDROELECTRICA_INVESTMENT,
        ScamScenarioKind.CRYPTO_BROKER_INVESTMENT -> {
            if (
                RequestedAsset.REMOTE_ACCESS in s.requestedAssets ||
                RequestedAsset.APK_INSTALL in s.requestedAssets
            ) {
                MachineVerdict.DANGEROUS
            } else {
                MachineVerdict.NO_ENTER_DATA
            }
        }

        else -> MachineVerdict.VERIFY_OFFICIAL
    }
}
```

### URL + Scenario Combo

```kotlin
fun scenarioUrlDecision(
    scenario: ScenarioEvidence,
    hasUnofficialDomain: Boolean,
    hasSensitiveForm: Boolean,
    hasDangerousReputation: Boolean,
    hasSandboxPhishing: Boolean
): MachineVerdict {
    if (hasDangerousReputation || hasSandboxPhishing) {
        return MachineVerdict.DANGEROUS
    }

    if (hasUnofficialDomain && hasSensitiveForm) {
        return MachineVerdict.DANGEROUS
    }

    if (
        hasUnofficialDomain &&
        scenario.requestedAssets.any {
            it in setOf(
                RequestedAsset.CARD_DATA,
                RequestedAsset.CVV,
                RequestedAsset.OTP_CODE,
                RequestedAsset.WHATSAPP_CODE,
                RequestedAsset.BANK_LOGIN,
                RequestedAsset.REMOTE_ACCESS,
                RequestedAsset.APK_INSTALL
            )
        }
    ) {
        return MachineVerdict.DANGEROUS
    }

    if (hasUnofficialDomain) {
        return MachineVerdict.VERIFY_OFFICIAL
    }

    return scenario.maxDecisionIfTextOnly
}
```

## Scenarii Concrete

### Familia / Telefon Stricat / Nepotul La Ananghie

Semnale:

- `FAMILY_NEW_NUMBER_CLAIM`;
- `FAMILY_PHONE_BROKEN_CLAIM`;
- `FAMILY_EMERGENCY_CLAIM`;
- `FAMILY_MONEY_REQUEST`;
- `TRANSFER_TO_FRIEND_ACCOUNT`;
- `AVOIDS_VOICE_VERIFICATION`.

Regula:

```text
IF pretinde ruda/copil/nepot
AND telefon stricat / numar nou / accident / jefuit / spital
AND cere bani/transfer
THEN DO_NOT_REPLY
```

User copy:

`Nu raspunde. Suna persoana pe numarul vechi din agenda ta. Cere parola familiei.`

### WhatsApp Takeover

Semnale:

- `VOTE_CONTEST_HOOK`;
- `PETITION_HOOK`;
- `WHATSAPP_VERIFICATION_CODE_REQUEST`;
- `WHATSAPP_DEVICE_LINKING_REQUEST`.

Reguli:

```text
IF mesaj cere cod WhatsApp / cod de verificare / asociere dispozitiv
THEN DO_NOT_REPLY

IF link + pagina cere telefon + cod WhatsApp
THEN DO_NOT_CONTINUE
```

User copy:

`Nu introduce codul WhatsApp. Cine iti cere codul iti poate prelua contul.`

### Curier / Colet / Locker / Taxa

Semnale:

- `DELIVERY_LOCKER_SELECTION_REQUEST`;
- `DELIVERY_ADDRESS_UPDATE_REQUEST`;
- `DELIVERY_SMALL_FEE_REQUEST`;
- `AWB_MISMATCH`;
- courier brand claim.

Reguli:

```text
IF brand curier
AND locker/adresa/colet blocat/taxa
AND domeniu neoficial
AND cere card/CVV/OTP/WhatsApp code
THEN DO_NOT_CONTINUE

IF brand curier
AND domeniu neoficial
AND fara cerere date
THEN VERIFY_OFFICIAL

IF domeniu oficial curier
AND fara card/OTP/parola
THEN CONTINUE_WITH_CAUTION
```

Nota critica:

`Tocmai asteptam colet` nu este semnal de safe. Este context neutru.

### BNR / Banca / Politie / Cont Sigur

Semnale:

- `OFFICIAL_AUTHORITY_CHAIN`;
- `FRAUDULENT_CREDIT_CLAIM`;
- `SAFE_ACCOUNT_TRANSFER_REQUEST`;
- `FAKE_LEGITIMATION_DOCUMENT`;
- `CONFIDENTIALITY_PRESSURE`;
- `CRYPTO_ATM_QR_REQUEST`.

Reguli:

```text
IF banca/politie/BNR/ANAF
AND credit fraudulos / cont compromis / cont sigur
AND cere transfer bani / date banking / instalare aplicatie
THEN DO_NOT_REPLY

IF official authority claim
AND domeniu neoficial
AND cere date bancare/autentificare/card
THEN DO_NOT_CONTINUE
```

User copy:

`Nu continua conversatia. Banca, BNR sau Politia nu iti cer sa muti banii intr-un cont sigur. Suna institutia pe canalul oficial.`

### Investitii False / Hidroelectrica / Broker / Cripto

Semnale:

- `INVESTMENT_FAST_GAIN_PROMISE`;
- `PUBLIC_COMPANY_INVESTMENT_IMPERSONATION`;
- `WITHDRAWAL_TAX_REQUEST`;
- `REMOTE_ACCESS_APP_REQUEST`;
- `CRYPTO_ATM_QR_REQUEST`;
- `APK_OR_SIDELOAD`.

Reguli:

```text
IF investitie/castig rapid
AND brand public cunoscut / Hidroelectrica / broker / cripto
AND cere card/date personale/transfer
THEN NO_ENTER_DATA

IF investment hook
AND cere AnyDesk/TeamViewer/RDP/aplicatie control
THEN DO_NOT_CONTINUE

IF investment hook
AND APK / sideload / aplicatie din afara Play Store
THEN DO_NOT_CONTINUE
```

### Marketplace / OLX-Style / Primeste Banii

Semnale:

- `MARKETPLACE_RECEIVE_MONEY_LINK`;
- `CARD_REQUIRED_TO_RECEIVE_MONEY`;
- `SMS_CODE_TO_RECEIVE_PAYMENT`.

Reguli:

```text
IF marketplace / vanzare / cumparator
AND "ca sa primesti banii"
AND cere card/cod SMS
THEN NO_ENTER_DATA

IF link catre domeniu neoficial + formular card
THEN DO_NOT_CONTINUE
```

User copy:

`Nu ai nevoie sa introduci cardul ca sa primesti bani.`

## Cum Folosim Reddit / Comunitati

Reddit si comunitatile sunt bune pentru:

- pattern discovery;
- exemple reale;
- acceptance tests;
- UX copy;
- detectarea campaniilor active inainte de surse oficiale.

Nu sunt bune pentru:

- hard block singure;
- registry updates automate;
- domenii safe/unsafe fara verificare;
- raw data trimisa la RAG.

Regula:

```text
CURATED_REDDIT_CASE -> max VERIFY_OFFICIAL / DO_NOT_REPLY / NO_ENTER_DATA
DO_NOT_CONTINUE doar cu URL/domain/contact confirmat de sandbox/reputation/corpus oficial.
```

## Acceptance Tests Noi

### Senior / Familie / WhatsApp

| ID | Caz | Expected |
| --- | --- | --- |
| S1 | `Mama, mi s-a stricat telefonul, salveaza numarul asta nou` + cere bani | `DO_NOT_REPLY` |
| S2 | `Bunico, am avut accident, am nevoie urgent de bani` | `DO_NOT_REPLY` |
| S3 | `Sunt nepotul, am fost jefuit, trimite bani la prietenul meu` | `DO_NOT_REPLY` |
| S4 | Contact WhatsApp cere urgent 1800 lei | `DO_NOT_REPLY` |
| S5 | `Voteaza pe Adeline` + link + cere cod WhatsApp | `DANGEROUS` |
| S6 | `Semneaza petitia` + cere cod WhatsApp | `DANGEROUS` |
| S7 | Mesaj cere `codul primit prin SMS` fara URL | `DO_NOT_REPLY` |

### Curier / Colet

| ID | Caz | Expected |
| --- | --- | --- |
| C1 | FANBOX / locker + domeniu neoficial fara date | `VERIFY_OFFICIAL` |
| C2 | FANBOX + domeniu neoficial + card/CVV | `DANGEROUS` |
| C3 | FAN real `fancourier.ro` tracking fara card | `CONTINUE_WITH_CAUTION` |
| C4 | Context real eMAG + SMS FAN fals + card form | `DANGEROUS` |
| C5 | Posta Romana + taxa livrare + domeniu neoficial + card | `DANGEROUS` |

### Telefon Oficial / BNR / Credit

| ID | Caz | Expected |
| --- | --- | --- |
| B1 | `Sunt de la banca, s-a facut credit pe numele tau` | `DO_NOT_REPLY` |
| B2 | Politie/BNR + `cont sigur` | `DO_NOT_REPLY` |
| B3 | Documente WhatsApp + legitimatie falsa + date bancare | `NO_ENTER_DATA` |
| B4 | Cere credit si depunere la crypto ATM cu QR | `DO_NOT_REPLY` |
| B5 | Formular BNR neoficial + date card | `DANGEROUS` |

### Investitii / Marketplace / Loterie

| ID | Caz | Expected |
| --- | --- | --- |
| I1 | Hidroelectrica investitii + castig garantat + formular date | `NO_ENTER_DATA` |
| I2 | Broker/cripto + cere AnyDesk | `DANGEROUS` |
| I3 | APK trading app / sideload | `DANGEROUS` |
| M1 | OLX/marketplace: link ca sa primesti banii + card | `DANGEROUS` |
| M2 | Trimite datele cardului ca sa-ti platesc produsul | `NO_ENTER_DATA` |
| L1 | Loteria Romana bonus + depune bani in casino app | `NO_ENTER_DATA` |

## Integrare In EvidenceGate

Adaugam regula noua in ordinea Gate:

```text
G32 official Romanian scenario + URL + sensitive destination -> DANGEROUS / NO_ENTER_DATA
G35 text-only/direct-message Romanian scenario -> DO_NOT_REPLY / NO_ENTER_DATA
```

Ordine recomandata:

```text
G00 no analyzable artifact -> UNKNOWN
G10 hard malicious evidence -> DANGEROUS
G20 APK / remote access / sideload compound -> DANGEROUS
G30 brand impersonation + unofficial/lookalike domain + secret collection -> DANGEROUS
G32 Romanian scenario with URL + sensitive/unofficial destination -> DANGEROUS / NO_ENTER_DATA
G35 text-only/direct-message Romanian scenario -> DO_NOT_REPLY / NO_ENTER_DATA
G40 secret collection on untrusted/unofficial domain -> NO_ENTER_DATA
...
```

## Verdict Final

Romanian Scam Scenario Corpus este necesar.

Fara el, SigurScan prinde bine URL phishing, dar rateaza exact scamurile care lovesc oameni reali in Romania:

- bunici;
- parinti;
- vanzatori pe marketplace;
- oameni cu cont bancar;
- oameni care asteapta colet;
- oameni atrasi de investitii rapide.

Principiul:

```text
Link Truth ramane nucleul.
Romanian Scam Scenario Corpus acopera scamurile sociale fara URL sau cu URL secundar.
EvidenceGate ramane singurul judecator.
```
