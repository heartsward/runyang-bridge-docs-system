package com.runyang.bridge.maintenance.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/**
 * 系统信息响应DTO
 */
@Serializable
data class SystemInfoResponseDto(
    @SerialName("success")
    val success: Boolean,
    @SerialName("code")
    val code: Int = 200,
    @SerialName("message")
    val message: String,
    @SerialName("data")
    val data: SystemInfoDataDto
)

/**
 * 系统信息数据DTO
 */
@Serializable
data class SystemInfoDataDto(
    @SerialName("system")
    val system: SystemBasicInfoDto,
    @SerialName("server_status")
    val serverStatus: ServerStatusDto,
    @SerialName("platform")
    val platform: PlatformInfoDto,
    @SerialName("features")
    val features: Map<String, Boolean>,
    @SerialName("mobile_config")
    val mobileConfig: MobileConfigDto,
    @SerialName("api_endpoints")
    val apiEndpoints: Map<String, Map<String, String>>,
    @SerialName("security")
    val security: SecurityInfoDto,
    @SerialName("database")
    val database: DatabaseStatusDto,
    @SerialName("response_time")
    val responseTime: String,
    @SerialName("server_time")
    val serverTime: String
)

/**
 * 系统基础信息DTO
 */
@Serializable
data class SystemBasicInfoDto(
    @SerialName("server_name")
    val serverName: String,
    @SerialName("version")
    val version: String,
    @SerialName("api_version")
    val apiVersion: String,
    @SerialName("build_time")
    val buildTime: String,
    @SerialName("environment")
    val environment: String
)

/**
 * 服务器状态DTO
 */
@Serializable
data class ServerStatusDto(
    @SerialName("status")
    val status: String,
    @SerialName("uptime")
    val uptime: Double? = null,
    @SerialName("cpu_usage")
    val cpuUsage: String? = null,
    @SerialName("memory_usage")
    val memoryUsage: String? = null,
    @SerialName("memory_total")
    val memoryTotal: String? = null,
    @SerialName("disk_usage")
    val diskUsage: String? = null,
    @SerialName("disk_free")
    val diskFree: String? = null,
    @SerialName("error")
    val error: String? = null
)

/**
 * 平台信息DTO
 */
@Serializable
data class PlatformInfoDto(
    @SerialName("os")
    val os: String,
    @SerialName("os_version")
    val osVersion: String,
    @SerialName("python_version")
    val pythonVersion: String,
    @SerialName("architecture")
    val architecture: String
)

/**
 * 移动端配置DTO
 */
@Serializable
data class MobileConfigDto(
    @SerialName("max_file_size")
    val maxFileSize: Long,
    @SerialName("supported_file_types")
    val supportedFileTypes: List<String>,
    @SerialName("cache_duration")
    val cacheDuration: Int,
    @SerialName("pagination_size")
    val paginationSize: Int,
    @SerialName("search_limit")
    val searchLimit: Int,
    @SerialName("token_expiry_days")
    val tokenExpiryDays: Int,
    @SerialName("refresh_token_expiry_days")
    val refreshTokenExpiryDays: Int
)

/**
 * 安全配置DTO
 */
@Serializable
data class SecurityInfoDto(
    @SerialName("authentication_required")
    val authenticationRequired: Boolean,
    @SerialName("token_type")
    val tokenType: String,
    @SerialName("https_enabled")
    val httpsEnabled: Boolean,
    @SerialName("cors_enabled")
    val corsEnabled: Boolean,
    @SerialName("rate_limiting")
    val rateLimiting: Boolean
)

/**
 * 数据库状态DTO
 */
@Serializable
data class DatabaseStatusDto(
    @SerialName("status")
    val status: String,
    @SerialName("type")
    val type: String? = null,
    @SerialName("version")
    val version: String? = null,
    @SerialName("error")
    val error: String? = null
)