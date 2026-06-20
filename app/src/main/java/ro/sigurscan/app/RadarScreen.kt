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
fun RadarTab(viewModel: ScannerViewModel) {
    val context = LocalContext.current
    var hasMicrophonePermission by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.RECORD_AUDIO
            ) == PackageManager.PERMISSION_GRANTED
        )
    }
    val microphonePermissionLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        hasMicrophonePermission = granted
        viewModel.refreshAudioReadiness()
        if (granted) {
            viewModel.startSpeakerGuard()
        } else {
            viewModel.audioReadinessStatus = "Permisiunea microfonului este necesară pentru Speaker Guard."
        }
    }
    val locatedCampaigns = remember(viewModel.campaigns) {
        viewModel.campaigns.count { it.lat != null && it.lon != null }
    }
    var selectedCampaign by remember { mutableStateOf<ScamCampaign?>(null) }
    val onMapCampaignSelected: (ScamCampaign?) -> Unit = { selectedCampaign = it }

    val campaignPins = remember(viewModel.campaigns) {
        viewModel.campaigns.filter { it.lat != null && it.lon != null }
    }
    var selectedCircleMemberId by remember { mutableStateOf<String?>(null) }
    val selectedCircleMember = remember(viewModel.familyMembers.toList(), selectedCircleMemberId) {
        viewModel.familyMembers.firstOrNull { it.id == selectedCircleMemberId }
            ?: viewModel.familyMembers.firstOrNull { it.isProtected }
            ?: viewModel.familyMembers.firstOrNull()
    }

    Column(modifier = Modifier.fillMaxSize().padding(20.dp).verticalScroll(rememberScrollState())) {
        Text("Radar Scam", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = SigurColors.TextPrimary)
        Spacer(modifier = Modifier.height(16.dp))

        RadarCallProtectionCard(
            cache = viewModel.radarHotCache,
            audit = viewModel.radarScreeningAudit,
            loading = viewModel.radarHotCacheLoading,
            status = viewModel.radarHotCacheStatus,
            reportPhoneInput = viewModel.radarReportPhoneInput,
            reportPhoneLoading = viewModel.radarReportPhoneLoading,
            reportPhoneStatus = viewModel.radarReportPhoneStatus,
            onSync = { viewModel.syncRadarHotCache() },
            onRefreshAudit = { viewModel.refreshRadarScreeningAudit() },
            onEnableRole = { requestCallScreeningRole(context) },
            onReportPhoneInputChange = { viewModel.radarReportPhoneInput = it },
            onReportPhone = { viewModel.reportRadarPhoneNumber() }
        )
        Spacer(modifier = Modifier.height(16.dp))

        BtrOnDeviceCard(
            snapshot = viewModel.btrSyncSnapshot,
            verdict = viewModel.inboxProvenanceVerdict,
            loading = viewModel.btrSyncLoading,
            status = viewModel.btrSyncStatus,
            provenanceStatus = viewModel.inboxProvenanceStatus,
            onSync = { viewModel.syncBtrManifests() },
            onLocalCheck = { viewModel.runLocalInboxProvenanceCheck() }
        )
        Spacer(modifier = Modifier.height(16.dp))

        CircleGuardianCard(
            members = viewModel.familyMembers,
            selectedMember = selectedCircleMember,
            onSelectedMember = { selectedCircleMemberId = it.id },
            snapshot = viewModel.circleSnapshot,
            circleLoading = viewModel.circleLoading,
            circleStatus = viewModel.circleStatus,
            guardianLoading = viewModel.guardianLoading,
            guardianStatus = viewModel.guardianStatus,
            hasAssessment = viewModel.assessment != null,
            onPair = { viewModel.createCirclePair(selectedCircleMember) },
            onPing = { viewModel.createCirclePing() },
            onResolve = { viewModel.resolveCirclePing(it) },
            onRevoke = { viewModel.revokeCirclePair() },
            onGuardian = { shareLevel, consent ->
                viewModel.requestGuardianSecondOpinion(selectedCircleMember, shareLevel, consent)
            }
        )
        Spacer(modifier = Modifier.height(16.dp))

        if (BuildConfig.SIGURSCAN_ENABLE_AUDIO_ASR) {
            AudioAsrReadinessCard(
                snapshot = viewModel.audioReadiness,
                status = viewModel.audioReadinessStatus,
                evidenceResult = viewModel.audioEvidenceResult,
                hasAssessment = viewModel.assessment != null,
                onConsentChanged = { viewModel.setAudioConsent(it) },
                onDisclosureChanged = { viewModel.setAudioPrivacyDisclosureAccepted(it) },
                onRefresh = { viewModel.refreshAudioReadiness() },
                onAnalyzeTranscript = { viewModel.analyzeCurrentTextAsAudioTranscript() },
                speakerGuard = viewModel.speakerGuardSnapshot,
                hasMicrophonePermission = hasMicrophonePermission,
                onStartSpeakerGuard = {
                    if (!hasMicrophonePermission) {
                        microphonePermissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
                    } else {
                        viewModel.startSpeakerGuard()
                    }
                },
                onStopSpeakerGuard = { viewModel.stopSpeakerGuard() }
            )
            Spacer(modifier = Modifier.height(16.dp))
        }

        viewModel.liveCampaignEvent?.let { liveCampaignEvent ->
            ActiveCampaignBanner(liveCampaignEvent) {
                viewModel.clearLiveCampaignEvent()
            }
            Spacer(modifier = Modifier.height(12.dp))
        }

        viewModel.activeCampaignAlert?.let { activeCampaignAlert ->
            Card(
                colors = CardDefaults.cardColors(containerColor = SigurColors.DangerousLight),
                border = BorderStroke(1.dp, SigurColors.DangerousBorder),
                shape = DSCardShape
            ) {
                Text(
                    text = activeCampaignAlert,
                    color = SigurColors.Dangerous,
                    fontSize = 12.sp,
                    modifier = Modifier.padding(10.dp)
                )
            }
            Spacer(modifier = Modifier.height(16.dp))
        }

        if (locatedCampaigns > 0) {
            Card(
                colors = CardDefaults.cardColors(containerColor = SigurColors.BrandTint),
                border = BorderStroke(1.dp, SigurColors.Brand.copy(alpha = 0.20f)),
                shape = DSCardShape
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.Place, contentDescription = null, tint = SigurColors.Brand)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Radar Geographic", color = SigurColors.TextPrimary, fontWeight = FontWeight.Bold)
                    }
                    Spacer(modifier = Modifier.height(8.dp))
                    Text("Am mapat $locatedCampaigns campanii pe hartă. Atinge un marker pentru detalii.", color = SigurColors.TextSecondary, fontSize = 12.sp)
                }
            }
            Spacer(modifier = Modifier.height(16.dp))
    RadarMapCard(
                campaigns = campaignPins,
                onCampaignSelected = onMapCampaignSelected
            )
            Spacer(modifier = Modifier.height(16.dp))
        }

        ActiveCampaignsSection(viewModel.campaigns, viewModel.campaignsLoading)
        Spacer(modifier = Modifier.height(8.dp))
        TextButton(
            onClick = { viewModel.loadCampaigns() },
            modifier = Modifier.align(Alignment.CenterHorizontally)
        ) {
            Icon(Icons.Default.Refresh, contentDescription = null, tint = SigurColors.Brand, modifier = Modifier.size(16.dp))
            Spacer(modifier = Modifier.width(8.dp))
            Text("Reîncarcă campanii", color = SigurColors.Brand)
        }

        selectedCampaign?.let { campaign ->
            Spacer(modifier = Modifier.height(12.dp))
            CampaignBottomCard(campaign = campaign) {
                openCampaignOnMap(
                    context,
                    campaign.lat,
                    campaign.lon,
                    campaign.title
                )
            }
        }
    }
}

