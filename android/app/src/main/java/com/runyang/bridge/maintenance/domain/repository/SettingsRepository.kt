package com.runyang.bridge.maintenance.domain.repository

import kotlinx.coroutines.flow.Flow

interface SettingsRepository {
    suspend fun getThemeMode(): Flow<String>
    suspend fun setThemeMode(mode: String)
    suspend fun getLanguage(): Flow<String>
    suspend fun setLanguage(language: String)
    suspend fun getNotificationEnabled(): Flow<Boolean>
    suspend fun setNotificationEnabled(enabled: Boolean)
    suspend fun getCacheSize(): Flow<Long>
    suspend fun clearCache()
}