package com.runyang.bridge.maintenance.data.mapper

import com.runyang.bridge.maintenance.data.local.entity.DocumentEntity
import com.runyang.bridge.maintenance.data.remote.dto.DocumentDetailDto
import com.runyang.bridge.maintenance.data.remote.dto.DocumentDto
import com.runyang.bridge.maintenance.domain.entity.Document

/**
 * 文档数据映射器
 * 负责在DTO、Entity和Domain实体之间进行转换
 */
object DocumentMapper {

    /**
     * 将API DTO转换为Domain实体
     */
    fun DocumentDto.toDomain(): Document {
        return Document(
            id = this.id,
            title = this.title,
            summary = this.summary,
            fileType = this.fileType,
            fileSize = null, // DTO中没有原始文件大小，只有显示文本
            fileSizeDisplay = this.fileSizeDisplay,
            createdAt = this.createdAt,
            updatedAt = this.updatedAt,
            category = this.category ?: "other",
            tags = this.tags,
            downloadUrl = null, // 基础DTO中没有下载链接
            previewUrl = this.thumbnailUrl,
            isFavorite = this.isFavorite,
            isDownloaded = false, // 需要从本地数据库查询
            localFilePath = null,
            lastSyncTime = System.currentTimeMillis()
        )
    }

    /**
     * 将API详情DTO转换为Domain实体
     */
    fun DocumentDetailDto.toDomain(): Document {
        return Document(
            id = this.id,
            title = this.title,
            summary = this.summary,
            fileType = this.fileType,
            fileSize = null, // DTO中没有原始文件大小
            fileSizeDisplay = this.fileSizeDisplay,
            createdAt = this.createdAt,
            updatedAt = this.updatedAt,
            category = "other", // 详情DTO中没有category字段
            tags = this.tags,
            downloadUrl = this.downloadUrl,
            previewUrl = null, // 详情DTO中没有预览URL
            isFavorite = false, // 详情DTO中没有收藏状态
            isDownloaded = false, // 需要从本地数据库查询
            localFilePath = null,
            lastSyncTime = System.currentTimeMillis()
        )
    }

    /**
     * 将Domain实体转换为本地Entity
     */
    fun Document.toEntity(): DocumentEntity {
        return DocumentEntity(
            id = this.id,
            title = this.title,
            summary = this.summary,
            fileType = this.fileType,
            fileSize = this.fileSize,
            createdAt = this.createdAt,
            updatedAt = this.updatedAt,
            tags = this.tags,
            isFavorite = this.isFavorite,
            isDownloaded = this.isDownloaded,
            localFilePath = this.localFilePath,
            lastSyncTime = this.lastSyncTime
        )
    }

    /**
     * 将本地Entity转换为Domain实体
     */
    fun DocumentEntity.toDomain(): Document {
        return Document(
            id = this.id,
            title = this.title,
            summary = this.summary,
            fileType = this.fileType,
            fileSize = this.fileSize,
            fileSizeDisplay = formatFileSize(this.fileSize),
            createdAt = this.createdAt,
            updatedAt = this.updatedAt,
            category = "other", // Entity中没有category字段
            tags = this.tags,
            downloadUrl = null, // Entity中没有下载URL
            previewUrl = null, // Entity中没有预览URL
            isFavorite = this.isFavorite,
            isDownloaded = this.isDownloaded,
            localFilePath = this.localFilePath,
            lastSyncTime = this.lastSyncTime
        )
    }

    /**
     * 批量转换DTO列表为Domain列表
     */
    fun List<DocumentDto>.toDomainList(): List<Document> {
        return this.map { it.toDomain() }
    }

    /**
     * 批量转换Entity列表为Domain列表
     */
    fun List<DocumentEntity>.toDomainListFromEntity(): List<Document> {
        return this.map { it.toDomain() }
    }

    /**
     * 批量转换Domain列表为Entity列表
     */
    fun List<Document>.toEntityList(): List<DocumentEntity> {
        return this.map { it.toEntity() }
    }

    /**
     * 格式化文件大小
     */
    private fun formatFileSize(bytes: Long?): String {
        if (bytes == null || bytes <= 0) return "未知大小"
        
        val kb = 1024.0
        val mb = kb * 1024
        val gb = mb * 1024
        
        return when {
            bytes >= gb -> String.format("%.1f GB", bytes / gb)
            bytes >= mb -> String.format("%.1f MB", bytes / mb)
            bytes >= kb -> String.format("%.1f KB", bytes / kb)
            else -> "$bytes B"
        }
    }

    /**
     * 合并远程和本地文档数据
     * 优先使用远程数据，但保留本地的下载状态和路径
     */
    fun mergeRemoteAndLocal(remote: Document, local: DocumentEntity?): Document {
        return if (local != null) {
            remote.copy(
                isFavorite = local.isFavorite,
                isDownloaded = local.isDownloaded,
                localFilePath = local.localFilePath,
                lastSyncTime = System.currentTimeMillis()
            )
        } else {
            remote.copy(lastSyncTime = System.currentTimeMillis())
        }
    }

    /**
     * 检查文档是否需要同步
     */
    fun Document.needsSync(lastSyncThreshold: Long = 24 * 60 * 60 * 1000L): Boolean {
        return (System.currentTimeMillis() - this.lastSyncTime) > lastSyncThreshold
    }
}