@Composable
internal fun BtrOnDeviceCard(
    snapshot: BtrSyncSnapshot?,
    verdict: InboxProvenanceVerdict?,
    loading: Boolean,
    status: String?,
    provenanceStatus: String?,
    onSync: () -> Unit,
    onLocalCheck: () -> Unit
) {
    val cacheText = snapshot?.let {
        "${it.manifests.size} manifeste oficiale • ${it.version}"
    } ?: "Registru oficial local indisponibil"

    Card(
        colors = CardDefaults.cardColors(containerColor = SigurColors.BackgroundCard),
        border = DSCardBorder,
        shape = DSCardShape,
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.VerifiedUser, contentDescription = null, tint = SigurColors.Safe, modifier = Modifier.size(18.dp))
                Spacer(modifier = Modifier.width(8.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text("BTR on-device", color = SigurColors.TextPrimary, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                    Text(cacheText, color = SigurColors.TextMuted, fontSize = 11.sp, lineHeight = 15.sp)
                }
                DSChip(if (snapshot == null) "necesită sync" else "local", tone = if (snapshot == null) DSChipTone.Pending else DSChipTone.Safe)
            }
            Text(
                "Manifestele coboară pe telefon; conținutul SMS nu este trimis la server.",
                color = SigurColors.TextSecondary,
                fontSize = 11.sp,
                lineHeight = 15.sp,
                modifier = Modifier.padding(top = 8.dp)
            )
            status?.takeIf { it.isNotBlank() }?.let {
                Spacer(modifier = Modifier.height(8.dp))
                Text(it, color = SigurColors.TextSecondary, fontSize = 11.sp, lineHeight = 15.sp)
            }
            verdict?.let {
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    "Ultima verificare locală: ${it.verdict.name.lowercase(Locale.getDefault())} · ${it.reasonCodes.joinToString(", ")}",
                    color = SigurColors.TextMuted,
                    fontSize = 11.sp,
                    lineHeight = 15.sp
                )
            }
            provenanceStatus?.takeIf { it.isNotBlank() }?.let {
                Spacer(modifier = Modifier.height(6.dp))
                Text(it, color = SigurColors.TextSecondary, fontSize = 11.sp, lineHeight = 15.sp)
            }
            Spacer(modifier = Modifier.height(12.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                Button(
                    onClick = onSync,
                    enabled = !loading,
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.buttonColors(containerColor = SigurColors.SafeLight),
                    border = BorderStroke(1.dp, SigurColors.SafeBorder),
                    shape = DSPillShape
                ) {
                    Icon(Icons.Default.Download, contentDescription = null, tint = SigurColors.Safe, modifier = Modifier.size(14.dp))
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(if (loading) "Sync..." else "Sincronizează", color = SigurColors.Safe, fontSize = 11.sp)
                }
                Button(
                    onClick = onLocalCheck,
                    enabled = snapshot != null,
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.buttonColors(containerColor = SigurColors.BackgroundSurface),
                    border = BorderStroke(1.dp, SigurColors.GlassBorder),
                    shape = DSPillShape
                ) {
                    Icon(Icons.Default.Verified, contentDescription = null, tint = SigurColors.TextPrimary, modifier = Modifier.size(14.dp))
                    Spacer(modifier = Modifier.width(6.dp))
                    Text("Verifică local", color = SigurColors.TextPrimary, fontSize = 11.sp)
                }
            }
        }
    }
}

