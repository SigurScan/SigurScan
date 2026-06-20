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

@Preview(showBackground = true, backgroundColor = 0xFF0B0F19)
@Composable
fun EvidenceSectionPreview() {
    SigurScanTheme {
        Column(modifier = Modifier.padding(16.dp)) {
            EvidenceSection(
                screenshotUrl = null,
                serverInfo = "Preview disponibil pentru pagina finală.",
                finalUrl = "https://exemplu.invalid"
            )
        }
    }
}

@Composable
fun ResultCard(
    assessment: OfflineAssessment,
    onBack: () -> Unit,
    onRescan: () -> Unit,
    onReport: () -> Unit,
    officialReportPackage: OneTapReportPackage? = null,
    officialReportLoading: Boolean = false,
    officialReportStatus: String? = null,
    onOfficialReport: () -> Unit = {},
    onFeedback: (String) -> Unit,
    onFamilyAlert: () -> Unit = {},
    actionPlanLoading: Boolean = false,
    actionPlanStatus: String? = null,
    onActionPlanImpacts: (List<String>) -> Unit = {}
) {
    val riskUi = mapRiskDisplayState(assessment)
    val decision = mapUserActionDecision(assessment, riskUi)
    val finalDomain = displayDomainFrom(assessment.finalUrl)
    val topReasons = buildTopReasons(assessment, decision)
    val nextActions = buildNextActions(assessment, decision)
    val hasTechnicalDetails = assessment.threatIntel.isNotEmpty() ||
            assessment.emailAuth != null ||
            assessment.detectedButtons.isNotEmpty() ||
            assessment.redirectChain.isNotEmpty() ||
            assessment.finalUrl != null ||
            assessment.sandboxReportUrl != null

    var feedbackSent by remember { mutableStateOf(false) }
    var showTechnicalDetails by remember { mutableStateOf(false) }

    val hasRiskVerdict = riskUi.level == "Suspect" || riskUi.level == "Periculos"
    val verdictLightBg = when (riskUi.level) {
        "Sigur" -> SigurColors.SafeLight
        "Periculos" -> SigurColors.DangerousLight
        "Suspect" -> SigurColors.SuspectLight
        else -> SigurColors.PendingLight
    }
    val verdictBorder = when (riskUi.level) {
        "Sigur" -> SigurColors.SafeBorder
        "Periculos" -> SigurColors.DangerousBorder
        "Suspect" -> SigurColors.SuspectBorder
        else -> SigurColors.Pending.copy(alpha = 0.32f)
    }
    val isCheckingFurther = assessment.gateResult?.asyncExpected == true ||
        assessment.gateResult?.finality == GateFinality.PROVISIONAL

    Column(modifier = Modifier.fillMaxWidth()) {
        // VerdictCard — DS hero block (icon circle + title + subtitle + message)
        Card(
            colors = CardDefaults.cardColors(containerColor = verdictLightBg),
            shape = RoundedCornerShape(16.dp),
            modifier = Modifier
                .fillMaxWidth()
                .border(1.5.dp, verdictBorder, RoundedCornerShape(16.dp))
        ) {
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                modifier = Modifier.fillMaxWidth().padding(20.dp)
            ) {
                Box(
                    modifier = Modifier
                        .size(56.dp)
                        .background(riskUi.color, CircleShape),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = resultIconFor(assessment.gateResult?.action, riskUi.level),
                        contentDescription = null,
                        tint = Color.White,
                        modifier = Modifier.size(30.dp)
                    )
                }
                Spacer(modifier = Modifier.height(14.dp))
                Text(
                    text = decision.headline.uppercase(Locale.getDefault()),
                    fontSize = 24.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 0.04.em,
                    color = riskUi.color,
                    textAlign = TextAlign.Center
                )
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = decision.supportText,
                    color = SigurColors.TextSecondary,
                    fontSize = 16.sp,
                    lineHeight = 24.sp,
                    textAlign = TextAlign.Center
                )
                if (isCheckingFurther) {
                    Spacer(modifier = Modifier.height(12.dp))
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        modifier = Modifier
                            .background(SigurColors.BackgroundCard, RoundedCornerShape(12.dp))
                            .padding(horizontal = 16.dp, vertical = 8.dp)
                    ) {
                        CircularProgressIndicator(
                            color = SigurColors.Pending,
                            strokeWidth = 2.dp,
                            modifier = Modifier.size(16.dp)
                        )
                        Text(
                            text = "Verificare suplimentară în curs",
                            color = SigurColors.Pending,
                            fontSize = 14.sp,
                            fontWeight = FontWeight.SemiBold
                        )
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

    Card(
        colors = CardDefaults.cardColors(containerColor = SigurColors.BackgroundCard),
        shape = RoundedCornerShape(16.dp),
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, SigurColors.GlassBorder, RoundedCornerShape(16.dp))
    ) {
        Column(modifier = Modifier.padding(20.dp)) {

            GateEvidenceSummary(assessment, riskUi)

            EvidenceSection(assessment.screenshotUrl, assessment.serverInfo, assessment.finalUrl)

            finalDomain?.let { domain ->
                Card(
                    colors = CardDefaults.cardColors(containerColor = SigurColors.BackgroundSurface),
                    border = BorderStroke(1.dp, SigurColors.GlassBorder),
                    shape = RoundedCornerShape(12.dp),
                    modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp)
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp).fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(Icons.Default.Link, contentDescription = null, tint = SigurColors.Brand, modifier = Modifier.size(16.dp))
                        Spacer(modifier = Modifier.width(8.dp))
                        Column {
                            Text("Te duce către", color = SigurColors.TextMuted, fontSize = 11.sp)
                            Text(domain, color = SigurColors.TextPrimary, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                        }
                    }
                }
            }

            Text(
                text = "Clasificare: ${assessment.family}",
                color = SigurColors.TextMuted,
                fontSize = 11.sp,
                modifier = Modifier.padding(bottom = 4.dp)
            )

            assessment.offerEvidence?.let { offer ->
                OfferEvidenceSection(offer)
                Spacer(modifier = Modifier.height(12.dp))
            }

            ResultSection(title = "De ce spunem asta", items = topReasons, icon = Icons.AutoMirrored.Filled.List)
            
            if (assessment.offerAnalysis != null) {
                OfferAnalysisSection(assessment.offerAnalysis)
            }

            if (assessment.keyDangers.isNotEmpty() && hasRiskVerdict) {
                ResultSection(title = "Riscuri principale", items = assessment.keyDangers.take(3), icon = Icons.Default.Warning)
            }

            ResultSection(title = "Ce să faci acum", items = nextActions, icon = Icons.Default.CheckCircle)

            assessment.actionPlan?.let { plan ->
                ActionPlanSection(plan)
            }

            if (hasRiskVerdict) {
                PostIncidentImpactControls(
                    loading = actionPlanLoading,
                    status = actionPlanStatus,
                    onSubmit = onActionPlanImpacts
                )
            }

            officialReportPackage?.let { report ->
                OfficialReportPackageSection(report)
            }

            assessment.legal?.let { legal ->
                LegalEducationSection(legal)
            }

            Text(
                text = "SigurScan oferă o estimare automată de risc. Scamurile noi sau personalizate pot să nu fie detectate. Verifică datele importante direct pe site-ul sau în aplicația oficială.",
                color = SigurColors.TextMuted,
                fontSize = 10.sp,
                lineHeight = 14.sp,
                modifier = Modifier.padding(top = 8.dp)
            )

            if (hasTechnicalDetails) {
                TextButton(
                    onClick = { showTechnicalDetails = !showTechnicalDetails },
                    modifier = Modifier.fillMaxWidth().padding(top = 8.dp)
                ) {
                    Text(
                        text = if (showTechnicalDetails) "Ascunde detalii tehnice" else "Arată detalii tehnice",
                        color = SigurColors.Brand,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold
                    )
                }

                if (showTechnicalDetails) {
                    SincerityPillarsSection(assessment)

                    if (assessment.threatIntel.isNotEmpty()) {
                        ThreatIntelSection(assessment.threatIntel, assessment.sandboxReportUrl)
                    }

                    if (assessment.emailAuth != null) {
                        ComplianceSection(assessment.emailAuth)
                    }

                    if (assessment.detectedButtons.isNotEmpty()) {
                        ButtonsSection(assessment.detectedButtons)
                    }

                    RedirectChainSection(assessment.redirectChain, assessment.finalUrl)
                }
            }

            Spacer(modifier = Modifier.height(20.dp))

            // Feedback Section
            if (!feedbackSent) {
                Text(
                    "A fost util acest verdict?",
                    color = SigurColors.TextPrimary,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.padding(bottom = 8.dp)
                )
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(
                        onClick = { onFeedback("correct"); feedbackSent = true },
                        modifier = Modifier.weight(1f),
                        colors = ButtonDefaults.buttonColors(containerColor = SigurColors.SafeLight),
                        border = BorderStroke(1.dp, SigurColors.SafeBorder)
                    ) {
                        Text("DA", color = SigurColors.Safe)
                    }
                    Button(
                        onClick = { onFeedback("false_positive"); feedbackSent = true },
                        modifier = Modifier.weight(1f),
                        colors = ButtonDefaults.buttonColors(containerColor = SigurColors.DangerousLight),
                        border = BorderStroke(1.dp, SigurColors.DangerousBorder)
                    ) {
                        Text("NU", color = SigurColors.Dangerous)
                    }
                }
                Spacer(modifier = Modifier.height(16.dp))
            } else {
                Text(
                    "Mulțumim pentru feedback! Împreună facem România mai sigură.",
                    color = SigurColors.Safe,
                    fontSize = 12.sp,
                    textAlign = TextAlign.Center,
                    modifier = Modifier.fillMaxWidth().padding(bottom = 16.dp)
                )
            }

            Button(
                onClick = onFamilyAlert,
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = SigurColors.BrandTint),
                shape = RoundedCornerShape(10.dp),
                border = BorderStroke(1.dp, SigurColors.Brand)
            ) {
                Icon(Icons.Default.People, contentDescription = null, tint = SigurColors.Brand, modifier = Modifier.size(16.dp))
                Spacer(modifier = Modifier.width(8.dp))
                Text("Trimite alertă Familie", color = SigurColors.Brand, fontSize = 12.sp)
            }
            Spacer(modifier = Modifier.height(12.dp))

            if (hasRiskVerdict) {
                Button(
                    onClick = onOfficialReport,
                    enabled = !officialReportLoading,
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(containerColor = SigurColors.SuspectLight),
                    shape = RoundedCornerShape(10.dp),
                    border = BorderStroke(1.dp, SigurColors.SuspectBorder)
                ) {
                    Icon(Icons.Default.AssignmentTurnedIn, contentDescription = null, tint = SigurColors.Suspect, modifier = Modifier.size(16.dp))
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(if (officialReportLoading) "Se pregătește..." else "Pregătește raport oficial", color = SigurColors.Suspect, fontSize = 12.sp)
                }
                officialReportStatus?.takeIf { it.isNotBlank() }?.let {
                    Text(it, color = SigurColors.TextMuted, fontSize = 11.sp, modifier = Modifier.padding(top = 6.dp, bottom = 8.dp))
                }
                Spacer(modifier = Modifier.height(12.dp))
            }

            if (riskUi.level == "Periculos") {
                Button(
                    onClick = onReport,
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(containerColor = SigurColors.SafeLight),
                    shape = RoundedCornerShape(10.dp),
                    border = BorderStroke(1.dp, SigurColors.SafeBorder)
                ) {
                    Icon(Icons.Default.Share, contentDescription = null, tint = SigurColors.Safe, modifier = Modifier.size(16.dp))
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Raportează către comunitatea SigurScan", color = SigurColors.Safe, fontSize = 12.sp)
                }
                Spacer(modifier = Modifier.height(12.dp))
            }

            if (assessment.cacheStatus != null) {
                Button(
                    onClick = onRescan,
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(containerColor = SigurColors.BrandTint),
                    shape = RoundedCornerShape(10.dp),
                    border = BorderStroke(1.dp, SigurColors.Brand)
                ) {
                    Icon(Icons.Default.Refresh, contentDescription = null, tint = SigurColors.Brand, modifier = Modifier.size(16.dp))
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Rescanează acum", color = SigurColors.Brand, fontSize = 12.sp)
                }
                Spacer(modifier = Modifier.height(12.dp))
            }

            Button(
                onClick = onBack,
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = SigurColors.BackgroundSurface),
                shape = RoundedCornerShape(10.dp)
            ) {
                Text("Înapoi la scanare", color = SigurColors.TextPrimary)
            }
        }
    }
    }
}

