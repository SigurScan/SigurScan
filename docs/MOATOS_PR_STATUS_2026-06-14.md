# MoatOS PR Status - 2026-06-14

Repo: `vaduvel/SigurScan`
Branch verificat: `feature/osint-intel-pipeline`
Production Cloud Run: `sigurscan-api-00043-qq7`
Production image: `europe-west1-docker.pkg.dev/project-20f225c0-d756-4cba-864/sigurscan/sigurscan-api:3231eeb`

## Rezumat Brutal

- Backend PR-5..PR-8 este deployat live si verificat pe endpoint-uri reale.
- Supabase PR-6 tables sunt aplicate live si citibile prin REST.
- DNS reputation este activ live (`ENABLE_DNS_REPUTATION=true`) si apare in scanari reale ca `infra_dns`.
- PR-6 Cercul are acum write-through plus read-fallback din Supabase; testat live cu link creat inainte de deploy.
- Android PR-5/PR-7/PR-9/PR-10 nu este feature-complete. Build-ul trece, dar lipsesc integrari reale on-device.
- Android PR-5 are acum hot-cache client, cache offline, CallScreeningService si UI pentru sync/rol OS. Nu a fost inca validat pe device real cu rolul activat.
- Android PR-7 are acum BTR sync local si motor on-device de provenienta pe semnale locale. Nu citeste automat SMS-uri.
- Android PR-8 afiseaza `action_plan` si are flow post-incident pentru impacts reale (`shared_card`, `paid_transfer` etc.).
- Android PR-9/PR-10 audio este blocat explicit prin policy pana exista model ASR on-device, consimtamant, disclosure si QA real-device.
- `origin/main` nu este sursa exacta a productiei; productia ruleaza branch-ul `feature/osint-intel-pipeline`.

## Verificari Rulate

- Backend full test: `INVOICE_CACHE_HMAC_KEY=testkey PRIVACY_SAFE_MODE=false pytest -q`
  - rezultat: `898 passed, 1 warning`
- Android JVM + build: `JAVA_HOME='/Applications/Android Studio.app/Contents/jbr/Contents/Home' ./gradlew testDebugUnitTest assembleDebug`
  - rezultat: `BUILD SUCCESSFUL`
- Android feature tests adaugate:
  - `RadarHotCacheTest`
  - `BtrSyncStoreTest`
  - `InboxProvenanceEngineTest`
  - `ActionPlanRequestTest`
  - `AudioSafetyPolicyTest`
- Cloud Run live:
  - revision: `sigurscan-api-00043-qq7`
  - traffic: `100%`
  - image: `:3231eeb`
- Domeniu oficial `https://api.sigurscan.com`:
  - `/health`: OK
  - `/v1/radar/hot-iocs`: OK
  - `/v1/btr/sync`: OK, `16` manifeste; no-op version-gated OK
  - `/v1/legal/action-plan`: OK, plan cu `4` pasi si `3` canale raportare pentru impacts reale
  - POST `/v1/scan/orchestrated` cu YOXO: `SAFE`, score `10`, preview `ready`
- Live scan YOXO:
  - verdict: `SAFE`
  - score: `10`
  - `infra_dns`: `clean / resolves`
  - preview: `ready`
- Live scan mesaj bancar periculos:
  - verdict: `DANGEROUS`
  - score: `90`
  - `action_plan`: prezent, 2 pasi
  - `infra_dns`: `suspicious / nxdomain`
- Live scan `https://urlz.fr/rZrw` dupa activare DNS:
  - status: `complete`
  - preview reason: `final_url_unresolved`
  - `infra_dns`: `suspicious / registrar_suspended`
  - observatie: user label ramas `UNVERIFIED/info`, nu `SUSPECT`

## PR / Moat Matrix

