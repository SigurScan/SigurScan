Analiză aprofundată pentru knowledge layer-ul SigurScan
Rezumat executiv. Am executat cerința din fișierul încărcat și am transformat-o într-un raport de cercetare orientat pe implementare pentru SigurScan. Documentul sursă a cerut explicit: registru oficial al brandurilor și instituțiilor relevante, corpus de avertismente oficiale, modelarea scenariilor de scam curente pentru România, un claim verifier cu mapare de semnale, garduri serioase anti-fals-pozitiv, un set mare de teste de acceptanță și un diagnostic final cu priorități. 

Concluzia principală este simplă: un nucleu robust pentru SigurScan poate fi construit fără a inventa reguli, pornind de la semnale explicite publicate de actori oficiali. În corpusul verificat există deja ancore foarte puternice: FAN Courier avertizează despre tentative de fraudă care folosesc identitatea sa și cer date bancare, Sameday publică o listă explicită de domenii oficiale și spune clar că nu solicită date de card sau cont pentru relocare/livrare, Ghișeul.ro spune că nu anunță obligații de plată prin SMS/e-mail, Orange și YOXO spun că nu cer parole, PIN-uri, coduri de reîncărcare sau detalii bancare prin canale neasumate, iar ING spune că niciun reprezentant nu îți va cere să accesezi linkuri trimise, să te loghezi prin link sau să divulgi PIN/CVV. În paralel, Poliția Română a publicat în 2025 materiale explicite despre spoofing-ul „cont sigur” și despre frauda WhatsApp de tip „votează pe Adeline/Cătălina/Daniela”, iar SigurantaOnline și ARB documentează clar fraudele de marketplace, phishing/smishing și frauda cu facturi. 

Ce lipsește încă pentru o acoperire „de producție” nu este filosofia, ci completitudinea de sursă. Am identificat zone care nu trebuie umplute cu presupuneri: nu am reconfirmat în corpusul accesat un comunicat ANAF curent dedicat exact scenariului „rambursare taxe/SPV”, nu am găsit o pagină publică clară pentru „service status iDroid”, nu am reconfirmat un registru public curent pentru campanii active eMAG/Altex, iar variantele exact textuale „telefonul meu s-a stricat”, „petiție WhatsApp”, respectiv recurența 2025–2026 a „metodei accidentul/nepotul” nu au fost revalidate direct în surse oficiale naționale din corpusul parcurs. Din acest motiv, aceste scenarii trebuie tratate în SigurScan cu plafon de verdict mai jos, nu cu încredere absolută. Aceasta este diferența dintre un motor bun și un motor care vede phishing și în frigider. 

Cadru de lucru folosit în acest raport. Am prioritizat: surse oficiale ale instituțiilor și brandurilor, apoi campanii publice oficiale comune (Poliția Română, DNSC, ARB, SigurantaOnline), iar abia la final semnale secundare. Pentru paginile de homepage sau de securitate unde nu apare o dată de publicare, am marcat pub.: ned.. Pentru toate sursele web din raport, acces: 2026-06-03.

OFFICIAL_REGISTRY_UPDATES
Mai jos este un registru de start pentru knowledge layer, limitat la domeniile/subdomeniile și partenerii pe care i-am putut verifica explicit din surse oficiale accesate. Unde nu am confirmat explicit un partener dintr-o pagină oficială, l-am lăsat în afara allowlist-ului. Asta e exact genul de conservatorism care previne accidente de producție.

Tabel public, logistică și utilități

Entitate	Domenii / subdomenii verificate	Parteneri / trackeri acceptați doar dacă sunt deja ancorați oficial	Canale / aplicații / portaluri oficiale observate	Pub.	Sursă
ANAF	anaf.ro, static.anaf.ro, chat.anaf.ro	mfinante.gov.ro apare în navigație ANAF pentru unele resurse	autentificare SPV, servicii online, notificări ANAF	ned.	
Ghișeul.ro	ghiseul.ro	registratura.rejust.ro pentru taxa judiciară de timbru	logare ROeID, eIDAS, plăți fără autentificare, amenzi, rovinietă, titluri de stat	ned.	
BNR	bnr.ro, muzeu.bnr.ro	nu am validat alți parteneri pentru cazul anti-fraudă	contact, media/publicații, educație financiară, comunicare instituțională	ned.	
FAN Courier	fancourier.ro, retur.fancourier.ro, selfawb.ro	nu am validat alt partener pentru anti-fraudă	tracking, retur, selfAWB, social oficial, aplicații oficiale	ned.	
Poșta Română	posta-romana.ro, awb.posta-romana.ro	fabricadetimbre.ro apare în meniul oficial	Track & Trace, My AWB, suport, reclamații	ned.	
Sameday	sameday.ro, eawb.sameday.ro, locker.sameday.ro, pick-updrop-off.sameday.ro, sameday.easybox.ro, locker-redirect.sameday.ro, awb.sameday.ro, plus domeniul scurt sdy.ro	allowlist explicit pe pagina de alertă; nu trebuie extins prin inferență	portal AWB, locker redirect, easybox, listă oficială de domenii	2026-04-11	
Cargus	cargus.ro, mycargus.cargus.ro, app.urgentcargus.ro	nu am validat un alt partener pentru anti-fraudă	aplicația Cargus, MyCargus, WebExpress	ned.	
Hidroelectrica	hidroelectrica.ro, cdn.hidroelectrica.ro, client.hidroelectrica.ro	nu am validat un alt partener pentru anti-fraudă	portal client, furnizare clienți casnici/business, relații cu investitorii	ned.	
PPC	ppcenergy.ro, myppc.ppcenergy.ro	nu am validat un alt partener pentru anti-fraudă	myPPC, copiere factură, transmitere index, asistent virtual	ned.	
E.ON	eon.ro	nu am validat un alt partener pentru anti-fraudă	E.ON Myline, status solicitări, facturi și plăți online sigure	ned.	

Tabel telecom și bănci