@Composable
internal fun GateEvidenceSummary(assessment: OfflineAssessment, riskUi: RiskDisplayState) {
    val gateResult = assessment.gateResult ?: return
    val snapshot = assessment.evidenceSnapshot
    val inProgress = GateResultPresentation.isScanInProgress(gateResult)
    val chips = listOfNotNull(
        if (inProgress) "Scanare în curs" else "Verdict final",
        if (assessment.cacheStatus != null) "Verificat anterior" else null,
        snapshot?.completeness?.let {
            when (it) {
                EvidenceCompleteness.FULL -> "Verificări complete"
                EvidenceCompleteness.PARTIAL_ONLINE -> "Se verifică linkul"
                EvidenceCompleteness.LOCAL_ONLY -> "Mai trebuie informații"
            }
        }
    ).distinct()

    Card(
        colors = CardDefaults.cardColors(containerColor = riskUi.color.copy(alpha = 0.08f)),
        border = BorderStroke(1.dp, riskUi.color.copy(alpha = 0.22f)),
        shape = RoundedCornerShape(12.dp),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            Text(
                text = GateResultPresentation.primaryAction(gateResult),
                color = SigurColors.TextPrimary,
                fontSize = 13.sp,
                fontWeight = FontWeight.SemiBold,
                lineHeight = 18.sp
            )
            if (chips.isNotEmpty()) {
                Spacer(modifier = Modifier.height(8.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    chips.take(3).forEach { chip ->
                        Surface(
                            color = SigurColors.BackgroundCard,
                            border = BorderStroke(1.dp, riskUi.color.copy(alpha = 0.18f)),
                            shape = RoundedCornerShape(999.dp)
                        ) {
                            Text(
                                text = chip,
                                color = SigurColors.TextSecondary,
                                fontSize = 10.sp,
                                fontWeight = FontWeight.SemiBold,
                                modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun ResultSection(title: String, items: List<String>, icon: ImageVector) {
    Column(modifier = Modifier.padding(vertical = 8.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(icon, contentDescription = null, tint = SigurColors.TextMuted, modifier = Modifier.size(16.dp))
            Spacer(modifier = Modifier.width(6.dp))
            Text(title, fontWeight = FontWeight.Bold, color = SigurColors.TextPrimary, fontSize = 14.sp)
        }
        items.forEach { item ->
            Text(
                text = "• $item",
                color = SigurColors.TextSecondary,
                fontSize = 13.sp,
                modifier = Modifier.padding(start = 22.dp, top = 2.dp)
            )
        }
    }
}

@Composable
fun OfferEvidenceSection(offer: OfferEvidenceSummary) {
    val entity = offer.entity
    val entityTone = when {
        entity?.brandImpersonation == true -> DSChipTone.Danger
        entity?.cuiChecked == false || entity?.cuiChecked == null -> DSChipTone.Pending
        entity.cuiExists == true && entity.cuiActive == true -> DSChipTone.Safe
        entity.cuiExists == false -> DSChipTone.Suspect
        else -> DSChipTone.Pending
    }
    val entityLabel = when {
        entity?.brandImpersonation == true -> "posibilă impersonare"
        entity?.cuiChecked == false || entity?.cuiChecked == null -> "ANAF neverificat"
        entity.cuiExists == true && entity.cuiActive == true -> "CUI activ"
        entity.cuiExists == false -> "CUI negăsit"
        else -> "ANAF incert"
    }

    Card(
        colors = CardDefaults.cardColors(containerColor = SigurColors.BackgroundCard),
        border = BorderStroke(1.dp, SigurColors.GlassBorder),
        shape = DSCardShape,
        modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(38.dp)
                        .background(SigurColors.BrandTint, RoundedCornerShape(14.dp)),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(Icons.Default.LocalOffer, contentDescription = null, tint = SigurColors.Brand, modifier = Modifier.size(20.dp))
                }
                Spacer(modifier = Modifier.width(10.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text("Date citite din ofertă", fontWeight = FontWeight.Bold, color = SigurColors.TextPrimary, fontSize = 15.sp)
                    Text("Confirmate din document și comparate cu dovezile scanării", color = SigurColors.TextMuted, fontSize = 11.sp)
                }
                DSChip(entityLabel, tone = entityTone)
            }

            Spacer(modifier = Modifier.height(10.dp))

            val fields = offer.fields
            InvoiceFieldRow("Emitent", fields.issuerName ?: entity?.denumire ?: "—")
            InvoiceFieldRow("CUI", fields.issuerCui ?: "—")
            InvoiceFieldRow("IBAN", fields.iban ?: "—")
            InvoiceFieldRow("Beneficiar plată", fields.paymentBeneficiary ?: "—")
            InvoiceFieldRow("Suma", formatOfferAmount(fields.totalAmount, fields.currency ?: "RON"))
            InvoiceFieldRow("Metodă plată", fields.paymentMethod ?: "—")
            InvoiceFieldRow("Tip document", fields.documentType ?: "ofertă")
            fields.familyCode?.takeIf { it.isNotBlank() }?.let {
                InvoiceFieldRow("Familie ofertă", it, DSChipTone.Brand)
            }

            if (offer.coherenceOk != null) {
                InvoiceFieldRow("Coerență sumă/date", if (offer.coherenceOk) "ok" else "neclar")
            }

            val readableSignals = offer.signals
                .map(::offerSignalLabel)
                .distinct()
                .take(5)
            if (readableSignals.isNotEmpty()) {
                Spacer(modifier = Modifier.height(10.dp))
                Text("Semnale observate", fontWeight = FontWeight.Bold, fontSize = 13.sp, color = SigurColors.TextPrimary)
                readableSignals.forEach { signal ->
                    Text("• $signal", fontSize = 12.sp, color = SigurColors.TextSecondary, modifier = Modifier.padding(start = 8.dp, top = 3.dp))
                }
            }

            if (offer.warnings.isNotEmpty()) {
                Spacer(modifier = Modifier.height(10.dp))
                Text("Atenționări", fontWeight = FontWeight.Bold, fontSize = 13.sp, color = SigurColors.Suspect)
                offer.warnings.take(4).forEach { warning ->
                    Text("• $warning", fontSize = 12.sp, color = SigurColors.TextSecondary, modifier = Modifier.padding(start = 8.dp, top = 3.dp))
                }
            }

            Text(
                text = "Notă: lipsa verificării ANAF sau un CUI neclar nu înseamnă automat fraudă; verdictul final folosește combinația de dovezi.",
                fontSize = 10.sp,
                lineHeight = 14.sp,
                color = SigurColors.TextMuted,
                modifier = Modifier.padding(top = 10.dp)
            )
        }
    }
}

@Composable
fun LegalEducationSection(legal: LegalSection) {
    // Strat educativ: randează DOAR ce întoarce backend-ul, verbatim. Nu atinge
    // verdictul. 0 carduri sau label lipsă => secțiunea nu apare deloc.
    val cards = legal.cards.orEmpty().filter { !it.title.isNullOrBlank() || !it.summary.isNullOrBlank() }
    val label = legal.label
    if (cards.isEmpty() || label.isNullOrBlank()) return

    Spacer(modifier = Modifier.height(12.dp))
    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(bottom = 8.dp)) {
        Icon(Icons.Default.Info, contentDescription = null, tint = SigurColors.Brand, modifier = Modifier.size(16.dp))
        Spacer(modifier = Modifier.width(8.dp))
        Text(label, color = SigurColors.TextPrimary, fontWeight = FontWeight.Bold, fontSize = 14.sp)
    }
    cards.forEach { card ->
        Card(
            colors = CardDefaults.cardColors(containerColor = SigurColors.BackgroundCard),
            shape = DSCardShape,
            border = DSCardBorder,
            modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                card.title?.takeIf { it.isNotBlank() }?.let {
                    Text(it, color = SigurColors.TextPrimary, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                }
                card.summary?.takeIf { it.isNotBlank() }?.let {
                    Spacer(modifier = Modifier.height(6.dp))
                    Text(it, color = SigurColors.TextSecondary, fontSize = 12.sp, lineHeight = 18.sp)
                }
                val actions = card.actions.orEmpty().filter { it.isNotBlank() }
                if (actions.isNotEmpty()) {
                    Spacer(modifier = Modifier.height(8.dp))
                    actions.forEach { action ->
                        Text("\u2022 $action", color = SigurColors.TextPrimary, fontSize = 12.sp, lineHeight = 18.sp)
                    }
                }
                val refs = card.sourceRefs.orEmpty().filter { it.isNotBlank() }
                if (refs.isNotEmpty()) {
                    Spacer(modifier = Modifier.height(8.dp))
                    refs.forEach { ref ->
                        Text(ref, color = SigurColors.TextMuted, fontSize = 10.sp)
                    }
                }
            }
        }
    }
    legal.disclaimer?.takeIf { it.isNotBlank() }?.let { disclaimer ->
        Row(modifier = Modifier.fillMaxWidth().padding(top = 2.dp, bottom = 8.dp)) {
            Icon(Icons.Default.Info, contentDescription = null, tint = SigurColors.TextMuted, modifier = Modifier.size(12.dp))
            Spacer(modifier = Modifier.width(6.dp))
            Text(disclaimer, color = SigurColors.TextMuted, fontSize = 10.sp, lineHeight = 14.sp, fontStyle = FontStyle.Italic)
        }
    }
}

@Composable
fun OfficialReportPackageSection(report: OneTapReportPackage) {
    val channels = report.channels.orEmpty()
        .filter { !it.name.isNullOrBlank() || !it.contact.isNullOrBlank() }
    if (channels.isEmpty()) return

    Spacer(modifier = Modifier.height(12.dp))
    Card(
        colors = CardDefaults.cardColors(containerColor = SigurColors.BackgroundCard),
        shape = DSCardShape,
        border = DSCardBorder,
        modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.AssignmentTurnedIn, contentDescription = null, tint = SigurColors.Suspect, modifier = Modifier.size(16.dp))
                Spacer(modifier = Modifier.width(8.dp))
                Text("Raport oficial pregătit", color = SigurColors.TextPrimary, fontWeight = FontWeight.Bold, fontSize = 14.sp)
            }
            Spacer(modifier = Modifier.height(10.dp))
            channels.take(4).forEachIndexed { index, channel ->
                if (index > 0) {
                    HorizontalDivider(color = SigurColors.GlassBorder, modifier = Modifier.padding(vertical = 10.dp))
                }
                channel.name?.takeIf { it.isNotBlank() }?.let {
                    Text(it, color = SigurColors.TextPrimary, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                }
                channel.contact?.takeIf { it.isNotBlank() }?.let {
                    Text(it, color = SigurColors.TextSecondary, fontSize = 12.sp, lineHeight = 17.sp)
                }
                channel.prefilledSubject?.takeIf { it.isNotBlank() }?.let {
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(it, color = SigurColors.TextMuted, fontSize = 11.sp, fontWeight = FontWeight.SemiBold)
                }
                channel.prefilledBody?.takeIf { it.isNotBlank() }?.let {
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(it.take(220), color = SigurColors.TextMuted, fontSize = 10.sp, lineHeight = 14.sp)
                }
            }
            report.disclaimer?.takeIf { it.isNotBlank() }?.let {
                Spacer(modifier = Modifier.height(10.dp))
                Text(it, color = SigurColors.TextMuted, fontSize = 10.sp, lineHeight = 14.sp, fontStyle = FontStyle.Italic)
            }
        }
    }
}

@Composable
fun ActionPlanSection(plan: ActionPlan) {
    val steps = plan.steps.orEmpty()
        .filter { !it.title.isNullOrBlank() || !it.detail.isNullOrBlank() }
        .sortedWith(compareBy<ActionPlanStep> { it.order ?: Int.MAX_VALUE })
    if (steps.isEmpty()) return

    Spacer(modifier = Modifier.height(12.dp))
    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(bottom = 8.dp)) {
        Icon(Icons.Default.AssignmentTurnedIn, contentDescription = null, tint = SigurColors.Brand, modifier = Modifier.size(16.dp))
        Spacer(modifier = Modifier.width(8.dp))
        Text(
            text = plan.label?.takeIf { it.isNotBlank() } ?: "Plan de acțiune",
            color = SigurColors.TextPrimary,
            fontWeight = FontWeight.Bold,
            fontSize = 14.sp
        )
    }

    Card(
        colors = CardDefaults.cardColors(containerColor = SigurColors.BackgroundCard),
        shape = DSCardShape,
        border = DSCardBorder,
        modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            steps.take(6).forEachIndexed { index, step ->
                if (index > 0) {
                    HorizontalDivider(color = SigurColors.GlassBorder, modifier = Modifier.padding(vertical = 10.dp))
                }
                Row(verticalAlignment = Alignment.Top) {
                    Surface(
                        color = actionPlanUrgencyColor(step.urgency).copy(alpha = 0.12f),
                        border = BorderStroke(1.dp, actionPlanUrgencyColor(step.urgency).copy(alpha = 0.35f)),
                        shape = RoundedCornerShape(999.dp)
                    ) {
                        Text(
                            text = actionPlanUrgencyLabel(step.urgency),
                            color = actionPlanUrgencyColor(step.urgency),
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                        )
                    }
                    Spacer(modifier = Modifier.width(10.dp))
                    Column(modifier = Modifier.weight(1f)) {
                        step.title?.takeIf { it.isNotBlank() }?.let {
                            Text(it, color = SigurColors.TextPrimary, fontWeight = FontWeight.Bold, fontSize = 13.sp)
                        }
                        step.detail?.takeIf { it.isNotBlank() }?.let {
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(it, color = SigurColors.TextSecondary, fontSize = 12.sp, lineHeight = 18.sp)
                        }
                        step.channel?.takeIf { it.isNotBlank() }?.let {
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(it, color = SigurColors.TextMuted, fontSize = 11.sp, fontWeight = FontWeight.SemiBold)
                        }
                    }
                }
            }

            val channels = plan.reportPackage?.channels.orEmpty()
                .mapNotNull { it.name?.takeIf(String::isNotBlank) }
                .distinct()
                .take(3)
            if (channels.isNotEmpty()) {
                Spacer(modifier = Modifier.height(12.dp))
                Text(
                    text = "Raportare: ${channels.joinToString(", ")}",
                    color = SigurColors.TextMuted,
                    fontSize = 11.sp,
                    lineHeight = 16.sp
                )
            }
            plan.disclaimer?.takeIf { it.isNotBlank() }?.let {
                Spacer(modifier = Modifier.height(8.dp))
                Text(it, color = SigurColors.TextMuted, fontSize = 10.sp, lineHeight = 14.sp, fontStyle = FontStyle.Italic)
            }
        }
    }
}

@Composable
fun PostIncidentImpactControls(
    loading: Boolean,
    status: String?,
    onSubmit: (List<String>) -> Unit
) {
    var selected by remember { mutableStateOf<Set<String>>(emptySet()) }
    val options = listOf(
        "shared_card" to "Am introdus cardul",
        "shared_otp" to "Am dat cod OTP",
        "shared_credentials" to "Am dat parola",
        "paid_transfer" to "Am trimis bani",
        "installed_remote_access" to "Am instalat remote"
    )

    Card(
        colors = CardDefaults.cardColors(containerColor = SigurColors.BackgroundCard),
        shape = DSCardShape,
        border = DSCardBorder,
        modifier = Modifier.fillMaxWidth().padding(top = 8.dp, bottom = 8.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.HealthAndSafety, contentDescription = null, tint = SigurColors.Suspect, modifier = Modifier.size(16.dp))
                Spacer(modifier = Modifier.width(8.dp))
                Text("Ce s-a întâmplat deja?", color = SigurColors.TextPrimary, fontWeight = FontWeight.Bold, fontSize = 14.sp)
            }
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                "Selectează doar ce ai făcut, ca planul să fie ordonat corect.",
                color = SigurColors.TextMuted,
                fontSize = 11.sp,
                lineHeight = 15.sp
            )
            Spacer(modifier = Modifier.height(10.dp))
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                options.forEach { (impact, label) ->
                    FilterChip(
                        selected = selected.contains(impact),
                        onClick = {
                            selected = if (selected.contains(impact)) selected - impact else selected + impact
                        },
                        label = { Text(label, fontSize = 11.sp) },
                        enabled = !loading
                    )
                }
            }
            status?.takeIf { it.isNotBlank() }?.let {
                Spacer(modifier = Modifier.height(8.dp))
                Text(it, color = SigurColors.TextSecondary, fontSize = 11.sp, lineHeight = 15.sp)
            }
            Spacer(modifier = Modifier.height(10.dp))
            Button(
                onClick = { onSubmit(selected.toList()) },
                enabled = selected.isNotEmpty() && !loading,
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = SigurColors.SuspectLight),
                border = BorderStroke(1.dp, SigurColors.SuspectBorder),
                shape = DSPillShape
            ) {
                Icon(Icons.Default.AssignmentTurnedIn, contentDescription = null, tint = SigurColors.Suspect, modifier = Modifier.size(14.dp))
                Spacer(modifier = Modifier.width(6.dp))
                Text(if (loading) "Se actualizează..." else "Actualizează planul", color = SigurColors.Suspect, fontSize = 11.sp)
            }
        }
    }
}

