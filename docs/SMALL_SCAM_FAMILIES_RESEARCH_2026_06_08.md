# Small Scam Families Research 2026-06-08

Status: research supplement pentru `ROMANIA_SCAM_ATLAS_2025_2026_INTEGRATION.md`.

Scope: familii mai mici/nise care nu trebuie sa devina gate-uri separate, dar care merita adaugate in corpus, claim verifier targets si acceptance tests.

Regula de integrare: `DECISION_CONTRACT_V1.md` castiga. Aceste familii nu seteaza verdict direct; ele produc context si evidence candidates pentru reducer.

## Rezumat executiv

Familii mici de adaugat:

- F26: BVB / dividende false / Depozitarul Central.
- F27: Loteria Romana / bonus loto / aplicatie cazino falsa.
- F28: bilete false la concerte/festivaluri/sport + cazare evenimente.
- F29: chirii/apartamente false pe platforme online.
- F30: rovinieta/CNAIR/taxa drum restanta prin SMS.
- F31: phishing pentru administratori de pagini social media.
- F32: DNSC/institutii - citatii/documente oficiale false.
- F33: job online/task scam social media -> Telegram/WhatsApp.
- F34: magazine online false/clone retail in valuri sezoniere.
- F35: romance/cadouri de 8 Martie/relatie artificiala.

Acestea sunt mai mici decat ANAF/banci/curieri/OLX, dar sunt reale si utile pentru produs deoarece apar in mesaje scurte, reclame social, WhatsApp sau emailuri simple.

## Cum le folosim in contract

Pentru fiecare familie:

```text
Corpus match -> context.nearest_family
Brand/source warning -> evidence candidate
Domain check -> final_url.identity
Request classifier -> request.sensitive + request.channel
Providers -> providers.*
Reducer -> singurul verdict
```

Nu folosim:

- `familie match == PERICULOS`;
- `textul suna ca scam == PERICULOS`;
- `urgenta == PERICULOS`;
- `bonus/oferta/premiu == PERICULOS`;
- `community story == hard evidence`.

## F26 - BVB / dividende false / Depozitarul Central

### Ce am gasit

Bursa de Valori Bucuresti a publicat pe 31 decembrie 2025 o alerta despre site-uri care copiaza identitatea vizuala BVB si promit dividende false. Atacatorii cer CNP, IBAN, telefon, email si alte date sensibile. BVB precizeaza ca site-ul oficial este `www.bvb.ro`, ca distribuirea dividendelor se face prin Depozitarul Central, agenti de plata sau broker, si ca BVB nu face plati directe catre investitori.

### Surse

- BVB comunicat oficial PDF: `https://m.bvb.ro/press/2025/Comunicat%20de%20presa_Noi%20tentative%20de%20inselaciune_31122025.pdf`

### Evidence candidates

- `CLAIMED_BRAND_BVB`
- `DIVIDEND_WITHDRAWAL_CLAIM`
- `UNEXPECTED_MONEY_CLAIM`
- `BVB_DOMAIN_MISMATCH`
- `CNP_IBAN_REQUEST`
- `REMOTE_APP_FOR_DIVIDEND`

### Contract mapping

- `bvb.ro` official.
- `depozitarulcentral.ro` si brokerii trebuie tratati ca registry/partner candidates doar dupa verificare.
- Dividende false + domeniu neoficial + CNP/IBAN/card/remote app => `request.sensitive` si `identity.unrelated/lookalike`.

### Verdict conform reducer

- Provider malicious => `PERICULOS`.
- Domeniu neoficial/lookalike + CNP/IBAN/card/remote app => `PERICULOS`.
- Domeniu oficial BVB + informatie educationala fara cerere sensibila => `SIGUR` daca providerii sunt clean.
- Doar text “ai dividende” fara URL/date cerute => `SUSPECT`, nu `PERICULOS`.

### Acceptance tests

- `BVB: ai dividende de 23.000 lei. Completeaza CNP si IBAN aici: https://bvb-dividende.test` -> `PERICULOS`.
- `BVB: informare investitori. Detalii pe https://www.bvb.ro` + providers clean -> `SIGUR`.