@Composable
internal fun CircleGuardianCard(
    members: List<FamilyMember>,
    selectedMember: FamilyMember?,
    onSelectedMember: (FamilyMember) -> Unit,
    snapshot: CircleProtectionSnapshot,
    circleLoading: Boolean,
    circleStatus: String?,
    guardianLoading: Boolean,
    guardianStatus: String?,
    hasAssessment: Boolean,
    onPair: () -> Unit,
    onPing: () -> Unit,
    onResolve: (String) -> Unit,
    onRevoke: () -> Unit,
    onGuardian: (String, Boolean) -> Unit
) {
    var memberMenuExpanded by remember { mutableStateOf(false) }
    var guardianShareLevel by remember { mutableStateOf("metadata_only") }
    var fullConsent by remember { mutableStateOf(false) }
    val link = snapshot.link
    val ping = snapshot.ping
    val outcome = snapshot.outcome
    val guardian = snapshot.guardianOpinion
    val activeLink = link?.active == true

    Card(
        colors = CardDefaults.cardColors(containerColor = SigurColors.BackgroundCard),
        border = DSCardBorder,
        shape = DSCardShape,
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.Group, contentDescription = null, tint = SigurColors.Brand, modifier = Modifier.size(18.dp))
                Spacer(modifier = Modifier.width(8.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text("Cercul + Guardian", color = SigurColors.TextPrimary, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                    Text(
                        "Verificare out-of-band; fără acces la conținut brut.",
                        color = SigurColors.TextMuted,
                        fontSize = 11.sp,
                        lineHeight = 15.sp
                    )
                }
                DSChip(
                    text = if (activeLink) "activ" else "neconfigurat",
                    tone = if (activeLink) DSChipTone.Safe else DSChipTone.Pending
                )
            }

            Spacer(modifier = Modifier.height(12.dp))

            if (members.isEmpty()) {
                Text(
                    "Adaugă întâi o persoană de încredere în Mai mult > Securitate și Familie.",
                    color = SigurColors.TextSecondary,
                    fontSize = 11.sp,
                    lineHeight = 15.sp
                )
            } else {
                Box {
                    Button(
                        onClick = { memberMenuExpanded = true },
                        modifier = Modifier.fillMaxWidth(),
                        colors = ButtonDefaults.buttonColors(containerColor = SigurColors.BackgroundSurface),
                        border = BorderStroke(1.dp, SigurColors.GlassBorder),
                        shape = DSPillShape
                    ) {
                        Icon(Icons.Default.Person, contentDescription = null, tint = SigurColors.TextPrimary, modifier = Modifier.size(14.dp))
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            selectedMember?.name ?: "Alege persoana",
                            color = SigurColors.TextPrimary,
                            fontSize = 12.sp
                        )
                    }
                    DropdownMenu(expanded = memberMenuExpanded, onDismissRequest = { memberMenuExpanded = false }) {
                        members.forEach { member ->
                            DropdownMenuItem(
                                text = {
                                    Column {
                                        Text(member.name)
                                        Text(member.contact, fontSize = 11.sp, color = SigurColors.TextMuted)
                                    }
                                },
                                onClick = {
                                    onSelectedMember(member)
                                    memberMenuExpanded = false
                                }
                            )
                        }
                    }
                }
            }

            circleStatus?.takeIf { it.isNotBlank() }?.let {
                Spacer(modifier = Modifier.height(8.dp))
                Text(it, color = SigurColors.TextSecondary, fontSize = 11.sp, lineHeight = 15.sp)
            }

            link?.let {
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    "Link: ${it.linkId} • citire conținut: ${if (it.verifierCanReadContent) "da" else "nu"} • supraveghere: ${if (it.verifierCanSurveil) "da" else "nu"}",
                    color = SigurColors.TextMuted,
                    fontSize = 10.sp,
                    lineHeight = 14.sp
                )
            }

            ping?.let {
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    "Ping: ${it.pingId} • ${it.payloadClass ?: "metadata_only"} • timeout=${it.defaultOnTimeout ?: "PRECAUTIE"}",
                    color = SigurColors.TextMuted,
                    fontSize = 10.sp,
                    lineHeight = 14.sp
                )
            }

            outcome?.let {
                Spacer(modifier = Modifier.height(8.dp))
                val tone = when (it.status) {
                    "CONFIRMED" -> DSChipTone.Safe
                    "REJECTED" -> DSChipTone.Danger
                    else -> DSChipTone.Suspect
                }
                DSChip(text = (it.status ?: "PRECAUTIE"), tone = tone)
            }

            Spacer(modifier = Modifier.height(12.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                Button(
                    onClick = onPair,
                    enabled = !circleLoading && selectedMember != null,
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.buttonColors(containerColor = SigurColors.BrandTint),
                    border = BorderStroke(1.dp, SigurColors.Brand),
                    shape = DSPillShape
                ) {
                    Icon(Icons.Default.Link, contentDescription = null, tint = SigurColors.Brand, modifier = Modifier.size(14.dp))
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(if (circleLoading) "..." else "Leagă", color = SigurColors.Brand, fontSize = 11.sp)
                }
                Button(
                    onClick = onPing,
                    enabled = !circleLoading && activeLink,
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.buttonColors(containerColor = SigurColors.SafeLight),
                    border = BorderStroke(1.dp, SigurColors.SafeBorder),
                    shape = DSPillShape
                ) {
                    Icon(Icons.Default.Send, contentDescription = null, tint = SigurColors.Safe, modifier = Modifier.size(14.dp))
                    Spacer(modifier = Modifier.width(6.dp))
                    Text("Ping", color = SigurColors.Safe, fontSize = 11.sp)
                }
            }

            Spacer(modifier = Modifier.height(8.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                Button(
                    onClick = { onResolve("its_me") },
                    enabled = !circleLoading && ping != null,
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.buttonColors(containerColor = SigurColors.SafeLight),
                    border = BorderStroke(1.dp, SigurColors.SafeBorder),
                    shape = DSPillShape
                ) {
                    Text("Confirmă", color = SigurColors.Safe, fontSize = 11.sp)
                }
                Button(
                    onClick = { onResolve("not_me") },
                    enabled = !circleLoading && ping != null,
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.buttonColors(containerColor = SigurColors.DangerousLight),
                    border = BorderStroke(1.dp, SigurColors.DangerousBorder),
                    shape = DSPillShape
                ) {
                    Text("Respinge", color = SigurColors.Dangerous, fontSize = 11.sp)
                }
                Button(
                    onClick = { onResolve("timeout") },
                    enabled = !circleLoading && ping != null,
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.buttonColors(containerColor = SigurColors.SuspectLight),
                    border = BorderStroke(1.dp, SigurColors.SuspectBorder),
                    shape = DSPillShape
                ) {
                    Text("Timeout", color = SigurColors.Suspect, fontSize = 11.sp)
                }
            }

            Spacer(modifier = Modifier.height(14.dp))
            HorizontalDivider(color = SigurColors.GlassBorder)
            Spacer(modifier = Modifier.height(12.dp))

            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.VerifiedUser, contentDescription = null, tint = SigurColors.Safe, modifier = Modifier.size(16.dp))
                Spacer(modifier = Modifier.width(8.dp))
                Text("Guardian second opinion", color = SigurColors.TextPrimary, fontWeight = FontWeight.SemiBold, fontSize = 13.sp)
            }
            Text(
                if (hasAssessment) "Trimite doar rezumat redactat al scanării curente." else "Poți cere o opinie metadata-only chiar fără scanare curentă.",
                color = SigurColors.TextSecondary,
                fontSize = 11.sp,
                lineHeight = 15.sp,
                modifier = Modifier.padding(top = 6.dp)
            )

            Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(top = 8.dp)) {
                Checkbox(
                    checked = guardianShareLevel == "redacted_excerpt",
                    onCheckedChange = { checked ->
                        guardianShareLevel = if (checked) "redacted_excerpt" else "metadata_only"
                    }
                )
                Text("Include extras redactat", color = SigurColors.TextSecondary, fontSize = 11.sp)
            }
            Row(verticalAlignment = Alignment.CenterVertically) {
                Checkbox(
                    checked = fullConsent,
                    onCheckedChange = { fullConsent = it }
                )
                Text("Consimțământ explicit pentru full_with_consent", color = SigurColors.TextSecondary, fontSize = 11.sp)
            }

            guardianStatus?.takeIf { it.isNotBlank() }?.let {
                Spacer(modifier = Modifier.height(8.dp))
                Text(it, color = SigurColors.TextSecondary, fontSize = 11.sp, lineHeight = 15.sp)
            }
            guardian?.let {
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    "Request: ${it.requestId} • share=${it.shareLevel ?: "metadata_only"} • downgraded=${it.shareDowngraded}",
                    color = SigurColors.TextMuted,
                    fontSize = 10.sp,
                    lineHeight = 14.sp
                )
            }

            Spacer(modifier = Modifier.height(10.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                Button(
                    onClick = {
                        val level = if (fullConsent) "full_with_consent" else guardianShareLevel
                        onGuardian(level, fullConsent)
                    },
                    enabled = !guardianLoading && selectedMember != null,
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.buttonColors(containerColor = SigurColors.SafeLight),
                    border = BorderStroke(1.dp, SigurColors.SafeBorder),
                    shape = DSPillShape
                ) {
                    Icon(Icons.Default.PrivacyTip, contentDescription = null, tint = SigurColors.Safe, modifier = Modifier.size(14.dp))
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(if (guardianLoading) "..." else "Cere opinie", color = SigurColors.Safe, fontSize = 11.sp)
                }
                Button(
                    onClick = onRevoke,
                    enabled = !circleLoading && link != null && activeLink,
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.buttonColors(containerColor = SigurColors.BackgroundSurface),
                    border = BorderStroke(1.dp, SigurColors.GlassBorder),
                    shape = DSPillShape
                ) {
                    Icon(Icons.Default.Delete, contentDescription = null, tint = SigurColors.TextMuted, modifier = Modifier.size(14.dp))
                    Spacer(modifier = Modifier.width(6.dp))
                    Text("Revocă", color = SigurColors.TextPrimary, fontSize = 11.sp)
                }
            }
        }
    }
}

