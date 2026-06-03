# SigurScan Evidence Gate Matrix

Ultima actualizare: 2026-06-02

Scop: matricea determinista care decide verdictul pe baza de dovezi. Daca un comportament nu este aici sau in corpus, nu il transformam in regula de productie fara test.

## Semnale slabe

Semnalele slabe sunt context. Singure nu pot produce `DANGEROUS`.

Exemple:

- `azi doar`;
- `ultima sansa`;
- `nu rata`;
- `profita acum`;
- `voucher`;
- `reducere`;
- `promotie`;
- link sub buton;
- tracking link;
- link scurt fara alta dovada;
- email de marketing cu CTA.

Actiune maxima din semnale slabe singure:

- `LOW_RISK`, daca restul dovezilor sunt coerente;
- `UNKNOWN`, daca nu avem final URL/reputatie;
- niciodata `DANGEROUS`.

## Semnale medii

Semnalele medii pot produce `SUSPICIOUS`, mai ales in combinatie.

Exemple:

- brand mentionat, dar linkul principal este pe domeniu neoficial;
- redirect chain neobisnuit;
- domeniu foarte nou;
- shortener/tracker fara fallback oficial;
- email auth lipsa sau neclar pentru brand sensibil;
- sender/reply-to mismatch;
- IDN/confusables;
- domeniu necunoscut intr-un context de plata/logare/livrare;
- urlscan neclar sau inca in procesare;
- VirusTotal `suspicious` fara confirmare puternica.

Output recomandat:

- `Verifica pe canalul oficial`;
- `Nu pot verifica suficient`, daca nu avem final URL sau preview.

## Semnale puternice

Semnalele puternice pot produce `DANGEROUS`.

Exemple:

- Google Web Risk confirma phishing/malware/social engineering;
- DNSC/blacklist match;
- urlscan verdict malicious;
- VirusTotal malicious cu motoare relevante;
- brand mismatch clar plus final URL cere card, OTP, parola, CNP, IBAN sau login;
- form action trimite date catre domeniu neoficial;
- link vizibil promite domeniu oficial, dar final URL duce in alta parte si cere date;
- pagina finala cere remote access sau download APK neoficial;
- homograph/confusable pe brand financiar/guvernamental plus cerere de date.

Output recomandat:

- `Nu apasa`;
- `Nu introduce date`;
- `Nu raspunde`, pentru emailuri care cer raspuns cu date.

## LOW_RISK

Conditii minime:

- domeniul final este oficial sau tracking legitim catre domeniu oficial;
- Web Risk este clean sau nu are semnale;
- urlscan nu are verdict malicious, cand exista;
- pagina nu cere date sensibile pe domeniu neoficial;
- brand/context/link sunt coerente;
- nu exista blacklist match.

Text user:

- `Poti continua cu prudenta`
- `Nu am gasit semnale cunoscute de risc`

Nu folosi:

- `100% sigur`
- `garantat legitim`
- `site sigur`

## SUSPICIOUS

Conditii:

- brand mismatch fara cerere clara de date;
- redirect chain dubios;
- domeniu necunoscut plus context sensibil;
- Web Risk clean, dar exista semnale medii;
- urlscan inca neclar, dar contextul cere prudenta.

Text user:

- `Verifica pe canalul oficial`
- `Verifica direct in aplicatia sau site-ul oficial`

## DANGEROUS

Conditii:

- cel putin un semnal puternic confirmat;
- sau doua semnale medii independente plus intent sensibil clar.

Text user:

- `Nu apasa`
- `Nu introduce date`
- `Nu trimite coduri OTP`

## UNKNOWN

Conditii:

- final URL nu poate fi determinat;
- urlscan nu este gata si nu exista surse suficiente;
- sursele se contrazic;
- inputul contine doar text vizibil fara link/HTML/header suficient;
- avem tracking link, dar nu putem valida fallback-ul.

Text user:

- `Nu pot verifica suficient`
- `Verifica pe canalul oficial pana avem destinatia finala`

## Reguli anti false-positive

Nu clasifica drept scam doar pentru:

- marketing urgency;
- buton in email;
- tracking link;
- newsletter;
- link scurt;
- brand mentionat in text fara link sensibil;
- `voucher` sau `reducere`.

Pentru orice regula noua care creste riscul, adauga mai intai cazuri in corpus si acceptance tests.
