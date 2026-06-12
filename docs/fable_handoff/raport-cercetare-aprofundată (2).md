# Atlas matur de scamuri de impersonare pentru SigurScan

## Verdict executiv

Pentru România, în 2024–2026, miezul dur al scamurilor de impersonare nu este „mesajul dubios” în sine, ci combinația dintre **identitate pretinsă de încredere**, **canal greșit**, **cerere sensibilă** și **dovadă tehnică de nepotrivire**. Sursele oficiale converg foarte clar: instituții publice, bănci, curieri, platforme și utilități spun în mod repetat că nu cer prin SMS, WhatsApp, e-mail nesecurizat sau apeluri neașteptate date de card, OTP, parole, instalare de aplicații de control la distanță, mutarea banilor într-un „cont sigur”, taxe de livrare sau taxe administrative plătite pe linkuri ad-hoc. Poliția Română a documentat explicit impersonarea Europol/Interpol/Poliției pentru a cere bani, precum și tehnica de spoofing în care atacatorii se prezintă drept bancă ori poliție și cer transfer într-un „cont sigur”; BNR, ASF și bănci reale au descris aceleași tipare în zona financiară; curierii și utilitățile au publicat la rândul lor alerte aproape copy-paste, doar brandul se schimbă. citeturn13view0turn14view0turn16search2turn16search5turn17search1turn46search0turn46search1turn48search0turn23search0turn23search3

Pentru SigurScan, concluzia product-grade este simplă și dură: **atlasul OP-IMP trebuie să fie o componentă semantică de evidence assembly, nu un judecător final**. El trebuie să emită `semantic_review`, `reason_codes`, `risk_class`, să propună verificări oficiale și să ofere false-positive guards. Verdictul final trebuie plafonat de dovezi tehnice și de verificare: hit în Web Risk/URLhaus/phishing DB rămâne hard dangerous; un domeniu oficial curat fără cerere sensibilă trebuie să poată ieși SIGUR; iar semnalele soft, precum marketing agresiv, „promoție”, link sub buton sau domeniu nou fără altă dovadă, nu trebuie să devină singure verdict final. Aici nu e loc de teatru. Scamurile moderne se prefac impecabil; de aceea, regula corectă este „dovezile câștigă, vibe-ul pierde”. citeturn46search6turn28search2turn28search3turn41search0turn45search0turn31search0turn47search2

O altă schimbare majoră din 2024–2026 este că **deepfake-ul și spoofingul au ieșit din laborator și au intrat în producție**. BNR a avertizat public despre deepfake-uri care folosesc imaginea guvernatorului pentru „investiții”, iar rapoartele sale descriu explicit fraude bazate pe smishing, spoofing și deepfake; ASF avertizează despre grupuri false de investiții pe WhatsApp și Telegram; Hidroelectrica a publicat un comunicat despre site-uri care îi simulează identitatea și atribuie fals declarații companiei; operatorii telecom au început blocarea anumitor apeluri internaționale cu CLI spoofed, ceea ce confirmă că fenomenul e suficient de serios încât să provoace măsuri la nivel de infrastructură. citeturn36search1turn36search6turn36search7turn17search1turn36search0turn48search2turn48search4

## Taxonomia matură OP-IMP

Tabelul de mai jos este versiunea matură recomandată pentru `families[]`. Este centrat pe familiile cerute și mai adaugă o familie justificată puternic de surse oficiale românești: impersonarea furnizorilor de telecom/utilități.

| Code | Nume | Identitate impersonată | Goal dominant | Acțiune cerută | Severity baseline | High-risk conditions | False-positive guards | Verificare oficială | Source refs |
|---|---|---|---|---|---|---|---|---|---|
| IMP-01 | Instituții de stat | ANAF, Poliția Română, instanțe, Europol/Interpol, Ghișeul.ro | bani, date personale, card, panică juridică | „plătește acum”, „deschide PDF/QR”, „trimite date”, „confirmă identitatea” | high | amenințare penală, termen în ore, plata prin link/crypto, cerere CI/card | comunicare informativă fără cerere sensibilă pe domeniu oficial | confirmare pe site-ul instituției sau contact page oficială; la Ghișeul.ro doar pe domeniul oficial | citeturn13view0turn10search13turn47search2turn47search3turn33search7 |
| IMP-02 | Bancă și fintech | bancă comercială, BNR, Revolut, „echipa antifraudă” | bani, OTP, login, remote access, mutare fonduri | „mută banii în cont sigur”, „spune OTP”, „instalează AnyDesk”, „verifică KYC” | critical | safe-account, OTP la telefon, remote access, cont blocat, spoofed caller ID | notificare de securitate pe domeniu oficial care avertizează să NU comunici codul | verificare în aplicația oficială / call-back din aplicație / registru BNR pentru entitate | citeturn14view0turn16search5turn45search0turn41search0turn41search1turn42search2turn43search4turn44search8 |
| IMP-03 | Curierat | FAN Courier, Poșta Română, Sameday, DHL | card, date personale, credential stuffing | „alege lockerul”, „plătește taxă”, „confirmă adresa”, „urmărește coletul” | high | taxă mică urgentă, link shortener/look-alike, cerere card/PIN, WhatsApp/SMS cu acțiune imediată | tracking real, fără cerere sensibilă, pe domeniu oficial sau din app oficială | verificare doar pe site/app oficial și AWB pe pagina oficială | citeturn46search0turn46search1turn48search0turn48search13turn19search9 |
| IMP-04 | Suport tehnic | Microsoft, Apple, ISP, „securitate Windows”, „Apple Support” | remote access, bani, card, gift card, crypto | „sună la numărul din pop-up”, „instalează Quick Assist/AnyDesk”, „plătește în gift card” | critical | pop-up cu număr de telefon, remote access + panică, gift card/crypto | articol oficial de suport fără cerere de acțiune financiară | verificare exclusiv pe domeniul oficial Microsoft/Apple, inițiată de utilizator | citeturn31search0turn31search4turn31search1turn31search5 |
| IMP-05 | Rudă, prieten, cont compromis | fiu, nepot, prieten, coleg cu WhatsApp compromis | transfer instant, cod WhatsApp, date personale | „am număr nou”, „trimite bani acum”, „dă-mi codul” | high | schimbare bruscă de număr, urgență emoțională, cerere transfer, cerere cod 6 cifre | mesaj banal fără bani/date/coduri | verificare out-of-band: apel la numărul vechi sau alt canal cunoscut | citeturn31search2turn31search6turn31search21 |
| IMP-06 | BEC și factură falsă | CEO, CFO, avocat, furnizor, contabil | schimbare IBAN, transfer bancar | „plată urgentă și confidențială”, „folosește noul IBAN” | critical | schimbare IBAN fără proces, secret/confidențial, bypass aprobare, domeniu asemănător | invoice thread legitim, același IBAN istoric, confirmare procedurală | verificare prin callback procedural și confirmare IBAN/nume beneficiar | citeturn35search0turn35search11turn41search8turn36search5 |
| IMP-07 | Persoane publice și deepfake investiții | guvernator BNR, lideri companii, celebrități | bani, crypto, date financiare | „investește azi”, „lasă telefonul”, „depune minim 250 EUR” | critical | randament garantat, videoclip deepfake, formular lead-gen + apel, WhatsApp/Telegram | articol de presă sau comunicat oficial care doar avertizează publicul | ASF register, BNR warning, site oficial companie | citeturn36search1turn17search1turn36search0turn41search13 |
| IMP-08 | Marketplace | OLX, Publi24, Facebook Marketplace, „cumpărătorul” | card, OTP, date, fake escrow | „primește banii pe link”, „escrow/livrare securizată”, „confirmă cardul pentru încasare” | high | link de plată trimis în chat, ieșire off-platform, cerere card/CVV/OTP | mesaj de cumpărare simplu, fără link, fără cerere sensibilă | verificare exclusiv în contul platformei, nu în site trimis de terț | citeturn28search2turn28search3turn28search4turn28search10 |
| IMP-09 | Retail și giveaway | eMAG, Altex, branduri mari | card, date, taxe de procesare | „voucher 1000 lei”, „cadou iPhone”, „plătește 9,99 lei transport” | medium-high | premiu improbabil, domeniu neoficial, taxă de „procesare”, sondaj + card | campanie pe domeniul oficial cu regulament public | verificare pe pagina oficială de campanii/regulamente | citeturn30search0turn30search2turn29search3 |
| IMP-10 | ONG și donații false | ONG, campanii umanitare, asociații | bani, date, transfer/crypto | „donează urgent”, „scanează QR”, „trimite pe IBAN personal” | medium-high | criză emoțională, IBAN personal, crypto, pagină clonă | campanii verificate pe site oficial și canale oficiale consistente | verificare pe site-ul oficial al ONG-ului și registrul juridic al entității, dacă există | citeturn33search0turn33search9 |
| IMP-11 | Romance, militar, doctor străin | militar, medic, contractor, relație la distanță | bani, identitate, documente | „trimite bani pentru urgență”, „plătește colet/taxă”, „trimite copie act” | high | relație rapidă, fotografii prea perfecte, cerere urgentă de bani, evitare întâlnire reală | conversație normală fără bani sau documente | reverse image, verificare identitate, fără trimiteri de bani/date | citeturn15view0 |
| IMP-12 | Autorități internaționale și sextortion | Europol, Interpol, „procuror”, „avocat”, extortionist | bani, crypto, teamă | „plătește amenda”, „plătește ca să nu publicăm”, „deschide ordinul atașat” | critical | termen limită scurt, bitcoin, PDF pseudo-oficial, acuzații sexuale/penale | notificare juridică reală ajunge prin canale verificabile și fără cerere de bitcoin | contact oficial al instituției + verificare de caz pe canale legitime | citeturn13view0turn33search7 |
| IMP-13 | Telecom și utilități | Orange, Vodafone, Digi, E.ON, PPC, Electrica, Hidroelectrica | bani, date personale, malware, lead-gen investiții | „plătește factura”, „actualizează datele”, „instalează aplicația”, „confirmă oferta” | high | deconectare iminentă, link de plată neoficial, alt domeniu, premii false, screens clone | factură/aviz pe canal oficial, fără cerere de OTP/card/pin în SMS | verificare pe domeniul oficial, în contul oficial, pe canalul din factură | citeturn21search3turn21search4turn21search5turn23search0turn23search3turn25search1turn25search2turn22search0turn23search1 |

## Semnalele de evidență care merită codate

Schema corectă pentru `signals[]` nu trebuie să confunde semnalele „tare” cu cele „de atmosferă”. Cea mai importantă separație este între **ce poate ridica singur la periculos** și **ce doar împinge spre suspect**.

Semnalele aproape decisive sunt cele în care sursa oficială spune explicit „nu facem asta niciodată”. Aici intră: solicitarea de OTP, PIN, CVC/CVV sau date complete de card pe telefon, SMS, WhatsApp sau e-mail; cererea de a muta banii într-un „cont sigur”; cererea de instalare AnyDesk, Quick Assist, TeamViewer sau alt software de control la distanță la instrucțiunea unui apel necerut; cererea de plată în crypto ori gift card pentru suport tehnic, taxe, utilități sau autorități; cererea de cod WhatsApp de 6 cifre; cererea de card/PIN/taxă de livrare în numele unui curier; cererea de plată dintr-un domeniu neoficial în numele Electrica, E.ON, Poșta sau Ghișeul.ro. Aici verdict effect-ul corect este `hard_dangerous` sau, dacă lipsește încă dovada tehnică a domeniului rău, `can_raise_dangerous_with_combo`. citeturn45search0turn31search0turn31search1turn31search2turn46search0turn48search0turn23search0turn23search3turn47search2

Semnalele puternice, dar nu singure decisive, sunt: brand-domain mismatch după rezolvarea URL final; alt domeniu decât cel oficial declarat de brand; look-alike domain; link către pagină nouă/necunoscută care cere doar „confirmare”; attachment pseudo-oficial care deschide cereri de date; mesaj de la „șef” sau „furnizor” cu schimbare de IBAN; ID spoofing/caller spoofing; formulare care cer urgent actualizarea KYC; pagină de investiții cu randament nerealist și distribuție prin WhatsApp/Telegram. Acestea trebuie mapate la `strong` sau `decisive` în funcție de cererea sensibilă și de dovezile provider. citeturn35search0turn35search11turn17search1turn36search1turn41search8turn48search8

Semnalele medii sunt utile doar în combinații: limbaj urgent, greșeli de limbă, preț prea bun, „ultimele minute”, „cadou”, QR lipit peste alt QR, domeniu foarte nou, WhatsApp în loc de aplicația oficială, trecerea conversației off-platform, apel venit din străinătate dar afișat ca număr local, cererea de „ștergere a urmelor” sau confidențialitate. Sunt bune pentru `risk_class: suspect`, nu pentru execuție sumară. Un detector care face `PERICULOS` doar pentru că textul sună „prea promo” e un detector care va biciui newslettere legitime. Și asta nu e anti-fraudă, e teatru experimental. citeturn20search4turn30search0turn41search14turn46search1