@Composable
internal fun AudioAsrReadinessCard(
    snapshot: AudioReadinessSnapshot,
    status: String?,
    evidenceResult: AudioEvidenceResult?,
    hasAssessment: Boolean,
    onConsentChanged: (Boolean) -> Unit,
    onDisclosureChanged: (Boolean) -> Unit,
    onRefresh: () -> Unit,
    onAnalyzeTranscript: () -> Unit,
    speakerGuard: SpeakerGuardSnapshot,
    hasMicrophonePermission: Boolean,
    onStartSpeakerGuard: () -> Unit,
    onStopSpeakerGuard: () -> Unit
) {
    val blocked = !snapshot.decision.allowed
    Card(
        colors = CardDefaults.cardColors(containerColor = SigurColors.BackgroundCard),
        border = DSCardBorder,
        shape = DSCardShape,
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.MicOff, contentDescription = null, tint = if (blocked) SigurColors.Suspect else SigurColors.Safe, modifier = Modifier.size(18.dp))
                Spacer(modifier = Modifier.width(8.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text("Whisper ASR local", color = SigurColors.TextPrimary, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                    Text("Nu se trimite audio la server. Captura pornește doar cu Whisper local și consimțământ.", color = SigurColors.TextMuted, fontSize = 11.sp, lineHeight = 15.sp)
                }
                DSChip(if (blocked) "blocat" else "pregătit", tone = if (blocked) DSChipTone.Suspect else DSChipTone.Safe)
            }

            Spacer(modifier = Modifier.height(10.dp))
            ReadinessRow("Feature flag", snapshot.featureFlagEnabled)
            ReadinessRow("Model Whisper local", snapshot.modelAvailable)
            ReadinessRow("Runtime Whisper native", snapshot.nativeRuntimeAvailable)
            ReadinessRow("Permisiune microfon", snapshot.microphonePermissionGranted || hasMicrophonePermission)
            ReadinessRow("Consimțământ explicit", snapshot.explicitConsent)
            ReadinessRow("Disclosure privacy acceptat", snapshot.privacyDisclosureAccepted)

            Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(top = 8.dp)) {
                Checkbox(checked = snapshot.explicitConsent, onCheckedChange = onConsentChanged)
                Text("Accept pornirea capturii audio locale", color = SigurColors.TextSecondary, fontSize = 11.sp)
            }
            Row(verticalAlignment = Alignment.CenterVertically) {
                Checkbox(checked = snapshot.privacyDisclosureAccepted, onCheckedChange = onDisclosureChanged)
                Text("Am citit că audio-ul nu părăsește telefonul", color = SigurColors.TextSecondary, fontSize = 11.sp)
            }

            status?.takeIf { it.isNotBlank() }?.let {
                Spacer(modifier = Modifier.height(8.dp))
                Text(it, color = SigurColors.TextSecondary, fontSize = 11.sp, lineHeight = 15.sp)
            }

            evidenceResult?.let { result ->
                Spacer(modifier = Modifier.height(8.dp))
                DSChip(
                    text = when (result.verdict) {
                        AudioEvidenceVerdict.DANGEROUS -> "PERICULOS"
                        AudioEvidenceVerdict.SUSPECT -> "SUSPECT"
                        AudioEvidenceVerdict.UNVERIFIED -> "NEVERIFICAT"
                    },
                    tone = when (result.verdict) {
                        AudioEvidenceVerdict.DANGEROUS -> DSChipTone.Danger
                        AudioEvidenceVerdict.SUSPECT -> DSChipTone.Suspect
                        AudioEvidenceVerdict.UNVERIFIED -> DSChipTone.Neutral
                    }
                )
            }

            Spacer(modifier = Modifier.height(10.dp))
            SpeakerGuardStatusBlock(speakerGuard)

            Spacer(modifier = Modifier.height(12.dp))
            Button(
                onClick = onRefresh,
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = SigurColors.BackgroundSurface),
                border = BorderStroke(1.dp, SigurColors.GlassBorder),
                shape = DSPillShape
            ) {
                Icon(Icons.Default.Security, contentDescription = null, tint = SigurColors.TextPrimary, modifier = Modifier.size(14.dp))
                Spacer(modifier = Modifier.width(6.dp))
                Text("Verifică readiness", color = SigurColors.TextPrimary, fontSize = 11.sp)
            }
            Spacer(modifier = Modifier.height(8.dp))
            Button(
                onClick = if (speakerGuard.active) onStopSpeakerGuard else onStartSpeakerGuard,
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (speakerGuard.active) SigurColors.DangerousLight else SigurColors.SafeLight
                ),
                border = BorderStroke(
                    1.dp,
                    if (speakerGuard.active) SigurColors.DangerousBorder else SigurColors.SafeBorder
                ),
                shape = DSPillShape
            ) {
                Icon(
                    if (speakerGuard.active) Icons.Default.Stop else Icons.Default.Mic,
                    contentDescription = null,
                    tint = if (speakerGuard.active) SigurColors.Dangerous else SigurColors.Safe,
                    modifier = Modifier.size(14.dp)
                )
                Spacer(modifier = Modifier.width(6.dp))
                Text(
                    if (speakerGuard.active) "Oprește Speaker Guard" else "Pornește Speaker Guard",
                    color = if (speakerGuard.active) SigurColors.Dangerous else SigurColors.Safe,
                    fontSize = 11.sp
                )
            }
            Spacer(modifier = Modifier.height(8.dp))
            Button(
                onClick = onAnalyzeTranscript,
                enabled = hasAssessment,
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = SigurColors.BackgroundSurface),
                border = BorderStroke(1.dp, SigurColors.GlassBorder),
                shape = DSPillShape
            ) {
                Icon(Icons.Default.Security, contentDescription = null, tint = SigurColors.TextPrimary, modifier = Modifier.size(14.dp))
                Spacer(modifier = Modifier.width(6.dp))
                Text("Analizează transcrierea curentă", color = SigurColors.TextPrimary, fontSize = 11.sp)
            }
        }
    }
}