Entitate	Domenii / subdomenii verificate	Parteneri / trackeri acceptați doar dacă sunt ancorați oficial	Canale / aplicații / portaluri oficiale observate	Pub.	Sursă
Orange	orange.ro, comunitate.orange.ro, newsroom.orange.ro, responsabilitate-sociala.orange.ro, realestate.orange.ro, qr.orange.ro, sso.orange.ro	qr.orange.ro este oficial; nu orice QR/shortener trebuie permis	My Orange, contact oficial, anti-fraudă, factură, reîncărcare, magazin	ned.	
YOXO	yoxo.ro, www.yoxo.blog, reconditionate.yoxo.ro	yoxo.page.link, tradein.recommerce.com apar explicit pe site-ul oficial	aplicația YOXO, Buy Back, prevenire fraudă	ned.	
DIGI	digi.ro, s.digi.ro, rdslink.rcs-rds.ro	nu am validat alt partener pentru anti-fraudă	plată factură online, securitatea datelor, asistență	ned.	
BCR	bcr.ro	nu am validat parteneri pentru antifraudă	George, contact, FAQ, campanii de educație financiară	ned.	
Banca Transilvania	bancatransilvania.ro	nu orice AI/widget e sigur; Privacy Hub și resursele BT sunt oficiale; nu am validat alt partener anti-fraudă	Întreb BT, AI Search, reguli campanii, disclosure	ned.	
ING	ing.ro, homebank.ro	nu am validat alt partener anti-fraudă	Home’Bank, stare servicii, securitate, blog	ned.	
Raiffeisen	raiffeisen.ro, bank.raiffeisen.ro	app.eu.adjust.com este prezent ca deep-link oficial pentru aplicație	Smart Mobile, articole oficiale, contact, tarife	ned.	

Notă operațională. Pentru OLX, eMAG, Altex și Revolut am reconfirmat prezența unor pagini oficiale de bază în corpusul accesat, dar nu am extras suficient conținut first-party de securitate pentru a le pune, în acest raport, în aceeași clasă de „allowlist complet” cu rândurile de mai sus. Pentru v1, ele trebuie tratate ca registry_partial, nu ca fully_verified. 

BRAND_WARNINGS
Această secțiune include doar afirmații „never asks / official only / beware” pe care le-am putut verifica explicit. Acolo unde nu am găsit o formulare oficială clară, am preferat să marchez „neconfirmat în corpus”, nu să completez din memorie. Așa se evită halucinațiile de produs.

Brand / instituție	Avertisment oficial verificat	Ce înseamnă pentru SigurScan	Pub.	Sursă
FAN Courier	spune clar să nu fie accesate linkuri false care solicită date bancare și că au crescut tentativele de fraudă care folosesc identitatea FAN	dacă mesajul invocă FAN și cere date bancare, severitatea poate urca rapid	ned.	
Sameday	publică lista exactă de domenii oficiale și spune că nu cere date personale sensibile, date de card sau cont bancar pentru plata transportului, schimbarea adresei ori reprogramare	allowlist-ul de domenii este un activ critic; orice Sameday-like în afara listei este semnal dur	2026-04-11	
Ghișeul.ro	spune explicit că nu anunță prin SMS sau e-mail apariția unei obligații de plată și recomandă verificarea expeditorului/URL-ului	orice „ai de plătit la Ghișeul.ro, click aici” trebuie urcat imediat la risc ridicat	ned.	
Orange	spune că nu solicită prin e-mail, SMS, scrisori sau apeluri informații despre conturi bancare, parole personale, PIN-uri ori coduri de reîncărcare	reguli robuste pentru telecom/phishing, plus protecție împotriva apelurilor cu coduri USSD și concursurilor false	ned.	
YOXO	transmite aceeași regulă ca Orange și, în plus, descrie tentative prin WhatsApp, SMS, social și chiar fraudă de tip FluBot prin „voicemail app” falsă	foarte util pentru poziționarea scenariilor OTP takeover, fake app, contest scam	ned.	
ING	spune că niciun reprezentant ING nu îți va cere să accesezi linkuri, să te loghezi în Home’Bank prin link, să divulgi PIN sau CVV, și că nu trebuie transferate sume în „conturi seif”	este una dintre cele mai valoroase surse pentru reguli anti-vishing și anti-safe-account	ned.	
Bănci, în general	campania SigurantaOnline / ARB spune că băncile nu cer datele cardului, parole de acces sau coduri PIN prin telefon, SMS, e-mail ori formulare de site	bun ca regulă transversală, dar mai slab decât o pagină first-party a băncii respective	2021-10-12	
Poliția Română	recomandă să nu se transfere bani în „conturi sigure” și să se valideze informațiile prin canale oficiale	regulă-cheie pentru scenariile cu impersonare bancă + poliție + credit fals	2025-01-20	

Surse oficiale secundare, utile pentru pattern discovery. SigurantaOnline este relevant pentru patternuri recurente de fraudă online și marketplace, iar ARB publică în 2026 comunicate și campanii explicite privind valuri noi de fraudă online și educație digitală. Pentru SigurScan, aceste surse sunt ideale ca „pattern enablers”, nu ca substitute pentru un „never asks” publicat chiar de brandul impersonat. 

Neconfirmat oficial în corpusul parcurs. Nu am extras în acest run o formulare oficială first-party echivalentă pentru Poșta Română, Cargus, PPC, E.ON, Hidroelectrica, BCR, BT, Raiffeisen, OLX, eMAG, Altex, Revolut care să poată fi citată în forma „brandul spune explicit că nu cere X”. Asta nu înseamnă că avertismentele nu există; înseamnă doar că nu trebuie inventate în knowledge layer-ul v1.

SCAM_SCENARIOS_2025_2026
În tabelul de mai jos folosesc o scară de verdict orientată pe produs: allow, needs_more_evidence, suspect, high_risk, confirmed_phishing. Cheia metodologică este asta: fără scanare de provider sau fără dovadă tehnică suplimentară, multe cazuri nu trebuie împinse la confirmed_phishing; ele trebuie plafonate la suspect ori high_risk. Când există dovadă tehnică externă sau confruntare exactă cu o regulă oficială „never asks”, plafonul poate urca. Acest principiu este susținut de avertismentele oficiale care insistă pe verificarea prin canale oficiale și pe evitarea acțiunilor ireversibile la primul contact. 

