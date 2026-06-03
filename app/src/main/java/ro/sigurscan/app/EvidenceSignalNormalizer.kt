package ro.sigurscan.app

import java.net.URI
import java.security.MessageDigest
import java.text.Normalizer
import java.util.Locale
import java.util.UUID
import java.util.regex.Pattern

data class EvidenceNormalizerInput(
    val scanId: String = UUID.randomUUID().toString(),
    val inputKind: String,
    val channel: String,
    val rawText: String = "",
    val htmlContent: String? = null,
    val extractedLinks: List<String> = emptyList(),
    val primaryUrl: String? = null,
    val finalUrl: String? = null,
    val redirectChain: List<String> = emptyList(),
    val senderDomain: String? = null,
    val threatIntel: List<ThreatIntelSourceResult> = emptyList(),
    val providerStates: Map<ProviderId, ProviderState> = emptyMap(),
    val formActionUrl: String? = null,
    val completeness: EvidenceCompleteness? = null,
    val registryVersion: String = "local",
    val corpusVersion: String = "local",
    val virusTotalConfigured: Boolean = false
)

object EvidenceSignalNormalizer {
    private val urlRegex = Pattern.compile(
        "(?:https?://|www\\.)[\\w\\-.~:/?#\\[\\]@!$&'()*+,;=%]+",
        Pattern.CASE_INSENSITIVE
    )

    private val brandPolicies = listOf(
        BrandPolicyLite(
            id = "uber",
            aliases = listOf("uber", "uber eats", "ubereats"),
            officialDomains = ScamRules.TRUSTED_OFFICIAL_DOMAINS["uber"].orEmpty(),
            approvedTrackerDomains = setOf("sng.link", "app.link", "branch.link", "bnc.lt", "uber.link")
        ),
        BrandPolicyLite(
            id = "emag",
            aliases = listOf("emag", "eMAG"),
            officialDomains = ScamRules.TRUSTED_OFFICIAL_DOMAINS["emag"].orEmpty(),
            approvedTrackerDomains = setOf("emag.delivery", "sng.link", "app.link", "branch.link", "bnc.lt")
        ),
        BrandPolicyLite(
            id = "fanCourier",
            aliases = listOf("fan courier", "fancourier", "fanbox", "awb"),
            officialDomains = ScamRules.TRUSTED_OFFICIAL_DOMAINS["fanCourier"].orEmpty()
        ),
        BrandPolicyLite(
            id = "postaRomana",
            aliases = listOf("posta romana", "poșta română", "posta", "poșta"),
            officialDomains = ScamRules.TRUSTED_OFFICIAL_DOMAINS["postaRomana"].orEmpty()
        ),
        BrandPolicyLite(
            id = "anaf",
            aliases = listOf("anaf", "spv", "mfinante", "spatiul privat virtual", "spațiul privat virtual"),
            officialDomains = ScamRules.TRUSTED_OFFICIAL_DOMAINS["anaf"].orEmpty()
        ),
        BrandPolicyLite(
            id = "revolut",
            aliases = listOf("revolut"),
            officialDomains = listOf("revolut.com", "revolut.me", "revolut.space")
        ),
        BrandPolicyLite(
            id = "banks",
            aliases = listOf("banca", "bcr", "ing", "bt", "banca transilvania", "george", "cont sigur"),
            officialDomains = ScamRules.TRUSTED_OFFICIAL_DOMAINS["cardAndBanks"].orEmpty()
        ),
        BrandPolicyLite(
            id = "whatsapp",
            aliases = listOf("whatsapp", "wa.me"),
            officialDomains = ScamRules.TRUSTED_OFFICIAL_DOMAINS["whatsapp"].orEmpty()
        ),
        BrandPolicyLite(
            id = "marketplace",
            aliases = listOf("olx", "marketplace"),
            officialDomains = ScamRules.TRUSTED_OFFICIAL_DOMAINS["marketplace"].orEmpty()
        ),
        BrandPolicyLite(
            id = "dnsc",
            aliases = listOf("dnsc", "siguranta online", "siguranța online"),
            officialDomains = ScamRules.TRUSTED_OFFICIAL_DOMAINS["dnsc"].orEmpty()
        ),
        BrandPolicyLite(
            id = "utilities",
            aliases = listOf("hidroelectrica"),
            officialDomains = ScamRules.TRUSTED_OFFICIAL_DOMAINS["utilities"].orEmpty()
        )
    )

    private val allOfficialDomains = brandPolicies.flatMap { it.officialDomains }.map(::normalizeDomain).toSet()
    private val approvedTrackerDomains = brandPolicies.flatMap { it.approvedTrackerDomains }.map(::normalizeDomain).toSet() +
        setOf(
            "sng.link",
            "app.link",
            "branch.link",
            "bnc.lt",
            "safelinks.protection.outlook.com",
            "urldefense.com"
        )
    private val shortenerDomains = setOf(
        "bit.ly",
        "tinyurl.com",
        "t.co",
        "goo.gl",
        "is.gd",
        "cutt.ly",
        "shorturl.at",
        "rebrand.ly"
    )

