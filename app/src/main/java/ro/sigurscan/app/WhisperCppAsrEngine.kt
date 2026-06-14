package ro.sigurscan.app

data class LocalAsrRequest(
    val pcm16Mono: ShortArray,
    val sampleRateHz: Int,
    val language: String
)

data class LocalAsrResult(
    val success: Boolean,
    val engine: String,
    val transcript: String,
    val reasonCode: String?,
    val evidence: AudioEvidenceResult?,
    val rawAudioBytesRetained: Int = 0
)

interface WhisperCppNativeRuntime {
    val available: Boolean

    fun transcribe(request: LocalAsrRequest): String
}

class WhisperCppAsrEngine(
    private val nativeRuntime: WhisperCppNativeRuntime = WhisperCppNativeBridge
) {
    fun transcribe(request: LocalAsrRequest): LocalAsrResult {
        if (!isSupported(request)) {
            return failure("unsupported_audio_format")
        }
        if (!nativeRuntime.available) {
            return failure("whisper_native_unavailable")
        }

        val transcript = nativeRuntime.transcribe(request).trim()
        if (transcript.isEmpty()) {
            return failure("empty_transcript")
        }
        val evidence = AudioTranscriptEvidence.analyze(transcript)
        return LocalAsrResult(
            success = true,
            engine = ENGINE_NAME,
            transcript = transcript,
            reasonCode = null,
            evidence = evidence
        )
    }

    private fun isSupported(request: LocalAsrRequest): Boolean {
        return request.sampleRateHz == REQUIRED_SAMPLE_RATE_HZ &&
            request.pcm16Mono.isNotEmpty() &&
            request.language.trim().lowercase() in SUPPORTED_LANGUAGES
    }

    private fun failure(reasonCode: String): LocalAsrResult {
        return LocalAsrResult(
            success = false,
            engine = ENGINE_NAME,
            transcript = "",
            reasonCode = reasonCode,
            evidence = null
        )
    }

    companion object {
        const val ENGINE_NAME = "whisper.cpp"
        const val REQUIRED_SAMPLE_RATE_HZ = 16_000
        private val SUPPORTED_LANGUAGES = setOf("ro", "ro-ro")
    }
}

object WhisperCppNativeBridge : WhisperCppNativeRuntime {
    override val available: Boolean by lazy {
        runCatching {
            System.loadLibrary("sigurscan_whisper")
            nativeIsReady()
        }.getOrDefault(false)
    }

    override fun transcribe(request: LocalAsrRequest): String {
        check(available) { "Whisper native runtime is not available." }
        return nativeTranscribe(
            request.pcm16Mono,
            request.sampleRateHz,
            request.language.trim().lowercase()
        )
    }

    private external fun nativeIsReady(): Boolean

    private external fun nativeTranscribe(
        pcm16Mono: ShortArray,
        sampleRateHz: Int,
        language: String
    ): String
}