Scenariu	Stare	Bază factuală solidă	Fără provider-scan	Cu provider-scan / URL / device intel	Observație de modelare
FAN locker / colet + link + cerere date bancare	activ	FAN avertizează explicit asupra linkurilor false cu cerere de date bancare	high_risk	confirmed_phishing dacă URL-ul e în afara allowlist-ului ori are comportament de colectare credențiale	regulă puternică first-party 
Sameday reprogramare / taxă / schimbare adresă	activ	Sameday publică domenii oficiale și spune că nu cere date de card/cont pentru aceste operațiuni	high_risk	confirmed_phishing dacă domeniul nu e în lista oficială sau pagina cere date interzise	unul dintre cele mai bune scenarii pentru semnături deterministe 
Poșta Română taxă de livrare + link	recurent, dar nereconfirmat direct pe site-ul Poștei în corpus	suport generic din phishing/smishing și din patternul courier scam; nu am extras avertisment Poșta first-party din corpus	suspect	high_risk / confirmed_phishing doar cu dovadă domeniu fals ori formular de card	plafon mai jos până la confirmare first-party 
ANAF rambursare taxe / SPV / actualizare date	recurent, dar nereconfirmat direct în comunicat ANAF din corpus	suport generic din phishing către instituții publice și allowlist-ul ANAF	suspect	high_risk dacă domeniul nu e anaf.ro / static.anaf.ro; confirmed dacă exfiltrarea e demonstrată	nu forța verdictul maxim fără dovadă first-party curentă 
BNR / Poliție / bancă / „cont sigur”	activ	IGPR 2025 descrie exact schema, inclusiv apel bancă + redirecționare către falsă autoritate și transfer în „cont sigur”	high_risk	confirmed_phishing când există număr spoofed + cont beneficiar suspect + script coerent cu scenariul	scenariu obligatoriu în v1 
„Ai cerut un credit” / „credit pe numele tău”	activ	aceeași sursă IGPR: atacatorii pretind că victima a solicitat un împrumut și cer date sensibile	high_risk	confirmed_phishing dacă apelul e spoofed și derivă în „cont sigur” sau KYC fals	variație a aceluiași playbook de impostură 
WhatsApp „Votează pe Adeline/Cătălina/Daniela”	activ	IGPR 2025 detaliază exact textul, linkul malițios, asocierea contului și preluarea listei de contacte	high_risk	confirmed_phishing dacă URL-ul/landingul cere codul de asociere sau produce takeover	extrem de bine documentat oficial 
WhatsApp „semnează petiția” / „vezi sondajul”	variantă activă, dar textul exact nu e reconfirmat în corpus	același mecanism de link malițios + preluare cont, dar copy-ul exact nu e confirmat first-party în corpus	suspect	high_risk / confirmed dacă infrastructura se potrivește takeover-ului WhatsApp	variantă de aceeași familie, nu caz separat „confirmat” 
„Mamă/tată/copil, am alt număr / telefon stricat”	recurent, copy exact nereconfirmat în corpus	se suprapune comportamental peste frauda de mesagerie + cerere urgentă de bani din contact compromis	suspect	high_risk dacă mesajul vine din cont compromis și cere transfer imediat	nu urca la confirmed doar din template-ul emoțional 
„Accidentul” / „nepotul”	istoric/recidivant, nereconfirmat național în corpus 2025–2026 accesat	seamănă cu fraudele telefonice bazate pe presiune și transfer urgent; nu am reconfirmare first-party dedicată în corpus	needs_more_evidence / suspect	high_risk dacă există probe telefonice suplimentare sau script de autoritate falsă	bun de păstrat în bibliotecă, dar cu plafon mic
Marketplace: „ca să primești banii introdu cardul”	recurent și foarte bine documentat	SigurantaOnline descrie exact mutarea conversației pe WhatsApp și linkul fals pentru „încasare”	high_risk	confirmed_phishing dacă landingul cere număr card/CVV/3DS	scenariu critic pentru OLX-like și C2C marketplaces 
Marketplace: vânzător fals + produs fictiv + link phishing	recurent și foarte bine documentat	aceeași sursă oficială descrie și partea de fals vânzător	high_risk	confirmed_phishing cu dovadă URL / formular / merchant mismatch	tot familie marketplace fraud 
„Investiții Hidroelectrica / profit garantat”	recurent, dar fără avertisment Hidroelectrica first-party extras în corpus	IGPR spune că entitățile autorizate nu garantează profituri și cumpărarea de acțiuni nu se face prin pagini care cer plăți/date personale	suspect	high_risk / confirmed dacă landingul cere plată directă sau impersonare de acțiuni/IPO	bun scenariu de impostură brand + investiții 
Broker crypto + AnyDesk / TeamViewer / remote app	activ ca familie de risc	ING spune explicit să nu instalezi aplicații și să nu accesezi site-uri la indicația apelanților; IGPR detaliază fraudele de investiții	high_risk	confirmed când există instrucțiuni de remote-control, wallet exfil sau fake brokerage	scenariu major de vishing financiar 
APK bancar fals / voicemail app falsă / FluBot	activ	YOXO/Orange documentează exact malware-ul distribuit prin SMS și „aplicație” falsă; ING avertizează împotriva logării prin link și instalării de aplicații la indicația apelanților	high_risk	confirmed_phishing / confirmed_malware dacă APK-ul e neoficial sau sandbox-ul vede payload	alt scenariu obligatoriu în v1 
„Ai câștigat premiu / loterie / bonus”	recurent	Orange/YOXO spun că multe fraude folosesc tombole, concursuri sau premii false pentru a cere autentificare ori coduri	suspect	high_risk dacă există cerere de cod, card sau logare în pagină clonă	nu trebuie confundat cu promoțiile reale găzduite pe domeniul oficial 
Job/task scam	neconfirmat direct în corpus	nu am extras sursă first-party dedicată; îl recomand doar ca placeholder de risc	needs_more_evidence	suspect / high_risk dacă cere plată inițială ori wallet/crypto	păstrează în backlog-ul de cercetare, nu în verdict puternic
Facturi utilități false / schimbare IBAN	recurent	SigurantaOnline descrie exact „frauda cu facturi”; PPC și E.ON au portaluri oficiale de facturi/plăți, ceea ce ajută verificarea claims	suspect	high_risk / confirmed dacă mesajul mută plata în alt cont sau în afara canalului oficial	scenariu critic B2C și B2B 

