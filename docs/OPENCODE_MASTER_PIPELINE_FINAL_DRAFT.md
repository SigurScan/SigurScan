# SigurScan - OpenCode Master Pipeline Final Draft

Ultima actualizare: 2026-06-02

Scop: versiunea OpenCode a livrabilului pe care vrem sa il comparam la 8 PM cu GPT 5.5 Pro Web. Acest document combina cercetare pe surse oficiale, arhitectura finala, evidence gate, pseudocode, data contracts, RAG/corpus policy si checklist de implementare.

## 1. Concluzie executiva

SigurScan trebuie sa fie un sistem de dovezi, nu un sistem de keyword-uri.

Formula finala:

`Input -> Extractor -> Normalizer -> Evidence Builder -> Cascaded Scans -> Evidence Gate -> Decision Engine -> RAG Explainer -> User Result`

Regula centrala:

- Nu decidem scam din limbaj comercial.
- Nu decidem scam din simplul fapt ca emailul este HTML.
- Nu decidem scam din simplul fapt ca linkul este sub buton.
- Nu decidem scam din simplul fapt ca exista tracking link.
- Decidem pe baza destinatiei reale, brand match, intentul paginii finale si reputatie.

UI-ul trebuie sa fie hotarat in actiune, dar prudent in promisiuni:

- `Poti continua cu prudenta`
- `Nu continua`
- `Nu introduce date`
- `Nu raspunde`
- `Verifica pe canalul oficial`
- `Nu pot verifica suficient`

Nu folosim in UI principal:

- `suspect`, ca raspuns final vag;
- `100% sigur`;
- `garantat legitim`;
- `site sigur`.

## 2. Cercetare oficiala si implicatii

### Google Web Risk

Surse consultate:

- `https://cloud.google.com/web-risk/docs/lookup-api`
- `https://cloud.google.com/web-risk/pricing`
- `https://docs.cloud.google.com/web-risk/docs/caching`
- `https://docs.cloud.google.com/web-risk/docs/lists`

Fapte relevante:

- Lookup API `uris.search` verifica un URL per request.
- Poate verifica mai multe threat types in acelasi request.
- Daca nu exista match, raspunsul este `{}`.
- Daca exista match, raspunsul contine `threatTypes` si `expireTime`.
- Google documenteaza cache pe baza de `expireTime`.
- Web Risk lists acopera resurse web nesigure, inclusiv social engineering/phishing, malware si unwanted software.
- Free tier confirmat: `uris.search` gratuit pana la 100.000 call-uri/luna.
- Dupa free tier: `$0.50 per 1,000 calls` pentru Lookup API.

Implicație pentru SigurScan:

- Web Risk este sursa comerciala corecta pentru reputatie Google.
- Ruleaza devreme, cu cache.
- Web Risk match este semnal puternic si poate produce `Nu continua` chiar daca urlscan inca proceseaza.
- Web Risk clean nu inseamna automat safe. Inseamna doar `no known match`.

### Google Safe Browsing API direct

Sursa consultata:

- `https://developers.google.com/safe-browsing/terms`

Fapte relevante:

- Termenii spun explicit ca uzul comercial al Safe Browsing API este interzis fara acord separat cu Google.
- Cer atributie si notificare despre limitarile serviciului.
- Atributia Google nu trebuie folosita pentru avertizari care nu vin din listele Google.

Implicație pentru SigurScan:

- Nu folosim Safe Browsing API direct in produs comercial fara acord separat.
- Folosim Web Risk.
- Daca pastram cod GSB existent, trebuie izolat ca beta/dev sau scos din release comercial.

### urlscan.io

Sursa consultata:

- `https://urlscan.io/docs/api/`

Fapte relevante:

- Scan visibility: `public`, `unlisted`, `private`.
- `Public` este vizibil public si in search.
- `Unlisted` nu apare public, dar poate fi vizibil pentru security researchers/security companies in urlscan Pro.
- `Private` este vizibil doar contului tau sau daca share-uiesti scan ID.
- urlscan recomanda eliminarea PII din URL-uri sau folosirea `unlisted`.
- Recomanda backoff, respectarea HTTP 429, work queue si retry.
- Recomanda search/domain lookup inainte sa submiti din nou acelasi URL.
- Result API poate returna 404 pana se termina scanarea.
- Screenshot este disponibil la `https://urlscan.io/screenshots/{uuid}.png`.