| PR | Moat / functie | Backend live | Android live | Evidence |
| --- | --- | --- | --- | --- |
| PR-0..PR-4 | verdict gate, BTR, provenance, Urechea, CFX | Da | Partial, prin flow-ul existent de scanare | `/v1/verify/provenance` live OK; backend tests passing |
| PR-5 | Radar hot-cache | Da | Partial real | `/v1/radar/hot-iocs` live OK; Android are cache offline, CallScreeningService si UI sync/rol. Lipseste QA device cu rol activ |
| PR-5 | Raport 1-tap | Da | Nu este conectat ca flow dedicat | `/v1/report` live OK, canale DNSC/PNRISC/Banca |
| PR-6 | Cercul out-of-band | Da | Nu are UI Android dedicat | `/v1/circle/pair`, `/ping`, `/respond`, `/revoke` live OK |
| PR-6 persist | Supabase durable state | Da | N/A | `circle_links`, `verification_pings`, `guardian_second_opinion` live OK; read-fallback adaugat in `4ba2b9b` |
| PR-6 | Guardian second opinion | Da | Nu are UI Android dedicat | `/v1/guardian/second-opinion` live OK; full fara consimtamant downgrade la metadata_only |
| PR-7 | Inbox provenance contract / BTR sync | Da ca endpoint | Foundation real | `/v1/btr/sync` live OK; Android consuma endpointul, stocheaza local si are engine on-device pe semnale locale. Nu citeste automat SMS-uri |
| PR-8 | Plan de actiune post-incident | Da | Da pentru flow de rezultat | `/v1/legal/action-plan` live OK; Android trimite impacts reale selectate si randeaza planul |
| PR-8/9 integ | `action_plan` in orchestrator + audio reference | Partial backend | Partial pentru action_plan, nu audio | Orchestratorul trimite `action_plan`; Android il afiseaza. Nu exista audio reference/on-device audio |
| Extra | DNS reputation | Da | Da indirect prin scan response | `infra_dns` live OK; flag Cloud Run activ |
| PR-9/PR-10 | Android on-device: ASR/Vosk, banda inline, captura difuzor | Nu ca feature complet | Gated sigur | `AudioSafetyPolicy` blocheaza capture by default. Nu exista inca model ASR si QA real-device |

## Gap-uri Care Nu Trebuie Numite Complete

1. Android CallScreening pentru PR-5 este implementat ca foundation, dar nu este inca validat pe device real.
   - Exista service in manifest.
   - Exista cerere `ROLE_CALL_SCREENING`.
   - Serviciul foloseste hot-cache offline, fara network in `onScreenCall`.
   - Lipseste test pe telefon/emulator cu rolul activat si apel simulat/real.

2. Android BTR sync / Inbox PR-7 este foundation, nu citire automata SMS.
   - Backend-ul ofera `/v1/btr/sync`.
   - App-ul are client Retrofit, store local si engine on-device.
   - Lipseste integrarea cu un flux real de inbox/SMS dupa decizia de produs si permisiuni.

3. Android PR-8 Action Plan este functional in ecranul de rezultat.
   - Backend-ul ofera `/v1/legal/action-plan`.
   - App-ul afiseaza `action_plan` primit in scan response.
   - App-ul permite declararea impacts reale si cere plan personalizat.

4. PR-9/PR-10 Android audio nu este implementat ca ASR, dar este blocat matur.
   - Nu exista Vosk/ASR/captura difuzor in productie.
   - `AudioSafetyPolicy` blocheaza capture fara feature flag, consimtamant, disclosure si model.

5. Gate/UX pentru `urlz.fr/rZrw` merita decis explicit.
   - Tehnic scanarea se inchide corect, preview explica `final_url_unresolved`, DNS detecteaza `registrar_suspended`.
   - User-facing label este `UNVERIFIED/info`; daca produsul vrea fail-safe mai vizibil, regula trebuie ajustata la `SUSPECT` pentru shortener + final unresolved + DNS suspended.

## Ce E Production-Grade Acum

- Backend scan pipeline nu mai ramane blocat la provider errors cunoscute.
- Malformed URL port nu mai crapa scanarea.
- Preview fallback queryless functioneaza pentru YOXO.
- DNS reputation este activ si verificat live.
- Supabase PR-6 tables exista live.
- Cercul PR-6 nu mai depinde strict de memoria unei singure instante Cloud Run.
- Android afiseaza planul de actiune preventiv PR-8 cand backend-ul il include in scan response.
- Android poate sincroniza Radar hot-cache si BTR de pe domeniul oficial.
- Android are CallScreeningService offline-first; nu face network in timpul apelului.
- Android poate cere plan post-incident personalizat pe impacts reale.
- Android audio capture este blocat by default prin policy testat.
