package ro.sigurscan.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class WhisperCppAsrEngineTest {
    @Test
    fun unavailableNativeRuntimeDoesNotPretendToTranscribe() {
        val engine = WhisperCppAsrEngine(nativeRuntime = FakeWhisperRuntime(available = false))

        val result = engine.transcribe(
            LocalAsrRequest(
                pcm16Mono = ShortArray(16_000),
                sampleRateHz = 16_000,
                language = "ro"
            )
        )

        assertFalse(result.success)
        assertEquals("whisper_native_unavailable", result.reasonCode)
        assertEquals("", result.transcript)
    }

    @Test
    fun whisperRequiresSixteenKilohertzMonoRomanianInput() {
        val engine = WhisperCppAsrEngine(nativeRuntime = FakeWhisperRuntime())

        val result = engine.transcribe(
            LocalAsrRequest(
                pcm16Mono = ShortArray(8_000),
                sampleRateHz = 8_000,
                language = "en"
            )
        )

        assertFalse(result.success)
        assertEquals("unsupported_audio_format", result.reasonCode)
    }

    @Test
    fun transcriptFromWhisperFeedsLocalAudioEvidenceWithoutRawAudio() {
        val engine = WhisperCppAsrEngine(
            nativeRuntime = FakeWhisperRuntime(
                transcript = "BNR cere sa muti banii intr-un cont sigur acum"
            )
        )

        val result = engine.transcribe(
            LocalAsrRequest(
                pcm16Mono = ShortArray(16_000),
                sampleRateHz = 16_000,
                language = "ro"
            )
        )

        assertTrue(result.success)
        assertEquals("whisper.cpp", result.engine)
        assertEquals(AudioEvidenceVerdict.DANGEROUS, result.evidence?.verdict)
        assertEquals(0, result.rawAudioBytesRetained)
    }

    private class FakeWhisperRuntime(
        override val available: Boolean = true,
        private val transcript: String = "salut"
    ) : WhisperCppNativeRuntime {
        override fun transcribe(request: LocalAsrRequest): String = transcript
    }
}
