package ro.sigurscan.app

class EvidenceGate(private val nowMillis: () -> Long = { System.currentTimeMillis() }) {
    fun evaluate(snapshot: EvidenceSnapshot): GateResult {
        val active = snapshot.signals
            .filter { it.isActive(nowMillis()) }
            .sortedWith(
                compareByDescending<EvidenceSignal> { actionRank(it.maxSoloAction) }
                    .thenByDescending { it.reliability }
                    .thenBy { it.code.name }
                    .thenBy { it.targetKey }
                    .thenBy { it.id }
        )
        val context = EvalContext(snapshot, active, detectConflicts(snapshot, active))

        providerReviewRequired(context)?.let { return it }

        return dangerous(context)
            ?: noReply(context)
            ?: noEnterData(context)
            ?: continueWithCaution(context)
            ?: verifyOfficial(context)
            ?: insufficientEvidence(context)
    }

    private fun dangerous(ctx: EvalContext): GateResult? = when {
        ctx.hasAny(
            EvidenceCode.WEBRISK_MATCH_MALWARE,
            EvidenceCode.WEBRISK_MATCH_SOCIAL_ENGINEERING,
            EvidenceCode.WEBRISK_MATCH_UNWANTED_SOFTWARE,
            EvidenceCode.WEBRISK_MATCH_SOCIAL_ENGINEERING_EXT
        ) -> final(
            GateAction.DO_NOT_CONTINUE,
            "HIGH_CONFIDENCE_REPUTATION",
            ctx.firstIds(
                EvidenceCode.WEBRISK_MATCH_MALWARE,
                EvidenceCode.WEBRISK_MATCH_SOCIAL_ENGINEERING,
                EvidenceCode.WEBRISK_MATCH_UNWANTED_SOFTWARE,
                EvidenceCode.WEBRISK_MATCH_SOCIAL_ENGINEERING_EXT
            ),
            ctx
        )

        ctx.hasAny(EvidenceCode.URLSCAN_VERDICT_PHISHING, EvidenceCode.URLSCAN_VERDICT_MALWARE) -> final(
            GateAction.DO_NOT_CONTINUE,
            "SANDBOX_VERDICT",
            ctx.firstIds(EvidenceCode.URLSCAN_VERDICT_PHISHING, EvidenceCode.URLSCAN_VERDICT_MALWARE),
            ctx
        )

        ctx.hasAny(EvidenceCode.APK_DOWNLOAD_UNOFFICIAL, EvidenceCode.REMOTE_ACCESS_DOWNLOAD_UNOFFICIAL) -> final(
            GateAction.DO_NOT_CONTINUE,
            "REMOTE_ACCESS_OR_APK",
            ctx.firstIds(EvidenceCode.APK_DOWNLOAD_UNOFFICIAL, EvidenceCode.REMOTE_ACCESS_DOWNLOAD_UNOFFICIAL),
            ctx
        )

        ctx.has(EvidenceCode.PHISHING_DATABASE_LISTED) -> final(
            GateAction.DO_NOT_CONTINUE,
            "PHISHING_DATABASE_LISTED",
            ctx.firstIds(EvidenceCode.PHISHING_DATABASE_LISTED),
            ctx
        )

        ctx.has(EvidenceCode.SENSITIVE_FORM_UNOFFICIAL) &&
            ctx.hasAny(
                EvidenceCode.BRAND_IMPERSONATION,
                EvidenceCode.OFFICIAL_DOMAIN_MISMATCH,
                EvidenceCode.COURIER_UNOFFICIAL_DOMAIN,
                EvidenceCode.PARCEL_TAX,
                EvidenceCode.TAX_NOTICE,
                EvidenceCode.ACCOUNT_SUSPEND
            ) -> final(
            GateAction.DO_NOT_CONTINUE,
            "SENSITIVE_FORM_ON_UNOFFICIAL_BRAND_DOMAIN",
            ctx.firstIds(
                EvidenceCode.SENSITIVE_FORM_UNOFFICIAL,
                EvidenceCode.BRAND_IMPERSONATION,
                EvidenceCode.OFFICIAL_DOMAIN_MISMATCH,
                EvidenceCode.COURIER_UNOFFICIAL_DOMAIN,
                EvidenceCode.PARCEL_TAX,
                EvidenceCode.TAX_NOTICE,
                EvidenceCode.ACCOUNT_SUSPEND
            ),
            ctx
        )

        ctx.has(EvidenceCode.COURIER_UNOFFICIAL_DOMAIN) &&
            ctx.hasAny(EvidenceCode.CARD_REQUEST, EvidenceCode.CVV_REQUEST, EvidenceCode.OTP_REQUEST) -> final(
            GateAction.DO_NOT_CONTINUE,
            "COURIER_UNOFFICIAL_SENSITIVE_REQUEST",
            ctx.firstIds(
                EvidenceCode.COURIER_UNOFFICIAL_DOMAIN,
                EvidenceCode.CARD_REQUEST,
                EvidenceCode.CVV_REQUEST,
                EvidenceCode.OTP_REQUEST
            ),
            ctx
        )

        ctx.has(EvidenceCode.HIDDEN_LINK_OFFICIAL_TO_UNOFFICIAL) &&
            ctx.hasAny(
                EvidenceCode.BRAND_IMPERSONATION,
                EvidenceCode.CARD_REQUEST,
                EvidenceCode.CVV_REQUEST,
                EvidenceCode.OTP_REQUEST,
                EvidenceCode.PASSWORD_REQUEST
            ) -> final(
            GateAction.DO_NOT_CONTINUE,
            "DISGUISED_LINK_IMPERSONATION",
            ctx.firstIds(
                EvidenceCode.HIDDEN_LINK_OFFICIAL_TO_UNOFFICIAL,
                EvidenceCode.BRAND_IMPERSONATION,
                EvidenceCode.CARD_REQUEST,
                EvidenceCode.CVV_REQUEST,
                EvidenceCode.OTP_REQUEST,
                EvidenceCode.PASSWORD_REQUEST
            ),
            ctx
        )

        ctx.has(EvidenceCode.BRAND_IMPERSONATION) &&
            ctx.has(EvidenceCode.OFFICIAL_DOMAIN_MISMATCH) &&
            ctx.hasAny(EvidenceCode.CARD_REQUEST, EvidenceCode.CVV_REQUEST) -> final(
            GateAction.DO_NOT_CONTINUE,
            "BRAND_IMPERSONATION_UNOFFICIAL_CARD_REQUEST",
            ctx.firstIds(
                EvidenceCode.BRAND_IMPERSONATION,
                EvidenceCode.OFFICIAL_DOMAIN_MISMATCH,
                EvidenceCode.CARD_REQUEST,
                EvidenceCode.CVV_REQUEST
            ),
            ctx
        )

        ctx.hasAny(EvidenceCode.TYPOSQUAT_LOOKALIKE, EvidenceCode.HOMOGLYPH_DOMAIN, EvidenceCode.PUNYCODE_HOST) &&
            ctx.hasAny(
                EvidenceCode.SENSITIVE_FORM_UNOFFICIAL,
                EvidenceCode.CARD_REQUEST,
                EvidenceCode.CVV_REQUEST,
                EvidenceCode.OTP_REQUEST,
                EvidenceCode.PASSWORD_REQUEST,
                EvidenceCode.CNP_IBAN_REQUEST
            ) -> final(
            GateAction.DO_NOT_CONTINUE,
            "LOOKALIKE_DOMAIN_SENSITIVE_REQUEST",
            ctx.firstIds(
                EvidenceCode.TYPOSQUAT_LOOKALIKE,
                EvidenceCode.HOMOGLYPH_DOMAIN,
                EvidenceCode.PUNYCODE_HOST,
                EvidenceCode.SENSITIVE_FORM_UNOFFICIAL,
                EvidenceCode.CARD_REQUEST,
                EvidenceCode.CVV_REQUEST,
                EvidenceCode.OTP_REQUEST,
                EvidenceCode.PASSWORD_REQUEST,
                EvidenceCode.CNP_IBAN_REQUEST
            ),
            ctx
        )

        else -> null
    }