False-positive guards obligatorii: newsletter promo pe domeniu oficial și fără cerere sensibilă; mesaj legitim de securitate bancară care spune explicit „nu comunica OTP”; tracking curier real fără cerere de card și verificabil în cont sau pe site-ul oficial; campanie retail cu regulament public pe domeniul brandului; link scurt care se rezolvă în final pe domeniu oficial; deep link către App Store / Google Play al aplicației oficiale; factură utilități care trimite doar în portalul oficial și ale cărei date de canal corespund cu cele comunicate public de companie. citeturn28search4turn30search2turn29search3turn23search3turn42search15turn47search2

Mai jos este un catalog compact, direct mapabil în `signals[]`.

```json
[
  {
    "signal_slug": "state_brand_on_wrong_channel_asks_payment",
    "text": "Instituție de stat pretinsă + cerere de plată/date pe SMS, WhatsApp sau e-mail nesecurizat.",
    "detectable_in": ["text", "html", "pdf", "ocr", "attachment"],
    "regex_or_heuristic": "brand in {ANAF, Politia Romana, Europol, Interpol, Ghișeul.ro} AND request in {plata, card, cont, CNP, CI, QR}",
    "required_context": "brand pretins + cerere sensibilă + canal neobișnuit sau link extern",
    "verification_method": "verificare pe site-ul instituției și pe contact page oficială",
    "power": "decisive",
    "verdict_effect": "can_raise_dangerous_with_combo",
    "false_positive_guard": "nu ridica singur la periculos dacă mesajul este doar informativ și vine de pe domeniul oficial curat",
    "source_refs": ["igpr_gov_impersonation", "anaf_warning", "ghiseul_phishing"]
  },
  {
    "signal_slug": "safe_account_request",
    "text": "Cerere de mutare a banilor într-un «cont sigur» sau cont nou pentru protecție.",
    "detectable_in": ["text", "phone_transcript", "ocr"],
    "regex_or_heuristic": "contains any of {'cont sigur','safe account','muta fondurile','transfer de protectie'}",
    "required_context": "impersonare bancă/poliție/fintech",
    "verification_method": "marcați ca fraudă compatibilă cu spoofing și solicitați verificare out-of-band în aplicația oficială",
    "power": "decisive",
    "verdict_effect": "hard_dangerous",
    "false_positive_guard": "none",
    "source_refs": ["igpr_spoofing", "revolut_vishing"]
  },
  {
    "signal_slug": "otp_requested_by_human",
    "text": "OTP, cod 3D Secure, PIN sau cod WhatsApp cerut de o persoană ori introdus pe pagină neoficială.",
    "detectable_in": ["text", "form", "html", "phone_transcript", "ocr"],
    "regex_or_heuristic": "contains OTP/PIN/CVV/verification code/read back code",
    "required_context": "cerere activă de comunicare sau introducere pe domeniu neoficial",
    "verification_method": "hard rule din paginile oficiale ale băncilor/WhatsApp",
    "power": "decisive",
    "verdict_effect": "hard_dangerous",
    "false_positive_guard": "mesajele care spun «nu comunica OTP» sunt guard, nu risc",
    "source_refs": ["revolut_vishing", "whatsapp_code", "ing_never_ask", "bt_fraud_reco", "raiffeisen_phishing", "bcr_phishing"]
  },
  {
    "signal_slug": "remote_access_requested",
    "text": "Cerere de instalare AnyDesk, TeamViewer, Quick Assist sau similar la apel/mesej necerut.",
    "detectable_in": ["text", "html", "phone_transcript"],
    "regex_or_heuristic": "contains any of {'AnyDesk','TeamViewer','Quick Assist','remote access','screen share'}",
    "required_context": "impersonare bancă, suport tehnic, operator telecom sau autoritate",
    "verification_method": "hard rule întrucât sursele oficiale cer să nu se facă asta",
    "power": "decisive",
    "verdict_effect": "hard_dangerous",
    "false_positive_guard": "remote support inițiat de utilizator din aplicația sau site-ul oficial rămâne nepenalizat singur",
    "source_refs": ["microsoft_support", "revolut_vishing", "bt_fraud_reco", "ing_smishing"]
  },
  {
    "signal_slug": "gift_card_or_crypto_for_support_or_authority",
    "text": "Plată cerută în gift card sau crypto pentru suport tehnic, taxe, utilități sau autorități.",
    "detectable_in": ["text", "html", "pdf"],
    "regex_or_heuristic": "contains any of {'gift card','Apple Gift Card','Bitcoin','USDT','crypto'}",
    "required_context": "plata nu este pentru un produs Apple/crypto real în aplicație autorizată",
    "verification_method": "hard rule conform Microsoft/Apple/Europol/BNR",
    "power": "decisive",
    "verdict_effect": "hard_dangerous",
    "false_positive_guard": "achiziția legitimă de crypto într-o entitate autorizată nu intră aici",
    "source_refs": ["microsoft_support", "apple_gift_card", "europol_fake_correspondence", "bnr_deepfake"]
  },
  {
    "signal_slug": "courier_tiny_fee_card_request",
    "text": "Curier pretins + taxă mică + cerere card/PIN/CVV sau alegere locker pe link extern.",
    "detectable_in": ["text", "html", "ocr", "qr"],
    "regex_or_heuristic": "brand in {FAN, Sameday, Posta, DHL} AND request in {'taxa','locker','redirectionare','actualizare adresa'} AND asks for card",
    "required_context": "URL final neoficial sau formular de plată",
    "verification_method": "verificare doar pe site/app oficială și AWB oficial",
    "power": "decisive",
    "verdict_effect": "hard_dangerous",
    "false_positive_guard": "tracking simplu fără cerere sensibilă nu e suficient",
    "source_refs": ["fan_sms", "sameday_phishing", "posta_phishing", "orange_courier_smishing"]
  },
  {
    "signal_slug": "lookalike_or_non_official_domain",
    "text": "Domeniu final care nu este în lista oficială a entității sau imită ortografic brandul.",
    "detectable_in": ["link", "html", "form", "qr"],
    "regex_or_heuristic": "final_url host not in official_domains OR fuzzy brand match",
    "required_context": "claim de brand sau identitate",
    "verification_method": "resolver URL + canonical domain allowlist",
    "power": "strong",
    "verdict_effect": "can_raise_suspect",
    "false_positive_guard": "servicii legitime third-party aprobate public și deep links oficiale",
    "source_refs": ["electrica_domain", "ghiseul_terms", "hidroelectrica_official_site", "olx_no_payment_links"]
  },
  {
    "signal_slug": "bec_supplier_iban_change",
    "text": "Factură, PDF sau e-mail care schimbă IBAN-ul cunoscut al furnizorului ori cere derogare procedurală.",
    "detectable_in": ["email", "pdf", "attachment", "ocr"],
    "regex_or_heuristic": "contains {'noul IBAN','schimbare cont','confidential','plata urgenta'}",
    "required_context": "furnizor/CEO/avocat pretins",
    "verification_method": "callback procedural și corelare nume beneficiar–IBAN acolo unde serviciul există",
    "power": "strong",
    "verdict_effect": "can_raise_dangerous_with_combo",
    "false_positive_guard": "schimbările de cont confirmate prin proces intern și istoric contractual",
    "source_refs": ["dnsc_bec", "orange_message_from_boss", "ing_ceo_fraud", "bnr_sanb_context"]
  },
  {
    "signal_slug": "deepfake_investment_with_lead_form",
    "text": "Persoană publică / brand financiar + promisiune de câștig + formular de lead sau apel de follow-up.",
    "detectable_in": ["text", "html", "ocr", "video_caption"],
    "regex_or_heuristic": "contains public figure/BNR/Hidroelectrica + profit promise + contact form/WhatsApp",
    "required_context": "investiție sau crypto",
    "verification_method": "ASF register, BNR warnings, site oficial companie",
    "power": "strong",
    "verdict_effect": "can_raise_dangerous_with_combo",
    "false_positive_guard": "material jurnalistic fără call-to-action financiar",
    "source_refs": ["bnr_deepfake", "asf_whatsapp", "hidroelectrica_invest"]
  },
  {
    "signal_slug": "marketing_only_or_hidden_link_only",
    "text": "Limbaj promoțional sau link ascuns sub buton fără altă cerere sensibilă.",
    "detectable_in": ["text", "html"],
    "regex_or_heuristic": "marketing hype OR anchor mismatch only",
    "required_context": "fără cereri de plată/date sensibile și fără hit provider",
    "verification_method": "ceiling rule: max suspect",
    "power": "weak",
    "verdict_effect": "never_decides_alone",
    "false_positive_guard": "newslettere și campanii legitime sunt frecvente",
    "source_refs": ["ecc_fake_stores", "emag_campaigns"]
  }
]
```

## Harta de verificare oficială

Pentru `verification_sources[]`, recomandarea este să existe două straturi. Primul este un **allowlist operațional** al domeniilor și canalelor oficiale. Al doilea este un **never-ask map**, adică ce spune explicit fiecare entitate că nu va cere niciodată. Unde nu există o declarație suficient de clară, trebuie marcat `needs_confirmation`, nu „inventat frumos”. Frumos e pentru poeți. Anti-frauda cere acte, nu optimism. citeturn41search0turn43search4turn44search8turn46search0turn48search0turn23search0

Mai jos este un map compact, numai cu entitățile cerute și cu cele indispensabile pentru familiile suport tehnic și social takeover.

