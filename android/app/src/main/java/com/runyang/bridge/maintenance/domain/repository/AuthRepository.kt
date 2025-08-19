package com.runyang.bridge.maintenance.domain.repository

import kotlinx.coroutines.flow.Flow

/**
 * 认证Repository接口
 */
interface AuthRepository {
    suspend fun login(username: String, password: String): Result<String>
    suspend fun logout()
    suspend fun getToken(): Flow<String?>
    suspend fun isLoggedIn(): Flow<Boolean>
    suspend fun refreshToken(): Result<String>
}