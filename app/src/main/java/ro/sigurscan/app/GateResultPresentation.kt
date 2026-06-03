package ro.sigurscan.app

object GateResultPresentation {
    fun legacyRiskLevel(action: GateAction): String = when (action) {
        GateAction.DO_NOT_CONTINUE,
        GateAction.NO_ENTER_DATA,
        GateAction.NO_REPLY -> "dangerous"
        GateAction.VERIFY_OFFICIAL -> "medium"
        GateAction.CONTINUE_WITH_CAUTION -> "low"
        GateAction.INSUFFICIENT_EVIDENCE -> "error"
    }

    fun legacyRiskScore(action: GateAction): Int = when (action) {
        GateAction.DO_NOT_CONTINUE -> 95
        GateAction.NO_ENTER_DATA -> 88
        GateAction.NO_REPLY -> 82
        GateAction.VERIFY_OFFICIAL -> 55
        GateAction.CONTINUE_WITH_CAUTION -> 20
        GateAction.INSUFFICIENT_EVIDENCE -> 0
    }

    fun familyLabel(action: GateAction, fallback: String): String = when (action) {
        GateAction.DO_NOT_CONTINUE -> "Risc confirmat"
        GateAction.NO_ENTER_DATA -> "Cerere de date sensibile"
        GateAction.NO_REPLY -> "Scenariu social / raspuns riscant"
        GateAction.VERIFY_OFFICIAL -> "Verificare oficiala recomandata"
        GateAction.CONTINUE_WITH_CAUTION -> "Flux cu risc scazut"
        GateAction.INSUFFICIENT_EVIDENCE -> "Dovezi insuficiente"
    }.ifBlank { fallback }

    fun supportText(result: GateResult): String = when (result.action) {
        GateAction.DO_NOT_CONTINUE -> "Dovezile tehnice indica phishing, malware sau impersonare clara."
        GateAction.NO_ENTER_DATA -> "Pagina sau mesajul cere date sensibile pe un canal care nu este suficient validat."
        GateAction.NO_REPLY -> "Mesajul cere raspuns, coduri, bani sau continuarea conversatiei intr-un scenariu riscant."
        GateAction.VERIFY_OFFICIAL -> "Exista semnale care cer verificare manuala pe canalul oficial."
        GateAction.CONTINUE_WITH_CAUTION -> "Destinatia verificata pare oficiala sau delegata si nu am gasit cereri sensibile."
        GateAction.INSUFFICIENT_EVIDENCE -> "Nu avem destule date tehnice pentru o concluzie responsabila."
    }

    fun primaryAction(result: GateResult): String = when (result.action) {
        GateAction.DO_NOT_CONTINUE -> "Nu apasa linkul si nu continua fluxul."
        GateAction.NO_ENTER_DATA -> "Nu introduce card, parola, CNP, IBAN sau cod OTP."
        GateAction.NO_REPLY -> "Nu raspunde si nu trimite coduri sau bani."
        GateAction.VERIFY_OFFICIAL -> "Deschide manual aplicatia sau site-ul oficial."
        GateAction.CONTINUE_WITH_CAUTION -> "Continua doar daca recunosti contextul si nu ti se cer date sensibile."
        GateAction.INSUFFICIENT_EVIDENCE -> "Reincearca cu linkul complet sau verifica direct pe canalul oficial."
    }

