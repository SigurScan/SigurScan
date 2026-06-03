package ro.sigurscan.app

data class OfflineRule(
    val id: String,
    val family: String,
    val claimedBrand: String,
    val baseScore: Int,
    val keywords: List<String>,
    val highSignals: List<String>,
    val urlSignals: List<String>,
    val suspiciousDomains: List<String>,
    val allowedDomains: List<String>,
    val reasons: List<String>,
    val keyDangers: List<String>,
    val safeActions: List<String>,
    val isGeneric: Boolean = false
)

object ScamRules {
    val TRUSTED_OFFICIAL_DOMAINS = mapOf(
        "fanCourier" to listOf("fancourier.ro", "fanbox.ro", "fan-courier.ro", "selfawb.ro"),
        "postaRomana" to listOf("posta-romana.ro"),
        "anaf" to listOf("anaf.ro", "mfinante.gov.ro", "mfinante.ro"),
        "cardAndBanks" to listOf(
            "revolut.com", "revolut.me", "revolut.space", "ing.ro", "ing.com",
            "ingbusiness.ro", "bcr.ro", "george.bcr.ro", "bancatransilvania.ro",
            "btpay.ro", "neo-bt.ro", "neo.bancatransilvania.ro"
        ),
        "remoteAccess" to listOf("anydesk.com", "teamviewer.com"),
        "whatsapp" to listOf("whatsapp.com", "web.whatsapp.com", "wa.me", "whatsapp.net"),
        "google" to listOf("google.com", "google.ro", "android.com", "developer.android.com", "youtube.com", "gmail.com"),
        "emag" to listOf("emag.ro", "emag.delivery"),
        "uber" to listOf("uber.com", "uber.link", "ubereats.com"),
        "marketplace" to listOf("olx.ro"),
        "dnsc" to listOf("dnsc.ro"),
        "utilities" to listOf("hidroelectrica.ro")
    )

