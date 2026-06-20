package ro.sigurscan.app

// Evidence/gate domain types (enums + data classes) extracted from EvidenceGate.kt.

enum class GateAction(val userLabel: String) {
    DO_NOT_CONTINUE("Periculos"),
    NO_ENTER_DATA("Periculos"),
    NO_REPLY("Periculos"),
    VERIFY_OFFICIAL("Suspect"),
    CONTINUE_WITH_CAUTION("Sigur"),
    UNVERIFIED("Neverificat"),
    INSUFFICIENT_EVIDENCE("Suspect")
}

enum class GateFinality {
    PROVISIONAL,
    FINAL
}

enum class EvidenceSource {
    LOCAL_EXTRACTOR,
    HTML_EXTRACTOR,
    INFRA_ANALYZER,
    OFFICIAL_REGISTRY,
    ROMANIA_SCENARIO,
    GOOGLE_WEB_RISK,
    URLSCAN,
    PHISHING_DATABASE,
    CLAIM_VERIFIER,
    USER_FEEDBACK,
    CORPUS,
    RAG
}

enum class ProviderId {
    WEB_RISK,
    URLSCAN,
    PHISHING_DATABASE,
    INFRA,
    CLAIM_VERIFIER,
    OFFICIAL_REGISTRY,
    CORPUS,
    RAG
}

enum class ProviderStatus {
    NOT_RUN,
    OK,
    PENDING,
    RATE_LIMITED,
    TIMEOUT,
    ERROR,
    SKIPPED
}

enum class EvidenceCompleteness {
    LOCAL_ONLY,
    PARTIAL_ONLINE,
    FULL
}

enum class EvidenceCode {
    WEBRISK_MATCH_MALWARE,
    WEBRISK_MATCH_SOCIAL_ENGINEERING,
    WEBRISK_MATCH_UNWANTED_SOFTWARE,
    WEBRISK_MATCH_SOCIAL_ENGINEERING_EXT,
    WEBRISK_NO_MATCH,
    URLSCAN_VERDICT_PHISHING,
    URLSCAN_VERDICT_MALWARE,
    URLSCAN_NO_CLASSIFICATION,
    PHISHING_DATABASE_LISTED,
    PHISHING_DATABASE_NOT_LISTED,
    OFFER_CLAIM_CONFIRMED,
    OFFER_CLAIM_NOT_FOUND,
    OFFER_CLAIM_INCONCLUSIVE,
    DOMAIN_AGE_SUSPICIOUS,
    DOMAIN_AGE_VERY_RECENT,
    TYPOSQUAT_LOOKALIKE,
    HOMOGLYPH_DOMAIN,
    PUNYCODE_HOST,
    DGA_ENTROPY_HIGH,
    URL_BEHAVIOUR_SUSPICIOUS,
    URL_TRANSPORT_RISK,
    APK_DOWNLOAD_UNOFFICIAL,
    REMOTE_ACCESS_DOWNLOAD_UNOFFICIAL,
    BRAND_IMPERSONATION,
    OFFICIAL_DOMAIN_MISMATCH,
    HIDDEN_LINK_OFFICIAL_TO_UNOFFICIAL,
    HIDDEN_LINK_PRESENT,
    HTML_BUTTON_LINK,
    TRACKING_LINK,
    UNRESOLVED_SHORTLINK,
    SENSITIVE_FORM_UNOFFICIAL,
    CARD_REQUEST,
    CVV_REQUEST,
    OTP_REQUEST,
    PASSWORD_REQUEST,
    CNP_IBAN_REQUEST,
    PERSONAL_DATA_REQUEST,
    PAYMENT_REQUEST,
    REPLY_WITH_CODE_REQUEST,
    MONEY_REQUEST,
    FAMILY_NEW_PHONE_MONEY,
    FAMILY_EMERGENCY_MONEY,
    ACCIDENT_NEPHEW_MONEY,
    WHATSAPP_CODE_REQUEST,
    WHATSAPP_DEVICE_LINKING_REQUEST,
    BNR_SAFE_ACCOUNT,
    FRAUDULENT_CREDIT_AUTHORITY_CHAIN,
    MARKETPLACE_RECEIVE_MONEY,
    COURIER_UNOFFICIAL_DOMAIN,
    PARCEL_TAX,
    TAX_NOTICE,
    ACCOUNT_SUSPEND,
    MARKETING_URGENCY,
    PROMO_TEXT,
    VOUCHER_TEXT,
    CTA_TEXT,
    DISPLAY_NAME_BRAND_ONLY,
    CORPUS_SIMILARITY,
    CORPUS_BRAND_WARNING,
    USER_REPORT_UNVERIFIED,
    RAG_EXPLANATION,
    OFFICIAL_DOMAIN_EXACT,
    DELEGATED_DOMAIN_EXACT,
    APPROVED_TRACKER_DOMAIN,
    REDIRECT_CHAIN_APPROVED,
    NO_SENSITIVE_FORM,
    TRACKING_ONLY_NO_PAYMENT,
    PROMO_CODE_REDEEM_IN_APP,
    LIST_UNSUBSCRIBE_PRESENT,
    WEBMAIL_SHELL_ONLY,
    OCR_LOW_CONFIDENCE,
    PROVIDERS_UNAVAILABLE,
    NO_TARGET
}

data class ProviderState(
    val provider: ProviderId,
    val status: ProviderStatus,
    val retryAtMillis: Long? = null,
    val note: String? = null
)

data class EvidenceSignal(
    val id: String,
    val source: EvidenceSource,
    val code: EvidenceCode,
    val targetKey: String,
    val brandId: String? = null,
    val reliability: Int = EvidenceGatePolicy.defaultReliability(code),
    val maxSoloAction: GateAction = EvidenceGatePolicy.maxSoloAction(code),
    val attrs: Map<String, String> = emptyMap(),
    val excerptRedacted: String? = null,
    val provider: ProviderId? = null,
    val providerRef: String? = null,
    val observedAtMillis: Long = 0L,
    val expiresAtMillis: Long? = null
) {
    fun isActive(nowMillis: Long): Boolean = expiresAtMillis == null || nowMillis < expiresAtMillis
}

data class EvidenceSnapshot(
    val scanId: String,
    val inputKind: String,
    val channel: String,
    val primaryUrl: String? = null,
    val finalUrl: String? = null,
    val formActionUrl: String? = null,
    val formActionHost: String? = null,
    val redirectChain: List<String> = emptyList(),
    val senderDomain: String? = null,
    val claimedBrands: Set<String> = emptySet(),
    val signals: List<EvidenceSignal> = emptyList(),
    val providerStates: Map<ProviderId, ProviderState> = emptyMap(),
    val registryVersion: String = "local",
    val corpusVersion: String = "local",
    val completeness: EvidenceCompleteness = EvidenceCompleteness.FULL
)

data class EvidenceConflict(
    val type: String,
    val targetKey: String,
    val leftSignalId: String,
    val rightSignalId: String,
    val resolution: String
)

data class GateResult(
    val action: GateAction,
    val finality: GateFinality,
    val reasonCodes: List<String>,
    val decisiveSignalIds: List<String>,
    val supportingSignalIds: List<String> = emptyList(),
    val conflicts: List<EvidenceConflict> = emptyList(),
    val asyncExpected: Boolean = false,
    val unknownReason: String? = null,
    val revision: Int = 1
) {
    val userLabel: String = action.userLabel
}
