package ro.sigurscan.app.ui.v2.components

import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.unit.Dp
import ro.sigurscan.app.ui.v2.theme.SigurTokensV2

/** Elevated card shadow — 0 6px 20px rgba(16,24,40,.09), matches DS §04. */
fun Modifier.elevatedCardV2(radius: Dp = SigurTokensV2.RadiusVerdict): Modifier = shadow(
    elevation = SigurTokensV2.ElevatedShadowRadius,
    shape = RoundedCornerShape(radius),
    ambientColor = SigurTokensV2.ElevatedShadowColor,
    spotColor = SigurTokensV2.ElevatedShadowColor,
)

/** FAB shadow — 0 4px 12px rgba(6,135,90,.30). */
fun Modifier.fabShadowV2(radius: Dp): Modifier = shadow(
    elevation = SigurTokensV2.FabShadowRadius,
    shape = RoundedCornerShape(radius),
    ambientColor = SigurTokensV2.FabShadowColor,
    spotColor = SigurTokensV2.FabShadowColor,
)

/** Nav bar / colored verdict shadow — 0 2px 6px rgba(accent,.16). */
fun Modifier.navBarShadowV2(radius: Dp): Modifier = shadow(
    elevation = SigurTokensV2.NavBarShadowRadius,
    shape = RoundedCornerShape(radius),
    ambientColor = SigurTokensV2.NavBarShadowColor,
    spotColor = SigurTokensV2.NavBarShadowColor,
)