    fun buildSnapshot(input: EvidenceNormalizerInput): EvidenceSnapshot {
        val rawForAnalysis = listOfNotNull(input.rawText, input.htmlContent).joinToString("\n")
        val normalizedText = normalizeText(rawForAnalysis)
        val html = input.htmlContent ?: input.rawText.takeIf { looksLikeHtml(it) }
        val htmlLinks = html?.let { HtmlLinkExtractor.extractHtmlLinks(it) }.orEmpty()
        val textUrls = extractUrls(rawForAnalysis)
        val formActionUrls = html?.let { extractFormActionUrls(it) }.orEmpty()
        val allUrls = (input.extractedLinks + htmlLinks + textUrls)
            .mapNotNull(::normalizeUrl)
            .distinct()
        val normalizedRedirectChain = input.redirectChain.mapNotNull(::normalizeUrl)
        val normalizedFinal = normalizeUrl(input.finalUrl) ?: normalizedRedirectChain.lastOrNull()
        val normalizedPrimary = normalizeUrl(input.primaryUrl)
            ?: normalizedFinal?.takeIf { final -> allUrls.contains(final) }
            ?: PrimaryUrlPicker.pick(allUrls, rawForAnalysis).takeIf { it.isNotBlank() }
        val normalizedFormActionUrl = normalizeUrl(input.formActionUrl) ?: formActionUrls.firstOrNull()
        val normalizedFormActionHost = hostOf(normalizedFormActionUrl)
        val targetUrl = normalizedFinal ?: normalizedPrimary
        val primaryHost = hostOf(normalizedPrimary)
        val targetHost = hostOf(targetUrl)
        val claimedBrands = detectClaimedBrands(normalizedText, rawForAnalysis)

        val builder = SignalBuilder(targetHost ?: textTargetKey(normalizedText))
        addLocalSignals(
            builder = builder,
            input = input,
            rawForAnalysis = rawForAnalysis,
            normalizedText = normalizedText,
            html = html,
            allUrls = allUrls,
            formActionUrl = normalizedFormActionUrl,
            formActionHost = normalizedFormActionHost,
            primaryHost = primaryHost,
            targetHost = targetHost,
            claimedBrands = claimedBrands
        )
        addThreatIntelSignals(builder, input.threatIntel, targetHost ?: textTargetKey(normalizedText))

        val providerStates = buildProviderStates(input, builder.signals)
        val completeness = input.completeness ?: inferCompleteness(
            finalUrl = normalizedFinal,
            providerStates = providerStates,
            signals = builder.signals
        )

        return EvidenceSnapshot(
            scanId = input.scanId,
            inputKind = input.inputKind,
            channel = input.channel,
            primaryUrl = normalizedPrimary,
            finalUrl = normalizedFinal,
            formActionUrl = normalizedFormActionUrl,
            formActionHost = normalizedFormActionHost,
            redirectChain = normalizedRedirectChain,
            senderDomain = input.senderDomain,
            claimedBrands = claimedBrands.map { it.id }.toSet(),
            signals = builder.signals,
            providerStates = providerStates,
            registryVersion = input.registryVersion,
            corpusVersion = input.corpusVersion,
            completeness = completeness
        )
    }

    fun fromAssessment(
        inputKind: String,
        channel: String,
        assessment: OfflineAssessment,
        rawText: String = assessment.originalText,
        providerStates: Map<ProviderId, ProviderState> = emptyMap()
    ): EvidenceSnapshot {
        return buildSnapshot(
            EvidenceNormalizerInput(
                scanId = assessment.scanId,
                inputKind = inputKind,
                channel = channel,
                rawText = rawText,
                primaryUrl = assessment.redirectChain.firstOrNull() ?: assessment.finalUrl,
                finalUrl = assessment.finalUrl,
                redirectChain = assessment.redirectChain,
                threatIntel = assessment.threatIntel,
                providerStates = providerStates,
                completeness = if (assessment.finalUrl.isNullOrBlank()) null else EvidenceCompleteness.PARTIAL_ONLINE
            )
        )
    }