CLAIM_VERIFIER_TARGETS
Aici este designul recomandat pentru claim verifier. Ideea nu e să „ghicească”, ci să rezolve trei întrebări în ordinea corectă: cine pretinde că este, unde te trimite, ce acțiune îți cere. Dacă al treilea răspuns intră în conflict cu o regulă official „never asks”, verdictul poate urca dur. Dacă primul și al doilea sunt încă neclare, verdictul trebuie plafonat. 

Nu

Da

Nu

Da

Da

Nu

Claim observat

Domeniu / app / canal în allowlist?

Suspect sau High_Risk

Claim-ul există exact în sursa oficială?

Needs_More_Evidence

Cere date interzise, coduri, card, PIN, CVV, login prin link, transfer în cont sigur?

High_Risk sau Confirmed

Probabil legit / Allow



Afișează codul
Țintă de verificare	Ce verifică motorul	Semnale pozitive	Semnale negative	Exemplu legitim verificat / model de legitim	Exemplu fake / verdict recomandat
YOXO buyback	dacă există programul și unde este ancorat	linkul Buy Back este publicat pe yoxo.ro și duce către tradein.recommerce.com	orice alt „buyback” trimis prin domeniu diferit, WhatsApp sau formular nou	yoxo.ro → Buy Back → tradein.recommerce.com este ancoră legitimă	yoxo-buy-back-ro.com sau tradein-yoxo-help.net = high_risk 
service status iDroid	existența publică a serviciului și a canalului oficial	neconfirmat în corpus; v1 trebuie să folosească doar linkuri ancorate din site-ul operatorului	orice inbound care pretinde status service și cere date/card fără ancoră oficială	unverified_public_target până la reconfirmare	verdict maxim fără allowlist: needs_more_evidence / suspect
campanii eMAG/Altex	dacă promoția există pe domeniul oficial și are regulament/T&C	necesită pagină oficială + regulament + acțiune comercială plauzibilă	premii/bonusuri care cer cod, card sau logare în pagină clonă	promoție găzduită pe domeniul principal cu T&C oficial	aceeași promoție pe oglindă sau în DM = high_risk
tracking curier	AWB, locker redirect, status colet	allowlist-ul courier + fără cereri interzise	domeniu neoficial, taxă de redelivery nealiniată cu regula companiei, cereri de card	fancourier.ro, posta-romana.ro, awb.posta-romana.ro, mycargus.cargus.ro, domeniile listate de Sameday	sameday-pay.help, fan-track-pay.ro, posta-taxe.app = high_risk / confirmed cu scan 
notificări ANAF / SPV	validarea sursei și a naturii acțiunii	domeniu oficial anaf.ro / static.anaf.ro; acces direct, nu prin link din SMS	SMS/e-mail care anunță rambursări și împinge spre completarea de date	acces direct la serviciile ANAF / SPV din navigația oficială	mesaje „ANAF-rambursare” cu domenii sau formulare externe = high_risk 
facturi utilități	existența facturii și a canalului de plată	portaluri oficiale client.hidroelectrica.ro, myppc.ppcenergy.ro, E.ON Myline / eon.ro	schimbări de IBAN, plăți mutate spre conturi noi, linkuri din afara portalurilor	portal client sau pagină oficială de factură/plată	„Factura atașată, plătește aici” pe domeniu exterior = high_risk 
oferte telecom	existența ofertei în site/aplicație oficială	pagină pe orange.ro, yoxo.ro, digi.ro, portal/aplicație oficială	solicitări de coduri, PIN, card, SIM swap pentru premii/reduceri	ofertă din My Orange, YOXO, DIGI sau magazinele oficiale	„reducere 90% dacă tastezi codul X” = high_risk 
campanii bancare educaționale	dacă pagina e educațională, nu tranzacțională	BCR are „Naționala de Edufin”, BT are Întreb BT, ARB publică campanii educate-siguranță, ING are secțiune de securitate	pagină care se pretinde educațională, dar cere autentificare, card sau instalare	educațional = conținut, FAQ, recomandări, fără cereri de autentificare sensibile	„ghid anti-fraudă” care cere login/card = high_risk 

Regulă-cheie de design. Pentru claim verifier, există pe domeniul oficial nu e suficient. Trebuie verificat și ce ți se cere. Tocmai asta spun sursele puternice: chiar dacă un mesaj evocă brandul real, devine periculos când cere link-login, coduri, date de card, PIN/CVV, transfer în „cont sigur” sau instalarea unei aplicații. 

FALSE_POSITIVE_GUARDS
Un motor bun pe phishing fără garduri de fals pozitiv devine o sirenă de fabrică. Aici sunt gardurile minime pe care le recomand pentru SigurScan v1.

Caz care poate părea suspect la suprafață	Ce îl poate face legitim	Ce îl face totuși suspect	Regulă recomandată
mesaj real de curier cu AWB și status	vine de pe domeniu/subdomeniu allowlisted și nu cere date bancare interzise	cere plata livrării sau cardul în afara regulilor declarate oficial	nu marca „fraudă” doar pentru că există link; verifică întâi allowlist-ul de domenii oficiale 
pagină Orange / YOXO despre „prevenire fraudă”	chiar există oficial și vorbește despre phishing, coduri și social media impersonation	mesajul te scoate din aceste pagini și cere acțiuni interzise	nu penaliza keyword-uri ca „fraudă”, „phishing”, „WhatsApp”, „premiu”; contextul contează 
pagină ING / BCR / BT de educație	existe secțiuni legitime de securitate sau educație financiară	dacă aceeași pagină pretinde autentificare prin link ori cere date sensibile	educaționalul trebuie clasificat separat de tranzacțional 
banking page cu parametri de tracking	bănci și telecom folosesc uneori resurse sau deeplinkuri oficiale auxiliare	parametri agresivi ≠ phishing prin definiție	nu penaliza automat query params; penalizează cererea interzisă sau domeniul neancorat
shortener / deeplink	YOXO folosește yoxo.page.link; Orange folosește qr.orange.ro; Raiffeisen folosește app.eu.adjust.com; Sameday folosește și sdy.ro	alt shortener cu nume similar, dar neancorat first-party	„shortener” nu e suficient pentru blocare; trebuie să fie sau nu în allowlist-ul explicit
subdomenii multiple ale aceluiași brand	companiile mari chiar folosesc multe subdomenii	lookalike-ul iese din familia oficială sau schimbă TLD-ul	menține allowlist semnătural, nu regulă vagă de string match
mesaj care menționează „cont sigur” în scop educațional	ING, Poliția Română și alții explică tocmai de ce e o fraudă	mesajul real îți cere transferul efectiv	detectează diferența dintre pagini educaționale și solicitări operaționale 
mesaj cu „vot”, „bursă”, „copil”	există campanii legitime și concursuri reale	takeover flow, cerere de cod PIN de asociere, cerere de bani după takeover	nu bloca doar pe vocabular emoțional; blochează pe lanțul de acțiuni periculoase 
marketplace link legitim	unele platforme au fluxuri reale de suport și centre de ajutor	„ca să primești banii introdu cardul” este explicit fraudulos în corpus	regula trebuie să privilegieze „instrument de plată, nu de încasare” și să detecteze mutarea conversației off-platform 
pagină oficială de factură/plată	PPC, E.ON, DIGI, Ghișeul.ro au plăți oficiale online	linkul sau contul de plată iese în afara canalului oficial	securizează verify-by-portal, nu verify-by-message 

