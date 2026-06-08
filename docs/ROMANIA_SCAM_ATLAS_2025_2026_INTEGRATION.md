# Romania Scam Atlas 2025-2026 Integration

Data: 2026-06-08

Status: document de integrare pentru materialele primite pe 2026-06-08:

- `/Users/vaduvageorge/Downloads/sigurscan_romania_scam_atlas_2025_2026.md`
- `/Users/vaduvageorge/Downloads/sigurscan_romania_scam_atlas_compact_2025_2026.json`
- `/Users/vaduvageorge/Downloads/sigurscan_romania_minor_scam_families_addendum_2025_2026.zip`
- `/Users/vaduvageorge/.codex/attachments/f5f02279-8fc7-491c-9265-9139cfbc0582/pasted-text.txt`

Acest document nu schimba codul. Scopul lui este sa stabileasca exact ce luam din atlas si cum il folosim fara sa stricam `DECISION_CONTRACT_V1.md`.

## Verdict scurt

Atlasul este valoros, dar nu trebuie folosit ca gate de verdict.

Ce luam:

- surse oficiale si confidence;
- official registry candidates;
- brand never-ask warnings;
- familii de scam pentru context/RAG;
- claim verifier targets;
- false-positive guards;
- acceptance tests Romania.

Ce nu luam:

- reguli textuale care pot seta direct `SIGUR`, `SUSPECT` sau `PERICULOS`;
- `urgent`, `cod`, `PIN`, `oferta`, `voucher`, `taxa` ca verdict signals brute;
- community/reddit/facebook ca hard evidence;
- `claim not found` ca `PERICULOS`.

## Aliniere cu Decision Contract

`docs/DECISION_CONTRACT_V1.md` ramane sursa de adevar.

Atlasul intra in pipeline doar asa:

```text
Atlas -> context + normalized evidence candidates + acceptance tests
Reducer -> singurul verdict final
```

Corpus/RAG similarity-only ramane maximum context si, cand este expus user-facing, maximum `SUSPECT`. Pentru `PERICULOS` este nevoie de dovezi tari normalizate:

- provider malicious;
- domeniu final lookalike/unrelated + cerere sensibila;
- cerere sensibila prin canal gresit;
- brand never-ask exact, canal-aware si asset-aware.

## Ce importam ca structuri

### 1. Source Index

Atlasul mare are un index de surse cu tip si confidence. Il folosim pentru provenance:

- `official_campaign`;
- `official_alert`;
- `official_brand_alert`;
- `official_brand_guidance`;
- `official_regulator_alert`;
- `official_domain_guidance`;
- `community_noisy`;
- `technical_standard`.

Regula:

```text
official_* si regulator_* pot sustine registry/warnings.
community_noisy poate sustine realism si teste, nu verdict hard.
```

### 2. Official Registry Updates

Importam ca registry candidate, nu whitelist absolut.

Branduri importante din atlas:

- ANAF / Ministerul Finantelor;
- DNSC;
- FAN Courier;
- Posta Romana;
- SAMEDAY;
- Cargus;
- OLX;
- eMAG / retail;
- Orange / YOXO;
- BT, ING, BCR, Raiffeisen, Revolut;
- Hidroelectrica;
- Ghiseul.ro;
- telecom/utilitati.

Regula:

```text
official_registry ajuta Identity:
official | delegated | lookalike | unrelated | unknown
```

Nu produce verdict direct.

Observatie FAN:

- atlasul confirma `fancourier.ro` si comunicarea oficiala FAN;
- pagina oficiala FAN are tracking AWB pe `fancourier.ro`;
- FAQ-ul FAN mentioneaza website-ul FAN, platforma `selfAWB.ro` si aplicatia FAN pentru AWB;
- `awb.fan.ro` trebuie tratat prin redirect-resolution si dovezi provider, nu ca whitelist absolut pana avem confirmare oficiala directa.

### 3. Brand Warnings / Never Ask For

Importam doar ca reguli canal-aware si asset-aware.

Exemple bune:

