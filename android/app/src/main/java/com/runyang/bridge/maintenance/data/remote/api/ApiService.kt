package com.runyang.bridge.maintenance.data.remote.api

import com.runyang.bridge.maintenance.data.remote.dto.AssetDetailDto
import com.runyang.bridge.maintenance.data.remote.dto.AssetListResponseDto
import com.runyang.bridge.maintenance.data.remote.dto.AuthResponseDto
import com.runyang.bridge.maintenance.data.remote.dto.DocumentDetailDto
import com.runyang.bridge.maintenance.data.remote.dto.DocumentListResponseDto
import com.runyang.bridge.maintenance.data.remote.dto.LoginRequestDto
import com.runyang.bridge.maintenance.data.remote.dto.RefreshTokenRequestDto
import com.runyang.bridge.maintenance.data.remote.dto.SystemInfoResponseDto
import com.runyang.bridge.maintenance.data.remote.dto.VoiceQueryRequestDto
import com.runyang.bridge.maintenance.data.remote.dto.VoiceQueryResponseDto
import okhttp3.ResponseBody
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query
import retrofit2.http.Streaming

/**
 * API服务接口
 * 定义所有网络请求端点
 */
interface ApiService {

    // ============= 认证相关 =============

    /**
     * 移动端用户登录
     */
    @POST("mobile/auth/login")
    suspend fun login(@Body request: LoginRequestDto): Response<AuthResponseDto>

    /**
     * 刷新访问Token
     */
    @POST("mobile/auth/refresh")
    suspend fun refreshToken(@Body request: RefreshTokenRequestDto): Response<AuthResponseDto>

    /**
     * 获取用户信息
     */
    @GET("mobile/auth/profile")
    suspend fun getUserProfile(): Response<AuthResponseDto>

    // ============= 系统信息 =============

    /**
     * 获取系统信息
     */
    @GET("system/info")
    suspend fun getSystemInfo(): Response<SystemInfoResponseDto>

    /**
     * 健康检查
     */
    @GET("system/health")
    suspend fun healthCheck(): Response<Map<String, Any>>

    /**
     * 获取系统版本信息
     */
    @GET("system/version")
    suspend fun getVersion(): Response<Map<String, Any>>

    /**
     * 获取系统能力
     */
    @GET("system/capabilities")
    suspend fun getCapabilities(): Response<Map<String, Any>>

    // ============= 文档管理 =============

    /**
     * 获取文档列表
     */
    @GET("mobile/documents/")
    suspend fun getDocuments(
        @Query("page") page: Int,
        @Query("size") size: Int,
        @Query("category") category: String? = null,
        @Query("search") search: String? = null
    ): Response<DocumentListResponseDto>

    /**
     * 获取文档详情
     */
    @GET("mobile/documents/{document_id}")
    suspend fun getDocumentDetail(
        @Path("document_id") documentId: Int
    ): Response<DocumentDetailDto>

    /**
     * 搜索文档
     */
    @POST("mobile/documents/search")
    suspend fun searchDocuments(
        @Body request: Map<String, Any>
    ): Response<DocumentListResponseDto>

    /**
     * 下载文档
     */
    @Streaming
    @GET("documents/{document_id}/download")
    suspend fun downloadDocument(
        @Path("document_id") documentId: Int
    ): Response<ResponseBody>

    // ============= 资产管理 =============

    /**
     * 获取资产列表
     */
    @GET("mobile/assets/")
    suspend fun getAssets(
        @Query("page") page: Int,
        @Query("size") size: Int,
        @Query("asset_type") assetType: String? = null,
        @Query("status") status: String? = null
    ): Response<AssetListResponseDto>

    /**
     * 获取资产详情
     */
    @GET("mobile/assets/{asset_id}")
    suspend fun getAssetDetail(
        @Path("asset_id") assetId: Int
    ): Response<AssetDetailDto>

    /**
     * 搜索资产
     */
    @POST("mobile/assets/search")
    suspend fun searchAssets(
        @Body request: Map<String, Any>
    ): Response<AssetListResponseDto>

    // ============= 语音查询 =============

    /**
     * 语音查询
     */
    @POST("voice/query")
    suspend fun voiceQuery(@Body request: VoiceQueryRequestDto): Response<VoiceQueryResponseDto>

    /**
     * 解析查询意图
     */
    @POST("voice/parse")
    suspend fun parseQuery(@Body request: Map<String, Any>): Response<Map<String, Any>>

    /**
     * 获取查询建议
     */
    @POST("voice/suggest")
    suspend fun getQuerySuggestions(@Body request: Map<String, Any>): Response<Map<String, Any>>

    // ============= 统一搜索 =============

    /**
     * 统一搜索（文档 + 资产）
     */
    @GET("search/")
    suspend fun unifiedSearch(
        @Query("q") query: String,
        @Query("type") type: String? = "mixed",
        @Query("page") page: Int = 1,
        @Query("size") size: Int = 20,
        @Query("sort") sort: String? = "relevance"
    ): Response<Map<String, Any>>

    // ============= 用户设置 =============

    /**
     * 获取用户设置
     */
    @GET("settings/profile")
    suspend fun getUserSettings(): Response<Map<String, Any>>

    /**
     * 更新用户设置
     */
    @POST("settings/profile")
    suspend fun updateUserSettings(@Body settings: Map<String, Any>): Response<Map<String, Any>>

    // ============= 分析和统计 =============

    /**
     * 获取数据统计
     */
    @GET("analytics/summary")
    suspend fun getAnalyticsSummary(): Response<Map<String, Any>>

    /**
     * 获取使用统计
     */
    @GET("analytics/usage")
    suspend fun getUsageStats(): Response<Map<String, Any>>
}