internal fun actionPlanUrgencyLabel(urgency: String?): String = when (urgency?.lowercase(Locale.US)) {
    "now" -> "Acum"
    "today" -> "Azi"
    "soon" -> "Curând"
    else -> "Pas"
}

internal fun actionPlanUrgencyColor(urgency: String?): Color = when (urgency?.lowercase(Locale.US)) {
    "now" -> SigurColors.Dangerous
    "today" -> SigurColors.Suspect
    "soon" -> SigurColors.Brand
    else -> SigurColors.TextMuted
}

@Composable
fun OfferAnalysisSection(analysis: String) {
    Column(modifier = Modifier.padding(vertical = 12.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(Icons.Default.AutoAwesome, contentDescription = null, tint = SigurColors.Suspect, modifier = Modifier.size(16.dp))
            Spacer(modifier = Modifier.width(6.dp))
            Text("🔍 Verificare Ofertă / Campanie (AI)", fontWeight = FontWeight.Bold, color = SigurColors.TextPrimary, fontSize = 14.sp)
        }
        
        Spacer(modifier = Modifier.height(8.dp))
        
        Card(
            colors = CardDefaults.cardColors(containerColor = SigurColors.SuspectLight),
            border = BorderStroke(1.dp, SigurColors.SuspectBorder),
            shape = RoundedCornerShape(12.dp)
        ) {
            Text(
                text = analysis,
                color = SigurColors.TextSecondary,
                fontSize = 13.sp,
                lineHeight = 20.sp,
                modifier = Modifier.padding(12.dp)
            )
        }
    }
}