@Composable
internal fun SpeakerGuardStatusBlock(snapshot: SpeakerGuardSnapshot) {
    val tone = when (snapshot.latestVerdict) {
        AudioEvidenceVerdict.DANGEROUS -> DSChipTone.Danger
        AudioEvidenceVerdict.SUSPECT -> DSChipTone.Suspect
        AudioEvidenceVerdict.UNVERIFIED -> DSChipTone.Neutral
        null -> if (snapshot.active) DSChipTone.Brand else DSChipTone.Neutral
    }
    Card(
        colors = CardDefaults.cardColors(containerColor = SigurColors.BackgroundSurface),
        border = BorderStroke(1.dp, SigurColors.BorderSubtle),
        shape = DSCardShape,
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(10.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    if (snapshot.active) Icons.Default.GraphicEq else Icons.Default.MicOff,
                    contentDescription = null,
                    tint = if (snapshot.active) SigurColors.Brand else SigurColors.TextMuted,
                    modifier = Modifier.size(16.dp)
                )
                Spacer(modifier = Modifier.width(6.dp))
                Text("Speaker Guard", color = SigurColors.TextPrimary, fontWeight = FontWeight.Bold, fontSize = 12.sp)
                Spacer(modifier = Modifier.weight(1f))
                DSChip(
                    when {
                        snapshot.latestVerdict == AudioEvidenceVerdict.DANGEROUS -> "PERICULOS"
                        snapshot.latestVerdict == AudioEvidenceVerdict.SUSPECT -> "SUSPECT"
                        snapshot.active -> "ascultă"
                        else -> "oprit"
                    },
                    tone = tone
                )
            }
            Spacer(modifier = Modifier.height(6.dp))
            Text(
                snapshot.status,
                color = SigurColors.TextSecondary,
                fontSize = 11.sp,
                lineHeight = 15.sp
            )
            Spacer(modifier = Modifier.height(6.dp))
            Text(
                "Fragmente analizate: ${snapshot.chunksAnalyzed} · pierdute: ${snapshot.chunksDropped} · audio brut salvat: nu",
                color = SigurColors.TextMuted,
                fontSize = 10.sp,
                lineHeight = 14.sp
            )
            snapshot.latestLatencyMs?.let { latency ->
                Text(
                    "Ultima analiză: ${latency / 1000.0}s${snapshot.latestArcFamily?.let { " · $it" } ?: ""}",
                    color = SigurColors.TextMuted,
                    fontSize = 10.sp,
                    lineHeight = 14.sp
                )
            }
        }
    }
}