    private fun noReply(ctx: EvalContext): GateResult? = when {
        ctx.hasAny(
            EvidenceCode.FAMILY_NEW_PHONE_MONEY,
            EvidenceCode.FAMILY_EMERGENCY_MONEY,
            EvidenceCode.ACCIDENT_NEPHEW_MONEY,
            EvidenceCode.WHATSAPP_CODE_REQUEST,
            EvidenceCode.WHATSAPP_DEVICE_LINKING_REQUEST,
            EvidenceCode.BNR_SAFE_ACCOUNT,
            EvidenceCode.FRAUDULENT_CREDIT_AUTHORITY_CHAIN
        ) -> final(
            GateAction.NO_REPLY,
            "TEXT_ONLY_SOCIAL_SCENARIO",
            ctx.firstIds(
                EvidenceCode.FAMILY_NEW_PHONE_MONEY,
                EvidenceCode.FAMILY_EMERGENCY_MONEY,
                EvidenceCode.ACCIDENT_NEPHEW_MONEY,
                EvidenceCode.WHATSAPP_CODE_REQUEST,
                EvidenceCode.WHATSAPP_DEVICE_LINKING_REQUEST,
                EvidenceCode.BNR_SAFE_ACCOUNT,
                EvidenceCode.FRAUDULENT_CREDIT_AUTHORITY_CHAIN
            ),
            ctx
        )

        ctx.has(EvidenceCode.REPLY_WITH_CODE_REQUEST) &&
            ctx.hasAny(EvidenceCode.OTP_REQUEST, EvidenceCode.PASSWORD_REQUEST, EvidenceCode.CARD_REQUEST, EvidenceCode.CNP_IBAN_REQUEST) -> final(
            GateAction.NO_REPLY,
            "DIRECT_REPLY_SECRET_REQUEST",
            ctx.firstIds(
                EvidenceCode.REPLY_WITH_CODE_REQUEST,
                EvidenceCode.OTP_REQUEST,
                EvidenceCode.PASSWORD_REQUEST,
                EvidenceCode.CARD_REQUEST,
                EvidenceCode.CNP_IBAN_REQUEST
            ),
            ctx
        )

        ctx.has(EvidenceCode.MONEY_REQUEST) && !ctx.hasAny(EvidenceCode.SENSITIVE_FORM_UNOFFICIAL, EvidenceCode.CARD_REQUEST) &&
            ctx.targetUrl().isNullOrBlank() -> final(
            GateAction.NO_REPLY,
            "TEXT_ONLY_MONEY_REQUEST",
            ctx.firstIds(EvidenceCode.MONEY_REQUEST),
            ctx
        )

        else -> null
    }

