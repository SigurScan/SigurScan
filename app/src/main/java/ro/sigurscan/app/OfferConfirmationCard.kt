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
fun OfferConfirmationCard(
    draft: PendingOfferConfirmation,
    onConfirm: (OfferConfirmationFields) -> Unit,
    onCancel: () -> Unit
) {
    var issuerName by remember(draft) { mutableStateOf(draft.fields.issuerName) }
    var issuerCui by remember(draft) { mutableStateOf(draft.fields.issuerCui) }
    var iban by remember(draft) { mutableStateOf(draft.fields.iban) }
    var paymentBeneficiary by remember(draft) { mutableStateOf(draft.fields.paymentBeneficiary) }
    var totalAmount by remember(draft) { mutableStateOf(draft.fields.totalAmount) }
    var currency by remember(draft) { mutableStateOf(draft.fields.currency.ifBlank { "RON" }) }
    var documentNumber by remember(draft) { mutableStateOf(draft.fields.documentNumber) }
    var documentDate by remember(draft) { mutableStateOf(draft.fields.documentDate) }

    val missingHints = listOfNotNull(
        if (issuerName.isBlank()) "emitent" else null,
        if (issuerCui.isBlank()) "CUI" else null,
        if (iban.isBlank()) "IBAN" else null,
        if (totalAmount.isBlank()) "sumă" else null
    )

    Card(
        colors = CardDefaults.cardColors(containerColor = SigurColors.BackgroundCard),
        shape = DSCardShape,
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, SigurColors.GlassBorder, DSCardShape)
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(48.dp)
                        .background(
                            brush = androidx.compose.ui.graphics.Brush.linearGradient(
                                colors = listOf(Color(0xFF14BE86), SigurColors.Brand, Color(0xFF06875A))
                            ),
                            shape = RoundedCornerShape(16.dp)
                        ),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(Icons.Default.LocalOffer, contentDescription = null, tint = Color.White, modifier = Modifier.size(24.dp))
                }
                Spacer(modifier = Modifier.width(12.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text("Confirmă oferta", fontWeight = FontWeight.Bold, fontSize = 20.sp, color = SigurColors.TextPrimary)
                    Text(
                        "Corectează câmpurile citite automat, apoi pornim verificarea completă.",
                        color = SigurColors.TextSecondary,
                        fontSize = 13.sp,
                        lineHeight = 18.sp
                    )
                }
                DSChip(
                    text = if (missingHints.isEmpty()) "gata" else "de verificat",
                    tone = if (missingHints.isEmpty()) DSChipTone.Safe else DSChipTone.Pending
                )
            }

            if (missingHints.isNotEmpty()) {
                Spacer(modifier = Modifier.height(12.dp))
                Card(
                    colors = CardDefaults.cardColors(containerColor = SigurColors.PendingLight),
                    border = BorderStroke(1.dp, SigurColors.Pending.copy(alpha = 0.25f)),
                    shape = RoundedCornerShape(16.dp)
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        verticalAlignment = Alignment.Top
                    ) {
                        Icon(Icons.Default.Info, contentDescription = null, tint = SigurColors.Pending, modifier = Modifier.size(18.dp))
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "Lipsesc sau sunt neclare: ${missingHints.joinToString(", ")}. Dacă documentul nu le conține, le poți lăsa goale.",
                            color = SigurColors.TextSecondary,
                            fontSize = 12.sp,
                            lineHeight = 16.sp
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(14.dp))
            OfferFieldEditor("Emitent / firmă", issuerName) { issuerName = it }
            OfferFieldEditor("CUI / CIF", issuerCui) { issuerCui = it.filter { ch -> ch.isDigit() || ch.uppercaseChar() in 'A'..'Z' }.take(14) }
            OfferFieldEditor("IBAN", iban) { iban = it.replace(" ", "").uppercase(Locale.getDefault()).take(34) }
            OfferFieldEditor("Beneficiar plată", paymentBeneficiary) { paymentBeneficiary = it }

            Row(horizontalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.fillMaxWidth()) {
                OfferFieldEditor(
                    label = "Sumă",
                    value = totalAmount,
                    modifier = Modifier.weight(1.35f)
                ) { totalAmount = it.take(24) }
                OfferFieldEditor(
                    label = "Monedă",
                    value = currency,
                    modifier = Modifier.weight(0.85f)
                ) { currency = it.uppercase(Locale.getDefault()).take(6) }
            }

            Row(horizontalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.fillMaxWidth()) {
                OfferFieldEditor(
                    label = "Nr. document",
                    value = documentNumber,
                    modifier = Modifier.weight(1f)
                ) { documentNumber = it.take(40) }
                OfferFieldEditor(
                    label = "Dată",
                    value = documentDate,
                    modifier = Modifier.weight(1f)
                ) { documentDate = it.take(20) }
            }

            if (draft.links.isNotEmpty()) {
                Spacer(modifier = Modifier.height(8.dp))
                Card(
                    colors = CardDefaults.cardColors(containerColor = SigurColors.BackgroundSurface),
                    border = BorderStroke(1.dp, SigurColors.BorderSubtle),
                    shape = RoundedCornerShape(16.dp)
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Text("Linkuri găsite: ${draft.links.size}", color = SigurColors.TextMuted, fontSize = 11.sp)
                        Text(
                            draft.links.take(2).joinToString("\n"),
                            color = SigurColors.TextSecondary,
                            fontSize = 11.sp,
                            lineHeight = 15.sp,
                            modifier = Modifier.padding(top = 4.dp)
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))
            Button(
                onClick = {
                    onConfirm(
                        OfferConfirmationFields(
                            issuerName = issuerName.trim(),
                            issuerCui = issuerCui.trim(),
                            iban = iban.trim(),
                            paymentBeneficiary = paymentBeneficiary.trim(),
                            totalAmount = totalAmount.trim(),
                            currency = currency.trim().ifBlank { "RON" },
                            documentNumber = documentNumber.trim(),
                            documentDate = documentDate.trim()
                        )
                    )
                },
                modifier = Modifier.fillMaxWidth().height(52.dp),
                colors = ButtonDefaults.buttonColors(containerColor = SigurColors.Brand),
                shape = DSPillShape
            ) {
                Icon(Icons.Default.Verified, contentDescription = null, tint = Color.White, modifier = Modifier.size(17.dp))
                Spacer(modifier = Modifier.width(8.dp))
                Text("Verifică oferta", color = Color.White, fontWeight = FontWeight.Bold)
            }

            TextButton(
                onClick = onCancel,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Renunță", color = SigurColors.TextSecondary)
            }
        }
    }
}