Implicație pentru SigurScan:

- urlscan este moat-ul de UX: preview vizual + final URL + redirect chain.
- Nu trimitem email complet catre urlscan. Trimitem doar URL sanitizat.
- Default recomandat: `private` daca planul permite; altfel `unlisted`.
- Nu folosim `public` in produs.
- Trebuie cache, backoff, timeout si status `Preview indisponibil momentan`.
- Ruleaza default pe un singur `primary_url`, nu pe toate linkurile din email.

### VirusTotal

Surse consultate:

- `https://docs.virustotal.com/reference/overview`
- `https://docs.virustotal.com/docs/consumption-quotas-handled`

Fapte relevante:

- API v3 include URL scan/report, domain report, IP report, file report.
- VT ofera reputatie/context din multe motoare si blocklists.
- API quotas au limite per minute, zilnice si lunare.
- Cand quota este atinsa, API v3 raspunde cu 429.

Implicație pentru SigurScan:

- VT este fallback/intaritor, nu pilon obligatoriu pentru fiecare scanare.
- Cheia VT nu trebuie sa stea in APK.
- VT ruleaza pe backend, cu cache si rate limiting.
- VT malicious poate intari `Nu continua`, dar VT not found/clean nu inseamna automat safe.

### DNSC / blacklist Romania

Sursa incercata:

- `https://www.dnsc.ro/`
- `https://dnsc.ro/vezi/document/ghid-site-uri-frauduloase`

Rezultat:

- Accesul prin fetch automat a primit 403.
- Nu am confirmat un feed/API public stabil in aceasta sesiune.

Implicație pentru SigurScan:

- Nu implementam scraping agresiv.
- Cream provider modular: `RomanianPublicBlacklistProvider`.
- Accepta surse oficiale doar daca avem feed/API/licenta clara sau dataset manual versionat.
- In UI nu spunem `oficial DNSC` sau parteneriat fara acord explicit.

## 3. Cei 5 piloni finali

### Pilon 1: Intake and Extraction

Rol: aduce dovezile brute in sistem.

Include:

- Share Intent text/html/stream.
- Upload/import email, HTML, PDF, imagine, QR.
- HTML parser pentru `href`, butoane, `formaction`, `data-*`, JS redirect hints, meta refresh.
- OCR/QR extraction.
- Email metadata cand exista: subject, from, reply-to, return-path, SPF/DKIM/DMARC daca avem `.eml`.

Nu are voie:

- verdict final;
- brand/family din keywords generice;
- `DANGEROUS` doar pentru HTML/link sub buton.

Output: `ExtractedPayload`.

### Pilon 2: URLscan Sandbox Preview

Rol: moat principal si dovada vizuala.

Include:

- URL final;
- redirect chain;
- screenshot/preview;
- verdict urlscan;
- HTTP status/server/IP/country in detalii tehnice.

Reguli:

- Ruleaza default pe `primary_url`.
- `private` preferat; `unlisted` fallback.
- Nu `public`.
- Sanitizare query params sensibili.
- Cache pe normalized URL, final URL, domain, screenshot hash.
- Preview poate continua async dupa verdict rapid.

### Pilon 3: Reputation and Blacklists

Rol: confirma riscul cunoscut.

Include:

- Google Web Risk.
- Romanian blacklist provider cand exista feed verificat.
- VirusTotal fallback.
- Cache intern.

Reguli:

- Web Risk match este strong signal.
- Blacklist match este strong signal.
- VT ruleaza doar in situatii neclare/conflictuale sau la cererea userului.

### Pilon 4: Romania Context, Scam Families, Official Domains

Rol: intelege contextul local fara false positives.

Include:

- FAN Courier, ANAF/SPV, Poșta Romana, banci, OLX, eMAG, Revolut, WhatsApp, remote access, investitii, job scams.
- Official domains registry.
- Brand claim confidence.
- Visible link vs actual href mismatch.
- Page intent: login/payment/card/OTP/CNP/IBAN/download/remote access.

Regula cheie:

- Brandul trebuie confirmat prin brand explicit, domeniu oficial, sender/final URL sau context puternic.
- `voucher`, `livrare`, `colet`, `plata`, `cod`, `promotie` sunt semnale slabe/medii, nu brand identity.

### Pilon 5: Offer Checker, RAG Explainer, User Decision

Rol: transforma dovezile in raspuns simplu.