@Composable
fun ComplianceSection(authSummary: String) {
    Column(modifier = Modifier.padding(vertical = 12.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(Icons.Default.CheckCircle, contentDescription = null, tint = SigurColors.Safe, modifier = Modifier.size(16.dp))
            Spacer(modifier = Modifier.width(6.dp))
            Text("Autentificare email (DKIM/SPF/DMARC)", fontWeight = FontWeight.Bold, color = SigurColors.TextPrimary, fontSize = 14.sp)
        }

        Spacer(modifier = Modifier.height(8.dp))

        Card(
            colors = CardDefaults.cardColors(containerColor = SigurColors.SafeLight),
            border = BorderStroke(1.dp, SigurColors.SafeBorder),
            shape = RoundedCornerShape(12.dp)
        ) {
            Text(
                text = authSummary,
                color = SigurColors.TextSecondary,
                fontSize = 12.sp,
                modifier = Modifier.padding(12.dp)
            )
        }
    }
}

@Composable
fun ButtonsSection(buttons: List<String>) {
    Column(modifier = Modifier.padding(vertical = 12.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(Icons.Default.TouchApp, contentDescription = null, tint = SigurColors.Suspect, modifier = Modifier.size(16.dp))
            Spacer(modifier = Modifier.width(6.dp))
            Text("Butoane Detectate În E-mail", fontWeight = FontWeight.Bold, color = SigurColors.TextPrimary, fontSize = 14.sp)
        }

        Spacer(modifier = Modifier.height(8.dp))

        Card(
            colors = CardDefaults.cardColors(containerColor = SigurColors.SuspectLight),
            border = BorderStroke(1.dp, SigurColors.SuspectBorder),
            shape = RoundedCornerShape(12.dp)
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                buttons.forEach { button ->
                    Text("• $button", color = SigurColors.TextSecondary, fontSize = 12.sp)
                }
            }
        }
    }
}