Heuristica supremă anti-fals-pozitiv. Dacă un URL sau un mesaj poate fi explicat mai bine printr-un flux oficial cunoscut decât prin fraudă, verdictul trebuie plafonat la needs_more_evidence până când apare unul dintre indicatorii tari: domeniu neancorat, cerere interzisă, redirecționare către login fals, transfer în „cont sigur”, APK neoficial, card ca „încasare”. Această ierarhie este aliniată cu toate sursele puternice din corpus. 

ACCEPTANCE_TESTS
Setul de mai jos conține 84 de teste concrete. Ele sunt concepute pentru regression, scoring și thresholding. În mod intenționat, includ atât cazuri care trebuie blocate, cât și cazuri care trebuie lăsate în pace. Asta separă un detector bun de unul isteric. Toate testele derivă din regulile și scenariile susținute mai sus. 

text
Copiază
T01 | SMS FAN cu link pe domeniu neallowlisted + cere card pentru redelivery | high_risk
T02 | SMS FAN cu link pe fancourier.ro/tracking și fără cerere de card | allow
T03 | URL pretinde FAN, sandbox arată formular card/CVV | confirmed_phishing
T04 | SMS Sameday cu domeniu din lista oficială și doar redirect locker | allow
T05 | SMS Sameday cu domeniu în afara listei + cere plata transportului | high_risk
T06 | Mesaj Sameday de pe sdy.ro fără cereri sensibile | allow
T07 | Mesaj Sameday de pe sdy-help.ro | high_risk
T08 | Poșta Română: email cu akt „Track & Trace” de pe posta-romana.ro | allow
T09 | Poșta Română: SMS cu taxa 2,99 lei pe domeniu străin | suspect
T10 | Poșta Română: URL scanat și landing cu formular card | confirmed_phishing
T11 | Cargus: link pe mycargus.cargus.ro pentru login cont existent | allow
T12 | Cargus: „plătește taxa de livrare” pe cargus-pay.help | high_risk

T13 | Ghișeul.ro: email „ai obligație fiscală, plătește acum” | high_risk
T14 | Ghișeul.ro: navigare directă la ghiseul.ro și autentificare ROeID | allow
T15 | Ghișeul.ro: mesaj fără link, doar recomandă să intri manual pe portal | allow
T16 | ANAF: email de pe domeniu extern care promite rambursare | suspect
T17 | ANAF: alertă internă cu link direct către anaf.ro din comunicare corporate cunoscută | needs_more_evidence
T18 | ANAF: landing pe domeniu clonă + cere CNP și card | confirmed_phishing
T19 | BNR/Poliție: apel „cont sigur” fără URL | high_risk
T20 | Apel „ai făcut credit” + redirecționare la falsă poliție | high_risk
T21 | Apel „ai făcut credit” dar fără cerere de bani/date, doar recomandă să suni banca pe numărul cardului | needs_more_evidence
T22 | SMS „validează creditul tău” pe domeniu bancă-falsă | high_risk
T23 | Email „actualizare date fiscale” de pe static.anaf.ro anchoring page oficială | allow
T24 | Email „actualizare date fiscale” de pe anaf-secure.help | high_risk

T25 | WhatsApp „votează pe Adeline” + link necunoscut | high_risk
T26 | „Votează pe Adeline” + landing cere cod asociere / PIN | confirmed_phishing
T27 | Mesaj prieten WhatsApp fără link, doar text vag | needs_more_evidence
T28 | Mesaj „semnează petiția” + link necunoscut + cerere cod | high_risk
T29 | Mesaj „telefonul meu s-a stricat, transferă urgent” din număr nou | suspect
T30 | Mesaj „telefonul meu s-a stricat” din cont compromis confirmat | high_risk
T31 | Mesaj „mama/tata, acesta este noul meu număr” fără cerere bani | needs_more_evidence
T32 | Mesaj „copilul tău are nevoie urgent de bani” + IBAN necunoscut | high_risk
T33 | Mesaj concurs prietenesc real pe domeniu oficial al organizatorului și fără cod/login | allow
T34 | Mesaj concurs cu domeniu clonă și premiu exagerat | suspect
T35 | Link de vot pe domeniu oficial cunoscut al organizatorului, fără login extern | needs_more_evidence
T36 | Takeover WhatsApp confirmat + mesaje către contacte pentru împrumut | confirmed_phishing

T37 | OLX-like: „ca să primești banii introdu cardul” | high_risk
T38 | Marketplace: conversația se mută pe WhatsApp + link de încasare | high_risk
T39 | Marketplace: vânzător cere avans pe card prin landing extern | high_risk
T40 | Marketplace: landing cere număr card + CVV + 3DS | confirmed_phishing
T41 | Marketplace: link către centru oficial de ajutor al platformei | allow
T42 | Marketplace: cumpărător cere doar IBAN și nume titular, fără link și fără card | needs_more_evidence
T43 | Marketplace: ofertă prea bună + pagină clonă de checkout | high_risk
T44 | Marketplace: seller profile vechi, plată escrow în platformă oficială | allow
T45 | Marketplace: cere „parolă statică și dinamică 3D Secure” | confirmed_phishing
T46 | Marketplace: link scurt neancorat first-party trimis după mutarea pe WhatsApp | high_risk
T47 | Marketplace: pretinde că „cardul este pentru încasare” | high_risk
T48 | Marketplace: cere doar ridicare personală, fără plăți online | allow

