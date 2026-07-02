package ro.sigurscan.app.ui.v2.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Bolt
import androidx.compose.material.icons.rounded.ChevronRight
import androidx.compose.material.icons.rounded.Description
import androidx.compose.material.icons.rounded.Image
import androidx.compose.material.icons.rounded.Link
import androidx.compose.material.icons.rounded.LocalOffer
import androidx.compose.material.icons.rounded.QrCodeScanner
import androidx.compose.material.icons.rounded.ReceiptLong
import androidx.compose.material3.Icon
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextField
import androidx.compose.material3.TextFieldDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import ro.sigurscan.app.ui.v2.components.AppHeaderV2
import ro.sigurscan.app.ui.v2.components.BottomNavBarV2
import ro.sigurscan.app.ui.v2.components.BottomNavTabV2
import ro.sigurscan.app.ui.v2.components.CardOutlinedV2
import ro.sigurscan.app.ui.v2.theme.SigurTokensV2
import ro.sigurscan.app.ui.v2.theme.TypeV2

private data class ScanTypeOption(val icon: ImageVector, val title: String, val subtitle: String)

private val scanTypeOptions = listOf(
    ScanTypeOption(Icons.Rounded.Image, "Încarcă Screenshot", "Analiză text & OCR"),
    ScanTypeOption(Icons.Rounded.Description, "Email / PDF", "Analiză fișiere"),
    ScanTypeOption(Icons.Rounded.QrCodeScanner, "Scanează Cod QR", "Scanare live din cameră"),
    ScanTypeOption(Icons.Rounded.ReceiptLong, "Scanează Factură", "Poză sau fișier"),
)

