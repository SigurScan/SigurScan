package ro.sigurscan.app.ui.theme

import androidx.compose.ui.graphics.Color

/**
 * v2 design system values, ported into the original token names so every
 * existing screen re-themes automatically without per-file changes. Source
 * of truth: `SigurScan Design System.html` §07 (CSS custom properties) —
 * see `ui/v2/theme/SigurTokensV2.kt` for the same values as the new
 * component library's canonical source.
 */
object SigurColors {
    val Background = Color(0xFFEAF1EE)
    val Canvas = Color(0xFFEAF1EE)
    val BackgroundElevated = Color(0xFFFFFFFF)
    val BackgroundCard = Color(0xFFFFFFFF)
    val BackgroundSurface = Color(0xFFF5F7FA)

    val GlassBorder = Color(0xFFE4E8EE)
    val GlassHairline = Color(0x0D000000)

    val Brand = Color(0xFF0AA06C)
    val BrandDeep = Color(0xFF06875A)
    val BrandLight = Color(0xFF1FD89A)
    val BrandTint = Color(0x140AA06C)

    val TextPrimary = Color(0xFF131722)
    val TextSecondary = Color(0xFF3A4252)
    val TextMuted = Color(0xFF7B8698)
    val TextSubtle = Color(0xFFACB1C3)
    val TextInverse = Color(0xFFFFFFFF)

    val BorderSubtle = Color(0x0D000000)
    val BorderDefault = Color(0x17000000)
    val BorderStrong = Color(0x2E000000)

    val Safe = Color(0xFF0AA06C)
    val SafeLight = Color(0x290AA06C)
    val SafeBorder = Color(0x480AA06C)
    val Suspect = Color(0xFFF2900B)
    val SuspectLight = Color(0x29F2900B)
    val SuspectBorder = Color(0x48F2900B)
    val Dangerous = Color(0xFFE5392B)
    val DangerousLight = Color(0x1FE5392B)
    val DangerousBorder = Color(0x48E5392B)
    val Pending = Color(0xFF64748B)
    val PendingLight = Color(0x2964748B)
    val Unknown = Color(0xFF7C3AED)
    val UnknownLight = Color(0x1A7C3AED)
    val UnknownBorder = Color(0x407C3AED)

    // Radii (DS: --ss-r-*)
    val RadiusXs = 4
    val RadiusSm = 8
    val RadiusMd = 12
    val RadiusCard = 18
    val RadiusXl = 22
    val RadiusInput = 16
    val RadiusPill = 100

    // Sizing (DS: --ss-*)
    val TouchTarget = 48
    val AppBarHeight = 64
    val NavBarHeight = 80
    val ListItem2Line = 72
    val TextFieldHeight = 56
    val ButtonHeight = 48
    val FabSize = 56
    val IconSize = 24
    val AvatarSize = 40

    // Spacing
    val SpaceScreen = 16
    val SpaceCard = 16
    val SpaceStack = 16
}