## F27 - Loteria Romana / bonus loto / aplicatie cazino falsa

### Ce am gasit

DNSC a avertizat despre fraude care folosesc imaginea Loteriei Romane si trimit utilizatorii catre site-uri/aplicatii false, bonusuri loto si platforme de cazino. Loteria Romana a publicat si ea un avertisment pe 5 iunie 2026: informatiile oficiale sunt pe `www.loto.ro` si pe paginile oficiale social media. Exista si platforme/parteneri oficiali reale, deci nu putem bloca orice aplicatie sau bonus doar din text.

### Surse

- DNSC relatat de Digi24: `https://www.digi24.ro/amphtml/stiri/actualitate/dnsc-avertisment-cu-privire-la-fraudele-care-folosesc-imaginea-loteriei-romane-pentru-a-pacali-utilizatorii-3707761`
- Loteria Romana alerta oficiala: `https://www.loto.ro/?p=20318`
- Loteria Romana plata castiguri: `https://www.loto.ro/?page_id=1060`
- Platforme oficiale gasite: `https://joc-loto.loto.ro/`, `https://un-doi.loto.ro/`

### Evidence candidates

- `CLAIMED_BRAND_LOTERIA_ROMANA`
- `LOTTERY_BONUS_CLAIM`
- `FAKE_CASINO_APP_CLAIM`
- `APP_STORE_IMPERSONATION`
- `INITIAL_DEPOSIT_FOR_BONUS`
- `LOTO_DOMAIN_MISMATCH`

### Contract mapping

- Registry: `loto.ro`, `bilete.loto.ro`, `joc-loto.loto.ro`, `un-doi.loto.ro` ca official/partner candidates.
- Aplicatie falsa care cere depunere initiala sau instalare din afara store-ului => sensitive request.

### Verdict conform reducer

- Domeniu neoficial + depunere/card/aplicatie falsa => `PERICULOS`.
- Domeniu oficial/partener + providers clean + fara cerere sensibila gresita => `SIGUR`.
- Promisiune de bonus/castig pe social fara target tehnic => `SUSPECT`.

### Acceptance tests

- `Loteria Romana: bonus 500 lei. Instaleaza aplicatia: https://bonus-loteria.test/app` -> `PERICULOS` daca cere APK/depunere/card.
- `Informatii joc loto online pe https://joc-loto.loto.ro/` + providers clean -> `SIGUR`.

## F28 - Bilete false la concerte/festivaluri/sport + cazare evenimente

### Ce am gasit

DNSC a avertizat despre bilete ieftine la concerte si cazare de Revelion, pagini false, profiluri social media nou-create, grupuri online si plati urgente. ANPC a emis recomandari dupa cazuri de bilete false la Metallica in mai 2026: cumparare doar din surse oficiale sau distribuitori autorizati.

### Surse

- DNSC relatat de Euronews: `https://www.euronews.ro/articole/dnsc-avertizeaza-biletele-ieftine-la-concerte-si-cazare-online-de-revelion-pot-as`
- ANPC relatat de Digi24: `https://www.digi24.ro/amphtml/stiri/recomandarile-anpc-dupa-ce-multi-fani-metallica-si-fostul-sef-al-institutiei-horia-constantinescu-au-fost-pacaliti-cu-bilete-false-3769865`

### Evidence candidates

- `EVENT_TICKET_RESALE_CLAIM`
- `UNOFFICIAL_TICKET_SELLER`
- `SOCIAL_GROUP_SELLER`
- `URGENT_ADVANCE_PAYMENT`
- `TOO_GOOD_PRICE`
- `EVENT_ACCOMMODATION_ADVANCE`

### Contract mapping

- Nu exista un singur brand registry universal pentru toate evenimentele.
- Claim verifier trebuie sa caute organizator/distribuitor oficial cand brandul/evenimentul este clar.
- Community/social group = context, nu hard evidence.

### Verdict conform reducer

