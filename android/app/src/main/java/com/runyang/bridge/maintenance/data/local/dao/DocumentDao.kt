package com.runyang.bridge.maintenance.data.local.dao

import androidx.paging.PagingSource
import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.runyang.bridge.maintenance.data.local.entity.DocumentEntity
import kotlinx.coroutines.flow.Flow

/**
 * 文档数据访问对象
 */
@Dao
interface DocumentDao {

    /**
     * 获取所有文档（分页）
     */
    @Query("SELECT * FROM documents ORDER BY created_at DESC")
    fun getDocumentsPagingSource(): PagingSource<Int, DocumentEntity>

    /**
     * 获取所有文档（Flow）
     */
    @Query("SELECT * FROM documents ORDER BY created_at DESC")
    fun getAllDocumentsFlow(): Flow<List<DocumentEntity>>

    /**
     * 获取所有文档（一次性）
     */
    @Query("SELECT * FROM documents ORDER BY created_at DESC")
    suspend fun getAllDocuments(): List<DocumentEntity>

    /**
     * 根据ID获取文档
     */
    @Query("SELECT * FROM documents WHERE id = :documentId")
    suspend fun getDocumentById(documentId: Int): DocumentEntity?

    /**
     * 根据ID获取文档（Flow）
     */
    @Query("SELECT * FROM documents WHERE id = :documentId")
    fun getDocumentByIdFlow(documentId: Int): Flow<DocumentEntity?>

    /**
     * 搜索文档
     */
    @Query("""
        SELECT * FROM documents 
        WHERE title LIKE '%' || :query || '%' 
        OR summary LIKE '%' || :query || '%'
        OR description LIKE '%' || :query || '%'
        ORDER BY 
            CASE 
                WHEN title LIKE '%' || :query || '%' THEN 1
                WHEN summary LIKE '%' || :query || '%' THEN 2
                ELSE 3
            END,
            created_at DESC
    """)
    suspend fun searchDocuments(query: String): List<DocumentEntity>

    /**
     * 搜索文档（分页）
     */
    @Query("""
        SELECT * FROM documents 
        WHERE title LIKE '%' || :query || '%' 
        OR summary LIKE '%' || :query || '%'
        OR description LIKE '%' || :query || '%'
        ORDER BY 
            CASE 
                WHEN title LIKE '%' || :query || '%' THEN 1
                WHEN summary LIKE '%' || :query || '%' THEN 2
                ELSE 3
            END,
            created_at DESC
    """)
    fun searchDocumentsPagingSource(query: String): PagingSource<Int, DocumentEntity>

    /**
     * 根据文件类型过滤文档
     */
    @Query("SELECT * FROM documents WHERE file_type = :fileType ORDER BY created_at DESC")
    suspend fun getDocumentsByFileType(fileType: String): List<DocumentEntity>

    /**
     * 根据分类过滤文档
     */
    @Query("SELECT * FROM documents WHERE category = :category ORDER BY created_at DESC")
    suspend fun getDocumentsByCategory(category: String): List<DocumentEntity>

    /**
     * 获取收藏的文档
     */
    @Query("SELECT * FROM documents WHERE is_favorite = 1 ORDER BY created_at DESC")
    suspend fun getFavoriteDocuments(): List<DocumentEntity>

    /**
     * 获取收藏的文档（Flow）
     */
    @Query("SELECT * FROM documents WHERE is_favorite = 1 ORDER BY created_at DESC")
    fun getFavoriteDocumentsFlow(): Flow<List<DocumentEntity>>

    /**
     * 获取已下载的文档
     */
    @Query("SELECT * FROM documents WHERE is_downloaded = 1 ORDER BY created_at DESC")
    suspend fun getDownloadedDocuments(): List<DocumentEntity>

    /**
     * 获取已下载的文档（Flow）
     */
    @Query("SELECT * FROM documents WHERE is_downloaded = 1 ORDER BY created_at DESC")
    fun getDownloadedDocumentsFlow(): Flow<List<DocumentEntity>>

    /**
     * 获取最近查看的文档（按查看次数排序）
     */
    @Query("SELECT * FROM documents WHERE view_count > 0 ORDER BY view_count DESC LIMIT :limit")
    suspend fun getPopularDocuments(limit: Int = 20): List<DocumentEntity>

    /**
     * 获取文档总数
     */
    @Query("SELECT COUNT(*) FROM documents")
    suspend fun getDocumentCount(): Int

    /**
     * 获取文档总数（Flow）
     */
    @Query("SELECT COUNT(*) FROM documents")
    fun getDocumentCountFlow(): Flow<Int>

    /**
     * 插入文档
     */
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertDocument(document: DocumentEntity)

    /**
     * 插入多个文档
     */
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertDocuments(documents: List<DocumentEntity>)

    /**
     * 更新文档
     */
    @Update
    suspend fun updateDocument(document: DocumentEntity)

    /**
     * 更新收藏状态
     */
    @Query("UPDATE documents SET is_favorite = :isFavorite WHERE id = :documentId")
    suspend fun updateFavoriteStatus(documentId: Int, isFavorite: Boolean)

    /**
     * 更新下载状态
     */
    @Query("""
        UPDATE documents 
        SET is_downloaded = :isDownloaded, local_file_path = :localFilePath 
        WHERE id = :documentId
    """)
    suspend fun updateDownloadStatus(documentId: Int, isDownloaded: Boolean, localFilePath: String?)

    /**
     * 增加查看次数
     */
    @Query("UPDATE documents SET view_count = view_count + 1 WHERE id = :documentId")
    suspend fun incrementViewCount(documentId: Int)

    /**
     * 删除文档
     */
    @Delete
    suspend fun deleteDocument(document: DocumentEntity)

    /**
     * 根据ID删除文档
     */
    @Query("DELETE FROM documents WHERE id = :documentId")
    suspend fun deleteDocumentById(documentId: Int)

    /**
     * 删除所有文档
     */
    @Query("DELETE FROM documents")
    suspend fun deleteAllDocuments()

    /**
     * 删除过期缓存
     */
    @Query("DELETE FROM documents WHERE last_sync_time < :threshold")
    suspend fun deleteExpiredDocuments(threshold: Long)

    /**
     * 根据同步时间获取需要更新的文档
     */
    @Query("SELECT * FROM documents WHERE last_sync_time < :threshold")
    suspend fun getDocumentsNeedingUpdate(threshold: Long): List<DocumentEntity>

    /**
     * 获取不同文件类型的统计
     */
    @Query("""
        SELECT file_type, COUNT(*) as count 
        FROM documents 
        GROUP BY file_type 
        ORDER BY count DESC
    """)
    suspend fun getFileTypeStatistics(): List<FileTypeCount>

    /**
     * 获取不同分类的统计
     */
    @Query("""
        SELECT category, COUNT(*) as count 
        FROM documents 
        WHERE category IS NOT NULL
        GROUP BY category 
        ORDER BY count DESC
    """)
    suspend fun getCategoryStatistics(): List<CategoryCount>
}

/**
 * 文件类型统计数据类
 */
data class FileTypeCount(
    val fileType: String,
    val count: Int
)

/**
 * 分类统计数据类
 */
data class CategoryCount(
    val category: String,
    val count: Int
)