T49 | Orange: mesaj cu reward/cadou și cere cod PIN sau număr card | high_risk
T50 | Orange: accesare pagină de prevenire fraudă de pe orange.ro | allow
T51 | Orange: DM de pe cont social neoficial cu numele brandului + link | high_risk
T52 | Orange: solicitare de tastare coduri speciale USSD pentru „remediere” | high_risk
T53 | YOXO: link oficial yoxo.page.link pentru aplicație | allow
T54 | YOXO: „Buy Back” pe tradein.recommerce.com, venit prin navigare din yoxo.ro | allow
T55 | YOXO: buyback pe tradein-yoxo.app | high_risk
T56 | YOXO/Orange: SMS „new voicemail” + APK extern | confirmed_phishing
T57 | DIGI: plata facturii prin canal oficial al portalului | allow
T58 | DIGI: email „ai restanță” pe domeniu extern + card request | high_risk
T59 | DIGI: mesaj comercial fără link, invită la apel pe număr oficial din site | needs_more_evidence
T60 | Orange/YOXO: concurs real pe domeniu oficial, fără cereri sensibile | allow

T61 | ING: email/link care cere login Home’Bank prin URL primit | high_risk
T62 | ING: pagină de securitate oficială explică fraudele și dă numere oficiale de contact | allow
T63 | ING: apel care cere transfer în „cont seif” | high_risk
T64 | ING: mesaj care cere PIN/CVV | confirmed_phishing
T65 | BCR: pagină „Naționala de Edufin” pe bcr.ro | allow
T66 | BT: pagină „Întreb BT” pe bancatransilvania.ro | allow
T67 | BT: widget care spune clar că AI poate greși și nu cere date sensibile | allow
T68 | Raiffeisen: deeplink app.eu.adjust.com ancorat în site oficial | allow
T69 | „Banca” generică: SMS cu formular card și adresare impersonală | high_risk
T70 | „Banca” generică: notificare push în aplicația oficială, fără link extern | allow
T71 | BNR/Poliție: apel cu credit fals + cerere de validare date personale sensibile | high_risk
T72 | „reprezentant bancă” cere instalare AnyDesk/TeamViewer | confirmed_phishing

T73 | PPC: copiere factură din portalul oficial | allow
T74 | PPC: email „schimbare IBAN” fără ancoră în portal oficial | high_risk
T75 | E.ON: acces în Myline / status solicitări din portal oficial | allow
T76 | E.ON: PDF factură trimis din domeniu străin cu IBAN nou | suspect
T77 | Hidroelectrica: ofertă investiții cu profit garantat și plată directă în pagină | high_risk
T78 | Hidroelectrica: acces portal client de pe client.hidroelectrica.ro | allow
T79 | Utilități: mesaj spune să intri manual în portal, fără link | needs_more_evidence
T80 | Utilități: landing cere card pentru „actualizare contract” pe domeniu clonă | confirmed_phishing
T81 | Factură utilități: atașament .zip / .apk | confirmed_phishing
T82 | Factură utilități: email de la domeniu oficial, dar cu link către alt TLD | high_risk
T83 | Factură utilități: mesaj în stil educațional, fără cereri operaționale | allow
T84 | Factură utilități: schimbare titular prin formular oficial din site | allow
GOV_RO_AND_SOCIAL_PLATFORM_NOTES
Pentru zona gov.ro și platforme sociale, recomand o regulă de produs separată, fiindcă aici apar două tipuri distincte de fals pozitiv: pe de o parte, mesajele oficiale reale care îți spun să intri pe portal ca să verifici ceva; pe de altă parte, mesajele false care folosesc exact aceeași emoție, dar te împing către un link sau o acțiune interzisă. Ghișeul.ro este cel mai clar exemplu: spune explicit că nu anunță prin SMS/e-mail apariția unei obligații de plată. ANAF oferă servicii oficiale și notificări prin canale proprii, dar în corpusul parcurs nu am extras un comunicat first-party recent dedicat exact scenariului „rambursare taxe”. Asta înseamnă că regula bună de produs este: trust the portal, distrust the inbound. 

Pentru rețelele sociale și aplicațiile de mesagerie, semnalul-cheie nu este doar brandul, ci lanțul comportamental. Poliția Română arată clar, în scenariul WhatsApp de tip „votează pe Adeline”, că atacul pornește dintr-un contact aparent legitim, introduce un link, apoi capturează codul necesar asocierii contului pe alt dispozitiv și continuă cu cereri de bani către contacte. Orange și YOXO completează perfect tabloul prin faptul că avertizează explicit despre conturi false social media, WhatsApp, concursuri false și cereri de coduri/date. Rezultatul practic pentru SigurScan este acesta: un mesaj venit „de la o persoană cunoscută” nu poate fi considerat benign dacă include unul dintre trigger-ele interzise. 

Pentru zona bancară și guvernamentală, Poliția Română a mai adăugat în 2025 un detaliu extrem de util pentru modelare: falsificarea identității apelantului și combinarea instituțiilor de încredere într-un singur scenariu – bancă, apoi poliție, apoi „cont sigur”. Asta justifică o regulă cross-domain importantă: dacă aceeași conversație combină autoritate, presiune temporală și transfer ireversibil, scorul trebuie să sară semnificativ chiar înainte de analiza tehnică a URL-ului. 

GAP_ANALYSIS
Diagnostic final. SigurScan are deja, pe baza corpusului oficial curent verificat, material suficient pentru un MVP foarte bun în România, dar nu pentru un „oracle absolut”. Partea foarte solidă este aceasta: curieri, telecom, Ghișeul.ro, spoofing bancă+poliție, WhatsApp takeover, phishing/smishing generic, frauda marketplace și factura falsă. Partea încă incompletă pentru un knowledge layer „full confidence” este aceasta: ANAF first-party anti-phishing extras recent, iDroid service-status public, eMAG/Altex registry de campanii curente, plus revalidarea națională a câtorva copy-variants populare, dar insuficient probate în corpusul oficial accesat. 

Top acțiuni imediate.