    private fun noEnterData(ctx: EvalContext): GateResult? = when {
        ctx.has(EvidenceCode.SENSITIVE_FORM_UNOFFICIAL) -> final(
            GateAction.NO_ENTER_DATA,
            "SENSITIVE_FORM_UNOFFICIAL",
            ctx.firstIds(EvidenceCode.SENSITIVE_FORM_UNOFFICIAL),
            ctx
        )

        ctx.has(EvidenceCode.MARKETPLACE_RECEIVE_MONEY) &&
            ctx.hasAny(EvidenceCode.CARD_REQUEST, EvidenceCode.CVV_REQUEST, EvidenceCode.OTP_REQUEST) -> final(
            GateAction.NO_ENTER_DATA,
            "MARKETPLACE_RECEIVE_MONEY_SENSITIVE_REQUEST",
            ctx.firstIds(
                EvidenceCode.MARKETPLACE_RECEIVE_MONEY,
                EvidenceCode.CARD_REQUEST,
                EvidenceCode.CVV_REQUEST,
                EvidenceCode.OTP_REQUEST
            ),
            ctx
        )

        ctx.hasAny(
            EvidenceCode.CARD_REQUEST,
            EvidenceCode.CVV_REQUEST,
            EvidenceCode.OTP_REQUEST,
            EvidenceCode.PASSWORD_REQUEST,
            EvidenceCode.CNP_IBAN_REQUEST,
            EvidenceCode.PERSONAL_DATA_REQUEST,
            EvidenceCode.PAYMENT_REQUEST
        ) && !ctx.hasAny(EvidenceCode.OFFICIAL_DOMAIN_EXACT, EvidenceCode.DELEGATED_DOMAIN_EXACT) -> final(
            GateAction.NO_ENTER_DATA,
            "DIRECT_SENSITIVE_REQUEST",
            ctx.firstIds(
                EvidenceCode.CARD_REQUEST,
                EvidenceCode.CVV_REQUEST,
                EvidenceCode.OTP_REQUEST,
                EvidenceCode.PASSWORD_REQUEST,
                EvidenceCode.CNP_IBAN_REQUEST,
                EvidenceCode.PERSONAL_DATA_REQUEST,
                EvidenceCode.PAYMENT_REQUEST
            ),
            ctx
        )

        ctx.hasAny(EvidenceCode.HOMOGLYPH_DOMAIN, EvidenceCode.DOMAIN_AGE_VERY_RECENT) &&
            !ctx.hasAny(EvidenceCode.OFFICIAL_DOMAIN_EXACT, EvidenceCode.DELEGATED_DOMAIN_EXACT) -> final(
            GateAction.NO_ENTER_DATA,
            "UNOFFICIAL_HIGH_RISK_INFRASTRUCTURE",
            ctx.firstIds(
                EvidenceCode.HOMOGLYPH_DOMAIN,
                EvidenceCode.DOMAIN_AGE_VERY_RECENT
            ),
            ctx
        )

        ctx.has(EvidenceCode.HIDDEN_LINK_OFFICIAL_TO_UNOFFICIAL) -> final(
            GateAction.NO_ENTER_DATA,
            "DISGUISED_LINK",
            ctx.firstIds(EvidenceCode.HIDDEN_LINK_OFFICIAL_TO_UNOFFICIAL),
            ctx
        )

        ctx.hasAny(
            EvidenceCode.TYPOSQUAT_LOOKALIKE,
            EvidenceCode.HOMOGLYPH_DOMAIN,
            EvidenceCode.PUNYCODE_HOST,
            EvidenceCode.DOMAIN_AGE_VERY_RECENT,
            EvidenceCode.DGA_ENTROPY_HIGH,
            EvidenceCode.URL_TRANSPORT_RISK
        ) && ctx.hasAny(
            EvidenceCode.CARD_REQUEST,
            EvidenceCode.CVV_REQUEST,
            EvidenceCode.OTP_REQUEST,
            EvidenceCode.PASSWORD_REQUEST,
            EvidenceCode.CNP_IBAN_REQUEST,
            EvidenceCode.PERSONAL_DATA_REQUEST,
            EvidenceCode.PAYMENT_REQUEST
        ) -> final(
            GateAction.NO_ENTER_DATA,
            "INFRASTRUCTURE_RISK_WITH_SENSITIVE_REQUEST",
            ctx.firstIds(
                EvidenceCode.TYPOSQUAT_LOOKALIKE,
                EvidenceCode.HOMOGLYPH_DOMAIN,
                EvidenceCode.PUNYCODE_HOST,
                EvidenceCode.DOMAIN_AGE_VERY_RECENT,
                EvidenceCode.DGA_ENTROPY_HIGH,
                EvidenceCode.URL_TRANSPORT_RISK,
                EvidenceCode.CARD_REQUEST,
                EvidenceCode.CVV_REQUEST,
                EvidenceCode.OTP_REQUEST,
                EvidenceCode.PASSWORD_REQUEST,
                EvidenceCode.CNP_IBAN_REQUEST,
                EvidenceCode.PERSONAL_DATA_REQUEST,
                EvidenceCode.PAYMENT_REQUEST
            ),
            ctx
        )

        else -> null
    }

