package ro.sigurscan.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

class AndroidBuildConfigPolicyTest {
    private val gradleFile: String
        get() = File("build.gradle.kts").readText()

    @Test
    fun directProviderKeysAreOptInAndProviderBuildConfigFieldsStayEmpty() {
        assertTrue(
            "Direct provider keys must default to disabled.",
            gradleFile.contains("""localProperties.getProperty("SIGURSCAN_ENABLE_DIRECT_PROVIDER_KEYS")""") &&
                gradleFile.contains("""?: "false"""")
        )

        assertEquals(
            "URLScan key must stay empty in debug and release BuildConfig.",
            2,
            Regex(
                """buildConfigField\(\s*"String",\s*"URLSCAN_API_KEY",\s*"\\"\\""\s*\)""",
                RegexOption.DOT_MATCHES_ALL
            ).findAll(gradleFile).count()
        )
        assertEquals(
            "Google Web Risk key must stay empty in debug and release BuildConfig.",
            2,
            Regex(
                """buildConfigField\(\s*"String",\s*"GOOGLE_WEB_RISK_API_KEY",\s*"\\"\\""\s*\)""",
                RegexOption.DOT_MATCHES_ALL
            ).findAll(gradleFile).count()
        )
    }

    @Test
    fun audioAsrFeatureFlagDefaultsOff() {
        assertTrue(
            "Audio ASR must default to disabled unless explicitly enabled for a reviewed build.",
            gradleFile.contains("""localProperties.getProperty("SIGURSCAN_ENABLE_AUDIO_ASR")""") &&
                gradleFile.contains("""?: "false"""")
        )
        assertTrue(
            "Both debug and release must use the same reviewed audio gate flag.",
            Regex(
                """buildConfigField\("Boolean",\s*"SIGURSCAN_ENABLE_AUDIO_ASR",\s*enableAudioAsr\.toString\(\)\)"""
            ).findAll(gradleFile).count() >= 2
        )
    }
}