    private fun addLocalSignals(
        builder: SignalBuilder,
        input: EvidenceNormalizerInput,
        rawForAnalysis: String,
        normalizedText: String,
        html: String?,
        allUrls: List<String>,
        formActionUrl: String?,
        formActionHost: String?,
        primaryHost: String?,
        targetHost: String?,
        claimedBrands: List<BrandPolicyLite>
    ) {
        val effectiveTargetHost = formActionHost ?: targetHost
        val hasTarget = !effectiveTargetHost.isNullOrBlank()
        val targetIsOfficial = targetHost?.let(::isOfficialHost) == true
        val targetIsApprovedTracker = targetHost?.let(::isApprovedTrackerHost) == true
        val effectiveIsOfficial = effectiveTargetHost?.let(::isOfficialHost) == true
        val effectiveIsApprovedTracker = effectiveTargetHost?.let(::isApprovedTrackerHost) == true
        val primaryIsApprovedTracker = primaryHost?.let(::isApprovedTrackerHost) == true
        val sensitiveCodes = detectSensitiveCodes(normalizedText, allUrls)
        val hasSensitiveRisk = sensitiveCodes.isNotEmpty()
        if (!formActionUrl.isNullOrBlank()) {
            builder.add(
                source = EvidenceSource.HTML_EXTRACTOR,
                code = EvidenceCode.HTML_BUTTON_LINK,
                targetKey = formActionHost.orEmpty()
            )
        }

        if ((input.channel.contains("webmail", ignoreCase = true) || normalizedText.contains("webmail")) && allUrls.isEmpty()) {
            builder.add(EvidenceSource.LOCAL_EXTRACTOR, EvidenceCode.WEBMAIL_SHELL_ONLY)
        }

        if (!hasTarget && allUrls.isEmpty() && normalizedText.isBlank()) {
            builder.add(EvidenceSource.LOCAL_EXTRACTOR, EvidenceCode.NO_TARGET)
        }

        html?.takeIf { it.isNotBlank() }?.let { htmlContent ->
            if (looksLikeHtml(htmlContent)) {
                if (htmlContent.contains(Regex("(?is)<\\s*(a|button|form|input)\\b"))) {
                    builder.add(EvidenceSource.HTML_EXTRACTOR, EvidenceCode.HTML_BUTTON_LINK)
                }
                if (allUrls.isNotEmpty()) {
                    builder.add(EvidenceSource.HTML_EXTRACTOR, EvidenceCode.HIDDEN_LINK_PRESENT)
                }
                if (hasOfficialLookingTextToUnofficialHref(htmlContent, claimedBrands)) {
                    builder.add(EvidenceSource.HTML_EXTRACTOR, EvidenceCode.HIDDEN_LINK_OFFICIAL_TO_UNOFFICIAL)
                }
            }
        }

        if (allUrls.any { isTrackingUrl(it) }) {
            builder.add(EvidenceSource.HTML_EXTRACTOR, EvidenceCode.TRACKING_LINK)
        }

        if (primaryHost != null && isShortenerHost(primaryHost) && input.finalUrl.isNullOrBlank()) {
            builder.add(EvidenceSource.LOCAL_EXTRACTOR, EvidenceCode.UNRESOLVED_SHORTLINK, targetKey = primaryHost)
        }

        addMarketingSignals(builder, normalizedText)
        addRomaniaScenarioSignals(builder, normalizedText)
        sensitiveCodes.forEach { builder.add(EvidenceSource.LOCAL_EXTRACTOR, it) }

        if (targetIsOfficial) {
            builder.add(EvidenceSource.OFFICIAL_REGISTRY, EvidenceCode.OFFICIAL_DOMAIN_EXACT, targetKey = targetHost.orEmpty())
        } else if (targetIsApprovedTracker) {
            builder.add(EvidenceSource.OFFICIAL_REGISTRY, EvidenceCode.APPROVED_TRACKER_DOMAIN, targetKey = targetHost.orEmpty())
        }

        if (primaryIsApprovedTracker) {
            builder.add(EvidenceSource.OFFICIAL_REGISTRY, EvidenceCode.APPROVED_TRACKER_DOMAIN, targetKey = primaryHost.orEmpty())
        }

        if (primaryIsApprovedTracker && targetIsOfficial) {
            builder.add(EvidenceSource.OFFICIAL_REGISTRY, EvidenceCode.REDIRECT_CHAIN_APPROVED, targetKey = targetHost.orEmpty())
        }

        if (hasTarget && (!hasSensitiveRisk || targetIsOfficial || effectiveIsOfficial) && !hasSensitiveForm(rawForAnalysis)) {
            builder.add(EvidenceSource.LOCAL_EXTRACTOR, EvidenceCode.NO_SENSITIVE_FORM)
        }

        if (hasSensitiveForm(rawForAnalysis) && !effectiveIsOfficial && !effectiveIsApprovedTracker) {
            builder.add(EvidenceSource.LOCAL_EXTRACTOR, EvidenceCode.SENSITIVE_FORM_UNOFFICIAL)
            if (!formActionHost.isNullOrBlank() && claimedBrands.isNotEmpty()) {
                builder.add(
                    EvidenceSource.OFFICIAL_REGISTRY,
                    EvidenceCode.OFFICIAL_DOMAIN_MISMATCH,
                    targetKey = formActionHost
                )
            }
        }

        if (claimedBrands.isNotEmpty() && hasTarget) {
            val officialForClaim = claimedBrands.any { it.isOfficialHost(effectiveTargetHost.orEmpty()) }
            val delegatedForClaim = claimedBrands.any { it.isApprovedTrackerHost(effectiveTargetHost.orEmpty()) }
            if (officialForClaim) {
                builder.add(EvidenceSource.OFFICIAL_REGISTRY, EvidenceCode.OFFICIAL_DOMAIN_EXACT, targetKey = effectiveTargetHost.orEmpty())
            } else if (delegatedForClaim) {
                builder.add(EvidenceSource.OFFICIAL_REGISTRY, EvidenceCode.DELEGATED_DOMAIN_EXACT, targetKey = effectiveTargetHost.orEmpty())
            } else if (!effectiveIsApprovedTracker) {
                builder.add(EvidenceSource.LOCAL_EXTRACTOR, EvidenceCode.BRAND_IMPERSONATION)
                builder.add(EvidenceSource.LOCAL_EXTRACTOR, EvidenceCode.OFFICIAL_DOMAIN_MISMATCH, targetKey = effectiveTargetHost.orEmpty())
            }
        }

        if (isCourierClaim(normalizedText) && hasTarget && !effectiveIsOfficial && !effectiveIsApprovedTracker) {
            builder.add(EvidenceSource.ROMANIA_SCENARIO, EvidenceCode.COURIER_UNOFFICIAL_DOMAIN)
        }
        if (containsAny(normalizedText, "colet", "locker", "awb", "livrare", "curier") &&
            containsAny(normalizedText, "taxa", "taxă", "plata", "plată", "ramburs") &&
            hasTarget) {
            builder.add(EvidenceSource.ROMANIA_SCENARIO, EvidenceCode.PARCEL_TAX)
        }
        if (containsAny(normalizedText, "anaf", "spv", "impozit", "taxa", "taxă", "rambursare")) {
            builder.add(EvidenceSource.ROMANIA_SCENARIO, EvidenceCode.TAX_NOTICE)
        }
        if (containsAny(normalizedText, "cont suspendat", "contul suspendat", "deblocare cont", "account suspend")) {
            builder.add(EvidenceSource.LOCAL_EXTRACTOR, EvidenceCode.ACCOUNT_SUSPEND)
        }
    }