    private fun verifyOfficial(ctx: EvalContext): GateResult? = when {
        ctx.requiresOfferConfirmationForSafe() &&
            !ctx.hasAny(EvidenceCode.OCR_LOW_CONFIDENCE, EvidenceCode.WEBMAIL_SHELL_ONLY, EvidenceCode.NO_TARGET) &&
            ctx.hasAny(EvidenceCode.OFFER_CLAIM_NOT_FOUND, EvidenceCode.OFFER_CLAIM_INCONCLUSIVE) -> result(
            GateAction.VERIFY_OFFICIAL,
            "CLAIM_NOT_CONFIRMED_ON_OFFICIAL_SOURCES",
            ctx.firstIds(
                EvidenceCode.OFFER_CLAIM_NOT_FOUND,
                EvidenceCode.OFFER_CLAIM_INCONCLUSIVE
            ),
            ctx
        )

        ctx.requiresOfferConfirmationForSafe() &&
            !ctx.hasAny(EvidenceCode.OCR_LOW_CONFIDENCE, EvidenceCode.WEBMAIL_SHELL_ONLY, EvidenceCode.NO_TARGET) &&
            !ctx.has(EvidenceCode.OFFER_CLAIM_CONFIRMED) &&
            !ctx.isAsyncPending() -> result(
            GateAction.VERIFY_OFFICIAL,
            "PROMOTIONAL_CLAIM_NEEDS_CONFIRMATION",
            ctx.firstIds(
                EvidenceCode.PROMO_TEXT,
                EvidenceCode.VOUCHER_TEXT,
                EvidenceCode.MARKETING_URGENCY,
                EvidenceCode.CTA_TEXT
            ),
            ctx
        )

        ctx.hasAny(
            EvidenceCode.UNRESOLVED_SHORTLINK,
            EvidenceCode.DOMAIN_AGE_SUSPICIOUS,
            EvidenceCode.DOMAIN_AGE_VERY_RECENT,
            EvidenceCode.TYPOSQUAT_LOOKALIKE,
            EvidenceCode.HOMOGLYPH_DOMAIN,
            EvidenceCode.PUNYCODE_HOST,
            EvidenceCode.DGA_ENTROPY_HIGH,
            EvidenceCode.URL_BEHAVIOUR_SUSPICIOUS,
            EvidenceCode.URL_TRANSPORT_RISK,
            EvidenceCode.MARKETPLACE_RECEIVE_MONEY,
            EvidenceCode.COURIER_UNOFFICIAL_DOMAIN,
            EvidenceCode.PARCEL_TAX,
            EvidenceCode.TAX_NOTICE,
            EvidenceCode.ACCOUNT_SUSPEND,
            EvidenceCode.OFFICIAL_DOMAIN_MISMATCH,
            EvidenceCode.BRAND_IMPERSONATION
        ) -> result(
            GateAction.VERIFY_OFFICIAL,
            "BRAND_OR_AUTHORITY_CLAIM_NEEDS_VERIFICATION",
            ctx.firstIds(
                EvidenceCode.UNRESOLVED_SHORTLINK,
                EvidenceCode.DOMAIN_AGE_SUSPICIOUS,
                EvidenceCode.DOMAIN_AGE_VERY_RECENT,
                EvidenceCode.TYPOSQUAT_LOOKALIKE,
                EvidenceCode.HOMOGLYPH_DOMAIN,
                EvidenceCode.PUNYCODE_HOST,
                EvidenceCode.DGA_ENTROPY_HIGH,
                EvidenceCode.URL_BEHAVIOUR_SUSPICIOUS,
                EvidenceCode.URL_TRANSPORT_RISK,
                EvidenceCode.MARKETPLACE_RECEIVE_MONEY,
                EvidenceCode.COURIER_UNOFFICIAL_DOMAIN,
                EvidenceCode.PARCEL_TAX,
                EvidenceCode.TAX_NOTICE,
                EvidenceCode.ACCOUNT_SUSPEND,
                EvidenceCode.OFFICIAL_DOMAIN_MISMATCH,
                EvidenceCode.BRAND_IMPERSONATION
            ),
            ctx
        )

        ctx.hasAny(
            EvidenceCode.HIDDEN_LINK_PRESENT,
            EvidenceCode.HTML_BUTTON_LINK,
            EvidenceCode.TRACKING_LINK,
            EvidenceCode.MARKETING_URGENCY,
            EvidenceCode.PROMO_TEXT,
            EvidenceCode.VOUCHER_TEXT,
            EvidenceCode.CTA_TEXT,
            EvidenceCode.DISPLAY_NAME_BRAND_ONLY,
            EvidenceCode.CORPUS_SIMILARITY,
            EvidenceCode.CORPUS_BRAND_WARNING,
            EvidenceCode.USER_REPORT_UNVERIFIED,
            EvidenceCode.RAG_EXPLANATION
        ) && ctx.hasWeakVerificationContext() &&
            !ctx.hasAny(EvidenceCode.OCR_LOW_CONFIDENCE, EvidenceCode.WEBMAIL_SHELL_ONLY, EvidenceCode.NO_TARGET) -> result(
            GateAction.VERIFY_OFFICIAL,
            "WEAK_OR_EXPLANATORY_EVIDENCE_ONLY",
            ctx.firstIds(
                EvidenceCode.HIDDEN_LINK_PRESENT,
                EvidenceCode.HTML_BUTTON_LINK,
                EvidenceCode.TRACKING_LINK,
                EvidenceCode.MARKETING_URGENCY,
                EvidenceCode.PROMO_TEXT,
                EvidenceCode.VOUCHER_TEXT,
                EvidenceCode.CTA_TEXT,
                EvidenceCode.DISPLAY_NAME_BRAND_ONLY,
                EvidenceCode.CORPUS_SIMILARITY,
                EvidenceCode.CORPUS_BRAND_WARNING,
                EvidenceCode.USER_REPORT_UNVERIFIED,
                EvidenceCode.RAG_EXPLANATION
            ),
            ctx
        )

        !ctx.snapshot.finalUrl.isNullOrBlank() &&
            ctx.snapshot.completeness != EvidenceCompleteness.LOCAL_ONLY &&
            !ctx.providersUnavailable() &&
            ctx.urlscanReviewed() &&
            ctx.has(EvidenceCode.NO_SENSITIVE_FORM) -> result(
            GateAction.VERIFY_OFFICIAL,
            "UNKNOWN_DESTINATION_REVIEW",
            ctx.firstIds(EvidenceCode.NO_SENSITIVE_FORM),
            ctx
        )

        else -> null
    }