Offer checker:

- Nu spune automat `oferta e falsa`.
- Spune `nu am gasit confirmare oficiala`, `verifica in aplicatia oficiala`, sau `oferta cere date pe domeniu neoficial`.

RAG:

- Este consultant, nu judecator.
- Primeste evidence summary si corpus snippets.
- Produce explicatie si copy.
- Nu produce verdict final.

User decision:

- Actiune concreta, nu threat intel.

## 4. Data contracts recomandate

### ScanInput

```json
{
  "scan_id": "uuid",
  "source_channel": "share_intent|upload|manual|qr|ocr",
  "declared_mime_type": "text/html",
  "raw_text": "...",
  "raw_html": "...",
  "file_refs": [],
  "received_at": 1760000000
}
```

### ExtractedPayload

```json
{
  "input_type": "email_html_or_eml",
  "visible_text": "...",
  "subject": "...",
  "sender": {
    "from_domain": "uber.com",
    "reply_to_domain": null,
    "return_path_domain": null,
    "auth": {
      "spf": "pass|fail|unknown",
      "dkim": "pass|fail|unknown",
      "dmarc": "pass|fail|unknown"
    }
  },
  "urls": [
    {
      "raw_url": "https://rides.sng.link/...",
      "normalized_url": "https://rides.sng.link/...",
      "visible_label": "Comanda o cursa",
      "source": "button_href",
      "is_user_actionable": true,
      "is_webmail_resource": false,
      "rank": 1
    }
  ],
  "forms": [
    {
      "action_url": "https://example.net/submit",
      "fields": ["card", "cvv"]
    }
  ],
  "weak_signals": ["marketing_urgency"],
  "extraction_warnings": []
}
```

### EvidenceSnapshot

```json
{
  "scan_id": "uuid",
  "primary_url": "https://rides.sng.link/...",
  "sanitized_primary_url": "https://rides.sng.link/...",
  "claimed_brand": "Uber",
  "brand_confidence": "high|medium|low|none",
  "expected_official_domains": ["uber.com", "uber.link", "ubereats.com"],
  "final_url": "https://www.uber.com/ro/",
  "final_domain": "uber.com",
  "redirect_chain": [],
  "visible_vs_actual_mismatch": false,
  "official_domain_match": true,
  "tracking_redirect": {
    "is_tracking": true,
    "fallback_official": true,
    "wrapper_domain": "sng.link"
  },
  "page_intent": {
    "login": false,
    "payment": false,
    "card": false,
    "otp": false,
    "identity": false,
    "download": false,
    "remote_access": false
  },
  "form_action_domain": null,
  "source_results": [],
  "strong_signals": [],
  "medium_signals": [],
  "weak_signals": ["marketing_urgency"],
  "source_conflicts": [],
  "missing_evidence": []
}
```

### SourceResult

```json
{
  "source": "web_risk|urlscan|virus_total|romanian_blacklist|official_domains|cache",
  "status": "clean|malicious|suspicious|not_found|unavailable|processing|error",
  "severity": "low|medium|high|critical|unknown",
  "summary": "No known Web Risk match",
  "raw_ref": "internal-log-id",
  "expires_at": 1760000000
}
```

### GateResult

```json
{
  "gate_status": "HAS_ENOUGH_EVIDENCE|NEEDS_MORE_INFO|CONFLICTING_EVIDENCE",
  "internal_class": "LOW_RISK|SUSPICIOUS|DANGEROUS|UNKNOWN",
  "recommended_user_action": "CONTINUE_WITH_CAUTION|DO_NOT_CONTINUE|DO_NOT_ENTER_DATA|DO_NOT_REPLY|VERIFY_OFFICIAL|CANNOT_VERIFY",
  "primary_reason_codes": ["OFFICIAL_FINAL_DOMAIN", "WEB_RISK_MATCH"],
  "required_followups": ["RUN_VT_FALLBACK"]
}
```

### UserResult

```json
{
  "headline": "Poti continua cu prudenta",
  "subheadline": "Nu am gasit semnale cunoscute de risc si destinatia este coerenta cu brandul.",
  "final_domain": "uber.com",
  "preview_url": "https://urlscan.io/screenshots/uuid.png",
  "reasons": [
    "Linkul ajunge pe domeniul oficial Uber.",
    "Nu am gasit semnale cunoscute de phishing sau malware."
  ],
  "next_action": "Continua doar daca recunosti expeditorul si nu ti se cer coduri sau date de card.",
  "technical_details_available": true
}
```

