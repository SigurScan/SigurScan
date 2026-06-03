package ro.sigurscan.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class EvidenceSignalNormalizerTest {
    private val gate = EvidenceGate { 1_000L }

    @Test
    fun uberPromoHtmlWithApprovedTrackerAndFinalOfficialCanContinueWithCaution() {
        val html = """
            <html>
              <body>
                <p>Uber promo: nu rata reducerea de azi.</p>
                <a href="https://rides.sng.link/Aw5zn/hw3r?campaign=crm">Comanda o cursa</a>
              </body>
            </html>
        """.trimIndent()

        val snapshot = normalize(
            rawText = html,
            htmlContent = html,
            primaryUrl = "https://rides.sng.link/Aw5zn/hw3r?campaign=crm",
            finalUrl = "https://www.uber.com/ro/ride/",
            redirectChain = listOf(
                "https://rides.sng.link/Aw5zn/hw3r?campaign=crm",
                "https://www.uber.com/ro/ride/"
            )
        )

        assertCodes(
            snapshot,
            EvidenceCode.HTML_BUTTON_LINK,
            EvidenceCode.HIDDEN_LINK_PRESENT,
            EvidenceCode.TRACKING_LINK,
            EvidenceCode.APPROVED_TRACKER_DOMAIN,
            EvidenceCode.REDIRECT_CHAIN_APPROVED,
            EvidenceCode.OFFICIAL_DOMAIN_EXACT,
            EvidenceCode.NO_SENSITIVE_FORM,
            EvidenceCode.PROMO_TEXT
        )
        assertEquals("https://www.uber.com/ro/ride/", snapshot.finalUrl)
        assertEquals(GateAction.CONTINUE_WITH_CAUTION, gate.evaluate(snapshot).action)
    }

    @Test
    fun emagPromoHtmlWithButtonAndFinalOfficialCanContinueWithCaution() {
        val html = """
            <html>
              <body>
                <p>eMAG: voucher de weekend si oferta limitata.</p>
                <a href="https://marketing.sng.link/click/emag">Vezi oferta</a>
              </body>
            </html>
        """.trimIndent()

        val snapshot = normalize(
            rawText = html,
            htmlContent = html,
            primaryUrl = "https://marketing.sng.link/click/emag",
            finalUrl = "https://www.emag.ro/oferta",
            redirectChain = listOf("https://marketing.sng.link/click/emag", "https://www.emag.ro/oferta")
        )

        assertCodes(snapshot, EvidenceCode.OFFICIAL_DOMAIN_EXACT, EvidenceCode.NO_SENSITIVE_FORM, EvidenceCode.VOUCHER_TEXT)
        assertEquals(GateAction.CONTINUE_WITH_CAUTION, gate.evaluate(snapshot).action)
    }

    @Test
    fun hiddenButtonOnlyWithoutOfficialFinalIsVerifyOfficial() {
        val html = """
            <html>
              <body>
                <button onclick="window.location.href='https://promo.example.net/landing'">Vezi oferta</button>
              </body>
            </html>
        """.trimIndent()

        val snapshot = normalize(rawText = html, htmlContent = html)

        assertCodes(snapshot, EvidenceCode.HTML_BUTTON_LINK, EvidenceCode.HIDDEN_LINK_PRESENT)
        assertEquals(GateAction.VERIFY_OFFICIAL, gate.evaluate(snapshot).action)
    }

    @Test
    fun telefonStricatMoneyTextMapsToNoReply() {
        val snapshot = normalize(
            rawText = "Mama, sunt eu. Mi s-a stricat telefonul si acesta e numar nou. Trimite bani urgent in cont."
        )

        assertCodes(snapshot, EvidenceCode.FAMILY_NEW_PHONE_MONEY, EvidenceCode.MONEY_REQUEST)
        assertEquals(GateAction.NO_REPLY, gate.evaluate(snapshot).action)
    }

    @Test
    fun whatsappCodeRequestMapsToNoReply() {
        val snapshot = normalize(
            rawText = "WhatsApp: trimite-mi codul de verificare primit prin SMS ca sa confirm dispozitivul."
        )

        assertCodes(snapshot, EvidenceCode.WHATSAPP_CODE_REQUEST, EvidenceCode.WHATSAPP_DEVICE_LINKING_REQUEST)
        assertEquals(GateAction.NO_REPLY, gate.evaluate(snapshot).action)
    }

    @Test
    fun fanFakeCardFormMapsToHardGateAction() {
        val html = """
            <html>
              <body>
                <p>FAN Courier: colet la locker. Plateste taxa de livrare.</p>
                <form action="https://fan-colet-plata.example.net/card">
                  <input name="card" />
                  <input name="cvv" />
                </form>
              </body>
            </html>
        """.trimIndent()

        val snapshot = normalize(rawText = html, htmlContent = html)

        assertCodes(
            snapshot,
            EvidenceCode.COURIER_UNOFFICIAL_DOMAIN,
            EvidenceCode.PARCEL_TAX,
            EvidenceCode.SENSITIVE_FORM_UNOFFICIAL,
            EvidenceCode.CARD_REQUEST,
            EvidenceCode.CVV_REQUEST,
            EvidenceCode.BRAND_IMPERSONATION
        )
        assertEquals(GateAction.DO_NOT_CONTINUE, gate.evaluate(snapshot).action)
    }

    @Test
    fun webRiskNoMatchDoesNotOverrideUnofficialCardForm() {
        val html = """
            <html>
              <body>
                <form action="https://checkout.example.net/pay-card">
                  <input name="card" />
                </form>
              </body>
            </html>
        """.trimIndent()

        val snapshot = normalize(
            rawText = html,
            htmlContent = html,
            threatIntel = listOf(
                ThreatIntelSourceResult(
                    source = "Google Web Risk",
                    verdict = "No Threats",
                    severity = "low",
                    details = "URL fara semnale in baza Google Web Risk."
                )
            )
        )

        assertCodes(snapshot, EvidenceCode.WEBRISK_NO_MATCH, EvidenceCode.SENSITIVE_FORM_UNOFFICIAL)
        assertEquals(ProviderStatus.OK, snapshot.providerStates[ProviderId.WEB_RISK]?.status)
        assertEquals(GateAction.NO_ENTER_DATA, gate.evaluate(snapshot).action)
    }

    @Test
    fun backendGoogleWebRiskSourceNameMapsToHardProviderEvidence() {
        val snapshot = normalize(
            rawText = "Verifica linkul https://danger.example.net",
            finalUrl = "https://danger.example.net",
            threatIntel = listOf(
                ThreatIntelSourceResult(
                    source = "google_web_risk",
                    verdict = "Threats Detected",
                    severity = "high",
                    details = "SOCIAL_ENGINEERING"
                )
            )
        )

        assertCodes(snapshot, EvidenceCode.WEBRISK_MATCH_SOCIAL_ENGINEERING)
        assertEquals(ProviderStatus.OK, snapshot.providerStates[ProviderId.WEB_RISK]?.status)
        assertEquals(GateAction.DO_NOT_CONTINUE, gate.evaluate(snapshot).action)
    }

    @Test
    fun formActionToUnofficialHostOverridesBrandTrustAndTriggersDoNotContinue() {
        val html = """
            <html>
              <body>
                <p>eMAG: confirmare comanda si plata securizata.</p>
                <form action="https://emag-pay.example.net/secure">
                  <input name="card" />
                  <input name="cvv" />
                  <button type="submit">Confirma plata</button>
                </form>
              </body>
            </html>
        """.trimIndent()

        val snapshot = normalize(rawText = html, htmlContent = html)

        assertCodes(
            snapshot,
            EvidenceCode.HTML_BUTTON_LINK,
            EvidenceCode.SENSITIVE_FORM_UNOFFICIAL,
            EvidenceCode.BRAND_IMPERSONATION,
            EvidenceCode.OFFICIAL_DOMAIN_MISMATCH,
            EvidenceCode.CARD_REQUEST,
            EvidenceCode.CVV_REQUEST
        )
        assertEquals(GateAction.DO_NOT_CONTINUE, gate.evaluate(snapshot).action)
    }

    @Test
    fun urlscanPhishingMapsToDoNotContinue() {
        val snapshot = normalize(
            rawText = "Verifica acest link: https://phish.example.net/login",
            finalUrl = "https://phish.example.net/login",
            threatIntel = listOf(
                ThreatIntelSourceResult(
                    source = "urlscan.io",
                    verdict = "Malicious phishing",
                    severity = "high",
                    details = "Sandbox verdict: phishing"
                )
            )
        )

        assertCodes(snapshot, EvidenceCode.URLSCAN_VERDICT_PHISHING)
        assertEquals(ProviderStatus.OK, snapshot.providerStates[ProviderId.URLSCAN]?.status)
        assertEquals(GateAction.DO_NOT_CONTINUE, gate.evaluate(snapshot).action)
    }

    @Test
    fun urlscanNoMaliciousClassificationDoesNotBecomePhishingBecauseOfTheWordMalicious() {
        val snapshot = normalize(
            rawText = "https://example.com",
            finalUrl = "https://example.com",
            threatIntel = listOf(
                ThreatIntelSourceResult(
                    source = "urlscan.io",
                    verdict = "No malicious classification",
                    severity = "low",
                    details = "urlscan verdict=No malicious classification; score=0"
                )
            )
        )

        assertCodes(snapshot, EvidenceCode.URLSCAN_NO_CLASSIFICATION)
        assertFalse(snapshot.signals.any { it.code == EvidenceCode.URLSCAN_VERDICT_PHISHING })
        assertFalse(gate.evaluate(snapshot).action == GateAction.DO_NOT_CONTINUE)
    }

    @Test
    fun urlscanPendingIsProviderStateAndNotSafe() {
        val snapshot = normalize(
            rawText = "Verifica linkul https://pending.example.net",
            finalUrl = "https://pending.example.net",
            threatIntel = listOf(
                ThreatIntelSourceResult(
                    source = "urlscan.io",
                    verdict = "Pending",
                    severity = "unknown",
                    details = "Sandbox queued and processing."
                )
            )
        )

        assertEquals(ProviderStatus.PENDING, snapshot.providerStates[ProviderId.URLSCAN]?.status)
        val result = gate.evaluate(snapshot)
        assertTrue(result.action in listOf(GateAction.VERIFY_OFFICIAL, GateAction.INSUFFICIENT_EVIDENCE))
        assertFalse(result.action == GateAction.CONTINUE_WITH_CAUTION)
        assertFalse(result.action == GateAction.DO_NOT_CONTINUE)
        assertTrue(result.asyncExpected)
    }

    @Test
    fun urlscanTimeoutIsProviderStateAndNotSafe() {
        val snapshot = normalize(
            rawText = "Verifica linkul https://timeout.example.net",
            finalUrl = "https://timeout.example.net",
            threatIntel = listOf(
                ThreatIntelSourceResult(
                    source = "urlscan.io",
                    verdict = "Timeout",
                    severity = "unknown",
                    details = "urlscan.io sandbox timed out."
                )
            )
        )

        assertEquals(ProviderStatus.TIMEOUT, snapshot.providerStates[ProviderId.URLSCAN]?.status)
        val result = gate.evaluate(snapshot)
        assertTrue(result.action in listOf(GateAction.VERIFY_OFFICIAL, GateAction.INSUFFICIENT_EVIDENCE))
        assertFalse(result.action == GateAction.CONTINUE_WITH_CAUTION)
        assertFalse(result.action == GateAction.DO_NOT_CONTINUE)
    }

    @Test
    fun urlscanSkippedIsProviderStateAndNotSafe() {
        val snapshot = normalize(
            rawText = "Verifica linkul https://skipped.example.net",
            finalUrl = "https://skipped.example.net",
            threatIntel = listOf(
                ThreatIntelSourceResult(
                    source = "urlscan.io",
                    verdict = "Skipped",
                    severity = "unknown",
                    details = "urlscan.io API key not configured."
                )
            )
        )

        assertEquals(ProviderStatus.SKIPPED, snapshot.providerStates[ProviderId.URLSCAN]?.status)
        val result = gate.evaluate(snapshot)
        assertTrue(result.action in listOf(GateAction.VERIFY_OFFICIAL, GateAction.INSUFFICIENT_EVIDENCE))
        assertFalse(result.action == GateAction.CONTINUE_WITH_CAUTION)
        assertFalse(result.action == GateAction.DO_NOT_CONTINUE)
    }

    @Test
    fun webmailShellOnlyMapsToInsufficientEvidence() {
        val snapshot = EvidenceSignalNormalizer.buildSnapshot(
            EvidenceNormalizerInput(
                inputKind = "share_text",
                channel = "webmail_shell",
                rawText = "Yahoo Mail shell fara body util"
            )
        )

        assertCodes(snapshot, EvidenceCode.WEBMAIL_SHELL_ONLY)
        assertEquals(GateAction.INSUFFICIENT_EVIDENCE, gate.evaluate(snapshot).action)
    }

    @Test
    fun finalUrlDifferentFromPrimaryPreventsOfficialPrimaryFromBeingTrusted() {
        val rawText = "Uber: confirma cardul pentru oferta ta la https://www.uber.com"
        val snapshot = normalize(
            rawText = rawText,
            primaryUrl = "https://rides.sng.link/Aw5zn/hw3r",
            finalUrl = "https://uber-card-check.example.net/verify-card",
            redirectChain = listOf(
                "https://rides.sng.link/Aw5zn/hw3r",
                "https://uber-card-check.example.net/verify-card"
            )
        )

        assertCodes(
            snapshot,
            EvidenceCode.APPROVED_TRACKER_DOMAIN,
            EvidenceCode.BRAND_IMPERSONATION,
            EvidenceCode.OFFICIAL_DOMAIN_MISMATCH,
            EvidenceCode.CARD_REQUEST
        )
        assertFalse(snapshot.signals.any { it.code == EvidenceCode.OFFICIAL_DOMAIN_EXACT && it.targetKey.contains("sng.link") })
        assertEquals("https://uber-card-check.example.net/verify-card", snapshot.finalUrl)
        assertEquals(GateAction.DO_NOT_CONTINUE, gate.evaluate(snapshot).action)
    }

    @Test
    fun virusTotalCleanIsNonDecisiveButMapped() {
        val snapshot = normalize(
            rawText = "Verifica linkul https://example.com",
            finalUrl = "https://example.com",
            threatIntel = listOf(
                ThreatIntelSourceResult(
                    source = "VirusTotal",
                    verdict = "Clean",
                    severity = "low",
                    details = "Engines: malicious=0, suspicious=0, undetected=65"
                )
            ),
            virusTotalConfigured = true
        )

        assertCodes(snapshot, EvidenceCode.VIRUSTOTAL_LOW_OR_NO_DETECTION)
        assertEquals(ProviderStatus.OK, snapshot.providerStates[ProviderId.VIRUSTOTAL]?.status)
        assertEquals(GateAction.INSUFFICIENT_EVIDENCE, gate.evaluate(snapshot).action)
    }

    @Test
    fun virusTotalMaliciousConsensusIsMapped() {
        val snapshot = normalize(
            rawText = "Verifica linkul https://bad.example.net",
            finalUrl = "https://bad.example.net",
            threatIntel = listOf(
                ThreatIntelSourceResult(
                    source = "VirusTotal",
                    verdict = "Malicious",
                    severity = "high",
                    details = "Engines: total=70, malicious=4, suspicious=1"
                )
            ),
            virusTotalConfigured = true
        )

        assertCodes(snapshot, EvidenceCode.VIRUSTOTAL_MALICIOUS_CONSENSUS)
        assertEquals(GateAction.DO_NOT_CONTINUE, gate.evaluate(snapshot).action)
    }

    @Test
    fun marketplaceReceiveMoneyWithOtpMapsToNoEnterData() {
        val snapshot = normalize(
            rawText = "OLX: ca sa primesti banii, introdu cardul si codul OTP primit prin SMS."
        )

        assertCodes(snapshot, EvidenceCode.MARKETPLACE_RECEIVE_MONEY, EvidenceCode.CARD_REQUEST, EvidenceCode.OTP_REQUEST)
        assertEquals(GateAction.NO_ENTER_DATA, gate.evaluate(snapshot).action)
    }

    private fun normalize(
        rawText: String,
        htmlContent: String? = null,
        primaryUrl: String? = null,
        finalUrl: String? = null,
        redirectChain: List<String> = emptyList(),
        threatIntel: List<ThreatIntelSourceResult> = emptyList(),
        virusTotalConfigured: Boolean = false
    ): EvidenceSnapshot {
        return EvidenceSignalNormalizer.buildSnapshot(
            EvidenceNormalizerInput(
                inputKind = "unit_test",
                channel = if (htmlContent != null) "email_html" else "text",
                rawText = rawText,
                htmlContent = htmlContent,
                primaryUrl = primaryUrl,
                finalUrl = finalUrl,
                redirectChain = redirectChain,
                threatIntel = threatIntel,
                virusTotalConfigured = virusTotalConfigured
            )
        )
    }

    private fun assertCodes(snapshot: EvidenceSnapshot, vararg expected: EvidenceCode) {
        val actual = snapshot.signals.map { it.code }.toSet()
        expected.forEach { code ->
            assertTrue("Missing $code in $actual", actual.contains(code))
        }
    }
}