@Composable
fun SincerityPillarsSection(assessment: OfflineAssessment) {
    Column(modifier = Modifier.padding(vertical = 12.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(Icons.Default.Verified, contentDescription = null, tint = SigurColors.Safe, modifier = Modifier.size(16.dp))
            Spacer(modifier = Modifier.width(6.dp))
            Text("Detalii de verificare", fontWeight = FontWeight.Bold, color = SigurColors.TextPrimary, fontSize = 14.sp)
        }
        
        Spacer(modifier = Modifier.height(8.dp))
        
        Card(
            colors = CardDefaults.cardColors(containerColor = SigurColors.BackgroundSurface),
            border = BorderStroke(1.dp, SigurColors.GlassBorder),
            shape = RoundedCornerShape(12.dp)
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                PillarRow("1. Cazier Global", assessment.reputationVerdict, Icons.Default.Public)
                PillarRow("2. Vârsta Domeniului", assessment.domainAgeText, Icons.Default.History)
                PillarRow("3. Infrastructură (SSL)", assessment.sslStatus, Icons.Default.Lock)
                PillarRow("4. Analiză de Conținut", assessment.aiConfidence, Icons.Default.AutoAwesome)
            }
        }
    }
}

@Composable
fun PillarRow(label: String, value: String, icon: ImageVector) {
    Row(
        modifier = Modifier.padding(vertical = 6.dp).fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(icon, contentDescription = null, tint = SigurColors.TextMuted, modifier = Modifier.size(14.dp))
            Spacer(modifier = Modifier.width(8.dp))
            Text(label, color = SigurColors.TextSecondary, fontSize = 12.sp)
        }
        Text(value, color = SigurColors.TextPrimary, fontSize = 12.sp, fontWeight = FontWeight.Bold)
    }
}