    private fun continueWithCaution(ctx: EvalContext): GateResult? {
        val hasOfficialDestination = ctx.hasAny(
            EvidenceCode.OFFICIAL_DOMAIN_EXACT,
            EvidenceCode.DELEGATED_DOMAIN_EXACT,
            EvidenceCode.APPROVED_TRACKER_DOMAIN
        )
        if (!hasOfficialDestination) return null
        if (!ctx.has(EvidenceCode.NO_SENSITIVE_FORM)) return null
        if (ctx.targetUrl().isNullOrBlank()) return null
        if (!ctx.hasCompletedRequiredPillars()) return null
        if (ctx.requiresOfferConfirmationForSafe() && !ctx.has(EvidenceCode.OFFER_CLAIM_CONFIRMED)) return null
        if (ctx.snapshot.completeness == EvidenceCompleteness.LOCAL_ONLY) return null
        if (ctx.hasAny(
                EvidenceCode.SENSITIVE_FORM_UNOFFICIAL,
                EvidenceCode.HIDDEN_LINK_OFFICIAL_TO_UNOFFICIAL,
                EvidenceCode.OFFICIAL_DOMAIN_MISMATCH,
                EvidenceCode.BRAND_IMPERSONATION,
                EvidenceCode.WEBRISK_MATCH_MALWARE,
                EvidenceCode.WEBRISK_MATCH_SOCIAL_ENGINEERING,
                EvidenceCode.WEBRISK_MATCH_UNWANTED_SOFTWARE,
                EvidenceCode.WEBRISK_MATCH_SOCIAL_ENGINEERING_EXT,
                EvidenceCode.URLSCAN_VERDICT_PHISHING,
                EvidenceCode.URLSCAN_VERDICT_MALWARE,
                EvidenceCode.PHISHING_DATABASE_LISTED,
                EvidenceCode.HOMOGLYPH_DOMAIN,
                EvidenceCode.PUNYCODE_HOST,
                EvidenceCode.TYPOSQUAT_LOOKALIKE,
                EvidenceCode.DOMAIN_AGE_VERY_RECENT,
                EvidenceCode.DOMAIN_AGE_SUSPICIOUS
            )
        ) return null

        return result(
            GateAction.CONTINUE_WITH_CAUTION,
            if (ctx.has(EvidenceCode.OFFER_CLAIM_CONFIRMED)) {
                "OFFICIAL_DESTINATION_AND_CLAIM_CONFIRMED"
            } else {
                "OFFICIAL_DESTINATION_NO_SENSITIVE_COLLECTION"
            },
            ctx.firstIds(
                EvidenceCode.OFFICIAL_DOMAIN_EXACT,
                EvidenceCode.DELEGATED_DOMAIN_EXACT,
                EvidenceCode.APPROVED_TRACKER_DOMAIN,
                EvidenceCode.NO_SENSITIVE_FORM,
                EvidenceCode.OFFER_CLAIM_CONFIRMED
            ),
            ctx
        )
    }