@Composable
internal fun ReadinessRow(label: String, ok: Boolean) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(vertical = 2.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(label, color = SigurColors.TextSecondary, fontSize = 11.sp)
        DSChip(if (ok) "OK" else "LIPSĂ", tone = if (ok) DSChipTone.Safe else DSChipTone.Pending)
    }
}

@Composable
internal fun RadarCallProtectionCard(
    cache: RadarHotCacheSnapshot?,
    audit: RadarScreeningAudit?,
    loading: Boolean,
    status: String?,
    reportPhoneInput: String,
    reportPhoneLoading: Boolean,
    reportPhoneStatus: String?,
    onSync: () -> Unit,
    onRefreshAudit: () -> Unit,
    onEnableRole: () -> Unit,
    onReportPhoneInputChange: (String) -> Unit,
    onReportPhone: () -> Unit
) {
    val expired = cache?.isExpired() ?: true
    val cacheText = when {
        cache == null -> "Cache apeluri indisponibil"
        expired -> "Cache apeluri expirat"
        else -> "${cache.hotCampaigns.size} campanii, ${cache.numberReputation.size} numere raportate"
    }

    Card(
        colors = CardDefaults.cardColors(containerColor = SigurColors.BackgroundCard),
        border = DSCardBorder,
        shape = DSCardShape,
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.Phone, contentDescription = null, tint = SigurColors.Brand, modifier = Modifier.size(18.dp))
                Spacer(modifier = Modifier.width(8.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text("Protecție apeluri", color = SigurColors.TextPrimary, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                    Text(cacheText, color = SigurColors.TextMuted, fontSize = 11.sp, lineHeight = 15.sp)
                }
                DSChip(if (expired) "necesită sync" else "offline ready", tone = if (expired) DSChipTone.Pending else DSChipTone.Safe)
            }
            status?.takeIf { it.isNotBlank() }?.let {
                Spacer(modifier = Modifier.height(8.dp))
                Text(it, color = SigurColors.TextSecondary, fontSize = 11.sp, lineHeight = 15.sp)
            }
            audit?.let {
                Spacer(modifier = Modifier.height(8.dp))
                val checkedAt = remember(it.checkedAtEpochMillis) {
                    SimpleDateFormat("HH:mm", Locale.getDefault()).format(Date(it.checkedAtEpochMillis))
                }
                Text(
                    "Ultimul apel verificat local: ${it.action.name.lowercase(Locale.getDefault())} · ${it.reason} · $checkedAt",
                    color = SigurColors.TextMuted,
                    fontSize = 11.sp,
                    lineHeight = 15.sp
                )
            }
            Spacer(modifier = Modifier.height(12.dp))
            OutlinedTextField(
                value = reportPhoneInput,
                onValueChange = onReportPhoneInputChange,
                enabled = !reportPhoneLoading,
                singleLine = true,
                label = { Text("Număr primit") },
                supportingText = {
                    Text(
                        "Raportăm doar amprenta numărului; nu trimitem contacte sau jurnalul de apeluri.",
                        color = SigurColors.TextMuted,
                        fontSize = 10.sp,
                        lineHeight = 13.sp
                    )
                },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = SigurColors.Brand,
                    unfocusedBorderColor = SigurColors.GlassBorder,
                    focusedTextColor = SigurColors.TextPrimary,
                    unfocusedTextColor = SigurColors.TextPrimary,
                    focusedLabelColor = SigurColors.Brand,
                    unfocusedLabelColor = SigurColors.TextSecondary,
                    cursorColor = SigurColors.Brand
                ),
                modifier = Modifier.fillMaxWidth()
            )
            reportPhoneStatus?.takeIf { it.isNotBlank() }?.let {
                Spacer(modifier = Modifier.height(6.dp))
                Text(it, color = SigurColors.TextSecondary, fontSize = 11.sp, lineHeight = 15.sp)
            }
            Spacer(modifier = Modifier.height(8.dp))
            Button(
                onClick = onReportPhone,
                enabled = !reportPhoneLoading && reportPhoneInput.isNotBlank(),
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = SigurColors.BackgroundSurface),
                border = BorderStroke(1.dp, SigurColors.Brand),
                shape = DSPillShape
            ) {
                Icon(Icons.Default.Report, contentDescription = null, tint = SigurColors.Brand, modifier = Modifier.size(14.dp))
                Spacer(modifier = Modifier.width(6.dp))
                Text(if (reportPhoneLoading) "Se raportează..." else "Raportează număr suspect", color = SigurColors.Brand, fontSize = 11.sp)
            }
            Spacer(modifier = Modifier.height(12.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                Button(
                    onClick = onSync,
                    enabled = !loading,
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.buttonColors(containerColor = SigurColors.BrandTint),
                    border = BorderStroke(1.dp, SigurColors.Brand),
                    shape = DSPillShape
                ) {
                    Icon(Icons.Default.Refresh, contentDescription = null, tint = SigurColors.Brand, modifier = Modifier.size(14.dp))
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(if (loading) "Sync..." else "Sync", color = SigurColors.Brand, fontSize = 11.sp, maxLines = 1)
                }
                Button(
                    onClick = onRefreshAudit,
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.buttonColors(containerColor = SigurColors.BackgroundSurface),
                    border = BorderStroke(1.dp, SigurColors.GlassBorder),
                    shape = DSPillShape
                ) {
                    Icon(Icons.Default.History, contentDescription = null, tint = SigurColors.TextPrimary, modifier = Modifier.size(14.dp))
                    Spacer(modifier = Modifier.width(6.dp))
                    Text("Ultim", color = SigurColors.TextPrimary, fontSize = 11.sp, maxLines = 1)
                }
                Button(
                    onClick = onEnableRole,
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.buttonColors(containerColor = SigurColors.BackgroundSurface),
                    border = BorderStroke(1.dp, SigurColors.GlassBorder),
                    shape = DSPillShape
                ) {
                    Icon(Icons.Default.SettingsPhone, contentDescription = null, tint = SigurColors.TextPrimary, modifier = Modifier.size(14.dp))
                    Spacer(modifier = Modifier.width(6.dp))
                    Text("Rol", color = SigurColors.TextPrimary, fontSize = 11.sp, maxLines = 1)
                }
            }
        }
    }
}

