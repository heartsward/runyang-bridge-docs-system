package com.runyang.bridge.maintenance.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.Index

/**
 * 缓存元数据实体
 * 用于管理本地数据缓存的生命周期
 */
@Entity(
    tableName = "cache_metadata",
    indices = [
        Index(value = ["cache_key"], unique = true),
        Index(value = ["cache_type"]),
        Index(value = ["expires_at"])
    ]
)
data class CacheMetadataEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    
    /**
     * 缓存键，唯一标识
     */
    val cacheKey: String,
    
    /**
     * 缓存类型：documents, assets, search_results
     */
    val cacheType: String,
    
    /**
     * 缓存数据的MD5哈希值，用于验证数据完整性
     */
    val dataHash: String? = null,
    
    /**
     * 缓存大小（字节）
     */
    val cacheSize: Long = 0,
    
    /**
     * 创建时间戳
     */
    val createdAt: Long = System.currentTimeMillis(),
    
    /**
     * 最后访问时间戳，用于LRU清理
     */
    val lastAccessedAt: Long = System.currentTimeMillis(),
    
    /**
     * 过期时间戳
     */
    val expiresAt: Long,
    
    /**
     * 访问次数，用于统计热点数据
     */
    val accessCount: Long = 0,
    
    /**
     * 是否已过期
     */
    val isExpired: Boolean = false,
    
    /**
     * 附加元数据，JSON格式
     */
    val metadata: String? = null
)