- FAN: nu cere parole, coduri WhatsApp/verificare, date card/CVC prin SMS.
- Posta Romana: nu cere date bancare/card/PIN sau plati online de taxe de livrare prin SMS-uri de tip phishing.
- SAMEDAY: nu cere plati prin SMS/social media.
- Bancile: nu cer PIN/parola/CVV/OTP prin telefon/SMS/e-mail/link.
- OLX: nu ceri card/CVV/sold ca sa primesti bani.
- Hidroelectrica: nu solicita investitii/date bancare prin reclame social/telefon.
- Ghiseul.ro: nu anunta obligatii de plata prin SMS/e-mail cu link.

Regula critica:

```text
Brand warning nu este regex textual.
Brand warning = claimed brand + asset exact + canal gresit + evidence normalizat.
```

Exemplu:

- `FAN + cod WhatsApp cerut in chat/reply` -> request sensitive `otp/whatsapp_code`, channel `whatsapp/reply`.
- `FAN + PIN de livrare/AWB pe domeniu oficial/delegat` -> request sensitive `none`.

### 4. Scam Families

Atlasul mare are 25 familii, iar textul scurt are 22 familii. Folosim varianta mare ca baza si pastram textul scurt ca rezumat operational.

Familiile intra in:

- `context.nearest_family`;
- `context.similarity`;
- `context.consistent`;
- explicatii user-friendly;
- acceptance tests.

Familiile nu intra direct in label.

### 5. Claim Verifier Targets

Importam targeturile ca tipuri de claim:

- `buyback_yoxo`;
- `campanie_emag_altex`;
- `tracking_curier`;
- `anaf_spv_notification`;
- `factura_utilitati`;
- `oferte_telecom`;
- `campanii_bancare_educationale`;
- `hidroelectrica_investment`.

Regula:

```text
Claim confirmed poate sustine SIGUR doar daca final URL identity + providers sunt clean.
Claim not found poate sustine SUSPECT, niciodata PERICULOS singur.
```

### 6. False-positive Guards

Acestea sunt foarte importante pentru produs:

- newsletter promo real cu tracking;
- link sub buton in email HTML;
- tracking curier legitim;
- OTP legitim pentru actiune initiata de user;
- facturi utilitati reale;
- campanii telecom/buyback reale;
- shortener/deeplink legitim;
- webmail shell only.

Le transformam in teste, nu in exceptii hard.

## Conflicte rezolvate

### `cod` si `PIN`

Atlasul contine multe cazuri unde `cod`/`PIN` sunt periculoase, dar si cazuri legitime de curier/locker.

Rezolvare:

```text
cod/PIN nu sunt sensibile prin ele insele.
Sunt sensibile doar daca sunt OTP/auth/banking/WhatsApp sau cerute pe canal gresit.
PIN livrare / PIN locker / AWB pe domeniu oficial/delegat = request.sensitive none.
```

### Urgenta si marketing

`urgent`, `azi`, `ultima sansa`, `weekendul acesta`, `oferta` sunt context, nu verdict.

```text
Marketing language + provider clean + final official/delegated = nu devine periculos.
Marketing language + unrelated/lookalike + card/CVV/login = periculos.
```

### Link sub buton

Linkul sub buton este normal in marketing.

```text
HTML_BUTTON_HIDDEN_LINK este tehnic util pentru extractie.
Nu este verdict signal fara mismatch/sensitive/provider risk.
```

### Community signals

Reddit/Facebook/presa pot ajuta realismul si testele.

```text
Nu devin hard evidence fara confirmare oficiala, provider hit sau request sensibil clar.
```

## Acceptance Tests de extras

Din atlasul mare trebuie generate teste pe minimum aceste clase:

- FAN oficial AWB/PIN pe domeniu oficial/delegat, providers clean -> `SIGUR`.
- FAN fake taxa/card/WhatsApp code pe domeniu neoficial -> `PERICULOS`.
- YOXO/Orange deeplink sau oferta oficiala, providers clean -> `SIGUR`.
- Newsletter eMAG/Altex real cu tracking si buton -> `SIGUR`.
- Retail giveaway fake cu domeniu neoficial + card/CVV/taxa -> `PERICULOS`.
- ANAF rambursare cu domeniu neoficial + card/CNP -> `PERICULOS`.
- Ghiseul.ro SMS amenda pe domeniu neoficial + card/login -> `PERICULOS`.
- OLX “ca sa primesti banii introdu card/CVV” -> `PERICULOS`.
- WhatsApp “trimite codul primit” -> `PERICULOS`.
- Telefon stricat fara cerere bani/date -> `SUSPECT`.
- Telefon stricat + transfer/voucher -> `PERICULOS`.
- Investment/Hidroelectrica profit garantat + remote access/depunere -> `PERICULOS`.
- Factura utilitati pe domeniu oficial/app si providers clean -> `SIGUR`.
- QR catre domeniu neoficial + card/login -> `PERICULOS`.
- URL/OCR incomplet fara target tehnic -> `PENDING` daca scanarea inca poate continua, altfel `SUSPECT` doar ca rezultat final inconcludent.

## Ce a fost produs din atlas

Atlasul compact JSON a fost importat in sursa runtime Android si apoi regenerat in backend prin `backend/tools/build_runtime_knowledge.py`.
Addendum-ul cu familii mici a fost importat ulterior ca material `scenario_corpus`, `signal_mapping`, `acceptance_tests` si `sources`.

Canonizari aplicate la import:

- `mfinante` -> `ministerul_finantelor`;
- `orange` -> `orange_yoxo`;
- `ppc_eon` -> split controlat in `ppc` si `eon`;
- domeniile `www.*` au fost normalizate la registrable host fara `www`;
- `brand_warnings` duplicate au fost unite pe `brand_id`, iar `never_ask_for` este pastrat ca dictionar asset-aware.

Fisiere normalizate existente:

- `backend/data/knowledge/official_registry_v2026_06_08.json`
- `backend/data/knowledge/brand_warnings_v2026_06_08.json`
- `backend/data/knowledge/romania_scam_families_v2026_06_08.json`
- `backend/data/knowledge/claim_verifier_targets_v2026_06_08.json`
- `backend/data/eval/romania_decision_contract_eval_v2026_06_08.jsonl`

Dimensiune dupa merge:

- 23 registry entries canonice in Android source;
- 18 brand warnings canonice in Android source;
- 63 familii de scam in corpus;
- 16 claim verifier targets;
- 8 false-positive guards;
- 115 signal mappings;
- 59 surse indexate;
- 433 fixture-uri de contract.

Familii mici adaugate din addendum:

- QR fals pe parcometre / plata parcare;
- amenzi false / Ghiseul.ro / autoritati rutiere;
- rovinieta / taxa drum falsa prin SMS;
- OSIM / taxe marca inregistrata false;
- phishing pentru ownership pagini social media;
- dispozitiv blocat / amenda falsa DNSC/Politie;
- bilete false evenimente;
- vacante/cazari false;
- chirii/Airbnb/student sublet;
- task/job scam;
- romance scam;
- caritate/adapost animale fals;
- pet adoption transport fee;
- mystery box / giveaway;
- deepfake investitii cu persoane publice;
- B2B invoice/payment change;
- sextortion;
- documente false instanta/Politie/Europol.

Aceste fisiere sunt input pentru normalizare si teste. Reducerul pur ramane singura autoritate de verdict.

## Decizie de produs

Atlasul ne ajuta mult, dar numai daca il folosim disciplinat:

```text
Atlasul stie cum arata scamurile.
Providerii si resolverul arata unde duce linkul.
Request classifier spune ce cere mesajul si pe ce canal.
Reducerul decide.
```

Nu mai folosim atlasul ca sperietoare textuala.

## Research supplement

Familiile mici cercetate pe 2026-06-08 sunt documentate in:

- `docs/SMALL_SCAM_FAMILIES_RESEARCH_2026_06_08.md`

Ele trebuie importate ca atlas supplement si acceptance tests, nu ca reguli directe de verdict.
