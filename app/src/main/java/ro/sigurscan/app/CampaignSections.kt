package ro.sigurscan.app

import android.Manifest
import android.app.role.RoleManager
import android.content.Intent
import android.content.Context
import android.graphics.BitmapFactory
import android.net.Uri
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.provider.Settings.ACTION_APPLICATION_DETAILS_SETTINGS
import android.text.Html
import android.text.Spanned
import android.util.Log
import android.view.ViewGroup.LayoutParams
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.annotation.OptIn as AndroidxOptIn
import androidx.camera.core.Camera
import androidx.camera.core.CameraSelector
import androidx.camera.core.ExperimentalGetImage
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.Preview as CameraPreview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.border
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.ui.draw.clip
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.List
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.em
import androidx.compose.ui.unit.sp
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import androidx.compose.ui.platform.LocalLifecycleOwner
import coil.compose.SubcomposeAsyncImage
import ro.sigurscan.app.ui.theme.SigurScanTheme
import ro.sigurscan.app.ui.theme.SigurColors
import org.json.JSONArray
import org.json.JSONObject
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import com.google.mlkit.vision.barcode.common.Barcode
import com.google.mlkit.vision.barcode.BarcodeScanning
import com.google.mlkit.vision.barcode.BarcodeScannerOptions
import com.google.mlkit.vision.common.InputImage
import java.text.SimpleDateFormat
import java.io.File
import java.util.*
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicBoolean
import kotlin.math.max
import kotlin.math.min
import kotlin.math.pow

@Composable
fun ActiveCampaignBanner(message: String, onDismiss: () -> Unit) {
    Card(
        colors = CardDefaults.cardColors(containerColor = SigurColors.Dangerous),
        shape = DSCardShape,
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.padding(12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(Icons.Default.Campaign, contentDescription = null, tint = Color.White, modifier = Modifier.size(24.dp))
            Spacer(modifier = Modifier.width(12.dp))
            Text(
                text = message,
                color = SigurColors.TextInverse,
                fontSize = 13.sp,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.weight(1f)
            )
            IconButton(onClick = onDismiss, modifier = Modifier.size(24.dp)) {
                Icon(Icons.Default.Close, contentDescription = "Închide", tint = Color.White, modifier = Modifier.size(16.dp))
            }
        }
    }
}

@Composable
fun ActiveCampaignsSection(campaigns: List<ScamCampaign>, isLoading: Boolean) {
    Column(modifier = Modifier.fillMaxWidth()) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(Icons.Default.Radar, contentDescription = null, tint = SigurColors.Brand, modifier = Modifier.size(18.dp))
            Spacer(modifier = Modifier.width(8.dp))
            Text("Alerte Active în România", color = SigurColors.TextPrimary, fontWeight = FontWeight.Bold, fontSize = 16.sp)
        }

        Spacer(modifier = Modifier.height(12.dp))

        if (isLoading) {
            LinearProgressIndicator(modifier = Modifier.fillMaxWidth(), color = SigurColors.Brand)
        } else if (campaigns.isEmpty()) {
            Text("Nicio alertă majoră în ultimele 24h.", color = SigurColors.TextMuted, fontSize = 12.sp)
        } else {
            campaigns.forEach { campaign ->
                CampaignItem(campaign)
                Spacer(modifier = Modifier.height(8.dp))
            }
        }
    }
}

@Composable
fun CampaignItem(campaign: ScamCampaign) {
    val context = LocalContext.current

    Card(
        colors = CardDefaults.cardColors(containerColor = SigurColors.BackgroundCard),
        border = DSCardBorder,
        shape = DSCardShape
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                DSChip(
                    text = campaign.risk.uppercase(),
                    tone = if (campaign.risk == "dangerous") DSChipTone.Danger else DSChipTone.Suspect
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(campaign.title, color = SigurColors.TextPrimary, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                }
            Text(campaign.description, color = SigurColors.TextSecondary, fontSize = 11.sp, maxLines = 2, modifier = Modifier.padding(top = 4.dp))

                campaign.count.takeIf { it > 0 }?.let { scanCount ->
                Spacer(modifier = Modifier.height(10.dp))
                Text(
                    text = "Număr scanări: $scanCount",
                    color = SigurColors.TextSecondary,
                    fontSize = 10.sp
                )
            }

            campaign.lastSeenText.takeIf { it.isNotBlank() }?.let { lastSeen ->
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "Ultima activitate: $lastSeen",
                    color = SigurColors.TextMuted,
                    fontSize = 10.sp
                )
            }

            campaign.region?.takeIf { it.isNotBlank() }?.let { region ->
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "Regiune: $region",
                    color = SigurColors.TextMuted,
                    fontSize = 10.sp
                )
            }

            if (campaign.lat != null && campaign.lon != null) {
                Spacer(modifier = Modifier.height(10.dp))
                Button(
                    onClick = {
                        openCampaignOnMap(context, campaign.lat, campaign.lon, campaign.title)
                    },
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(containerColor = SigurColors.BrandTint),
                    border = BorderStroke(1.dp, SigurColors.Brand),
                    shape = DSPillShape
                ) {
                    Icon(Icons.Default.Place, contentDescription = null, tint = SigurColors.Brand, modifier = Modifier.size(14.dp))
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        "Vezi pe hartă",
                        color = SigurColors.Brand,
                        fontSize = 11.sp
                    )
                }
            }
        }
    }
}

internal fun openCampaignOnMap(context: android.content.Context, lat: Double?, lon: Double?, title: String) {
    if (lat == null || lon == null) return
    val uri = Uri.parse("geo:$lat,$lon?q=$lat,$lon(${Uri.encode(title)})")
    try {
        val mapIntent = Intent(Intent.ACTION_VIEW, uri)
        context.startActivity(mapIntent)
    } catch (_: Exception) {
        try {
            val browserUri = Uri.parse("https://www.google.com/maps/search/?api=1&query=${lat},${lon}")
            val browserIntent = Intent(Intent.ACTION_VIEW, browserUri)
            context.startActivity(browserIntent)
        } catch (_: Exception) {
            // no-op; action unavailable in this environment
        }
    }
}