construiește official_registry cu allowlist strict de domenii/subdomenii/parteneri doar din surse ancorate first-party;
implementează never_asks_rules pentru FAN, Sameday, Ghișeul.ro, Orange, YOXO, ING;
implementează scenario packs obligatorii: safe_account, whatsapp_vote_takeover, marketplace_receive_money_card, fake_voicemail_apk, fake_invoice;
separă clar verdictul high_risk de confirmed_phishing;
adaugă plafon de verdict pentru scenariile nereconfirmate direct first-party;
tratează paginile educaționale drept clasă proprie education_or_warning_page;
introdu o listă de „trusted auxiliary domains” (sdy.ro, yoxo.page.link, tradein.recommerce.com, app.eu.adjust.com, qr.orange.ro) pe bază de ancorare first-party;
fă regression pack cu testele T01–T84;
loghează explicațiile de verdict în stil auditabil: who, where, what requested;
planifică un update cycle săptămânal pentru brand rules și scenarii.
2026-06-07
2026-06-14
2026-06-21
2026-06-28
2026-07-05
2026-07-12
Registru oficial + allowlisturi
Reguli never-asks first-party
Bibliotecă scenarii și plafon verdict
Claim verifier + explainability
False-positive guards
Regression pack T01-T84
Telemetrie + review tooling
Proces de refresh săptămânal
Fundație
Detecție
Calitate
Operaționalizare
Roadmap minim recomandat pentru SigurScan


Afișează codul
Întrebări deschise / limite.
Înainte de a declara produsul „gata pentru generalizare”, aș completa explicit patru lipsuri: un extractor dedicat pentru comunicate ANAF recente despre phishing, un reconfirmator public pentru iDroid, un mini-registry de campanii comerciale oficiale pentru eMAG și Altex, și un corpus actualizat pentru variantele „telefon stricat”, „petiție WhatsApp” și „accident/nepot”, astfel încât ele să nu rămână doar copii ale unor familii de scam deja cunoscute. Fără această completare, ele trebuie păstrate în zona suspect/needs_more_evidence, nu în zona confirmed.

JSON-ul de mai jos comprimă exact obiectele susținute mai sus și nu introduce decizii noi.

