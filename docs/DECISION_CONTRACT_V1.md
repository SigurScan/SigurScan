# SigurScan Decision Contract v1

Data: 2026-06-08

Status: source of truth pentru urmatoarea implementare a verdictului. Acest document inlocuieste orice logica veche de gate care permite `legacy_risk_level`, `analysis.reasons`, regex-uri textuale, corpus, RAG sau Mistral sa seteze verdictul final.

## Scop

SigurScan trebuie sa aiba un singur creier de decizie:

```text
verdict(evidence_bundle) -> { label, score, reasons, confidence, completeness }
```

Verdictul user-facing este produs de o singura functie pura determinista. Niciun alt strat nu are voie sa seteze `SIGUR`, `SUSPECT`, `PERICULOS` sau `PENDING`.

Daca o linie de cod seteaza label-ul in afara reducerului, este bug.

## Invariantul central

Corpusul, RAG-ul, Mistral, regex-ul vechi si `analysis.reasons` nu voteaza verdictul.

Acestea pot produce doar:

- context;
- explicatii;
- similaritati cu familii de scam;
- sugestii pentru `reasons`;
- semnale brute care trebuie normalizate in evidence bundle.

Ele nu pot urca sau cobori label-ul final.

## De ce schimbam

Bug-ul FAN real a aratat defectul structural:

- sistemul nou vede providerii clean si domeniul oficial/delegat;
- sistemul vechi vede cuvinte precum `cod` sau `PIN` si ridica risc;
- ambele au drept de vot, deci verdictul devine inconsistent.

Nu reparam asta prin guard-uri per brand. Reparam prin de-autorizarea logicii vechi.

## Pipeline-ul unic

Fiecare etapa produce dovezi normalizate. Doar reducerul produce verdict.

```text
Input user: text / URL / email / HTML / image / PDF / QR
  -> Extract: PII redaction, URL-uri, brand pretins, text vizibil, HTML unde exista
  -> Resolve: final URL real, redirect chain, resolution status
  -> Providers: Web Risk, VirusTotal, urlscan verdict, preview best-effort
  -> Identity: registry oficial, domeniu delegat, lookalike, unrelated, unknown
  -> Request: ce se cere si prin ce canal
  -> Context: corpus / RAG / Mistral shadow, doar informativ
  -> Reduce: singurul verdict final
```

## Evidence Bundle

Reducerul citeste doar acest tip de obiect, nu obiecte istorice din atlas/gate:

```json
{
  "final_url": {
    "resolution": "resolved | partial | failed",
    "url": "https://selfawb.fancourier.ro/...",
    "registrable_domain": "fancourier.ro",
    "identity": "official | delegated | lookalike | unrelated | unknown",
    "suspicious_tld": false
  },
  "providers": {
    "web_risk": "clean | malicious | unknown | pending",
    "safe_browsing": "clean | malicious | unknown | pending",
    "virustotal": "clean | malicious | unknown | pending",
    "urlscan": "clean | malicious | unknown | pending",
    "worst_of": "clean | malicious | unknown | pending"
  },
  "request": {
    "sensitive": "none | card | cvv | otp | password | banking_pin | cnp | iban | crypto | remote | apk",
    "channel": "official | reply | whatsapp | unofficial_site | phone | unknown"
  },
  "claimed_brand": "FAN Courier",
  "context": {
    "nearest_family": "RO_SCN_001_FAN_LOCKER_WHATSAPP",
    "similarity": 0.62,
    "consistent": true
  },
  "completeness": {
    "final_url_resolved": true,
    "providers_quorum_met": true,
    "missing_required_pillars": []
  }
}
```

## Required vs enhancement

Pentru un input cu URL, verdict final necesita:

- final URL rezolvat sau esec explicit dupa retry/deadline;
- Web Risk rezultat terminal: `clean`, `malicious` sau `unknown`;
- VirusTotal rezultat terminal: `clean`, `malicious` sau `unknown`;
- urlscan verdict terminal: `clean`, `malicious` sau `unknown`.

Preview-ul vizual urlscan este enhancement. Screenshot-ul poate ramane pending fara sa blocheze label-ul, dar verdictul urlscan nu trebuie confundat cu screenshot-ul.

## Scara determinista

Prima regula care se potriveste castiga:

| Prioritate | Conditie | Verdict |
| --- | --- | --- |
| 1 | Orice provider este `malicious` | `PERICULOS` |
| 2 | Identitate finala `lookalike` sau `unrelated` si exista TLD suspect sau cerere sensibila | `PERICULOS` |
| 3 | Cerere sensibila prin canal gresit: reply, WhatsApp, site neoficial, telefon | `PERICULOS` |
| 4 | Rezolutie `partial`/`failed` fara quorum sau provider necesar `pending` | `PENDING` |
| 5 | Identitate `official`/`delegated`, providerii terminali fara malicious si fara cerere sensibila pe canal gresit | `SIGUR` |
| 6 | Identitate `unknown`, providerii terminali fara malicious si fara cerere sensibila | `SUSPECT` |
| 7 | Orice altceva | `SUSPECT` |

