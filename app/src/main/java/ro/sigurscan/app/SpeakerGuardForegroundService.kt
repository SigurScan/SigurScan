package ro.sigurscan.app

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.net.Uri
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object SpeakerGuardForegroundServiceEvents {
    private val _updates = MutableSharedFlow<SpeakerGuardUpdate>(extraBufferCapacity = 64)
    val updates: SharedFlow<SpeakerGuardUpdate> = _updates.asSharedFlow()

    fun publish(update: SpeakerGuardUpdate) {
        _updates.tryEmit(update)
    }
}

class SpeakerGuardForegroundService : Service() {
    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
    private var captureSession: SpeakerGuardSession? = null
    private val audioSemanticApi: SigurScanApi by lazy { buildAudioSemanticApi() }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        return when (intent?.action) {
            ACTION_START_CAPTURE -> handleStartCapture(intent, startId)
            ACTION_STOP_CAPTURE -> {
                stopCaptureSession()
                stopSelf(startId)
                START_NOT_STICKY
            }
            else -> {
                stopSelf(startId)
                START_NOT_STICKY
            }
        }
    }

    override fun onDestroy() {
        stopCaptureSession(removeForeground = false)
        serviceScope.cancel()
        super.onDestroy()
    }

    private fun handleStartCapture(intent: Intent, startId: Int): Int {
        val modelPath = intent.getStringExtra(EXTRA_MODEL_PATH).orEmpty()
        if (modelPath.isBlank()) {
            SpeakerGuardForegroundServiceEvents.publish(
                SpeakerGuardUpdate(
                    phase = SpeakerGuardPhase.ERROR,
                    active = false,
                    reasonCode = "asr_model_missing",
                    status = "Modelul audio local lipsește."
                )
            )
            stopSelf(startId)
            return START_NOT_STICKY
        }

        ensureChannel()
        startCaptureForeground()
        if (captureSession?.active == true) return START_STICKY

        val session = SpeakerGuardSession(
            context = applicationContext,
            semanticReviewer = BackendAudioSemanticReviewer(audioSemanticApi, channel = "call_live")
        )
        captureSession = session
        Log.i(TAG, "speaker_guard_capture_started")
        session.start(serviceScope, modelPath) { update ->
            SpeakerGuardForegroundServiceEvents.publish(update)
            if (!update.active && update.phase != SpeakerGuardPhase.PROCESSING) {
                stopCaptureSession()
                stopSelf(startId)
            }
        }
        return START_STICKY
    }

    private fun ensureChannel() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val manager = getSystemService(NotificationManager::class.java) ?: return
        val channel = NotificationChannel(
            CHANNEL_ID,
            "Urechea SigurScan",
            NotificationManager.IMPORTANCE_LOW
        ).apply {
            description = "Serviciu vizibil pentru captura Urechea în timpul apelurilor."
        }
        manager.createNotificationChannel(channel)
    }

    private fun startCaptureForeground() {
        val notification = captureNotification()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(
                CAPTURE_NOTIFICATION_ID,
                notification,
                ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE
            )
        } else {
            startForeground(CAPTURE_NOTIFICATION_ID, notification)
        }
    }

    private fun captureNotification(): Notification {
        val intent = speakerGuardDeepLinkIntent(this)
        val pendingIntent = PendingIntent.getActivity(
            this,
            CAPTURE_REQUEST_CODE,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setContentTitle("Urechea ascultă")
            .setContentText("Analiza rulează local. Ține apelul pe difuzor.")
            .setStyle(NotificationCompat.BigTextStyle().bigText("Audio-ul brut rămâne pe telefon. Pentru verdict trimitem doar transcriere redactată."))
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setCategory(NotificationCompat.CATEGORY_SERVICE)
            .setVisibility(NotificationCompat.VISIBILITY_PRIVATE)
            .setOngoing(true)
            .setContentIntent(pendingIntent)
            .build()
    }

    private fun stopCaptureSession(removeForeground: Boolean = true) {
        if (captureSession != null) {
            Log.i(TAG, "speaker_guard_capture_stopped")
        }
        captureSession?.stop()
        captureSession = null
        if (removeForeground) {
            runCatching { stopForeground(STOP_FOREGROUND_REMOVE) }
        }
    }

    private fun buildAudioSemanticApi(): SigurScanApi {
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.NONE
        }
        val client = OkHttpClient.Builder()
            .callTimeout(15, TimeUnit.SECONDS)
            .readTimeout(15, TimeUnit.SECONDS)
            .writeTimeout(15, TimeUnit.SECONDS)
            .connectTimeout(8, TimeUnit.SECONDS)
            .addInterceptor(ApiKeyInterceptor(rawApiKey = BuildConfig.SIGURSCAN_API_KEY))
            .addInterceptor(logging)
            .build()

        return Retrofit.Builder()
            .baseUrl(configuredBackendBaseUrl())
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(SigurScanApi::class.java)
    }

    private fun configuredBackendBaseUrl(): String {
        val configured = BuildConfig.SIGURSCAN_BACKEND_BASE_URL.trim()
        val allowed = configured.takeIf {
            it.startsWith("https://", ignoreCase = true) ||
                (BuildConfig.DEBUG && it.startsWith("http://", ignoreCase = true))
        }
        return (allowed ?: "https://offline.sigurscan.invalid/")
            .let { if (it.endsWith("/")) it else "$it/" }
    }

    companion object {
        private const val ACTION_START_CAPTURE = "ro.sigurscan.app.action.START_SPEAKER_GUARD_CAPTURE"
        private const val ACTION_STOP_CAPTURE = "ro.sigurscan.app.action.STOP_SPEAKER_GUARD_CAPTURE"
        private const val EXTRA_MODEL_PATH = "model_path"
        private const val CHANNEL_ID = "speaker_guard_foreground"
        private const val CAPTURE_NOTIFICATION_ID = 4732
        private const val CAPTURE_REQUEST_CODE = 4732
        private const val DEEP_LINK = "sigurscan://speaker-guard?autostart=1&source=call_screening"
        private const val TAG = "SpeakerGuardCapture"

        fun startCapture(context: Context, modelPath: String) {
            val intent = Intent(context, SpeakerGuardForegroundService::class.java).apply {
                action = ACTION_START_CAPTURE
                putExtra(EXTRA_MODEL_PATH, modelPath)
            }
            ContextCompat.startForegroundService(context.applicationContext, intent)
        }

        fun stopCapture(context: Context) {
            val intent = Intent(context, SpeakerGuardForegroundService::class.java).apply {
                action = ACTION_STOP_CAPTURE
            }
            runCatching { context.applicationContext.startService(intent) }
        }

        private fun speakerGuardDeepLinkIntent(context: Context): Intent {
            return Intent(Intent.ACTION_VIEW, Uri.parse(DEEP_LINK)).apply {
                setPackage(context.packageName)
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP)
            }
        }
    }
}