    private fun providerReviewRequired(ctx: EvalContext): GateResult? {
        if (ctx.snapshot.completeness == EvidenceCompleteness.LOCAL_ONLY) {
            return providerReviewGateResult(ctx, "PILLARS_NOT_RUN")
        }
        if (
            ctx.targetUrl().isNullOrBlank() &&
            ctx.hasAny(EvidenceCode.WEBMAIL_SHELL_ONLY, EvidenceCode.OCR_LOW_CONFIDENCE, EvidenceCode.NO_TARGET)
        ) return null
        if (!ctx.needsProviderReviewBeforeVerdict()) return null

        val reason = when {
            ctx.isAsyncPending() -> "PROVIDERS_PENDING_FOR_TARGET"
            ctx.hasRequiredPillarFailure() || ctx.providersUnavailable() -> "PROVIDERS_UNAVAILABLE"
            ctx.targetNeedsFinalUrlResolution() -> "FINAL_URL_NOT_RESOLVED"
            ctx.targetUrl().isNullOrBlank() -> "PILLARS_NOT_RUN"
            else -> "PROVIDERS_NOT_RUN_FOR_TARGET"
        }

        return providerReviewGateResult(ctx, reason)
    }

    private fun providerReviewGateResult(ctx: EvalContext, reason: String): GateResult {
        val asyncExpected = ctx.isAsyncPending() || reason in setOf(
            "PROVIDERS_PENDING_FOR_TARGET",
            "PROVIDERS_NOT_RUN_FOR_TARGET",
            "FINAL_URL_NOT_RESOLVED"
        )
        return GateResult(
            action = GateAction.INSUFFICIENT_EVIDENCE,
            finality = if (asyncExpected) GateFinality.PROVISIONAL else GateFinality.FINAL,
            reasonCodes = listOf("PROVIDER_REVIEW_REQUIRED"),
            decisiveSignalIds = emptyList(),
            supportingSignalIds = ctx.active.map { it.id }.take(5),
            conflicts = ctx.conflicts,
            asyncExpected = asyncExpected,
            unknownReason = reason
        )
    }

    private fun insufficientEvidence(ctx: EvalContext): GateResult {
        val reason = when {
            ctx.has(EvidenceCode.WEBMAIL_SHELL_ONLY) -> "WEBMAIL_SHELL_ONLY"
            ctx.has(EvidenceCode.OCR_LOW_CONFIDENCE) -> "OCR_LOW_CONFIDENCE"
            ctx.has(EvidenceCode.UNRESOLVED_SHORTLINK) -> "UNRESOLVED_SHORTLINK"
            ctx.has(EvidenceCode.PROVIDERS_UNAVAILABLE) || ctx.providersUnavailable() -> "PROVIDERS_UNAVAILABLE"
            ctx.has(EvidenceCode.NO_TARGET) || ctx.targetUrl().isNullOrBlank() -> "NO_TARGET"
            else -> "NO_DECISIVE_SIGNAL"
        }
        return GateResult(
            action = GateAction.INSUFFICIENT_EVIDENCE,
            finality = if (ctx.isAsyncPending()) GateFinality.PROVISIONAL else GateFinality.FINAL,
            reasonCodes = listOf("INSUFFICIENT_EVIDENCE"),
            decisiveSignalIds = emptyList(),
            supportingSignalIds = ctx.active.map { it.id }.take(5),
            conflicts = ctx.conflicts,
            asyncExpected = ctx.isAsyncPending(),
            unknownReason = reason
        )
    }