    private fun addThreatIntelSignals(
        builder: SignalBuilder,
        threatIntel: List<ThreatIntelSourceResult>,
        targetKey: String
    ) {
        threatIntel.forEach { item ->
            val source = item.source.lowercase(Locale.US)
            val text = listOf(item.source, item.verdict, item.severity, item.details.orEmpty())
                .joinToString(" ")
                .lowercase(Locale.US)
            val sourceKey = providerSourceKey(item.source)
            when {
                sourceKey.contains("webrisk") -> mapWebRisk(builder, item, text, targetKey)
                source.contains("urlscan") -> mapUrlscan(builder, item, text, targetKey)
                source.contains("virustotal") || source == "vt" -> mapVirusTotal(builder, item, text, targetKey)
            }
        }
    }

    private fun mapWebRisk(builder: SignalBuilder, item: ThreatIntelSourceResult, text: String, targetKey: String) {
        if (containsAny(text, "no threats", "no threat", "no-match", "no match", "clean")) {
            builder.add(EvidenceSource.GOOGLE_WEB_RISK, EvidenceCode.WEBRISK_NO_MATCH, targetKey = targetKey, provider = ProviderId.WEB_RISK)
            return
        }

        val high = item.severity.equals("high", ignoreCase = true) || containsAny(text, "threats detected", "malware", "phishing", "social_engineering", "unwanted_software")

        if (text.contains("malware")) {
            builder.add(EvidenceSource.GOOGLE_WEB_RISK, EvidenceCode.WEBRISK_MATCH_MALWARE, targetKey = targetKey, provider = ProviderId.WEB_RISK)
        }
        if (text.contains("unwanted_software") || text.contains("unwanted software")) {
            builder.add(EvidenceSource.GOOGLE_WEB_RISK, EvidenceCode.WEBRISK_MATCH_UNWANTED_SOFTWARE, targetKey = targetKey, provider = ProviderId.WEB_RISK)
        }
        if (text.contains("social_engineering_extended") || text.contains("extended_coverage")) {
            builder.add(EvidenceSource.GOOGLE_WEB_RISK, EvidenceCode.WEBRISK_MATCH_SOCIAL_ENGINEERING_EXT, targetKey = targetKey, provider = ProviderId.WEB_RISK)
        }
        if (text.contains("social_engineering") || text.contains("phishing") || (high && !text.contains("malware"))) {
            builder.add(EvidenceSource.GOOGLE_WEB_RISK, EvidenceCode.WEBRISK_MATCH_SOCIAL_ENGINEERING, targetKey = targetKey, provider = ProviderId.WEB_RISK)
        }
    }

    private fun mapUrlscan(builder: SignalBuilder, item: ThreatIntelSourceResult, text: String, targetKey: String) {
        val high = item.severity.equals("high", ignoreCase = true)
        when {
            containsAny(text, "no malicious", "no classification", "clean", "low", "no threats") -> builder.add(EvidenceSource.URLSCAN, EvidenceCode.URLSCAN_NO_CLASSIFICATION, targetKey = targetKey, provider = ProviderId.URLSCAN)
            text.contains("malware") -> builder.add(EvidenceSource.URLSCAN, EvidenceCode.URLSCAN_VERDICT_MALWARE, targetKey = targetKey, provider = ProviderId.URLSCAN)
            text.contains("phishing") || text.contains("malicious") || high -> builder.add(EvidenceSource.URLSCAN, EvidenceCode.URLSCAN_VERDICT_PHISHING, targetKey = targetKey, provider = ProviderId.URLSCAN)
        }
    }

    private fun mapVirusTotal(builder: SignalBuilder, item: ThreatIntelSourceResult, text: String, targetKey: String) {
        val high = item.severity.equals("high", ignoreCase = true)
        val maliciousCount = Regex("""malicious\s*[=:]\s*(\d+)""").find(text)?.groupValues?.getOrNull(1)?.toIntOrNull() ?: 0
        when {
            maliciousCount >= 3 || (high && containsAny(text, "malicious", "suspicious")) -> {
                builder.add(EvidenceSource.VIRUSTOTAL, EvidenceCode.VIRUSTOTAL_MALICIOUS_CONSENSUS, targetKey = targetKey, provider = ProviderId.VIRUSTOTAL)
            }
            containsAny(text, "clean", "harmless", "undetected", "not found", "low") -> {
                builder.add(EvidenceSource.VIRUSTOTAL, EvidenceCode.VIRUSTOTAL_LOW_OR_NO_DETECTION, targetKey = targetKey, provider = ProviderId.VIRUSTOTAL)
            }
        }
    }