```json
[
  {
    "brand": "ANAF",
    "official_domains": ["anaf.ro"],
    "official_apps_or_deeplinks": ["needs_confirmation"],
    "official_phone_or_contact_page": "anaf.ro",
    "never_ask_for": "date bancare sau personale prin fraude telefonice in numele institutiei",
    "verification_method": "verifica pe anaf.ro sau in SPV, nu pe link din SMS/email",
    "confidence": "high",
    "caveats": "in aceasta cercetare nu a fost extras un articol HTML ANAF la fel de clar ca la alte branduri; avertismentul este confirmat prin rezultatul oficial de cautare"
  },
  {
    "brand": "DNSC",
    "official_domains": ["dnsc.ro", "pnrisc.dnsc.ro", "sigurantaonline.ro"],
    "official_apps_or_deeplinks": [],
    "official_phone_or_contact_page": "dnsc.ro",
    "never_ask_for": "needs_confirmation",
    "verification_method": "foloseste exclusiv site-ul oficial si canalele publicate de DNSC",
    "confidence": "medium",
    "caveats": "nu a fost localizata in aceasta cercetare o formulare standard «nu cerem niciodata X»"
  },
  {
    "brand": "Poliția Română / IGPR",
    "official_domains": ["politiaromana.ro"],
    "official_apps_or_deeplinks": [],
    "official_phone_or_contact_page": "politiaromana.ro/ro/contact",
    "never_ask_for": "plata unor sume pentru evitarea procedurilor judiciare prin emailuri ce pretind a proveni de la politie/europol/interpol",
    "verification_method": "verifica pe site-ul IGPR si prin unitatea teritoriala, nu in reply la mesaj",
    "confidence": "high",
    "caveats": ""
  },
  {
    "brand": "BNR",
    "official_domains": ["bnr.ro"],
    "official_apps_or_deeplinks": [],
    "official_phone_or_contact_page": "bnr.ro/6-contact",
    "never_ask_for": "date personale/confidentiale despre conturi, carduri, credite ori aplicatii bancare prin email/telefon/SMS/mesaje instant",
    "verification_method": "verifica in avertismentele BNR si in registrele BNR",
    "confidence": "high",
    "caveats": ""
  },
  {
    "brand": "ASF",
    "official_domains": ["asfromania.ro"],
    "official_apps_or_deeplinks": [],
    "official_phone_or_contact_page": "asfromania.ro/ro/a/1544/registre-entit%C4%83%C8%9Bi-autorizate",
    "never_ask_for": "ASF nu apeleaza consumatorii de la Tel Verde si cere verificarea entitatilor in registru",
    "verification_method": "consulta registrele ASF si avertismentele publice",
    "confidence": "high",
    "caveats": ""
  },
  {
    "brand": "ANCOM",
    "official_domains": ["ancom.ro"],
    "official_apps_or_deeplinks": [],
    "official_phone_or_contact_page": "ancom.ro",
    "never_ask_for": "needs_confirmation",
    "verification_method": "foloseste site-ul oficial; pentru spoofing, trateaza ANCOM mai ales ca sursa de context/reglementare, nu ca brand des impersonat in retail",
    "confidence": "medium",
    "caveats": "in aceasta cercetare, masurile ANCOM au fost confirmate prin sumar DNSC"
  },
  {
    "brand": "Ghișeul.ro",
    "official_domains": ["ghiseul.ro"],
    "official_apps_or_deeplinks": ["ghiseul.ro subdomains only"],
    "official_phone_or_contact_page": "ghiseul.ro/ghiseul/public/informatii/contact",
    "never_ask_for": "nu anunta prin SMS sau email aparitia unei obligatii de plata",
    "verification_method": "numai pe ghiseul.ro si subdomeniile sale",
    "confidence": "high",
    "caveats": ""
  },
  {
    "brand": "FAN Courier",
    "official_domains": ["fancourier.ro"],
    "official_apps_or_deeplinks": ["needs_confirmation"],
    "official_phone_or_contact_page": "fancourier.ro/contact",
    "never_ask_for": "accesarea linkurilor false care solicita date bancare",
    "verification_method": "verifica AWB-ul si statusul doar pe fancourier.ro sau in aplicatia oficiala",
    "confidence": "high",
    "caveats": ""
  },
  {
    "brand": "Poșta Română",
    "official_domains": ["posta-romana.ro"],
    "official_apps_or_deeplinks": [],
    "official_phone_or_contact_page": "posta-romana.ro",
    "never_ask_for": "informatii bancare confidentiale, numere de card, coduri PIN sau plati online ale unor taxe de livrare",
    "verification_method": "verifica numai pe site-ul oficial sau la oficiul postal",
    "confidence": "high",
    "caveats": ""
  },
  {
    "brand": "Sameday",
    "official_domains": ["sameday.ro"],
    "official_apps_or_deeplinks": ["needs_confirmation"],
    "official_phone_or_contact_page": "sameday.ro/contact",
    "never_ask_for": "informatii personale sau taxe suplimentare din mesaje care cer actiune imediata prin link",
    "verification_method": "consulta doar sameday.ro si canalele publicate de companie",
    "confidence": "high",
    "caveats": ""
  },
  {
    "brand": "DHL",
    "official_domains": ["dhl.com"],
    "official_apps_or_deeplinks": ["needs_confirmation"],
    "official_phone_or_contact_page": "dhl.com",
    "never_ask_for": "needs_confirmation",
    "verification_method": "foloseste doar paginile oficiale DHL si track&trace oficial",
    "confidence": "medium",
    "caveats": "pagina oficiala anti-fraudă a fost identificata, dar detaliile fine nu au fost aprofundate aici"
  },
  {
    "brand": "OLX",
    "official_domains": ["olx.ro", "ajutor.olx.ro", "livrare.olx.ro"],
    "official_apps_or_deeplinks": ["olx.ro app store/play links via official site"],
    "official_phone_or_contact_page": "ajutor.olx.ro",
    "never_ask_for": "OLX nu furnizeaza linkuri de plati pentru transferul banilor",
    "verification_method": "verifica doar in contul OLX si in help center-ul oficial",
    "confidence": "high",
    "caveats": ""
  },
  {
    "brand": "eMAG",
    "official_domains": ["emag.ro"],
    "official_apps_or_deeplinks": ["official store links published from emag.ro"],
    "official_phone_or_contact_page": "emag.ro/help/contact",
    "never_ask_for": "needs_confirmation",
    "verification_method": "campaniile legitime si regulamentele sunt pe emag.ro/help",
    "confidence": "medium",
    "caveats": "am localizat ghid anti-phishing si pagini de campanii, nu o formula explicita standard «nu cerem niciodata X»"
  },
  {
    "brand": "Altex",
    "official_domains": ["altex.ro"],
    "official_apps_or_deeplinks": ["official store links via altex.ro"],
    "official_phone_or_contact_page": "altex.ro/suport-clienti/",
    "never_ask_for": "needs_confirmation",
    "verification_method": "verifica suportul si regulamentul campaniei pe domeniul oficial",
    "confidence": "medium",
    "caveats": "nu am localizat in aceasta cercetare o pagina anti-phishing explicita Altex"
  },
  {
    "brand": "Revolut",
    "official_domains": ["revolut.com", "help.revolut.com"],
    "official_apps_or_deeplinks": ["app.revolut.com", "official app-store/play links"],
    "official_phone_or_contact_page": "help.revolut.com",
    "never_ask_for": "mutarea banilor in «safe account», citirea OTP la telefon, instalarea remote access la cererea apelantului",
    "verification_method": "verifica in aplicatia Revolut si in help.revolut.com",
    "confidence": "high",
    "caveats": ""
  },
  {
    "brand": "Banca Transilvania",
    "official_domains": ["bancatransilvania.ro", "intreb.bancatransilvania.ro"],
    "official_apps_or_deeplinks": ["btpay", "bt24", "neo bt official links from bank site"],
    "official_phone_or_contact_page": "bancatransilvania.ro/call-center",
    "never_ask_for": "user, parola, OTP sau instalarea unei aplicatii precum AnyDesk",
    "verification_method": "verifica in canalele BT si pe site-ul oficial",
    "confidence": "high",
    "caveats": ""
  },
  {
    "brand": "BCR",
    "official_domains": ["bcr.ro"],
    "official_apps_or_deeplinks": ["George official links from bcr.ro"],
    "official_phone_or_contact_page": "bcr.ro/ro/contact",
    "never_ask_for": "date de identificare/autentificare bancara prin phishing",
    "verification_method": "call-back in George / contact page oficiala",
    "confidence": "high",
    "caveats": ""
  },
  {
    "brand": "ING",
    "official_domains": ["ing.ro"],
    "official_apps_or_deeplinks": ["Home'Bank official links from ing.ro"],
    "official_phone_or_contact_page": "ing.ro/ing-in-romania/contact",
    "never_ask_for": "date bancare, parole, OTP sau instalarea unui program pentru actualizarea datelor",
    "verification_method": "Home'Bank, ING Business, ing.ro",
    "confidence": "high",
    "caveats": ""
  },
  {
    "brand": "Raiffeisen Bank",
    "official_domains": ["raiffeisen.ro", "bank.raiffeisen.ro"],
    "official_apps_or_deeplinks": ["Smart Mobile official links from raiffeisen.ro"],
    "official_phone_or_contact_page": "raiffeisen.ro/ro/imm/in-sprijinul-tau/asistenta/urgente.html",
    "never_ask_for": "formulare, programe atasate, redirectari spre site-uri care cer date personale; PIN/parole la telefon",
    "verification_method": "verifica in aplicatia oficiala si pe site-urile bancii",
    "confidence": "high",
    "caveats": ""
  },
  {
    "brand": "Orange / YOXO",
    "official_domains": ["orange.ro", "yoxo.ro"],
    "official_apps_or_deeplinks": ["official store links from orange.ro/yoxo.ro"],
    "official_phone_or_contact_page": "orange.ro/contact",
    "never_ask_for": "needs_confirmation",
    "verification_method": "curier fantoma, malware si alte alerte sunt publicate pe orange.ro",
    "confidence": "medium",
    "caveats": "ghiduri bune, dar formula standard «nu cerem niciodata X» nu a fost localizata explicit pentru toate fluxurile"
  },
  {
    "brand": "Vodafone",
    "official_domains": ["vodafone.ro"],
    "official_apps_or_deeplinks": ["official store links from vodafone.ro"],
    "official_phone_or_contact_page": "vodafone.ro/contact",
    "never_ask_for": "needs_confirmation",
    "verification_method": "foloseste canalele si numerele publicate oficial de Vodafone",
    "confidence": "medium",
    "caveats": ""
  },
  {
    "brand": "Digi",
    "official_domains": ["digi.ro"],
    "official_apps_or_deeplinks": ["official store links from digi.ro"],
    "official_phone_or_contact_page": "digi.ro/ghid-clienti",
    "never_ask_for": "date sensibile prin SMS/e-mail sau date bancare pentru revendicarea premiilor",
    "verification_method": "verifica exclusiv pe digi.ro",
    "confidence": "high",
    "caveats": ""
  },
  {
    "brand": "E.ON Energie România",
    "official_domains": ["eon-ro.ro", "eon.ro", "eon-romania.ro"],
    "official_apps_or_deeplinks": ["official links from eon.ro/eon-romania.ro"],
    "official_phone_or_contact_page": "eon.ro/contact",
    "never_ask_for": "mesaje false cu linkuri/atasamente; incasarea facturilor nu se realizeaza la domiciliu prin angajatii companiei",
    "verification_method": "verifica pe site-ul oficial si pe datele din factura",
    "confidence": "high",
    "caveats": "domeniul operational variaza intre proprietati web E.ON; foloseste allowlist explicit"
  },
  {
    "brand": "PPC Energie",
    "official_domains": ["ppcenergy.ro"],
    "official_apps_or_deeplinks": ["myPPC official links from ppcenergy.ro"],
    "official_phone_or_contact_page": "ppcenergy.ro/legislatie/transmitere-sesizari/",
    "never_ask_for": "plati in numerar si nu incaseaza sume prin angajati",
    "verification_method": "plata numai prin canalele listate oficial",
    "confidence": "high",
    "caveats": ""
  },
  {
    "brand": "Electrica Furnizare",
    "official_domains": ["electricafurnizare.ro"],
    "official_apps_or_deeplinks": ["MyElectrica official links from electricafurnizare.ro"],
    "official_phone_or_contact_page": "electricafurnizare.ro",
    "never_ask_for": "plati prin alte canale decat cele oficiale; emailuri de pe alte domenii; in SMS de plata foloseste doar 1874 si electricafurnizare.ro",
    "verification_method": "allowlist strict pentru domeniu si SMS sender 1874",
    "confidence": "high",
    "caveats": ""
  },
  {
    "brand": "Hidroelectrica",
    "official_domains": ["hidroelectrica.ro"],
    "official_apps_or_deeplinks": [],
    "official_phone_or_contact_page": "hidroelectrica.ro",
    "never_ask_for": "nu incurajeaza folosirea unei anumite platforme de investitii si opereaza un singur site oficial",
    "verification_method": "doar pe site-ul oficial si prin comunicatele companiei",
    "confidence": "high",
    "caveats": ""
  },
  {
    "brand": "Microsoft",
    "official_domains": ["microsoft.com", "support.microsoft.com"],
    "official_apps_or_deeplinks": ["official store links from microsoft.com"],
    "official_phone_or_contact_page": "support.microsoft.com",
    "never_ask_for": "gift cards, crypto, apelare la un numar afisat in pop-up, remote access la apel neinitiati de utilizator",
    "verification_method": "support.microsoft.com only",
    "confidence": "high",
    "caveats": ""
  },
  {
    "brand": "Apple",
    "official_domains": ["apple.com", "support.apple.com"],
    "official_apps_or_deeplinks": ["apps.apple.com"],
    "official_phone_or_contact_page": "support.apple.com",
    "never_ask_for": "gift cards pentru utilitati, datorii, taxe sau servicii non-Apple",
    "verification_method": "support.apple.com only",
    "confidence": "high",
    "caveats": ""
  },
  {
    "brand": "WhatsApp",
    "official_domains": ["whatsapp.com", "faq.whatsapp.com"],
    "official_apps_or_deeplinks": ["wa.me", "official app store/play links"],
    "official_phone_or_contact_page": "whatsapp.com/security",
    "never_ask_for": "codul de inregistrare de 6 cifre sau PIN-ul de verificare in doi pasi",
    "verification_method": "faq.whatsapp.com / security page",
    "confidence": "high",
    "caveats": ""
  }
]
```

## Contractul de integrare în gate

Atlasul trebuie să scrie în `semantic_review`, nu în verdictul final. Asta înseamnă că fiecare semnal produce **reason_codes**, **risk_class recomandat** și **next checks**. Modelul corect de mapare către Evidence Bundle v2 este acesta:

`identity.status` trebuie să reflecte dacă identitatea pretinsă a fost confirmată pe canalul corect. Recomandare de vocabular: `OFFICIAL_MATCH`, `OFFICIAL_MATCH_CHANNEL_MISALIGNED`, `BRAND_MATCH_UNKNOWN_CHANNEL`, `BRAND_MISMATCH`, `NO_MATCH`, `LOOKALIKE_DOMAIN`, `NEEDS_CONFIRMATION`. Un mesaj „de la Ghișeul.ro” care vine de pe final URL ghiseul.ro și nu cere date sensibile poate ajunge `OFFICIAL_MATCH`; același text pe un domeniu look-alike trebuie să devină `BRAND_MISMATCH` sau `LOOKALIKE_DOMAIN`. Ghișeul.ro spune explicit că nu anunță prin SMS sau e-mail apariția unei obligații de plată, ceea ce face foarte puternică regula „brand oficial + canal greșit + cerere sensibilă”. citeturn47search2turn47search3

`request.sensitive` trebuie normalizat la patru niveluri: `none`, `moderate`, `high`, `hard_sensitive`. În `hard_sensitive` intră OTP, PIN, CVC/CVV, full card, parole, seed phrase, remote access, mutare în cont sigur, gift card/crypto ca metodă de plată, copie CI pentru „verificare” când mesajul nu e pe canalul oficial, ori instrucțiuni de schimbare IBAN în BEC. Aici sursele nu lasă mult loc de poezie: Revolut spune explicit că safe account e scam, WhatsApp spune explicit să nu partajezi codul, Microsoft și Apple spun explicit că gift card/crypto nu sunt metodă legitimă de suport sau taxe, iar curierii/utilitățile spun explicit că nu cer card/PIN pe astfel de linkuri. citeturn45search0turn31search2turn31search0turn31search1turn46search0turn48search0turn23search0

`request.channel` trebuie să captureze `expected`, `unexpected_but_plausible`, `misaligned`, `forbidden_for_action`. Exemple: un newsletter promo de la eMAG pe emag.ro este `expected`; un SMS de la bancă cerând „citește-mi OTP-ul” este `forbidden_for_action`; un e-mail de la furnizor cu alt IBAN, fără confirmare procedurală, este `misaligned`. citeturn30search2turn41search0turn41search8

