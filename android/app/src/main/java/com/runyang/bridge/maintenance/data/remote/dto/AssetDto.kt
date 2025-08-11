package com.runyang.bridge.maintenance.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/**
 * 资产DTO
 */
@Serializable
data class AssetDto(
    @SerialName("id")
    val id: Int,
    @SerialName("name")
    val name: String,
    @SerialName("asset_type")
    val assetType: String,
    @SerialName("status")
    val status: String,
    @SerialName("status_display")
    val statusDisplay: String,
    @SerialName("status_icon")
    val statusIcon: String,
    @SerialName("status_color")
    val statusColor: String,
    @SerialName("location")
    val location: String? = null,
    @SerialName("ip_address")
    val ipAddress: String? = null,
    @SerialName("last_check")
    val lastCheck: String? = null,
    @SerialName("health_score")
    val healthScore: Int? = null,
    @SerialName("priority")
    val priority: String = "medium",
    @SerialName("created_at")
    val createdAt: String
)

/**
 * 资产详情DTO
 */
@Serializable
data class AssetDetailDto(
    @SerialName("id")
    val id: Int,
    @SerialName("name")
    val name: String,
    @SerialName("asset_type")
    val assetType: String,
    @SerialName("status")
    val status: String,
    @SerialName("status_display")
    val statusDisplay: String,
    @SerialName("status_icon")
    val statusIcon: String,
    @SerialName("status_color")
    val statusColor: String,
    @SerialName("location")
    val location: String? = null,
    @SerialName("ip_address")
    val ipAddress: String? = null,
    @SerialName("last_check")
    val lastCheck: String? = null,
    @SerialName("health_score")
    val healthScore: Int? = null,
    @SerialName("priority")
    val priority: String = "medium",
    @SerialName("created_at")
    val createdAt: String,
    @SerialName("description")
    val description: String? = null,
    @SerialName("specifications")
    val specifications: Map<String, Any> = emptyMap(),
    @SerialName("maintenance_info")
    val maintenanceInfo: Map<String, Any> = emptyMap(),
    @SerialName("related_documents")
    val relatedDocuments: List<Map<String, Any>> = emptyList()
)

/**
 * 资产列表响应DTO
 */
@Serializable
data class AssetListResponseDto(
    @SerialName("data")
    val data: List<AssetDto>,
    @SerialName("pagination")
    val pagination: PaginationInfoDto,
    @SerialName("meta")
    val meta: MetaInfoDto
)