package com.runyang.bridge.maintenance.ui.theme

import android.app.Activity
import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

// 润扬大桥主题色彩
private val BridgeBlue = Color(0xFF1976D2)  // 主蓝色
private val BridgeBlueVariant = Color(0xFF1565C0)  // 深蓝色
private val BridgeOrange = Color(0xFFFF9800)  // 橙色，代表阳光和活力
private val BridgeGreen = Color(0xFF4CAF50)  // 绿色，代表安全和稳定
private val BridgeRed = Color(0xFFE53935)  // 红色，用于警告和错误

private val DarkColorScheme = darkColorScheme(
    primary = BridgeBlue,
    secondary = BridgeOrange,
    tertiary = BridgeGreen,
    background = Color(0xFF121212),
    surface = Color(0xFF1E1E1E),
    error = BridgeRed,
    onPrimary = Color.White,
    onSecondary = Color.White,
    onTertiary = Color.White,
    onBackground = Color(0xFFE0E0E0),
    onSurface = Color(0xFFE0E0E0),
    onError = Color.White
)

private val LightColorScheme = lightColorScheme(
    primary = BridgeBlue,
    secondary = BridgeOrange,
    tertiary = BridgeGreen,
    background = Color(0xFFFFFBFE),
    surface = Color(0xFFFFFBFE),
    error = BridgeRed,
    onPrimary = Color.White,
    onSecondary = Color.White,
    onTertiary = Color.White,
    onBackground = Color(0xFF1C1B1F),
    onSurface = Color(0xFF1C1B1F),
    onError = Color.White
)

@Composable
fun RunYangBridgeMaintenanceTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    // Dynamic color is available on Android 12+
    dynamicColor: Boolean = true,
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
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = colorScheme.primary.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = darkTheme
        }
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}