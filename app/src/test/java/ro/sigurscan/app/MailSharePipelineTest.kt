package ro.sigurscan.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class MailSharePipelineTest {

    private data class Scenario(
        val name: String,
        val rawMessage: String,
        val expectedLinks: List<String>,
        val mustContainText: List<String> = emptyList()
    )

    private fun buildPlainEmail(htmlBody: String): String {
        return """
            From: attacks@malicious.test
            To: user@example.com
            Subject: Urgent: Actiune necesara
            Content-Type: text/html; charset="UTF-8"

            $htmlBody
        """.trimIndent()
    }

    private fun buildMultipartEmail(plainBody: String, htmlBody: String): String {
        return """
            From: attacks@malicious.test
            To: user@example.com
            Subject: Confirmare cont
            MIME-Version: 1.0
            Content-Type: multipart/alternative; boundary="scan-mp-boundary"

            --scan-mp-boundary
            Content-Type: text/plain; charset="UTF-8"
            Content-Transfer-Encoding: quoted-printable

            $plainBody
            --scan-mp-boundary
            Content-Type: text/html; charset="UTF-8"

            $htmlBody
            --scan-mp-boundary--
        """.trimIndent()
    }

    private fun runScenario(scenario: Scenario) {
        val parsed = EmailMessageParser.parse(scenario.rawMessage)
        val htmlForExtraction = parsed.htmlText.ifBlank { parsed.plainText }
        val extractedLinks = HtmlLinkExtractor.extractHtmlLinks(htmlForExtraction)

        assertEquals(
            "Could not parse all expected links for: ${scenario.name}",
            scenario.expectedLinks.toSet(),
            extractedLinks.filter { it in scenario.expectedLinks }.toSet()
        )

        val assembledInput = MailShareInputAssembler.buildMailScanInput(
            parsed.bodyForAnalysis,
            extractedLinks,
            "Email Share Test"
        )

        assertTrue(
            "Expected assembled payload header for: ${scenario.name}",
            assembledInput.contains("SCANARE MAIL: Email Share Test")
        )

        scenario.expectedLinks.forEach { expected ->
            assertTrue(
                "Expected hidden/visible link missing for ${scenario.name}: $expected",
                assembledInput.contains(expected)
            )
        }
        scenario.mustContainText.forEach { expectedText ->
            assertTrue(
                "Expected text missing for ${scenario.name}: $expectedText",
                assembledInput.contains(expectedText)
            )
        }
    }

    @Test
    fun testMailScamScenarios_18Plus_detectedLinksAndPayload() {
        val scenarios = listOf(
            Scenario(
                name = "Button onclick direct location",
                rawMessage = buildPlainEmail(
                    """
                    <html>
                      <body>
                        <p>Click aici pentru securizare</p>
                        <button onclick="window.location.href='https://scam-bank.example.com/verify'">Verifica</button>
                      </body>
                    </html>
                    """.trimIndent()
                ),
                expectedLinks = listOf("https://scam-bank.example.com/verify"),
                mustContainText = listOf("Click aici pentru securizare", "Verifica")
            ),
            Scenario(
                name = "Button onclick with window.open + base64",
                rawMessage = buildPlainEmail(
                    """
                    <html>
                      <body>
                        <button onclick="window.open(atob('aHR0cHM6Ly9wcm9uY2UuZXhhbXBsZS5uZXQvaW9uZXQ/cD05'))">Actualizeaza</button>
                      </body>
                    </html>
                    """.trimIndent()
                ),
                expectedLinks = listOf("https://pronce.example.net/ionet?p=9")
            ),
            Scenario(
                name = "Form action + formaction fallback",
                rawMessage = buildPlainEmail(
                    """
                    <html>
                      <form action="https://form.example.net/login" onsubmit="return false;">
                        <button formaction="https://fallback.example.net/submit">Trimite</button>
                      </form>
                    </html>
                    """.trimIndent()
                ),
                expectedLinks = listOf("https://form.example.net/login", "https://fallback.example.net/submit")
            ),
            Scenario(
                name = "Data attributes and onclick on container",
                rawMessage = buildPlainEmail(
                    """
                    <html>
                      <div data-url="https://data-url.example.net/track" onclick="location.href=this.dataset.url">Deschide</div>
                    </html>
                    """.trimIndent()
                ),
                expectedLinks = listOf("https://data-url.example.net/track")
            ),
            Scenario(
                name = "Meta refresh redirect",
                rawMessage = buildPlainEmail(
                    """
                    <html>
                      <head>
                        <meta http-equiv="refresh" content="0;url=https://meta-redirect.example.org/pay" />
                      </head>
                      <body>Confirma taxa</body>
                    </html>
                    """.trimIndent()
                ),
                expectedLinks = listOf("https://meta-redirect.example.org/pay"),
                mustContainText = listOf("Confirma taxa")
            ),
            Scenario(
                name = "Script variable assignment + window.location",
                rawMessage = buildPlainEmail(
                    """
                    <html>
                      <body>
                        <script>
                          const base = 'https://script.example.net';
                          window.location.replace(base + '/unlock');
                        </script>
                      </body>
                    </html>
                    """.trimIndent()
                ),
                expectedLinks = listOf("https://script.example.net/unlock")
            ),
            Scenario(
                name = "Template literal in script",
                rawMessage = buildPlainEmail(
                    """
                    <html>
                      <script>
                        const host = 'template-mail.example.com';
                        window.location.href = `https://${'$'}{host}/suspicious`;
                      </script>
                    </html>
                    """.trimIndent()
                ),
                expectedLinks = listOf("https://template-mail.example.com/suspicious")
            ),
            Scenario(
                name = "String concatenation",
                rawMessage = buildPlainEmail(
                    """
                    <html>
                      <a onclick="window.location='https://' + 'concat-mail' + '.example.com' + '/verify'">Verifica contul</a>
                    </html>
                    """.trimIndent()
                ),
                expectedLinks = listOf("https://concat-mail.example.com/verify")
            ),
            Scenario(
                name = "Decode URI in script handler",
                rawMessage = buildPlainEmail(
                    """
                    <html>
                      <button onclick="window.location.assign(decodeURIComponent('https%3A%2F%2Fdecode-uri.example.net%2Fsecure%3Fq%3D1'))">
                        Urgent
                      </button>
                    </html>
                    """.trimIndent()
                ),
                expectedLinks = listOf("https://decode-uri.example.net/secure?q=1")
            ),
            Scenario(
                name = "Unescape in mouseover",
                rawMessage = buildPlainEmail(
                    """
                    <html>
                      <div onmouseover="location.href=unescape('https%3A%2F%2Funescape-mail.example.net%2Fwarning')">Muta cursorul</div>
                    </html>
                    """.trimIndent()
                ),
                expectedLinks = listOf("https://unescape-mail.example.net/warning")
            ),
            Scenario(
                name = "Entity encoded anchor",
                rawMessage = buildPlainEmail(
                    """
                    <html>
                      <a href="https://&#x73;&#x70;&#x61;&#x6d;&#x2e;&#x65;&#x78;&#x61;&#x6d;&#x70;&#x6c;&#x65;&#x2e;&#x63;&#x6f;&#x6d;/claim">Spam claim</a>
                    </html>
                    """.trimIndent()
                ),
                expectedLinks = listOf("https://spam.example.com/claim")
            ),
            Scenario(
                name = "Image src and srcset extraction",
                rawMessage = buildPlainEmail(
                    """
                    <html>
                      <img src="https://assets.safeexample.net/banner.png" srcset="/fallback.png 1x, https://assets.safeexample.net/banner@2x.png 2x"/>
                    </html>
                    """.trimIndent()
                ),
                expectedLinks = listOf("https://assets.safeexample.net/banner.png", "https://assets.safeexample.net/banner@2x.png"),
                mustContainText = listOf("banner@2x.png")
            ),
            Scenario(
                name = "Iframe and style background URL",
                rawMessage = buildPlainEmail(
                    """
                    <html>
                      <style>body { background: url('https://styles.example.org/background.jpg'); }</style>
                      <iframe src="https://iframe.example.org/widget"></iframe>
                    </html>
                    """.trimIndent()
                ),
                expectedLinks = listOf("https://styles.example.org/background.jpg", "https://iframe.example.org/widget")
            ),
            Scenario(
                name = "CSS import",
                rawMessage = buildPlainEmail(
                    """
                    <html>
                      <style>
                        @import url("https://css-remote.example.net/theme.css");
                      </style>
                    </html>
                    """.trimIndent()
                ),
                expectedLinks = listOf("https://css-remote.example.net/theme.css")
            ),
            Scenario(
                name = "Multipart fallback should use HTML part",
                rawMessage = buildMultipartEmail(
                    plainBody = "Text clar: actualizeaza plata.",
                    htmlBody = """
                        <html>
                          <body>
                            <a href="https://multipart.example.com/verify">Verifica</a>
                          </body>
                        </html>
                    """.trimIndent()
                ),
                expectedLinks = listOf("https://multipart.example.com/verify"),
                mustContainText = listOf("Text clar")
            ),
            Scenario(
                name = "Self/parent location assignment",
                rawMessage = buildPlainEmail(
                    """
                    <html>
                      <button onclick="parent.location='https://parent-location.example.com/redirect'">Click</button>
                    </html>
                    """.trimIndent()
                ),
                expectedLinks = listOf("https://parent-location.example.com/redirect")
            ),
            Scenario(
                name = "Action link plus onsubmit",
                rawMessage = buildPlainEmail(
                    """
                    <html>
                      <form action="https://form-action.example.net/start" onsubmit="window.location='https://submit.example.net/callback';return false;">
                        <input type="submit" value="Trimite">
                      </form>
                    </html>
                    """.trimIndent()
                ),
                expectedLinks = listOf("https://form-action.example.net/start", "https://submit.example.net/callback")
            ),
            Scenario(
                name = "onkeydown and top.location",
                rawMessage = buildPlainEmail(
                    """
                    <html>
                      <button id="btn" onkeydown="top.location='https://keyboard.example.net/alert'">Apeleaza</button>
                    </html>
                    """.trimIndent()
                ),
                expectedLinks = listOf("https://keyboard.example.net/alert")
            ),
            Scenario(
                name = "Encoded URL in style data and anchor",
                rawMessage = buildPlainEmail(
                    """
                    <html>
                      <a href="https://encode.example.net/login">Intra</a>
                      <div style="background:url('https%3A%2F%2Fstyle-url.example.net%2Fpixel.gif')"></div>
                    </html>
                    """.trimIndent()
                ),
                expectedLinks = listOf("https://encode.example.net/login")
            ),
            Scenario(
                name = "Plain anchor fallback",
                rawMessage = buildPlainEmail(
                    """
                    <html>
                      <a href="https://plain-link.example.net/verify">Verifica-ti contul</a>
                    </html>
                    """.trimIndent()
                ),
                expectedLinks = listOf("https://plain-link.example.net/verify"),
                mustContainText = listOf("Verifica-ti contul")
            ),
            Scenario(
                name = "Input formaction extraction",
                rawMessage = buildPlainEmail(
                    """
                    <html>
                      <input type="submit" formaction="https://input-formaction.example.net/update" />
                    </html>
                    """.trimIndent()
                ),
                expectedLinks = listOf("https://input-formaction.example.net/update")
            ),
            Scenario(
                name = "Data-link attribute extraction",
                rawMessage = buildPlainEmail(
                    """
                    <html>
                      <button data-link="https://data-link.example.net/track">Click</button>
                    </html>
                    """.trimIndent()
                ),
                expectedLinks = listOf("https://data-link.example.net/track")
            ),
            Scenario(
                name = "Outlook SafeLinks unwraps target URL",
                rawMessage = buildPlainEmail(
                    """
                    <html>
                      <a href="https://eur03.safelinks.protection.outlook.com/?url=https%3A%2F%2Frevolut-login.example.net%2Funlock%3Fcase%3D42&amp;data=05%7C01%7Cdemo">Deblocheaza Revolut</a>
                    </html>
                    """.trimIndent()
                ),
                expectedLinks = listOf("https://revolut-login.example.net/unlock?case=42"),
                mustContainText = listOf("Deblocheaza Revolut")
            ),
            Scenario(
                name = "Google and Facebook redirect wrappers expose final destination",
                rawMessage = buildPlainEmail(
                    """
                    <html>
                      <a href="https://www.google.com/url?q=https%3A%2F%2Fanaf-plata.example.org%2Fspv&amp;sa=D">ANAF SPV</a>
                      <a href="https://facebook.com/l.php?u=https%3A%2F%2Folx-pay.example.net%2Fconfirm&amp;h=abc">Confirma plata</a>
                    </html>
                    """.trimIndent()
                ),
                expectedLinks = listOf(
                    "https://anaf-plata.example.org/spv",
                    "https://olx-pay.example.net/confirm"
                )
            ),
            Scenario(
                name = "Proofpoint URLDefense v3 unwraps double-underscore URL",
                rawMessage = buildPlainEmail(
                    """
                    <html>
                      <a href="https://urldefense.com/v3/__https://bt24-login.example.com/session?id=7__;!!token!abc">BT24</a>
                    </html>
                    """.trimIndent()
                ),
                expectedLinks = listOf("https://bt24-login.example.com/session?id=7")
            ),
            Scenario(
                name = "Yahoo Mail RU redirect unwraps target URL",
                rawMessage = buildPlainEmail(
                    """
                    <html>
                      <a href="https://r.mail.yahoo.com/delivery/RU=https%3A%2F%2Fyahoo-hidden.example.net%2Fclaim%3Fid%3D99/RK=2/RS=abc">Ridica premiul</a>
                    </html>
                    """.trimIndent()
                ),
                expectedLinks = listOf("https://yahoo-hidden.example.net/claim?id=99"),
                mustContainText = listOf("Ridica premiul")
            ),
            Scenario(
                name = "CSS percent-encoded url and SVG xlink extraction",
                rawMessage = buildPlainEmail(
                    """
                    <html>
                      <div style="background-image:url('https%3A%2F%2Fcss-hidden.example.net%2Fpixel.gif')">Oferta</div>
                      <svg><a xlink:href="https://svg-hidden.example.net/claim"><text>Premiu</text></a></svg>
                    </html>
                    """.trimIndent()
                ),
                expectedLinks = listOf(
                    "https://css-hidden.example.net/pixel.gif",
                    "https://svg-hidden.example.net/claim"
                )
            ),
            Scenario(
                name = "Data URI HTML payload exposes nested phishing link",
                rawMessage = buildPlainEmail(
                    """
                    <html>
                      <iframe src="data:text/html,%3Ca%20href%3D%22https%3A%2F%2Fdata-uri.example.net%2Fcard%22%3ECard%3C%2Fa%3E"></iframe>
                    </html>
                    """.trimIndent()
                ),
                expectedLinks = listOf("https://data-uri.example.net/card")
            ),
            Scenario(
                name = "Invisible obfuscation is removed from visible brand text",
                rawMessage = buildPlainEmail(
                    """
                    <html>
                      <p>O<!-- stealth -->L&#8203;X: plata este blocata.</p>
                      <a href="https://olx-payments.example.net/confirm">Continua</a>
                    </html>
                    """.trimIndent()
                ),
                expectedLinks = listOf("https://olx-payments.example.net/confirm"),
                mustContainText = listOf("OLX: plata este blocata.")
            )
        )

        scenarios.forEach { runScenario(it) }
        assertTrue("Should run at least 18 scenarios", scenarios.size >= 18)
    }
}
