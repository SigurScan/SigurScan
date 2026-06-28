package ro.sigurscan.app

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.content.pm.PackageManager
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.util.Log
import androidx.core.content.ContextCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlin.math.max

enum class SpeakerGuardPhase {
    IDLE,
    LISTENING,
    PROCESSING,
    STOPPED,
    ERROR
}

data class SpeakerGuardUpdate(
    val phase: SpeakerGuardPhase,
    val active: Boolean,
    val chunksAnalyzed: Int = 0,
    val chunksDropped: Int = 0,
    val result: LocalAsrResult? = null,
    val latencyMs: Long? = null,
    val reasonCode: String? = null,
    val status: String
)

class SpeakerGuardSession(
    private val context: Context,
    private val asrEngine: WhisperCppAsrEngine = WhisperCppAsrEngine(),
    private val semanticReviewer: AudioSemanticReviewer = NoopAudioSemanticReviewer
) {
    private var job: Job? = null
    @Volatile
    private var activeAudioRecord: AudioRecord? = null
    @Volatile
    private var stopRequested: Boolean = false

    val active: Boolean
        get() = job?.isActive == true

    fun start(
        scope: CoroutineScope,
        modelPath: String,
        onUpdate: (SpeakerGuardUpdate) -> Unit
    ) {
        if (active) return
        stopRequested = false
        job = scope.launch(Dispatchers.Default) {
            runCatching {
                runCaptureLoop(modelPath, onUpdate)
            }.onFailure { throwable ->
                if (stopRequested || throwable is CancellationException) {
                    return@onFailure
                }
                onUpdate(
                    SpeakerGuardUpdate(
                        phase = SpeakerGuardPhase.ERROR,
                        active = false,
                        reasonCode = throwable.javaClass.simpleName,
                        status = "Urechea s-a oprit: ${throwable.message ?: "eroare audio"}."
                    )
                )
            }
        }
    }

    fun stop() {
        stopRequested = true
        releaseActiveAudioRecord()
    }

    fun cancel() {
        stopRequested = true
        job?.cancel()
        releaseActiveAudioRecord()
        job = null
    }

    @SuppressLint("MissingPermission")
    private suspend fun runCaptureLoop(
        modelPath: String,
        onUpdate: (SpeakerGuardUpdate) -> Unit
    ) = coroutineScope {
        if (ContextCompat.checkSelfPermission(context, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            onUpdate(
                SpeakerGuardUpdate(
                    phase = SpeakerGuardPhase.ERROR,
                    active = false,
                    reasonCode = "microphone_permission_missing",
                    status = "Permisiunea microfonului lipsește."
                )
            )
            return@coroutineScope
        }

        val minBufferBytes = AudioRecord.getMinBufferSize(
            SAMPLE_RATE_HZ,
            AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT
        )
        if (minBufferBytes <= 0) {
            onUpdate(
                SpeakerGuardUpdate(
                    phase = SpeakerGuardPhase.ERROR,
                    active = false,
                    reasonCode = "audio_record_unavailable",
                    status = "Microfonul nu poate porni pe acest dispozitiv."
                )
            )
            return@coroutineScope
        }

        val chunkSamples = SAMPLE_RATE_HZ * CHUNK_SECONDS
        val recordBufferSamples = max(minBufferBytes / BYTES_PER_SAMPLE, SAMPLE_RATE_HZ)
        val audioRecord = AudioRecord.Builder()
            .setAudioSource(MediaRecorder.AudioSource.VOICE_RECOGNITION)
            .setAudioFormat(
                AudioFormat.Builder()
                    .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                    .setSampleRate(SAMPLE_RATE_HZ)
                    .setChannelMask(AudioFormat.CHANNEL_IN_MONO)
                    .build()
            )
            .setBufferSizeInBytes(max(minBufferBytes, recordBufferSamples * BYTES_PER_SAMPLE * 2))
            .build()

        if (audioRecord.state != AudioRecord.STATE_INITIALIZED) {
            audioRecord.release()
            onUpdate(
                SpeakerGuardUpdate(
                    phase = SpeakerGuardPhase.ERROR,
                    active = false,
                    reasonCode = "audio_record_init_failed",
                    status = "Microfonul nu s-a inițializat corect."
                )
            )
            return@coroutineScope
        }

        val chunks = Channel<ShortArray>(capacity = CHUNK_QUEUE_CAPACITY)
        var chunksAnalyzed = 0
        var chunksDropped = 0
        var lastResult: LocalAsrResult? = null
        var lastLatencyMs: Long? = null
        var lastReasonCode: String? = null
        val evidenceAggregator = AudioEvidenceSessionAggregator()

        try {
            activeAudioRecord = audioRecord
            audioRecord.startRecording()
            onUpdate(
                SpeakerGuardUpdate(
                    phase = SpeakerGuardPhase.LISTENING,
                    active = true,
                    status = "Ascult conversația. Ține apelul pe difuzor."
                )
            )

            val recorder = launch(Dispatchers.IO) {
                val readBuffer = ShortArray(recordBufferSamples)
                var chunk = ShortArray(chunkSamples)
                var offset = 0

                while (isActive && !stopRequested) {
                    val read = try {
                        audioRecord.read(readBuffer, 0, readBuffer.size)
                    } catch (throwable: Throwable) {
                        if (stopRequested) break
                        throw throwable
                    }
                    if (stopRequested) break
                    if (read <= 0) continue

                    var consumed = 0
                    while (consumed < read) {
                        val copyCount = minOf(read - consumed, chunk.size - offset)
                        readBuffer.copyInto(
                            destination = chunk,
                            destinationOffset = offset,
                            startIndex = consumed,
                            endIndex = consumed + copyCount
                        )
                        offset += copyCount
                        consumed += copyCount

                        if (offset == chunk.size) {
                            chunks.send(chunk)
                            chunk = ShortArray(chunkSamples)
                            offset = 0
                        }
                    }
                }

                if (offset >= MIN_PARTIAL_CHUNK_SAMPLES) {
                    chunks.send(chunk.copyOf(offset))
                }
                chunks.close()
            }

            val processor = launch(Dispatchers.Default) {
                for (chunk in chunks) {
                    Log.i(
                        TAG,
                        "speaker_guard_chunk_processing index=${chunksAnalyzed + 1} samples=${chunk.size}"
                    )
                    onUpdate(
                        SpeakerGuardUpdate(
                            phase = SpeakerGuardPhase.PROCESSING,
                            active = true,
                            chunksAnalyzed = chunksAnalyzed,
                            chunksDropped = chunksDropped,
                            status = "Analizez conversația. Ține apelul pe difuzor."
                        )
                    )
                    val started = System.currentTimeMillis()
                    val rawResult = withContext(Dispatchers.Default) {
                        asrEngine.transcribe(
                            LocalAsrRequest(
                                pcm16Mono = chunk,
                                sampleRateHz = SAMPLE_RATE_HZ,
                                language = "ro",
                                modelPath = modelPath
                            )
                        )
                    }
                    val semanticResult = rawResult.withSemanticReview()
                    val result = semanticResult.withSessionEvidence(evidenceAggregator)
                    chunksAnalyzed += 1
                    val latency = System.currentTimeMillis() - started
                    lastResult = result
                    lastLatencyMs = latency
                    lastReasonCode = result.reasonCode
                    Log.i(
                        TAG,
                        "speaker_guard_chunk_result index=$chunksAnalyzed " +
                            "transcript_present=${rawResult.transcript.isNotBlank()} " +
                            "success=${result.success} " +
                            "reason=${result.reasonCode.orEmpty()} " +
                            "verdict=${result.evidence?.verdict?.name ?: "NONE"} " +
                            "processing=${result.evidence?.processing ?: "none"} " +
                            "latency_ms=$latency"
                    )
                    onUpdate(
                        SpeakerGuardUpdate(
                            phase = SpeakerGuardPhase.LISTENING,
                            active = true,
                            chunksAnalyzed = chunksAnalyzed,
                            chunksDropped = chunksDropped,
                            result = result,
                            latencyMs = latency,
                            reasonCode = result.reasonCode,
                            status = statusFor(result)
                        )
                    )
                }
            }

            recorder.join()
            processor.join()
        } finally {
            chunks.close()
            if (activeAudioRecord === audioRecord) {
                activeAudioRecord = null
            }
            releaseAudioRecord(audioRecord)
            onUpdate(
                SpeakerGuardUpdate(
                    phase = SpeakerGuardPhase.STOPPED,
                    active = false,
                    chunksAnalyzed = chunksAnalyzed,
                    chunksDropped = chunksDropped,
                    result = lastResult,
                    latencyMs = lastLatencyMs,
                    reasonCode = lastReasonCode ?: if (chunksAnalyzed == 0) "no_audio_chunk" else null,
                    status = stoppedStatus(chunksAnalyzed, lastResult)
                )
            )
            job = null
        }
    }

    private fun releaseActiveAudioRecord() {
        activeAudioRecord?.let { audioRecord ->
            activeAudioRecord = null
            releaseAudioRecord(audioRecord)
        }
    }

    private fun releaseAudioRecord(audioRecord: AudioRecord) {
        runCatching { audioRecord.stop() }
        runCatching { audioRecord.release() }
    }

    private fun statusFor(result: LocalAsrResult): String {
        val evidence = result.evidence
        return when {
            !result.success && result.reasonCode == "empty_transcript" -> "Nu am prins voce clară în ultimul fragment. Ține telefonul aproape de difuzor."
            !result.success -> "Nu am putut transcrie fragmentul: ${result.reasonCode ?: "eroare ASR"}."
            evidence?.verdict == AudioEvidenceVerdict.DANGEROUS -> "Semnale puternice de fraudă în conversație."
            evidence?.verdict == AudioEvidenceVerdict.SUSPECT -> "Semnale suspecte în conversație. Verifică înainte să continui."
            else -> "Am analizat vocea, dar încă nu sunt suficiente dovezi."
        }
    }

    private fun stoppedStatus(chunksAnalyzed: Int, lastResult: LocalAsrResult?): String {
        if (chunksAnalyzed == 0) {
            return "Urechea s-a oprit fără fragment audio clar. Pune apelul pe difuzor și încearcă din nou."
        }
        return lastResult?.let { statusFor(it) } ?: "Urechea este oprită."
    }

    private fun LocalAsrResult.withSessionEvidence(
        aggregator: AudioEvidenceSessionAggregator
    ): LocalAsrResult {
        val currentEvidence = evidence ?: return this
        val aggregatedEvidence = aggregator.absorb(currentEvidence)
        return if (aggregatedEvidence == currentEvidence) {
            this
        } else {
            copy(evidence = aggregatedEvidence)
        }
    }

    private suspend fun LocalAsrResult.withSemanticReview(): LocalAsrResult {
        if (!success || transcript.isBlank()) return this
        val redacted = AudioTranscriptRedactor.redact(transcript)
        Log.i(TAG, "speaker_guard_semantic_review_requested transcript_chars=${redacted.length}")
        val review = withContext(Dispatchers.IO) {
            semanticReviewer.review(redacted, evidence)
        }
        Log.i(
            TAG,
            "speaker_guard_semantic_review_result received=${review != null} " +
                "risk=${review?.semanticReview?.riskClass ?: "none"} " +
                "escalates=${review?.escalates ?: false}"
        )
        val fused = AudioSemanticReviewFusion.fuse(evidence, review)
        return copy(evidence = fused)
    }

    companion object {
        const val SAMPLE_RATE_HZ = 16_000
        const val CHUNK_SECONDS = 6
        private const val CHUNK_QUEUE_CAPACITY = 8
        private const val BYTES_PER_SAMPLE = 2
        private const val MIN_PARTIAL_CHUNK_SECONDS = 2
        private const val MIN_PARTIAL_CHUNK_SAMPLES = SAMPLE_RATE_HZ * MIN_PARTIAL_CHUNK_SECONDS
        private const val TAG = "SpeakerGuardSession"
    }
}
