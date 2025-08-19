package com.runyang.bridge.maintenance.data.repository

import androidx.paging.ExperimentalPagingApi
import androidx.paging.Pager
import androidx.paging.PagingConfig
import androidx.paging.PagingData
import androidx.paging.map
import com.runyang.bridge.maintenance.data.local.dao.DocumentDao
import com.runyang.bridge.maintenance.data.mapper.DocumentMapper
import com.runyang.bridge.maintenance.data.mapper.DocumentMapper.toDomain
import com.runyang.bridge.maintenance.data.mapper.DocumentMapper.toEntity
import com.runyang.bridge.maintenance.data.remote.api.ApiService
import com.runyang.bridge.maintenance.domain.entity.Document
import com.runyang.bridge.maintenance.domain.entity.DocumentSortType
import com.runyang.bridge.maintenance.domain.repository.DocumentRepository
import com.runyang.bridge.maintenance.domain.repository.DocumentStatistics
import com.runyang.bridge.maintenance.util.NetworkException
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.map
import java.io.File
import java.io.FileOutputStream
import java.net.HttpURLConnection
import java.net.URL
import javax.inject.Inject
import javax.inject.Singleton

/**
 * 文档Repository实现
 * 实现文档数据的获取、缓存和管理
 */
@Singleton
class DocumentRepositoryImpl @Inject constructor(
    private val apiService: ApiService,
    private val documentDao: DocumentDao
) : DocumentRepository {

    @OptIn(ExperimentalPagingApi::class)
    override fun getDocumentsPaging(
        category: String?,
        searchQuery: String?,
        sortType: DocumentSortType
    ): Flow<PagingData<Document>> {
        return Pager(
            config = PagingConfig(
                pageSize = 20,
                enablePlaceholders = false,
                prefetchDistance = 5
            ),
            // TODO: 实现RemoteMediator用于处理网络和本地数据同步
            // remoteMediator = DocumentRemoteMediator(
            //     apiService = apiService,
            //     documentDao = documentDao,
            //     category = category,
            //     searchQuery = searchQuery,
            //     sortType = sortType
            // ),
            pagingSourceFactory = {
                // 暂时使用本地数据
                when {
                    !searchQuery.isNullOrBlank() -> documentDao.searchDocumentsPagingSource(
                        "%$searchQuery%"
                    )
                    !category.isNullOrBlank() -> documentDao.getDocumentsByCategoryPagingSource(
                        category
                    )
                    else -> documentDao.getDocumentsPagingSource()
                }
            }
        ).flow.map { pagingData ->
            pagingData.map { entity -> entity.toDomain() }
        }
    }

    override suspend fun getDocumentById(documentId: Int): Result<Document> {
        return try {
            // 先尝试从本地获取
            val localDocument = documentDao.getDocumentById(documentId)
            if (localDocument != null) {
                return Result.success(localDocument.toDomain())
            }

            // 从远程获取
            val response = apiService.getDocumentDetail(documentId)
            if (response.isSuccessful && response.body() != null) {
                val document = response.body()!!.toDomain()
                
                // 保存到本地
                documentDao.insertDocument(document.toEntity())
                
                Result.success(document)
            } else {
                Result.failure(
                    NetworkException("获取文档详情失败: ${response.code()}")
                )
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun searchDocuments(
        query: String,
        category: String?,
        page: Int,
        size: Int
    ): Result<List<Document>> {
        return try {
            val response = apiService.searchDocuments(
                mapOf(
                    "query" to query,
                    "category" to category,
                    "page" to page,
                    "size" to size
                ).filterValues { it != null }
            )
            
            if (response.isSuccessful && response.body() != null) {
                val documents = response.body()!!.data.map { it.toDomain() }
                
                // 更新本地缓存
                documentDao.insertDocuments(documents.map { it.toEntity() })
                
                Result.success(documents)
            } else {
                Result.failure(
                    NetworkException("搜索文档失败: ${response.code()}")
                )
            }
        } catch (e: Exception) {
            // 网络失败时从本地搜索
            try {
                val localResults = documentDao.searchDocuments("%$query%")
                    .map { it.toDomain() }
                Result.success(localResults)
            } catch (localError: Exception) {
                Result.failure(e)
            }
        }
    }

    override suspend fun toggleFavorite(documentId: Int, isFavorite: Boolean): Result<Unit> {
        return try {
            documentDao.updateFavoriteStatus(documentId, isFavorite)
            
            // TODO: 如果需要同步到服务器
            // apiService.updateDocumentFavorite(documentId, isFavorite)
            
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun downloadDocument(document: Document): Result<String> {
        return try {
            if (document.downloadUrl.isNullOrBlank()) {
                return Result.failure(Exception("文档没有下载链接"))
            }

            // 创建下载目录
            val downloadsDir = File("downloads/documents")
            if (!downloadsDir.exists()) {
                downloadsDir.mkdirs()
            }

            // 生成文件名
            val fileName = "${document.id}_${document.title}.${document.fileType}"
            val file = File(downloadsDir, fileName)

            // 如果文件已存在，直接返回
            if (file.exists()) {
                return Result.success(file.absolutePath)
            }

            // 下载文件
            val url = URL(document.downloadUrl)
            val connection = url.openConnection() as HttpURLConnection
            connection.connectTimeout = 10000
            connection.readTimeout = 30000

            connection.inputStream.use { input ->
                FileOutputStream(file).use { output ->
                    input.copyTo(output)
                }
            }

            // 更新本地数据库
            documentDao.updateDownloadStatus(document.id, true, file.absolutePath)

            Result.success(file.absolutePath)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun getDownloadedDocuments(): Flow<List<Document>> {
        return documentDao.getDownloadedDocuments().map { entities ->
            entities.map { it.toDomain() }
        }
    }

    override suspend fun getFavoriteDocuments(): Flow<List<Document>> {
        return documentDao.getFavoriteDocuments().map { entities ->
            entities.map { it.toDomain() }
        }
    }

    override suspend fun deleteLocalDocument(documentId: Int): Result<Unit> {
        return try {
            val document = documentDao.getDocumentById(documentId)
            
            // 删除本地文件
            document?.localFilePath?.let { path ->
                val file = File(path)
                if (file.exists()) {
                    file.delete()
                }
            }

            // 更新数据库状态
            documentDao.updateDownloadStatus(documentId, false, null)

            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun syncDocuments(): Result<Unit> {
        return try {
            // TODO: 实现完整的同步逻辑
            // 1. 获取远程文档列表
            // 2. 比较本地和远程数据
            // 3. 更新本地数据库
            // 4. 处理冲突
            
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun clearExpiredCache(): Result<Unit> {
        return try {
            val expiryTime = System.currentTimeMillis() - (24 * 60 * 60 * 1000) // 24小时前
            documentDao.deleteOldDocuments(expiryTime)
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun isDocumentDownloaded(documentId: Int): Boolean {
        return try {
            val document = documentDao.getDocumentById(documentId)
            document?.isDownloaded == true && 
            !document.localFilePath.isNullOrBlank() && 
            File(document.localFilePath).exists()
        } catch (e: Exception) {
            false
        }
    }

    override fun getDownloadProgress(documentId: Int): Flow<Float> {
        // TODO: 实现下载进度跟踪
        return flow {
            emit(0f)
        }
    }

    override suspend fun cancelDownload(documentId: Int): Result<Unit> {
        // TODO: 实现下载取消逻辑
        return Result.success(Unit)
    }

    override suspend fun getRecentDocuments(limit: Int): Flow<List<Document>> {
        return documentDao.getRecentDocuments(limit).map { entities ->
            entities.map { it.toDomain() }
        }
    }

    override suspend fun recordDocumentView(documentId: Int): Result<Unit> {
        return try {
            // TODO: 记录查看历史到数据库
            // 可以创建一个单独的表来存储查看历史
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun getDocumentStatistics(): Result<DocumentStatistics> {
        return try {
            val totalDocuments = documentDao.getTotalDocumentsCount()
            val downloadedDocuments = documentDao.getDownloadedDocumentsCount()
            val favoriteDocuments = documentDao.getFavoriteDocumentsCount()
            
            // TODO: 计算其他统计信息
            val statistics = DocumentStatistics(
                totalDocuments = totalDocuments,
                downloadedDocuments = downloadedDocuments,
                favoriteDocuments = favoriteDocuments,
                recentViews = 0, // TODO: 从查看历史表获取
                categoriesCount = emptyMap(), // TODO: 统计各分类文档数量
                totalStorageUsed = 0L // TODO: 计算本地存储使用量
            )
            
            Result.success(statistics)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}