package com.runyang.bridge.maintenance.data.local.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * 资产数据库实体
 */
@Entity(
    tableName = "assets",
    indices = [
        Index(value = ["name"]),
        Index(value = ["asset_type"]),
        Index(value = ["status"]),
        Index(value = ["location"]),
        Index(value = ["health_score"]),
        Index(value = ["created_at"]),
        Index(value = ["last_sync_time"])
    ]
)
data class AssetEntity(
    @PrimaryKey
    @ColumnInfo(name = "id")
    val id: Int,
    
    @ColumnInfo(name = "name")
    val name: String,
    
    @ColumnInfo(name = "asset_type")
    val assetType: String,
    
    @ColumnInfo(name = "status")
    val status: String,
    
    @ColumnInfo(name = "status_display")
    val statusDisplay: String,
    
    @ColumnInfo(name = "status_icon")
    val statusIcon: String,
    
    @ColumnInfo(name = "status_color")
    val statusColor: String,
    
    @ColumnInfo(name = "location")
    val location: String? = null,
    
    @ColumnInfo(name = "ip_address")
    val ipAddress: String? = null,
    
    @ColumnInfo(name = "last_check")
    val lastCheck: String? = null,
    
    @ColumnInfo(name = "health_score")
    val healthScore: Int? = null,
    
    @ColumnInfo(name = "priority")
    val priority: String = "medium",
    
    @ColumnInfo(name = "created_at")
    val createdAt: String,
    
    @ColumnInfo(name = "description")
    val description: String? = null,
    
    @ColumnInfo(name = "specifications")
    val specifications: Map<String, Any> = emptyMap(),
    
    @ColumnInfo(name = "maintenance_info")
    val maintenanceInfo: Map<String, Any> = emptyMap(),
    
    @ColumnInfo(name = "tags")
    val tags: List<String> = emptyList(),
    
    @ColumnInfo(name = "last_sync_time")
    val lastSyncTime: Long = System.currentTimeMillis(),
    
    @ColumnInfo(name = "is_cached")
    val isCached: Boolean = true
)