@Composable
fun ThreatIntelSection(items: List<ThreatIntelSourceResult>, sandboxReportUrl: String?) {
    val context = LocalContext.current

    Column(modifier = Modifier.padding(vertical = 12.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(Icons.Default.Security, contentDescription = null, tint = SigurColors.Brand, modifier = Modifier.size(16.dp))
            Spacer(modifier = Modifier.width(6.dp))
            Text("Surse de verificare", fontWeight = FontWeight.Bold, color = SigurColors.TextPrimary, fontSize = 14.sp)
        }

        Spacer(modifier = Modifier.height(8.dp))

        Card(
            colors = CardDefaults.cardColors(containerColor = SigurColors.BackgroundSurface),
            border = BorderStroke(1.dp, SigurColors.GlassBorder),
            shape = RoundedCornerShape(12.dp)
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                items.forEach { item ->
                    val statusColor = when (item.severity.lowercase(Locale.getDefault())) {
                        "high", "critical" -> SigurColors.Dangerous
                        "medium", "warning", "suspicious" -> SigurColors.Suspect
                        "low", "safe", "clean" -> SigurColors.Safe
                        else -> SigurColors.TextMuted
                    }
                    Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.Top) {
                        Box(
                            modifier = Modifier
                                .padding(top = 5.dp)
                                .size(8.dp)
                                .border(1.dp, statusColor, RoundedCornerShape(99.dp))
                        )
                        Spacer(modifier = Modifier.width(10.dp))
                        Column(modifier = Modifier.weight(1f)) {
                            Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                                Text(publicThreatSource(item.source), color = SigurColors.TextPrimary, fontWeight = FontWeight.Bold, fontSize = 12.sp)
                                Text(publicThreatVerdict(item.verdict), color = statusColor, fontWeight = FontWeight.Bold, fontSize = 11.sp)
                            }
                            publicThreatDetails(item.details)?.let { details ->
                                Text(details, color = SigurColors.TextSecondary, fontSize = 11.sp, lineHeight = 16.sp)
                            }
                        }
                    }
                    Spacer(modifier = Modifier.height(10.dp))
                }

                sandboxReportUrl?.takeIf { BuildConfig.DEBUG }?.let { url ->
                    TextButton(
                        onClick = {
                            runCatching {
                                context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
                            }
                        },
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Icon(Icons.Default.OpenInNew, contentDescription = null, tint = SigurColors.Brand, modifier = Modifier.size(14.dp))
                        Spacer(modifier = Modifier.width(6.dp))
                        Text("Deschide detalii tehnice", color = SigurColors.Brand, fontSize = 12.sp)
                    }
                }
            }
        }
    }
}