    private fun addMarketingSignals(builder: SignalBuilder, normalizedText: String) {
        if (containsAny(normalizedText, "voucher", "card cadou", "premiu", "gratuit", "promo code", "cod promo")) {
            builder.add(EvidenceSource.LOCAL_EXTRACTOR, EvidenceCode.VOUCHER_TEXT)
        }
        if (containsAny(normalizedText, "promo", "promotie", "promoție", "oferta", "ofertă", "reducere", "discount")) {
            builder.add(EvidenceSource.LOCAL_EXTRACTOR, EvidenceCode.PROMO_TEXT)
        }
        if (containsAny(normalizedText, "nu rata", "ultima sansa", "ultima șansă", "expira azi", "expiră azi", "urgent", "imediat")) {
            builder.add(EvidenceSource.LOCAL_EXTRACTOR, EvidenceCode.MARKETING_URGENCY)
        }
        if (containsAny(normalizedText, "click", "apas", "apasă", "deschide", "vezi oferta", "continua", "continuă", "confirma", "confirmă")) {
            builder.add(EvidenceSource.LOCAL_EXTRACTOR, EvidenceCode.CTA_TEXT)
        }
    }

    private fun addRomaniaScenarioSignals(builder: SignalBuilder, normalizedText: String) {
        if (containsAny(normalizedText, "telefon stricat", "mi s-a stricat telefonul", "numar nou", "număr nou") && hasMoneyRequest(normalizedText)) {
            builder.add(EvidenceSource.ROMANIA_SCENARIO, EvidenceCode.FAMILY_NEW_PHONE_MONEY)
        }
        if (containsAny(normalizedText, "accident", "nepot", "fiul tau", "fiica ta", "spital") && hasMoneyRequest(normalizedText)) {
            builder.add(EvidenceSource.ROMANIA_SCENARIO, EvidenceCode.ACCIDENT_NEPHEW_MONEY)
        }
        val whatsappCodeEducationalNegation = containsAny(
            normalizedText,
            "nu introduce coduri whatsapp",
            "nu introduceți coduri whatsapp",
            "nu introduceti coduri whatsapp",
            "nu trimite coduri whatsapp",
            "nu comunica coduri whatsapp",
            "nu comunicați coduri whatsapp",
            "nu comunicati coduri whatsapp"
        )
        if (!whatsappCodeEducationalNegation && containsAny(normalizedText, "whatsapp") && containsAny(normalizedText, "cod", "otp", "verificare", "sms")) {
            builder.add(EvidenceSource.ROMANIA_SCENARIO, EvidenceCode.WHATSAPP_CODE_REQUEST)
        }
        if (containsAny(normalizedText, "whatsapp") && containsAny(normalizedText, "dispozitiv", "device", "linking", "asociere")) {
            builder.add(EvidenceSource.ROMANIA_SCENARIO, EvidenceCode.WHATSAPP_DEVICE_LINKING_REQUEST)
        }
        if (containsAny(normalizedText, "bnr", "cont sigur", "cont de siguranta", "cont de siguranță")) {
            builder.add(EvidenceSource.ROMANIA_SCENARIO, EvidenceCode.BNR_SAFE_ACCOUNT)
        }
        if (containsAny(normalizedText, "credit fraudulos", "credit pe numele", "politia", "poliția") &&
            containsAny(normalizedText, "banca", "transfer", "cont sigur", "bnr")) {
            builder.add(EvidenceSource.ROMANIA_SCENARIO, EvidenceCode.FRAUDULENT_CREDIT_AUTHORITY_CHAIN)
        }
        if (containsAny(normalizedText, "ca sa primesti banii", "ca să primești banii", "primeste banii", "primești banii")) {
            builder.add(EvidenceSource.ROMANIA_SCENARIO, EvidenceCode.MARKETPLACE_RECEIVE_MONEY)
        }
        if (containsAny(normalizedText, "credit") &&
            containsAny(normalizedText, "fraudulos", "aprobat", "numele tau", "numele tău") &&
            containsAny(normalizedText, "banca", "bancara", "bancară", "datele de acces", "aplicatia bancara", "aplicația bancară")) {
            builder.add(EvidenceSource.ROMANIA_SCENARIO, EvidenceCode.FRAUDULENT_CREDIT_AUTHORITY_CHAIN)
        }
        if (containsAny(normalizedText, "spune", "spuneti", "spuneți", "raspunde", "răspunde", "trimite", "comunica", "comunică") &&
            containsAny(normalizedText, "cod", "otp", "sms", "pin", "parola", "parolă", "date de acces", "ultimele 4 cifre")) {
            builder.add(EvidenceSource.ROMANIA_SCENARIO, EvidenceCode.REPLY_WITH_CODE_REQUEST)
        }
        if (containsAny(normalizedText, "anydesk", "teamviewer", "remote access", "control la distanta", "control la distanță")) {
            builder.add(EvidenceSource.LOCAL_EXTRACTOR, EvidenceCode.REMOTE_ACCESS_DOWNLOAD_UNOFFICIAL)
        }
        if (containsAny(normalizedText, "apk", "instaleaza aplicatia", "instalează aplicația", "descarca aplicatia", "descarcă aplicația")) {
            builder.add(EvidenceSource.LOCAL_EXTRACTOR, EvidenceCode.APK_DOWNLOAD_UNOFFICIAL)
        }
        if (hasMoneyRequest(normalizedText)) {
            builder.add(EvidenceSource.ROMANIA_SCENARIO, EvidenceCode.MONEY_REQUEST)
        }
        if (containsAny(normalizedText, "raspunde cu cod", "răspunde cu cod", "trimite codul", "spune codul")) {
            builder.add(EvidenceSource.ROMANIA_SCENARIO, EvidenceCode.REPLY_WITH_CODE_REQUEST)
        }
    }