## 5. Orchestrare cascadata

### Principiu

Nu rulam tot mereu. Rulam pana avem dovezi suficiente.

Ordine recomandata:

1. Extractor.
2. Normalizer + primary URL picker.
3. Cache lookup.
4. Official domains registry + brand hypothesis.
5. Web Risk Lookup.
6. Romanian blacklist provider.
7. urlscan preview pentru `primary_url`.
8. Evidence Gate v1.
9. VT fallback doar daca gate-ul cere.
10. Offer checker daca exista oferta/brand claim si verdictul depinde de confirmare.
11. Evidence Gate v2.
12. RAG explainer.
13. User Result.

### Cand sarim peste VT

Sarim peste VT daca:

- Web Risk a confirmat risc si avem deja `DANGEROUS`;
- DNSC/blacklist a confirmat risc si avem deja `DANGEROUS`;
- urlscan este malicious si avem deja `DANGEROUS`;
- urlscan + Web Risk + official domain sunt coerente si fara intent sensibil;
- rezultatul este in cache proaspat;
- scanarea este doar marketing legitim cu final URL oficial si fara conflict.

### Cand rulam VT

Rulam VT daca:

- urlscan este indisponibil/processing peste timeout;
- Web Risk este clean, dar exista brand mismatch + context sensibil;
- final domain este necunoscut si pagina cere date/logare/plata;
- sursele se contrazic;
- exista redirect chain complex si final URL nu e clar;
- userul cere analiza extinsa.

### Cand rulam offer checker

Rulam offer checker daca:

- textul contine o oferta/premiu/rambursare/voucher/investitie;
- exista brand claim;
- verdictul nu este deja `DANGEROUS` din malware/phishing/blacklist;
- avem nevoie sa formulam `Verifica pe canalul oficial` vs `Poti continua cu prudenta`.

Offer checker nu transforma absenta confirmarii oficiale in `DANGEROUS` singur.

## 6. Evidence Gate final

### Minimum evidence sets

#### A. Malicious reputation set

Suficient pentru `DANGEROUS`:

- Web Risk match malware/social engineering/phishing;
- Romanian blacklist match;
- urlscan malicious;
- VT malicious relevant in fallback.

Output:

- `Nu continua`;
- `Nu apasa`;
- `Nu introduce date`, daca exista pagina/formular sensibil.

#### B. Sensitive destination mismatch set

Suficient pentru `DANGEROUS`:

- claimed brand medium/high;
- final domain neoficial;
- pagina cere card/OTP/parola/CNP/IBAN/login/plata;
- sau form action trimite catre domeniu neoficial.

Output:

- `Nu introduce date`;
- `Nu continua`.

#### C. Deceptive link set

Suficient pentru `DANGEROUS` sau `VERIFY_OFFICIAL` in functie de intent:

- text vizibil arata domeniu oficial;
- href/final URL duce catre alt domeniu;
- daca cere date sensibile: `DANGEROUS`;
- daca nu cere date si reputatia este clean/neclara: `Verifica pe canalul oficial`.

#### D. Benign coherence set

Suficient pentru `LOW_RISK`:

- final URL determinat;
- final domain oficial sau tracking legitim cu fallback oficial;
- Web Risk clean/no match;
- no blacklist match;
- urlscan clean/no malicious, daca a rulat;
- nu cere date sensibile pe domeniu neoficial;
- brand/context coerente.

Output:

- `Poti continua cu prudenta`.

#### E. Insufficient evidence set

Suficient pentru `UNKNOWN`:

- nu avem final URL;
- urlscan indisponibil si Web Risk/blacklist nu spun nimic;
- inputul e doar text vag;
- tracking link fara fallback validat;
- surse conflictuale.

Output:

- `Nu pot verifica suficient`;
- daca context sensibil: `Verifica pe canalul oficial`.

### Weak signals

Nu pot produce `DANGEROUS` singure:

- HTML email;
- link sub buton;
- tracking link;
- newsletter;
- `profita acum`;
- `ultima sansa`;
- `nu rata`;
- `voucher`;
- `promotie`;
- `reducere`;
- `oferta limitata`.

### Medium signals

Pot produce `Verifica pe canalul oficial` sau pot cere VT/urlscan fallback:

