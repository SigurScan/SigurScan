package ro.sigurscan.app.ui.v2.screens

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Link
import androidx.compose.material.icons.rounded.TaskAlt
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import ro.sigurscan.app.ui.v2.components.AppHeaderV2
import ro.sigurscan.app.ui.v2.components.BottomNavBarV2
import ro.sigurscan.app.ui.v2.components.BottomNavTabV2
import ro.sigurscan.app.ui.v2.components.ActionPlanCardV2
import ro.sigurscan.app.ui.v2.components.DestinationRowV2
import ro.sigurscan.app.ui.v2.components.FeedbackRowV2
import ro.sigurscan.app.ui.v2.components.VerdictCardV2
import ro.sigurscan.app.ui.v2.components.VerdictReason
import ro.sigurscan.app.ui.v2.theme.SigurTokensV2
import ro.sigurscan.app.ui.v2.theme.TypeV2
import ro.sigurscan.app.ui.v2.theme.VerdictTone

/** Everything one of screens 2-5 needs — the verdict card themes the whole screen (DS §06). */
data class VerdictScreenDataV2(
    val tone: VerdictTone,
    val badgeLabel: String,
    val title: String,
    val subtitle: String,
    val headerIcon: ImageVector,
    val reasons: List<VerdictReason>,
    val destinationValue: String,
    val destinationPill: String,
    val destinationIcon: ImageVector = Icons.Rounded.Link,
    val actions: List<String>,
    val techDetails: List<Pair<String, String>>,
)

/** Screens 2-5 · Sigur / Neverificat / Suspect / Periculos — one composable, themed by tone. */
@Composable
fun VerdictScreenV2(
    data: VerdictScreenDataV2,
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

            DestinationRowV2(
                icon = data.destinationIcon,
                accent = accent,
                label = "Te duce către",
                value = data.destinationValue,
                pillLabel = data.destinationPill,
                modifier = Modifier.padding(top = 12.dp),
            )

            ActionPlanCardV2(
                accent = accent,
                icon = Icons.Rounded.TaskAlt,
                actions = data.actions,
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
