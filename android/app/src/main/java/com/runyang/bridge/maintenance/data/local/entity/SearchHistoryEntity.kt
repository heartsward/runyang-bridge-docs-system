package com.runyang.bridge.maintenance.data.local.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * 搜索历史数据库实体
 */
@Entity(
    tableName = "search_history",
    indices = [
        Index(value = ["query"]),
        Index(value = ["search_type"]),
        Index(value = ["search_time"]),
        Index(value = ["result_count"])
    ]
)
data class SearchHistoryEntity(
    @PrimaryKey(autoGenerate = true)
    @ColumnInfo(name = "id")
    val id: Long = 0,
    
    @ColumnInfo(name = "query")
    val query: String,
    
    @ColumnInfo(name = "search_type")
    val searchType: String, // voice, text, mixed
    
    @ColumnInfo(name = "result_count")
    val resultCount: Int,
    
    @ColumnInfo(name = "search_time")
    val searchTime: Long = System.currentTimeMillis(),
    
    @ColumnInfo(name = "is_voice_query")
    val isVoiceQuery: Boolean = false,
    
    @ColumnInfo(name = "query_intent")
    val queryIntent: String? = null,
    
    @ColumnInfo(name = "filters_used")
    val filtersUsed: Map<String, Any> = emptyMap(),
    
    @ColumnInfo(name = "response_time_ms")
    val responseTimeMs: Long = 0
)

/**
 * 缓存元数据实体
 */
@Entity(
    tableName = "cache_metadata",
    indices = [
        Index(value = ["cache_key"], unique = true),
        Index(value = ["cache_type"]),
        Index(value = ["expiry_time"])
    ]
)
data class CacheMetadataEntity(
    @PrimaryKey
    @ColumnInfo(name = "cache_key")
    val cacheKey: String,
    
    @ColumnInfo(name = "cache_type")
    val cacheType: String, // document_list, asset_list, search_result, etc.
    
    @ColumnInfo(name = "created_time")
    val createdTime: Long = System.currentTimeMillis(),
    
    @ColumnInfo(name = "expiry_time")
    val expiryTime: Long,
    
    @ColumnInfo(name = "data_size")
    val dataSize: Long = 0,
    
    @ColumnInfo(name = "last_accessed")
    val lastAccessed: Long = System.currentTimeMillis(),
    
    @ColumnInfo(name = "access_count")
    val accessCount: Int = 0
)

/**
 * 下载任务实体
 */
@Entity(
    tableName = "download_tasks",
    indices = [
        Index(value = ["document_id"]),
        Index(value = ["status"]),
        Index(value = ["created_time"])
    ]
)
data class DownloadTaskEntity(
    @PrimaryKey(autoGenerate = true)
    @ColumnInfo(name = "id")
    val id: Long = 0,
    
    @ColumnInfo(name = "document_id")
    val documentId: Int,
    
    @ColumnInfo(name = "document_title")
    val documentTitle: String,
    
    @ColumnInfo(name = "file_url")
    val fileUrl: String,
    
    @ColumnInfo(name = "local_file_path")
    val localFilePath: String,
    
    @ColumnInfo(name = "file_size")
    val fileSize: Long = 0,
    
    @ColumnInfo(name = "downloaded_size")
    val downloadedSize: Long = 0,
    
    @ColumnInfo(name = "status")
    val status: String, // pending, downloading, completed, failed, cancelled
    
    @ColumnInfo(name = "progress")
    val progress: Int = 0, // 0-100
    
    @ColumnInfo(name = "error_message")
    val errorMessage: String? = null,
    
    @ColumnInfo(name = "created_time")
    val createdTime: Long = System.currentTimeMillis(),
    
    @ColumnInfo(name = "started_time")
    val startedTime: Long? = null,
    
    @ColumnInfo(name = "completed_time")
    val completedTime: Long? = null,
    
    @ColumnInfo(name = "retry_count")
    val retryCount: Int = 0
)