package com.runyang.bridge.maintenance.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/**
 * 登录请求DTO
 */
@Serializable
data class LoginRequestDto(
    @SerialName("username")
    val username: String,
    @SerialName("password")
    val password: String,
    @SerialName("device_id")
    val deviceId: String? = null,
    @SerialName("device_name")
    val deviceName: String? = null,
    @SerialName("platform")
    val platform: String = "android"
)

/**
 * Token刷新请求DTO
 */
@Serializable
data class RefreshTokenRequestDto(
    @SerialName("refresh_token")
    val refreshToken: String,
    @SerialName("device_id")
    val deviceId: String? = null
)

/**
 * 认证响应DTO
 */
@Serializable
data class AuthResponseDto(
    @SerialName("success")
    val success: Boolean,
    @SerialName("code")
    val code: Int = 200,
    @SerialName("message")
    val message: String,
    @SerialName("access_token")
    val accessToken: String? = null,
    @SerialName("refresh_token")
    val refreshToken: String? = null,
    @SerialName("token_type")
    val tokenType: String = "bearer",
    @SerialName("expires_in")
    val expiresIn: Int = 2592000, // 30天
    @SerialName("user")
    val user: UserProfileDto? = null,
    @SerialName("data")
    val data: Map<String, Any>? = null
)

/**
 * 用户信息DTO
 */
@Serializable
data class UserProfileDto(
    @SerialName("id")
    val id: Int,
    @SerialName("username")
    val username: String,
    @SerialName("full_name")
    val fullName: String? = null,
    @SerialName("email")
    val email: String? = null,
    @SerialName("department")
    val department: String? = null,
    @SerialName("role")
    val role: String,
    @SerialName("avatar_url")
    val avatarUrl: String? = null,
    @SerialName("last_login")
    val lastLogin: String? = null,
    @SerialName("preferences")
    val preferences: Map<String, Any> = emptyMap()
)