@Composable
internal fun OfferFieldEditor(
    label: String,
    value: String,
    modifier: Modifier = Modifier,
    onValueChange: (String) -> Unit
) {
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        label = { Text(label, color = SigurColors.TextMuted) },
        singleLine = true,
        colors = OutlinedTextFieldDefaults.colors(
            focusedBorderColor = SigurColors.Brand,
            unfocusedBorderColor = SigurColors.GlassBorder,
            focusedTextColor = SigurColors.TextPrimary,
            unfocusedTextColor = SigurColors.TextPrimary,
            focusedContainerColor = SigurColors.BackgroundCard,
            unfocusedContainerColor = SigurColors.BackgroundCard,
            cursorColor = SigurColors.Brand
        ),
        shape = RoundedCornerShape(SigurColors.RadiusInput.dp),
        modifier = modifier
            .fillMaxWidth()
            .padding(bottom = 10.dp)
    )
}

internal fun formatInvoiceAmount(value: Double?, currency: String): String {
    return value?.let { String.format(Locale.getDefault(), "%.2f %s", it, currency) } ?: "—"
}

internal fun formatOfferAmount(value: Double?, currency: String): String {
    return value?.let { String.format(Locale.getDefault(), "%.2f %s", it, currency) } ?: "—"
}

@Composable
internal fun InvoiceBeneficiaryNameCheck(
    check: BeneficiaryNameCheckResponse,
    onAttestation: (String) -> Unit
) {
    Spacer(modifier = Modifier.height(12.dp))
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, SigurColors.Pending.copy(alpha = 0.35f), RoundedCornerShape(10.dp))
            .background(SigurColors.PendingLight, RoundedCornerShape(10.dp))
            .padding(12.dp)
    ) {
        Text(
            check.title ?: "Verifică numele beneficiarului în aplicația băncii",
            fontWeight = FontWeight.Bold,
            fontSize = 13.sp,
            color = SigurColors.TextPrimary
        )
        check.reason?.takeIf { it.isNotBlank() }?.let {
            Spacer(modifier = Modifier.height(4.dp))
            Text(it, fontSize = 12.sp, color = SigurColors.TextSecondary)
        }
        check.expectedBeneficiary?.takeIf { it.isNotBlank() }?.let {
            Spacer(modifier = Modifier.height(6.dp))
            Text("Nume așteptat: $it", fontSize = 12.sp, fontWeight = FontWeight.SemiBold, color = SigurColors.TextPrimary)
        }
        val contextLine = listOfNotNull(
            check.ibanMaskedForClient?.takeIf { it.isNotBlank() }?.let { "IBAN $it" },
            check.bank?.takeIf { it.isNotBlank() } ?: check.bankCode?.takeIf { it.isNotBlank() },
            check.localServiceHint?.takeIf { it.isNotBlank() },
        ).joinToString(" · ")
        if (contextLine.isNotBlank()) {
            Spacer(modifier = Modifier.height(4.dp))
            Text(contextLine, fontSize = 12.sp, color = SigurColors.TextSecondary)
        }
        check.sanb?.let { sanb ->
            Spacer(modifier = Modifier.height(6.dp))
            DSChip(
                text = if (sanb.payeeBankParticipant) "BANCA BENEFICIARULUI: SANB" else "SANB NECONFIRMAT",
                tone = if (sanb.payeeBankParticipant) DSChipTone.Safe else DSChipTone.Pending
            )
            sanb.participantName?.takeIf { it.isNotBlank() }?.let {
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    listOfNotNull(it, sanb.bic?.takeIf { bic -> bic.isNotBlank() }).joinToString(" · "),
                    fontSize = 11.sp,
                    color = SigurColors.TextSecondary
                )
            }
        }
        check.steps.take(4).forEachIndexed { index, step ->
            Spacer(modifier = Modifier.height(6.dp))
            Text("${index + 1}. $step", fontSize = 12.sp, color = SigurColors.TextPrimary)
        }
        Spacer(modifier = Modifier.height(12.dp))
        Text(
            "După ce banca îți afișează numele beneficiarului:",
            fontSize = 12.sp,
            fontWeight = FontWeight.SemiBold,
            color = SigurColors.TextPrimary
        )
        Spacer(modifier = Modifier.height(8.dp))
        Button(
            onClick = { onAttestation("match") },
            modifier = Modifier.fillMaxWidth().height(44.dp),
            colors = ButtonDefaults.buttonColors(containerColor = SigurColors.Safe),
            shape = DSPillShape
        ) {
            Icon(Icons.Default.CheckCircle, contentDescription = null, tint = Color.White, modifier = Modifier.size(16.dp))
            Spacer(modifier = Modifier.width(8.dp))
            Text("Numele se potrivește", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 12.sp)
        }
        Spacer(modifier = Modifier.height(8.dp))
        Button(
            onClick = { onAttestation("no_match") },
            modifier = Modifier.fillMaxWidth().height(44.dp),
            colors = ButtonDefaults.buttonColors(containerColor = SigurColors.Dangerous),
            shape = DSPillShape
        ) {
            Icon(Icons.Default.ReportProblem, contentDescription = null, tint = Color.White, modifier = Modifier.size(16.dp))
            Spacer(modifier = Modifier.width(8.dp))
            Text("Nu se potrivește", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 12.sp)
        }
        Spacer(modifier = Modifier.height(8.dp))
        OutlinedButton(
            onClick = { onAttestation("not_shown") },
            modifier = Modifier.fillMaxWidth().height(44.dp),
            border = BorderStroke(1.dp, SigurColors.Pending.copy(alpha = 0.45f)),
            shape = DSPillShape
        ) {
            Icon(Icons.Default.Info, contentDescription = null, tint = SigurColors.Pending, modifier = Modifier.size(16.dp))
            Spacer(modifier = Modifier.width(8.dp))
            Text("Banca nu afișează numele", color = SigurColors.TextPrimary, fontWeight = FontWeight.SemiBold, fontSize = 12.sp)
        }
        check.privacyNote?.takeIf { it.isNotBlank() }?.let {
            Spacer(modifier = Modifier.height(8.dp))
            Text(it, fontSize = 11.sp, color = SigurColors.TextSecondary)
        }
    }
}

