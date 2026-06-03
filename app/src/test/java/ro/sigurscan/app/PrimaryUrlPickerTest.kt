package ro.sigurscan.app

import org.junit.Assert.assertEquals
import org.junit.Test

class PrimaryUrlPickerTest {

    @Test
    fun picksSuspiciousCloneOverManyOfficialSupportLinks() {
        val candidates = listOf(
            "https://www.bcr.ro/ro/persoane-fizice",
            "https://www.bcr.ro/ro/persoane-fizice/contact",
            "https://www.bcr.ro/ro/persoane-fizice/termeni-si-conditii",
            "https://www.bcr.ro/ro/persoane-fizice/protectia-datelor",
            "https://bcr-secure-login.example.net/verify?step=card",
            "https://www.bcr.ro/ro/persoane-fizice/suport"
        )

        val picked = PrimaryUrlPicker.pick(
            candidates = candidates,
            rawText = "BCR: Verifică urgent contul pentru a evita suspendarea."
        )

        assertEquals("https://bcr-secure-login.example.net/verify?step=card", picked)
    }

    @Test
    fun ignoresUnsubscribeWhenChoosingPrimaryUrl() {
        val candidates = listOf(
            "https://newsletter.example.com/unsubscribe?email=user@example.com",
            "https://anaf-plata.example.net/spv/login",
            "https://www.anaf.ro/termeni"
        )

        val picked = PrimaryUrlPicker.pick(
            candidates = candidates,
            rawText = "ANAF: ai o plată nouă în SPV."
        )

        assertEquals("https://anaf-plata.example.net/spv/login", picked)
    }

    @Test
    fun officialOnlyMarketingKeepsOfficialPrimaryUrl() {
        val candidates = listOf(
            "https://www.emag.ro/oferta",
            "https://www.emag.ro/help",
            "https://www.emag.ro/terms"
        )

        val picked = PrimaryUrlPicker.pick(
            candidates = candidates,
            rawText = "eMAG: Nu rata voucherul de weekend."
        )

        assertEquals("https://www.emag.ro/oferta", picked)
    }
}