    val OFFLINE_RULES = listOf(
        OfflineRule(
            id = "emag-fake",
            family = "eMAG fals / Premiu fals",
            claimedBrand = "eMAG",
            baseScore = 85,
            keywords = listOf("emag"),
            highSignals = listOf("voucher", "card cadou", "premiu", "gratuit", "iphone", "taxa", "activare", "castigat", "norocos", "urgent"),
            urlSignals = listOf("emag", "premii"),
            suspiciousDomains = listOf(".top", ".info", ".xyz", ".online"),
            allowedDomains = TRUSTED_OFFICIAL_DOMAINS["emag"]!!,
            reasons = listOf(
                "Mesajul folosește momeala unui premiu sau voucher gratuit de la eMAG.",
                "Se solicită plata unei taxe modice pentru revendicarea unui produs valoros (tactică de phishing)."
            ),
            keyDangers = listOf(
                "Furtul datelor de card sub pretextul plății transportului.",
                "Furtul identității prin formulare false."
            ),
            safeActions = listOf(
                "Nu accesați linkul.",
                "eMAG nu solicită niciodată taxe de transport prin SMS pentru premii.",
                "Verificați campaniile oficiale doar în aplicația eMAG."
            )
        ),
        OfflineRule(
            id = "fan-courier",
            family = "Curier fals / FAN Courier",
            claimedBrand = "FAN Courier",
            baseScore = 78,
            keywords = listOf("fancourier", "fan courier"),
            highSignals = listOf("colet", "locker", "awb", "ridica", "ridicare", "livrare", "link", "urgent", "pret", "taxa", "comanda", "actualizeaza", "actualizare", "tracking"),
            urlSignals = listOf("fancourier", "locker"),
            suspiciousDomains = listOf(".ru", ".top", ".click", ".biz", ".info"),
            allowedDomains = TRUSTED_OFFICIAL_DOMAINS["fanCourier"]!!,
            reasons = listOf(
                "Mesajul folosește context de colet, locker sau AWB, frecvent asociat cu escrocherii de livrări.",
                "Se cere acțiune rapidă pe un link aparent legat de curier."
            ),
            keyDangers = listOf(
                "Trimiterea datelor personale sau cardului pe pagini de clonă.",
                "Exfiltrarea codurilor OTP trimise prin SMS."
            ),
            safeActions = listOf(
                "Nu accesați linkul din mesaj.",
                "Verificați AWB doar pe fancourier.ro sau aplicația oficială.",
                "Cereți confirmare pe numărul oficial al curierului."
            )
        ),
        OfflineRule(
            id = "posta-romana",
            family = "Posta Română falsă",
            claimedBrand = "Poșta Română",
            baseScore = 72,
            keywords = listOf("posta", "poșta", "postaromana"),
            highSignals = listOf("colet", "taxa", "eliberare", "ridicare", "plata", "factură", "avizare", "sms", "comanda", "livrare"),
            urlSignals = listOf("posta", "colet", "dostava", "taxa"),
            suspiciousDomains = listOf(".top", ".info", ".xyz", ".pw", ".cf"),
            allowedDomains = TRUSTED_OFFICIAL_DOMAINS["postaRomana"]!!,
            reasons = listOf(
                "Există solicitare de plată suplimentară pe link extern pentru eliberare livrare.",
                "Mesajul imitativ folosește termeni Poșta Română fără context oficial verificabil."
            ),
            keyDangers = listOf(
                "Plata poate trimite victima pe portal fals.",
                "Datele introduse pot fi intercepționate."
            ),
            safeActions = listOf(
                "Nu plătiți taxe pe link-uri din SMS.",
                "Verificați statusul coletului doar în aplicația/portalul oficial.",
                "Nu transmiteți date personale prin mesaj."
            )
        ),
        OfflineRule(
            id = "anaf-spv",
            family = "ANAF / SPV fals",
            claimedBrand = "ANAF / SPV",
            baseScore = 80,
            keywords = listOf("anaf", "spv", "spatiul privat", "spatiul virtual"),
            highSignals = listOf("impozit", "datorie", "rambursare", "debitor", "aviz", "taxa", "sosire", "factura", "urgent", "blocat", "plateste", "plata", "nu o", "redeschide", "reactiveaza", "actualizeaza"),
            urlSignals = listOf("anaf", "mfinante", "spv", "taxa", "suspension"),
            suspiciousDomains = listOf(".ro", ".top", ".xyz", ".info", ".shop", ".online", ".biz"),
            allowedDomains = TRUSTED_OFFICIAL_DOMAINS["anaf"]!!,
            reasons = listOf(
                "Mesajul introduce termeni fiscali clari: ANAF/SPV, plata sau deblocare cont.",
                "Limbajul de urgență sugerează presiune de răspuns rapid."
            ),
            keyDangers = listOf(
                "Datele introduse pot ajunge la pagini clonă din sfera fiscală.",
                "Poate redirecționa către malware prin portal fals."
            ),
            safeActions = listOf(
                "Nu intrați pe linkuri din SMS.",
                "Verificați personal în SPV/anaf.ro după autentificare oficială.",
                "Cereți confirmare pe numărul oficial ANAF."
            )
        ),
        OfflineRule(
            id = "card-otp",
            family = "Furt date card / OTP",
            claimedBrand = "Nespecificat",
            baseScore = 88,
            keywords = listOf("card", "cvc", "cvv", "cvv2", "otp", "parola", "iban"),
            highSignals = listOf("cod", "pin", "plateste", "transfer", "plata", "nu", "nu o", "nu impart", "actualizeaza", "activa", "inregistreaza", "valideaza"),
            urlSignals = listOf("card", "plata", "banca", "revolut", "bt", "bcr", "ing", "otp", "3d"),
            suspiciousDomains = listOf(".ru", ".top", ".xyz", ".pw"),
            allowedDomains = TRUSTED_OFFICIAL_DOMAINS["cardAndBanks"]!!,
            reasons = listOf(
                "Textul solicită informații asociate de siguranță bancară sau card.",
                "Se observă indicii de presiune pentru acțiune rapidă."
            ),
            keyDangers = listOf(
                "Datele cardului sau codurile OTP pot fi capturate de falsiști.",
                "Risc de tranzacții neautorizate imediat după divulgare."
            ),
            safeActions = listOf(
                "Nu introduceți niciodată cardul sau OTP-ul pe site-uri trimise prin mesaj.",
                "Blocați imediat cardul și schimbați parolele dacă ați introdus date.",
                "Confirmați direct în aplicația băncii."
            )
        ),
        OfflineRule(
            id = "remote-access",
            family = "Remote access / remote support fraud",
            claimedBrand = "Remote Access",
            baseScore = 84,
            keywords = listOf("anydesk", "teamviewer", "quicksupport", "ultravnc", "any desk", "remote", "acces la telefon"),
            highSignals = listOf("aplicatie", "tehnic", "ecran", "instrucțiuni", "instaleaza", "acces", "partajeaza", "telefo", "comanda"),
            urlSignals = listOf("anydesk", "teamviewer", "remote", "apk"),
            suspiciousDomains = listOf(".ru", ".top", ".xyz", ".site", ".fun"),
            allowedDomains = TRUSTED_OFFICIAL_DOMAINS["remoteAccess"]!!,
            reasons = listOf(
                "Mesajul sugerează instalarea sau pornirea unui acces la distanță.",
                "Acest tip de solicitare este folosit frecvent pentru furt de control asupra telefonului."
            ),
            keyDangers = listOf("Pierdere control dispozitiv", "Instalare malware prin aplicații false", "Furt conturi"),
            safeActions = listOf(
                "Nu instalați aplicații de acces la distanță la cerere din chat.",
                "Deconectați Wi-Fi/DATA și schimbați parolele dacă ați instalat ceva.",
                "Contactați echipa oficială a aplicației pe canale cunoscute."
            )
        ),
        OfflineRule(
            id = "whatsapp-takeover",
            family = "Compromitere WhatsApp",
            claimedBrand = "WhatsApp",
            baseScore = 70,
            keywords = listOf("whatsapp"),
            highSignals = listOf("cod", "sms", "dispozitiv", "device", "two factor", "2fa", "sesizare", "numar", "apel", "cont", "deconectat", "verificare", "intrat", "suspendat", "compromis"),
            urlSignals = listOf("whatsapp", "whatsapp.com", "api.whatsapp.com", "wa.me"),
            suspiciousDomains = listOf(".ru", ".top", ".click"),
            allowedDomains = TRUSTED_OFFICIAL_DOMAINS["whatsapp"]!!,
            reasons = listOf(
                "Există indicatori de recuperare sau verificare de cont prin cod.",
                "Acest pattern apare la încercări de preluare de cont."
            ),
            keyDangers = listOf("Acces neautorizat la conversații", "Răspândire de mesaje de phishing"),
            safeActions = listOf(
                "Activați verificarea în doi pași.",
                "Revocați dispozitivele asociate din setări.",
                "Nu trimiteți niciodată coduri de verificare altcuiva."
            )
        )
    )
}