`providers.verdict` trebuie să aibă ultimul cuvânt tehnic cu privire la URL. Reguli de plafon recomandate:
- `WebRisk/URLhaus/PhishingDB HIT` => `PERICULOS` direct.
- `official clean domain + no sensitive request + allowlisted app/deeplink` => poate coborî la `SIGUR`.
- `established clean domain + no sensitive request` => `SIGUR` sau `SUSPECT` doar dacă semanticul ridică alte probleme.
- `malicious provider + brand mismatch` => `PERICULOS`.
- `unknown provider + hard_sensitive request + wrong channel` => `PERICULOS`.
- `unknown provider + only marketing / hidden link` => maxim `SUSPECT`.
- `NO_MATCH registry solo` => maxim `SUSPECT`.
- `SOURCE_ERROR` sau `NOT_CONFIGURED` nu au voie să împingă spre `SIGUR`; cel mult lasă verdictul în `SUSPECT` dacă restul dovezilor nu curăță cazul. Acestea sunt reguli de produs, nu reguli „de feeling”. Ele trebuie să fie codate explicit, nu lăsate la cheremul modelului. citeturn28search3turn47search2turn45search0

`registry_or_official_verification` trebuie să consume registre și pagini oficiale acolo unde există: registrele BNR pentru instituții de credit/IFN/instituții de plată; registrele ASF pentru entități autorizate; listele și contact pages oficiale ale brandurilor; allowlisturi stricte de domenii; și, unde compania publică un canal oficial unic, reguli dedicate. Electrica este exemplul perfect: comunică public că mesajele SMS de plată vin doar de pe 1874 și linkul de plată trebuie să ducă în electricafurnizare.ro. Asta merită o regulă tare, nu o recomandare timidă. citeturn40search0turn17search2turn23search3

## Fixturi de regresie și ce trebuie să devină test obligatoriu

Am acoperit mai jos setul de fixture-uri care trebuie să existe în suita de regresie. Din motive de spațiu, nu extind inline toate cele 120 de obiecte complete în JSON, dar distribuția și testele obligatorii sunt suficient de precise pentru a fi transformate direct în `backend/test_*.py` și într-un patch de fixtures. Aș împărți suita astfel: 60 periculoase, 30 suspecte, 30 sigure.

Distribuția minimă recomandată este:
`IMP-01` 8 fixture-uri, `IMP-02` 12, `IMP-03` 12, `IMP-04` 8, `IMP-05` 8, `IMP-06` 8, `IMP-07` 10, `IMP-08` 12, `IMP-09` 8, `IMP-10` 6, `IMP-11` 6, `IMP-12` 8, `IMP-13` 12. Această distribuție supra-acoperă deliberat finanțele, curierii, marketplace-ul și utilitățile, pentru că acolo există și cel mai puternic suport oficial, și cea mai mare probabilitate de input real de la utilizatori români. citeturn14view0turn46search0turn28search3turn23search0turn36search1

Exemple de fixture-uri periculoase obligatorii:
1. SMS „ANAF” cu link `.example` care cere date de card pentru „deblocare cont fiscal”.
2. Transcript telefonic „bancă + poliție” cu „cont sigur”.
3. SMS FAN / Sameday cu alegere locker și card.
4. Pop-up „Microsoft Defender” cu număr de telefon și cerere AnyDesk.
5. WhatsApp „sunt eu, am telefonul stricat” + cerere transfer instant.
6. Email CFO/vendor cu schimbare de IBAN și „strict confidențial”.
7. Ad cu deepfake și guvernator BNR + formular lead-gen.
8. OLX „primești banii prin link” + cerere OTP/card.
9. eMAG/Altex voucher + taxă de procesare.
10. SMS deconectare Electrica cu link neoficial.
Toate acestea sunt acoperite de surse oficiale sau de combinații foarte solide de surse oficiale. citeturn14view0turn46search0turn31search0turn31search2turn41search8turn36search1turn28search3turn23search3

Exemple de fixture-uri suspecte obligatorii:
1. HTML email promo cu anchor text oficial, dar final URL off-brand și fără cerere sensibilă.
2. PDF „factură” fără cerere de plată imediată, dar cu brand mismatch.
3. Newsletter aparent retail de pe domeniu nou înregistrat, dar fără formular.
4. SMS de tracking cu AWB și link necunoscut, fără card request.
5. Articol pseudo-news cu celebritate și investiții, dar fără CTA financiar direct.
Aceste cazuri trebuie plafonate la `SUSPECT` în lipsa altor dovezi. citeturn20search4turn30search0turn46search1

Exemple de fixture-uri SIGUR, adică false-positive guards obligatorii:
1. Newsletter promo real de la eMAG pe `emag.ro`.
2. Tracking curier real, verificabil pe `fancourier.ro` sau în contul OLX.
3. Factură/aviz real de utilități care duce doar în portalul oficial.
4. SMS OTP legitim care spune clar să nu comunici codul.
5. Campanie buyback telecom/retail publicată pe domeniul oficial.
6. Link scurt legitim care se rezolvă în final pe domeniu oficial.
7. Deep link către App Store / Google Play publicat de brand.
Acestea sunt absolut necesare ca să nu transformi detectorul într-un ciocan care vede doar cuie. citeturn30search2turn28search4turn23search3turn42search15turn29search3

Cele mai importante 10 teste de acceptare, pe care eu le-aș bloca în CI fără milă, sunt acestea:

1. `safe_account_request` + `wrong_channel` => `PERICULOS`.
2. `OTP requested` de orice om, pe orice canal neoficial => `PERICULOS`.
3. `remote_access_requested` în numele băncii/tech support => `PERICULOS`.
4. `curier + taxa + card` => `PERICULOS`.
5. `public_figure + investment + lead_form` cu domeniu non-oficial => `PERICULOS`.
6. `OLX payment link` + `card/OTP` => `PERICULOS`.
7. `marketing only` fără cerere sensibilă și cu provider clean => maximum `SUSPECT`.
8. `official clean domain + no sensitive request` => `SIGUR`.
9. `NO_MATCH registry` fără alt red flag => maximum `SUSPECT`.
10. `SOURCE_ERROR/NOT_CONFIGURED` nu poate reduce automat la `SIGUR`.

## JSON de implementare

JSON-ul de mai jos este un **excerpt compact**, nu artifactul complet cu toate cele 120 de fixture-uri expandate inline. L-am păstrat scurt ca să rămână lizibil în răspuns, dar schema, vocabularul și contractul de integrare sunt suficient de precise pentru implementare directă.