    private fun detectSensitiveCodes(normalizedText: String, urls: List<String>): Set<EvidenceCode> {
        val visibleText = normalizedText
            .replace(Regex("(?is)<\\s*(style|script)\\b.*?</\\s*\\1\\s*>"), " ")
            .replace(Regex("(?is)<[^>]+>"), " ")
        val combined = (visibleText + " " + urls.joinToString(" ")).lowercase(Locale.US)
        val output = linkedSetOf<EvidenceCode>()
        val sensitiveCardField = Regex("""(?i)\b(name|id|placeholder)\s*=\s*['"][^'"]*(card|numar[_-]?card|număr[_-]?card|cc-number)[^'"]*['"]""")
            .containsMatchIn(normalizedText)
        val sensitiveCvvField = Regex("""(?i)\b(name|id|placeholder)\s*=\s*['"][^'"]*(cvv|cvc|cvv2|security[_-]?code)[^'"]*['"]""")
            .containsMatchIn(normalizedText)
        val cardIsEducationalNegation = containsAny(
            combined,
            "nu introduce card",
            "nu introduceți card",
            "nu introduceti card",
            "nu iti cerem coduri",
            "nu îți cerem coduri",
            "nu va cerem coduri",
            "nu vă cerem coduri"
        )
        val cardRequestPattern = Regex("""(?i)(introdu|completeaz|confirm|valideaz|plat(e|ă)ste|pl(a|ă)t(e|ă)|spune|r(a|ă)spunde|trimite|tax(a|ă)|prime(s|ș)ti banii).{0,48}(card|num(a|ă)r card|date card)|(card|num(a|ă)r card|date card).{0,48}(cvv|cvc|pin|confirm|valideaz|plat(e|ă)ste|pl(a|ă)t(e|ă)|tax(a|ă))""")
        if (!cardIsEducationalNegation && (sensitiveCardField || cardRequestPattern.containsMatchIn(combined) || containsAny(combined, "numar card", "număr card", "date card"))) {
            output.add(EvidenceCode.CARD_REQUEST)
        }
        if (sensitiveCvvField || containsAny(combined, "cvv", "cvc", "cvv2")) output.add(EvidenceCode.CVV_REQUEST)
        if (containsAny(combined, "otp", "cod sms", "codul sms", "cod de verificare", "codul primit", "cod primit", "3d secure")) output.add(EvidenceCode.OTP_REQUEST)
        if (containsAny(combined, "parola", "parolă", "password", "pin bancar", "pin-ul", "pin ", "date de acces")) output.add(EvidenceCode.PASSWORD_REQUEST)
        if (containsAny(
                combined,
                "cnp",
                "iban",
                "date personale",
                "datele personale",
                "actualizare date",
                "actualizeaza date",
                "actualizează date",
                "completeaza datele",
                "completează datele",
                "completeaza nume",
                "completează nume",
                "nume, adresa",
                "nume, adresă",
                "telefon pentru livrare",
                "verificare identitate",
                "identitate bancara",
                "identitate bancară",
                "/date",
                "/confirmare"
            )
        ) output.add(EvidenceCode.CNP_IBAN_REQUEST)
        if (containsAny(combined, "plata", "plată", "plateste", "plătește", "payment", "checkout", "taxa", "taxă")) output.add(EvidenceCode.PAYMENT_REQUEST)
        return output
    }

    private fun hasSensitiveForm(raw: String): Boolean {
        val normalized = normalizeText(raw)
        val hasForm = raw.contains(Regex("(?is)<\\s*(form|input|textarea|select)\\b"))
        val hasSensitive = containsAny(
            normalized,
            "card",
            "cvv",
            "cvc",
            "otp",
            "parola",
            "parolă",
            "password",
            "iban",
            "cnp",
            "payment",
            "checkout",
            "plata",
            "plată"
        )
        return hasForm && hasSensitive
    }

