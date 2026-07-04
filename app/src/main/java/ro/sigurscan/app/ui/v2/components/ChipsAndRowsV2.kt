package ro.sigurscan.app.ui.v2.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import ro.sigurscan.app.ui.v2.theme.SigurTokensV2
import ro.sigurscan.app.ui.v2.theme.TypeV2

/** Small colored status pill — "Domeniu oficial", "Imită eMAG", "Cere plată", etc. */
@Composable
fun StatusPillV2(label: String, color: Color, modifier: Modifier = Modifier) {
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(SigurTokensV2.RadiusPill))
            .background(color.copy(alpha = 0.15f))
            .padding(horizontal = 10.dp, vertical = 5.dp),
    ) {
        Text(
            label,
            style = TypeV2.Caption.copy(fontWeight = FontWeight.Bold, fontSize = 11.5.sp, color = color),
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
        )
    }
}

/** Square-ish tinted icon chip, radius 11-13. */
@Composable
fun IconChipV2(
    icon: ImageVector,
    tint: Color,
    modifier: Modifier = Modifier,
    size: Dp = 40.dp,
    radius: Dp = SigurTokensV2.RadiusIconChip,
) {
    Box(
        modifier = modifier
            .size(size)
            .clip(RoundedCornerShape(radius))
            .background(tint.copy(alpha = 0.14f)),
        contentAlignment = Alignment.Center,
    ) {
        Icon(icon, contentDescription = null, tint = tint, modifier = Modifier.size(size * 0.5f))
    }
}

/** "Te duce către <domain>" row with an icon chip and an optional trailing status pill. */
@Composable
fun DestinationRowV2(
    icon: ImageVector,
    accent: Color,
    label: String,
    value: String,
    pillLabel: String? = null,
    modifier: Modifier = Modifier,
) {
    CardOutlinedV2(modifier = modifier.fillMaxWidth(), radius = SigurTokensV2.RadiusCardAlt, padding = 13.dp) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            IconChipV2(icon = icon, tint = accent)
            Column(modifier = Modifier.padding(start = 12.dp).weight(1f)) {
                Text(label, style = TypeV2.Eyebrow, color = SigurTokensV2.Muted)
                Text(
                    value,
                    style = TypeV2.MonoLarge,
                    color = SigurTokensV2.Ink,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.padding(top = 3.dp),
                )
            }
            if (pillLabel != null) {
                StatusPillV2(pillLabel, color = accent, modifier = Modifier.padding(start = 8.dp))
            }
        }
    }
}

/** Muted key/value technical row used inside "Detalii tehnice" and invoice cards. */
@Composable
fun DetailRowV2(key: String, value: String, showTopDivider: Boolean = true, modifier: Modifier = Modifier) {
    Column(modifier = modifier.fillMaxWidth()) {
        if (showTopDivider) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(1.dp)
                    .background(SigurTokensV2.Hairline),
            )
        }
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 9.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.Top,
        ) {
            Text(
                key,
                style = TypeV2.Body.copy(color = SigurTokensV2.Muted, fontSize = 13.sp),
                modifier = Modifier.weight(1f),
            )
            Text(
                value,
                style = TypeV2.Mono,
                color = SigurTokensV2.Ink,
                textAlign = androidx.compose.ui.text.style.TextAlign.End,
                modifier = Modifier.weight(1.35f),
            )
        }
    }
}

/** Outlined support card — white surface, hairline border, no shadow. */
@Composable
fun CardOutlinedV2(
    modifier: Modifier = Modifier,
    radius: Dp = SigurTokensV2.RadiusCard,
    padding: Dp = 16.dp,
    content: @Composable ColumnScope.() -> Unit,
) {
    Column(
        modifier = modifier
            .clip(RoundedCornerShape(radius))
            .background(SigurTokensV2.Surface)
            .border(1.dp, SigurTokensV2.Hairline, RoundedCornerShape(radius))
            .padding(padding),
        content = content,
    )
}
