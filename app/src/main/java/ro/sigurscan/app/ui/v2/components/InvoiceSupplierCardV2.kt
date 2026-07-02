package ro.sigurscan.app.ui.v2.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.ReceiptLong
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import ro.sigurscan.app.ui.v2.theme.SigurTokensV2
import ro.sigurscan.app.ui.v2.theme.TypeV2

/** "Factură de la <furnizor>" card — invoice-specific variant of DestinationRowV2. */
@Composable
fun InvoiceSupplierCardV2(
    accent: Color,
    supplierName: String,
    iban: String,
    sourceBadge: String,
    sourceLine: String,
    modifier: Modifier = Modifier,
) {
    CardOutlinedV2(modifier = modifier.fillMaxWidth(), radius = SigurTokensV2.RadiusCardAlt, padding = 14.dp) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            IconChipV2(icon = Icons.Rounded.ReceiptLong, tint = accent, size = 40.dp, radius = 11.dp)
            Column(modifier = Modifier.padding(start = 12.dp).weight(1f)) {
                Text("Factură de la", style = TypeV2.Eyebrow, color = SigurTokensV2.Muted)
                Text(
                    supplierName,
                    style = TypeV2.CardTitle.copy(fontSize = 14.sp),
                    color = SigurTokensV2.Ink,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.padding(top = 3.dp),
                )
                Text(
                    iban,
                    style = TypeV2.Mono,
                    color = SigurTokensV2.Muted,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.padding(top = 2.dp),
                )
            }
            StatusPillV2(sourceBadge, color = accent)
        }
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 10.dp)
                .background(SigurTokensV2.Fill, RoundedCornerShape(10.dp))
                .padding(horizontal = 10.dp, vertical = 8.dp),
        ) {
            Icon(Icons.Rounded.ReceiptLong, contentDescription = null, tint = SigurTokensV2.Muted, modifier = Modifier.padding(end = 8.dp))
            Text(sourceLine, style = TypeV2.Caption)
        }
    }
}
