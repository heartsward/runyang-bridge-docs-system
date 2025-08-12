package com.runyang.bridge.maintenance.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.Index

/**
 * 下载任务实体
 * 用于管理文档下载任务的状态和进度
 */
@Entity(
    tableName = "download_tasks",
    indices = [
        Index(value = ["document_id"]),
        Index(value = ["status"]),
        Index(value = ["created_at"])
    ]
)
data class DownloadTaskEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    
    /**
     * 关联的文档ID
     */
    val documentId: Int,
    
    /**
     * 下载任务状态：pending, downloading, paused, completed, failed, cancelled
     */
    val status: String,
    
    /**
     * 下载进度（0-100）
     */
    val progress: Int = 0,
    
    /**
     * 下载URL
     */
    val downloadUrl: String,
    
    /**
     * 本地文件路径
     */
    val localFilePath: String? = null,
    
    /**
     * 临时文件路径（下载中使用）
     */
    val tempFilePath: String? = null,
    
    /**
     * 文件总大小（字节）
     */
    val totalSize: Long = 0,
    
    /**
     * 已下载大小（字节）
     */
    val downloadedSize: Long = 0,
    
    /**
     * 下载速度（字节/秒）
     */
    val downloadSpeed: Long = 0,
    
    /**
     * 剩余时间（秒）
     */
    val remainingTime: Long = 0,
    
    /**
     * 创建时间戳
     */
    val createdAt: Long = System.currentTimeMillis(),
    
    /**
     * 开始下载时间戳
     */
    val startedAt: Long? = null,
    
    /**
     * 完成时间戳
     */
    val completedAt: Long? = null,
    
    /**
     * 错误信息
     */
    val errorMessage: String? = null,
    
    /**
     * 重试次数
     */
    val retryCount: Int = 0,
    
    /**
     * 是否仅在WiFi下下载
     */
    val wifiOnly: Boolean = true,
    
    /**
     * 下载优先级：high, normal, low
     */
    val priority: String = "normal",
    
    /**
     * 附加数据，JSON格式
     */
    val metadata: String? = null
)