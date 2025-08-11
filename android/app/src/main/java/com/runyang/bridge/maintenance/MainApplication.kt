package com.runyang.bridge.maintenance

import android.app.Application
import androidx.hilt.work.HiltWorkerFactory
import androidx.work.Configuration
import dagger.hilt.android.HiltAndroidApp
import javax.inject.Inject

/**
 * 主应用程序类
 * 配置Hilt依赖注入和WorkManager
 */
@HiltAndroidApp
class MainApplication : Application(), Configuration.Provider {

    @Inject
    lateinit var workerFactory: HiltWorkerFactory

    override fun onCreate() {
        super.onCreate()
        
        // 初始化应用级别的配置
        initializeApp()
    }

    private fun initializeApp() {
        // 这里可以添加其他初始化逻辑
        // 例如：崩溃报告、分析工具等
        
        // 设置严格模式（仅在调试模式下）
        if (BuildConfig.DEBUG_MODE) {
            enableStrictMode()
        }
    }

    private fun enableStrictMode() {
        // 在调试模式下启用严格模式以检测潜在问题
        try {
            android.os.StrictMode.setThreadPolicy(
                android.os.StrictMode.ThreadPolicy.Builder()
                    .detectAll()
                    .penaltyLog()
                    .build()
            )
            
            android.os.StrictMode.setVmPolicy(
                android.os.StrictMode.VmPolicy.Builder()
                    .detectAll()
                    .penaltyLog()
                    .build()
            )
        } catch (e: Exception) {
            // 忽略严格模式设置错误
        }
    }

    override fun getWorkManagerConfiguration(): Configuration =
        Configuration.Builder()
            .setWorkerFactory(workerFactory)
            .setMinimumLoggingLevel(
                if (BuildConfig.DEBUG_MODE) {
                    android.util.Log.DEBUG
                } else {
                    android.util.Log.WARN
                }
            )
            .build()
}