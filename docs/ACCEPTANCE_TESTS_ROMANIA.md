# SigurScan Acceptance Tests Romania

Ultima actualizare: 2026-06-02

Scop: lista de teste end-to-end si corpus tests care trebuie sa treaca inainte ca pipeline-ul sa fie considerat pregatit pentru clienti.

## Reguli generale

Fiecare test trebuie sa verifice:

- inputul real sau fixture-ul;
- linkurile extrase;
- URL-ul principal ales;
- final URL;
- sursele de reputatie;
- verdictul user-facing;
- motivele simple;
- lipsa false-positive-ului asteptat.

## Test 1: Uber promotional real

Input:

- email HTML cu buton `Comanda o cursa`;
- link `rides.sng.link` cu `_fallback_redirect=https://www.uber.com`.

Expected:

- `Am primit HTML complet`;
- linkul din buton este extras;
- fallback/final URL este `uber.com`;
- nu apare `Mail cu link ascuns`;
- nu apare `eMAG fals`;
- verdict `LOW_RISK` sau `UNKNOWN` daca urlscan nu este gata;
- user copy: `Poti continua cu prudenta` sau `Nu pot verifica suficient`.

## Test 2: Uber fake payment/card

Input:

- email/SMS care pretinde Uber;
- link catre `uber-promo-login.example.net/card/verify`.

Expected:

- linkul este extras;
- brand claim `Uber`;
- domeniu neoficial;
- intent sensibil `card/verify`;
- verdict minim `SUSPICIOUS`, iar cu form/card confirmat `DANGEROUS`;
- user copy: `Verifica pe canalul oficial` sau `Nu continua`.

## Test 3: FAN Courier fake taxa

Input:

- mesaj cu FAN Courier, colet blocat, taxa mica, link neoficial.

Expected:

- brand claim `FAN Courier`;
- domeniu final neoficial;
- intent plata/date;
- verdict `DANGEROUS`;
- user copy: `Nu apasa`.

## Test 4: FAN Courier real

Input:

- link catre domeniu oficial FAN/selfawb/fanbox.

Expected:

- domeniu oficial;
- fara cerere neoficiala de card/OTP;
- Web Risk clean;
- verdict `LOW_RISK` sau `UNKNOWN`;
- nu se marcheaza scam doar pentru `livrare`, `AWB`, `tracking`.

## Test 5: ANAF fake/SPV

Input:

- mesaj/email care pretinde ANAF/SPV;
- link neoficial;
- cere plata, login, date personale sau rambursare.

Expected:

- brand claim `ANAF`;
- domeniu neoficial;
- intent sensibil;
- verdict `DANGEROUS`.

## Test 6: eMAG real newsletter

Input:

- newsletter real pe domeniu oficial sau tracking cu fallback oficial.

Expected:

- brand `eMAG`;
- fara familie `eMAG fals / Premiu fals`;
- marketing language ignorat ca dovada decisiva;
- verdict `LOW_RISK` sau `UNKNOWN`.

## Test 7: eMAG fake premiu/card

Input:

- mesaj cu premiu/voucher/eMAG;
- link neoficial;
- cere plata transport/card/date.

Expected:

- verdict `DANGEROUS`;
- motiv: brand mismatch + cerere date/plata.

## Test 8: Web Risk malware test

Input:

- URL de test malware/phishing pentru Google Web Risk.

Expected:

- Web Risk `Threats Detected`;
- verdict vizibil `DANGEROUS`;
- user copy: `Nu apasa`.

## Test 9: example.com

Input:

- `https://example.com`

Expected:

- nu apare familie scam;
- nu apare `100% sigur`;
- verdict `LOW_RISK` sau `UNKNOWN`;
- user copy prudent.

## Test 10: Yahoo/Gmail/Outlook shell HTML

Input:

- HTML shell al webmailului, cu scripturi/resource URLs, fara corpul real al emailului.

Expected:

- resource links webmail sunt ignorate ca actiuni user;
- nu apare `Mail cu link ascuns`;
- verdict `UNKNOWN` sau input insuficient.

## Test 11: Link vizibil diferit de href

Input:

- text vizibil `https://revolut.com`;
- href/final URL catre domeniu neoficial care cere login/OTP.

Expected:

- mismatch vizibil vs real;
- verdict `DANGEROUS`;
- user copy: `Nu introduce date`.

## Test 12: Tracking legitim catre brand

Input:

- tracking/marketing redirect cu fallback oficial clar.

Expected:

- wrapper-ul nu este considerat domeniu oficial global;
- fallback-ul oficial reduce riscul;
- verdict nu devine `DANGEROUS` doar din tracking.

## Test 13: urlscan unavailable

Input:

- URL normal, Web Risk clean, urlscan nu raspunde.

Expected:

- verdict `UNKNOWN` sau `LOW_RISK` doar daca restul dovezilor sunt suficiente;
- user copy: `Nu pot verifica suficient` daca final URL nu este clar.

## Test 14: VirusTotal fallback

Input:

- Web Risk clean;
- urlscan neclar;
- domeniu necunoscut cu context sensibil.

Expected:

- VT ruleaza fallback;
- daca VT malicious, verdict `DANGEROUS`;
- daca VT not found, verdict intern ramane `SUSPICIOUS` sau `UNKNOWN`, iar userul vede `Verifica pe canalul oficial` sau `Nu pot verifica suficient`, nu `safe`.

## Test 15: Marketing urgency benign

Input:

- oferta reala pe domeniu oficial cu `azi doar`, `nu rata`, `reducere`.

Expected:

- semnalele slabe nu produc `DANGEROUS`;
- verdict `LOW_RISK` sau `UNKNOWN`;
- motivul nu acuza marketingul singur.
