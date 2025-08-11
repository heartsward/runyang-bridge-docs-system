package com.runyang.bridge.maintenance.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/**
 * 文档DTO
 */
@Serializable
data class DocumentDto(
    @SerialName("id")
    val id: Int,
    @SerialName("title")
    val title: String,
    @SerialName("summary")
    val summary: String,
    @SerialName("file_type")
    val fileType: String,
    @SerialName("file_size_display")
    val fileSizeDisplay: String,
    @SerialName("created_at")
    val createdAt: String,
    @SerialName("updated_at")
    val updatedAt: String,
    @SerialName("category")
    val category: String? = null,
    @SerialName("tags")
    val tags: List<String> = emptyList(),
    @SerialName("preview_available")
    val previewAvailable: Boolean = false,
    @SerialName("thumbnail_url")
    val thumbnailUrl: String? = null,
    @SerialName("view_count")
    val viewCount: Int = 0,
    @SerialName("is_favorite")
    val isFavorite: Boolean = false
)

/**
 * 文档详情DTO
 */
@Serializable
data class DocumentDetailDto(
    @SerialName("id")
    val id: Int,
    @SerialName("title")
    val title: String,
    @SerialName("description")
    val description: String? = null,
    @SerialName("summary")
    val summary: String,
    @SerialName("content_preview")
    val contentPreview: String,
    @SerialName("file_type")
    val fileType: String,
    @SerialName("file_size_display")
    val fileSizeDisplay: String,
    @SerialName("created_at")
    val createdAt: String,
    @SerialName("updated_at")
    val updatedAt: String,
    @SerialName("tags")
    val tags: List<String> = emptyList(),
    @SerialName("preview_available")
    val previewAvailable: Boolean = false,
    @SerialName("view_count")
    val viewCount: Int = 0,
    @SerialName("download_url")
    val downloadUrl: String? = null,
    @SerialName("related_assets")
    val relatedAssets: List<Map<String, Any>> = emptyList()
)

/**
 * 文档列表响应DTO
 */
@Serializable
data class DocumentListResponseDto(
    @SerialName("data")
    val data: List<DocumentDto>,
    @SerialName("pagination")
    val pagination: PaginationInfoDto,
    @SerialName("meta")
    val meta: MetaInfoDto
)

/**
 * 分页信息DTO
 */
@Serializable
data class PaginationInfoDto(
    @SerialName("page")
    val page: Int,
    @SerialName("size")
    val size: Int,
    @SerialName("total")
    val total: Int,
    @SerialName("has_next")
    val hasNext: Boolean,
    @SerialName("has_prev")
    val hasPrev: Boolean
)

/**
 * 元信息DTO
 */
@Serializable
data class MetaInfoDto(
    @SerialName("cached")
    val cached: Boolean = false,
    @SerialName("response_time")
    val responseTime: String? = null,
    @SerialName("api_version")
    val apiVersion: String = "v1.1",
    @SerialName("server_time")
    val serverTime: String
)