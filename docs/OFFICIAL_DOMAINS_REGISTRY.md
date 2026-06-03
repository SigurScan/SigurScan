# SigurScan Official Domains Registry

Ultima actualizare: 2026-06-02

Scop: registru de domenii oficiale folosit pentru brand consistency si false-positive prevention. Acest document nu este blacklist. Este allowlist prudenta.

## Reguli de folosire

- Domeniul oficial reduce riscul doar daca restul dovezilor sunt coerente.
- Domeniul oficial nu inseamna `100% safe`.
- Tracking redirect este permis doar daca fallback/final URL ajunge pe domeniu oficial.
- Domeniile din registry trebuie testate in corpus cu cazuri reale si fake.
- Nu adauga domenii largi de tracking ca oficiale globale (`sng.link`, `bit.ly`, `t.co`). Se valideaza fallback-ul, nu wrapper-ul.

## Registry initial

### Uber

- `uber.com`
- `uber.link`
- `ubereats.com`

Tracking acceptat conditionat:

- `sng.link`, doar daca `_fallback_redirect` sau deep link-ul confirma Uber.

### eMAG

- `emag.ro`
- `emag.delivery`

### FAN Courier

- `fancourier.ro`
- `fanbox.ro`
- `fan-courier.ro`
- `selfawb.ro`

### Poșta Romana

- `posta-romana.ro`

### ANAF / Ministerul Finantelor

- `anaf.ro`
- `mfinante.gov.ro`
- `mfinante.ro`

### Bancar

- `revolut.com`
- `revolut.me`
- `ing.ro`
- `ing.com`
- `ingbusiness.ro`
- `bcr.ro`
- `george.bcr.ro`
- `bancatransilvania.ro`
- `btpay.ro`
- `neo-bt.ro`
- `neo.bancatransilvania.ro`

### Remote access legitim

- `anydesk.com`
- `teamviewer.com`

Nota: remote access poate fi legitim, dar contextul in care cineva cere instalarea lui poate fi fraudulos.

### WhatsApp

- `whatsapp.com`
- `web.whatsapp.com`
- `wa.me`
- `whatsapp.net`

### Google

- `google.com`
- `google.ro`
- `android.com`
- `developer.android.com`
- `youtube.com`
- `gmail.com`

## Proces de adaugare domeniu

1. Adauga domeniul in registry.
2. Adauga cel putin un caz legitim in corpus.
3. Adauga cel putin un caz fake asemanator.
4. Adauga test care verifica false-positive prevention.
5. Actualizeaza `ScamRules.TRUSTED_OFFICIAL_DOMAINS` sau backend registry.