```json
{
  "atlas": "OP-IMP",
  "version": "2026-06-12",
  "families": [
    {
      "code": "IMP-01",
      "name": "institutii_de_stat",
      "description": "Impersonare ANAF, Politia, instante, Europol/Interpol, Ghiseul.ro cu amenintari, amenzi, cereri de plata sau date.",
      "common_channels": ["sms", "whatsapp", "email", "html_email", "pdf", "qr", "ocr_image", "phone_transcript"],
      "impersonated_identity": ["ANAF", "Politia Romana", "instanta", "Europol", "Interpol", "Ghiseul.ro"],
      "attack_goal": ["bani", "card", "date_personale"],
      "typical_user_action_requested": ["plateste acum", "deschide atasamentul", "completeaza datele", "scaneaza QR-ul"],
      "severity_baseline": "high",
      "high_risk_conditions": ["amenintare penala", "termen foarte scurt", "plata crypto", "cerere card/CI/CNP"],
      "false_positive_guards": ["comunicare informativa pe domeniu oficial fara cerere sensibila"],
      "official_verification_paths": ["site oficial al institutiei", "contact page oficiala", "ghiseul.ro only"],
      "source_refs": ["igpr_gov_impersonation", "anaf_warning", "ghiseul_phishing", "europol_fake_correspondence"]
    },
    {
      "code": "IMP-02",
      "name": "banca_fintech",
      "description": "Impersonare banca, BNR, Revolut sau echipa antifrauda pentru OTP, cont sigur, KYC, acces la distanta.",
      "common_channels": ["sms", "whatsapp", "phone_transcript", "email", "html_email", "qr", "ocr_image"],
      "impersonated_identity": ["banca", "BNR", "Revolut"],
      "attack_goal": ["bani", "otp", "login", "remote_access"],
      "typical_user_action_requested": ["muta banii", "spune OTP-ul", "instaleaza AnyDesk", "reseteaza credentialele"],
      "severity_baseline": "critical",
      "high_risk_conditions": ["safe account", "OTP", "remote access", "spoofed caller ID"],
      "false_positive_guards": ["mesaj de securitate pe domeniu oficial care spune sa nu comunici codurile"],
      "official_verification_paths": ["aplicatia oficiala", "call-back din aplicatie", "registrele BNR"],
      "source_refs": ["igpr_spoofing", "bnr_warning", "revolut_vishing", "ing_never_ask", "bt_fraud_reco", "bcr_phishing", "raiffeisen_phishing"]
    },
    {
      "code": "IMP-03",
      "name": "curierat",
      "description": "Impersonare curier cu taxa de livrare, alegere locker, confirmare adresa sau tracking fals.",
      "common_channels": ["sms", "whatsapp", "email", "html_email", "qr", "ocr_image"],
      "impersonated_identity": ["FAN Courier", "Posta Romana", "Sameday", "DHL"],
      "attack_goal": ["card", "date_personale"],
      "typical_user_action_requested": ["plateste taxa", "alege lockerul", "actualizeaza adresa", "urmareste coletul"],
      "severity_baseline": "high",
      "high_risk_conditions": ["taxa mica urgenta", "cerere card/PIN/CVV", "lookalike domain"],
      "false_positive_guards": ["tracking real fara cerere sensibila, pe domeniul oficial"],
      "official_verification_paths": ["site/app oficiala", "AWB oficial"],
      "source_refs": ["fan_sms", "fan_smishing", "sameday_phishing", "posta_phishing"]
    },
    {
      "code": "IMP-04",
      "name": "suport_tehnic",
      "description": "Pop-up, apel sau mesaj in numele Microsoft/Apple/ISP care cere control la distanta sau plata in gift card/crypto.",
      "common_channels": ["html_email", "email", "phone_transcript", "ocr_image", "qr", "text"],
      "impersonated_identity": ["Microsoft", "Apple", "ISP"],
      "attack_goal": ["remote_access", "bani", "card", "gift_card", "crypto"],
      "typical_user_action_requested": ["suna numarul", "instaleaza aplicatia", "cumpara gift card"],
      "severity_baseline": "critical",
      "high_risk_conditions": ["pop-up cu telefon", "AnyDesk/Quick Assist", "gift card", "crypto"],
      "false_positive_guards": ["suport initiat de utilizator din site-ul oficial"],
      "official_verification_paths": ["support.microsoft.com", "support.apple.com"],
      "source_refs": ["microsoft_support", "apple_gift_card", "apple_social_engineering"]
    },
    {
      "code": "IMP-05",
      "name": "ruda_prieten_cont_compromis",
      "description": "Mesaje de la ruda/prieten cu numar nou, urgenta sau cerere de cod WhatsApp.",
      "common_channels": ["whatsapp", "sms", "social_dm", "phone_transcript", "ocr_image"],
      "impersonated_identity": ["ruda", "prieten", "coleg"],
      "attack_goal": ["bani", "date_personale", "otp"],
      "typical_user_action_requested": ["trimite bani", "salveaza numarul nou", "da-mi codul"],
      "severity_baseline": "high",
      "high_risk_conditions": ["urgenta emotionala", "schimbare numar", "cod de 6 cifre"],
      "false_positive_guards": ["mesaj banal fara bani/date/coduri"],
      "official_verification_paths": ["apel out-of-band la numarul vechi"],
      "source_refs": ["whatsapp_code", "whatsapp_security"]
    },
    {
      "code": "IMP-06",
      "name": "bec_factura_falsa",
      "description": "Business Email Compromise, mesaj de la sef, avocat sau furnizor fals, de regula cu schimbare de IBAN.",
      "common_channels": ["email", "html_email", "pdf", "attachment", "ocr_image"],
      "impersonated_identity": ["CEO", "CFO", "avocat", "furnizor"],
      "attack_goal": ["iban_changed", "bani"],
      "typical_user_action_requested": ["plateste urgent", "foloseste noul IBAN", "ocoleste procedura"],
      "severity_baseline": "critical",
      "high_risk_conditions": ["confidential", "urgent", "schimbare IBAN", "exceptie de proces"],
      "false_positive_guards": ["confirmare procedurala pe canale deja cunoscute", "nume beneficiar corespunde"],
      "official_verification_paths": ["callback procedural", "confirmare nume beneficiar"],
      "source_refs": ["dnsc_bec", "orange_message_from_boss", "ing_ceo_fraud"]
    },
    {
      "code": "IMP-07",
      "name": "persoane_publice_deepfake_investitii",
      "description": "Deepfake sau endorsement fals cu BNR, companii listate sau celebritati pentru investitii.",
      "common_channels": ["social_dm", "html_email", "email", "ocr_image", "video_caption", "text"],
      "impersonated_identity": ["Mugur Isarescu", "BNR", "Hidroelectrica", "celebritati"],
      "attack_goal": ["bani", "crypto", "lead_capture"],
      "typical_user_action_requested": ["depune suma minima", "completeaza formularul", "intra pe WhatsApp"],
      "severity_baseline": "critical",
      "high_risk_conditions": ["profit garantat", "deepfake", "WhatsApp/Telegram group"],
      "false_positive_guards": ["articol jurnalistic fara CTA financiar"],
      "official_verification_paths": ["avertismente BNR", "registre ASF", "site oficial companie"],
      "source_refs": ["bnr_deepfake", "asf_whatsapp", "hidroelectrica_invest", "ing_investment_fraud"]
    },
    {
      "code": "IMP-08",
      "name": "marketplace",
      "description": "Impersonare OLX/Publi24/Facebook Marketplace prin link de plata, escrow fals, livrare falsa.",
      "common_channels": ["whatsapp", "sms", "email", "social_dm", "ocr_image", "qr"],
      "impersonated_identity": ["OLX", "Publi24", "cumparator"],
      "attack_goal": ["card", "otp", "date_personale"],
      "typical_user_action_requested": ["primeste plata pe link", "activeaza livrarea", "introdu datele cardului"],
      "severity_baseline": "high",
      "high_risk_conditions": ["link de plata in chat", "iesire off-platform", "cerere CVV/OTP"],
      "false_positive_guards": ["comenzi vizibile in contul oficial OLX"],
      "official_verification_paths": ["ajutor.olx.ro", "livrare.olx.ro", "contul OLX"],
      "source_refs": ["olx_linkuri_false", "olx_no_payment_links", "olx_livrare_faq"]
    },
    {
      "code": "IMP-09",
      "name": "retail_brand_giveaway",
      "description": "Giveaway fals, voucher fals, premiu fals in numele eMAG/Altex sau alt brand mare.",
      "common_channels": ["sms", "email", "html_email", "social_dm", "ocr_image"],
      "impersonated_identity": ["eMAG", "Altex"],
      "attack_goal": ["card", "date_personale"],
      "typical_user_action_requested": ["plateste taxa de procesare", "completeaza sondajul", "revendica premiul"],
      "severity_baseline": "medium_high",
      "high_risk_conditions": ["premiu improbabil", "taxa mica obligatorie", "domeniu neoficial"],
      "false_positive_guards": ["campanie pe domeniu oficial cu regulament public"],
      "official_verification_paths": ["emag.ro/help", "altex.ro/suport-clienti", "pagina de regulament"],
      "source_refs": ["emag_phishing", "emag_campaigns", "altex_support", "altex_campaign"]
    },
    {
      "code": "IMP-10",
      "name": "ong_donatii_false",
      "description": "Campanii emotionale sau umanitare care cer donatii pe IBAN personal, crypto sau QR fals.",
      "common_channels": ["sms", "whatsapp", "email", "social_dm", "qr", "ocr_image"],
      "impersonated_identity": ["ONG", "campanie umanitara"],
      "attack_goal": ["bani", "date_personale"],
      "typical_user_action_requested": ["doneaza urgent", "scaneaza QR", "trimite pe cont personal"],
      "severity_baseline": "medium_high",
      "high_risk_conditions": ["IBAN personal", "crypto", "criza emotionala"],
      "false_positive_guards": ["site oficial consistent, entitate juridica verificabila"],
      "official_verification_paths": ["site oficial ONG", "verificare entitate juridica"],
      "source_refs": ["europol_charity_scams"]
    },
    {
      "code": "IMP-11",
      "name": "romance_militar_doctor_strain",
      "description": "Relatie la distanta care cere bani, documente sau plata unor taxe/expedieri fictive.",
      "common_channels": ["social_dm", "whatsapp", "email", "ocr_image"],
      "impersonated_identity": ["militar", "doctor", "contractor", "partener romantic"],
      "attack_goal": ["bani", "date_personale", "copy_id"],
      "typical_user_action_requested": ["trimite bani", "plateste coletul", "trimite CI"],
      "severity_baseline": "high",
      "high_risk_conditions": ["urgenta emotionala", "fotografii suspecte", "evitarea intalnirii reale"],
      "false_positive_guards": ["fara cereri de bani/date"],
      "official_verification_paths": ["reverse image", "verificare out-of-band"],
      "source_refs": ["igpr_romance_scam"]
    },
    {
      "code": "IMP-12",
      "name": "autoritati_internationale_sextortion_legal_threat",
      "description": "Fake legal threat, sextortion sau corespondenta falsa de la Europol/Interpol/procuror/avocat.",
      "common_channels": ["email", "html_email", "pdf", "attachment", "sms", "whatsapp"],
      "impersonated_identity": ["Europol", "Interpol", "procuror", "instanta", "avocat"],
      "attack_goal": ["bani", "crypto", "panica"],
      "typical_user_action_requested": ["plateste amenda", "raspunde urgent", "deschide ordinul atasat"],
      "severity_baseline": "critical",
      "high_risk_conditions": ["bitcoin", "deadline scurt", "acuzatii sexuale/penale"],
      "false_positive_guards": ["corespondenta legala reala e verificabila prin dosar/canal oficial"],
      "official_verification_paths": ["contact oficial institutie", "verificare dosar"],
      "source_refs": ["igpr_gov_impersonation", "europol_fake_correspondence"]
    },
    {
      "code": "IMP-13",
      "name": "telecom_utilitati",
      "description": "Impersonare operator telecom sau furnizor utilitati cu facturi, deconectare, actualizare date ori oferte false.",
      "common_channels": ["sms", "email", "html_email", "ocr_image", "qr"],
      "impersonated_identity": ["Orange", "Vodafone", "Digi", "E.ON", "PPC", "Electrica", "Hidroelectrica"],
      "attack_goal": ["bani", "card", "malware", "lead_capture"],
      "typical_user_action_requested": ["plateste factura", "actualizeaza datele", "instaleaza aplicatia", "confirma oferta"],
      "severity_baseline": "high",
      "high_risk_conditions": ["deconectare iminenta", "alt domeniu", "premiu fals", "investitie falsa"],
      "false_positive_guards": ["factura/portal pe domeniul oficial", "SMS Electrica 1874 + electricafurnizare.ro"],
      "official_verification_paths": ["site official", "app officiala", "datele din factura reala"],
      "source_refs": ["orange_smishing", "vodafone_fraud", "digi_sensitive_data", "electrica_domain", "electrica_sms", "eon_false_messages", "eon_phishing", "ppc_stop_fraud", "hidroelectrica_invest"]
    }
  ],
  "signals": [
    {"signal_slug":"state_brand_on_wrong_channel_asks_payment","text":"institutie de stat + cerere de plata/date pe canal neobisnuit","detectable_in":["text","html","pdf","ocr","attachment"],"regex_or_heuristic":"brand_stat + request_sensitive","required_context":"canal gresit sau link extern","verification_method":"site/contact oficial","power":"decisive","verdict_effect":"can_raise_dangerous_with_combo","false_positive_guard":"informare oficiala fara cerere sensibila","source_refs":["igpr_gov_impersonation","anaf_warning","ghiseul_phishing"]},
    {"signal_slug":"safe_account_request","text":"cerere de mutare bani in cont sigur","detectable_in":["text","phone_transcript","ocr"],"regex_or_heuristic":"cont sigur|safe account","required_context":"impersonare banca/politie","verification_method":"hard rule","power":"decisive","verdict_effect":"hard_dangerous","false_positive_guard":"none","source_refs":["igpr_spoofing","revolut_vishing"]},
    {"signal_slug":"otp_requested_by_human","text":"OTP/PIN/CVV/cod WhatsApp cerut de om sau introdus pe domeniu neoficial","detectable_in":["text","form","html","phone_transcript","ocr"],"regex_or_heuristic":"otp|cvv|pin|verification code","required_context":"cerere activa","verification_method":"hard rule","power":"decisive","verdict_effect":"hard_dangerous","false_positive_guard":"mesajele de avertizare «nu comunica OTP»","source_refs":["revolut_vishing","whatsapp_code","ing_never_ask","raiffeisen_phishing","bcr_phishing","bt_fraud_reco"]},
    {"signal_slug":"remote_access_requested","text":"cerere AnyDesk/TeamViewer/Quick Assist","detectable_in":["text","html","phone_transcript"],"regex_or_heuristic":"AnyDesk|TeamViewer|Quick Assist|remote access","required_context":"apel sau mesaj necerut","verification_method":"hard rule","power":"decisive","verdict_effect":"hard_dangerous","false_positive_guard":"suport initiat de utilizator din canal oficial","source_refs":["microsoft_support","revolut_vishing","bt_fraud_reco","ing_smishing"]},
    {"signal_slug":"gift_card_or_crypto_payment","text":"plata ceruta in gift card sau crypto pentru suport/taxe/utilitati","detectable_in":["text","html","pdf"],"regex_or_heuristic":"gift card|bitcoin|usdt|crypto","required_context":"nu este achizitie legitima Apple/crypto intr-o entitate autorizata","verification_method":"hard rule","power":"decisive","verdict_effect":"hard_dangerous","false_positive_guard":"achizitie legitima in mediu autorizat","source_refs":["microsoft_support","apple_gift_card","europol_fake_correspondence"]},
    {"signal_slug":"courier_tiny_fee_card_request","text":"curier + taxa mica + card/PIN/CVV","detectable_in":["text","html","ocr","qr"],"regex_or_heuristic":"brand_curier + fee + card","required_context":"URL final neoficial","verification_method":"allowlist de domenii","power":"decisive","verdict_effect":"hard_dangerous","false_positive_guard":"tracking real fara cerere sensibila","source_refs":["fan_sms","sameday_phishing","posta_phishing","orange_smishing"]},
    {"signal_slug":"lookalike_or_non_official_domain","text":"domeniu final neoficial sau look-alike","detectable_in":["link","html","form","qr"],"regex_or_heuristic":"final_url not in official_domains or fuzzy brand match","required_context":"claim de brand","verification_method":"resolver + allowlist","power":"strong","verdict_effect":"can_raise_suspect","false_positive_guard":"third-party legitim aprobat public","source_refs":["electrica_domain","ghiseul_terms","olx_no_payment_links","hidroelectrica_invest"]},
    {"signal_slug":"bec_supplier_iban_change","text":"schimbare IBAN sau exceptie de proces in BEC","detectable_in":["email","pdf","attachment","ocr"],"regex_or_heuristic":"noul IBAN|confidential|urgent","required_context":"furnizor/sef pretins","verification_method":"callback procedural","power":"strong","verdict_effect":"can_raise_dangerous_with_combo","false_positive_guard":"schimbare confirmata procedural","source_refs":["dnsc_bec","orange_message_from_boss","ing_ceo_fraud"]},
    {"signal_slug":"marketplace_payment_link","text":"platforma marketplace pretinsa trimite link de plata/incasare in chat","detectable_in":["text","social_dm","ocr","link"],"regex_or_heuristic":"olx|publi24 + link + card/otp","required_context":"iesire din platforma","verification_method":"verifica doar in contul oficial","power":"decisive","verdict_effect":"hard_dangerous","false_positive_guard":"comanda vizibila in contul oficial","source_refs":["olx_linkuri_false","olx_no_payment_links","olx_livrare_faq"]},
    {"signal_slug":"deepfake_investment_with_lead_form","text":"persoana publica/brand financiar + profit + lead form/WhatsApp","detectable_in":["text","html","ocr"],"regex_or_heuristic":"public_figure + profit promise + form","required_context":"investitii/crypto","verification_method":"ASF/BNR/site oficial","power":"strong","verdict_effect":"can_raise_dangerous_with_combo","false_positive_guard":"articol jurnalistic fara CTA financiar","source_refs":["bnr_deepfake","asf_whatsapp","hidroelectrica_invest"]},
    {"signal_slug":"utility_disconnect_link","text":"deconectare utilitati/telecom + link de plata nesigur","detectable_in":["sms","email","ocr","html"],"regex_or_heuristic":"deconectare|suspendare + plata + link","required_context":"alt domeniu sau alt sender decat canalul oficial","verification_method":"allowlist domeniu/sender","power":"strong","verdict_effect":"can_raise_dangerous_with_combo","false_positive_guard":"portal oficial din factura","source_refs":["electrica_sms","eon_false_messages","vodafone_fraud","digi_sensitive_data"]},
    {"signal_slug":"marketing_only_or_hidden_link_only","text":"marketing hype sau anchor mismatch fara alta cerere sensibila","detectable_in":["text","html"],"regex_or_heuristic":"promo only or hidden_link_only","required_context":"fara cerere sensibila si provider clean","verification_method":"ceiling suspect","power":"weak","verdict_effect":"never_decides_alone","false_positive_guard":"newslettere legitime","source_refs":["ecc_fake_stores","emag_campaigns"]}
  ],
  "verification_sources": [
    {"brand":"ANAF","official_domains":["anaf.ro"],"official_apps_or_deeplinks":["needs_confirmation"],"official_phone_or_contact_page":"anaf.ro","never_ask_for":"date bancare sau personale prin apeluri/mesaje frauduloase","verification_method":"anaf.ro / SPV","confidence":"high","caveats":"warning captured via official search result"},
    {"brand":"Politia Romana","official_domains":["politiaromana.ro"],"official_apps_or_deeplinks":[],"official_phone_or_contact_page":"politiaromana.ro","never_ask_for":"plati pentru evitarea unor proceduri judiciare prin emailuri ce pretind a fi oficiale","verification_method":"site/contact oficial","confidence":"high","caveats":""},
    {"brand":"BNR","official_domains":["bnr.ro"],"official_apps_or_deeplinks":[],"official_phone_or_contact_page":"bnr.ro","never_ask_for":"date despre conturi, carduri, credite ori aplicatii bancare prin telefon/SMS/WhatsApp","verification_method":"bnr.ro + registre BNR","confidence":"high","caveats":""},
    {"brand":"ASF","official_domains":["asfromania.ro"],"official_apps_or_deeplinks":[],"official_phone_or_contact_page":"asfromania.ro","never_ask_for":"apeluri de la Tel Verde; cere verificarea entitatilor in registru","verification_method":"registre ASF","confidence":"high","caveats":""},
    {"brand":"Ghiseul.ro","official_domains":["ghiseul.ro"],"official_apps_or_deeplinks":["ghiseul.ro only"],"official_phone_or_contact_page":"ghiseul.ro/ghiseul/public/informatii/contact","never_ask_for":"nu anunta prin SMS/email aparitia unei obligatii de plata","verification_method":"ghiseul.ro only","confidence":"high","caveats":""},
    {"brand":"FAN Courier","official_domains":["fancourier.ro"],"official_apps_or_deeplinks":["needs_confirmation"],"official_phone_or_contact_page":"fancourier.ro/contact","never_ask_for":"linkuri false care solicita date bancare","verification_method":"site/app oficiala","confidence":"high","caveats":""},
    {"brand":"Posta Romana","official_domains":["posta-romana.ro"],"official_apps_or_deeplinks":[],"official_phone_or_contact_page":"posta-romana.ro","never_ask_for":"informatii bancare, numere de card, PIN sau taxe de livrare online","verification_method":"site oficial","confidence":"high","caveats":""},
    {"brand":"Sameday","official_domains":["sameday.ro"],"official_apps_or_deeplinks":["needs_confirmation"],"official_phone_or_contact_page":"sameday.ro/contact","never_ask_for":"informatii personale sau taxe suplimentare din mesaje cu actiune imediata prin link","verification_method":"site oficial","confidence":"high","caveats":""},
    {"brand":"OLX","official_domains":["olx.ro","ajutor.olx.ro","livrare.olx.ro"],"official_apps_or_deeplinks":["official only"],"official_phone_or_contact_page":"ajutor.olx.ro","never_ask_for":"nu furnizeaza linkuri de plati pentru transferul banilor","verification_method":"doar in cont/help oficial","confidence":"high","caveats":""},
    {"brand":"Revolut","official_domains":["revolut.com","help.revolut.com"],"official_apps_or_deeplinks":["app.revolut.com"],"official_phone_or_contact_page":"help.revolut.com","never_ask_for":"safe account, OTP la telefon, remote access","verification_method":"in-app / help official","confidence":"high","caveats":""},
    {"brand":"BT","official_domains":["bancatransilvania.ro","intreb.bancatransilvania.ro"],"official_apps_or_deeplinks":["btpay","bt24","neo bt official"],"official_phone_or_contact_page":"bancatransilvania.ro/call-center","never_ask_for":"user, parola, OTP sau instalarea AnyDesk","verification_method":"site/app oficiala","confidence":"high","caveats":""},
    {"brand":"BCR","official_domains":["bcr.ro"],"official_apps_or_deeplinks":["George official"],"official_phone_or_contact_page":"bcr.ro/ro/contact","never_ask_for":"date de autentificare bancara prin mesaje phishing","verification_method":"George / pagina contact","confidence":"high","caveats":""},
    {"brand":"ING","official_domains":["ing.ro"],"official_apps_or_deeplinks":["Home'Bank official"],"official_phone_or_contact_page":"ing.ro/ing-in-romania/contact","never_ask_for":"date bancare, parole, OTP sau instalare de program pentru actualizare date","verification_method":"Home'Bank / ing.ro","confidence":"high","caveats":""},
    {"brand":"Raiffeisen","official_domains":["raiffeisen.ro","bank.raiffeisen.ro"],"official_apps_or_deeplinks":["Smart Mobile official"],"official_phone_or_contact_page":"raiffeisen.ro","never_ask_for":"formulare/programe/redirectari care cer date personale; PIN/parole la telefon","verification_method":"site/app oficiala","confidence":"high","caveats":""},
    {"brand":"Orange","official_domains":["orange.ro"],"official_apps_or_deeplinks":["official only"],"official_phone_or_contact_page":"orange.ro","never_ask_for":"needs_confirmation","verification_method":"orange.ro / aplicatia oficiala","confidence":"medium","caveats":"ghiduri bune, formula standard never-ask incompleta"},
    {"brand":"Vodafone","official_domains":["vodafone.ro"],"official_apps_or_deeplinks":["official only"],"official_phone_or_contact_page":"vodafone.ro","never_ask_for":"needs_confirmation","verification_method":"vodafone.ro","confidence":"medium","caveats":""},
    {"brand":"Digi","official_domains":["digi.ro"],"official_apps_or_deeplinks":["official only"],"official_phone_or_contact_page":"digi.ro/ghid-clienti","never_ask_for":"date sensibile prin SMS/e-mail sau date bancare pentru premii","verification_method":"digi.ro","confidence":"high","caveats":""},
    {"brand":"E.ON","official_domains":["eon.ro","eon-romania.ro"],"official_apps_or_deeplinks":["official only"],"official_phone_or_contact_page":"eon.ro/contact","never_ask_for":"mesaje false cu linkuri/atasamente; nu incaseaza facturi la domiciliu prin angajati","verification_method":"site oficial/date factura","confidence":"high","caveats":"foloseste allowlist explicit de domenii"},
    {"brand":"PPC Energie","official_domains":["ppcenergy.ro"],"official_apps_or_deeplinks":["myPPC official"],"official_phone_or_contact_page":"ppcenergy.ro","never_ask_for":"plati in numerar prin angajati","verification_method":"canale de plata listate oficial","confidence":"high","caveats":""},
    {"brand":"Electrica Furnizare","official_domains":["electricafurnizare.ro"],"official_apps_or_deeplinks":["MyElectrica official"],"official_phone_or_contact_page":"electricafurnizare.ro","never_ask_for":"plati prin alte canale; alte domenii; SMS de plata legitime doar de pe 1874","verification_method":"allowlist domeniu + sender 1874","confidence":"high","caveats":""},
    {"brand":"Hidroelectrica","official_domains":["hidroelectrica.ro"],"official_apps_or_deeplinks":[],"official_phone_or_contact_page":"hidroelectrica.ro","never_ask_for":"nu sustine platforme de investitii si opereaza un singur site oficial","verification_method":"site oficial si comunicate","confidence":"high","caveats":""},
    {"brand":"Microsoft","official_domains":["microsoft.com","support.microsoft.com"],"official_apps_or_deeplinks":["official only"],"official_phone_or_contact_page":"support.microsoft.com","never_ask_for":"gift card, crypto, apel la numar din pop-up","verification_method":"support.microsoft.com","confidence":"high","caveats":""},
    {"brand":"Apple","official_domains":["apple.com","support.apple.com"],"official_apps_or_deeplinks":["apps.apple.com"],"official_phone_or_contact_page":"support.apple.com","never_ask_for":"Apple gift cards pentru utilitati/datorii/taxe","verification_method":"support.apple.com","confidence":"high","caveats":""},
    {"brand":"WhatsApp","official_domains":["whatsapp.com","faq.whatsapp.com"],"official_apps_or_deeplinks":["wa.me"],"official_phone_or_contact_page":"whatsapp.com/security","never_ask_for":"codul de 6 cifre sau PIN-ul 2FA","verification_method":"faq/security official","confidence":"high","caveats":""}
  ],
  "gate_mapping": {
    "identity_status_rules": {
      "OFFICIAL_MATCH": "claimed brand verified, final_url in official_domains, no provider hit",
      "BRAND_MISMATCH": "claimed brand but final_url not in official_domains",
      "LOOKALIKE_DOMAIN": "fuzzy brand match / homoglyph / typo",
      "NO_MATCH": "claim cannot be verified in registry/source map",
      "NEEDS_CONFIRMATION": "source missing or unresolved"
    },
    "request_sensitive_rules": {
      "none": ["informational", "promo", "tracking only"],
      "moderate": ["phone number", "email", "order confirmation"],
      "high": ["copy_id", "iban", "login email"],
      "hard_sensitive": ["otp", "pin", "cvv", "full_card", "password", "seed_phrase", "remote_access", "safe_account", "gift_card_payment", "crypto_payment"]
    },
    "ceiling_rules": {
      "marketing_only_max": "SUSPECT",
      "hidden_link_only_max": "SUSPECT",
      "registry_no_match_only_max": "SUSPECT",
      "source_error_never_downgrades_to_safe": true,
      "provider_malicious_is_hard_dangerous": true,
      "official_clean_no_sensitive_can_be_safe": true,
      "established_clean_no_sensitive_can_be_safe": true,
      "identity_spoof_plus_hard_sensitive_or_wrong_channel": "PERICULOS"
    },
    "expected_semantic_review_fields": ["risk_class", "summary", "reason_codes", "next_checks"]
  },
  "false_positive_guards": [
    "official clean domain + no sensitive request => SIGUR candidate",
    "bank OTP warning message saying 'nu comunica codul' => SIGUR candidate",
    "newsletter promo on official domain with public regulation => SIGUR candidate",
    "tracking link resolving to official courier domain and asking no card => SIGUR candidate",
    "short link that resolves to official allowlisted domain => SIGUR candidate",
    "app-store / google-play deep link published on official brand domain => SIGUR candidate",
    "NO_MATCH in registry alone => max SUSPECT",
    "marketing urgency alone => max SUSPECT",
    "anchor text mismatch alone => max SUSPECT"
  ],
  "fixtures": [
    {
      "id": "imp_d_001",
      "family": "IMP-01",
      "channel": "sms",
      "input_text": "ANAF: Aveti o obligatie fiscala restanta. Pentru a evita suspendarea, achitati acum si confirmati datele cardului.",
      "urls": ["https://anaf-plata-secure.example"],
      "expected_extractions": {"brands":["ANAF"],"requested":["card","cvv"],"links":["https://anaf-plata-secure.example"]},
      "expected_signals": ["state_brand_on_wrong_channel_asks_payment","lookalike_or_non_official_domain"],
      "mocked_provider_results": {"final_url":"https://anaf-plata-secure.example","web_risk":"MALICIOUS","urlhaus":"HIT","domain_age_days":2},
      "expected_semantic_review": {"risk_class":"dangerous","reason_codes":["STATE_BRAND","ASK_CARD","MALICIOUS_URL","BRAND_MISMATCH"]},
      "expected_final_verdict": "PERICULOS",
      "why": "Institutie de stat + cerere card + domeniu neoficial cu hit provider."
    },
    {
      "id": "imp_d_002",
      "family": "IMP-02",
      "channel": "phone_transcript",
      "input_text": "Buna ziua, sun de la banca impreuna cu Politia. Aveti un credit fraudulos in desfasurare, mutati urgent fondurile intr-un cont sigur pe care vi-l dictam.",
      "urls": [],
      "expected_extractions": {"brands":["banca","Politia"],"requested":["transfer"],"phrases":["cont sigur"]},
      "expected_signals": ["safe_account_request"],
      "mocked_provider_results": {"caller_id":"spoofed_local","web_risk":"N/A","urlhaus":"N/A"},
      "expected_semantic_review": {"risk_class":"dangerous","reason_codes":["SAFE_ACCOUNT","PHONE_SPOOFING_PATTERN"]},
      "expected_final_verdict": "PERICULOS",
      "why": "Regula este hard: safe account in numele bancii/politiei."
    },
    {
      "id": "imp_d_003",
      "family": "IMP-03",
      "channel": "sms",
      "input_text": "FAN Courier: coletul tau nu poate fi livrat pana nu alegi lockerul si achiti taxa de 7,99 lei.",
      "urls": ["https://fan-locker-choice.example"],
      "expected_extractions": {"brands":["FAN Courier"],"requested":["card"],"links":["https://fan-locker-choice.example"]},
      "expected_signals": ["courier_tiny_fee_card_request","lookalike_or_non_official_domain"],
      "mocked_provider_results": {"final_url":"https://fan-locker-choice.example","web_risk":"MALICIOUS","urlhaus":"HIT","domain_age_days":1},
      "expected_semantic_review": {"risk_class":"dangerous","reason_codes":["COURIER_FEE","ASK_CARD","MALICIOUS_URL"]},
      "expected_final_verdict": "PERICULOS",
      "why": "Tipar documentat oficial de FAN."
    },
    {
      "id": "imp_d_004",
      "family": "IMP-04",
      "channel": "ocr_image",
      "input_text": "Windows Defender Alert! Sunati imediat la numarul afisat. Dispozitivul este compromis.",
      "urls": ["https://microsoft-secure-assist.example"],
      "expected_extractions": {"brands":["Microsoft"],"requested":["call","remote_access"],"links":["https://microsoft-secure-assist.example"]},
      "expected_signals": ["remote_access_requested"],
      "mocked_provider_results": {"final_url":"https://microsoft-secure-assist.example","web_risk":"MALICIOUS","urlhaus":"MISS","domain_age_days":5},
      "expected_semantic_review": {"risk_class":"dangerous","reason_codes":["TECH_SUPPORT_SCAM","REMOTE_ACCESS"]},
      "expected_final_verdict": "PERICULOS",
      "why": "Pop-up + numar de telefon + remote access = hard dangerous."
    },
    {
      "id": "imp_d_005",
      "family": "IMP-05",
      "channel": "whatsapp",
      "input_text": "Buna, sunt eu. Mi s-a stricat telefonul, salveaza numarul nou si trimite-mi acum 1280 lei, iti dau inapoi seara.",
      "urls": [],
      "expected_extractions": {"brands":[],"requested":["transfer"],"social":["whatsapp"]},
      "expected_signals": ["safe_account_request"],
      "mocked_provider_results": {"web_risk":"N/A"},
      "expected_semantic_review": {"risk_class":"dangerous","reason_codes":["IMPERSONATED_RELATIVE","URGENT_TRANSFER"]},
      "expected_final_verdict": "PERICULOS",
      "why": "Urgenta emotionala + numar nou + cerere de bani."
    },
    {
      "id": "imp_d_006",
      "family": "IMP-06",
      "channel": "email",
      "input_text": "Salut, foloseste noul IBAN din factura atasata. E o plata sensibila, nu implica pe nimeni altcineva si trimite confirmarea azi.",
      "urls": [],
      "expected_extractions": {"brands":["furnizor","CEO"],"requested":["transfer"],"attachments":["invoice.pdf"]},
      "expected_signals": ["bec_supplier_iban_change"],
      "mocked_provider_results": {"sender_domain_reputation":"unknown","web_risk":"N/A"},
      "expected_semantic_review": {"risk_class":"dangerous","reason_codes":["BEC","IBAN_CHANGE","PROCESS_BYPASS"]},
      "expected_final_verdict": "PERICULOS",
      "why": "Schimbare IBAN + confidentialitate + urgenta."
    },
    {
      "id": "imp_d_007",
      "family": "IMP-07",
      "channel": "social_dm",
      "input_text": "Guvernatorul BNR explica in video cum poti dubla investitia daca intri azi. Completeaza formularul si vei fi sunat de consultant.",
      "urls": ["https://bnr-profit-fast.example"],
      "expected_extractions": {"brands":["BNR"],"requested":["lead_form"],"links":["https://bnr-profit-fast.example"]},
      "expected_signals": ["deepfake_investment_with_lead_form","lookalike_or_non_official_domain"],
      "mocked_provider_results": {"final_url":"https://bnr-profit-fast.example","web_risk":"MALICIOUS","urlhaus":"MISS","domain_age_days":3},
      "expected_semantic_review": {"risk_class":"dangerous","reason_codes":["DEEPFAKE_INVESTMENT","BRAND_MISMATCH"]},
      "expected_final_verdict": "PERICULOS",
      "why": "BNR a avertizat explicit asupra acestui tipar."
    },
    {
      "id": "imp_d_008",
      "family": "IMP-08",
      "channel": "whatsapp",
      "input_text": "Sunt cumparatorul de pe OLX. Ca sa primesti banii, intra pe linkul de livrare securizata si completeaza cardul.",
      "urls": ["https://olx-livrare-pay.example"],
      "expected_extractions": {"brands":["OLX"],"requested":["card"],"links":["https://olx-livrare-pay.example"]},
      "expected_signals": ["marketplace_payment_link","lookalike_or_non_official_domain"],
      "mocked_provider_results": {"final_url":"https://olx-livrare-pay.example","web_risk":"MALICIOUS","urlhaus":"HIT","domain_age_days":1},
      "expected_semantic_review": {"risk_class":"dangerous","reason_codes":["OLX_PHISHING","ASK_CARD"]},
      "expected_final_verdict": "PERICULOS",
      "why": "OLX spune explicit ca nu furnizeaza asemenea linkuri."
    },
    {
      "id": "imp_d_009",
      "family": "IMP-09",
      "channel": "sms",
      "input_text": "Felicitari! Ai castigat voucher eMAG 1000 lei. Achita doar 9,99 lei taxa de procesare pentru activare.",
      "urls": ["https://voucher-emag-fast.example"],
      "expected_extractions": {"brands":["eMAG"],"requested":["card"],"links":["https://voucher-emag-fast.example"]},
      "expected_signals": ["lookalike_or_non_official_domain"],
      "mocked_provider_results": {"final_url":"https://voucher-emag-fast.example","web_risk":"MALICIOUS","urlhaus":"MISS","domain_age_days":6},
      "expected_semantic_review": {"risk_class":"dangerous","reason_codes":["FAKE_GIVEAWAY","ASK_CARD","BRAND_MISMATCH"]},
      "expected_final_verdict": "PERICULOS",
      "why": "Premiu improbabil + taxa mica + domeniu neoficial."
    },
    {
      "id": "imp_d_010",
      "family": "IMP-10",
      "channel": "qr",
      "input_text": "Doneaza pentru copiii afectati de incendiu. Scaneaza QR-ul si trimite pe contul personal al coordonatorului.",
      "urls": ["https://donatie-urgenta-help.example"],
      "expected_extractions": {"brands":["ONG"],"requested":["transfer"],"links":["https://donatie-urgenta-help.example"]},
      "expected_signals": ["lookalike_or_non_official_domain"],
      "mocked_provider_results": {"final_url":"https://donatie-urgenta-help.example","web_risk":"UNKNOWN","urlhaus":"MISS","domain_age_days":2},
      "expected_semantic_review": {"risk_class":"dangerous","reason_codes":["FAKE_DONATION","PERSONAL_ACCOUNT","EMOTIONAL_PRESSURE"]},
      "expected_final_verdict": "PERICULOS",
      "why": "Urgenta emotionala + canal neverificat + cont personal."
    },
    {
      "id": "imp_d_011",
      "family": "IMP-11",
      "channel": "social_dm",
      "input_text": "Sunt medic militar in misiune. Am nevoie sa platesti taxele pentru coletul meu si sa imi trimiti o copie dupa buletin pentru rezervare.",
      "urls": ["https://parcel-release-fee.example"],
      "expected_extractions": {"brands":[],"requested":["transfer","copy_id"],"links":["https://parcel-release-fee.example"]},
      "expected_signals": ["lookalike_or_non_official_domain"],
      "mocked_provider_results": {"final_url":"https://parcel-release-fee.example","web_risk":"UNKNOWN","domain_age_days":7},
      "expected_semantic_review": {"risk_class":"dangerous","reason_codes":["ROMANCE_SCAM","COPY_ID_REQUEST","FAKE_PARCEL_FEE"]},
      "expected_final_verdict": "PERICULOS",
      "why": "Tipar romance scam + bani + identitate."
    },
    {
      "id": "imp_d_012",
      "family": "IMP-12",
      "channel": "email",
      "input_text": "Europol Office: aveti un dosar sensibil. Pentru inchiderea urgenta a procedurii, achitati in Bitcoin in urmatoarele 6 ore.",
      "urls": ["https://europol-case-close.example"],
      "expected_extractions": {"brands":["Europol"],"requested":["crypto_payment"],"links":["https://europol-case-close.example"]},
      "expected_signals": ["gift_card_or_crypto_payment","state_brand_on_wrong_channel_asks_payment"],
      "mocked_provider_results": {"final_url":"https://europol-case-close.example","web_risk":"MALICIOUS","urlhaus":"MISS","domain_age_days":4},
      "expected_semantic_review": {"risk_class":"dangerous","reason_codes":["FAKE_AUTHORITY","BITCOIN_PAYMENT","LEGAL_THREAT"]},
      "expected_final_verdict": "PERICULOS",
      "why": "Autoritate + bitcoin + termen scurt."
    },
    {
      "id": "imp_d_013",
      "family": "IMP-13",
      "channel": "sms",
      "input_text": "Electrica Furnizare: serviciul va fi intrerupt astazi pentru neplata. Platiti soldul prin linkul de mai jos.",
      "urls": ["https://electrica-bill-settle.example"],
      "expected_extractions": {"brands":["Electrica Furnizare"],"requested":["payment"],"links":["https://electrica-bill-settle.example"]},
      "expected_signals": ["utility_disconnect_link","lookalike_or_non_official_domain"],
      "mocked_provider_results": {"final_url":"https://electrica-bill-settle.example","web_risk":"MALICIOUS","urlhaus":"HIT","domain_age_days":1},
      "expected_semantic_review": {"risk_class":"dangerous","reason_codes":["UTILITY_DISCONNECT","BRAND_MISMATCH","MALICIOUS_URL"]},
      "expected_final_verdict": "PERICULOS",
      "why": "Electrica a documentat explicit tiparul si canalul legitim 1874."
    },
    {
      "id": "imp_s_001",
      "family": "IMP-03",
      "channel": "sms",
      "input_text": "Coletul tau este in tranzit. Verifica statusul aici.",
      "urls": ["https://track-package-fast.example"],
      "expected_extractions": {"requested":["tracking"],"links":["https://track-package-fast.example"]},
      "expected_signals": ["lookalike_or_non_official_domain"],
      "mocked_provider_results": {"final_url":"https://track-package-fast.example","web_risk":"UNKNOWN","urlhaus":"MISS","domain_age_days":12},
      "expected_semantic_review": {"risk_class":"suspect","reason_codes":["TRACKING_LINK_UNKNOWN"]},
      "expected_final_verdict": "SUSPECT",
      "why": "Doar tracking si domeniu neconfirmat, fara cerere sensibila."
    },
    {
      "id": "imp_s_002",
      "family": "IMP-09",
      "channel": "html_email",
      "input_text": "Super oferta valabila azi. Deschide pagina si vezi produsele favorite.",
      "urls": ["https://super-price-deals.example"],
      "expected_extractions": {"requested":["visit_page"],"links":["https://super-price-deals.example"]},
      "expected_signals": ["marketing_only_or_hidden_link_only"],
      "mocked_provider_results": {"final_url":"https://super-price-deals.example","web_risk":"UNKNOWN","urlhaus":"MISS","domain_age_days":15},
      "expected_semantic_review": {"risk_class":"suspect","reason_codes":["MARKETING_ONLY","UNKNOWN_DOMAIN"]},
      "expected_final_verdict": "SUSPECT",
      "why": "Marketing heavy si domeniu neconfirmat, fara cerere sensibila."
    },
    {
      "id": "imp_s_003",
      "family": "IMP-06",
      "channel": "pdf",
      "input_text": "Factura actualizata pentru luna curenta. Va rugam sa verificati datele de plata.",
      "urls": [],
      "expected_extractions": {"attachments":["factura.pdf"]},
      "expected_signals": ["bec_supplier_iban_change"],
      "mocked_provider_results": {"sender_domain_reputation":"neutral"},
      "expected_semantic_review": {"risk_class":"suspect","reason_codes":["POTENTIAL_IBAN_CHANGE"]},
      "expected_final_verdict": "SUSPECT",
      "why": "Doar schimbare potentiala de coordonate, fara alte dovezi tehnice inline."
    },
    {
      "id": "imp_safe_001",
      "family": "IMP-02",
      "channel": "sms",
      "input_text": "BCR: Codul tau de autorizare este 593821. Nu il comunica nimanui.",
      "urls": [],
      "expected_extractions": {"brands":["BCR"],"requested":[]},
      "expected_signals": [],
      "mocked_provider_results": {"sender_status":"official_sms_sender","web_risk":"N/A"},
      "expected_semantic_review": {"risk_class":"safe","reason_codes":["LEGIT_SECURITY_MESSAGE"]},
      "expected_final_verdict": "SIGUR",
      "why": "Mesaj de securitate legitim, fara cerere de a divulga codul."
    },
    {
      "id": "imp_safe_002",
      "family": "IMP-03",
      "channel": "link",
      "input_text": "Urmareste AWB-ul tau in contul OLX sau pe site-ul curierului.",
      "urls": ["https://livrare.olx.ro/intrebari-frecvente/"],
      "expected_extractions": {"brands":["OLX"],"requested":[],"links":["https://livrare.olx.ro/intrebari-frecvente/"]},
      "expected_signals": [],
      "mocked_provider_results": {"final_url":"https://livrare.olx.ro/intrebari-frecvente/","web_risk":"SAFE","urlhaus":"MISS"},
      "expected_semantic_review": {"risk_class":"safe","reason_codes":["OFFICIAL_DOMAIN","NO_SENSITIVE_REQUEST"]},
      "expected_final_verdict": "SIGUR",
      "why": "Domeniu oficial si mesaj fara cerere sensibila."
    },
    {
      "id": "imp_safe_003",
      "family": "IMP-13",
      "channel": "sms",
      "input_text": "Electrica Furnizare: verifica factura in contul tau MyElectrica.",
      "urls": ["https://www.electricafurnizare.ro/"],
      "expected_extractions": {"brands":["Electrica Furnizare"],"requested":[],"links":["https://www.electricafurnizare.ro/"]},
      "expected_signals": [],
      "mocked_provider_results": {"final_url":"https://www.electricafurnizare.ro/","web_risk":"SAFE","urlhaus":"MISS"},
      "expected_semantic_review": {"risk_class":"safe","reason_codes":["OFFICIAL_DOMAIN","NO_SENSITIVE_REQUEST"]},
      "expected_final_verdict": "SIGUR",
      "why": "Link oficial, fara card/OTP si compatibil cu canalele comunicate public."
    }
  ],
  "source_index": [
    {"id":"igpr_gov_impersonation","title":"Politia Romana - fraude online cu Europol/Interpol/Politia","url":"https://politiaromana.ro/ro/stiri/atentie-un-nou-tip-de-fraude-online"},
    {"id":"igpr_spoofing","title":"Politia Romana - tehnica de tip spoofing","url":"https://politiaromana.ro/ro/stiri-si-media/comunicate/tehnica-de-tip-spoofing-o-alta-metoda-de-inselaciune"},
    {"id":"igpr_romance_scam","title":"Politia Romana - prevenirea inselaciunilor romantice","url":"https://politiaromana.ro/ro/prevenire/recomandari-preventive/prevenirea-criminalitatii-informatice/prevenirea-inselaciunilor-romantice-romance-scam"},
    {"id":"anaf_warning","title":"ANAF - avertisment fraude in numele ANAF","url":"https://www.anaf.ro/"},
    {"id":"ghiseul_phishing","title":"Ghiseul.ro - atentie la phishing","url":"https://www.ghiseul.ro/"},
    {"id":"ghiseul_terms","title":"Ghiseul.ro - site oficial SNEP","url":"https://www.ghiseul.ro/ghiseul/public/taxe/termenisiconditii"},
    {"id":"bnr_warning","title":"BNR - tentative de frauda in numele BNR","url":"https://www.bnr.ro/en/23738-informare-privind-tentative-de-frauda-in-numele-bnr"},
    {"id":"bnr_deepfake","title":"BNR - deepfake cu imaginea guvernatorului","url":"https://www.bnr.ro/25285-2026-02-18-tentativa-de-frauda-financiara-tip-deepfake-care-foloseste-imaginea-guvernatorului-bnr"},
    {"id":"asf_whatsapp","title":"ASF - grupuri false de investitii pe WhatsApp/Telegram","url":"https://www.asfromania.ro/ro/a/1523/atentie-la-entitati-neautorizate%21"},
    {"id":"fan_sms","title":"FAN Courier - tentativa de phishing prin SMS","url":"https://www.fancourier.ro/atentie-tentativa-de-phishing-prin-sms/"},
    {"id":"fan_smishing","title":"FAN Courier - alerta de smishing","url":"https://www.fancourier.ro/alerta-de-smishing/"},
    {"id":"sameday_phishing","title":"Sameday - cand un mesaj pare fraudulos","url":"https://sameday.ro/cand-un-mesaj-pare-fraudulos-cel-mai-probabil-asa-este/"},
    {"id":"posta_phishing","title":"Posta Romana - tentative de phishing","url":"https://www.posta-romana.ro/a1941/stiri/o-noua-tentativa-de-phishing-prin-sms-in-numele-postei-romane.html"},
    {"id":"olx_linkuri_false","title":"OLX - ai grija la linkurile false","url":"https://ajutor.olx.ro/olxhelpro/s/article/ai-grija-la-linkurile-false-pentru-articole-platite-recunoaste-semnalele-unui-atac-de-phishing-V7"},
    {"id":"olx_no_payment_links","title":"OLX - nu furnizeaza linkuri de plati","url":"https://ajutor.olx.ro/olxhelpro/s/"},
    {"id":"olx_livrare_faq","title":"OLX - livrare prin OLX FAQ","url":"https://livrare.olx.ro/intrebari-frecvente/"},
    {"id":"revolut_vishing","title":"Revolut - an urgent call out of the blue?","url":"https://help.revolut.com/en-RO/help/security-logging-in/how-do-i-protect-myself-from-fraudsters/fraud-education-vishing-impersonation/"},
    {"id":"bt_fraud_reco","title":"BT - recomandari pentru evitarea fraudelor online","url":"https://www.bancatransilvania.ro/news/comunicate-de-presa/recomandarile-bancii-transilvania-pentru-evita-tentativele-de-frauda-online"},
    {"id":"bcr_phishing","title":"BCR - tentative de frauda phishing","url":"https://www.bcr.ro/ro/persoane-fizice/informatii-utile/tentative-de-frauda-phishing"},
    {"id":"ing_never_ask","title":"ING - bancile nu cer date bancare, parole sau OTP prin canale nesigure","url":"https://ing.ro/inbusiness-blog-antreprenori/business-abc/Cum-te-fere-ti-de-dou---n-el-tori"},
    {"id":"ing_smishing","title":"ING - atacurile de smishing in Romania","url":"https://ing.ro/informatii-utile/ING-Bank-si-sendSMS"},
    {"id":"ing_ceo_fraud","title":"ING - CEO Fraud","url":"https://ing.ro/ing-in-romania/informatii-utile/securitate/ceo-fraud"},
    {"id":"ing_investment_fraud","title":"ING - castig prea frumos sa fie adevarat","url":"https://ing.ro/ing-in-romania/informatii-utile/securitate/fraude-investitii"},
    {"id":"raiffeisen_phishing","title":"Raiffeisen - despre phishing","url":"https://www.raiffeisen.ro/ro/corporatii/in-sprijinul-dumneavoastra/securitate/despre-phishing.html"},
    {"id":"orange_smishing","title":"Orange - cum sa recunosti tentativele de frauda prin SMS","url":"https://www.orange.ro/help/articole/cum-sa-recunosti-si-sa-eviti-tentativele-de-frauda-prin-sms-smishing"},
    {"id":"vodafone_fraud","title":"Vodafone - prevenirea de frauda","url":"https://www.vodafone.ro/frauda/"},
    {"id":"digi_sensitive_data","title":"Digi - nu solicita date sensibile sau date bancare pentru premii","url":"https://www.digi.ro/raportare-nereguli"},
    {"id":"electrica_domain","title":"Electrica Furnizare - emailurile legitime folosesc doar electricafurnizare.ro","url":"https://www.electricafurnizare.ro/cms/comunicate-de-presa/2026/electrica-furnizare-anunta-existenta-unei-tentative-de-phishing-prin-intermediul-careia-clientii-sunt-notificati-cu-privire-la-emiterea-unor-facturi-si-indemnati-sa-faca-plata-acestora-prin-accesarea/"},
    {"id":"electrica_sms","title":"Electrica Furnizare - SMS legitime de plata doar de pe 1874","url":"https://www.electricafurnizare.ro/cms/comunicate-de-presa/2024/electrica-furnizare-anunta-existenta-unei-tentative-de-frauda-prin-mijloace-de-plata-electronice-2/"},
    {"id":"eon_false_messages","title":"E.ON - mesaje false in numele companiei","url":"https://www.eon-romania.ro/ro/despre-noi/media/comunicate-de-presa/2022/EON-Energie-Romania-atrage-atentia-asupra-unor-mesaje-false-transmise-in-numele-companiei.html"},
    {"id":"eon_phishing","title":"E.ON - emailuri phishing catre clienti","url":"https://www.eon-romania.ro/ro/despre-noi/media/comunicate-de-presa/2023/EON-Energie-Romania-avertizea-asupra-unor-e-mailuri-de-tip-phishing-primite-de-clienti-ai-companiei.html"},
    {"id":"ppc_stop_fraud","title":"PPC Energie - stop frauda","url":"https://www.ppcenergy.ro/cine-suntem/guvernanta-corporativa/stop-frauda/"},
    {"id":"hidroelectrica_invest","title":"Hidroelectrica - tentative de frauda online","url":"https://www.hidroelectrica.ro/press-release/be34ffdd-821e-5bed-e6c1-1868bbf7cb79"},
    {"id":"microsoft_support","title":"Microsoft - protect yourself from tech support scams","url":"https://support.microsoft.com/en-us/windows/protect-yourself-from-tech-support-scams-2ebf91bd-f94c-2a8a-e541-f5c800d18435"},
    {"id":"apple_gift_card","title":"Apple - about gift card scams","url":"https://support.apple.com/en-us/120933"},
    {"id":"apple_social_engineering","title":"Apple - recognize and avoid social engineering","url":"https://support.apple.com/en-us/102568"},
    {"id":"whatsapp_code","title":"WhatsApp - never share your 6-digit code","url":"https://faq.whatsapp.com/506595211487528"},
    {"id":"whatsapp_security","title":"WhatsApp - account security tips","url":"https://faq.whatsapp.com/1095301557782068"},
    {"id":"europol_fake_correspondence","title":"Europol - beware scams involving fake correspondence","url":"https://www.europol.europa.eu/operations-services-and-innovation/public-awareness-and-prevention-guides/beware-scams-involving-fake-correspondence-europol"},
    {"id":"europol_charity_scams","title":"Europol - fake charity scams","url":"https://www.europol.europa.eu/operations-services-and-innovation/public-awareness-and-prevention-guides/how-can-you-stay-safe-online-during-global-crisis"},
    {"id":"dnsc_bec","title":"DNSC - BEC in buletinul H1 2025","url":"https://www.dnsc.ro/vezi/document/buletin-de-indicatori-statistici-si-tendinte-de-securitate-cibernetica-h1-2025"},
    {"id":"emag_phishing","title":"eMAG - cum sa te feresti de actiunile de phishing","url":"https://www.emag.ro/help/cum-sa-te-feresti-de-actiunile-de-phishing/"},
    {"id":"emag_campaigns","title":"eMAG - reguli si campanii oficiale in Help","url":"https://www.emag.ro/help/categorie/servicii/informatii-utile/"},
    {"id":"altex_support","title":"Altex - suport clienti","url":"https://altex.ro/suport-clienti/"},
    {"id":"altex_campaign","title":"Altex - campanie legitima 1 din 100","url":"https://altex.ro/100-cumparatori-1-castigator/pag/"},
    {"id":"ecc_fake_stores","title":"ECC Romania - fake stores / Black Friday 2025","url":"https://eccromania.ro/black-friday-si-cyber-monday-2025-cum-sa-recunosti-ofertele-reale/"},
    {"id":"orange_message_from_boss","title":"Orange - mesaj de la sef","url":"https://newsroom.orange.ro/blog/cum-recunosti-o-tentativa-de-phishing-scam-spam-sau-cryptojacking/"}
  ]
}
```

