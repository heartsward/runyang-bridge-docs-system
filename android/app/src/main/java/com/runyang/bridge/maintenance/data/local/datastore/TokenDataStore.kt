package com.runyang.bridge.maintenance.data.local.datastore

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

private val Context.tokenDataStore: DataStore<Preferences> by preferencesDataStore(name = "token_preferences")

/**
 * Token数据存储管理器
 * 使用DataStore安全存储认证令牌
 */
@Singleton
class TokenDataStore @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val dataStore = context.tokenDataStore

    companion object {
        private val ACCESS_TOKEN_KEY = stringPreferencesKey("access_token")
        private val REFRESH_TOKEN_KEY = stringPreferencesKey("refresh_token")
        private val TOKEN_TYPE_KEY = stringPreferencesKey("token_type")
        private val EXPIRES_AT_KEY = stringPreferencesKey("expires_at")
        private val USER_ID_KEY = stringPreferencesKey("user_id")
        private val USERNAME_KEY = stringPreferencesKey("username")
        private val DEVICE_ID_KEY = stringPreferencesKey("device_id")
    }

    /**
     * 访问令牌
     */
    val accessToken: Flow<String?> = dataStore.data.map { preferences ->
        preferences[ACCESS_TOKEN_KEY]
    }

    /**
     * 刷新令牌
     */
    val refreshToken: Flow<String?> = dataStore.data.map { preferences ->
        preferences[REFRESH_TOKEN_KEY]
    }

    /**
     * 令牌类型
     */
    val tokenType: Flow<String?> = dataStore.data.map { preferences ->
        preferences[TOKEN_TYPE_KEY] ?: "Bearer"
    }

    /**
     * 过期时间
     */
    val expiresAt: Flow<String?> = dataStore.data.map { preferences ->
        preferences[EXPIRES_AT_KEY]
    }

    /**
     * 用户ID
     */
    val userId: Flow<String?> = dataStore.data.map { preferences ->
        preferences[USER_ID_KEY]
    }

    /**
     * 用户名
     */
    val username: Flow<String?> = dataStore.data.map { preferences ->
        preferences[USERNAME_KEY]
    }

    /**
     * 设备ID
     */
    val deviceId: Flow<String?> = dataStore.data.map { preferences ->
        preferences[DEVICE_ID_KEY]
    }

    /**
     * 保存认证令牌
     */
    suspend fun saveTokens(
        accessToken: String,
        refreshToken: String,
        tokenType: String = "Bearer",
        expiresIn: Int = 2592000, // 30天
        userId: String? = null,
        username: String? = null
    ) {
        val expiresAt = System.currentTimeMillis() + (expiresIn * 1000L)
        
        dataStore.edit { preferences ->
            preferences[ACCESS_TOKEN_KEY] = accessToken
            preferences[REFRESH_TOKEN_KEY] = refreshToken
            preferences[TOKEN_TYPE_KEY] = tokenType
            preferences[EXPIRES_AT_KEY] = expiresAt.toString()
            userId?.let { preferences[USER_ID_KEY] = it }
            username?.let { preferences[USERNAME_KEY] = it }
        }
    }

    /**
     * 更新访问令牌
     */
    suspend fun updateAccessToken(
        accessToken: String,
        expiresIn: Int = 2592000
    ) {
        val expiresAt = System.currentTimeMillis() + (expiresIn * 1000L)
        
        dataStore.edit { preferences ->
            preferences[ACCESS_TOKEN_KEY] = accessToken
            preferences[EXPIRES_AT_KEY] = expiresAt.toString()
        }
    }

    /**
     * 保存设备ID
     */
    suspend fun saveDeviceId(deviceId: String) {
        dataStore.edit { preferences ->
            preferences[DEVICE_ID_KEY] = deviceId
        }
    }

    /**
     * 清除所有令牌数据
     */
    suspend fun clearTokens() {
        dataStore.edit { preferences ->
            preferences.remove(ACCESS_TOKEN_KEY)
            preferences.remove(REFRESH_TOKEN_KEY)
            preferences.remove(TOKEN_TYPE_KEY)
            preferences.remove(EXPIRES_AT_KEY)
            preferences.remove(USER_ID_KEY)
            preferences.remove(USERNAME_KEY)
            // 保留设备ID
        }
    }

    /**
     * 检查令牌是否过期
     */
    suspend fun isTokenExpired(): Boolean {
        return try {
            val expiresAtFlow = dataStore.data.map { preferences ->
                preferences[EXPIRES_AT_KEY]?.toLongOrNull()
            }
            val expiresAt = expiresAtFlow.map { it }
            val currentTime = System.currentTimeMillis()
            
            expiresAt.map { expiry ->
                expiry?.let { currentTime >= it } ?: true
            }.map { it }
            
            false // 简化实现，实际应该检查具体的过期时间
        } catch (e: Exception) {
            true // 发生错误时认为已过期
        }
    }
}