- brand mentionat cu link neoficial, fara cerere de date;
- redirect chain complex;
- sender/reply-to mismatch;
- email auth lipsa la brand sensibil;
- domain foarte nou, IDN/confusable;
- shortener fara fallback oficial;
- context sensibil, dar pagina finala nu e clara.

### Strong signals

Pot produce `Nu continua`:

- Web Risk match;
- blacklist match;
- urlscan malicious;
- brand mismatch + cerere date sensibile;
- form action neoficial pentru date sensibile;
- visible link mismatch + intent sensibil;
- download APK/remote access neoficial.

## 7. Decision Matrix user-facing

| Internal class | Condition | User headline | Subcopy |
| --- | --- | --- | --- |
| `LOW_RISK` | Benign coherence set complet | `Poti continua cu prudenta` | `Nu am gasit semnale cunoscute de risc. Verifica totusi expeditorul.` |
| `SUSPICIOUS` | Medium signals, fara strong signals | `Verifica pe canalul oficial` | `Nu avem destule dovezi sa recomandam continuarea direct din link.` |
| `DANGEROUS` | Reputation malicious sau sensitive mismatch | `Nu continua` | `Am gasit semnale reale de risc pentru acest link.` |
| `DANGEROUS_DATA` | Cere card/OTP/parola/CNP/IBAN pe domeniu neoficial | `Nu introduce date` | `Pagina cere date sensibile pe un domeniu care nu corespunde brandului.` |
| `DANGEROUS_REPLY` | Email cere raspuns cu date/coduri/bani | `Nu raspunde` | `Mesajul cere informatii sau actiuni riscante.` |
| `UNKNOWN` | Lipsa final URL/surse/conflict | `Nu pot verifica suficient` | `Nu am destule dovezi pentru un verdict ferm.` |

## 8. Raspunsuri explicite la intrebarile critice

### Cand afisam `Poti continua cu prudenta`?

Doar cand:

- final URL este cunoscut;
- domeniul final este oficial sau tracking legitim catre oficial;
- Web Risk nu are match;
- nu exista blacklist match;
- urlscan nu este malicious, daca a rulat;
- pagina nu cere date sensibile pe domeniu neoficial;
- brand/context sunt coerente.

### Cand afisam `Nu continua`?

Cand exista un semnal puternic:

- Web Risk match;
- blacklist match;
- urlscan malicious;
- brand mismatch clar + intent sensibil;
- visible URL mismatch + intent sensibil;
- download/remote access neoficial.

### Cand afisam `Verifica pe canalul oficial`?

Cand nu avem malware/blacklist, dar exista risc contextual:

- brand mentionat si link neoficial fara intent sensibil confirmat;
- oferta neconfirmata oficial;
- sender/reply-to mismatch;
- tracking/fallback nevalidat;
- surse incomplete, dar contextul este banca/curier/ANAF/plata.

### Cand afisam `Nu pot verifica suficient`?

Cand:

- nu avem final URL;
- urlscan/Web Risk/blacklist nu pot rula;
- inputul nu contine destule date;
- HTML share este doar shell de webmail;
- sursele se contrazic si nu avem fallback suficient.

### Daca urlscan este clean, dar pagina cere card pe domeniu neoficial?

Verdict: `Nu introduce date`.

Motiv: intentul paginii finale si domeniul neoficial bat un sandbox clean. urlscan clean inseamna doar ca nu a vazut malware/phishing cunoscut, nu ca pagina este legitima.

### Daca Web Risk este clean, dar brand mismatch + form action dubios exista?

Verdict: `Nu introduce date` sau `Nu continua`, in functie de intent.

Motiv: Web Risk clean nu este dovada de siguranta.

### Daca emailul are tracking link legitim catre domeniu oficial?

Verdict: `Poti continua cu prudenta` daca restul surselor sunt clean si nu cere date sensibile neoficiale.

### Daca exista doar `voucher/profita acum/nu rata`?

Verdict maxim permis: `UNKNOWN` sau `LOW_RISK`, in functie de dovezile de destinatie. Niciodata `DANGEROUS` doar din aceste cuvinte.

### Cand ruleaza VT si cand il sarim?

Ruleaza cand gate-ul are nevoie de intarire sau exista conflict. Il sarim cand Web Risk/urlscan/blacklist/gate sunt suficiente.

### Ce ascundem implicit in UI?