- Daca URL/vanzator neoficial + plata avans/card/transfer rapid => `SUSPECT` sau `PERICULOS` cand cererea de plata este clara si canalul este gresit.
- Domeniu/distribuitor oficial + providers clean => `SIGUR`.
- Doar oferta de bilet pe social fara URL/date/plata => `SUSPECT`.

### Acceptance tests

- `Vand 2 bilete Metallica, plata Revolut acum, trimit PDF dupa` -> `SUSPECT` sau `PERICULOS` daca cere plata imediata catre persoana necunoscuta.
- `Bilete disponibile pe distribuitor oficial eveniment.ro` + providers clean -> `SIGUR`.

## F29 - Chirii/apartamente false pe platforme online

### Ce am gasit

Politia Capitalei a anuntat in februarie 2026 un dosar in care persoane ofereau apartamente inexistente sau foloseau identitati false, cereau chirie + garantie, fotografii ale actelor si date pentru portofele virtuale/crypto.

### Surse

- Politia Romana / DGPMB: `https://b.politiaromana.ro/ro/stiri/perchezitii-ale-politistilor-capitalei-intr-un-dosar-de-inselaciune-si-fals-informatic1771482753`

### Evidence candidates

- `RENTAL_TOO_CHEAP`
- `ADVANCE_RENT_GUARANTEE_REQUEST`
- `ID_DOCUMENT_PHOTO_REQUEST`
- `VIRTUAL_WALLET_OR_CRYPTO_ACCOUNT_REQUEST`
- `MESSAGING_ONLY_LANDLORD`
- `FAKE_CONTRACT`

### Contract mapping

- Fara URL, acesta este text/social scam. Cererea de bani + act identitate + crypto wallet este sensitive request.
- Corpus poate explica familia, dar reducerul decide pe `request.sensitive` si canal.

### Verdict conform reducer

- Cere garantie/chirie + poza act + crypto wallet/cont virtual pe WhatsApp => `PERICULOS`.
- Doar anunt ieftin, fara cereri => `SUSPECT`.

### Acceptance tests

- `Apartament sub pretul pietei. Trimite CI si garantia acum, facem contract electronic` -> `PERICULOS`.
- `Anunt chirie cu link catre platforma imobiliara oficiala, fara cerere de date` -> `SUSPECT` sau `SIGUR` doar daca identity/providers sunt clare.

## F30 - Rovinieta / CNAIR / taxa drum restanta prin SMS

### Ce am gasit

In februarie 2026 au circulat mesaje false despre rovinieta/taxa de drum restanta, cu amenintari de amenda sau confiscare/reținere vehicul si linkuri suspecte. Relatarile mentioneaza CNAIR ca avertizand ca mesajele sunt false.

### Surse

- Adevarul despre avertizarea CNAIR: `https://adevarul.ro/stiri-interne/societate/atentie-la-sms-urile-care-va-anunta-sa-platiti-2505535.html`
- Europa FM despre SMS rovinieta: `https://www.europafm.ro/tentativa-de-frauda-prin-sms-privind-plata-unei-roviniete-autoritatile-ii-avertizeaza-pe-soferi-sa-blocheze-expeditorul/`

### Evidence candidates

- `CLAIMED_BRAND_CNAIR_ROVINIETA`
- `ROAD_TAX_RESTANȚA_CLAIM`
- `VEHICLE_CONFISCATION_THREAT`
- `URGENT_FINE_PAYMENT`
- `UNOFFICIAL_PAYMENT_LINK`

### Contract mapping

- Registry candidates de verificat: `cnadnr.ro`, `erovinieta.ro`, `roviniete.ro`, `ghiseul.ro` doar cu confirmare oficiala.
- Nu dam `PERICULOS` doar pentru cuvantul rovinieta; avem nevoie de link neoficial + plata/card sau provider malicious.

### Verdict conform reducer

- SMS rovinieta + link neoficial + plata/card => `PERICULOS`.
- Mesaj informativ despre rovinieta fara link/plata => `SUSPECT`.
- Domeniu oficial + providers clean => `SIGUR`, daca nu cere date sensibile gresit.