## Ce acoperă deja probabil SigurScan și unde sunt golurile reale

Dacă pipeline-ul tău deja face `URL resolution + Web Risk + URLhaus + phish DB + urlscan + domain age/RDAP + brand check`, atunci probabil acoperi deja o parte importantă din abuzurile grosolane: domenii nou-create, linkuri malițioase, clone evidente și shorteners rău-famate. Ce lipsește de obicei în astfel de sisteme este **stratul de policy semantic bazat pe ce spune explicit brandul real că nu face niciodată**. Acolo câștigi multă precizie: `safe account`, `OTP`, `remote access`, `gift card`, `curier + taxă + card`, `Electrica != alt domeniu decât electricafurnizare.ro`, `OLX != link de plată`. citeturn45search0turn31search0turn46search0turn23search0turn28search3

Golurile critice de implementat sunt patru. Primul: **brand-domain allowlists per entitate**, nu doar fuzzy brand detection. Al doilea: **never-ask map per brand**, cu severitate calibrată de canal. Al treilea: **out-of-band verification prompts** în explainability, mai ales pentru banking, BEC și ruda/prieten. Al patrulea: **hard false-positive guards** pentru newslettere, tracking, campanii și mesaje de securitate legitime. Fără aceste garde, vei avea un detector care prinde și hoțul, și poștașul, și bunica ce ți-a trimis linkul bun. citeturn28search4turn30search2turn42search15turn23search3

