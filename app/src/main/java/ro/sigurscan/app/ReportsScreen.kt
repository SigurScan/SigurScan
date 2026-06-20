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
fun ReportsTab(viewModel: ScannerViewModel) {
    val readiness = viewModel.readiness
    val quality = viewModel.quality
    val summary = quality?.summary as? Map<String, Any>
    val falsePositiveCount = viewModel.feedbackSamples?.topFalsePositive?.size ?: 0
    val falseNegativeCount = viewModel.feedbackSamples?.topFalseNegative?.size ?: 0

    fun asFloat(value: Any?): Float {
        return when (value) {
            is Number -> value.toFloat()
            is String -> value.toFloatOrNull() ?: 0f
            else -> 0f
        }
    }

    fun percent(value: Any?): Float {
        val normalized = asFloat(value)
        return if (normalized > 1f) normalized / 100f else normalized
    }

    Column(modifier = Modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text("Rapoarte Detective", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = SigurColors.TextPrimary)
            if (viewModel.reportsLoading) {
                CircularProgressIndicator(modifier = Modifier.size(20.dp), strokeWidth = 2.dp, color = SigurColors.Brand)
            }
        }
        Spacer(modifier = Modifier.height(16.dp))
        
        Card(
            colors = CardDefaults.cardColors(containerColor = SigurColors.BackgroundCard),
            shape = DSCardShape,
            border = DSCardBorder
        ) {
            Column(modifier = Modifier.padding(20.dp)) {
                Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                    Text("Maturitate Detectiv", color = SigurColors.TextPrimary, fontWeight = FontWeight.Bold)
                    val readinessTone = when (readiness?.status) {
                        "healthy" -> DSChipTone.Safe
                        "watch" -> DSChipTone.Suspect
                        else -> DSChipTone.Danger
                    }
                    val readinessLabel = when (readiness?.status) {
                        "healthy" -> "Sănătos"
                        "watch" -> "Atenție"
                        "degraded" -> "Degradat"
                        else -> "Încărcare..."
                    }
                    DSChip(text = readinessLabel.uppercase(Locale.getDefault()), tone = readinessTone)
                }
                Text(
                    text = String.format("%.2f", readiness?.readinessScore ?: 0f),
                    color = SigurColors.Safe,
                    fontSize = 40.sp,
                    fontWeight = FontWeight.Black
                )
                Text("readiness_score (0..1)", color = SigurColors.TextSecondary, fontSize = 12.sp)
                
                Spacer(modifier = Modifier.height(16.dp))
                
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    val qualityScore = readiness?.readinessComponents?.get("quality_score") ?: 0f
                    val coverageScore = readiness?.readinessComponents?.get("coverage_score") ?: 0f
                    Text("Calitate: ${String.format("%.0f%%", qualityScore * 100)}", color = SigurColors.TextPrimary, fontSize = 12.sp)
                    Text("Acoperire: ${String.format("%.0f%%", coverageScore * 100)}", color = SigurColors.TextPrimary, fontSize = 12.sp)
                }
            }
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            val metrics = listOf(
                "Precision" to percent(summary?.get("precision")),
                "Recall" to percent(summary?.get("recall")),
                "F1" to percent(summary?.get("f1"))
            )
            
            metrics.forEach { (label, value) ->
                Card(
                    modifier = Modifier.weight(1f),
                    colors = CardDefaults.cardColors(containerColor = SigurColors.BackgroundCard),
                    shape = DSCardShape,
                    border = DSCardBorder
                ) {
                    Column(modifier = Modifier.padding(12.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(label, color = SigurColors.TextSecondary, fontSize = 11.sp)
                        Text(String.format("%.0f%%", value * 100), color = SigurColors.TextPrimary, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Card(
            colors = CardDefaults.cardColors(containerColor = SigurColors.BackgroundCard),
            shape = DSCardShape,
            border = DSCardBorder
        ) {
            Column(modifier = Modifier.padding(20.dp)) {
                Text("Bucăți evaluate: ${quality?.itemsEvaluated ?: 0}", color = SigurColors.TextPrimary, fontWeight = FontWeight.Bold)
                Spacer(modifier = Modifier.height(12.dp))
                MetricRow("Reputație URL", String.format("%.0f%%", (readiness?.readinessComponents?.get("reputation_score") ?: 0f) * 100))
                MetricRow("Rate Corecte", "${quality?.itemsEvaluated ?: 0}")
                MetricRow("False positive / False negative", "$falsePositiveCount / $falseNegativeCount")
            }
        }

        if (viewModel.feedbackSamples != null) {
            Spacer(modifier = Modifier.height(16.dp))
            Card(
                colors = CardDefaults.cardColors(containerColor = SigurColors.BackgroundCard),
                shape = DSCardShape,
                border = DSCardBorder
            ) {
                Column(modifier = Modifier.padding(20.dp)) {
                    Text("Monitorizare feedback comunitate", color = SigurColors.TextPrimary, fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.height(12.dp))
                    Text(
                        "False Positive (cele mai frecvente): ${viewModel.feedbackSamples?.topFalsePositive?.joinToString(", ") ?: "N/A"}",
                        color = SigurColors.TextSecondary,
                        fontSize = 12.sp
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        "False Negative (cele mai frecvente): ${viewModel.feedbackSamples?.topFalseNegative?.joinToString(", ") ?: "N/A"}",
                        color = SigurColors.TextSecondary,
                        fontSize = 12.sp
                    )
                }
            }
        }

        viewModel.reputationStats?.let { stats ->
            Spacer(modifier = Modifier.height(16.dp))
            Card(
                colors = CardDefaults.cardColors(containerColor = SigurColors.BackgroundCard),
                shape = DSCardShape,
                border = DSCardBorder
            ) {
                Column(modifier = Modifier.padding(20.dp)) {
                    Text("Statistici cache reputație", color = SigurColors.TextPrimary, fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.height(12.dp))
                    MetricRow("Rata de hit cache", String.format("%.0f%%", (stats.cacheHitRatio ?: 0f) * 100))
                    MetricRow("În cache", "${stats.cachedDomains ?: 0}")
                    MetricRow("Înregistrări", "${stats.entries ?: 0}")
                    MetricRow("Ultima sincronizare", stats.lastUpdated ?: "N/A")
                }
            }
        }
    }
}

@Composable
fun MetricRow(label: String, value: String) {
    Row(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp), horizontalArrangement = Arrangement.SpaceBetween) {
        Text(label, color = SigurColors.TextSecondary, fontSize = 12.sp)
        Text(value, color = SigurColors.TextPrimary, fontSize = 12.sp, fontWeight = FontWeight.Bold)
    }
}