/** Screen 1 · Scanează — ported from `SigurScan v2.html` §01, faithful to ScanScreen.kt. */
@Composable
fun ScanScreenV2(
    onScan: (String) -> Unit,
    onScanTypeSelected: (String) -> Unit,
    onCheckOffer: () -> Unit,
    modifier: Modifier = Modifier,
    selectedNavTab: BottomNavTabV2 = BottomNavTabV2.SCANEAZA,
    onNavSelect: (BottomNavTabV2) -> Unit = {},
) {
    var query by remember { mutableStateOf("") }
    val looksLikeLink = query.contains("http") || query.contains("www.") || query.contains(".ro") || query.contains(".com")

    Scaffold(
        modifier = modifier,
        containerColor = SigurTokensV2.Canvas,
        bottomBar = { BottomNavBarV2(selected = selectedNavTab, onSelect = onNavSelect) },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 16.dp),
        ) {
            AppHeaderV2()

            // Primary scan card
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(SigurTokensV2.RadiusVerdict))
                    .background(SigurTokensV2.BrandGradient)
                    .padding(18.dp),
            ) {
                Text("Introdu textul sau linkul suspect", style = TypeV2.FeatureHero, color = Color.White)
                Text(
                    "Îți spunem în câteva secunde dacă e o capcană.",
                    style = TypeV2.Body.copy(color = Color.White.copy(alpha = 0.9f)),
                    modifier = Modifier.padding(top = 5.dp),
                )
                TextField(
                    value = query,
                    onValueChange = { query = it },
                    placeholder = { Text("Lipește textul sau URL-ul aici", color = SigurTokensV2.Muted) },
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 14.dp),
                    minLines = 4,
                    keyboardOptions = KeyboardOptions.Default,
                    shape = RoundedCornerShape(16.dp),
                    colors = TextFieldDefaults.colors(
                        focusedContainerColor = Color.White,
                        unfocusedContainerColor = Color.White,
                        focusedIndicatorColor = Color.Transparent,
                        unfocusedIndicatorColor = Color.Transparent,
                    ),
                )
                Row(
                    modifier = Modifier.fillMaxWidth().padding(top = 11.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("${query.length}/2000", style = TypeV2.Caption.copy(color = Color.White.copy(alpha = 0.82f)))
                        if (looksLikeLink) {
                            Row(
                                modifier = Modifier
                                    .padding(start = 8.dp)
                                    .clip(RoundedCornerShape(SigurTokensV2.RadiusPill))
                                    .background(Color.White.copy(alpha = 0.95f))
                                    .padding(horizontal = 9.dp, vertical = 3.dp),
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                Icon(Icons.Rounded.Link, contentDescription = null, tint = SigurTokensV2.Sigur.dark, modifier = Modifier.size(13.dp))
                                Text("Link", style = TypeV2.Eyebrow.copy(color = SigurTokensV2.Sigur.dark), modifier = Modifier.padding(start = 4.dp))
                            }
                        }
                    }
                }
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 13.dp)
                        .clip(RoundedCornerShape(SigurTokensV2.RadiusButton))
                        .background(if (query.isNotBlank()) Color.White else Color.White.copy(alpha = 0.3f))
                        .clickable(enabled = query.isNotBlank()) { onScan(query) }
                        .padding(vertical = 14.dp),
                    horizontalArrangement = Arrangement.Center,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Icon(
                        Icons.Rounded.Bolt,
                        contentDescription = null,
                        tint = if (query.isNotBlank()) SigurTokensV2.Sigur.accent else Color.White,
                        modifier = Modifier.size(19.dp),
                    )
                    Text(
                        "Scanează acum",
                        style = TypeV2.CardTitle.copy(fontSize = 16.sp),
                        color = if (query.isNotBlank()) SigurTokensV2.Sigur.accent else Color.White,
                        modifier = Modifier.padding(start = 8.dp),
                    )
                }
            }

            Text(
                "Sau alege tipul de scanare",
                style = TypeV2.CardTitle.copy(fontSize = 13.sp, letterSpacing = 0.2.sp),
                color = SigurTokensV2.Ink,
                modifier = Modifier.padding(top = 18.dp, bottom = 10.dp, start = 4.dp),
            )

            Column(verticalArrangement = Arrangement.spacedBy(11.dp)) {
                scanTypeOptions.chunked(2).forEach { rowOptions ->
                    Row(horizontalArrangement = Arrangement.spacedBy(11.dp)) {
                        rowOptions.forEach { option ->
                            Box(modifier = Modifier.weight(1f)) {
                                ScanTypeCardV2(option) { onScanTypeSelected(option.title) }
                            }
                        }
                    }
                }
            }

            CardOutlinedV2(
                modifier = Modifier.fillMaxWidth().padding(top = 11.dp).clickable(onClick = onCheckOffer),
                radius = SigurTokensV2.RadiusCardAlt,
                padding = 15.dp,
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        modifier = Modifier
                            .size(46.dp)
                            .clip(RoundedCornerShape(14.dp))
                            .background(SigurTokensV2.Sigur.accent.copy(alpha = 0.13f)),
                        contentAlignment = Alignment.Center,
                    ) {
                        Icon(Icons.Rounded.LocalOffer, contentDescription = null, tint = SigurTokensV2.Sigur.accent, modifier = Modifier.size(23.dp))
                    }
                    Column(modifier = Modifier.padding(start = 13.dp).weight(1f)) {
                        Text("Verifică o ofertă", style = TypeV2.FeatureHero.copy(fontSize = 16.sp), color = SigurTokensV2.Ink)
                        Text(
                            "Avansuri, bilete, chirii, contracte sau plăți cerute rapid",
                            style = TypeV2.Caption,
                            modifier = Modifier.padding(top = 2.dp),
                        )
                    }
                    Icon(Icons.Rounded.ChevronRight, contentDescription = null, tint = SigurTokensV2.ToggleOff)
                }
            }
        }
    }
}

@Composable
private fun ScanTypeCardV2(option: ScanTypeOption, onClick: () -> Unit) {
    CardOutlinedV2(
        modifier = Modifier.fillMaxWidth().clickable(onClick = onClick),
        radius = SigurTokensV2.RadiusCardAlt,
        padding = 15.dp,
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.fillMaxWidth()) {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .clip(RoundedCornerShape(12.dp))
                    .background(SigurTokensV2.Sigur.accent.copy(alpha = 0.14f)),
                contentAlignment = Alignment.Center,
            ) {
                Icon(option.icon, contentDescription = null, tint = SigurTokensV2.Sigur.accent, modifier = Modifier.size(22.dp))
            }
            Text(
                option.title,
                style = TypeV2.CardTitle.copy(fontSize = 13.5.sp, fontWeight = FontWeight.Bold),
                color = SigurTokensV2.Ink,
                modifier = Modifier.padding(top = 10.dp),
            )
            Text(
                option.subtitle,
                style = TypeV2.Caption.copy(fontSize = 11.sp),
                modifier = Modifier.padding(top = 3.dp),
            )
        }
    }
}