- VT engine counts;
- Web Risk raw threat types;
- urlscan raw JSON;
- IP, ASN, server, country;
- redirect chain complet;
- rule IDs;
- provider errors;
- model/RAG internals.

## 9. Pseudocode orchestrator

```kotlin
suspend fun scan(input: ScanInput): UserResult {
    val extracted = extractor.extract(input)
    val candidates = normalizer.normalizeAndRank(extracted.urls)

    if (candidates.isEmpty()) {
        return decisionEngine.fromTextOnly(extracted)
    }

    val primary = primaryUrlPicker.pick(candidates, extracted)
    val evidence = EvidenceSnapshot(scanId = input.scanId, primaryUrl = primary.normalizedUrl)

    evidence.merge(cache.lookup(primary.normalizedUrl))
    evidence.merge(officialDomains.evaluate(extracted, primary))
    evidence.merge(brandDetector.detect(extracted, primary))

    if (!evidence.hasFreshWebRisk()) {
        evidence.merge(webRisk.lookup(primary.normalizedUrl))
    }

    if (!evidence.hasFreshRomanianBlacklist()) {
        evidence.merge(romanianBlacklist.lookup(primary.normalizedUrl))
    }

    val earlyGate = evidenceGate.evaluate(evidence)
    if (earlyGate.internalClass == DANGEROUS && earlyGate.hasStrongReputationSignal()) {
        urlscan.submitAsyncIfAllowed(primary.sanitizedUrl)
        return resultBuilder.build(earlyGate, evidence, rag.explain(earlyGate, evidence))
    }

    if (urlscanPolicy.shouldRun(evidence, primary)) {
        evidence.merge(urlscan.scanOrGetCached(primary.sanitizedUrl))
    }

    var gate = evidenceGate.evaluate(evidence)

    if (vtPolicy.shouldRun(gate, evidence)) {
        evidence.merge(virusTotal.lookupOrScan(primary.normalizedUrl))
        gate = evidenceGate.evaluate(evidence)
    }

    if (offerPolicy.shouldRun(extracted, evidence, gate)) {
        evidence.merge(offerChecker.checkOfficialSources(extracted, evidence))
        gate = evidenceGate.evaluate(evidence)
    }

    val explanation = rag.explain(gate, evidence)
    cache.store(evidence, gate)
    return resultBuilder.build(gate, evidence, explanation)
}
```

## 10. Pseudocode evidence gate

```kotlin
fun evaluate(e: EvidenceSnapshot): GateResult {
    if (e.webRisk.isMalicious || e.romanianBlacklist.isMatch || e.urlscan.isMalicious) {
        return dangerous("MALICIOUS_REPUTATION")
    }

    if (e.vt.isMaliciousRelevant && e.needsReputationFallback) {
        return dangerous("VT_MALICIOUS_FALLBACK")
    }

    if (e.hasSensitiveIntent && e.finalDomainIsUnofficialForClaimedBrand) {
        return dangerousData("SENSITIVE_INTENT_ON_UNOFFICIAL_DOMAIN")
    }

    if (e.formActionDomainIsUnofficial && e.formCollectsSensitiveData) {
        return dangerousData("SENSITIVE_FORM_TO_UNOFFICIAL_DOMAIN")
    }

    if (e.visibleLinkClaimsOfficialDomain && e.finalDomainDiffers) {
        return if (e.hasSensitiveIntent) {
            dangerousData("VISIBLE_ACTUAL_MISMATCH_WITH_SENSITIVE_INTENT")
        } else {
            verifyOfficial("VISIBLE_ACTUAL_MISMATCH")
        }
    }

    if (!e.hasFinalUrl && !e.hasStrongReputationSignal) {
        return unknown("FINAL_URL_MISSING")
    }

    if (e.hasSourceConflicts) {
        return unknown("CONFLICTING_EVIDENCE", followups = listOf("RUN_VT_FALLBACK"))
    }

    if (e.hasMediumSignals && !e.hasStrongSignals) {
        return verifyOfficial("MEDIUM_SIGNALS_ONLY")
    }

    if (e.isOfficialOrOfficialFallback && e.webRisk.isCleanOrNoMatch && !e.hasBlacklistMatch && !e.hasUnofficialSensitiveIntent) {
        return lowRisk("BENIGN_COHERENCE")
    }

    return unknown("INSUFFICIENT_EVIDENCE")
}
```

