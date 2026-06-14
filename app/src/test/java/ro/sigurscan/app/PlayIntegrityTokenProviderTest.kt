package ro.sigurscan.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class PlayIntegrityTokenProviderTest {
    private class FakeSource(private val token: String?) : IntegrityTokenSource {
        val nonces = mutableListOf<String>()

        override fun requestIntegrityToken(nonce: String): String? {
            nonces += nonce
            return token
        }
    }

    @Test
    fun disabledProviderDoesNotRequestToken() {
        val source = FakeSource("token")
        val provider = PlayIntegrityTokenProvider(
            enabled = false,
            source = source,
            nonceFactory = { "nonce-1" }
        )

        assertNull(provider.currentToken())
        assertTrue(source.nonces.isEmpty())
    }

    @Test
    fun enabledProviderReturnsTrimmedToken() {
        val source = FakeSource("  integrity-token \n")
        val provider = PlayIntegrityTokenProvider(
            enabled = true,
            source = source,
            nonceFactory = { "nonce-1" }
        )

        assertEquals("integrity-token", provider.currentToken())
        assertEquals(listOf("nonce-1"), source.nonces)
    }

    @Test
    fun blankTokenIsNotForwarded() {
        val source = FakeSource("   ")
        val provider = PlayIntegrityTokenProvider(
            enabled = true,
            source = source,
            nonceFactory = { "nonce-1" }
        )

        assertNull(provider.currentToken())
    }
}
