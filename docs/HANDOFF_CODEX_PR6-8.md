# Handoff Codex — PR-6 / PR-7 / PR-8 (backend gata, infra de finalizat)

Branch: `feature/osint-intel-pipeline`. Codul de backend e scris, testat și
împins (suită verde). Acest document listează DOAR ce nu poate face Claude
(nu are cheile Supabase / acces Cloud Run / Cloudflare) și rămâne în sarcina Codex.

Context infra existent (nu rescrie, doar aplică):
- [docs/CLOUD_RUN_MIGRATION_PLAN.md](CLOUD_RUN_MIGRATION_PLAN.md)
- [docs/CLOUDFLARE_API_DOMAIN.md](CLOUDFLARE_API_DOMAIN.md)

---

## Ce e DEJA făcut în backend (de Claude)

| PR | Cod | Endpoints | Teste |
| --- | --- | --- | --- |
| PR-6 Cercul | `services/circle_verification.py` + persistență write-through în `services/supabase_store.py` | `/v1/circle/pair\|ping\|respond\|revoke`, `/v1/guardian/second-opinion` | `test_circle_verification.py` (31) |
| PR-7 Inbox | `services/inbox_provenance.py` | `GET /v1/btr/sync` | `test_inbox_provenance.py` (16) |
| PR-8 Legal L2 | `services/legal_action_plan.py` | `POST /v1/legal/action-plan` | `test_legal_action_plan.py` (16) |

Persistența Cercului e **write-through best-effort**: fără `SUPABASE_URL` +
`SUPABASE_SERVICE_ROLE_KEY` toate apelurile sunt no-op (backend-ul merge identic).
Cu cheile + migrarea aplicată, datele devin durabile.

---

## 1. Supabase — ce trebuie făcut (Codex are cheile, Claude NU)

### 1.1 Aplică migrarea PR-6
Fișier: `supabase/migrations/20260614000000_create_circle_verification_tables.sql`
Creează: `circle_links`, `verification_pings`, `guardian_second_opinion`
(id-uri `text`, prefixate `cl_/vp_/go_` de backend; RLS enabled).

> **Stare verificată live (2026-06-14), proiect `hslqboubacrdhatmqcky`:**
> conexiunea REST cu service role key răspunde (`scan_events` → 200), DAR cele 3
> tabele ale Cercului încă **NU există** (`circle_links`/`verification_pings`/
> `guardian_second_opinion` → 404). Deci persistența write-through e gata în cod,
> dar așteaptă aplicarea migrării. Service role key NU poate face DDL (PostgREST);
> e nevoie de DB password / dashboard / CLI linkat.

```bash
# Varianta A (recomandat) — doar tabelele Cercului, fără să atingi alte migrări:
#   Supabase Dashboard → SQL Editor → paste conținutul fișierului de mai sus → Run
# Varianta B — CLI (ATENȚIE: aplică TOATE migrările nepuse din folder):
supabase db push --project-ref hslqboubacrdhatmqcky
```

Verifică după aplicare:
```sql
select count(*) from public.circle_links;          -- trebuie să existe (0 rânduri ok)
select count(*) from public.verification_pings;
select count(*) from public.guardian_second_opinion;
```

> Migrarea anterioară `20260613000000_create_persistence_tables.sql` conține un
> `circle_link` (singular) = graful de corelare INTEL, alt concept. Nu le confunda:
> Cercul uman folosește tabelele PLURAL din migrarea nouă.

### 1.2 Env vars pe serviciu (Cloud Run / Vercel)
Backend-ul citește (vezi `services/supabase_store.py`):
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- (opțional) `SUPABASE_TIMEOUT_SECONDS` (default 4.0)

Fără ele → Cercul rulează in-memory per-proces (ok pt dev, NU pt prod multi-instanță).

### 1.3 RLS / policies
Tabelele au `enable row level security` dar NU au policies definite → cu
`service_role` (backend) merge oricum (bypass RLS). Dacă vreun client accesează
direct cu `anon key`, definește policies restrictive. Recomandat: acces DOAR prin
backend (service_role), zero acces direct din client la aceste tabele
(conțin grafa Cercului).

---

## 2. Read-fallback cross-instanță (decizie + cod — rămâne de făcut)

Acum persistența e **write-through** (scrie în Supabase), dar citirile
(`get_link`, `get_ping`) sunt DOAR din memoria procesului. Pe Cloud Run cu
>1 instanță, un `pair` pe instanța A + `respond` pe instanța B → 404.

**De decis de Codex/owner:**
- (a) Cloud Run cu `max_instances=1` pentru aceste rute (simplu, dar nu scalează), SAU
- (b) adaugă read-fallback din Supabase în `CircleStore.get_link/get_ping` când
  lipsește din memorie (parsează rândul înapoi în dataclass). Cod + teste necesită
  DB live de validat — de aceea l-am lăsat pe seama ta.

Recomandare: (b) înainte de a porni Cercul în prod cu trafic real.

---

## 3. Cloud Run — ce ține de tine (Claude nu are acces)