    fun reasonText(result: GateResult, snapshot: EvidenceSnapshot?): String {
        val codes = result.reasonCodes.toSet()
        return when {
            "HIGH_CONFIDENCE_REPUTATION" in codes -> "Serviciul de reputatie a raportat phishing, malware sau social engineering."
            "SANDBOX_VERDICT" in codes -> "Sandbox-ul a gasit comportament de phishing sau malware pe destinatie."
            "SENSITIVE_FORM_ON_UNOFFICIAL_BRAND_DOMAIN" in codes -> "Pagina cere date sensibile pe un domeniu care nu apartine brandului mentionat."
            "BRAND_IMPERSONATION_UNOFFICIAL_SECRET_REQUEST" in codes -> "Mesajul pretinde un brand, dar linkul final cere secrete pe domeniu neoficial."
            "COURIER_UNOFFICIAL_SENSITIVE_REQUEST" in codes -> "Mesajul de curier cere plata sau date de card pe un domeniu neoficial."
            "DIRECT_REPLY_SECRET_REQUEST" in codes -> "Mesajul cere sa raspunzi cu un cod sau date sensibile."
            "TEXT_ONLY_SOCIAL_SCENARIO" in codes -> "Textul se potriveste unui scenariu social romanesc folosit pentru fraude."
            "MARKETPLACE_RECEIVE_MONEY_SENSITIVE_REQUEST" in codes -> "Fluxul de marketplace cere card sau OTP ca sa primesti bani."
            "SENSITIVE_FORM_UNOFFICIAL" in codes -> "Am gasit formular sensibil pe un domeniu nevalidat."
            "OFFICIAL_DESTINATION_NO_SENSITIVE_COLLECTION" in codes -> "Linkul ajunge pe domeniu oficial/delegat si nu cere date sensibile."
            "WEAK_OR_EXPLANATORY_EVIDENCE_ONLY" in codes -> "Am gasit doar semnale slabe, precum marketing, CTA, tracking sau explicatii."
            "BRAND_OR_AUTHORITY_CLAIM_NEEDS_VERIFICATION" in codes -> "Mesajul mentioneaza un brand sau o autoritate si trebuie verificat pe canalul oficial."
            result.action == GateAction.INSUFFICIENT_EVIDENCE && result.unknownReason == "WEBMAIL_SHELL_ONLY" -> "Am primit doar shell-ul webmail, nu corpul complet al mesajului."
            result.action == GateAction.INSUFFICIENT_EVIDENCE && result.unknownReason == "OCR_LOW_CONFIDENCE" -> "OCR-ul nu a extras suficient text verificabil."
            result.action == GateAction.INSUFFICIENT_EVIDENCE && result.unknownReason == "PROVIDERS_UNAVAILABLE" -> "Providerii de verificare nu au fost disponibili pentru acest scan."
            result.action == GateAction.INSUFFICIENT_EVIDENCE && result.unknownReason == "NO_TARGET" -> "Nu am o tinta verificabila: lipseste linkul final sau contextul decisiv."
            snapshot?.finalUrl != null -> "Am decis pe baza destinatiei finale, nu doar pe primul link."
            else -> supportText(result)
        }
    }

    fun recommendedActions(result: GateResult): List<String> = when (result.action) {
        GateAction.DO_NOT_CONTINUE -> listOf(
            "Nu apasa linkul.",
            "Deschide manual site-ul sau aplicatia oficiala.",
            "Daca ai introdus date, contacteaza banca imediat."
        )
        GateAction.NO_ENTER_DATA -> listOf(
            "Nu introduce date sensibile.",
            "Inchide pagina si verifica manual canalul oficial.",
            "Daca ai trimis card/OTP, blocheaza cardul si suna banca."
        )
        GateAction.NO_REPLY -> listOf(
            "Nu raspunde mesajului.",
            "Suna persoana sau institutia pe un numar cunoscut oficial.",
            "Nu trimite coduri, bani sau date personale."
        )
        GateAction.VERIFY_OFFICIAL -> listOf(
            "Verifica pe canalul oficial.",
            "Nu folosi numerele sau linkurile din mesaj.",
            "Continua doar dupa confirmare independenta."
        )
        GateAction.CONTINUE_WITH_CAUTION -> listOf(
            "Continua cu prudenta.",
            "Verifica domeniul final inainte de orice actiune.",
            "Nu introduce secrete daca apar cereri neasteptate."
        )
        GateAction.INSUFFICIENT_EVIDENCE -> listOf(
            "Reincearca cu linkul complet sau HTML-ul emailului.",
            "Verifica manual pe canalul oficial.",
            "Nu introduce date pana nu ai confirmare."
        )
    }
}