## Semnale care nu sunt verdict

Urmatoarele nu pot produce singure `SUSPECT` sau `PERICULOS`:

- `cod`;
- `PIN`;
- `urgent`;
- `oferta`;
- `voucher`;
- `promotie`;
- `accesati link`;
- `weekendul acesta`;
- limbaj comercial;
- link sub buton;
- tracking link;
- shortener/deeplink care rezolva pe destinatie oficiala/delegata si providerii sunt clean.

## Cerere sensibila reala

O cerere devine sensibila cand cere explicit date sau actiuni cu risc:

- numar card;
- CVV/CVC;
- OTP / cod de autentificare / cod WhatsApp;
- parola;
- PIN bancar;
- CNP, IBAN, copie act;
- seed phrase / crypto deposit;
- instalare APK;
- AnyDesk, TeamViewer, RustDesk sau control remote.

Context important:

- PIN de livrare, PIN locker, AWB sau cod de ridicare pe domeniu oficial/delegat de curier nu este OTP bancar.
- Un cod devine periculos cand este cerut prin reply, WhatsApp, telefon, site neoficial sau pentru autentificare/plata.

## Cazuri obligatorii de acceptanta

Acestea trebuie sa treaca inainte de orice claim de maturitate:

| Caz | Dovada asteptata | Verdict |
| --- | --- | --- |
| FAN oficial AWB / PIN livrare pe domeniu FAN/selfAWB clean | official/delegated + providers clean + request none | `SIGUR` |
| FAN fake plata taxa pe domeniu lookalike `.top` | unrelated/lookalike + card/payment | `PERICULOS` |
| YOXO onelink catre App Store / domeniu oficial clean | delegated + providers clean | `SIGUR` |
| eMAG/retail newsletter cu tracking legitim clean | delegated/official + providers clean | `SIGUR` |
| ANAF refund cu domeniu neoficial si card/CNP | unrelated + sensitive request | `PERICULOS` |
| WhatsApp/telefon stricat cere bani fara URL | sensitive request by reply/phone | `PERICULOS` |
| URL nerezolvat sau provider pending | incomplete evidence | `PENDING` |
| Domeniu necunoscut clean fara cerere sensibila | unknown + providers clean | `SUSPECT` |

## Ce se taie ca autoritate

Nu stergem toate fisierele istorice. Taiem dreptul lor de a decide verdictul:

- `legacy_risk_level` nu mai intra in verdict.
- `analysis.reasons` nu mai intra in verdict.
- `has_domain_mismatch` vechi nu mai intra direct in verdict; trebuie normalizat in `final_url.identity`.
- `_provider_reason_has_sensitive_request_signal()` nu mai poate influenta label-ul.
- `_brand_warning_matches_text()` nu mai poate influenta label-ul; poate produce context sau request normalizat doar daca detectorul este canal-aware.
- `scam_atlas.py` nu mai emite risc final; emite context si semnale normalizabile.
- Mistral ramane shadow analyst pana exista promovare formala bazata pe date reale etichetate.

## Definition of Done

- Exista o functie pura `verdict(evidence_bundle)`.
- Niciun alt loc din cod nu seteaza user label-ul final.
- Testele demonstreaza ca modificarea unui motiv textual/corpus match nu schimba label-ul daca evidence bundle-ul ramane identic.
- Testele demonstreaza `PENDING` pentru scanare partiala, nu `SUSPECT` din text.
- Testele acopera 50-100 mesaje reale romanesti etichetate.
- FAN oficial, YOXO, newslettere legitime si curieri oficiali ies `SIGUR` cand providerii sunt clean.
- ANAF/FAN/OLX/Revolut fake cu domenii neoficiale si cereri sensibile ies `PERICULOS`.

## Ordinea de lucru

1. Inghetam acest contract ca sursa de adevar.
2. Construim datasetul real etichetat.
3. Implementam normalizarea evidence bundle-ului.
4. Implementam reducerul pur.
5. Scoatem autoritatea de verdict din logica veche.
6. Repararam resolverul si urlscan orchestration doar cat sa alimenteze bundle-ul.
7. Rulam datasetul, E2E si smoke live.

## Atlas Romania 2025-2026

Materialele primite pe 2026-06-08 sunt integrate ca plan in `docs/ROMANIA_SCAM_ATLAS_2025_2026_INTEGRATION.md`.

Regula de compatibilitate:

```text
Scam atlas = context, registry candidate, brand warnings candidate, claim targets si tests.
Scam atlas != verdict engine.
```

Orice import din atlas trebuie sa fie normalizat in Evidence Bundle inainte sa poata influenta reducerul.
