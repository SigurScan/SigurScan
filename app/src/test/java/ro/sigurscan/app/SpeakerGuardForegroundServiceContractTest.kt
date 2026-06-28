package ro.sigurscan.app

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

class SpeakerGuardForegroundServiceContractTest {
    @Test
    fun viewModelDelegatesLiveCaptureToMicrophoneForegroundService() {
        val viewModelAudioSource = File("src/main/java/ro/sigurscan/app/ScannerViewModelAudio.kt").readText()

        assertTrue(
            "Starting live-call Speaker Guard must enter the microphone foreground service after consent.",
            viewModelAudioSource.contains("SpeakerGuardForegroundService.startCapture(")
        )
        assertTrue(
            "Stopping live-call Speaker Guard must explicitly stop the microphone foreground service.",
            viewModelAudioSource.contains("SpeakerGuardForegroundService.stopCapture(")
        )
        assertFalse(
            "The ViewModel must not own AudioRecord capture in viewModelScope; Android can background-limit it behind the dialer.",
            viewModelAudioSource.contains("SpeakerGuardSession(")
        )
    }

    @Test
    fun foregroundServiceOwnsCaptureSessionOnlyAfterExplicitStartAction() {
        val serviceSource = File("src/main/java/ro/sigurscan/app/SpeakerGuardForegroundService.kt").readText()
        val promptServiceSource = File("src/main/java/ro/sigurscan/app/SpeakerGuardPromptForegroundService.kt")
            .takeIf { it.exists() }
            ?.readText()
            .orEmpty()
        val promptActivitySource = File("src/main/java/ro/sigurscan/app/SpeakerGuardPromptActivity.kt")
            .takeIf { it.exists() }
            ?.readText()
            .orEmpty()

        assertTrue(serviceSource.contains("ACTION_START_CAPTURE"))
        assertTrue(serviceSource.contains("ACTION_STOP_CAPTURE"))
        assertTrue(serviceSource.contains("SpeakerGuardSession("))
        assertTrue(
            "The service must start foreground capture with microphone type, not just a prompt notification.",
            serviceSource.contains("FOREGROUND_SERVICE_TYPE_MICROPHONE") ||
                serviceSource.contains("ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE")
        )
        assertFalse(
            "The microphone capture service must not own the call-screening prompt action; the prompt starts from background before consent.",
            serviceSource.contains("ACTION_SHOW_CALL_PROMPT") ||
                serviceSource.contains("handleCallPrompt")
        )
        assertTrue(
            "A separate prompt-only foreground service must own the call-screening prompt.",
            promptServiceSource.contains("ACTION_SHOW_CALL_PROMPT") &&
                promptServiceSource.contains("handleCallPrompt") &&
                promptServiceSource.contains("SpeakerGuardCallPromptNotifier.fromContext(applicationContext).showIfNeeded(decision)")
        )
        assertFalse(
            "The prompt-only foreground service must not own microphone capture.",
            promptServiceSource.contains("ACTION_START_CAPTURE") ||
                promptServiceSource.contains("SpeakerGuardSession(")
        )
        assertTrue(
            "Prompt/capture lifecycle must be observable in live-call QA without logging audio or phone numbers.",
            promptServiceSource.contains("speaker_guard_prompt_toast_shown") &&
                serviceSource.contains("speaker_guard_capture_started") &&
                serviceSource.contains("speaker_guard_capture_stopped")
        )
        assertTrue(
            "The unlocked-call fallback must tell the user the real action sequence, not just mention a hidden notification.",
            promptServiceSource.contains("răspunde") &&
                promptServiceSource.contains("pune pe difuzor") &&
                promptServiceSource.contains("cardul de jos")
        )
        assertTrue(
            "Unlocked incoming-call UX must not compete with the dialer popup at the top of the screen.",
            promptActivitySource.contains("contentAlignment = Alignment.BottomCenter") &&
                promptActivitySource.contains("Răspunde sus") &&
                promptActivitySource.contains("Cardul stă jos")
        )
    }

