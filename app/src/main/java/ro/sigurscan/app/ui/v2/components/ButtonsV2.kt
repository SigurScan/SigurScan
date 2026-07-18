package ro.sigurscan.app.ui.v2.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import ro.sigurscan.app.ui.v2.theme.SigurTokensV2
import ro.sigurscan.app.ui.v2.theme.TypeV2

/** Primary — brand gradient fill, white text/icon. */
@Composable
fun PrimaryButtonV2(
    label: String,
    modifier: Modifier = Modifier,
    icon: ImageVector? = null,
    onClick: () -> Unit,
) {
    GradientButtonRow(
        label = label,
        icon = icon,
        gradient = SigurTokensV2.BrandGradient,
        contentColor = Color.White,
        modifier = modifier,
        onClick = onClick,
    )
}

/** Destructive — red gradient fill, white text/icon (e.g. hang up / delete). */
@Composable
fun DestructiveButtonV2(
    label: String,
    modifier: Modifier = Modifier,
    icon: ImageVector? = null,
    onClick: () -> Unit,
) {
    GradientButtonRow(
        label = label,
        icon = icon,
        gradient = Brush.linearGradient(colors = listOf(Color(0xFFFB6F5F), Color(0xFFD32C1F))),
        contentColor = Color.White,
        modifier = modifier,
        onClick = onClick,
    )
}

/** Secondary — white surface, hairline border, accent text/icon. */
@Composable
fun SecondaryButtonV2(
    label: String,
    modifier: Modifier = Modifier,
    icon: ImageVector? = null,
    accent: Color = SigurTokensV2.Sigur.accent,
    onClick: () -> Unit,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(SigurTokensV2.RadiusButton))
            .background(SigurTokensV2.Surface)
            .border(1.dp, SigurTokensV2.Hairline, RoundedCornerShape(SigurTokensV2.RadiusButton))
            .clickable(onClick = onClick)
            .padding(vertical = 13.dp),
        horizontalArrangement = Arrangement.Center,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        if (icon != null) {
            Icon(icon, contentDescription = null, tint = accent, modifier = Modifier.padding(end = 8.dp))
        }
        Text(label, style = TypeV2.CardTitle, color = accent)
    }
}

/** Subtle / tertiary — muted fill, muted text, no border. */
@Composable
fun SubtleButtonV2(
    label: String,
    modifier: Modifier = Modifier,
    onClick: () -> Unit,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(SigurTokensV2.RadiusButton))
            .background(SigurTokensV2.Fill)
            .clickable(onClick = onClick)
            .padding(vertical = 13.dp),
        horizontalArrangement = Arrangement.Center,
    ) {
        Text(label, style = TypeV2.CardTitle, color = SigurTokensV2.Muted)
    }
}

@Composable
private fun GradientButtonRow(
    label: String,
    icon: ImageVector?,
    gradient: Brush,
    contentColor: Color,
    modifier: Modifier = Modifier,
    onClick: () -> Unit,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(SigurTokensV2.RadiusButton))
            .background(gradient)
            .clickable(onClick = onClick)
            .padding(vertical = 14.dp),
        horizontalArrangement = Arrangement.Center,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        if (icon != null) {
            Icon(icon, contentDescription = null, tint = contentColor, modifier = Modifier.padding(end = 8.dp))
        }
        Text(label, style = TypeV2.CardTitle, color = contentColor)
    }
}
