package ro.sigurscan.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class SandboxPreviewModelTest {
    @Test
    fun sandboxPreviewDoesNotUseFaviconFallbackBeforeScreenshotExists() {
        assertNull(sandboxScreenshotModel(null))
    }

    @Test
    fun sandboxPreviewUsesUrlscanScreenshotWhenAvailable() {
        assertEquals(
            "https://urlscan.io/screenshots/scan-id.png",
            sandboxScreenshotModel("https://urlscan.io/screenshots/scan-id.png")
        )
    }

    @Test
    fun sandboxPreviewKeepsLocalPrivateScreenshotUriUnchanged() {
        assertEquals(
            "file:///data/user/0/ro.sigurscan.app/cache/urlscan-screenshots/scan-id.png",
            sandboxScreenshotModel("file:///data/user/0/ro.sigurscan.app/cache/urlscan-screenshots/scan-id.png")
        )
    }

    @Test
    fun urlscanScreenshotUrlPointsToPublicScreenshotAsset() {
        assertEquals(
            "https://urlscan.io/screenshots/019e8715-bb13-75e8-ab41-ddb55713c24e.png",
            urlscanScreenshotUrl("019e8715-bb13-75e8-ab41-ddb55713c24e")
        )
    }
}
