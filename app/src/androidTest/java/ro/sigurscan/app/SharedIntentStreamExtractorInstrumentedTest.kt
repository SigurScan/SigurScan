package ro.sigurscan.app

import android.content.ClipData
import android.content.Intent
import android.net.Uri
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.assertEquals
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class SharedIntentStreamExtractorInstrumentedTest {
    @Test
    fun actionSendReadsSingleStreamUri() {
        val uri = Uri.parse("content://ro.sigurscan.test/share/email.eml")
        val intent = Intent(Intent.ACTION_SEND)
            .setType("message/rfc822")
            .putExtra(Intent.EXTRA_STREAM, uri)

        assertEquals(listOf(uri), collectSharedStreamUris(intent))
    }

    @Test
    fun actionSendMultipleReadsAllStreamUris() {
        val first = Uri.parse("content://ro.sigurscan.test/share/one.pdf")
        val second = Uri.parse("content://ro.sigurscan.test/share/two.png")
        val intent = Intent(Intent.ACTION_SEND_MULTIPLE)
            .setType("*/*")
            .putParcelableArrayListExtra(Intent.EXTRA_STREAM, arrayListOf(first, second))

        assertEquals(listOf(first, second), collectSharedStreamUris(intent))
    }

    @Test
    fun clipDataUrisAreIncludedAndDeduplicated() {
        val stream = Uri.parse("content://ro.sigurscan.test/share/body.html")
        val clipOnly = Uri.parse("content://ro.sigurscan.test/share/attachment.pdf")
        val contentResolver = InstrumentationRegistry.getInstrumentation()
            .targetContext
            .contentResolver
        val intent = Intent(Intent.ACTION_SEND)
            .setType("text/html")
            .putExtra(Intent.EXTRA_STREAM, stream)
        intent.clipData = ClipData.newUri(
            contentResolver,
            "SigurScan share",
            stream
        ).apply {
            addItem(ClipData.Item(clipOnly))
        }

        assertEquals(listOf(stream, clipOnly), collectSharedStreamUris(intent))
    }
}
