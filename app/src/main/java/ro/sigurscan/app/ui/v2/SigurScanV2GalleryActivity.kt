package ro.sigurscan.app.ui.v2

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.ChevronRight
import androidx.compose.material3.Icon
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.unit.dp
import ro.sigurscan.app.ui.v2.components.BottomNavTabV2
import ro.sigurscan.app.ui.v2.screens.InvoiceVerdictScreenV2
import ro.sigurscan.app.ui.v2.screens.InvoiceVerdictSampleDataV2
import ro.sigurscan.app.ui.v2.screens.ScanScreenV2
import ro.sigurscan.app.ui.v2.screens.VerdictSampleDataV2
import ro.sigurscan.app.ui.v2.screens.VerdictScreenV2
import ro.sigurscan.app.ui.v2.theme.SigurTokensV2
import ro.sigurscan.app.ui.v2.theme.SigurScanV2Theme
import ro.sigurscan.app.ui.v2.theme.TypeV2

/**
 * Standalone entry point for previewing/testing the v2 screens on a real
 * device without touching MainActivity's existing navigation graph.
 * Launch with: adb shell am start -n ro.sigurscan.app/.ui.v2.SigurScanV2GalleryActivity
 */
class SigurScanV2GalleryActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            SigurScanV2Theme {
                GalleryRootV2()
            }
        }
    }
}

private enum class GalleryScreenV2(val label: String) {
    MENU("Meniu"),
    SCAN("01 · Scanează"),
    SIGUR("02 · Sigur"),
    NEVERIFICAT("03 · Neverificat"),
    SUSPECT("04 · Suspect"),
    PERICULOS("05 · Periculos"),
    FACTURA_SIGUR("06 · Factură — Sigur"),
    FACTURA_NEVERIFICAT("07 · Factură — Neverificat"),
    FACTURA_SUSPECT("08 · Factură — Suspect"),
    FACTURA_PERICULOS("09 · Factură — Periculos"),
}

@Composable
private fun GalleryRootV2() {
    var screen by remember { mutableStateOf(GalleryScreenV2.MENU) }
    val goBack = { screen = GalleryScreenV2.MENU }
    val nav: (BottomNavTabV2) -> Unit = { if (it != BottomNavTabV2.SCANEAZA) goBack() }
    BackHandler(enabled = screen != GalleryScreenV2.MENU) { goBack() }

    when (screen) {
        GalleryScreenV2.MENU -> GalleryMenuV2 { screen = it }
        GalleryScreenV2.SCAN -> ScanScreenV2(onScan = {}, onScanTypeSelected = {}, onCheckOffer = {}, onNavSelect = nav)
        GalleryScreenV2.SIGUR -> VerdictScreenV2(VerdictSampleDataV2.sigur, onFeedbackYes = {}, onFeedbackNo = {}, onNavSelect = nav)
        GalleryScreenV2.NEVERIFICAT -> VerdictScreenV2(VerdictSampleDataV2.neverificat, onFeedbackYes = {}, onFeedbackNo = {}, onNavSelect = nav)
        GalleryScreenV2.SUSPECT -> VerdictScreenV2(VerdictSampleDataV2.suspect, onFeedbackYes = {}, onFeedbackNo = {}, onNavSelect = nav)
        GalleryScreenV2.PERICULOS -> VerdictScreenV2(VerdictSampleDataV2.periculos, onFeedbackYes = {}, onFeedbackNo = {}, onNavSelect = nav)
        GalleryScreenV2.FACTURA_SIGUR -> InvoiceVerdictScreenV2(InvoiceVerdictSampleDataV2.sigur, onFeedbackYes = {}, onFeedbackNo = {}, onNavSelect = nav)
        GalleryScreenV2.FACTURA_NEVERIFICAT -> InvoiceVerdictScreenV2(InvoiceVerdictSampleDataV2.neverificat, onFeedbackYes = {}, onFeedbackNo = {}, onNavSelect = nav)
        GalleryScreenV2.FACTURA_SUSPECT -> InvoiceVerdictScreenV2(InvoiceVerdictSampleDataV2.suspect, onFeedbackYes = {}, onFeedbackNo = {}, onNavSelect = nav)
        GalleryScreenV2.FACTURA_PERICULOS -> InvoiceVerdictScreenV2(InvoiceVerdictSampleDataV2.periculos, onFeedbackYes = {}, onFeedbackNo = {}, onNavSelect = nav)
    }
}

@Composable
private fun GalleryMenuV2(onSelect: (GalleryScreenV2) -> Unit) {
    Scaffold(containerColor = SigurTokensV2.Canvas) { padding ->
        Column(modifier = Modifier.fillMaxSize().padding(padding).statusBarsPadding().padding(16.dp)) {
            Text("SigurScan v2 — Galerie ecrane", style = TypeV2.SectionTitle, color = SigurTokensV2.Ink)
            Text(
                "Preview izolat, fără să atingă navigația reală a aplicației.",
                style = TypeV2.Caption,
                modifier = Modifier.padding(top = 4.dp, bottom = 16.dp),
            )
            LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                items(GalleryScreenV2.entries.drop(1)) { entry ->
                    GalleryMenuRow(entry) { onSelect(entry) }
                }
            }
        }
    }
}

@Composable
private fun GalleryMenuRow(entry: GalleryScreenV2, onClick: () -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(SigurTokensV2.RadiusCardAlt))
            .background(androidx.compose.ui.graphics.Color.White)
            .clickable(onClick = onClick)
            .padding(horizontal = 16.dp, vertical = 15.dp),
    ) {
        androidx.compose.foundation.layout.Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(entry.label, style = TypeV2.CardTitle, color = SigurTokensV2.Ink)
            Icon(Icons.Rounded.ChevronRight, contentDescription = null, tint = SigurTokensV2.Muted)
        }
    }
}