### Acceptance tests

- `Rovinieta neplatita. Plateste in 3 ore sau se retine vehiculul: https://rovinieta-plata.test` -> `PERICULOS` daca cere card/plata.
- `Informatii rovinieta pe domeniu oficial verificat` + providers clean -> `SIGUR`.

## F31 - Phishing pentru administratori de pagini social media

### Ce am gasit

DNSC a avertizat despre mesaje pe social media care par oficiale si solicita confirmarea drepturilor de proprietate asupra unei pagini administrate; formularul fals colecteaza date sensibile si poate duce la deturnarea paginii.

### Surse

- Radio Romania despre alerta DNSC: `https://www.radioromania.ro/Actualitate/dnsc-noi-tentative-de-frauda-prin-mesaje-trimise-pe-retelele-de-socializare-id110289.html`

### Evidence candidates

- `SOCIAL_PAGE_ADMIN_CLAIM`
- `PAGE_OWNERSHIP_CONFIRMATION`
- `FAKE_PLATFORM_FORM`
- `PASSWORD_OR_OTP_REQUEST`
- `SOCIAL_ACCOUNT_TAKEOVER`

### Contract mapping

- Daca formularul este pe domeniu Meta/Google/etc oficial si providers clean, nu e automat risc.
- Daca linkul este neoficial si cere parola/OTP/session token => sensitive request.

### Verdict conform reducer

- Link neoficial + parola/OTP/date autentificare => `PERICULOS`.
- Mesaj vag despre pagina, fara URL sau date cerute => `SUSPECT`.

### Acceptance tests

- `Meta Business: confirma drepturile paginii tale aici https://meta-page-appeal.test/login` -> `PERICULOS`.
- `Notificare Meta in app oficiala, fara link extern` -> `SIGUR` daca target oficial.

## F32 - DNSC/institutii: citatii/documente oficiale false

### Ce am gasit

Au aparut tentative care folosesc identitatea DNSC sub forma unor citatii/documente oficiale sau mesaje urgente, cu domenii/adrese care nu apartin institutiei si linkuri catre pagini/documente suspecte. Pentru DNSC, domeniile importante sunt `dnsc.ro`, `pnrisc.dnsc.ro` si platforma blacklist noua mentionata in 2026.

### Surse

- Digi24 despre citatie falsa DNSC: `https://www.digi24.ro/stiri/actualitate/tentativa-de-frauda-in-numele-dnsc-sub-forma-unei-citatii-oficiale-nu-raspundeti-si-nu-divulgati-informatii-3273731`
- StiriPeSurse/AGERPRES despre PNRISC blacklist: `https://www.stiripesurse.ro/dnsc-simplifies-reporting-process-for-cyber-security-incidents_3881569`
- Eveniment de Olt despre mesaje frauduloase in numele DNSC: `https://evenimentdeolt.ro/2026/05/14/mesaje-frauduloase-in-mediul-online-care-folosesc-in-mod-abuziv-numele-si-elemente-de-identitate-vizuala-ale-dnsc/`

### Evidence candidates

- `CLAIMED_BRAND_DNSC`
- `OFFICIAL_CITATION_OR_LEGAL_DOCUMENT`
- `URGENT_DOCUMENT_DOWNLOAD`
- `DNSC_DOMAIN_MISMATCH`
- `ASKS_PERSONAL_DATA_OR_PAYMENT`

### Contract mapping

- Registry: `dnsc.ro`, `pnrisc.dnsc.ro`.
- DNSC blacklist este provider/corpus source candidate, nu verdict absolut fara confirmare API/format.

### Verdict conform reducer

- Domeniu neoficial + document/citatie + date/plata/download suspect => `PERICULOS`.
- Domeniu oficial DNSC/PNRISC + providers clean + informare => `SIGUR`.

## F33 - Job online / task scam social -> Telegram/WhatsApp

### Ce am gasit

