# GPT 5.5 Pro Response 3 Of 3 - Extract Pentru Spec Final

Data: 2026-06-02

Sursa: `/Users/vaduvageorge/.codex/attachments/0d741b1d-2a65-410b-a2d7-9d35d8a42ac8/pasted-text.txt`

Scop: extragere filtrata din raspunsul 3/3. Acesta NU inlocuieste `docs/LAUNCH_ARCHITECTURE_FINAL.md`; doar noteaza completarile utile.

## Verdict Pe 3/3

Nu schimba arhitectura.

Ce aduce valoros:

- decizia trebuie facuta pe `finalUrl` cand exista, nu pe primul hop;
- orice verdict calculat pe `primaryUrl` trebuie reevaluat cand apare `finalUrl`;
- Web Risk trebuie sa includa si `SOCIAL_ENGINEERING_EXTENDED_COVERAGE` daca este disponibil si contractual permis;
- urlscan trebuie sa fie `private` by default; `public` este interzis pentru URL-uri de user;
- `unlisted` este mai bun decat public, dar tot poate fi vizibil pentru cercetatori/pro customers, deci nu este default pentru date user sensibile;
- VirusTotal Public API nu este pentru produs comercial; in productie: Premium/Private Scanning sau eliminat din v1;
- preferam Google Code Scanner / Document Scanner / system picker pentru a evita `CAMERA` si storage broad unde se poate;
- update-urile async trebuie sa fie monotone: nu coboram automat verdict tare in aceeasi sesiune;
- testele trebuie rulate in 3 moduri: `FULL_ONLINE`, `DEGRADED_PROVIDER`, `LOCAL_ONLY`.

Ce nu folosim direct:

- scheletul Kotlin cu `GateAction` fara `NO_REPLY`;
- maparea `DANGEROUS -> Nu raspunde` doar pe baza canalului; noi pastram `NO_REPLY` first-class;
- `HIDDEN_LINK_OFFICIAL_TO_UNOFFICIAL` ca `DO_NOT_CONTINUE` local in offline fara cerere sensibila; in arhitectura finala hidden link singur e capped;
- orice copiere directa a pseudo-code-ului in locul contractului din `LAUNCH_ARCHITECTURE_FINAL.md`.

## Completari Pentru Source Of Truth

### Target-ul De Decizie Este `finalUrl`

Regula:

```text
primaryUrl este doar punctul de intrare.
finalUrl este tinta deciziei cand exista.
```

Implicații:

- rulam fast checks pe `primaryUrl`;
- cand redirect chain/finalUrl apare, reconstruim `EvidenceSnapshot`;
- reevaluam `EvidenceGate`;
- daca `finalUrl.host != primaryUrl.host`, hostul final castiga pentru official registry, forms si reputation;
- form action host poate castiga chiar si peste finalUrl daca formularul trimite date in alta parte.

### Web Risk Extended Coverage

Threat types relevante:

- `MALWARE`;
- `SOCIAL_ENGINEERING`;
- `UNWANTED_SOFTWARE`;
- `SOCIAL_ENGINEERING_EXTENDED_COVERAGE`, daca este disponibil si permis.

Regula:

- match pozitiv -> hard evidence;
- no-match -> supporting only, nu safe.

### urlscan Visibility

Policy:

- default: `private`;
- `public`: interzis pentru URL-uri user-submitted;
- `unlisted`: permis doar daca `private` nu este disponibil, URL-ul este redacted si nu contine PII/tokeni, iar privacy policy explica asta;
- daca URL-ul nu poate fi trimis sigur, sandbox este `SKIPPED_PRIVACY`.

### VirusTotal Commercial Policy

Policy:

- v1 productie nu foloseste VT Public API;
- daca VT ramane, trebuie Premium/Private Scanning / contract compatibil;
- daca nu avem licenta potrivita, VT adapter este disabled si Gate foloseste Web Risk/urlscan/structural/corpus;
- VT nu este feature obligatoriu pentru launch.

### Android Permissions

Recomandare mai stricta:

- ideal v1 fara `CAMERA`, daca QR/OCR pot fi acoperite prin Google Code Scanner / Document Scanner / picker;
- daca implementarea curenta cere `CAMERA`, ramane permis doar pentru QR/OCR explicit user-initiated;
- nu cerem `POST_NOTIFICATIONS` in v1;
- nu cerem broad media/storage; folosim Photo Picker / SAF.

### Async Monotonicity

Regula:

- `VERIFY_OFFICIAL` poate urca la `NO_ENTER_DATA` sau `DO_NOT_CONTINUE`;
- `INSUFFICIENT_EVIDENCE` poate urca la orice verdict cand apar date;
- `CONTINUE_WITH_CAUTION` poate urca la `VERIFY_OFFICIAL`, `NO_ENTER_DATA` sau `DO_NOT_CONTINUE`;
- nu auto-coboram `DO_NOT_CONTINUE` sau `NO_ENTER_DATA` in aceeasi sesiune;
- downgrade-ul unui verdict tare necesita rescan manual sau review, nu update async silent.

### Provider Fallback Details

- urlscan result `404` inainte de poll window = `PENDING`, nu fail;
- urlscan `410` = rezultat sters/indisponibil, nu clean;
- urlscan `429` = rate limited, respectam reset/backoff;
- VT queued/in-progress nu blocheaza UI;
- backend down -> OfflineRiskPolicy, max `VERIFY_OFFICIAL` in semnale slabe.

### Cache Additions

- cache key ignora query params sensibile;
- unknown/provider outage nu se cache-uieste ca verdict de continut;
- finalUrl change invalideaza evidence/cache dependent de host;
- registryVersion change invalideaza evidence care depinde de official/delegated status.

### Test Harness

Fiecare fixture critica trebuie rulata in:

- `FULL_ONLINE`;
- `DEGRADED_PROVIDER`;
- `LOCAL_ONLY`.

Asertii obligatorii:

- action exact;
- decisive signal ids in ordine stabila;
- headline exact conform mapping-ului UI.

## Concluzie

3/3 este util ca rafinare operationala/compliance, nu ca schimbare de arhitectura.

Cele mai importante linii de pastrat:

```text
Decide pe finalUrl.
urlscan private by default.
Nu folosi VT Public API in productie comerciala.
Prefer permissionless scanners/pickers.
Async updates pot urca riscul, dar nu coboara silent verdicturi tari.
```
