package ro.sigurscan.app.ui.v2.screens

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.AccountBalance
import androidx.compose.material.icons.rounded.GppMaybe
import androidx.compose.material.icons.rounded.Help
import androidx.compose.material.icons.rounded.ReportProblem
import androidx.compose.material.icons.rounded.Verified
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import ro.sigurscan.app.ui.v2.components.ActionPlanCardV2
import ro.sigurscan.app.ui.v2.components.AppHeaderV2
import ro.sigurscan.app.ui.v2.components.BottomNavBarV2
import ro.sigurscan.app.ui.v2.components.BottomNavTabV2
import ro.sigurscan.app.ui.v2.components.FeedbackRowV2
import ro.sigurscan.app.ui.v2.components.InvoiceSupplierCardV2
import ro.sigurscan.app.ui.v2.components.VerdictCardV2
import ro.sigurscan.app.ui.v2.components.VerdictReason
import ro.sigurscan.app.ui.v2.theme.SigurTokensV2
import ro.sigurscan.app.ui.v2.theme.TypeV2
import ro.sigurscan.app.ui.v2.theme.VerdictTone

data class InvoiceVerdictScreenDataV2(
    val tone: VerdictTone,
    val badgeLabel: String,
    val title: String,
    val subtitle: String,
    val headerIcon: ImageVector,
    val reasons: List<VerdictReason>,
    val supplierName: String,
    val iban: String,
    val sourceBadge: String,
    val sourceLine: String,
    val nextStep: String,
    val techDetails: List<Pair<String, String>>,
)

/** Screens 6-9 · Factură (Sigur/Neverificat/Suspect/Periculos) — invoice-specific verdict card. */
@Composable
fun InvoiceVerdictScreenV2(
    data: InvoiceVerdictScreenDataV2,
    onFeedbackYes: () -> Unit,
    onFeedbackNo: () -> Unit,
    modifier: Modifier = Modifier,
    selectedNavTab: BottomNavTabV2 = BottomNavTabV2.SCANEAZA,
    onNavSelect: (BottomNavTabV2) -> Unit = {},
) {
    val accent = SigurTokensV2.palette(data.tone).accent

    Scaffold(
        modifier = modifier,
        containerColor = SigurTokensV2.Canvas,
        bottomBar = { BottomNavBarV2(selected = selectedNavTab, onSelect = onNavSelect) },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 16.dp)
                .verticalScroll(rememberScrollState()),
        ) {
            AppHeaderV2()

            VerdictCardV2(
                tone = data.tone,
                badgeLabel = data.badgeLabel,
                title = data.title,
                subtitle = data.subtitle,
                headerIcon = data.headerIcon,
                reasons = data.reasons,
            )

            InvoiceSupplierCardV2(
                accent = accent,
                supplierName = data.supplierName,
                iban = data.iban,
                sourceBadge = data.sourceBadge,
                sourceLine = data.sourceLine,
                modifier = Modifier.padding(top = 12.dp),
            )

            ActionPlanCardV2(
                accent = accent,
                icon = Icons.Rounded.AccountBalance,
                title = "Următorul pas",
                actions = listOf(data.nextStep),
                techDetails = data.techDetails,
                modifier = Modifier.padding(top = 12.dp),
            )

            Text(
                "A fost util acest verdict?",
                style = TypeV2.CardTitle.copy(fontSize = 13.sp, letterSpacing = 0.2.sp),
                color = SigurTokensV2.Ink,
                modifier = Modifier.padding(top = 18.dp, bottom = 10.dp),
            )
            FeedbackRowV2(onYes = onFeedbackYes, onNo = onFeedbackNo, modifier = Modifier.padding(bottom = 24.dp))
        }
    }
}

object InvoiceVerdictSampleDataV2 {
    val sigur = InvoiceVerdictScreenDataV2(
        tone = VerdictTone.SIGUR,
        badgeLabel = "SIGUR",
        title = "Poți plăti",
        subtitle = "Poți plăti. Pentru siguranță, confirmă și în SANB.",
        headerIcon = Icons.Rounded.Verified,
        reasons = listOf(
            VerdictReason("Firma e reală și activă la ANAF.", ro.sigurscan.app.ui.v2.components.ReasonSeverity.GOOD),
            VerdictReason("Contul beneficiarului se potrivește cu furnizorul.", ro.sigurscan.app.ui.v2.components.ReasonSeverity.GOOD),
            VerdictReason("Sumele și TVA-ul sunt coerente.", ro.sigurscan.app.ui.v2.components.ReasonSeverity.GOOD),
        ),
        supplierName = "eMAG IT DISTRIBUTION SRL",
        iban = "RO49 RNCB 0082 0044 1766 0001",
        sourceBadge = "XML verificat",
        sourceLine = "Sursă: document scanat + XML oficial verificat",
        nextStep = "Poți plăti. Pentru siguranță, confirmă numele beneficiarului în aplicația băncii (SANB).",
        techDetails = listOf(
            "CUI" to "RO 12345678",
            "IBAN" to "RO49 RNCB 0082 0044 1766 0001",
            "Subtotal" to "—",
            "TVA (19%)" to "—",
            "Total" to "—",
            "Scor de risc" to "8 / 100",
        ),
    )