internal fun publicThreatSource(source: String): String {
    val normalized = source.lowercase(Locale.getDefault())
    return when {
        normalized.contains("urlscan") -> "Analiză izolată"
        normalized.contains("web risk") || normalized.contains("webrisk") || normalized.contains("google") -> "Reputație globală"
        normalized.contains("phishing.database") || normalized.contains("phishing_database") -> "Listă phishing activ"
        normalized.contains("backend") -> "Analiză SigurScan"
        else -> "Sursă de verificare"
    }
}

internal fun publicThreatVerdict(verdict: String): String {
    val normalized = verdict.lowercase(Locale.getDefault())
    return when {
        normalized.contains("pending") || normalized.contains("queued") || normalized.contains("processing") -> "În verificare"
        normalized.contains("malware") || normalized.contains("phish") || normalized.contains("malicious") || normalized.contains("threat") -> "Periculos"
        normalized.contains("clean") || normalized.contains("no malicious") || normalized.contains("no threat") || normalized.contains("no classification") -> "Sigur"
        normalized.isBlank() -> "În verificare"
        else -> "Suspect"
    }
}

internal fun publicThreatDetails(details: String?): String? {
    val value = details?.trim()?.takeIf { it.isNotBlank() } ?: return null
    val normalized = value.lowercase(Locale.getDefault())
    return when {
        normalized.contains("http ") ||
            normalized.contains("exception") ||
            normalized.contains("api key") ||
            normalized.contains("backend") ||
            normalized.contains("urlscan") ||
            normalized.contains("phishing.database") ||
            normalized.contains("phishing_database") ||
            normalized.contains("web risk") ||
            normalized.contains("engines:") ||
            normalized.contains("sandbox") ->
            "Verificarea online nu a returnat suficiente detalii publice. Folosește și canalul oficial."
        normalized.contains("queued") || normalized.contains("processing") || normalized.contains("attempt") ->
            "Verificarea online este încă în curs."
        normalized.contains("not configured") || normalized.contains("unavailable") || normalized.contains("timeout") ->
            "Unele surse online nu sunt disponibile momentan."
        else -> value.take(180)
    }
}

