package ro.sigurscan.app

import android.content.Context
import com.google.android.gms.tasks.Tasks
import com.google.android.play.core.integrity.IntegrityManagerFactory
import com.google.android.play.core.integrity.IntegrityTokenRequest
import java.util.UUID
import java.util.concurrent.TimeUnit

interface IntegrityTokenSource {
    fun requestIntegrityToken(nonce: String): String?
}

class PlayIntegrityTokenProvider(
    private val enabled: Boolean,
    private val source: IntegrityTokenSource,
    private val nonceFactory: () -> String = { UUID.randomUUID().toString() }
) {
    fun currentToken(): String? {
        if (!enabled) return null
        val nonce = nonceFactory().trim()
        if (nonce.isBlank()) return null
        return runCatching { source.requestIntegrityToken(nonce) }
            .getOrNull()
            ?.trim()
            ?.takeIf { it.isNotBlank() }
    }

    companion object {
        fun disabled(): PlayIntegrityTokenProvider =
            PlayIntegrityTokenProvider(enabled = false, source = NoopIntegrityTokenSource)

        fun fromContext(context: Context): PlayIntegrityTokenProvider =
            PlayIntegrityTokenProvider(
                enabled = BuildConfig.SIGURSCAN_ENABLE_PLAY_INTEGRITY,
                source = PlayCoreIntegrityTokenSource(context.applicationContext)
            )
    }
}

private object NoopIntegrityTokenSource : IntegrityTokenSource {
    override fun requestIntegrityToken(nonce: String): String? = null
}

private class PlayCoreIntegrityTokenSource(context: Context) : IntegrityTokenSource {
    private val integrityManager = IntegrityManagerFactory.create(context)

    override fun requestIntegrityToken(nonce: String): String? {
        val request = IntegrityTokenRequest.builder()
            .setNonce(nonce)
            .build()
        val response = Tasks.await(
            integrityManager.requestIntegrityToken(request),
            4,
            TimeUnit.SECONDS
        )
        return response.token()
    }
}