    private fun final(
        action: GateAction,
        reason: String,
        decisiveIds: List<String>,
        ctx: EvalContext
    ): GateResult = GateResult(
        action = action,
        finality = GateFinality.FINAL,
        reasonCodes = listOf(reason),
        decisiveSignalIds = decisiveIds,
        supportingSignalIds = supportIds(ctx, decisiveIds),
        conflicts = ctx.conflicts,
        asyncExpected = false
    )

    private fun result(
        action: GateAction,
        reason: String,
        decisiveIds: List<String>,
        ctx: EvalContext
    ): GateResult = GateResult(
        action = action,
        finality = if (ctx.isAsyncPending()) GateFinality.PROVISIONAL else GateFinality.FINAL,
        reasonCodes = listOf(reason),
        decisiveSignalIds = decisiveIds,
        supportingSignalIds = supportIds(ctx, decisiveIds),
        conflicts = ctx.conflicts,
        asyncExpected = ctx.isAsyncPending()
    )

    private fun supportIds(ctx: EvalContext, decisiveIds: List<String>): List<String> {
        return ctx.active
            .asSequence()
            .filter { it.id !in decisiveIds }
            .filter { EvidenceGatePolicy.isDecisionEligible(it) }
            .map { it.id }
            .take(5)
            .toList()
    }

    private fun detectConflicts(
        snapshot: EvidenceSnapshot,
        active: List<EvidenceSignal>
    ): List<EvidenceConflict> {
        val conflicts = mutableListOf<EvidenceConflict>()
        val primary = snapshot.primaryUrl
        val final = snapshot.finalUrl
        if (!primary.isNullOrBlank() && !final.isNullOrBlank() && primary != final) {
            val positiveFinal = active.firstOrNull { signal ->
                signal.code in setOf(
                    EvidenceCode.WEBRISK_MATCH_MALWARE,
                    EvidenceCode.WEBRISK_MATCH_SOCIAL_ENGINEERING,
                    EvidenceCode.URLSCAN_VERDICT_PHISHING,
                    EvidenceCode.URLSCAN_VERDICT_MALWARE,
                    EvidenceCode.SENSITIVE_FORM_UNOFFICIAL,
                    EvidenceCode.HIDDEN_LINK_OFFICIAL_TO_UNOFFICIAL
                )
            }
            val benignPrimary = active.firstOrNull { it.code == EvidenceCode.OFFICIAL_DOMAIN_EXACT }
            if (positiveFinal != null && benignPrimary != null) {
                conflicts.add(
                    EvidenceConflict(
                        type = "TARGET_MISMATCH",
                        targetKey = positiveFinal.targetKey,
                        leftSignalId = benignPrimary.id,
                        rightSignalId = positiveFinal.id,
                        resolution = "Decide pe finalUrl/form host, nu pe primul hop."
                    )
                )
            }
        }
        return conflicts
    }

    private fun actionRank(action: GateAction): Int = when (action) {
        GateAction.DO_NOT_CONTINUE -> 6
        GateAction.NO_ENTER_DATA -> 5
        GateAction.NO_REPLY -> 4
        GateAction.VERIFY_OFFICIAL -> 3
        GateAction.UNVERIFIED -> 2
        GateAction.INSUFFICIENT_EVIDENCE -> 2
        GateAction.CONTINUE_WITH_CAUTION -> 1
    }

