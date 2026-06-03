# SigurScan Android - iOS parity audit

Ultima analiza: 2026-06-01

Update 2026-06-01:

- Au fost adaugate token-uri `SigurColors` in `ui/theme/Color.kt`, aliniate cu iOS `AppTheme`.
- `SigurScanTheme` foloseste acum schema light SigurScan si dynamic color este dezactivat implicit.
- Shell-ul Compose, bottom navigation, header-ul, CyberHero card, alertele active, input-ul de scanare, butoanele de fisiere, rezultatul, Radar, Educatie, More, Family, History, Urgenta, Rapoarte si About au fost migrate din dark hardcoded catre token-uri light.
- Input-ul de scanare are acum parity mai buna cu iOS: `Lipeste`, `Sterge` si contor de caractere.
- URL-urile simple folosesc endpoint-ul dedicat `/v1/scan/url`.
- Build verificat cu JDK-ul bundled Android Studio: `BUILD SUCCESSFUL`.

Referinta iOS: `/Users/vaduvageorge/Desktop/NuApasa/docs/FUNCTIONALITY_INVENTORY.md`

Proiect Android: `/Users/vaduvageorge/AndroidStudioProjects/SigurScan`

## Verdict scurt

Android are un MVP functional, dar nu este inca 1:1 cu iOS. Structura cu 5 tab-uri exista, multe fluxuri exista partial, iar migrarea catre design system light iOS a inceput. Inca lipsesc mai multe blocuri majore: threat intelligence complet, familie cloud si push real.

## Paritate existenta

- 5 tab-uri bottom navigation: Scaneaza, Radar, Urgenta, Educatie, Mai Mult.
- Share intent Android pentru text, HTML, email, imagine, PDF si fisiere generice.
- Deep link `sigurscan://scan`.
- Scanare text/link prin backend.
- Upload imagine/PDF/email prin backend.
- OCR local cu ML Kit ca fallback pentru imagine.
- QR scan din imagine cu ML Kit Barcode.
- Istoric local in SharedPreferences.
- Triage cu checklist si progres persistat.
- Educatie statica cu quiz si progres persistat.
- Familie locala cu membri, alerte si scor protectie.
- Readiness/quality/samples/reputation stats partial.
- Radar cu campanii backend si fallback local; Supabase Realtime direct din client este scos pentru release.
- Sandbox urlscan.io cu polling si screenshot.
- Contrast checker minimal.

## Gap-uri majore fata de iOS

### Scaneaza

- Android are camera live QR cu preview, permisiune camera, torch și debouncing (implementat pentru MVP).
- QR-ul Android a fost completat și din imagine, și live.
- URL-urile simple folosesc acum `/v1/scan/url`, ca iOS.
- Input-ul Android are acum paste explicit, clear si contor caractere, ca iOS.
- Fallback PDF local este completat: OCR local + extragere linkuri din PDF annotations (`/URI`) + fallback testat.
- Email/HTML fallback exista, iar parserul de link-uri a fost extins pentru a detecta butoane/JS:
  - se parcurg taguri `a`, `button`, `input`, `form`, `area`, `iframe`, `img`, `object`, `meta`
  - se citește `onclick`, `onmouseover`, `onsubmit`, `onload`, `formaction`, `action`, `href`, `src`
  - se desfac redirecționări JS simple (`location`, `window.location`, `window.open`) și URL-uri în `style`
  - se încearcă decodări din `atob(...)` și `decodeURIComponent(...)` în handler-ele JS
- Threat intel client-side există prin Google Web Risk și VirusTotal, dar cheile trebuie mutate pe backend/proxy înainte de release.
- Analiza ofertei nu foloseste Mistral client-side ca iOS; depinde de backend/fallback text.

### Rezultat scanare

