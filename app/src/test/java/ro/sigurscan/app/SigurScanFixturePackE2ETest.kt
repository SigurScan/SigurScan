package ro.sigurscan.app

import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File
import java.net.URI
import java.util.Locale

class SigurScanFixturePackE2ETest {
    private val gson = Gson()
    private val gate = EvidenceGate { 1_000L }
    private val fixtureRoot: File = resolveFixtureRoot()

    @Test
    fun fixturePackIntegrity_allCasesHaveLocalFilesAndSafeScamDomains() {
        val cases = loadCases()
        assertEquals("Fixture pack should contain the full v1 corpus", 143, cases.size)

        val failures = mutableListOf<String>()
        cases.forEach { case ->
            if (!fixtureRoot.resolve(case.fixturePath).isFile) {
                failures += "${case.id}: missing fixture ${case.fixturePath}"
            }
            if (!fixtureRoot.resolve(case.providerMockPath).isFile) {
                failures += "${case.id}: missing provider mock ${case.providerMockPath}"
            }
            case.primaryUrlExpected?.let { expected ->
                val host = runCatching { URI(expected).host?.lowercase(Locale.US)?.removePrefix("www.").orEmpty() }.getOrDefault("")
                val expectedSafe = host.endsWith(".test") ||
                    host.endsWith(".invalid") ||
                    host.endsWith(".example") ||
                    host in OFFICIAL_HOST_ALLOWLIST
                if (!expectedSafe) failures += "${case.id}: unexpected primary host in fixture pack: $host"
            }
        }

        assertTrue(failures.take(20).joinToString("\n"), failures.isEmpty())
    }

    @Test
    fun textAndHtmlEmailFixtures_matchGateDecisionsWithMockedProviders() {
        val cases = loadCases().filter { it.inputType in setOf("PASTE_TEXT", "SHARE_HTML_EMAIL") }
        assertEquals("Text/html subset should stay stable", 110, cases.size)

        val failures = mutableListOf<String>()
        cases.forEach { case ->
            val snapshot = buildSnapshot(case)
            val result = gate.evaluate(snapshot)
            val expectedAction = GateAction.valueOf(case.expectedDecision)

            if (result.action != expectedAction) {
                failures += "${case.id} ${case.title}: expected ${case.expectedDecision}, got ${result.action}; " +
                    "signals=${snapshot.signals.map { it.code }.distinct()}; primary=${snapshot.primaryUrl}; final=${snapshot.finalUrl}"
            }
            if (result.action.userLabel != case.expectedUserLabel) {
                failures += "${case.id} ${case.title}: expected label '${case.expectedUserLabel}', got '${result.action.userLabel}'"
            }
            case.primaryUrlExpected?.let { expected ->
                if (snapshot.primaryUrl != expected) {
                    failures += "${case.id} ${case.title}: expected primary '$expected', got '${snapshot.primaryUrl}'"
                }
            }
            case.primaryHostExpected?.let { expected ->
                val actual = hostOf(snapshot.primaryUrl)
                if (actual != expected.lowercase(Locale.US).removePrefix("www.")) {
                    failures += "${case.id} ${case.title}: expected primary host '$expected', got '$actual'"
                }
            }
        }

        assertTrue(failures.take(40).joinToString("\n"), failures.isEmpty())
    }

    private fun buildSnapshot(case: FixtureCase): EvidenceSnapshot {
        val fixture = fixtureRoot.resolve(case.fixturePath)
        val mock = loadProviderMock(case.providerMockPath)
        val providerModel = providerModelFrom(mock, case.shouldSubmitExternal)
        val input = when (case.inputType) {
            "SHARE_HTML_EMAIL" -> buildEmailInput(case, fixture, providerModel)
            else -> buildTextInput(case, fixture, providerModel)
        }
        return EvidenceSignalNormalizer.buildSnapshot(input)
    }

    private fun buildTextInput(case: FixtureCase, fixture: File, providerModel: ProviderModel): EvidenceNormalizerInput {
        return EvidenceNormalizerInput(
            scanId = case.id,
            inputKind = case.inputType,
            channel = "fixture_pack_v1",
            rawText = fixture.readText(),
            finalUrl = providerModel.finalUrl,
            threatIntel = providerModel.threatIntel,
            providerStates = providerModel.providerStates,
            completeness = providerModel.completeness,
            registryVersion = case.registryVersion,
            corpusVersion = case.policyVersion,
            virusTotalConfigured = providerModel.virusTotalConfigured
        )
    }