Vezi planul complet: [CLOUD_RUN_MIGRATION_PLAN.md](CLOUD_RUN_MIGRATION_PLAN.md).
Specific pentru PR-6..8:
- Deploy `backend/main.py` (FastAPI) ca `sigurscan-api` cu env-urile Supabase de la §1.2.
- **Decizia `min_instances` (golul #3 din MoatOS §12):** free-first presupune
  `min_instances=0`, dar infra live rulează `minScale=1` (~$5-10/lună). Alege:
  cobori la 0 pentru free-first, sau accepți baseline-ul. Nu e decizie de cod.
- Noile rute nu adaugă dependențe noi (zero provideri externi în PR-6/8;
  PR-7 `/v1/btr/sync` doar citește registrul local din `data/`).

---

## 4. Cloudflare — ce ține de tine

Vezi [CLOUDFLARE_API_DOMAIN.md](CLOUDFLARE_API_DOMAIN.md). Noile endpoint-uri sunt
sub același host `api.sigurscan.com` → **nu necesită config nou de domeniu**.
Doar confirmă că Worker-ul nu blochează metodele/path-urile noi:
`/v1/circle/*`, `/v1/guardian/second-opinion`, `/v1/btr/sync`, `/v1/legal/action-plan`.

---

## 5. Smoke-test live după deploy (Codex, cu DB+domeniu reale)

```bash
BASE=https://api.sigurscan.com
# PR-6 flow
LINK=$(curl -s $BASE/v1/circle/pair -H 'content-type: application/json' \
  -d '{"protected_id":"u_g","verifier_id":"u_s","consent":"explicit"}' | jq -r .link_id)
PING=$(curl -s $BASE/v1/circle/ping -H 'content-type: application/json' \
  -d "{\"link_id\":\"$LINK\"}" | jq -r .ping_id)
curl -s $BASE/v1/circle/respond -H 'content-type: application/json' \
  -d "{\"ping_id\":\"$PING\",\"response\":\"its_me\"}"        # -> {"status":"CONFIRMED",...}
# PR-7
curl -s "$BASE/v1/btr/sync" | jq '.count, .version'
# PR-8
curl -s $BASE/v1/legal/action-plan -H 'content-type: application/json' \
  -d '{"verdict":"DANGEROUS","impacts":["shared_card","paid_transfer"],"family":"CONV_BANK_SAFE_ACCOUNT"}' | jq '.steps[0].urgency'
```
Apoi verifică în Supabase că `circle_links` / `verification_pings` au primit rânduri.

---

## 6. Ce NU se face (linii roșii — valabile și pentru Codex)

- **NICIUN endpoint care primește conținut SMS sau audio brut** (MoatOS §8/§13/§14).
  PR-7 trimite DOAR manifeste în jos (`/v1/btr/sync`); verdictul SMS se calculează
  on-device (Android portează `inbox_provenance.build_inbox_verdict`).
- Nu promova manifeste BTR la `confidence: high` fără sursă primară (gol #1, §12).
- Nu publica IOC/numere brute; doar hash-uri/buckets.

---

## 7. Rămâne Android (nu e backend, doar referință)

- PR-7 UI: rol SMS pe profilul protejat, citire on-device, bandă inline,
  portarea `build_inbox_verdict` în Kotlin, cache BTR local din `/v1/btr/sync`.
- PR-9/PR-10: stack audio on-device (Vosk RO + VAD), captură difuzor, consimțământ
  per-apel, zero upload audio. Logica de verdict e gata ca referință în
  `services/audio_evidence.py` (`build_audio_case_verdict`, reuse verdict_gate,
  STT-solo→max SUSPECT) — Android o portează on-device. INTENȚIONAT fără endpoint
  audio pe server (§14.5).
- TriageScreen care consumă `/v1/legal/action-plan`. Pe ruta ofertă, `result.action_plan`
  vine deja preventiv (impacts=["none"]); ecranul re-cere cu impacts reale după ce
  userul spune ce a făcut.

---

## 8. Provideri URL — chei expirate + pilon DNS nou (verificat live)

### 8.1 Chei provider — OK în prod (verificat de Codex live)
Cheile **Google Web Risk** și **URLhaus** funcționează în producție (testate live de Codex).
⚠️ Atenție: copia locală `backend/.env.vercel` a întors `API_KEY_INVALID` /
`unknown_auth_key` la un test local — deci **fișierul local e stale/diferit de prod**;
nu vă bazați pe el pentru cheile providerilor, sursa de adevăr e env-ul din Vercel/Cloud Run.

**Recomandare free-first (gol #3 §12), rămâne valabilă:** pentru Web Risk, treci de la
**Lookup API** (costă per-scan la scară, ~100k useri) la **Update API** (liste hash
descărcate local, match offline) — rezolvă costul și privacy-ul. Nu blochează nimic acum.

### 8.2 Pilon nou DNS reputation — `services/dns_reputation.py` (GRATIS, fără cheie)
Adăugat în pipeline, **opt-in** prin `ENABLE_DNS_REPUTATION` (implicit **OFF** → fără
latență/rețea by default). Semnale, via DNS-over-HTTPS (Cloudflare normal vs
`security.cloudflare-dns.com`), care NU vizitează site-ul:
- `blocked` (rezolvă normal dar DNS-ul de securitate îl refuză) → provider hard
  `dns_security` (malicious) → terminal, ca Web Risk/URLhaus.
- `suspended` (NS de hold la registrar, ex. `trs-dns.com`) / `nxdomain` → semnal
  ponderat `infra_dns` (severity medium, niciodată terminal solo — ca `infra_rdap`).

**De decis Codex:** activează în prod cu `ENABLE_DNS_REPUTATION=true` (e gratis,
Play-safe, fără cheie). Recomandat — tocmai a prins un domeniu real luat jos
(`flixsou.site`, suspendat pe `trs-dns.com`) pe care Web Risk/URLhaus (chei moarte)
l-ar fi ratat. Bonus: rulează și on-device (DoH e free, fără permisiuni Play).
