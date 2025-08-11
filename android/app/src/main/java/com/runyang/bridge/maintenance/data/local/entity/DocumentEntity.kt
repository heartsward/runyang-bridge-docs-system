package com.runyang.bridge.maintenance.data.local.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * 文档数据库实体
 */
@Entity(
    tableName = "documents",
    indices = [
        Index(value = ["title"]),
        Index(value = ["file_type"]),
        Index(value = ["created_at"]),
        Index(value = ["last_sync_time"]),
        Index(value = ["is_favorite"])
    ]
)
data class DocumentEntity(
    @PrimaryKey
    @ColumnInfo(name = "id")
    val id: Int,
    
    @ColumnInfo(name = "title")
    val title: String,
    
    @ColumnInfo(name = "summary")
    val summary: String,
    
    @ColumnInfo(name = "description")
    val description: String? = null,
    
    @ColumnInfo(name = "content_preview")
    val contentPreview: String? = null,
    
    @ColumnInfo(name = "file_type")
    val fileType: String,
    
    @ColumnInfo(name = "file_size")
    val fileSize: Long? = null,
    
    @ColumnInfo(name = "file_size_display")
    val fileSizeDisplay: String,
    
    @ColumnInfo(name = "created_at")
    val createdAt: String,
    
    @ColumnInfo(name = "updated_at")
    val updatedAt: String,
    
    @ColumnInfo(name = "category")
    val category: String? = null,
    
    @ColumnInfo(name = "tags")
    val tags: List<String> = emptyList(),
    
    @ColumnInfo(name = "preview_available")
    val previewAvailable: Boolean = false,
    
    @ColumnInfo(name = "thumbnail_url")
    val thumbnailUrl: String? = null,
    
    @ColumnInfo(name = "view_count")
    val viewCount: Int = 0,
    
    @ColumnInfo(name = "is_favorite")
    val isFavorite: Boolean = false,
    
    @ColumnInfo(name = "is_downloaded")
    val isDownloaded: Boolean = false,
    
    @ColumnInfo(name = "local_file_path")
    val localFilePath: String? = null,
    
    @ColumnInfo(name = "download_url")
    val downloadUrl: String? = null,
    
    @ColumnInfo(name = "last_sync_time")
    val lastSyncTime: Long = System.currentTimeMillis(),
    
    @ColumnInfo(name = "is_cached")
    val isCached: Boolean = true
)