    val neverificat = InvoiceVerdictScreenDataV2(
        tone = VerdictTone.NEVERIFICAT,
        badgeLabel = "NEVERIFICAT",
        title = "Verifică contul întâi",
        subtitle = "Nu am putut confirma automat proprietarul IBAN-ului.",
        headerIcon = Icons.Rounded.Help,
        reasons = listOf(
            VerdictReason("Nu am putut confirma automat proprietarul IBAN-ului.", ro.sigurscan.app.ui.v2.components.ReasonSeverity.NEUTRAL),
            VerdictReason("Firma e reală și activă la ANAF.", ro.sigurscan.app.ui.v2.components.ReasonSeverity.GOOD),
            VerdictReason("Sumele și TVA-ul sunt coerente.", ro.sigurscan.app.ui.v2.components.ReasonSeverity.GOOD),
        ),
        supplierName = "GRĂDINA VERDE SRL",
        iban = "RO12 BTRL 0099 1234 5678 9000",
        sourceBadge = "doc scanat",
        sourceLine = "Sursă: document scanat",
        nextStep = "Verifică numele beneficiarului în aplicația băncii (SANB) înainte să plătești.",
        techDetails = listOf(
            "CUI" to "RO 30441002",
            "IBAN" to "RO12 BTRL 0099 1234 5678 9000",
            "Subtotal" to "—",
            "TVA (19%)" to "—",
            "Total" to "—",
            "Scor de risc" to "25 / 100",
        ),
    )

    val suspect = InvoiceVerdictScreenDataV2(
        tone = VerdictTone.SUSPECT,
        badgeLabel = "SUSPECT",
        title = "Nu plăti încă",
        subtitle = "Nu plăti încă — verifică în SANB înainte să plătești.",
        headerIcon = Icons.Rounded.ReportProblem,
        reasons = listOf(
            VerdictReason("Sumele nu se potrivesc: total 9.990 lei ≠ 1.000 + 190 TVA.", ro.sigurscan.app.ui.v2.components.ReasonSeverity.ALERT),
            VerdictReason("Nu putem confirma automat proprietarul contului.", ro.sigurscan.app.ui.v2.components.ReasonSeverity.ALERT),
            VerdictReason("Firma e reală și activă la ANAF.", ro.sigurscan.app.ui.v2.components.ReasonSeverity.GOOD),
            VerdictReason("IBAN-ul are format valid.", ro.sigurscan.app.ui.v2.components.ReasonSeverity.GOOD),
        ),
        supplierName = "ALFA DISTRIB SRL",
        iban = "RO17 BTRL 0001 2233 4455 6677",
        sourceBadge = "doc scanat",
        sourceLine = "Sursă: document scanat",
        nextStep = "Verifică în SANB și recalculează totalul înainte să plătești.",
        techDetails = listOf(
            "CUI" to "RO 12345678",
            "IBAN" to "RO17 BTRL 0001 2233 4455 6677",
            "Subtotal" to "1.000 lei",
            "TVA (19%)" to "190 lei",
            "Total facturat" to "9.990 lei",
            "Scor de risc" to "55 / 100",
        ),
    )

    val periculos = InvoiceVerdictScreenDataV2(
        tone = VerdictTone.PERICULOS,
        badgeLabel = "PERICULOS",
        title = "Nu plăti",
        subtitle = "Nu plăti — sună furnizorul pe un număr cunoscut.",
        headerIcon = Icons.Rounded.GppMaybe,
        reasons = listOf(
            VerdictReason("Beneficiarul plății diferă de furnizor: TECH SOLUTIONS PRO ≠ MGH.", ro.sigurscan.app.ui.v2.components.ReasonSeverity.ALERT),
            VerdictReason("Contul (IBAN) pare schimbat față de cel obișnuit.", ro.sigurscan.app.ui.v2.components.ReasonSeverity.ALERT),
            VerdictReason("Documentul a fost citit complet.", ro.sigurscan.app.ui.v2.components.ReasonSeverity.NEUTRAL),
        ),
        supplierName = "MGH SRL",
        iban = "RO39 RNCB 0000 1111 2222 3333",
        sourceBadge = "XML ≠",
        sourceLine = "Sursă: document scanat + XML oficial nu se potrivește",
        nextStep = "Sună furnizorul pe un număr cunoscut înainte să plătești.",
        techDetails = listOf(
            "Furnizor (factură)" to "MGH SRL",
            "Beneficiar plată" to "TECH SOLUTIONS PRO",
            "IBAN" to "RO39 RNCB (BCR)",
            "Familie" to "schimbare_iban_bec",
            "Scor de risc" to "90 / 100",
        ),
    )

    val all = listOf(sigur, neverificat, suspect, periculos)
}