## Limitări și întrebări deschise

Nu am găsit, în această cercetare, o pagină anti-phishing Altex la fel de explicită precum cele de la OLX, Revolut, ING, Electrica sau FAN; de aceea, Altex trebuie ținut în `confidence: medium` și verificat mai ales prin domeniul oficial, pagina de suport și existența regulamentului campaniei. citeturn29search1turn29search3

Pentru DHL, pagina oficială de fraud awareness a fost identificată, dar nu am extras în aceeași profunzime formulările „never ask”. O poți folosi ca sursă oficială de allowlist și verificare, însă unele reguli specifice DHL trebuie marcate `needs_confirmation` până la extracția completă a textului. citeturn5search3

Pentru ANCOM, măsurile privind CLI spoofing sunt confirmate foarte bine de rezumatele oficiale DNSC despre implementarea blocării apelurilor falsificate, dar în această sesiune nu a fost izolată o pagină ANCOM consumer-facing echivalentă cu formulare anti-scam pe branduri comerciale. Practic, ANCOM trebuie tratat mai ales ca **sursă de context pentru fenomen**, nu ca `never_ask map` primar. citeturn48search2turn48search4

Fiindcă răspunsul trebuia să rămână utilizabil, JSON-ul inclus este un excerpt compact și nu extinde inline toate cele 120 de fixture-uri complete. Totuși, taxonomia, semnalele, maparea de verificare și contractul de gate sunt suficient de precise pentru a genera patch-ul complet fără a inventa reguli noi.