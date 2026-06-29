package ro.sigurscan.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class SpeakerGuardSemanticReviewCoordinatorTest {
    @Test
    fun accumulatesConversationWindowBeforeReviewing() {
        val coordinator = SpeakerGuardSemanticReviewCoordinator(minNewChars = 60, maxReviews = 4)
        val evidence = AudioTranscriptEvidence.analyze(
            "BNR cere sa muti banii intr-un cont sigur acum"
        )

        assertNull(coordinator.offer(transcript("BNR cere sa muti banii", evidence)))

        val request = coordinator.offer(transcript("intr-un cont sigur acum si sa nu spui nimanui", evidence))

        assertEquals(evidence, request?.localEvidence)
        assertTrue(request!!.redactedTranscript.contains("BNR cere"))
        assertTrue(request.redactedTranscript.contains("cont sigur"))
        assertEquals(1, coordinator.reviewsStarted)
    }

    @Test
    fun capsSemanticReviewsPerSession() {
        val coordinator = SpeakerGuardSemanticReviewCoordinator(minNewChars = 8, maxReviews = 2)
        val evidence = AudioTranscriptEvidence.analyze(
            "BNR cere sa muti banii intr-un cont sigur acum"
        )

        assertTrue(coordinator.offer(transcript("muta banii acum", evidence)) != null)
        assertTrue(coordinator.offer(transcript("cont sigur urgent", evidence)) != null)
        assertNull(coordinator.offer(transcript("inca o cerere de transfer", evidence)))

        assertEquals(2, coordinator.reviewsStarted)
    }

    @Test
    fun doesNotSendBlankOrNonEscalableResidualTranscript() {
        val coordinator = SpeakerGuardSemanticReviewCoordinator(minNewChars = 5, maxReviews = 4)
        val residual = AudioEvidenceEngine.evaluate(AudioEvidenceInput())

        assertNull(coordinator.offer(transcript("", residual)))
        assertNull(coordinator.offer(transcript("salut confirm programarea", residual)))

        assertEquals(0, coordinator.reviewsStarted)
    }

    private fun transcript(value: String, evidence: AudioEvidenceResult): LocalAsrResult {
        return LocalAsrResult(
            success = true,
            engine = WhisperCppAsrEngine.ENGINE_NAME,
            transcript = value,
            reasonCode = null,
            evidence = evidence
        )
    }
}
