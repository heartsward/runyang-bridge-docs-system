package com.runyang.bridge.maintenance.domain.entity

import android.os.Parcelable
import kotlinx.parcelize.Parcelize
import kotlinx.serialization.Serializable

/**
 * 文档实体类
 * 领域层的文档数据模型
 */
@Parcelize
@Serializable
data class Document(
    val id: Int,
    val title: String,
    val summary: String,
    val fileType: String,
    val fileSize: Long?,
    val fileSizeDisplay: String,
    val createdAt: String,
    val updatedAt: String,
    val category: String,
    val tags: List<String>,
    val downloadUrl: String?,
    val previewUrl: String?,
    val isFavorite: Boolean = false,
    val isDownloaded: Boolean = false,
    val localFilePath: String? = null,
    val lastSyncTime: Long = System.currentTimeMillis()
) : Parcelable {
    
    /**
     * 获取文件扩展名
     */
    val fileExtension: String
        get() = fileType.lowercase()
    
    /**
     * 是否支持预览
     */
    val isPreviewSupported: Boolean
        get() = when (fileExtension) {
            "pdf", "txt", "md", "doc", "docx" -> true
            else -> false
        }
    
    /**
     * 获取文件类型图标资源名
     */
    val fileTypeIcon: String
        get() = when (fileExtension) {
            "pdf" -> "ic_file_pdf"
            "doc", "docx" -> "ic_file_word"
            "xls", "xlsx" -> "ic_file_excel"
            "ppt", "pptx" -> "ic_file_powerpoint"
            "txt", "md" -> "ic_file_text"
            "jpg", "jpeg", "png", "gif" -> "ic_file_image"
            "mp4", "avi", "mov" -> "ic_file_video"
            "mp3", "wav", "aac" -> "ic_file_audio"
            "zip", "rar", "7z" -> "ic_file_archive"
            else -> "ic_file_unknown"
        }
    
    /**
     * 创建显示用的标签文本
     */
    fun getTagsText(maxTags: Int = 3): String {
        return if (tags.isEmpty()) {
            "无标签"
        } else {
            val displayTags = tags.take(maxTags)
            val tagsText = displayTags.joinToString(", ")
            if (tags.size > maxTags) {
                "$tagsText 等${tags.size}个标签"
            } else {
                tagsText
            }
        }
    }
    
    /**
     * 获取文档状态描述
     */
    fun getStatusDescription(): String {
        return when {
            isDownloaded -> "已下载"
            downloadUrl != null -> "可下载"
            else -> "在线查看"
        }
    }
}

/**
 * 文档分类枚举
 */
enum class DocumentCategory(val displayName: String, val value: String) {
    MAINTENANCE("维护文档", "maintenance"),
    OPERATION("运营文档", "operation"),
    TECHNICAL("技术文档", "technical"),
    SAFETY("安全文档", "safety"),
    TRAINING("培训文档", "training"),
    REPORT("报告文档", "report"),
    OTHER("其他文档", "other");
    
    companion object {
        fun fromValue(value: String): DocumentCategory {
            return values().find { it.value == value } ?: OTHER
        }
        
        fun getAllCategories(): List<DocumentCategory> {
            return values().toList()
        }
    }
}

/**
 * 文档排序类型
 */
enum class DocumentSortType(val displayName: String, val value: String) {
    CREATE_TIME_DESC("最新创建", "created_desc"),
    CREATE_TIME_ASC("最早创建", "created_asc"),
    UPDATE_TIME_DESC("最近更新", "updated_desc"),
    TITLE_ASC("标题A-Z", "title_asc"),
    TITLE_DESC("标题Z-A", "title_desc"),
    FILE_SIZE_DESC("文件大小(大到小)", "size_desc"),
    FILE_SIZE_ASC("文件大小(小到大)", "size_asc");
    
    companion object {
        fun fromValue(value: String): DocumentSortType {
            return values().find { it.value == value } ?: CREATE_TIME_DESC
        }
    }
}