## 11. Scam family definitions

### FAN Courier fake

Brand evidence required:

- `FAN Courier`, `fancourier`, `fan courier`, official sender/domain, or visual brand evidence.

Strong risk combo:

- brand claim FAN + final domain not in official registry + payment/card/address update/OTP/login.

Weak signals only:

- `colet`, `AWB`, `livrare`, `tracking`.

### eMAG fake

Brand evidence required:

- explicit `eMAG` in text/sender/final page/link context.

Strong risk combo:

- eMAG claim + unofficial domain + prize/voucher/payment/card/form.

Weak signals only:

- `voucher`, `promotie`, `reducere`, `gratuit`, `nu rata`.

### ANAF/SPV fake

Brand evidence required:

- `ANAF`, `SPV`, `Spatiul Privat Virtual`, official fiscal context.

Strong risk combo:

- ANAF/SPV claim + unofficial domain + login/payment/rambursare/date personale.

Weak signals only:

- `taxa`, `factura`, `rambursare` fara ANAF/SPV/context oficial.

### Banking/OTP/card

Brand evidence:

- bank brand, financial app, or page asking financial credentials.

Strong risk combo:

- request card/CVV/OTP/password/IBAN + final domain not official.

Weak signals only:

- `plata`, `cod`, `transfer` fara context sensibil.

### WhatsApp takeover

Brand evidence required:

- explicit WhatsApp or WhatsApp-related URL/context.

Strong risk combo:

- request verification code/device link + sender not official/social engineering.

Weak signals only:

- `cod`, `sms`, `numar` fara WhatsApp/context.

### Remote access fraud

Strong risk combo:

- AnyDesk/TeamViewer/QuickSupport/remote access request + pressure + financial/support context.

Weak signals only:

- `aplicatie`, `tehnic`, `ecran`.

## 12. Official domains registry schema

```json
{
  "brand_id": "uber",
  "display_name": "Uber",
  "country": "RO",
  "official_domains": ["uber.com", "uber.link", "ubereats.com"],
  "conditional_tracking_domains": [
    {
      "domain": "sng.link",
      "valid_if": "fallback_redirect_domain_in_official_domains"
    }
  ],
  "sensitive_actions_allowed_only_on_official": ["login", "payment", "card", "otp"],
  "last_verified_at": "2026-06-02",
  "verification_source": "manual_internal",
  "corpus_cases": ["ro-uber-real-promo-001", "ro-uber-fake-card-001"]
}
```

Regula:

- Tracking domains nu sunt oficiale global.
- Sunt acceptate doar conditionat, daca fallback/final URL este oficial.

## 13. Corpus plan

Fiecare caz trebuie sa contina:

- raw input;
- extraction expected;
- evidence expected;
- gate expected;
- user result expected;
- false-positive guards.

Categorii minime:

- Uber real promo tracking;
- Uber fake card;
- eMAG real newsletter;
- eMAG fake premiu/card;
- FAN real tracking;
- FAN fake taxa/card;
- ANAF fake SPV;
- Revolut real;
- Revolut fake OTP;
- OLX fake curier/plata;
- Poșta fake;
- WhatsApp takeover;
- AnyDesk/remote support fraud;
- crypto/investment scam;
- job scam;
- tracking link legitim;
- webmail shell HTML fara email body;
- urlscan unavailable;
- Web Risk malware test.

## 14. UI final

### Above the fold

Ordine:

1. Preview securizat, daca exista.
2. Headline actiune.
3. Domeniul final: `Te duce catre: domain.tld`.
4. 1-2 motive simple.
5. Actiune recomandata.
6. Disclaimer scurt.

### Headline copy

`Poti continua cu prudenta`

- Cand benign coherence set este complet.

`Nu continua`

- Cand reputatia sau pagina finala indica risc real.

`Nu introduce date`

- Cand pagina cere card/OTP/parola/CNP/IBAN/login pe domeniu neoficial.

`Nu raspunde`

- Cand emailul cere date/coduri/bani prin raspuns.

`Verifica pe canalul oficial`

- Cand exista semnale medii sau oferta neconfirmata, dar nu dovezi suficiente pentru `Nu continua`.

`Nu pot verifica suficient`

- Cand lipseste final URL sau sursele sunt indisponibile/conflictuale.

### Disclaimer scurt