    private fun hasOfficialLookingTextToUnofficialHref(html: String, claimedBrands: List<BrandPolicyLite>): Boolean {
        val anchorPattern = Regex("""(?is)<\s*(a|button)[^>]*(?:href|formaction|data-href|data-url)\s*=\s*(["'])(.*?)\2[^>]*>(.*?)</\s*\1\s*>""")
        anchorPattern.findAll(html).forEach { match ->
            val href = normalizeUrl(match.groupValues.getOrNull(3)) ?: return@forEach
            val visible = normalizeText(match.groupValues.getOrNull(4).orEmpty())
            val host = hostOf(href) ?: return@forEach
            val claimsOfficial = allOfficialDomains.any { visible.contains(it) } || claimedBrands.any { brand ->
                brand.aliases.any { visible.contains(normalizeText(it)) }
            }
            if (claimsOfficial && !isOfficialHost(host) && !isApprovedTrackerHost(host)) return true
        }

        val normalizedHtml = normalizeText(html)
        val mentionedOfficialDomain = allOfficialDomains.any { normalizedHtml.contains(it) }
        val hrefHosts = HtmlLinkExtractor.extractHtmlLinks(html).mapNotNull(::hostOf)
        return mentionedOfficialDomain && hrefHosts.any { !isOfficialHost(it) && !isApprovedTrackerHost(it) }
    }

    private fun detectClaimedBrands(normalizedText: String, rawForAnalysis: String): List<BrandPolicyLite> {
        val normalizedRaw = normalizeText(rawForAnalysis)
        return brandPolicies.filter { policy ->
            policy.aliases.any { alias -> containsAlias(normalizedText, alias) || containsAlias(normalizedRaw, alias) }
        }
    }

    private fun containsAlias(text: String, alias: String): Boolean {
        val normalizedAlias = normalizeText(alias)
        if (normalizedAlias.isBlank()) return false
        if (normalizedAlias.length <= 3) {
            return Regex("""(?<![a-z0-9])${Regex.escape(normalizedAlias)}(?![a-z0-9])""").containsMatchIn(text)
        }
        return text.contains(normalizedAlias)
    }

    private fun buildProviderStates(
        input: EvidenceNormalizerInput,
        signals: List<EvidenceSignal>
    ): Map<ProviderId, ProviderState> {
        val states = mutableMapOf<ProviderId, ProviderState>()
        states.putAll(input.providerStates)
        listOf(ProviderId.WEB_RISK, ProviderId.URLSCAN, ProviderId.VIRUSTOTAL).forEach { provider ->
            if (states[provider] == null) {
                val hasSignal = signals.any { it.provider == provider }
                states[provider] = when {
                    hasSignal -> ProviderState(provider, ProviderStatus.OK)
                    provider == ProviderId.VIRUSTOTAL && !input.virusTotalConfigured -> ProviderState(provider, ProviderStatus.SKIPPED, note = "VirusTotal not configured")
                    else -> ProviderState(provider, ProviderStatus.NOT_RUN)
                }
            }
        }
        input.threatIntel.forEach { item ->
            val provider = providerForThreatIntel(item) ?: return@forEach
            states[provider] = ProviderState(provider, inferProviderStatus(item))
        }
        return states
    }

    private fun inferProviderStatus(item: ThreatIntelSourceResult): ProviderStatus {
        val text = listOf(item.verdict, item.severity, item.details.orEmpty()).joinToString(" ").lowercase(Locale.US)
        return when {
            containsAny(text, "pending", "queued", "in-progress", "in progress", "processing") -> ProviderStatus.PENDING
            containsAny(text, "rate limited", "429") -> ProviderStatus.RATE_LIMITED
            containsAny(text, "timeout", "timed out") -> ProviderStatus.TIMEOUT
            containsAny(text, "error", "unavailable", "failed") -> ProviderStatus.ERROR
            containsAny(text, "skipped", "not configured", "not run") -> ProviderStatus.SKIPPED
            else -> ProviderStatus.OK
        }
    }

    private fun inferCompleteness(
        finalUrl: String?,
        providerStates: Map<ProviderId, ProviderState>,
        signals: List<EvidenceSignal>
    ): EvidenceCompleteness {
        if (providerStates.values.any { it.status == ProviderStatus.PENDING }) return EvidenceCompleteness.PARTIAL_ONLINE
        if (finalUrl != null) return EvidenceCompleteness.FULL
        if (signals.any { it.provider != null }) return EvidenceCompleteness.PARTIAL_ONLINE
        return EvidenceCompleteness.LOCAL_ONLY
    }

    private fun providerForThreatIntel(item: ThreatIntelSourceResult): ProviderId? {
        val source = item.source.lowercase(Locale.US)
        val sourceKey = providerSourceKey(item.source)
        return when {
            sourceKey.contains("webrisk") -> ProviderId.WEB_RISK
            source.contains("urlscan") -> ProviderId.URLSCAN
            source.contains("virustotal") || source == "vt" -> ProviderId.VIRUSTOTAL
            else -> null
        }
    }

    private fun providerSourceKey(source: String): String {
        return source.lowercase(Locale.US).replace(Regex("[^a-z0-9]+"), "")
    }

    private fun extractUrls(input: String): List<String> {
        val matcher = urlRegex.matcher(input)
        val urls = mutableListOf<String>()
        while (matcher.find()) {
            urls.add(matcher.group().trimEnd('.', ',', ';', ')', ']', '}', '"', '\''))
        }
        return urls
    }

