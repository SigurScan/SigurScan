package ro.sigurscan.app

import java.util.Locale

internal fun backendGateResult(response: ScanResponse): GateResult {
    if (response.isFinal != true) {
        return backendScanInProgressGateResult()
    }

    val gatePayload = response.evidence
        ?.get("verdict_gate")
        .asStringKeyMap()
    val backendLabel = (gatePayload?.get("label")?.toString() ?: response.userRiskLabel)
        ?.trim()
        ?.uppercase(Locale.ROOT)
    val exactReasonCodes = gatePayload
        ?.get("reason_codes")
        .asStringList()
    val action = when (backendLabel) {
        "SAFE" -> GateAction.CONTINUE_WITH_CAUTION
        "SUSPECT" -> GateAction.VERIFY_OFFICIAL
        "DANGEROUS" -> GateAction.DO_NOT_CONTINUE
        "UNVERIFIED" -> GateAction.UNVERIFIED
        else -> GateAction.INSUFFICIENT_EVIDENCE
    }
    val fallbackReason = when {
        backendLabel == "UNVERIFIED" -> "BACKEND_UNVERIFIED"
        action == GateAction.INSUFFICIENT_EVIDENCE -> "BACKEND_FINAL_LABEL_MISSING"
        else -> "BACKEND_ORCHESTRATED_VERDICT"
    }
    val reasonCodes = exactReasonCodes.ifEmpty { listOf(fallbackReason) }
    val normalizedReasons = reasonCodes.map { it.trim().lowercase(Locale.ROOT) }.toSet()
    val unknownReason = when {
        action == GateAction.UNVERIFIED && "provider_error" in normalizedReasons -> "PROVIDERS_UNAVAILABLE"
        action == GateAction.UNVERIFIED -> "BACKEND_UNVERIFIED"
        action == GateAction.INSUFFICIENT_EVIDENCE -> "BACKEND_FINAL_LABEL_MISSING"
        else -> null
    }
    return GateResult(
        action = action,
        finality = GateFinality.FINAL,
        reasonCodes = reasonCodes,
        decisiveSignalIds = emptyList(),
        unknownReason = unknownReason
    )
}

internal fun backendGateResult(response: OrchestratedScanResponse): GateResult {
    return response.result?.let(::backendGateResult) ?: backendScanInProgressGateResult()
}

internal fun backendScanInProgressGateResult(): GateResult = GateResult(
    action = GateAction.INSUFFICIENT_EVIDENCE,
    finality = GateFinality.PROVISIONAL,
    reasonCodes = listOf("PROVIDER_REVIEW_REQUIRED"),
    decisiveSignalIds = emptyList(),
    asyncExpected = true,
    unknownReason = "BACKEND_SCAN_IN_PROGRESS"
)

private fun Any?.asStringKeyMap(): Map<String, Any?>? {
    val raw = this as? Map<*, *> ?: return null
    return raw.entries.associate { (key, value) -> key.toString() to value }
}

private fun Any?.asStringList(): List<String> = when (this) {
    is Iterable<*> -> mapNotNull { it?.toString()?.trim()?.takeIf(String::isNotBlank) }
    is Array<*> -> mapNotNull { it?.toString()?.trim()?.takeIf(String::isNotBlank) }
    else -> emptyList()
}
