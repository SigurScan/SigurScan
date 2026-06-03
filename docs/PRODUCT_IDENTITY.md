# SigurScan Product Identity

## Final Android Identity

- Product name: `SigurScan`
- Store title: `SigurScan - verifică mesaje, linkuri și emailuri`
- Android applicationId: `ro.sigurscan.app`
- Android namespace: `ro.sigurscan.app`
- Deep link scheme: `sigurscan://scan`
- Release app label: `SigurScan`

## Product Promise

SigurScan este o aplicație user-initiated pentru România care verifică mesaje, linkuri, emailuri, QR-uri, poze și documente suspecte înainte ca utilizatorul să continue.

Aplicația nu monitorizează automat notificări, inbox, SMS-uri, clipboard sau apeluri. Utilizatorul decide explicit ce partajează/scanează.

## User-Facing Decisions

SigurScan trebuie să afișeze decizii simple, nu scoruri procentuale:

- `Nu continua`
- `Nu introduce date`
- `Nu răspunde`
- `Verifică pe canalul oficial`
- `Poți continua cu prudență`
- `Nu pot verifica suficient`

## Core Differentiator

Moat-ul principal este combinația:

- parsare reală de HTML/email/share intent;
- extragerea linkurilor ascunse sub butoane;
- rezolvarea URL-ului final;
- preview securizat al destinației finale;
- gate determinist bazat pe dovezi, nu pe cuvinte de marketing.

## Current Backend Note

Codul Android acceptă `SIGURSCAN_BACKEND_BASE_URL`. Până la rebrandul backend-ului, fallback-ul operațional rămâne backend-ul live existent.

Înainte de lansare publică, creează un alias/domeniu dedicat SigurScan și actualizează:

- `SIGURSCAN_BACKEND_BASE_URL`;
- Privacy Policy URL în Play Console;
- documentele de suport public.
