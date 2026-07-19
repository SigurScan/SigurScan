package ro.sigurscan.app.ui.v2.theme

import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

/**
 * SigurScan v2 design tokens — ported 1:1 from `SigurScan Design System.html`
 * (section 07 · CSS custom properties). Values are copied verbatim, not
 * reinterpreted, so this file is the single source of truth for the v2 UI.
 */
enum class VerdictTone { SIGUR, NEVERIFICAT, SUSPECT, PERICULOS }

data class VerdictPalette(
    val gradient: Brush,
    val accent: Color,
    val dark: Color,
    val tint: Color,
    val fill: Color,
)

object SigurTokensV2 {
    // ---- neutrals ----
    val Ink = Color(0xFF131722)
    val Body = Color(0xFF3A4252)
    val Muted = Color(0xFF7B8698)
    val Canvas = Color(0xFFEAF1EE)
    val Surface = Color(0xFFFFFFFF)
    val Fill = Color(0xFFF5F7FA)
    val Hairline = Color(0xFFE4E8EE)
    val ToggleOff = Color(0xFFCBD2DD)

    // ---- brand ----
    val BrandGradient = Brush.linearGradient(
        colors = listOf(Color(0xFF14BE86), Color(0xFF0AA06C), Color(0xFF06875A)),
    )
    val NavGradient = Brush.linearGradient(
        colors = listOf(Color(0xFF0FA877), Color(0xFF067A50)),
    )

    // ---- function colors (≠ verdict) ----
    val FunctionCall = Color(0xFF2563EB)
    val FunctionEar = Color(0xFF7C3AED)
    val FunctionSecondOpinion = Color(0xFF0891B2)

    // ---- verdict palettes ----
    val Sigur = VerdictPalette(
        gradient = Brush.radialGradient(
            colors = listOf(Color(0xFF1FD89A), Color(0xFF0AA06C), Color(0xFF05663E)),
        ),
        accent = Color(0xFF0AA06C),
        dark = Color(0xFF067A50),
        tint = Color(0x290AA06C),
        fill = Color(0x140AA06C),
    )
    val Neverificat = VerdictPalette(
        gradient = Brush.radialGradient(
            colors = listOf(Color(0xFFA2AFBF), Color(0xFF64748B), Color(0xFF3C4655)),
        ),
        accent = Color(0xFF64748B),
        dark = Color(0xFF475569),
        tint = Color(0x2964748B),
        fill = Color(0x1464748B),
    )
    val Suspect = VerdictPalette(
        gradient = Brush.radialGradient(
            colors = listOf(Color(0xFFFBB63A), Color(0xFFF2900B), Color(0xFFB36309)),
        ),
        accent = Color(0xFFF2900B),
        dark = Color(0xFFB36309),
        tint = Color(0x29F2900B),
        fill = Color(0x14F2900B),
    )
    val Periculos = VerdictPalette(
        gradient = Brush.radialGradient(
            colors = listOf(Color(0xFFFB6F5F), Color(0xFFE5392B), Color(0xFFB11D12)),
        ),
        accent = Color(0xFFE5392B),
        dark = Color(0xFFC32A1E),
        tint = Color(0x29E5392B),
        fill = Color(0x14E5392B),
    )

    fun palette(tone: VerdictTone): VerdictPalette = when (tone) {
        VerdictTone.SIGUR -> Sigur
        VerdictTone.NEVERIFICAT -> Neverificat
        VerdictTone.SUSPECT -> Suspect
        VerdictTone.PERICULOS -> Periculos
    }

    // ---- radius ----
    val RadiusVerdict = 22.dp
    val RadiusCard = 18.dp
    val RadiusCardAlt = 16.dp
    val RadiusButton = 14.dp
    val RadiusIconChip = 11.dp
    val RadiusPill = 999.dp

    // ---- spacing ----
    val GapCard = 12.dp
    val GapBeforeSectionLabel = 18.dp
    val PaddingCardMin = 14.dp
    val PaddingCardMax = 18.dp

    // ---- elevation (shadow color + radius/offset approximations of the CSS box-shadows) ----
    val ElevatedShadowColor = Color(0x17101828) // rgba(16,24,40,.09)
    val ElevatedShadowRadius = 20.dp
    val ElevatedShadowOffsetY = 6.dp

    val FabShadowColor = Color(0x4D06875A) // rgba(6,135,90,.30)
    val FabShadowRadius = 12.dp
    val FabShadowOffsetY = 4.dp

    val NavBarShadowColor = Color(0x29067A50) // rgba(6,135,90,.16)
    val NavBarShadowRadius = 6.dp
    val NavBarShadowOffsetY = 2.dp
}
