package ro.sigurscan.app

import kotlinx.coroutines.CancellationException

interface AudioSemanticReviewer {
    suspend fun review(
        redactedTranscript: String,
        localEvidence: AudioEvidenceResult?
    ): AudioSemanticReviewOutcome
}

data class AudioSemanticReviewOutcome(
    val response: AudioSemanticReviewResponse?,
    val status: VerificationPillarStatus,
    val reasonCode: String? = null
) {
    val reasonCodes: List<String>
        get() = (
            response?.semanticReview?.reasonCodes.orEmpty() +
                response?.reasonCodes.orEmpty() +
                listOfNotNull(reasonCode)
            )
            .map { it.trim() }
            .filter { it.isNotBlank() }
            .distinct()

    fun asVerificationPillar(): VerificationPillarDisplay = VerificationPillarDisplay(
        id = "semantic_review",
        status = status,
        required = true,
        details = when (status) {
            VerificationPillarStatus.OK -> "Analiza semantică a răspuns."
            VerificationPillarStatus.ERROR -> "Analiza semantică nu a fost disponibilă; verdictul local a fost păstrat."
            VerificationPillarStatus.SKIPPED -> "Analiza semantică nu a fost necesară sau nu a putut porni."
            else -> "Stare analiză semantică: ${status.name.lowercase()}."
        }
    )
}

class BackendAudioSemanticReviewer(
    private val api: SigurScanApi,
    private val channel: String
) : AudioSemanticReviewer {
    override suspend fun review(
        redactedTranscript: String,
        localEvidence: AudioEvidenceResult?
    ): AudioSemanticReviewOutcome {
        if (redactedTranscript.isBlank()) {
            return AudioSemanticReviewOutcome(
                response = null,
                status = VerificationPillarStatus.SKIPPED,
                reasonCode = "semantic:audio_empty_transcript"
            )
        }
        return try {
            val response = api.reviewAudioTranscript(
                AudioSemanticReviewRequest(
                    transcriptRedacted = redactedTranscript,
                    channel = channel,
                    localVerdict = localEvidence?.verdict?.name ?: AudioEvidenceVerdict.UNVERIFIED.name,
                    localReasonCodes = localEvidence?.reasonCodes.orEmpty(),
                    claimedIdentity = localEvidence?.claimedIdentity,
                    arcFamily = localEvidence?.arcFamily
                )
            )
            val responseReasons = (
                response.semanticReview?.reasonCodes.orEmpty() + response.reasonCodes
                ).map { it.trim() }.filter { it.isNotBlank() }
            val responseComplete = response.status.equals("done", ignoreCase = true) &&
                response.semanticReview != null
            val status = if (responseComplete) {
                VerificationPillarStatus.OK
            } else {
                VerificationPillarStatus.ERROR
            }
            AudioSemanticReviewOutcome(
                response = response,
                status = status,
                reasonCode = responseReasons.firstOrNull { it.startsWith("semantic:mistral_") }
                    ?: responseReasons.firstOrNull()
                    ?: if (response.status.equals("done", ignoreCase = true)) {
                        "semantic:invalid_response"
                    } else {
                        "semantic:provider_fallback"
                    }
            )
        } catch (cancelled: CancellationException) {
            throw cancelled
        } catch (_: Exception) {
            AudioSemanticReviewOutcome(
                response = null,
                status = VerificationPillarStatus.ERROR,
                reasonCode = "semantic:backend_unavailable"
            )
        }
    }
}

object NoopAudioSemanticReviewer : AudioSemanticReviewer {
    override suspend fun review(
        redactedTranscript: String,
        localEvidence: AudioEvidenceResult?
    ): AudioSemanticReviewOutcome = AudioSemanticReviewOutcome(
        response = null,
        status = VerificationPillarStatus.SKIPPED,
        reasonCode = "semantic:not_requested"
    )
}

object AudioSemanticReviewFusion {
    private fun rank(verdict: AudioEvidenceVerdict): Int = when (verdict) {
        AudioEvidenceVerdict.UNVERIFIED -> 0
        AudioEvidenceVerdict.SUSPECT -> 1
        AudioEvidenceVerdict.DANGEROUS -> 2
    }

    private fun verdictForRiskClass(value: String?): AudioEvidenceVerdict? {
        return when (value?.trim()?.lowercase()) {
            "high" -> AudioEvidenceVerdict.DANGEROUS
            "medium" -> AudioEvidenceVerdict.SUSPECT
            else -> null
        }
    }

    fun fuse(
        local: AudioEvidenceResult?,
        review: AudioSemanticReviewResponse?
    ): AudioEvidenceResult {
        val base = local ?: AudioEvidenceEngine.evaluate(AudioEvidenceInput())
        val semantic = review?.semanticReview ?: return base
        val semanticVerdict = verdictForRiskClass(semantic.riskClass) ?: return base
        if (rank(semanticVerdict) <= rank(base.verdict)) return base

        val reasonCodes = (
            base.reasonCodes +
                semantic.reasonCodes +
                review.reasonCodes +
                "semantic:mistral_escalation"
            )
            .map { it.trim() }
            .filter { it.isNotBlank() }
            .distinct()

        return base.copy(
            verdict = semanticVerdict,
            reasonCodes = reasonCodes,
            sttOnly = false,
            processing = "on_device_plus_mistral_semantic",
            transcriptRedacted = true,
            arcFamily = semantic.matchedFamily ?: base.arcFamily,
            campaignMatch = semantic.matchedFamily ?: base.campaignMatch
        )
    }
}
