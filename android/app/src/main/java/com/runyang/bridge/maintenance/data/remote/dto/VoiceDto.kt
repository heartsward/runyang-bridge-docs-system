package com.runyang.bridge.maintenance.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/**
 * 语音查询请求DTO
 */
@Serializable
data class VoiceQueryRequestDto(
    @SerialName("query_text")
    val queryText: String,
    @SerialName("query_id")
    val queryId: String? = null,
    @SerialName("limit")
    val limit: Int = 20,
    @SerialName("include_suggestions")
    val includeSuggestions: Boolean = true,
    @SerialName("filters")
    val filters: Map<String, Any>? = null,
    @SerialName("context")
    val context: Map<String, Any>? = null
)

/**
 * 语音查询响应DTO
 */
@Serializable
data class VoiceQueryResponseDto(
    @SerialName("success")
    val success: Boolean,
    @SerialName("code")
    val code: Int = 200,
    @SerialName("message")
    val message: String,
    @SerialName("data")
    val data: VoiceQueryResultDto,
    @SerialName("statistics")
    val statistics: VoiceStatisticsDto? = null,
    @SerialName("meta")
    val meta: Map<String, Any> = emptyMap()
)

/**
 * 语音查询结果DTO
 */
@Serializable
data class VoiceQueryResultDto(
    @SerialName("query")
    val query: String,
    @SerialName("intent")
    val intent: VoiceQueryIntentDto,
    @SerialName("total_results")
    val totalResults: Int,
    @SerialName("search_time")
    val searchTime: String,
    @SerialName("results")
    val results: List<VoiceSearchResultDto>,
    @SerialName("suggestions")
    val suggestions: List<String> = emptyList(),
    @SerialName("filters_applied")
    val filtersApplied: Map<String, Any> = emptyMap(),
    @SerialName("related_queries")
    val relatedQueries: List<String> = emptyList()
)

/**
 * 语音查询意图DTO
 */
@Serializable
data class VoiceQueryIntentDto(
    @SerialName("original_query")
    val originalQuery: String,
    @SerialName("query_type")
    val queryType: String,
    @SerialName("keywords")
    val keywords: List<String>,
    @SerialName("date_range")
    val dateRange: Map<String, String>? = null,
    @SerialName("file_types")
    val fileTypes: List<String> = emptyList(),
    @SerialName("asset_types")
    val assetTypes: List<String> = emptyList(),
    @SerialName("status_filters")
    val statusFilters: List<String> = emptyList(),
    @SerialName("sort_by")
    val sortBy: String = "relevance",
    @SerialName("confidence")
    val confidence: Double = 0.5
)

/**
 * 语音搜索结果DTO
 */
@Serializable
data class VoiceSearchResultDto(
    @SerialName("id")
    val id: Int,
    @SerialName("title")
    val title: String,
    @SerialName("content")
    val content: String,
    @SerialName("type")
    val type: String, // document, asset
    @SerialName("relevance_score")
    val relevanceScore: Double,
    @SerialName("created_at")
    val createdAt: String,
    @SerialName("metadata")
    val metadata: Map<String, Any> = emptyMap(),
    @SerialName("highlights")
    val highlights: List<String> = emptyList(),
    
    // 文档特定字段
    @SerialName("file_type")
    val fileType: String? = null,
    @SerialName("file_size")
    val fileSize: Long? = null,
    @SerialName("file_size_display")
    val fileSizeDisplay: String? = null,
    @SerialName("view_count")
    val viewCount: Int? = null,
    @SerialName("download_url")
    val downloadUrl: String? = null,
    @SerialName("tags")
    val tags: List<String> = emptyList(),
    @SerialName("author")
    val author: String? = null,
    
    // 资产特定字段
    @SerialName("asset_type")
    val assetType: String? = null,
    @SerialName("status")
    val status: String? = null,
    @SerialName("status_display")
    val statusDisplay: String? = null,
    @SerialName("location")
    val location: String? = null,
    @SerialName("ip_address")
    val ipAddress: String? = null,
    @SerialName("health_score")
    val healthScore: Int? = null,
    @SerialName("last_check")
    val lastCheck: String? = null
)

/**
 * 语音查询统计DTO
 */
@Serializable
data class VoiceStatisticsDto(
    @SerialName("documents_found")
    val documentsFound: Int,
    @SerialName("assets_found")
    val assetsFound: Int,
    @SerialName("average_relevance")
    val averageRelevance: Double,
    @SerialName("search_coverage")
    val searchCoverage: String, // high, medium, low
    @SerialName("query_complexity")
    val queryComplexity: String // simple, moderate, complex
)