package com.runyang.bridge.maintenance.domain.repository

import androidx.paging.PagingData
import com.runyang.bridge.maintenance.domain.entity.Document
import com.runyang.bridge.maintenance.domain.entity.DocumentCategory
import com.runyang.bridge.maintenance.domain.entity.DocumentSortType
import kotlinx.coroutines.flow.Flow

/**
 * 文档Repository接口
 * 定义文档数据操作的抽象接口
 */
interface DocumentRepository {

    /**
     * 获取分页文档列表
     */
    fun getDocumentsPaging(
        category: String? = null,
        searchQuery: String? = null,
        sortType: DocumentSortType = DocumentSortType.CREATE_TIME_DESC
    ): Flow<PagingData<Document>>

    /**
     * 根据ID获取文档详情
     */
    suspend fun getDocumentById(documentId: Int): Result<Document>

    /**
     * 搜索文档
     */
    suspend fun searchDocuments(
        query: String,
        category: String? = null,
        page: Int = 1,
        size: Int = 20
    ): Result<List<Document>>

    /**
     * 收藏/取消收藏文档
     */
    suspend fun toggleFavorite(documentId: Int, isFavorite: Boolean): Result<Unit>

    /**
     * 下载文档
     */
    suspend fun downloadDocument(document: Document): Result<String>

    /**
     * 获取已下载的文档列表
     */
    suspend fun getDownloadedDocuments(): Flow<List<Document>>

    /**
     * 获取收藏的文档列表
     */
    suspend fun getFavoriteDocuments(): Flow<List<Document>>

    /**
     * 删除本地下载的文档
     */
    suspend fun deleteLocalDocument(documentId: Int): Result<Unit>

    /**
     * 同步文档数据
     */
    suspend fun syncDocuments(): Result<Unit>

    /**
     * 清除过期缓存
     */
    suspend fun clearExpiredCache(): Result<Unit>

    /**
     * 检查文档是否已下载
     */
    suspend fun isDocumentDownloaded(documentId: Int): Boolean

    /**
     * 获取文档下载进度
     */
    fun getDownloadProgress(documentId: Int): Flow<Float>

    /**
     * 取消文档下载
     */
    suspend fun cancelDownload(documentId: Int): Result<Unit>

    /**
     * 获取最近查看的文档
     */
    suspend fun getRecentDocuments(limit: Int = 10): Flow<List<Document>>

    /**
     * 记录文档查看历史
     */
    suspend fun recordDocumentView(documentId: Int): Result<Unit>

    /**
     * 获取文档统计信息
     */
    suspend fun getDocumentStatistics(): Result<DocumentStatistics>
}

/**
 * 文档统计信息
 */
data class DocumentStatistics(
    val totalDocuments: Int = 0,
    val downloadedDocuments: Int = 0,
    val favoriteDocuments: Int = 0,
    val recentViews: Int = 0,
    val categoriesCount: Map<String, Int> = emptyMap(),
    val totalStorageUsed: Long = 0L
)