    private fun normalizeUrl(raw: String?): String? {
        if (raw.isNullOrBlank()) return null
        return HtmlLinkExtractor.normalizeCandidateUrl(raw) ?: run {
            val trimmed = raw.trim().trimEnd('.', ',', ';', ')', ']', '}', '"', '\'')
            when {
                trimmed.startsWith("http://", ignoreCase = true) || trimmed.startsWith("https://", ignoreCase = true) -> trimmed
                trimmed.startsWith("www.", ignoreCase = true) -> "https://$trimmed"
                else -> null
            }
        }
    }

    private fun hostOf(url: String?): String? {
        val normalized = normalizeUrl(url) ?: url ?: return null
        return runCatching {
            URI(normalized).host?.lowercase(Locale.US)?.removePrefix("www.")?.takeIf { it.isNotBlank() }
        }.getOrNull()
    }

    private fun normalizeDomain(domain: String): String = domain.lowercase(Locale.US).removePrefix("www.")

    private fun isOfficialHost(host: String): Boolean {
        val normalized = normalizeDomain(host)
        return allOfficialDomains.any { normalized == it || normalized.endsWith(".$it") }
    }

    private fun isApprovedTrackerHost(host: String): Boolean {
        val normalized = normalizeDomain(host)
        return approvedTrackerDomains.any { normalized == it || normalized.endsWith(".$it") }
    }

    private fun isShortenerHost(host: String): Boolean {
        val normalized = normalizeDomain(host)
        return shortenerDomains.any { normalized == it || normalized.endsWith(".$it") }
    }

    private fun isTrackingUrl(url: String): Boolean {
        val host = hostOf(url) ?: return false
        val normalized = url.lowercase(Locale.US)
        return isApprovedTrackerHost(host) ||
            containsAny(normalized, "track", "tracking", "click", "utm_", "redirect", "safelinks")
    }

    private fun isCourierClaim(text: String): Boolean {
        return containsAny(text, "fan courier", "fancourier", "fanbox", "posta", "poșta", "curier", "colet", "awb", "locker")
    }

    private fun hasMoneyRequest(text: String): Boolean {
        return containsAny(text, "trimite bani", "transfer", "bani", "ron", "euro", "lei", "plata", "plată", "depunere")
    }

    private fun extractFormActionUrls(html: String): List<String> {
        if (html.isBlank()) return emptyList()
        val pattern = Regex("""(?i)<\s*(form|button|input)\b[^>]*\b(formaction|action)\s*=\s*(?:(['\"])(.*?)\3|([^\"'\s>]+))""")
        return pattern.findAll(html)
            .mapNotNull { match ->
                val raw = listOfNotNull(
                    match.groupValues.getOrNull(4),
                    match.groupValues.getOrNull(5)
                ).firstOrNull { it.isNotBlank() }
                normalizeUrl(raw)
            }
            .distinct()
            .toList()
    }

    private fun looksLikeHtml(value: String): Boolean {
        return value.contains(Regex("(?is)<\\s*(html|body|a|button|form|input|div|span|p|meta|script)\\b"))
    }

    private fun normalizeText(value: String): String {
        val decomposed = Normalizer.normalize(value, Normalizer.Form.NFD)
        return decomposed
            .replace(Regex("\\p{Mn}+"), "")
            .lowercase(Locale.getDefault())
    }

    private fun containsAny(value: String, vararg needles: String): Boolean {
        return needles.any { value.contains(normalizeText(it)) || value.contains(it.lowercase(Locale.getDefault())) }
    }

    private fun textTargetKey(normalizedText: String): String {
        return "text:${sha256(normalizedText.take(256))}"
    }

    private fun sha256(value: String): String {
        val digest = MessageDigest.getInstance("SHA-256").digest(value.toByteArray())
        return digest.joinToString("") { "%02x".format(it) }.take(16)
    }

    private data class BrandPolicyLite(
        val id: String,
        val aliases: List<String>,
        val officialDomains: List<String>,
        val approvedTrackerDomains: Set<String> = emptySet()
    ) {
        fun isOfficialHost(host: String): Boolean {
            val normalizedHost = normalizeDomain(host)
            return officialDomains.map(::normalizeDomain).any { normalizedHost == it || normalizedHost.endsWith(".$it") }
        }

        fun isApprovedTrackerHost(host: String): Boolean {
            val normalizedHost = normalizeDomain(host)
            return approvedTrackerDomains.map(::normalizeDomain).any { normalizedHost == it || normalizedHost.endsWith(".$it") }
        }
    }

    private class SignalBuilder(private val defaultTargetKey: String) {
        private val mutableSignals = mutableListOf<EvidenceSignal>()
        val signals: List<EvidenceSignal> get() = mutableSignals

        fun add(
            source: EvidenceSource,
            code: EvidenceCode,
            targetKey: String = defaultTargetKey,
            brandId: String? = null,
            provider: ProviderId? = null,
            attrs: Map<String, String> = emptyMap()
        ) {
            val key = listOf(source.name, code.name, targetKey, brandId.orEmpty(), provider?.name.orEmpty()).joinToString("|")
            if (mutableSignals.any { it.attrs["dedupeKey"] == key }) return
            mutableSignals.add(
                EvidenceSignal(
                    id = "sig-${mutableSignals.size + 1}-${code.name.lowercase(Locale.US)}",
                    source = source,
                    code = code,
                    targetKey = targetKey,
                    brandId = brandId,
                    provider = provider,
                    attrs = attrs + ("dedupeKey" to key)
                )
            )
        }
    }
}