    @Test
    fun liveCallCaptureDoesNotDropAudioChunksUnderSlowAsrBackpressure() {
        val sessionSource = File("src/main/java/ro/sigurscan/app/SpeakerGuardSession.kt").readText()

        assertFalse(
            "Live-call recall must prefer latency over losing the exact sentence with the scam.",
            sessionSource.contains("BufferOverflow.DROP_OLDEST")
        )
        assertFalse(
            "trySend hides overflow when the channel is configured to drop; capture must suspend/backpressure instead.",
            sessionSource.contains("trySend(chunk)")
        )
        assertTrue(
            "Capture must enqueue chunks with a suspending send so slow ASR cannot silently discard audio.",
            sessionSource.contains("chunks.send(chunk)")
        )
        assertTrue(
            "The queue must buffer several 6s chunks so first-run Whisper latency on Nokia does not erase the call.",
            sessionSource.contains("CHUNK_QUEUE_CAPACITY")
        )
    }

    @Test
    fun foregroundServiceReplaysLatestUpdateAfterActivityRecreation() {
        val serviceSource = File("src/main/java/ro/sigurscan/app/SpeakerGuardForegroundService.kt").readText()
        val viewModelAudioSource = File("src/main/java/ro/sigurscan/app/ScannerViewModelAudio.kt").readText()

        assertTrue(
            "Live-call verdict updates must survive Activity/ViewModel recreation while the dialer owns the screen.",
            serviceSource.contains("MutableSharedFlow<SpeakerGuardUpdate>(replay = 1")
        )
        assertTrue(
            "Starting a fresh session must not replay an old STOPPED update and cancel the new collector.",
            serviceSource.contains("resetReplayCache()") &&
                viewModelAudioSource.contains("SpeakerGuardForegroundServiceEvents.clear()")
        )
    }

    @Test
    fun stopDrainsQueuedAudioInsteadOfCancellingTheProcessor() {
        val sessionSource = File("src/main/java/ro/sigurscan/app/SpeakerGuardSession.kt").readText()

        assertFalse(
            "Normal live-call stop must not cancel the session job before queued chunks reach ASR/Mistral.",
            sessionSource.contains("fun stop() {\n        stopRequested = true\n        job?.cancel()")
        )
        assertTrue(
            "Normal stop should only request stop and release AudioRecord so recorder can close the queue gracefully.",
            sessionSource.contains("fun stop() {\n        stopRequested = true\n        releaseActiveAudioRecord()\n    }")
        )
        assertFalse(
            "The processor must not be cancelled after recorder.join(); it must drain the closed channel.",
            sessionSource.contains("processor.cancel()")
        )
        assertTrue(
            "The recorder should close the chunk channel and the processor should finish by join().",
            sessionSource.contains("processor.join()")
        )
    }

    @Test
    fun liveCallDebugLogsArePrivacySafeAndShowChunkAndSemanticProgress() {
        val sessionSource = File("src/main/java/ro/sigurscan/app/SpeakerGuardSession.kt").readText()

        assertTrue(sessionSource.contains("speaker_guard_chunk_processing"))
        assertTrue(sessionSource.contains("speaker_guard_chunk_result"))
        assertTrue(sessionSource.contains("speaker_guard_semantic_review_requested"))
        assertTrue(sessionSource.contains("speaker_guard_semantic_review_result"))
        assertFalse(
            "Never log the raw transcript from a live call.",
            sessionSource.contains("Log.i(TAG, \"") && sessionSource.contains("\$transcript")
        )
    }

    @Test
    fun stoppedUpdateKeepsLastAsrReasonInsteadOfMaskingItAsCleanUnverified() {
        val viewModelAudioSource = File("src/main/java/ro/sigurscan/app/ScannerViewModelAudio.kt").readText()

        assertTrue(
            "Stopping after an empty transcript must still tell the user we did not hear clear voice.",
            viewModelAudioSource.contains("speakerGuardSnapshot.latestReasonCode")
        )
    }
}
