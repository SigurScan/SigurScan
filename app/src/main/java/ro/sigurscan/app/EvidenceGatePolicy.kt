package ro.sigurscan.app

// Gate policy lookup tables extracted from EvidenceGate.kt.

object EvidenceGatePolicy {
    fun maxSoloAction(code: EvidenceCode): GateAction = when (code) {
        EvidenceCode.WEBRISK_MATCH_MALWARE,
        EvidenceCode.WEBRISK_MATCH_SOCIAL_ENGINEERING,
        EvidenceCode.WEBRISK_MATCH_UNWANTED_SOFTWARE,
        EvidenceCode.WEBRISK_MATCH_SOCIAL_ENGINEERING_EXT,
        EvidenceCode.URLSCAN_VERDICT_PHISHING,
        EvidenceCode.URLSCAN_VERDICT_MALWARE,
        EvidenceCode.PHISHING_DATABASE_LISTED,
        EvidenceCode.APK_DOWNLOAD_UNOFFICIAL,
        EvidenceCode.REMOTE_ACCESS_DOWNLOAD_UNOFFICIAL -> GateAction.DO_NOT_CONTINUE

        EvidenceCode.SENSITIVE_FORM_UNOFFICIAL,
        EvidenceCode.CARD_REQUEST,
        EvidenceCode.CVV_REQUEST,
        EvidenceCode.OTP_REQUEST,
        EvidenceCode.PASSWORD_REQUEST,
        EvidenceCode.CNP_IBAN_REQUEST,
        EvidenceCode.PERSONAL_DATA_REQUEST,
        EvidenceCode.PAYMENT_REQUEST,
        EvidenceCode.HIDDEN_LINK_OFFICIAL_TO_UNOFFICIAL,
        EvidenceCode.MARKETPLACE_RECEIVE_MONEY,
        EvidenceCode.HOMOGLYPH_DOMAIN,
        EvidenceCode.DOMAIN_AGE_VERY_RECENT -> GateAction.NO_ENTER_DATA

        EvidenceCode.REPLY_WITH_CODE_REQUEST,
        EvidenceCode.MONEY_REQUEST,
        EvidenceCode.FAMILY_NEW_PHONE_MONEY,
        EvidenceCode.FAMILY_EMERGENCY_MONEY,
        EvidenceCode.ACCIDENT_NEPHEW_MONEY,
        EvidenceCode.WHATSAPP_CODE_REQUEST,
        EvidenceCode.WHATSAPP_DEVICE_LINKING_REQUEST,
        EvidenceCode.BNR_SAFE_ACCOUNT,
        EvidenceCode.FRAUDULENT_CREDIT_AUTHORITY_CHAIN -> GateAction.NO_REPLY

        EvidenceCode.OFFICIAL_DOMAIN_EXACT,
        EvidenceCode.DELEGATED_DOMAIN_EXACT,
        EvidenceCode.APPROVED_TRACKER_DOMAIN,
        EvidenceCode.REDIRECT_CHAIN_APPROVED,
        EvidenceCode.NO_SENSITIVE_FORM,
        EvidenceCode.TRACKING_ONLY_NO_PAYMENT,
        EvidenceCode.PROMO_CODE_REDEEM_IN_APP,
        EvidenceCode.LIST_UNSUBSCRIBE_PRESENT -> GateAction.CONTINUE_WITH_CAUTION

        EvidenceCode.WEBMAIL_SHELL_ONLY,
        EvidenceCode.OCR_LOW_CONFIDENCE,
        EvidenceCode.PROVIDERS_UNAVAILABLE,
        EvidenceCode.NO_TARGET -> GateAction.INSUFFICIENT_EVIDENCE

        EvidenceCode.WEBRISK_NO_MATCH,
        EvidenceCode.URLSCAN_NO_CLASSIFICATION,
        EvidenceCode.PHISHING_DATABASE_NOT_LISTED,
        EvidenceCode.OFFER_CLAIM_CONFIRMED,
        EvidenceCode.OFFER_CLAIM_NOT_FOUND,
        EvidenceCode.OFFER_CLAIM_INCONCLUSIVE,
        EvidenceCode.DOMAIN_AGE_SUSPICIOUS,
        EvidenceCode.TYPOSQUAT_LOOKALIKE,
        EvidenceCode.PUNYCODE_HOST,
        EvidenceCode.DGA_ENTROPY_HIGH,
        EvidenceCode.URL_BEHAVIOUR_SUSPICIOUS,
        EvidenceCode.URL_TRANSPORT_RISK,
        EvidenceCode.BRAND_IMPERSONATION,
        EvidenceCode.OFFICIAL_DOMAIN_MISMATCH,
        EvidenceCode.HIDDEN_LINK_PRESENT,
        EvidenceCode.HTML_BUTTON_LINK,
        EvidenceCode.TRACKING_LINK,
        EvidenceCode.UNRESOLVED_SHORTLINK,
        EvidenceCode.COURIER_UNOFFICIAL_DOMAIN,
        EvidenceCode.PARCEL_TAX,
        EvidenceCode.TAX_NOTICE,
        EvidenceCode.ACCOUNT_SUSPEND,
        EvidenceCode.MARKETING_URGENCY,
        EvidenceCode.PROMO_TEXT,
        EvidenceCode.VOUCHER_TEXT,
        EvidenceCode.CTA_TEXT,
        EvidenceCode.DISPLAY_NAME_BRAND_ONLY,
        EvidenceCode.CORPUS_SIMILARITY,
        EvidenceCode.CORPUS_BRAND_WARNING,
        EvidenceCode.USER_REPORT_UNVERIFIED,
        EvidenceCode.RAG_EXPLANATION -> GateAction.VERIFY_OFFICIAL
    }

    fun defaultReliability(code: EvidenceCode): Int = when (maxSoloAction(code)) {
        GateAction.DO_NOT_CONTINUE -> 100
        GateAction.NO_ENTER_DATA -> 80
        GateAction.NO_REPLY -> 75
        GateAction.VERIFY_OFFICIAL -> 45
        GateAction.UNVERIFIED -> 30
        GateAction.INSUFFICIENT_EVIDENCE -> 30
        GateAction.CONTINUE_WITH_CAUTION -> 20
    }

    fun isDecisionEligible(signal: EvidenceSignal): Boolean {
        if (signal.source == EvidenceSource.RAG || signal.code == EvidenceCode.RAG_EXPLANATION) return false
        if (signal.code == EvidenceCode.CORPUS_SIMILARITY) return false
        if (signal.code == EvidenceCode.USER_REPORT_UNVERIFIED) return false
        if (signal.code == EvidenceCode.WEBRISK_NO_MATCH) return false
        if (signal.code == EvidenceCode.URLSCAN_NO_CLASSIFICATION) return false
        if (signal.code == EvidenceCode.PHISHING_DATABASE_NOT_LISTED) return false
        return true
    }
}
