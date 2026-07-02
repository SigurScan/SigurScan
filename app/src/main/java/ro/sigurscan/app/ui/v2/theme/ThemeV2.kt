package ro.sigurscan.app.ui.v2.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

/**
 * v2 design system lives alongside the existing [ro.sigurscan.app.ui.theme.SigurScanTheme]
 * on purpose: this lets v2 screens ship and be reviewed/tested independently
 * without re-theming (and risking) every existing screen in one overnight pass.
 * Once all screens are migrated, this can replace the old theme outright.
 */
private val LightColorSchemeV2 = lightColorScheme(
    primary = SigurTokensV2.Sigur.accent,
    onPrimary = SigurTokensV2.Surface,
    secondary = SigurTokensV2.Sigur.dark,
    background = SigurTokensV2.Canvas,
    onBackground = SigurTokensV2.Ink,
    surface = SigurTokensV2.Surface,
    onSurface = SigurTokensV2.Ink,
    surfaceVariant = SigurTokensV2.Fill,
    onSurfaceVariant = SigurTokensV2.Body,
    outline = SigurTokensV2.Hairline,
    error = SigurTokensV2.Periculos.accent,
)

private val TypographyV2 = Typography(
    displayMedium = TypeV2.Display,
    headlineMedium = TypeV2.SectionTitle,
    headlineSmall = TypeV2.VerdictHeader,
    titleLarge = TypeV2.FeatureHero,
    titleMedium = TypeV2.CardTitle,
    bodyMedium = TypeV2.Body,
    bodySmall = TypeV2.Caption,
    labelSmall = TypeV2.Eyebrow,
)

@Composable
fun SigurScanV2Theme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    // v2 mockups are light-only for now; dark theme is a follow-up.
    MaterialTheme(
        colorScheme = LightColorSchemeV2,
        typography = TypographyV2,
        content = content,
    )
}