DNSC a avertizat despre mesaje care ofera joburi online si campanii raportate in Romania/strainatate. Modelele internationale si comunitare arata aceeasi structura: taskuri usoare, plata mica initiala, mutare pe Telegram/WhatsApp, apoi cerere de depuneri/crypto pentru a debloca castiguri.

### Surse

- Forbes despre avertisment DNSC: `https://www.forbes.ro/avertisment-dnsc-atentie-la-mesajele-care-ofera-job-uri-online-o-noua-tentativa-de-frauda-cibernetica-420987`
- Reddit r/Scams/task scam ca pattern community/noisy: `https://www.reddit.com/r/Scams/comments/1o5ur4d`

### Evidence candidates

- `ONLINE_JOB_OFFER_UNSOLICITED`
- `TASKS_FOR_MONEY`
- `TELEGRAM_WORKFLOW`
- `ADVANCE_DEPOSIT_TO_UNLOCK`
- `CRYPTO_DEPOSIT`
- `MONEY_MULE_REQUEST`

### Contract mapping

- Community confirms realism only.
- Cererea de depozit/crypto/cont bancar/acte devine sensitive request.

### Verdict conform reducer

- Job + Telegram + depunere/crypto/card => `PERICULOS`.
- Job online vag fara cereri => `SUSPECT`.

## F34 - Magazine online false / clone retail

### Ce am gasit

DNSC a avertizat in 2026 despre un val de fraude prin linkuri catre site-uri false si platforme de cumparaturi online, cu colectare date card si branduri cunoscute. Aceasta familie este diferita de giveaway/voucher: este magazin fals sau clonat.

### Surse

- Playtech despre avertisment DNSC: `https://playtech.ro/2026/dnsc-avertizeaza-asupra-unui-val-de-tentative-de-frauda-online-prin-linkuri-catre-site-uri-false/`
- PNRISC blacklist lansat in 2026: `https://www.digi24.ro/stiri/sci-tech/lumea-digitala/cum-verifici-daca-un-site-este-periculos-dnsc-lanseaza-o-platforma-de-tip-blacklist-si-simplifica-raportarea-incidentelor-3747693`

### Evidence candidates

- `FAKE_ONLINE_STORE`
- `CLONED_RETAIL_BRAND`
- `UNREALISTIC_DISCOUNT`
- `CARD_CHECKOUT_ON_UNRELATED_DOMAIN`
- `DNSC_BLACKLIST_HIT`

### Contract mapping

- Reducer se bazeaza pe identity/provider/request.
- Discountul singur nu decide.

### Verdict conform reducer

- Provider/blacklist malicious => `PERICULOS`.
- Domeniu neoficial + card checkout => `PERICULOS`.
- Domeniu necunoscut + providers clean fara plata inca => `SUSPECT`.

## F35 - Romance / cadouri / 8 Martie / relatie artificiala

### Ce am gasit

DNSC si SigurantaOnline au avertizat ca in jurul zilei de 8 Martie se intensifica fraudele cu mesaje emotionale, cadouri false, notificari fictive de livrare si romance scam. Aceasta familie este deja in atlas, dar trebuie extinsa ca subfamilie sezoniera.

### Surse

- TVR despre avertisment DNSC 8 Martie: `https://tvrinfo.ro/tentativele-de-frauda-se-intensifica-in-aceasta-perioada-cu-ocazia-zilei-de-8-martie-avertizeaza-dnsc/`
- Digi Economic despre romance scam: `https://www.digi24.ro/digieconomic/digital/romance-scam-capcana-tot-mai-periculoasa-pe-internet-cum-actioneaza-escrocii-si-ce-recomanda-expertii-65137`

### Evidence candidates

- `ROMANCE_RAPID_INTIMACY`
- `GIFT_DELIVERY_HOOK`
- `EMOTIONAL_MANIPULATION`
- `EMERGENCY_MONEY_REQUEST`
- `CARD_OR_TRANSFER_REQUEST`

### Contract mapping

- Romance context alone = `SUSPECT`.
- Money/voucher/crypto/card request by chat = sensitive request.

