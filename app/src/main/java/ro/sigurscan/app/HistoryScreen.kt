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
fun HistoryTab(viewModel: ScannerViewModel) {
    Column(modifier = Modifier.fillMaxSize().padding(20.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(bottom = 20.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.History, contentDescription = null, tint = SigurColors.Brand)
                Spacer(modifier = Modifier.width(8.dp))
                Text("Istoric Scanări", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = SigurColors.TextPrimary)
            }
            if (viewModel.historyItems.isNotEmpty()) {
                Text(
                    "Șterge tot",
                    color = SigurColors.Dangerous,
                    fontSize = 12.sp,
                    modifier = Modifier.clickable { viewModel.clearHistory() }
                )
            }
        }

        if (viewModel.historyItems.isEmpty()) {
            Card(
                modifier = Modifier.fillMaxSize(),
                colors = CardDefaults.cardColors(containerColor = SigurColors.BackgroundCard),
                shape = DSCardShape,
                border = DSCardBorder
            ) {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Icon(Icons.Default.History, contentDescription = null, modifier = Modifier.size(64.dp), tint = SigurColors.TextSubtle)
                        Spacer(modifier = Modifier.height(16.dp))
                        Text("Nicio scanare efectuată", color = SigurColors.TextPrimary, fontWeight = FontWeight.Bold)
                        Text(
                            "Istoricul scanărilor tale va fi salvat local, în siguranță pe dispozitiv.",
                            color = SigurColors.TextSecondary,
                            fontSize = 13.sp,
                            textAlign = TextAlign.Center,
                            modifier = Modifier.padding(horizontal = 40.dp)
                        )
                    }
                }
            }
        } else {
            LazyColumn {
                items(viewModel.historyItems) { item ->
                    HistoryItemCard(item, onClick = { viewModel.assessment = item; viewModel.currentTab = "scan" }, onDelete = { viewModel.deleteHistoryItem(item) })
                }
            }
        }
    }
}

@Composable
fun HistoryItemCard(item: OfflineAssessment, onClick: () -> Unit, onDelete: () -> Unit) {
    val risk = mapRiskDisplayState(item)
    val chipTone = when (risk.color) {
        SigurColors.Dangerous -> DSChipTone.Danger
        SigurColors.Safe -> DSChipTone.Safe
        SigurColors.Brand -> DSChipTone.Pending
        else -> DSChipTone.Suspect
    }

    Card(
        modifier = Modifier.fillMaxWidth().padding(vertical = 6.dp).clickable { onClick() },
        colors = CardDefaults.cardColors(containerColor = SigurColors.BackgroundCard),
        shape = DSCardShape,
        border = DSCardBorder
    ) {
        Row(modifier = Modifier.padding(16.dp)) {
            Column(modifier = Modifier.weight(1f)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    DSChip(text = risk.label.uppercase(Locale.getDefault()), tone = chipTone)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = SimpleDateFormat("dd.MM.yyyy HH:mm", Locale.getDefault()).format(Date(item.timestamp)),
                        color = SigurColors.TextMuted,
                        fontSize = 11.sp
                    )
                }
                Spacer(modifier = Modifier.height(8.dp))
                Text("Clasificare: ${item.family}", color = SigurColors.TextPrimary, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                Text(publicHistorySummary(item), color = SigurColors.TextSecondary, fontSize = 12.sp, maxLines = 1)
            }
            IconButton(onClick = onDelete) {
                Icon(Icons.Default.Delete, contentDescription = null, tint = SigurColors.Dangerous.copy(alpha = 0.70f), modifier = Modifier.size(18.dp))
            }
        }
    }
}

internal fun publicHistorySummary(item: OfflineAssessment): String {
    item.finalUrl?.let { return "Link analizat: ${it.take(72)}" }
    return when {
        item.originalText.startsWith("scan=", ignoreCase = true) -> "Conținut analizat local, detalii redactate"
        item.originalText.contains("Scanare imagine", ignoreCase = true) -> "Imagine analizată"
        item.originalText.contains("Scanare PDF", ignoreCase = true) -> "PDF analizat"
        item.originalText.contains("Scanare email", ignoreCase = true) -> "E-mail analizat"
        item.originalText.contains("Fișier", ignoreCase = true) -> "Fișier analizat"
        else -> "Mesaj analizat, conținut redactat"
    }
}