`SigurScan ofera o estimare automata bazata pe dovezile disponibile. Scamurile noi sau personalizate pot sa nu fie detectate. Pentru plati, parole sau coduri, verifica direct in aplicatia sau pe site-ul oficial.`

## 15. Acceptance tests obligatorii

1. Uber real email cu `rides.sng.link` si fallback `uber.com`.
   Expected: `Poti continua cu prudenta` sau `Nu pot verifica suficient` daca final URL lipseste; niciodata eMAG scam.

2. eMAG real newsletter cu promotie/voucher.
   Expected: nu devine scam doar din limbaj promo.

3. FAN Courier fake cu domeniu neoficial + taxa/card.
   Expected: `Nu introduce date` sau `Nu continua`.

4. FAN Courier real pe `fancourier.ro`, `selfawb.ro`, `fanbox.ro`.
   Expected: nu devine scam doar din `colet/AWB/livrare`.

5. ANAF/SPV fake cu link extern + login/plata/rambursare.
   Expected: `Nu continua`.

6. Web Risk malware test.
   Expected: `Nu continua`.

7. example.com.
   Expected: `Poti continua cu prudenta` sau `Nu pot verifica suficient`; nu familie scam.

8. Yahoo/Gmail shell HTML fara corpul emailului.
   Expected: `Nu pot verifica suficient`; ignora resource links.

9. Link vizibil `revolut.com`, href/final neoficial + OTP.
   Expected: `Nu introduce date`.

10. Tracking legitim catre brand oficial.
    Expected: nu `DANGEROUS` doar pentru tracking.

11. urlscan unavailable.
    Expected: `Nu pot verifica suficient` daca final URL nu e clar.

12. Marketing urgency benign.
    Expected: urgency nu este motiv principal de risc.

## 16. Implementare recomandata

### Backend first

Mutam orchestrarea si API keys pe backend.

Endpoint recomandat:

- `POST /v1/scans`
- `GET /v1/scans/{scan_id}`
- `POST /v1/scans/{scan_id}/feedback`

Android trimite input extras sau raw redacted, backend orchestreaza.

### Android responsibilities

- Share/import/upload extraction cat permite OS-ul.
- UX scan states.
- Preview display.
- Result display.
- Feedback false positive/false negative.

### Backend responsibilities

- API key protection.
- Web Risk/urlscan/VT calls.
- Cache.
- Official domains registry.
- Blacklist provider.
- Evidence Gate.
- RAG/corpus retrieval.

## 17. Privacy, legal, cost

- Cheile API nu stau in APK.
- Web Risk, nu Safe Browsing direct, pentru comercial.
- urlscan `private`/`unlisted`, nu `public`.
- Redactare PII/tokenuri inainte de urlscan/RAG.
- Privacy Policy declara procesatorii: backend, urlscan, Google Web Risk, VirusTotal daca folosit, AI/RAG provider daca folosit.
- Nu colecta SMS/Call Log/Accessibility in versiunea light.
- Nu trimite continut complet de email la urlscan.
- VT si urlscan trebuie cache/rate limited.

## 18. Schimbari concrete pentru Android/backend

1. Defineste `ExtractedPayload`, `EvidenceSnapshot`, `GateResult`, `UserResult`.
2. Refactor `ScannerViewModel` ca orchestrator UI, nu ca decider final monolitic.
3. Mutare Web Risk/urlscan/VT in backend/proxy.
4. Implementare cache pentru Web Risk/urlscan/VT.
5. Implementare `PrimaryUrlPicker`.
6. Implementare `OfficialDomainsRegistry` backend + sync local read-only.
7. Implementare `EvidenceGate` determinist.
8. Implementare `RagExplainer` dupa gate.
9. Implementare `OfferChecker` ca sursa de evidence, nu verdict absolut.
10. Test corpus runner pentru acceptance tests.
11. UI result action-first, technical details collapsed.
12. Feedback loop pentru false positives/false negatives.

## 19. Verdict final asupra directiei

Directia corecta este:

`SigurScan nu este un detector de marketing agresiv. Este un verificator de destinatie, identitate, intent si reputatie.`

Moat-ul real:

- userul da share/import;
- noi extragem ce nu vede userul;
- deschidem linkul in sandbox, nu pe telefon;
- aratam preview;
- verificam reputatia;
- comparam cu domeniile oficiale si corpusul Romania;
- dam o actiune clara.