@Composable
fun RedirectChainSection(chain: List<String>, finalUrl: String?) {
    if (chain.isNotEmpty() || finalUrl != null) {
        Column(modifier = Modifier.padding(vertical = 12.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.Link, contentDescription = null, tint = SigurColors.Brand, modifier = Modifier.size(16.dp))
                Spacer(modifier = Modifier.width(6.dp))
                Text("Analiză linkuri și redirecționări", fontWeight = FontWeight.Bold, color = SigurColors.TextPrimary, fontSize = 14.sp)
            }
            
            Spacer(modifier = Modifier.height(8.dp))
            
            Card(
                colors = CardDefaults.cardColors(containerColor = SigurColors.BackgroundSurface),
                border = BorderStroke(1.dp, SigurColors.GlassBorder),
                shape = RoundedCornerShape(10.dp)
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Text("Urmărirea redirecționărilor a arătat următoarele:", color = SigurColors.TextSecondary, fontSize = 11.sp)
                    Spacer(modifier = Modifier.height(8.dp))
                    
                    chain.forEachIndexed { index, url ->
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(
                                text = "${index + 1}. ",
                                color = SigurColors.Brand,
                                fontWeight = FontWeight.Bold,
                                fontSize = 11.sp
                            )
                            Text(
                                text = url,
                                color = SigurColors.TextPrimary,
                                fontSize = 11.sp,
                                maxLines = 1,
                                modifier = Modifier.weight(1f)
                            )
                        }
                        if (index < chain.size - 1) {
                            Icon(Icons.Default.ArrowDownward, contentDescription = null, tint = SigurColors.TextMuted, modifier = Modifier.size(12.dp).padding(start = 12.dp))
                        }
                    }
                    
                    if (finalUrl != null && !chain.contains(finalUrl)) {
                        Spacer(modifier = Modifier.height(4.dp))
                        Icon(Icons.Default.ArrowDownward, contentDescription = null, tint = SigurColors.TextMuted, modifier = Modifier.size(12.dp).padding(start = 12.dp))
                        Text(
                            text = "DESTINAȚIE FINALĂ: $finalUrl",
                            color = SigurColors.Safe,
                            fontWeight = FontWeight.Bold,
                            fontSize = 11.sp,
                            modifier = Modifier.padding(top = 4.dp)
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun EvidenceSection(screenshotUrl: String?, serverInfo: String?, finalUrl: String?) {
    if (screenshotUrl != null || finalUrl != null) {
        val screenshotModel = sandboxScreenshotModel(screenshotUrl)
        val previewPending = screenshotUrl == null && serverInfo?.contains("genere", ignoreCase = true) == true

        Column(modifier = Modifier.padding(vertical = 12.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.Visibility, contentDescription = null, tint = SigurColors.Brand, modifier = Modifier.size(16.dp))
                Spacer(modifier = Modifier.width(6.dp))
                Text("Preview securizat", fontWeight = FontWeight.Bold, color = SigurColors.TextPrimary, fontSize = 14.sp)
            }
            
            Spacer(modifier = Modifier.height(8.dp))
            
            Card(
                shape = RoundedCornerShape(12.dp),
                border = BorderStroke(1.dp, SigurColors.GlassBorder),
                modifier = Modifier
                    .fillMaxWidth()
                    .height(220.dp),
                colors = CardDefaults.cardColors(containerColor = SigurColors.BackgroundSurface)
            ) {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    if (screenshotModel == null) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            if (previewPending) {
                                CircularProgressIndicator(color = SigurColors.Brand, modifier = Modifier.size(30.dp))
                            } else if (screenshotUrl == null) {
                                Icon(Icons.Default.Visibility, contentDescription = null, tint = SigurColors.TextMuted, modifier = Modifier.size(30.dp))
                            } else {
                                CircularProgressIndicator(color = SigurColors.Brand, modifier = Modifier.size(30.dp))
                            }
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                text = if (previewPending || screenshotUrl != null) {
                                    "Se generează captura paginii finale..."
                                } else {
                                    "Preview indisponibil momentan"
                                },
                                color = SigurColors.TextPrimary,
                                fontSize = 10.sp
                            )
                            finalUrl?.let {
                                Text(
                                    text = "Destinație verificată: ${it.take(72)}",
                                    color = SigurColors.TextMuted,
                                    fontSize = 9.sp,
                                    textAlign = TextAlign.Center,
                                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 4.dp)
                                )
                            }
                        }
	                    } else {
	                        val localBitmap = remember(screenshotModel) {
	                            screenshotModel
	                                ?.takeIf { it.startsWith("file://", ignoreCase = true) }
	                                ?.let { Uri.parse(it).path }
	                                ?.let { path -> runCatching { BitmapFactory.decodeFile(path) }.getOrNull() }
	                        }
	                        if (localBitmap != null) {
	                            androidx.compose.foundation.Image(
	                                bitmap = localBitmap.asImageBitmap(),
                                contentDescription = "Captură izolată a paginii finale",
	                                modifier = Modifier.fillMaxSize(),
	                                contentScale = androidx.compose.ui.layout.ContentScale.Fit
	                            )
	                        } else {
	                            SubcomposeAsyncImage(
	                                model = screenshotModel,
	                                contentDescription = "Captură izolată a paginii finale",
	                                modifier = Modifier.fillMaxSize(),
	                                contentScale = androidx.compose.ui.layout.ContentScale.Fit,
	                                loading = {
	                                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
	                                        CircularProgressIndicator(color = SigurColors.Brand, modifier = Modifier.size(30.dp))
	                                        Spacer(modifier = Modifier.height(8.dp))
	                                        Text("Se încarcă preview-ul securizat...", color = SigurColors.TextPrimary, fontSize = 10.sp)
	                                    }
	                                },
	                                error = {
	                                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
	                                        Icon(Icons.Default.HourglassEmpty, contentDescription = null, tint = SigurColors.TextMuted)
	                                        Text("Captura încă se procesează...", color = SigurColors.TextMuted, fontSize = 10.sp)
	                                        Text("(reîncercare automată)", color = Color(0xFF4B5563), fontSize = 9.sp)
	                                    }
	                                }
	                            )
	                        }
	                    }
                    
                    // Overlay for info
                    Surface(
                        color = SigurColors.TextPrimary.copy(alpha = 0.72f),
                        modifier = Modifier
                            .align(Alignment.BottomCenter)
                            .fillMaxWidth()
                    ) {
                        Text(
                            text = publicServerInfo(serverInfo),
                            color = SigurColors.TextInverse,
                            fontSize = 11.sp,
                            modifier = Modifier.padding(8.dp),
                            textAlign = TextAlign.Center
                        )
                    }
                }
            }
            Text(
                "Aceasta este o imagine izolată a paginii finale, nu site-ul real. Nu interacționezi cu pagina.",
                color = SigurColors.TextSecondary,
                fontSize = 10.sp,
                modifier = Modifier.padding(top = 4.dp, start = 4.dp)
            )
        }
    }
}

internal fun sandboxScreenshotModel(screenshotUrl: String?): String? =
    screenshotUrl
        ?.takeIf { it.isNotBlank() }

internal fun publicServerInfo(serverInfo: String?): String {
    val value = serverInfo?.trim()?.takeIf { it.isNotBlank() } ?: return "Preview securizat al paginii finale"
    val normalized = value.lowercase(Locale.getDefault())
    return when {
        normalized.contains("server:") || normalized.contains("backend") || normalized.contains("http ") || normalized.contains("sandbox") ->
            "Preview securizat al paginii finale"
        normalized.contains("genere") || normalized.contains("processing") || normalized.contains("pending") ->
            "Preview-ul securizat se generează."
        else -> value.take(140)
    }
}
