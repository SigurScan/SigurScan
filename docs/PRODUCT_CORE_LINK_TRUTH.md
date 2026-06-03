# SigurScan Product Core - Link Truth

Data: 2026-06-02

Acesta este principiul central al produsului. Daca spec-urile tehnice devin prea complicate, revenim aici.

## Intrebarea Principala

Linkul duce unde pretinde mesajul ca duce?

Pentru user, produsul trebuie sa raspunda simplu:

- cine pretinde mesajul ca este;
- unde duce linkul real;
- daca destinatia finala este oficiala sau partener valid;
- daca i se cere userului o actiune sensibila;
- ce trebuie sa faca mai departe.

## Regula De Aur

```text
Claimed brand != final official/partner domain
+ user is asked to act
= Nu continua
```

Regula mai stricta:

```text
Claimed brand != final official/partner domain
+ asks for card / OTP / password / login / payment / CNP / IBAN / APK / remote access
= Nu introduce date sau Nu continua
```

## Ce Inseamna Asta Practic

Mesajul pretinde un brand sau o institutie.

Noi extragem linkul real, inclusiv linkul ascuns sub buton, imagine, tracking URL sau redirector.

Urmam redirecturile pana la destinatia finala.

Comparam final domain cu domeniile oficiale si partenerii validati.

Daca final domain nu se potriveste cu brandul pretins si mesajul cere o actiune, verdictul trebuie sa fie clar.

## Exemple De Decizie

Uber:

- zice Uber si duce la `uber.com` sau tracking valid cu fallback Uber -> `Poti continua cu prudenta`;
- zice Uber si duce la `uber-promo-login.xyz` -> `Nu continua`;
- zice Uber si cere login/card/OTP pe domeniu neoficial -> `Nu introduce date`.

FAN Courier:

- zice FAN si duce la `fancourier.ro` / `selfawb.ro` / partener valid -> `Poti continua cu prudenta`;
- zice FAN si duce la `fan-colet-plata.top` -> `Nu continua`;
- zice FAN si cere plata/card pe domeniu neoficial -> `Nu introduce date`.

ANAF:

- zice ANAF si duce la `anaf.ro` / `mfinante.gov.ro` / canal oficial validat -> `Poti continua cu prudenta`;
- zice ANAF si duce la domeniu necunoscut fara cerere de date -> `Verifica pe canalul oficial`;
- zice ANAF si cere date/plata/login pe domeniu neoficial -> `Nu introduce date` sau `Nu continua`.

Revolut / banca:

- zice Revolut/BT/BCR/ING si cere OTP/parola prin raspuns -> `Nu raspunde`;
- zice banca si linkul final nu este domeniu oficial/partener valid -> `Nu continua`;
- zice banca si cere login/card/OTP pe domeniu neoficial -> `Nu introduce date`.

## Cele 5 Module Necesare

1. Brand Claim Detection

Detecteaza cine pretinde mesajul ca este: Uber, eMAG, ANAF, FAN, Revolut, banca, curier, marketplace etc.

2. Final URL Resolver

Extrage linkul real si urmareste redirecturile pana la final URL. Aici urlscan/preview/redirect chain sunt moat-ul nostru vizual.

3. Official Domains Registry

Lista domeniilor oficiale si a partenerilor/tracking domains validate. Fara aceasta lista, marketingul real poate fi confundat cu scam.

4. Sensitive Intent Detection

Detecteaza daca mesajul sau pagina cere card, CVV, OTP, parola, CNP, IBAN, login, plata, APK, remote access sau raspuns cu cod.

5. Fallback

Daca nu putem afla final URL sau nu avem destule dovezi, nu inventam verdict.

Verdict corect:

- `Nu pot verifica suficient`;
- sau `Verifica pe canalul oficial`.

## Rolul Web Risk / urlscan / VirusTotal

Aceste surse sunt intaritoare, nu inlocuiesc intrebarea principala.

Web Risk:

- daca raporteaza phishing/malware -> `Nu continua`;
- daca spune no-match -> nu inseamna safe.

urlscan:

- arata final URL, redirect chain si preview;
- daca observa phishing/formular sensibil/malware -> `Nu continua`;
- daca pare clean -> nu inseamna safe absolut.

VirusTotal:

- fallback cand Web Risk/urlscan sunt incomplete sau exista conflict;
- high-confidence malicious -> `Nu continua`;
- low/no detection -> nu anuleaza semnale structurale puternice.

## Ce Nu Este Dovada Suficienta

Aceste semnale nu pot produce singure verdict grav:

- "Nu rata";
- "ultima sansa";
- "voucher";
- "reducere";
- "promotie";
- buton in email;
- link ascuns sub buton;
- tracking link;
- shortener;
- redirect simplu;
- RAG/corpus similar;
- user report neconfirmat.

Ele sunt context. Dovada reala este destinatia finala, identitatea brandului, cererea de actiune sensibila si reputatia tehnica.

## Formula Finala

```text
Input user
-> extragem brand claim + linkuri reale
-> rezolvam final URL
-> verificam official/partner registry
-> detectam intent sensibil
-> imbogatim cu Web Risk / urlscan / VT
-> EvidenceGate decide
-> UI spune actiunea simpla
```

## Principiul Brutal

SigurScan nu este un AI care decide daca un mesaj "suna a scam".

SigurScan este un detector de adevar al linkului:

```text
Iti arata unde duce linkul cu adevarat
si iti spune daca acel loc se potriveste cu ce pretinde mesajul.
```

Acesta este moat-ul produsului.