    private data class EvalContext(
        val snapshot: EvidenceSnapshot,
        val active: List<EvidenceSignal>,
        val conflicts: List<EvidenceConflict>
    ) {
        fun has(code: EvidenceCode): Boolean = active.any { it.code == code && EvidenceGatePolicy.isDecisionEligible(it) }
        fun hasAny(vararg codes: EvidenceCode): Boolean = codes.any(::has)
        fun firstIds(vararg codes: EvidenceCode): List<String> {
            val wanted = codes.toSet()
            return active
                .filter { it.code in wanted && EvidenceGatePolicy.isDecisionEligible(it) }
                .map { it.id }
                .take(5)
        }
        fun targetUrl(): String? = snapshot.formActionUrl ?: snapshot.finalUrl ?: snapshot.primaryUrl
        fun hasWeakVerificationContext(): Boolean {
            return !targetUrl().isNullOrBlank() ||
                snapshot.claimedBrands.isNotEmpty() ||
                !snapshot.senderDomain.isNullOrBlank() ||
                snapshot.providerStates.isNotEmpty()
        }
        fun isAsyncPending(): Boolean = snapshot.providerStates.values.any { it.status == ProviderStatus.PENDING }
        fun hasHardProviderEvidence(): Boolean = hasAny(
            EvidenceCode.WEBRISK_MATCH_MALWARE,
            EvidenceCode.WEBRISK_MATCH_SOCIAL_ENGINEERING,
            EvidenceCode.WEBRISK_MATCH_UNWANTED_SOFTWARE,
            EvidenceCode.WEBRISK_MATCH_SOCIAL_ENGINEERING_EXT,
            EvidenceCode.URLSCAN_VERDICT_PHISHING,
            EvidenceCode.URLSCAN_VERDICT_MALWARE,
            EvidenceCode.PHISHING_DATABASE_LISTED
        )
        fun needsProviderReviewBeforeVerdict(): Boolean {
            if (snapshot.completeness == EvidenceCompleteness.LOCAL_ONLY) return true
            if (isAsyncPending()) return true
            if (providersUnavailable()) return true
            return if (targetUrl().isNullOrBlank()) {
                !hasProviderOutcome()
            } else {
                !hasCompletedRequiredPillars()
            }
        }
        fun hasCompletedRequiredPillars(): Boolean {
            if (targetNeedsFinalUrlResolution()) return false
            return required.all { provider ->
                snapshot.providerStates[provider]?.status == ProviderStatus.OK
            }
        }
        fun targetNeedsFinalUrlResolution(): Boolean =
            !targetUrl().isNullOrBlank() &&
                snapshot.formActionUrl.isNullOrBlank() &&
                snapshot.finalUrl.isNullOrBlank()

        fun hasRequiredPillarFailure(): Boolean {
            return required.any { provider ->
                snapshot.providerStates[provider]?.status in setOf(
                    ProviderStatus.ERROR,
                    ProviderStatus.TIMEOUT,
                    ProviderStatus.RATE_LIMITED,
                    ProviderStatus.SKIPPED
                )
            }
        }
        private val required: Set<ProviderId> by lazy {
            buildSet {
                add(ProviderId.WEB_RISK)
                add(ProviderId.URLSCAN)
                if (requiresClaimVerification()) add(ProviderId.CLAIM_VERIFIER)
            }
        }
        private fun requiresClaimVerification(): Boolean {
            if (snapshot.claimedBrands.isNotEmpty()) return true
            return active.any { signal ->
                signal.code in setOf(
                    EvidenceCode.MARKETING_URGENCY,
                    EvidenceCode.PROMO_TEXT,
                    EvidenceCode.VOUCHER_TEXT,
                    EvidenceCode.CTA_TEXT,
                    EvidenceCode.PARCEL_TAX,
                    EvidenceCode.TAX_NOTICE,
                    EvidenceCode.ACCOUNT_SUSPEND,
                    EvidenceCode.MARKETPLACE_RECEIVE_MONEY,
                    EvidenceCode.COURIER_UNOFFICIAL_DOMAIN,
                    EvidenceCode.BRAND_IMPERSONATION,
                    EvidenceCode.OFFICIAL_DOMAIN_MISMATCH
                )
            }
        }
        fun requiresOfferConfirmationForSafe(): Boolean {
            return active.any { signal ->
                signal.code in setOf(
                    EvidenceCode.MARKETING_URGENCY,
                    EvidenceCode.PROMO_TEXT,
                    EvidenceCode.VOUCHER_TEXT,
                    EvidenceCode.CTA_TEXT,
                    EvidenceCode.OFFER_CLAIM_CONFIRMED,
                    EvidenceCode.OFFER_CLAIM_NOT_FOUND,
                    EvidenceCode.OFFER_CLAIM_INCONCLUSIVE
                )
            }
        }
        private fun hasProviderOutcome(): Boolean {
            val requiredProviders = if (targetUrl().isNullOrBlank()) {
                setOf(ProviderId.CLAIM_VERIFIER)
            } else {
                setOf(ProviderId.WEB_RISK, ProviderId.URLSCAN, ProviderId.PHISHING_DATABASE)
            }
            if (snapshot.providerStates.values.any { it.provider in requiredProviders && it.status == ProviderStatus.OK }) return true
            return active.any { signal ->
                when {
                    targetUrl().isNullOrBlank() -> signal.provider in requiredProviders
                    else -> signal.source in setOf(
                        EvidenceSource.GOOGLE_WEB_RISK,
                        EvidenceSource.URLSCAN,
                        EvidenceSource.PHISHING_DATABASE
                    )
                }
            }
        }
        fun urlscanReviewed(): Boolean {
            val status = snapshot.providerStates[ProviderId.URLSCAN]?.status ?: return false
            return status in setOf(ProviderStatus.OK, ProviderStatus.PENDING)
        }
        fun providersUnavailable(): Boolean {
            if (snapshot.providerStates.isEmpty()) return false
            return snapshot.providerStates.values.all { state ->
                state.status in setOf(
                    ProviderStatus.ERROR,
                    ProviderStatus.TIMEOUT,
                    ProviderStatus.RATE_LIMITED,
                    ProviderStatus.SKIPPED
                )
            }
        }
    }
}
