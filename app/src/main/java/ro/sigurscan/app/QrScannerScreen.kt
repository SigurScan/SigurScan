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

@AndroidxOptIn(ExperimentalGetImage::class)
@Composable
fun QrScannerScreen(
    hasCameraPermission: Boolean,
    onRequestCameraPermission: () -> Unit,
    onClose: () -> Unit,
    onQrCodeScanned: (String) -> Unit,
    onPickImageFallback: () -> Unit
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    var statusMessage by remember { mutableStateOf("Poziționează codul QR în zona verde.") }
    var errorMessage by remember { mutableStateOf<String?>(null) }
    var showTorchUnavailable by remember { mutableStateOf(false) }
    var isTorchOn by remember { mutableStateOf(false) }
    var camera by remember { mutableStateOf<Camera?>(null) }

    val previewView = remember {
        PreviewView(context).apply {
            layoutParams = LayoutParams(
                LayoutParams.MATCH_PARENT,
                LayoutParams.MATCH_PARENT
            )
            scaleType = PreviewView.ScaleType.FILL_CENTER
        }
    }
    val executor = remember { Executors.newSingleThreadExecutor() }
    val barcodeScanner = remember {
        runCatching {
            val options = BarcodeScannerOptions.Builder()
                .setBarcodeFormats(Barcode.FORMAT_QR_CODE)
                .build()
            BarcodeScanning.getClient(options)
        }.onFailure { throwable ->
            Log.e("SigurScanQr", "Failed to initialize live QR scanner", throwable)
        }.getOrNull()
    }
    val hasScanned = remember { AtomicBoolean(false) }
    var cameraProvider by remember { mutableStateOf<ProcessCameraProvider?>(null) }
    val liveQrAvailable = barcodeScanner != null

    fun stopCamera() {
        cameraProvider?.unbindAll()
    }

    DisposableEffect(hasCameraPermission, liveQrAvailable) {
        if (!hasCameraPermission || !liveQrAvailable) {
            return@DisposableEffect onDispose {}
        }

        var imageAnalysis: ImageAnalysis? = null
        val providerFuture = ProcessCameraProvider.getInstance(context)
        val activeScanner = barcodeScanner ?: return@DisposableEffect onDispose {}

        val startCamera = Runnable {
            runCatching {
                val provider = providerFuture.get()
                cameraProvider = provider

                val preview = CameraPreview.Builder().build().apply {
                    setSurfaceProvider(previewView.surfaceProvider)
                }

                imageAnalysis = ImageAnalysis.Builder()
                    .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                    .build()

                imageAnalysis?.setAnalyzer(executor) { imageProxy ->
                    if (hasScanned.get()) {
                        imageProxy.close()
                        return@setAnalyzer
                    }

                    val mediaImage = imageProxy.image
                    if (mediaImage == null) {
                        imageProxy.close()
                        return@setAnalyzer
                    }

                    val inputImage = InputImage.fromMediaImage(mediaImage, imageProxy.imageInfo.rotationDegrees)
                    activeScanner.process(inputImage)
                        .addOnSuccessListener { barcodes ->
                            val qrValue = barcodes.firstOrNull()?.rawValue?.trim()
                            if (!qrValue.isNullOrBlank() && hasScanned.compareAndSet(false, true)) {
                                stopCamera()
                                onQrCodeScanned(qrValue)
                                onClose()
                            }
                        }
                        .addOnFailureListener {
                            statusMessage = "Nu am reușit să citesc QR-ul, încearcă din nou."
                        }
                        .addOnCompleteListener {
                            imageProxy.close()
                        }
                }

                provider.unbindAll()
                camera = provider.bindToLifecycle(
                    lifecycleOwner,
                    CameraSelector.DEFAULT_BACK_CAMERA,
                    preview,
                    imageAnalysis
                )
            }.onFailure { throwable ->
                errorMessage = throwable.message ?: "Nu pot porni camera."
            }
        }

        providerFuture.addListener(startCamera, ContextCompat.getMainExecutor(context))

        onDispose {
            stopCamera()
            camera?.cameraControl?.enableTorch(false)
            camera = null
            imageAnalysis?.clearAnalyzer()
            executor.shutdown()
            barcodeScanner?.close()
        }
    }

    Box(
        modifier = Modifier.fillMaxSize()
    ) {
        if (!hasCameraPermission || !liveQrAvailable) {
            Surface(
                modifier = Modifier.fillMaxSize(),
                color = SigurColors.Canvas
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(20.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    Text(
                        text = if (liveQrAvailable) {
                            "Ai nevoie de acces la cameră pentru scanare live"
                        } else {
                            "Scanarea live QR nu este disponibilă pe acest telefon"
                        },
                        style = MaterialTheme.typography.titleMedium,
                        color = SigurColors.TextPrimary,
                        textAlign = TextAlign.Center
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    Text(
                        text = if (liveQrAvailable) {
                            errorMessage ?: "Apasă „Permite camera” și încearcă din nou."
                        } else {
                            "Poți continua sigur cu scanarea QR din poză."
                        },
                        color = SigurColors.TextSecondary,
                        textAlign = TextAlign.Center
                    )
                    Spacer(modifier = Modifier.height(24.dp))
                    if (liveQrAvailable) {
                        Button(
                            onClick = {
                                onRequestCameraPermission()
                            },
                            colors = ButtonDefaults.buttonColors(containerColor = SigurColors.Brand)
                        ) {
                            Text("Permite camera")
                        }
                        Spacer(modifier = Modifier.height(12.dp))
                    }
                    OutlinedButton(onClick = onPickImageFallback) {
                        Text("Scanează din poză")
                    }
                    Spacer(modifier = Modifier.height(12.dp))
                    TextButton(onClick = {
                        val uri = android.net.Uri.parse("package:${context.packageName}")
                        val intent = Intent(ACTION_APPLICATION_DETAILS_SETTINGS, uri)
                        context.startActivity(intent)
                    }) {
                        Text("Deschide setări")
                    }
                }
            }
        } else {
            AndroidView(
                factory = { previewView },
                modifier = Modifier.fillMaxSize()
            )

            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(24.dp)
            ) {
                Card(
                    modifier = Modifier
                        .align(Alignment.TopCenter)
                        .fillMaxWidth(),
                    colors = CardDefaults.cardColors(containerColor = SigurColors.Canvas.copy(alpha = 0.92f))
                ) {
                    Column(modifier = Modifier.padding(10.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                        Text("Scanează codul QR", color = SigurColors.TextPrimary, fontWeight = FontWeight.Bold)
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(statusMessage, color = SigurColors.TextSecondary, fontSize = 12.sp, textAlign = TextAlign.Center)
                    }
                }

                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(4.dp)
                ) {
                    val hasTorch = camera?.cameraInfo?.hasFlashUnit() == true

                    Row(
                        modifier = Modifier
                            .align(Alignment.TopEnd),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        if (camera != null) {
                            Surface(
                                shape = CircleShape,
                                color = SigurColors.BackgroundCard,
                                modifier = Modifier.size(38.dp)
                            ) {
                                IconButton(
                                    onClick = {
                                        if (!hasTorch) {
                                            showTorchUnavailable = true
                                            return@IconButton
                                        }
                                        isTorchOn = !isTorchOn
                                        camera?.cameraControl?.enableTorch(isTorchOn)
                                    }
                                ) {
                                    Icon(
                                        if (isTorchOn) Icons.Default.FlashOn else Icons.Default.FlashOff,
                                        contentDescription = if (isTorchOn) "Oprește lanternă" else "Pornește lanternă",
                                        tint = SigurColors.TextPrimary
                                    )
                                }
                            }
                        }

                        Surface(
                            shape = CircleShape,
                            color = SigurColors.BackgroundCard,
                            modifier = Modifier
                                .size(38.dp)
                        ) {
                            IconButton(onClick = onClose) {
                                Icon(Icons.Default.Close, contentDescription = "Închide", tint = SigurColors.TextPrimary)
                            }
                        }
                    }

                    if (showTorchUnavailable) {
                        AssistChip(
                            onClick = { showTorchUnavailable = false },
                            label = { Text("Camera nu are lanternă", color = SigurColors.Dangerous) },
                            colors = AssistChipDefaults.assistChipColors(
                                labelColor = SigurColors.Dangerous,
                                containerColor = SigurColors.BackgroundCard
                            ),
                            modifier = Modifier
                                .align(Alignment.TopCenter)
                                .padding(top = 48.dp)
                        )
                    }

                    Box(
                        modifier = Modifier
                            .size(220.dp)
                            .align(Alignment.Center)
                            .border(3.dp, SigurColors.Brand, RoundedCornerShape(12.dp))
                    )
                }

                Surface(
                    modifier = Modifier
                        .align(Alignment.BottomCenter)
                        .fillMaxWidth(0.9f),
                    color = SigurColors.BackgroundCard.copy(alpha = 0.9f)
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        horizontalArrangement = Arrangement.Center
                    ) {
                        Text(
                            text = "Nu pleca app-ul în fundal pe durata scanării",
                            color = SigurColors.TextSecondary,
                            fontSize = 12.sp,
                            textAlign = TextAlign.Center
                        )
                    }
                }
            }
        }

        errorMessage?.let { message ->
            if (errorMessage != null) {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(24.dp),
                    verticalArrangement = Arrangement.Bottom,
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    AssistChip(
                        onClick = { errorMessage = null },
                        label = { Text(message) },
                        colors = AssistChipDefaults.assistChipColors(
                            labelColor = SigurColors.Dangerous,
                            containerColor = SigurColors.BackgroundCard
                        )
                    )
                }
            }
        }
    }
}