internal fun requestCallScreeningRole(context: Context) {
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
        val roleManager = context.getSystemService(RoleManager::class.java)
        val intent = roleManager?.createRequestRoleIntent(RoleManager.ROLE_CALL_SCREENING)
        if (intent != null) {
            context.startActivity(intent)
            return
        }
    }
    val fallback = Intent(ACTION_APPLICATION_DETAILS_SETTINGS).apply {
        data = Uri.parse("package:${context.packageName}")
        addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
    }
    context.startActivity(fallback)
}

@Composable
internal fun CampaignBottomCard(campaign: ScamCampaign, onOpenMap: () -> Unit) {
    Card(
        colors = CardDefaults.cardColors(containerColor = SigurColors.BackgroundCard),
        border = DSCardBorder,
        shape = DSCardShape
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.Info, contentDescription = null, tint = SigurColors.Brand)
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = campaign.title,
                    color = SigurColors.TextPrimary,
                    fontWeight = FontWeight.Bold,
                    fontSize = 14.sp
                )
            }
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                "Brand: ${campaign.brand}",
                color = SigurColors.TextSecondary,
                fontSize = 12.sp
            )
            Text(
                "Risc: ${campaign.risk.uppercase()} • Scanări: ${campaign.count}",
                color = SigurColors.TextSecondary,
                fontSize = 12.sp
            )
            Text(
                "Mesaj: ${campaign.safeActionText}",
                color = SigurColors.TextPrimary,
                fontSize = 12.sp,
                modifier = Modifier.padding(top = 8.dp)
            )
            Spacer(modifier = Modifier.height(12.dp))
            Button(
                onClick = onOpenMap,
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = SigurColors.BrandTint),
                border = BorderStroke(1.dp, SigurColors.Brand),
                shape = DSPillShape
            ) {
                Icon(Icons.Default.Place, contentDescription = null, tint = SigurColors.Brand, modifier = Modifier.size(14.dp))
                Spacer(modifier = Modifier.width(6.dp))
                Text("Vezi locația exactă", color = SigurColors.Brand, fontSize = 11.sp)
            }
        }
    }
}

@Composable
internal fun RadarMapCard(
    campaigns: List<ScamCampaign>,
    onCampaignSelected: (ScamCampaign?) -> Unit
) {
    val campaignLookup = remember(campaigns) { campaigns.associateBy { it.id } }
    val mapHtml = remember(campaigns) { buildRadarMapHtml(campaigns) }

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .height(280.dp),
        colors = CardDefaults.cardColors(containerColor = SigurColors.BackgroundSurface),
        border = DSCardBorder,
        shape = DSCardShape
    ) {
        Column(modifier = Modifier.fillMaxSize()) {
            if (campaigns.isEmpty()) {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text("Nu sunt campanii geografice valide în acest moment.", color = SigurColors.TextMuted, fontSize = 12.sp)
                }
            } else {
                AndroidView(
                    modifier = Modifier.fillMaxSize(),
	                    factory = { context ->
	                        WebView(context).apply {
	                            settings.apply {
	                                javaScriptEnabled = false
	                                domStorageEnabled = false
	                                cacheMode = WebSettings.LOAD_NO_CACHE
	                                blockNetworkLoads = true
	                                allowFileAccess = false
	                                allowContentAccess = false
	                                mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
	                            }
	                            webViewClient = RadarWebViewClient(campaignLookup, onCampaignSelected)
	                            loadDataWithBaseURL(
	                                "https://sigurscan-radar.local/",
	                                mapHtml,
                                "text/html",
                                "UTF-8",
                                null
                            )
                        }
                    },
                    update = { webView ->
                        webView.loadDataWithBaseURL(
                            "https://sigurscan-radar.local/",
                            mapHtml,
                            "text/html",
                            "UTF-8",
                            null
                        )
                    }
                )
            }
        }
	}
}

