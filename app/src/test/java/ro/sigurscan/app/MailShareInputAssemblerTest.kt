package ro.sigurscan.app

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class MailShareInputAssemblerTest {

    @Test
    fun yahooMailShellResourcesDoNotBecomeHiddenMailLinks() {
        val yahooShell = """
            <!DOCTYPE html>
            <html id="Atom" lang="ro-RO" dir="ltr">
              <body dir="ltr" class="bold-focus pointer-mode">
                <div id="mail-app-container" data-reactroot></div>
                <script async defer crossorigin="anonymous" src="https://s.yimg.com/cx/pv/perf-vitals_3.5.0.js"></script>
                <script src="https://s.yimg.com/ng/nv/js/ym/2.0.0-snapshot.147429867/ymanalytics-core.js" async></script>
                <iframe frameborder="0" height="0" width="0" src="https://opus.analytics.yahoo.com/tag/opus-frame.html?referer=https%3A%2F%2Fmail.yahoo.com%2F&app=DBAA" style="display: none;"></iframe>
              </body>
            </html>
        """.trimIndent()

        val extractedLinks = HtmlLinkExtractor.extractHtmlLinks(yahooShell)
        assertTrue("The generic extractor should still see resource URLs", extractedLinks.isNotEmpty())

        val assembled = MailShareInputAssembler.buildMailScanInput(
            rawText = yahooShell,
            links = extractedLinks,
            sourceLabel = "Conținut HTML partajat"
        )

        assertFalse(assembled.contains("SCANARE MAIL:"))
        assertFalse(assembled.contains("URL-uri ascunse/expuse detectate"))
        assertFalse(assembled.contains("s.yimg.com"))
        assertFalse(assembled.contains("opus.analytics.yahoo.com"))
    }
}