    private fun buildEmailInput(case: FixtureCase, fixture: File, providerModel: ProviderModel): EvidenceNormalizerInput {
        val rawEmail = fixture.readText()
        val parsed = EmailMessageParser.parse(rawEmail)
        val htmlForExtraction = parsed.htmlText.ifBlank { parsed.plainText }
        val extractedLinks = HtmlLinkExtractor.extractHtmlLinks(htmlForExtraction)
        val assembled = MailShareInputAssembler.buildMailScanInput(
            parsed.bodyForAnalysis,
            extractedLinks,
            "Fixture ${case.id}"
        )
        return EvidenceNormalizerInput(
            scanId = case.id,
            inputKind = case.inputType,
            channel = "email_html_fixture",
            rawText = assembled,
            htmlContent = htmlForExtraction,
            extractedLinks = extractedLinks,
            finalUrl = providerModel.finalUrl,
            threatIntel = providerModel.threatIntel,
            providerStates = providerModel.providerStates,
            completeness = providerModel.completeness,
            registryVersion = case.registryVersion,
            corpusVersion = case.policyVersion,
            virusTotalConfigured = providerModel.virusTotalConfigured
        )
    }

    private fun providerModelFrom(mock: ProviderMock, shouldSubmitExternal: Boolean): ProviderModel {
        if (!shouldSubmitExternal) {
            return ProviderModel(
                finalUrl = null,
                threatIntel = emptyList(),
                providerStates = mapOf(
                    ProviderId.WEB_RISK to ProviderState(ProviderId.WEB_RISK, ProviderStatus.SKIPPED, note = "privacy skip"),
                    ProviderId.URLSCAN to ProviderState(ProviderId.URLSCAN, ProviderStatus.SKIPPED, note = "privacy skip"),
                    ProviderId.VIRUSTOTAL to ProviderState(ProviderId.VIRUSTOTAL, ProviderStatus.SKIPPED, note = "privacy skip")
                ),
                completeness = EvidenceCompleteness.LOCAL_ONLY,
                virusTotalConfigured = false
            )
        }

        val threatIntel = mutableListOf<ThreatIntelSourceResult>()
        val providerStates = mutableMapOf<ProviderId, ProviderState>()

        mock.providers["google_web_risk"]?.let { provider ->
            val status = providerStatus(provider.status)
            providerStates[ProviderId.WEB_RISK] = ProviderState(ProviderId.WEB_RISK, status)
            when (provider.result) {
                "NO_MATCH" -> threatIntel += ThreatIntelSourceResult("google_web_risk", "No Threats", "low", "NO_MATCH")
                "WEB_RISK_MALWARE" -> threatIntel += ThreatIntelSourceResult("google_web_risk", "Threats Detected", "high", "MALWARE")
                "UNAVAILABLE" -> providerStates[ProviderId.WEB_RISK] = ProviderState(ProviderId.WEB_RISK, ProviderStatus.ERROR)
            }
        }

        var finalUrl: String? = null
        mock.providers["urlscan"]?.let { provider ->
            finalUrl = provider.finalUrl.takeIf { provider.status == "SUCCESS" }
            val status = providerStatus(provider.status)
            providerStates[ProviderId.URLSCAN] = ProviderState(ProviderId.URLSCAN, status)
            when (provider.verdict) {
                "NO_VISIBLE_RISK" -> threatIntel += ThreatIntelSourceResult("urlscan.io", "No malicious classification", "low", "NO_VISIBLE_RISK")
                "MALICIOUS_CARD_FORM" -> threatIntel += ThreatIntelSourceResult("urlscan.io", "Malicious card form phishing", "high", "MALICIOUS_CARD_FORM")
                "MALICIOUS_OTP_FORM" -> threatIntel += ThreatIntelSourceResult("urlscan.io", "Malicious OTP form phishing", "high", "MALICIOUS_OTP_FORM")
                "MALICIOUS_REDIRECT" -> threatIntel += ThreatIntelSourceResult("urlscan.io", "Malicious redirect phishing", "high", "MALICIOUS_REDIRECT")
                "MALICIOUS_PHISHING" -> threatIntel += ThreatIntelSourceResult("urlscan.io", "Malicious phishing", "high", "MALICIOUS_PHISHING")
            }
        }

        var virusTotalConfigured = false
        mock.providers["virustotal"]?.let { provider ->
            virusTotalConfigured = provider.status != "NOT_RUN"
            val status = providerStatus(provider.status)
            providerStates[ProviderId.VIRUSTOTAL] = ProviderState(ProviderId.VIRUSTOTAL, status)
            when (provider.verdict) {
                "MALICIOUS_HIGH" -> threatIntel += ThreatIntelSourceResult("VirusTotal", "Malicious", "high", "malicious=5 suspicious=2")
                "LOW_ENGINE_HIT" -> threatIntel += ThreatIntelSourceResult("VirusTotal", "Low detection", "low", "malicious=1 suspicious=0")
            }
        }

        val completeness = when {
            providerStates.values.any { it.status in setOf(ProviderStatus.PENDING, ProviderStatus.TIMEOUT, ProviderStatus.RATE_LIMITED, ProviderStatus.ERROR) } -> EvidenceCompleteness.PARTIAL_ONLINE
            finalUrl != null || threatIntel.isNotEmpty() -> EvidenceCompleteness.FULL
            else -> EvidenceCompleteness.LOCAL_ONLY
        }

        return ProviderModel(finalUrl, threatIntel, providerStates, completeness, virusTotalConfigured)
    }

