# Security Notes

Acest worker trebuie tratat ca proces care deschide pagini ostile.

## Izolare recomandată

Rulare recomandată în container separat:

```bash
docker run --rm \
  --network bridge \
  --cap-drop=ALL \
  --security-opt=no-new-privileges \
  -v $PWD:/work \
  -w /work \
  node:22-bookworm \
  bash -lc "npm ci && npx playwright install --with-deps chromium && node src/index.js --email-source ./emails"
```

În producție, nu rula workerul în aceeași rețea cu servicii interne sensibile. Route handlerul blochează IP-uri private, dar izolarea de rețea rămâne obligatorie. Centura + airbag, nu centură din ață.

## Blocare IP-uri interne

Workerul rezolvă DNS pentru fiecare request și blochează:

- localhost / loopback
- link-local
- private IPv4: 10/8, 172.16/12, 192.168/16
- cloud metadata 169.254/16
- IPv6 loopback / unique local / link local / reserved

## Comportament pagini

Workerul:

- auto-dismiss dialogs;
- nu face click;
- nu completează formulare;
- nu acceptă downloaduri;
- blochează navigarea către extensii executabile comune;
- timeout hard per navigation.

## Limitări

- DNS rebinding poate fi complicat; de aceea workerul verifică fiecare request, nu doar hostul inițial.
- O pagină poate servi conținut benign în momentul capturii și malițios ulterior. Cache-ul nu este verdict absolut.
- Full-page screenshot poate include cookie banners; este acceptabil pentru preview.
- URL-urile marcate `privacy_skipped`, `skipped` sau `blocked` nu sunt persistate și nu primesc alias.
- GitHub Actions este limitat la seed-ul public oficial; nu este worker on-demand pentru URL-uri de la utilizatori.
