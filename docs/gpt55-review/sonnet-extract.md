# Sonnet Intel Pipeline Notes - Extract Pentru Spec Final

Data: 2026-06-02

Sursa: `/Users/vaduvageorge/.codex/attachments/58bd306f-52f6-40de-b78f-3f8576a083b2/pasted-text.txt`

Scop: extragere filtrata din materialul Sonnet despre surse romanesti de threat intel, corpus si registry updates. Acesta NU este spec final si NU se implementeaza direct in scan flow v1.

## Verdict Pe Materialul Sonnet

Foarte util pentru etapa de threat-intel/corpus, nu pentru MVP-ul imediat de parser + EvidenceGate.

Ce merita pastrat:

- diferentierea intre surse lente/autoritare si surse rapide/noisy;
- pipeline separat: ingest -> extract -> cluster -> amplify -> emit;
- brand official warnings ca input puternic pentru registry si `neverAskFor`;
- brand official warning cu domenii false ca `CORPUS_CONFIRMED_BAD_DOMAIN`;
- Reddit ca semnal rapid, dar noisy si capped;
- ANCPD ca sursa istorica/autoritativa, nu live detection;
- ideea de `PhoneNumberCorpus` pentru scamuri fara URL;
- regula ca StatementParser ruleaza doar pe surse oficiale validate;
- ANAF ca brand/institutie speciala cu reguli mai stricte;
- output-ul pipeline-ului trebuie sa fie `EvidenceSignal` si registry update, nu verdict direct.

Ce trebuie amanat:

- scraping ANCPD/Reddit/brand RSS in MVP;
- crowd consensus ca hard evidence fara anti-abuz/manual review;
- sezonalitate ca policy din prima;
- auto-update registry fara semnatura si review;
- OCR pe screenshot-uri Reddit in prima faza.

## Insight Principal

Sursele au cicluri de viata diferite:

- ANCPD: lenta, autoritativa, buna pentru corpus istoric si validare legala;
- Reddit / comunitate: rapid, util pentru campanii active, dar noisy;
- avertismente oficiale de brand: cele mai valoroase pentru registry si reguli `neverAskFor`.

Nu le amestecam intr-un singur scor.

## Pipeline De Threat Intel Separat

Sonnet propune corect un pipeline separat de scan orchestrator:

```text
INGEST
-> EXTRACT
-> CLUSTER
-> AMPLIFY
-> EMIT
```

### Ingest

Surse candidate:

- ANCPD / decizii / comunicate relevante;
- Reddit / comunitati romanesti, dar doar ca semnal noisy;
- pagini oficiale brand: BCR, BT, FAN, eMAG, Revolut, ING, ANAF, Posta etc.;
- feed-uri DNSC/ANPC daca sunt disponibile.

### Extract

Module utile:

- `DecisionParser` pentru surse oficiale/ANCPD;
- `PostParser` pentru comunitate;
- `StatementParser` pentru avertismente oficiale de brand;
- OCR pe screenshot-uri doar in etapa viitoare.

### Cluster

Clustering util:

- acelasi domeniu in N surse intr-un interval scurt;
- template text similar dupa normalizare;
- campanie activa legata de brand + domeniu + template.

### Emit

Pipeline-ul emite doar:

- `EvidenceSignal`;
- `BrandRegistryEntry` update;
- `BrandIntelUpdate`;
- corpus entries versionate.

Nu emite verdict user-facing.

## Brand Official Warning Este Foarte Puternic

Regula de pastrat:

Daca brandul oficial numeste explicit un domeniu fals, acel domeniu poate deveni `CORPUS_CONFIRMED_BAD_DOMAIN` cu confidence mare si TTL.

Exemple:

- BCR spune "nu cerem niciodata PIN/SMS code" -> update in `neverAskFor`;
- eMAG spune "domeniile false sunt X/Y" -> `CORPUS_CONFIRMED_BAD_DOMAIN`;
- FAN spune "campanie activa in numele nostru" -> `activeCampaignFlag`;
- ANAF spune "nu trimitem SMS cu link" -> regula speciala pentru ANAF.

Regula de siguranta:

`StatementParser` ruleaza numai pe URL-uri care sunt deja in `officialDomains` ale brandului.

Motiv: altfel un atacator poate publica un "avertisment fals" si injecta date gresite in registry/corpus.

## BrandIntelUpdate - Model Util

Model candidat:

```kotlin
data class BrandIntelUpdate(
    val brandId: String,
    val sourceUrl: String,
    val sourceVerified: Boolean,
    val extractedAt: Instant,
    val confirmedBadDomains: List<String>,
    val neverAskForUpdates: Set<NeverAskFor>,
    val officialDomainsReconfirmed: Set<String>,
    val activeCampaignFlag: Boolean,
    val activeCampaignTtl: Duration = Duration.ofDays(7)
)
```

De completat in spec final:

- `sourceHash`;
- `parserVersion`;
- `reviewStatus`;
- `expiresAt`;
- `confidence`;
- `signedRegistryVersionProduced`.

## Amplification Rules - Cu Corectii

Ce e bun:

- brand official bad domain -> confirmed;
- ANCPD + Reddit mention -> mai puternic decat Reddit singur;
- Reddit 1 post -> single report;
- Reddit 3-9 -> similar/likely, nu dangerous;
- Reddit 10+ poate indica campanie, dar tot are nevoie de anti-abuz/review.

Corectie:

- `brandNamedItBad && redditCount >= 3 -> CONFIRMED_BAD_ACTIVE_CAMPAIGN` era unreachable daca prima regula intoarce deja `CONFIRMED_BAD_DOMAIN`; in spec final separăm `domain classification` de `active campaign flag`.

Reguli recomandate:

```text
Brand oficial numeste domeniul fals
-> CORPUS_CONFIRMED_BAD_DOMAIN, TTL 30 zile, confidence HIGH

Brand oficial anunta campanie fara domeniu
-> activeCampaignFlag pentru brand, TTL 7 zile

Reddit 1-2 postari
-> USER_SINGLE_REPORT / weak signal

Reddit 3-9 postari similare
-> CORPUS_SIMILAR_SCAM_TEMPLATE, capped VERIFY_OFFICIAL

Reddit 10+ postari + template consistent
-> active campaign candidate, needs review/anti-abuz

ANCPD + Reddit/domain match
-> confirmed historical/corpus, nu neaparat live active
```

## ANAF Ca Regula Speciala

Sonnet are dreptate ca ANAF merita tratament special.

Regula candidate:

- ANAF nu are tracking marketing obisnuit;
- ANAF nu trimite SMS-uri comerciale cu linkuri de plata;
- ANAF nu cere OTP/card/CVV prin SMS/email;
- claimed ANAF + domeniu neoficial + orice cerere de date/plata/login -> minim `NO_ENTER_DATA`, adesea `DO_NOT_CONTINUE`;
- claimed ANAF + domeniu necunoscut fara cerere de date -> `VERIFY_OFFICIAL`;
- `anaf.ro`, `mfinante.gov.ro` si canale oficiale validate trebuie in registry.

Atentie:

- nu spunem "orice altceva decat anaf.ro e automat scam" fara registry complet;
- spunem "nu putem valida ca oficial" si blocam actiunile sensibile.

## PhoneNumberCorpus - Bun Pentru NO_REPLY

Materialul observa corect ca multe scamuri romanesti nu au URL, ci numar de telefon sau cer raspuns cu cod/bani.

Idee de pastrat:

- `PhoneNumberCorpus` paralel cu URL/domain corpus;
- numere hash-uite/HMAC, nu stocate raw;
- TTL scurt;
- folosit ca semnal pentru `NO_REPLY`;
- nu produce `DO_NOT_CONTINUE` pentru link, pentru ca nu e link.

MVP:

- detectam cereri de OTP/bani/parola/CNP prin reply;
- `PhoneNumberCorpus` poate fi etapa 2.

## Sezonalitate - Util, Dar Amanat

Idee buna:

- ANAF spike martie-mai;
- curieri/eMAG/Posta spike Black Friday/Craciun.

Dar pentru MVP:

- nu introducem sezon ca factor de risc direct;
- putem folosi sezonalitatea doar pentru prioritizarea colectarii/corpusului;
- nu crestem verdictul doar pentru ca este sezon.

## Ce Nu Facem Cu Aceste Surse

Nu facem:

- nu marcam domeniu safe pentru ca nu apare in corpus;
- nu actualizam registry fara versionare si semnatura;
- nu luam Reddit ca hard evidence imediat;
- nu trimitem postari Reddit brute la RAG fara sanitizare;
- nu stocam PII din screenshot-uri/postari;
- nu lasam social media sa modifice official domains;
- nu combinam crowd data cu registry fara review.

## Cum Se Leaga De EvidenceGate

Output-ul pipeline-ului produce semnale deja definite:

| Input intel | Output |
| --- | --- |
| Brand naming bad domain | `CORPUS_CONFIRMED_BAD_DOMAIN`, HIGH |
| Reddit 10+ posts + review | `CORPUS_CONFIRMED_BAD_DOMAIN`, MEDIUM/HIGH |
| Reddit 3-9 posts | `CORPUS_SIMILAR_SCAM_TEMPLATE` |
| Reddit 1-2 posts | `USER_SINGLE_REPORT` |
| Reddit template match pe domeniu nou | `CORPUS_SIMILAR_SCAM_TEMPLATE` sau `VERIFY_OFFICIAL` context |
| Brand active campaign | amplifica sensitivity pentru brand mismatch |
| Brand neverAskFor update | registry rule, nu signal direct |
| ANCPD + Reddit/domain match | `CORPUS_CONFIRMED_BAD_DOMAIN`, historical/validated |

Scan flow nu trebuie sa stie de unde vine corpusul.

Scan flow intreaba `CorpusAdapter`, primeste `EvidenceSignal`, iar `EvidenceGate` decide.

## Ce Adaugam In Spec Final Din Sonnet

Adaugam:

- `BrandIntelUpdate`;
- `StatementParser` doar pe official domains;
- `activeCampaignFlag` cu TTL;
- `neverAskFor` ca parte din registry;
- `PhoneNumberCorpus` ca etapa viitoare pentru `NO_REPLY`;
- ANAF special policy;
- corpus/crowd signals capped pana la confirmare;
- no "absence from corpus means safe".

## Concluzie Pentru Sinteza Finala

Sonnet aduce partea buna de "cum invata sistemul despre Romania" fara sa transforme scanarea intr-un AI care ghiceste.

Principiul de pastrat:

`Threat intel pipeline-ul alimenteaza corpusul si registry-ul. EvidenceGate ramane singurul judecator.`

Pentru MVP, implementam mai intai Link Truth + Official Registry + Sensitive Intent + Provider checks. Threat-intel ingest romanesc vine dupa ce Gate-ul este stabil si testat.
