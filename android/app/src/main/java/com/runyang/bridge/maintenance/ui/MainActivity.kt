package com.runyang.bridge.maintenance.ui

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.runyang.bridge.maintenance.ui.auth.AuthViewModel
import com.runyang.bridge.maintenance.ui.auth.LoginScreen
import com.runyang.bridge.maintenance.ui.asset.AssetListScreen
import com.runyang.bridge.maintenance.ui.document.DocumentDetailScreen
import com.runyang.bridge.maintenance.ui.document.DocumentListScreen
import com.runyang.bridge.maintenance.ui.home.HomeScreen
import com.runyang.bridge.maintenance.ui.theme.RunYangBridgeMaintenanceTheme
import dagger.hilt.android.AndroidEntryPoint

/**
 * 主Activity
 * 使用Jetpack Compose和Navigation Compose进行UI管理
 */
@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        // 安装启动屏幕
        val splashScreen = installSplashScreen()
        
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        setContent {
            RunYangBridgeMaintenanceTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    MainApp()
                }
            }
        }
    }
}

@Composable
fun MainApp() {
    val navController = rememberNavController()
    val authViewModel: AuthViewModel = hiltViewModel()
    val authState by authViewModel.authState.collectAsState()

    // 监听认证状态变化
    LaunchedEffect(authState.isLoggedIn) {
        if (authState.isLoggedIn) {
            navController.navigate("home") {
                popUpTo("login") { inclusive = true }
            }
        } else {
            navController.navigate("login") {
                popUpTo(0) { inclusive = true }
            }
        }
    }

    NavHost(
        navController = navController,
        startDestination = "login"
    ) {
        composable("login") {
            LoginScreen(
                onNavigateToHome = {
                    navController.navigate("home") {
                        popUpTo("login") { inclusive = true }
                    }
                }
            )
        }

        composable("home") {
            HomeScreen(
                onLogout = {
                    authViewModel.logout()
                    navController.navigate("login") {
                        popUpTo(0) { inclusive = true }
                    }
                },
                onNavigateToDocuments = {
                    navController.navigate("documents")
                },
                onNavigateToAssets = {
                    navController.navigate("assets")
                }
            )
        }

        // 文档管理路由
        composable("documents") {
            DocumentListScreen(
                onDocumentClick = { document ->
                    navController.navigate("document_detail/${document.id}")
                },
                onNavigateBack = {
                    navController.popBackStack()
                }
            )
        }

        composable(
            route = "document_detail/{documentId}",
            arguments = listOf(
                navArgument("documentId") {
                    type = NavType.IntType
                }
            )
        ) { backStackEntry ->
            val documentId = backStackEntry.arguments?.getInt("documentId") ?: 0
            DocumentDetailScreen(
                documentId = documentId,
                onNavigateBack = {
                    navController.popBackStack()
                },
                onPreviewDocument = { document ->
                    // TODO: 实现文档预览功能
                }
            )
        }

        // 资产管理路由
        composable("assets") {
            AssetListScreen(
                onAssetClick = { asset ->
                    // TODO: 导航到资产详情页面
                    // navController.navigate("asset_detail/${asset.id}")
                },
                onNavigateBack = {
                    navController.popBackStack()
                }
            )
        }
    }
}