- Android afiseaza rezultatul inline in tab, iOS il afiseaza ca sheet mare.
- Modelele Android sunt mai sarace si folosesc mult `Map<String, Any>`, deci sunt fragile la schimbari de JSON.
- Nu exista echivalent complet pentru `ScanResult` iOS.

### Radar

- Android are harta embedded în Radar (Leaflet prin WebView) cu markers și card contextual la selectare.
- Nu avea pull-to-refresh; a fost adăugat buton de reîmprospătare rapidă.
- Deschide coordonatele in app externa de harti.

### Urgenta

- Functionalitatea exista si este chiar mai buna la persistenta decat iOS.
- Continutul trebuie aliniat exact cu pasii iOS daca vrem copy parity.

### Educatie

- Android are lecții extinse (8+), iar conținutul de bază acoperă punctele-cheie din iOS.
- Lipsesc sfatul zilnic si progresul vizual complet ca iOS.

### Mai Mult / Settings

- Android combina multe sectiuni intr-un singur scroll, in timp ce iOS are navigatie pe sub-ecrane.
- Istoric, Family, Readiness, About si Contrast Checker nu sunt separate ca pe iOS.

### Family

- Android Family este local-only.
- iOS are cod CloudKit, chiar daca incomplet configurat.
- Lipseste pairing/invitatie reala pe Android.

### Share / extensii sistem

- Android are share intent, nu un ecran dedicat tip Share Extension.
- Share-ul text/HTML din email/messaging este preluat și prin `EXTRA_HTML_TEXT`, nu doar prin `EXTRA_TEXT`.
- Pentru text/HTML partajat, Android are flow de confirmare (banner de revizuire înainte de scanare).
- Pentru fișiere partajate, Android stochează într-o coadă și permite scanare manuală pe fiecare item.
- Nu exista echivalent Android pentru SMS Filter iOS (în aceeași formă de extensie).
- Notification Listener exista, dar doar logheaza riscul; nu protejeaza activ utilizatorul.

### Visual design

- iOS foloseste tema light `AppTheme` cu canvas deschis si carduri albe.
- Android are acum `SigurColors` si `SigurScanTheme` light aliniate cu iOS.
- Migrarea vizuala principala este facuta pe token-uri light pentru ecranele mari si cardurile principale.
- Pentru 1:1 vizual complet mai trebuie rafinate spacing-ul, shadow/elevation, radius-urile, teste UI și separarea componentelor din `MainActivity.kt` în module.

## Riscuri tehnice

- Chei hardcodate in client: urlscan.io si Supabase.
- urlscan.io foloseste acum `visibility: unlisted` cu sanitizare de URL inainte de submit.
- SharedPreferences migrate către EncryptedSharedPreferences pentru datele locale sensibile (fallback la standard dacă hardware/keychain nu e disponibil).
- `android:allowBackup` a fost dezactivat (`false`), dar rămân recomandări de hardening suplimentar pe backup/cloud.
- Loggingul URL/text a fost redus la nivel `NONE`, dar trebuie verificat și în release.
- Cheile URLScan/VT/Web Risk sunt încă dependente de BuildConfig în local; recomandat backend proxy.
- Build verificat cu JDK-ul bundled Android Studio: `BUILD SUCCESSFUL`.

## Prioritate recomandata pentru portare 1:1

1. [DONE] QR live cu CameraX + ML Kit Barcode + torch.
2. Mutare ecrane din `MainActivity.kt` in fisiere separate.
3. [DONE] Radar cu hartă embedded (WebView + Leaflet + markers) și card contextual la tap.
4. Lectiile Android completate la aceleasi 6 ca iOS.
5. Contrast Checker complet ca iOS.
6. Threat intel: Google Web Risk + VirusTotal.
7. Persistenta mai sigura: EncryptedSharedPreferences/Room si backup rules.
8. Fallback PDF local cu text/link extraction (realizat; testat în unități).
9. Family cloud/pairing sau backend shared cu iOS.
10. Push/notification protection clarificata si implementata real.