internal fun offerSignalLabel(signal: String): String {
    val normalized = signal.lowercase(Locale.getDefault())
    return when {
        "crypto" in normalized || "wallet" in normalized -> "Plată crypto/wallet: verifică foarte atent înainte să trimiți bani."
        "off_platform" in normalized || "platform" in normalized -> "Discuția sau plata pare mutată în afara platformei oficiale."
        "card" in normalized || "cvv" in normalized || "otp" in normalized -> "Cerere de card/CVV/OTP: nu trimite coduri sau date bancare."
        "id_document" in normalized || "document" in normalized || "buletin" in normalized -> "Se cer acte personale; trimite-le doar prin canal oficial verificat."
        "price_urgency" in normalized || "urgency" in normalized -> "Presiune de timp/preț; este doar semnal contextual, nu verdict singur."
        "iban" in normalized -> "IBAN detectat; verificăm dacă se aliniază cu beneficiarul."
        "cui" in normalized || "entity" in normalized -> "Date firmă/CUI detectate și comparate unde se poate."
        "qr_payment" in normalized || "qr" in normalized -> "Cod QR de plată detectat."
        "family" in normalized -> "Seamănă cu o familie cunoscută de fraudă din atlas."
        "readiness" in normalized || "missing" in normalized -> "Unele câmpuri lipsesc sau sunt greu de citit."
        else -> signal.replace('_', ' ').replace('-', ' ')
    }
}

@Composable
internal fun InvoiceFieldRow(label: String, value: String, valueTone: DSChipTone = DSChipTone.Neutral) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
        horizontalArrangement = Arrangement.spacedBy(12.dp),
        verticalAlignment = Alignment.Top
    ) {
        Text(
            label,
            fontSize = 13.sp,
            color = SigurColors.TextSecondary,
            modifier = Modifier.widthIn(min = 88.dp, max = 138.dp)
        )
        if (valueTone == DSChipTone.Brand) {
            DSChip(value, tone = valueTone, modifier = Modifier.weight(1f))
        } else {
            Text(
                value,
                fontSize = 13.sp,
                fontWeight = FontWeight.Medium,
                color = SigurColors.TextPrimary,
                textAlign = TextAlign.End,
                lineHeight = 18.sp,
                modifier = Modifier.weight(1f)
            )
        }
    }
    HorizontalDivider(color = SigurColors.BorderSubtle, thickness = 0.5.dp)
}
