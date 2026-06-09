package ro.sigurscan.app

import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class AndroidUrlExtractorCompatibilityTest {
    @Test
    fun textAndHtmlExtractorsInitializeAndExtractOnAndroid() {
        val textLinks = UrlTextExtractor.extract(
            "Vezi oferta la https://www.hipo.ro/ADT_TM"
        )
        val htmlLinks = HtmlLinkExtractor.extractHtmlLinks(
            """<a href="https://www.hipo.ro/ADT_TM">Înscrie-te</a>"""
        )

        assertTrue(textLinks.contains("https://www.hipo.ro/ADT_TM"))
        assertTrue(htmlLinks.contains("https://www.hipo.ro/ADT_TM"))
    }
}