    private fun providerStatus(status: String?): ProviderStatus {
        return when (status) {
            "SUCCESS" -> ProviderStatus.OK
            "TIMEOUT" -> ProviderStatus.TIMEOUT
            "RATE_LIMITED" -> ProviderStatus.RATE_LIMITED
            "404", "UNAVAILABLE" -> ProviderStatus.ERROR
            "NOT_RUN" -> ProviderStatus.NOT_RUN
            else -> ProviderStatus.NOT_RUN
        }
    }

    private fun loadCases(): List<FixtureCase> {
        val type = object : TypeToken<List<FixtureCase>>() {}.type
        return gson.fromJson(fixtureRoot.resolve("test_cases.json").readText(), type)
    }

    private fun loadProviderMock(path: String): ProviderMock {
        return gson.fromJson(fixtureRoot.resolve(path).readText(), ProviderMock::class.java)
    }

    private fun resolveFixtureRoot(): File {
        val candidates = listOfNotNull(
            System.getenv("SIGURSCAN_E2E_FIXTURES_DIR"),
            System.getenv("NUDACLICK_E2E_FIXTURES_DIR"),
            "e2e_fixtures/nudaclick_e2e_fixtures_v1",
            "../e2e_fixtures/nudaclick_e2e_fixtures_v1"
        ).map(::File)
        return candidates.firstOrNull { it.resolve("test_cases.json").isFile }
            ?: error("SigurScan E2E fixture pack not found. Set SIGURSCAN_E2E_FIXTURES_DIR.")
    }

    private fun hostOf(url: String?): String? {
        if (url.isNullOrBlank()) return null
        return runCatching { URI(url).host?.lowercase(Locale.US)?.removePrefix("www.") }.getOrNull()
    }

    private data class FixtureCase(
        val id: String,
        val title: String,
        val group: String,
        val persona: String,
        @com.google.gson.annotations.SerializedName("input_type") val inputType: String,
        @com.google.gson.annotations.SerializedName("fixture_path") val fixturePath: String,
        @com.google.gson.annotations.SerializedName("primary_url_expected") val primaryUrlExpected: String?,
        @com.google.gson.annotations.SerializedName("primary_host_expected") val primaryHostExpected: String?,
        @com.google.gson.annotations.SerializedName("expected_decision") val expectedDecision: String,
        @com.google.gson.annotations.SerializedName("expected_user_label") val expectedUserLabel: String,
        @com.google.gson.annotations.SerializedName("provider_mock_path") val providerMockPath: String,
        @com.google.gson.annotations.SerializedName("should_submit_external") val shouldSubmitExternal: Boolean,
        @com.google.gson.annotations.SerializedName("policy_version") val policyVersion: String,
        @com.google.gson.annotations.SerializedName("registry_version") val registryVersion: String
    )

    private data class ProviderMock(
        @com.google.gson.annotations.SerializedName("case_id") val caseId: String,
        val providers: Map<String, ProviderPayload>
    )

    private data class ProviderPayload(
        val status: String?,
        val result: String?,
        val verdict: String?,
        @com.google.gson.annotations.SerializedName("final_url") val finalUrl: String?
    )

    private data class ProviderModel(
        val finalUrl: String?,
        val threatIntel: List<ThreatIntelSourceResult>,
        val providerStates: Map<ProviderId, ProviderState>,
        val completeness: EvidenceCompleteness,
        val virusTotalConfigured: Boolean
    )

    companion object {
        private val OFFICIAL_HOST_ALLOWLIST = setOf(
            "uber.com",
            "emag.ro",
            "fancourier.ro",
            "posta-romana.ro",
            "anaf.ro",
            "mfinante.gov.ro",
            "revolut.com",
            "bancatransilvania.ro",
            "ing.ro",
            "bcr.ro",
            "dnsc.ro",
            "olx.ro",
            "example.com"
        )
    }
}
