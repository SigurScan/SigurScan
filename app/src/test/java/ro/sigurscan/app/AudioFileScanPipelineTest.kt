package ro.sigurscan.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class AudioFileScanPipelineTest {
    @Test
    fun sharedAudioPcmFeedsWhisperAndLocalEvidenceWithoutRetainingRawAudio() {
        val pipeline = AudioFileScanPipeline(
            asrEngine = WhisperCppAsrEngine(
                nativeRuntime = FakeWhisperRuntime(
                    transcript = "BNR spune ca s-a facut un credit pe numele tau si trebuie sa muti banii in RO49AAAA1B31007593840000. Codul este 123456."
                )
            )
        )

        val result = pipeline.scan(
            decodedAudio = DecodedAudioFile(
                pcm16Mono = ShortArray(16_000),
                sampleRateHz = 16_000
            ),
            modelPath = "/local/ggml-model.bin"
        )

        assertTrue(result.success)
        assertEquals("import_audio_file", result.inputKind)
        assertEquals("audio_share", result.channel)
        assertEquals(AudioEvidenceVerdict.DANGEROUS, result.evidence?.verdict)
        assertEquals(0, result.rawAudioBytesRetained)
        assertFalse(result.transcriptForTelemetry.contains("BNR"))
        assertTrue(result.redactedTranscriptForSemanticReview.contains("[iban]"))
        assertTrue(result.redactedTranscriptForSemanticReview.contains("[cod]"))
        assertFalse(result.redactedTranscriptForSemanticReview.contains("RO49AAAA1B31007593840000"))
        assertFalse(result.redactedTranscriptForSemanticReview.contains("123456"))
    }

    @Test
    fun sharedAudioPipelineFailsClosedWhenWhisperCannotTranscribe() {
        val pipeline = AudioFileScanPipeline(
            asrEngine = WhisperCppAsrEngine(
                nativeRuntime = FakeWhisperRuntime(available = false)
            )
        )

        val result = pipeline.scan(
            decodedAudio = DecodedAudioFile(
                pcm16Mono = ShortArray(16_000),
                sampleRateHz = 16_000
            ),
            modelPath = "/local/ggml-model.bin"
        )

        assertFalse(result.success)
        assertEquals("whisper_native_unavailable", result.reasonCode)
        assertEquals(AudioEvidenceVerdict.UNVERIFIED, result.evidence?.verdict)
        assertEquals(0, result.rawAudioBytesRetained)

        val assessment = result.toOfflineAssessment("voice-note.m4a")
        assertEquals("Neverificat", assessment.family)
        assertEquals("unknown", assessment.riskLevel)
        assertEquals("Neverificat", assessment.reputationVerdict)
        assertEquals(0, assessment.riskScore)
        assertEquals(GateAction.UNVERIFIED, assessment.gateResult?.action)
        assertEquals(GateFinality.FINAL, assessment.gateResult?.finality)
        assertTrue(assessment.gateResult?.reasonCodes?.contains("whisper_native_unavailable") == true)
    }

    @Test
    fun semanticProviderFailureIsVisibleWithoutDowngradingLocalEvidence() {
        val result = AudioFileScanResult(
            success = true,
            evidence = AudioTranscriptEvidence.analyze(
                "Sunt de la banca si trebuie sa imi dai codul OTP primit prin SMS"
            ),
            reasonCode = null,
            transcriptForTelemetry = "[redactat]",
            redactedTranscriptForSemanticReview = "Sunt de la banca si trebuie sa imi dai [cod] primit prin SMS"
        )
        val outcome = AudioSemanticReviewOutcome(
            response = null,
            status = VerificationPillarStatus.ERROR,
            reasonCode = "semantic:backend_unavailable"
        )

        val assessment = result.toOfflineAssessment("voice-note.m4a", outcome)

        assertEquals(GateAction.DO_NOT_CONTINUE, assessment.gateResult?.action)
        assertTrue(assessment.gateResult?.reasonCodes?.contains("semantic:backend_unavailable") == true)
        assertEquals(VerificationPillarStatus.ERROR, assessment.verificationPillars.single().status)
    }

    private class FakeWhisperRuntime(
        override val available: Boolean = true,
        private val transcript: String = "salut"
    ) : WhisperCppNativeRuntime {
        override fun transcribe(request: LocalAsrRequest): String = transcript
    }
}