json
Copiază
{
  "official_registry_updates": [
    {"entity":"ANAF","domains":["anaf.ro","static.anaf.ro","chat.anaf.ro"],"apps_or_channels":["SPV","servicii online"],"status":"verified_official"},
    {"entity":"Ghiseul.ro","domains":["ghiseul.ro"],"apps_or_channels":["ROeID","eIDAS","plata amenzi","rovinieta"],"status":"verified_official"},
    {"entity":"BNR","domains":["bnr.ro","muzeu.bnr.ro"],"apps_or_channels":["media/publicatii","educatie financiara"],"status":"verified_official"},
    {"entity":"FAN Courier","domains":["fancourier.ro","retur.fancourier.ro","selfawb.ro"],"apps_or_channels":["tracking","selfAWB","retur"],"status":"verified_official"},
    {"entity":"Posta Romana","domains":["posta-romana.ro","awb.posta-romana.ro"],"apps_or_channels":["Track & Trace","My AWB"],"status":"verified_official"},
    {"entity":"Sameday","domains":["sameday.ro","eawb.sameday.ro","locker.sameday.ro","pick-updrop-off.sameday.ro","sameday.easybox.ro","locker-redirect.sameday.ro","awb.sameday.ro","sdy.ro"],"apps_or_channels":["AWB","easybox","locker redirect"],"status":"verified_official"},
    {"entity":"Cargus","domains":["cargus.ro","mycargus.cargus.ro","app.urgentcargus.ro"],"apps_or_channels":["MyCargus","WebExpress"],"status":"verified_official"},
    {"entity":"Orange","domains":["orange.ro","comunitate.orange.ro","newsroom.orange.ro","qr.orange.ro","sso.orange.ro"],"apps_or_channels":["My Orange","prevenire frauda"],"status":"verified_official"},
    {"entity":"YOXO","domains":["yoxo.ro","www.yoxo.blog","reconditionate.yoxo.ro"],"partner_domains":["yoxo.page.link","tradein.recommerce.com"],"apps_or_channels":["YOXO app","Buy Back","prevenire frauda"],"status":"verified_official"},
    {"entity":"DIGI","domains":["digi.ro","s.digi.ro","rdslink.rcs-rds.ro"],"apps_or_channels":["plata factura","asistenta"],"status":"verified_official"},
    {"entity":"Hidroelectrica","domains":["hidroelectrica.ro","cdn.hidroelectrica.ro","client.hidroelectrica.ro"],"apps_or_channels":["portal client","relatia cu investitorii"],"status":"verified_official"},
    {"entity":"PPC","domains":["ppcenergy.ro","myppc.ppcenergy.ro"],"apps_or_channels":["myPPC","copie factura","transmitere index"],"status":"verified_official"},
    {"entity":"E.ON","domains":["eon.ro"],"apps_or_channels":["E.ON Myline","status solicitari","facturi"],"status":"verified_official"},
    {"entity":"ING","domains":["ing.ro","homebank.ro"],"apps_or_channels":["Home'Bank","securitate"],"status":"verified_official"}
  ],
  "brand_warnings": [
    {"brand":"FAN Courier","rule":"nu accesa linkuri false care solicita date bancare","confidence":"high"},
    {"brand":"Sameday","rule":"nu solicita date personale sensibile / card / cont pentru transport, adresa, reprogramare; foloseste doar domeniile din lista oficiala","confidence":"high"},
    {"brand":"Ghiseul.ro","rule":"nu anunta prin SMS sau e-mail aparitia unei obligatii de plata","confidence":"high"},
    {"brand":"Orange","rule":"nu solicita conturi bancare, parole, PIN-uri, coduri de reincarcare prin email/SMS/apel","confidence":"high"},
    {"brand":"YOXO","rule":"nu solicita conturi bancare, parole, PIN-uri, coduri de reincarcare; avertizeaza si despre FluBot","confidence":"high"},
    {"brand":"ING","rule":"nu cere accesare linkuri, login Home'Bank prin link, PIN sau CVV; nu transfera in cont sigur","confidence":"high"},
    {"brand":"Banci - regula transversala","rule":"bancile nu cer datele cardului, parole, PIN prin telefon/SMS/email/site clonat","confidence":"medium"},
    {"brand":"Politia Romana","rule":"nu transfera bani in conturi sigure; verifica prin canale oficiale","confidence":"high"}
  ],
  "scam_scenarios_2025_2026": [
    {"name":"fan_link_card","status":"active","no_scan":"high_risk","with_scan":"confirmed_phishing"},
    {"name":"sameday_redirect_taxa","status":"active","no_scan":"high_risk","with_scan":"confirmed_phishing"},
    {"name":"posta_taxa_livrare","status":"recurring_unverified_first_party","no_scan":"suspect","with_scan":"high_risk_or_confirmed"},
    {"name":"anaf_refund_spv","status":"recurring_unverified_first_party","no_scan":"suspect","with_scan":"high_risk_or_confirmed"},
    {"name":"safe_account_bnr_police_bank","status":"active","no_scan":"high_risk","with_scan":"confirmed_phishing"},
    {"name":"fake_credit_on_your_name","status":"active","no_scan":"high_risk","with_scan":"confirmed_phishing"},
    {"name":"whatsapp_vote_adeline","status":"active","no_scan":"high_risk","with_scan":"confirmed_phishing"},
    {"name":"whatsapp_petition_variant","status":"active_variant","no_scan":"suspect","with_scan":"high_risk_or_confirmed"},
    {"name":"broken_phone_new_number","status":"recurring_variant","no_scan":"suspect","with_scan":"high_risk"},
    {"name":"accident_nepot","status":"historic_or_unverified_current","no_scan":"needs_more_evidence","with_scan":"high_risk"},
    {"name":"marketplace_receive_money_card","status":"recurring","no_scan":"high_risk","with_scan":"confirmed_phishing"},
    {"name":"fake_seller_phishing_checkout","status":"recurring","no_scan":"high_risk","with_scan":"confirmed_phishing"},
    {"name":"fake_hidroelectrica_investment","status":"recurring_brand_imposture","no_scan":"suspect","with_scan":"high_risk_or_confirmed"},
    {"name":"crypto_remote_access","status":"active_family","no_scan":"high_risk","with_scan":"confirmed_phishing"},
    {"name":"fake_banking_apk_voicemail","status":"active","no_scan":"high_risk","with_scan":"confirmed_malware"},
    {"name":"fake_utility_invoice_ibAN_change","status":"recurring","no_scan":"suspect","with_scan":"high_risk_or_confirmed"}
  ],
  "claim_verifier_targets": [
    {"target":"yoxo_buyback","official_anchor":["yoxo.ro","tradein.recommerce.com"],"mode":"verify_exact_anchor"},
    {"target":"idroid_service_status","official_anchor":[],"mode":"unverified_public_target"},
    {"target":"emag_altex_campaigns","official_anchor":["official_campaign_page_required"],"mode":"needs_current_campaign_registry"},
    {"target":"courier_tracking","official_anchor":["fancourier.ro","posta-romana.ro","awb.posta-romana.ro","mycargus.cargus.ro","sameday_allowlist"],"mode":"allowlist_plus_forbidden_action_check"},
    {"target":"anaf_spv_notifications","official_anchor":["anaf.ro","static.anaf.ro"],"mode":"portal_over_inbound_message"},
    {"target":"utility_invoices","official_anchor":["client.hidroelectrica.ro","myppc.ppcenergy.ro","eon.ro"],"mode":"portal_and_billing_channel_check"},
    {"target":"telecom_offers","official_anchor":["orange.ro","yoxo.ro","digi.ro"],"mode":"official_offer_plus_no_forbidden_request"},
    {"target":"bank_education_campaigns","official_anchor":["bcr.ro","bancatransilvania.ro","ing.ro","arb.ro"],"mode":"education_page_class"}
  ],
  "false_positive_guards": [
    {"guard":"allowlisted_courier_link_without_card_request","effect":"downgrade"},
    {"guard":"official_orange_yoxo_fraud_prevention_page","effect":"allow"},
    {"guard":"official_ing_bcr_bt_education_or_security_page","effect":"allow"},
    {"guard":"official_partner_shortener_or_deeplink_anchored_first_party","effect":"downgrade"},
    {"guard":"official_subdomain_family_verified_first_party","effect":"downgrade"},
    {"guard":"education_about_safe_account_not_equal_real_safe_account_request","effect":"downgrade"},
    {"guard":"emotional_vocabulary_without_forbidden_action","effect":"needs_more_evidence"},
    {"guard":"manual_portal_navigation_recommended_without_link","effect":"allow_or_needs_more_evidence"}
  ],
  "acceptance_tests": [
    "T01 FAN fake card link -> high_risk",
    "T03 FAN fake landing with card form -> confirmed_phishing",
    "T05 Sameday domain outside allowlist + tax -> high_risk",
    "T08 Posta official Track&Trace -> allow",
    "T13 Ghiseul obligation by SMS/email -> high_risk",
    "T19 safe_account call -> high_risk",
    "T25 WhatsApp vote link -> high_risk",
    "T29 broken_phone new number -> suspect",
    "T37 marketplace receive money by card -> high_risk",
    "T45 marketplace asks card+CVV+3DS -> confirmed_phishing",
    "T49 Orange reward asks PIN/card -> high_risk",
    "T54 YOXO Buy Back via official anchor -> allow",
    "T56 fake voicemail APK -> confirmed_phishing",
    "T61 ING login through received link -> high_risk",
    "T63 ING account_safe transfer -> high_risk",
    "T68 Raiffeisen app.eu.adjust.com deep link -> allow",
    "T74 PPC IBAN change email outside portal -> high_risk",
    "T77 fake Hidroelectrica investment guaranteed profit -> high_risk",
    "T81 utility invoice zip/apk -> confirmed_phishing",
    "T84 official ownership change form -> allow"
  ],
  "priority_worklist_now": [
    "build_official_registry_allowlists",
    "encode_first_party_never_asks_rules",
    "ship_safe_account_and_whatsapp_takeover_detectors",
    "ship_marketplace_card_for_receiving_money_detector",
    "ship_fake_apk_fluBot_detector",
    "ship_fake_invoice_and_iban_change_detector",
    "separate_education_pages_from_transactional_claims",
    "add_partner_domain_allowlist_only_if_first_party_anchored",
    "implement_verdict_caps_without_provider_scan",
    "run_regression_pack_T01_T84_on_every_release"
  ]
}