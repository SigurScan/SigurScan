package ro.sigurscan.app.ui.theme

import android.app.Activity
import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.platform.LocalContext

private val DarkColorScheme = darkColorScheme(
    primary = SigurColors.BrandLight,
    onPrimary = SigurColors.TextInverse,
    secondary = SigurColors.Brand,
    tertiary = SigurColors.Unknown,
    background = SigurColors.Canvas,
    onBackground = SigurColors.TextPrimary,
    surface = SigurColors.BackgroundCard,
    onSurface = SigurColors.TextPrimary,
    surfaceVariant = SigurColors.BackgroundSurface,
    onSurfaceVariant = SigurColors.TextSecondary,
    outline = SigurColors.GlassBorder,
    error = SigurColors.Dangerous
)

private val LightColorScheme = lightColorScheme(
    primary = SigurColors.Brand,
    onPrimary = SigurColors.TextInverse,
    secondary = SigurColors.BrandDeep,
    tertiary = SigurColors.Unknown,
    background = SigurColors.Canvas,
    onBackground = SigurColors.TextPrimary,
    surface = SigurColors.BackgroundCard,
    onSurface = SigurColors.TextPrimary,
    surfaceVariant = SigurColors.BackgroundSurface,
    onSurfaceVariant = SigurColors.TextSecondary,
    outline = SigurColors.GlassBorder,
    error = SigurColors.Dangerous
)

@Composable
fun SigurScanTheme(
    darkTheme: Boolean = false,
    // Dynamic color is available on Android 12+
    dynamicColor: Boolean = false,
    content: @Composable () -> Unit
) {
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        }

        darkTheme -> DarkColorScheme
        else -> LightColorScheme
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}
