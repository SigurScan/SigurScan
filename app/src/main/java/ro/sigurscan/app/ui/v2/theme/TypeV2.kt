package ro.sigurscan.app.ui.v2.theme

import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import ro.sigurscan.app.R
import ro.sigurscan.app.ui.theme.SpaceGrotesk

/**
 * SigurScan v2 typography — Manrope for all UI copy (500-800), JetBrains Mono
 * for technical/mono values (IBAN, scores, domains), Space Grotesk reserved
 * for large numerals on the call screen only (see design system §02).
 */
val ManropeV2 = FontFamily(
    Font(R.font.manrope_medium, FontWeight.Medium),
    Font(R.font.manrope_semibold, FontWeight.SemiBold),
    Font(R.font.manrope_bold, FontWeight.Bold),
    Font(R.font.manrope_extrabold, FontWeight.ExtraBold),
)

val JetBrainsMonoV2 = FontFamily(
    Font(R.font.jetbrains_mono_regular, FontWeight.Normal),
    Font(R.font.jetbrains_mono_medium, FontWeight.Medium),
    Font(R.font.jetbrains_mono_semibold, FontWeight.SemiBold),
)

/** Space Grotesk stays available for the call-screen big numerals (screen 13/14). */
val SpaceGroteskV2 = SpaceGrotesk

object TypeV2 {
    val Display = TextStyle(
        fontFamily = ManropeV2,
        fontWeight = FontWeight.ExtraBold,
        fontSize = 32.sp,
        lineHeight = 36.sp,
        letterSpacing = (-0.8).sp,
    )
    val SectionTitle = TextStyle(
        fontFamily = ManropeV2,
        fontWeight = FontWeight.ExtraBold,
        fontSize = 24.sp,
        lineHeight = 28.sp,
        letterSpacing = (-0.4).sp,
    )
    val VerdictHeader = TextStyle(
        fontFamily = ManropeV2,
        fontWeight = FontWeight.ExtraBold,
        fontSize = 21.sp,
        lineHeight = 23.sp,
        letterSpacing = (-0.5).sp,
    )
    val FeatureHero = TextStyle(
        fontFamily = ManropeV2,
        fontWeight = FontWeight.ExtraBold,
        fontSize = 19.sp,
        lineHeight = 24.sp,
    )
    val CardTitle = TextStyle(
        fontFamily = ManropeV2,
        fontWeight = FontWeight.ExtraBold,
        fontSize = 15.sp,
        lineHeight = 20.sp,
    )
    val Body = TextStyle(
        fontFamily = ManropeV2,
        fontWeight = FontWeight.Medium,
        fontSize = 14.sp,
        lineHeight = 20.sp,
        color = SigurTokensV2.Body,
    )
    val Caption = TextStyle(
        fontFamily = ManropeV2,
        fontWeight = FontWeight.Medium,
        fontSize = 12.5.sp,
        lineHeight = 17.sp,
        color = SigurTokensV2.Muted,
    )
    val Eyebrow = TextStyle(
        fontFamily = ManropeV2,
        fontWeight = FontWeight.ExtraBold,
        fontSize = 11.sp,
        lineHeight = 14.sp,
        letterSpacing = 0.8.sp,
    )
    val Mono = TextStyle(
        fontFamily = JetBrainsMonoV2,
        fontWeight = FontWeight.SemiBold,
        fontSize = 12.5.sp,
        lineHeight = 16.sp,
    )
    val MonoLarge = TextStyle(
        fontFamily = JetBrainsMonoV2,
        fontWeight = FontWeight.Medium,
        fontSize = 14.sp,
        lineHeight = 18.sp,
    )
}