internal class RadarWebViewClient(
    private val campaignLookup: Map<String, ScamCampaign>,
    private val onCampaignSelected: (ScamCampaign?) -> Unit
) : WebViewClient() {
    override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
        return handleRadarUri(request?.url)
    }

    @Suppress("OVERRIDE_DEPRECATION")
    override fun shouldOverrideUrlLoading(view: WebView?, url: String?): Boolean {
        return handleRadarUri(url?.let(Uri::parse))
    }

    private fun handleRadarUri(uri: Uri?): Boolean {
        if (uri?.scheme != "sigurscan-radar" || uri.host != "campaign") return true
        val campaignId = uri.lastPathSegment.orEmpty()
        onCampaignSelected(campaignLookup[campaignId])
        return true
    }
}

internal fun buildRadarMapHtml(campaigns: List<ScamCampaign>): String {
    val payload = JSONArray()
    for (campaign in campaigns) {
        val lat = campaign.lat
        val lon = campaign.lon
        if (lat == null || lon == null) continue

        val item = JSONObject()
        item.put("id", campaign.id)
        item.put("title", campaign.title)
        item.put("brand", campaign.brand)
        item.put("risk", campaign.risk)
        item.put("lat", lat)
        item.put("lon", lon)
        item.put("scanCount", campaign.count)
        item.put("safeActionText", campaign.safeActionText)
        item.put("lastSeenText", campaign.lastSeenText)
        payload.put(item)
    }

    return """
	        <!doctype html>
	        <html>
	            <head>
	                <meta name="viewport" content="width=device-width, initial-scale=1.0">
	                <style>
	                    html, body, .radar {
	                        margin: 0;
	                        width: 100%;
	                        height: 100%;
	                        background:
	                            radial-gradient(circle at 48% 48%, rgba(6, 182, 212, 0.24), transparent 28%),
	                            linear-gradient(145deg, #07111f 0%, #111827 58%, #172554 100%);
	                    }
	                    body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; overflow: hidden; }
	                    .radar {
	                        position: relative;
	                        border-radius: 0;
	                    }
	                    .grid {
	                        position: absolute;
	                        inset: 0;
	                        opacity: 0.28;
	                        background-image:
	                            linear-gradient(rgba(148, 163, 184, 0.18) 1px, transparent 1px),
	                            linear-gradient(90deg, rgba(148, 163, 184, 0.18) 1px, transparent 1px);
	                        background-size: 32px 32px;
	                    }
	                    .label {
	                        position: absolute;
	                        left: 14px;
	                        top: 12px;
	                        color: #e2e8f0;
	                        font-size: 12px;
	                        letter-spacing: 0.06em;
	                        text-transform: uppercase;
	                    }
	                    .hint {
	                        position: absolute;
	                        left: 14px;
	                        right: 14px;
	                        bottom: 12px;
	                        color: #94a3b8;
	                        font-size: 11px;
	                    }
	                    .marker {
	                        position: absolute;
	                        width: 18px;
	                        height: 18px;
	                        margin: -9px 0 0 -9px;
	                        border: 2px solid #ffffff;
	                        border-radius: 999px;
	                        box-shadow: 0 0 0 8px rgba(255, 255, 255, 0.08), 0 10px 24px rgba(0, 0, 0, 0.35);
	                        text-decoration: none;
	                    }
	                    .marker.dangerous, .marker.high { background: #ef4444; }
	                    .marker.medium { background: #f59e0b; }
	                    .marker.low { background: #22c55e; }
	                    .marker span {
	                        position: absolute;
	                        left: 22px;
	                        top: -5px;
	                        min-width: 110px;
	                        color: #f8fafc;
	                        background: rgba(15, 23, 42, 0.86);
	                        border: 1px solid rgba(148, 163, 184, 0.28);
	                        border-radius: 8px;
	                        padding: 4px 6px;
	                        font-size: 10px;
	                        pointer-events: none;
	                    }
	                </style>
	            </head>
	            <body>
	                <div class="radar">
	                    <div class="grid"></div>
	                    <div class="label">Radar Romania</div>
	                    ${buildStaticRadarMarkers(payload)}
	                    <div class="hint">Punctele sunt aproximative si nu incarca resurse externe.</div>
	                </div>
	            </body>
	        </html>
	    """.trimIndent()
}

internal fun buildStaticRadarMarkers(payload: JSONArray): String {
    if (payload.length() == 0) {
        return """<div class="hint">Nu exista campanii valide pe harta.</div>"""
    }
    return (0 until payload.length()).joinToString("\n") { index ->
        val item = payload.getJSONObject(index)
        val id = item.optString("id")
        val title = item.optString("title", "Campanie")
        val risk = item.optString("risk", "medium").lowercase(Locale.US)
        val lat = item.optDouble("lat")
        val lon = item.optDouble("lon")
        val left = romanianMapX(lon)
        val top = romanianMapY(lat)
        val safeTitle = title.htmlEscape()
        """<a class="marker $risk" href="sigurscan-radar://campaign/${Uri.encode(id)}" style="left:${left}%;top:${top}%"><span>$safeTitle</span></a>"""
    }
}

internal fun romanianMapX(lon: Double): Int {
    val minLon = 20.2
    val maxLon = 29.8
    return (((lon - minLon) / (maxLon - minLon)) * 78.0 + 11.0).toInt().coerceIn(8, 92)
}

internal fun romanianMapY(lat: Double): Int {
    val minLat = 43.6
    val maxLat = 48.3
    return ((1.0 - ((lat - minLat) / (maxLat - minLat))) * 72.0 + 14.0).toInt().coerceIn(8, 92)
}

internal fun String.htmlEscape(): String {
    return replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\"", "&quot;")
        .replace("'", "&#39;")
}
