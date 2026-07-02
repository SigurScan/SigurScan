package ro.sigurscan.app.ui.v2.screens

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.GppMaybe
import androidx.compose.material.icons.rounded.Help
import androidx.compose.material.icons.rounded.ReportProblem
import androidx.compose.material.icons.rounded.Verified
import ro.sigurscan.app.ui.v2.components.ReasonSeverity
import ro.sigurscan.app.ui.v2.components.VerdictReason
import ro.sigurscan.app.ui.v2.theme.VerdictTone

/**
 * Sample data mirroring the exact copy from `SigurScan v2.html` screens 02-05,
 * used by the gallery preview and as a reference shape for real wiring later.
 */
object VerdictSampleDataV2 {
    val sigur = VerdictScreenDataV2(
        tone = VerdictTone.SIGUR,
        badgeLabel = "SIGUR",
        title = "Poți continua",
        subtitle = "Am verificat destinația și nu am găsit semnale de risc.",
        headerIcon = Icons.Rounded.Verified,
        reasons = listOf(
            VerdictReason("Destinație verificată — domeniu oficial, cu reputație bună.", ReasonSeverity.GOOD),
            VerdictReason("Fără redirectări ascunse sau cereri de date sensibile.", ReasonSeverity.GOOD),
        ),
        destinationValue = "emag.ro",
        destinationPill = "Domeniu oficial",
        actions = listOf("Poți continua liniștit."),
        techDetails = listOf(
            "Reputație domeniu" to "Bună",
            "Vârstă domeniu" to "peste 5 ani",
            "Certificat SSL" to "Valid",
            "Încredere AI" to "Ridicată",
            "Scor de risc" to "8 / 100",
        ),
    )

    val neverificat = VerdictScreenDataV2(
        tone = VerdictTone.NEVERIFICAT,
        badgeLabel = "NEVERIFICAT",
        title = "Verifică înainte să continui",
        subtitle = "Nu am putut confirma sursa acestui link.",
        headerIcon = Icons.Rounded.Help,
        reasons = listOf(
            VerdictReason("Domeniu înregistrat recent, fără istoric.", ReasonSeverity.NEUTRAL),
            VerdictReason("Nu am găsit semnale clare bune sau rele.", ReasonSeverity.NEUTRAL),
        ),
        destinationValue = "magazin-flori-online.ro",
        destinationPill = "Domeniu nou",
        actions = listOf(
            "Caută numele firmei separat, în Google.",
            "Nu introduce date personale până nu confirmi.",
        ),
        techDetails = listOf(
            "Reputație domeniu" to "Neverificată",
            "Vârstă domeniu" to "Necunoscută",
            "Certificat SSL" to "Valid",
            "Încredere AI" to "Scăzută",
            "Scor de risc" to "25 / 100",
        ),
    )

    val suspect = VerdictScreenDataV2(
        tone = VerdictTone.SUSPECT,
        badgeLabel = "SUSPECT",
        title = "Nu continua încă",
        subtitle = "Sunt semnale care nu se potrivesc.",
        headerIcon = Icons.Rounded.ReportProblem,
        reasons = listOf(
            VerdictReason("Numele imită un magazin cunoscut, dar domeniul e diferit.", ReasonSeverity.ALERT),
            VerdictReason("Domeniu de tip „.shop” folosit pentru o ofertă urgentă.", ReasonSeverity.ALERT),
        ),
        destinationValue = "promo-emag.shop",
        destinationPill = "Imită eMAG",
        actions = listOf(
            "Nu apăsa pe link.",
            "Intră direct pe emag.ro, din aplicația oficială.",
        ),
        techDetails = listOf(
            "Reputație domeniu" to "Slabă",
            "Vârstă domeniu" to "—",
            "Certificat SSL" to "Valid (gratuit)",
            "Încredere AI" to "Ridicată",
            "Familie" to "tiposquatting_brand",
            "Scor de risc" to "55 / 100",
        ),
    )

    val periculos = VerdictScreenDataV2(
        tone = VerdictTone.PERICULOS,
        badgeLabel = "PERICULOS",
        title = "Nu continua",
        subtitle = "Am găsit semnale clare de risc.",
        headerIcon = Icons.Rounded.GppMaybe,
        reasons = listOf(
            VerdictReason("Pagină de plată falsă pentru un „colet reținut”.", ReasonSeverity.ALERT),
            VerdictReason("Domeniu .top fără legătură cu firma de curierat reală.", ReasonSeverity.ALERT),
        ),
        destinationValue = "ng-colet-ro.top/plata",
        destinationPill = "Cere plată",
        actions = listOf(
            "Nu plăti și nu introduce datele cardului.",
            "Șterge mesajul.",
        ),
        techDetails = listOf(
            "Reputație domeniu" to "Periculoasă",
            "Vârstă domeniu" to "—",
            "Certificat SSL" to "Absent",
            "Încredere AI" to "Ridicată",
            "Familie" to "plata_falsa_colet",
            "Scor de risc" to "90 / 100",
        ),
    )

    val all = listOf(sigur, neverificat, suspect, periculos)
}