### Verdict conform reducer

- Cere bani/voucher/crypto/card dupa relatie construita => `PERICULOS`.
- Doar conversatie romantica intensa fara cerere => `SUSPECT`.

## Provider/registry implications

### Surse noi de provider/corpus

- PNRISC blacklist: `https://pnrisc.dnsc.ro/blacklist` ca potential provider romanesc, daca exista endpoint consumabil sau scraping permis.
- BVB alerts: source oficial pentru brand warning.
- Loteria Romana alerts: source oficial pentru registry si false app warnings.
- ANPC/DNSC event ticket guidance: source pentru family/test, nu hard provider.

### Registry candidates de verificat

- `bvb.ro`
- `loto.ro`
- `bilete.loto.ro`
- `joc-loto.loto.ro`
- `un-doi.loto.ro`
- `dnsc.ro`
- `pnrisc.dnsc.ro`
- `erovinieta.ro` / domenii CNAIR oficiale pentru rovinieta - necesita verificare suplimentara oficiala inainte de runtime.

## Acceptance test additions

Adauga minimum aceste teste in eval dupa implementarea reducerului pur:

```jsonl
{"id":"SM-F26-01","text":"BVB: ai dividende de 23.400 lei. Completeaza CNP si IBAN aici: https://bvb-dividende.test","expected":"PERICULOS","why":"brand BVB + domeniu neoficial + CNP/IBAN"}
{"id":"SM-F26-FP1","text":"BVB: informare investitori pe https://www.bvb.ro","expected":"SIGUR","why":"domeniu oficial + fara cerere sensibila + providers clean"}
{"id":"SM-F27-01","text":"Loteria Romana: bonus 500 lei, descarca aplicatia de aici https://bonus-loto.test","expected":"PERICULOS","why":"aplicatie/depunere pe domeniu neoficial"}
{"id":"SM-F28-01","text":"Vand bilete concert, plata Revolut acum si trimit PDF dupa","expected":"SUSPECT","why":"plata catre persoana necunoscuta, fara provider/link"}
{"id":"SM-F29-01","text":"Apartament sub pretul pietei. Trimite poza CI si garantia acum pe Revolut","expected":"PERICULOS","why":"chirie falsa + act identitate + bani"}
{"id":"SM-F30-01","text":"Rovinieta restanta. Plateste urgent sau se retine vehiculul: https://rovinieta-plata.test","expected":"PERICULOS","why":"domeniu neoficial + plata urgenta"}
{"id":"SM-F31-01","text":"Meta Business: confirma drepturile paginii aici https://meta-page-appeal.test/login","expected":"PERICULOS","why":"platform admin phishing + login neoficial"}
{"id":"SM-F32-01","text":"DNSC citatie oficiala. Descarca documentul si confirma datele: https://dnsc-citatie.test","expected":"PERICULOS","why":"institutie + domeniu neoficial + document/date"}
{"id":"SM-F33-01","text":"Job online 500 lei/zi. Continua pe Telegram si depune 100 lei pentru taskuri premium","expected":"PERICULOS","why":"task scam + depunere"}
{"id":"SM-F34-01","text":"Reduceri 90% la telefoane. Comanda pe https://emag-oferta-speciala.test/card","expected":"PERICULOS","why":"retail clone + card pe domeniu neoficial"}
{"id":"SM-F35-01","text":"Iubire, am nevoie urgent de bani pentru bilet, trimite 300 euro azi","expected":"PERICULOS","why":"romance + money request"}
```

Nota: `SIGUR` in teste necesita mocked providers clean si identity official/delegated. Fara provider bundle complet, testul trebuie sa astepte `PENDING` sau sa ruleze ca unit test pe reducer cu bundle complet.

## Decizie finala

Familiile mici merita integrate, dar doar in forma asta:

```text
research -> atlas supplement -> normalized evidence -> pure reducer tests
```

Nu implementam regex-uri noi care fac verdict. Asta ar recrea exact problema pe care contractul nou o elimina.
