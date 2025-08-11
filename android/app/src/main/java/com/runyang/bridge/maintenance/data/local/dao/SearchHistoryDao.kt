package com.runyang.bridge.maintenance.data.local.dao

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.runyang.bridge.maintenance.data.local.entity.CacheMetadataEntity
import com.runyang.bridge.maintenance.data.local.entity.DownloadTaskEntity
import com.runyang.bridge.maintenance.data.local.entity.SearchHistoryEntity
import kotlinx.coroutines.flow.Flow

/**
 * 搜索历史数据访问对象
 */
@Dao
interface SearchHistoryDao {

    // ============= 搜索历史相关 =============

    /**
     * 获取所有搜索历史
     */
    @Query("SELECT * FROM search_history ORDER BY search_time DESC")
    fun getAllSearchHistoryFlow(): Flow<List<SearchHistoryEntity>>

    /**
     * 获取最近的搜索历史
     */
    @Query("SELECT * FROM search_history ORDER BY search_time DESC LIMIT :limit")
    suspend fun getRecentSearchHistory(limit: Int = 50): List<SearchHistoryEntity>

    /**
     * 获取热门搜索词
     */
    @Query("""
        SELECT query, COUNT(*) as search_count, MAX(search_time) as last_search_time
        FROM search_history 
        WHERE search_time > :timeThreshold
        GROUP BY query 
        ORDER BY search_count DESC, last_search_time DESC 
        LIMIT :limit
    """)
    suspend fun getPopularSearchQueries(timeThreshold: Long, limit: Int = 20): List<PopularSearchQuery>

    /**
     * 根据查询文本搜索历史记录
     */
    @Query("SELECT * FROM search_history WHERE query LIKE '%' || :query || '%' ORDER BY search_time DESC")
    suspend fun searchInHistory(query: String): List<SearchHistoryEntity>

    /**
     * 获取语音搜索历史
     */
    @Query("SELECT * FROM search_history WHERE is_voice_query = 1 ORDER BY search_time DESC LIMIT :limit")
    suspend fun getVoiceSearchHistory(limit: Int = 30): List<SearchHistoryEntity>

    /**
     * 插入搜索历史
     */
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertSearchHistory(searchHistory: SearchHistoryEntity)

    /**
     * 删除搜索历史
     */
    @Delete
    suspend fun deleteSearchHistory(searchHistory: SearchHistoryEntity)

    /**
     * 根据ID删除搜索历史
     */
    @Query("DELETE FROM search_history WHERE id = :id")
    suspend fun deleteSearchHistoryById(id: Long)

    /**
     * 清除所有搜索历史
     */
    @Query("DELETE FROM search_history")
    suspend fun clearAllSearchHistory()

    /**
     * 删除过期的搜索历史
     */
    @Query("DELETE FROM search_history WHERE search_time < :threshold")
    suspend fun deleteExpiredSearchHistory(threshold: Long)

    /**
     * 获取搜索统计
     */
    @Query("""
        SELECT 
            COUNT(*) as total_searches,
            COUNT(DISTINCT query) as unique_queries,
            AVG(result_count) as avg_results,
            AVG(response_time_ms) as avg_response_time
        FROM search_history
    """)
    suspend fun getSearchStatistics(): SearchStatistics

    // ============= 缓存元数据相关 =============

    /**
     * 获取所有缓存元数据
     */
    @Query("SELECT * FROM cache_metadata ORDER BY created_time DESC")
    suspend fun getAllCacheMetadata(): List<CacheMetadataEntity>

    /**
     * 根据缓存键获取元数据
     */
    @Query("SELECT * FROM cache_metadata WHERE cache_key = :cacheKey")
    suspend fun getCacheMetadata(cacheKey: String): CacheMetadataEntity?

    /**
     * 根据类型获取缓存元数据
     */
    @Query("SELECT * FROM cache_metadata WHERE cache_type = :cacheType ORDER BY created_time DESC")
    suspend fun getCacheMetadataByType(cacheType: String): List<CacheMetadataEntity>

    /**
     * 获取过期的缓存
     */
    @Query("SELECT * FROM cache_metadata WHERE expiry_time < :currentTime")
    suspend fun getExpiredCacheMetadata(currentTime: Long): List<CacheMetadataEntity>

    /**
     * 插入缓存元数据
     */
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertCacheMetadata(cacheMetadata: CacheMetadataEntity)

    /**
     * 更新缓存访问信息
     */
    @Query("""
        UPDATE cache_metadata 
        SET last_accessed = :accessTime, access_count = access_count + 1 
        WHERE cache_key = :cacheKey
    """)
    suspend fun updateCacheAccess(cacheKey: String, accessTime: Long)

    /**
     * 删除缓存元数据
     */
    @Query("DELETE FROM cache_metadata WHERE cache_key = :cacheKey")
    suspend fun deleteCacheMetadata(cacheKey: String)

    /**
     * 删除过期缓存元数据
     */
    @Query("DELETE FROM cache_metadata WHERE expiry_time < :currentTime")
    suspend fun deleteExpiredCacheMetadata(currentTime: Long)

    /**
     * 清理LRU缓存（保留最近访问的N个）
     */
    @Query("""
        DELETE FROM cache_metadata 
        WHERE cache_key NOT IN (
            SELECT cache_key FROM cache_metadata 
            ORDER BY last_accessed DESC 
            LIMIT :keepCount
        )
    """)
    suspend fun cleanupLRUCache(keepCount: Int)

    // ============= 下载任务相关 =============

    /**
     * 获取所有下载任务
     */
    @Query("SELECT * FROM download_tasks ORDER BY created_time DESC")
    fun getAllDownloadTasksFlow(): Flow<List<DownloadTaskEntity>>

    /**
     * 根据状态获取下载任务
     */
    @Query("SELECT * FROM download_tasks WHERE status = :status ORDER BY created_time DESC")
    suspend fun getDownloadTasksByStatus(status: String): List<DownloadTaskEntity>

    /**
     * 获取进行中的下载任务
     */
    @Query("SELECT * FROM download_tasks WHERE status IN ('pending', 'downloading') ORDER BY created_time ASC")
    suspend fun getActiveDownloadTasks(): List<DownloadTaskEntity>

    /**
     * 获取进行中的下载任务（Flow）
     */
    @Query("SELECT * FROM download_tasks WHERE status IN ('pending', 'downloading') ORDER BY created_time ASC")
    fun getActiveDownloadTasksFlow(): Flow<List<DownloadTaskEntity>>

    /**
     * 根据文档ID获取下载任务
     */
    @Query("SELECT * FROM download_tasks WHERE document_id = :documentId")
    suspend fun getDownloadTaskByDocumentId(documentId: Int): DownloadTaskEntity?

    /**
     * 插入下载任务
     */
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertDownloadTask(downloadTask: DownloadTaskEntity): Long

    /**
     * 更新下载任务
     */
    @Update
    suspend fun updateDownloadTask(downloadTask: DownloadTaskEntity)

    /**
     * 更新下载进度
     */
    @Query("""
        UPDATE download_tasks 
        SET downloaded_size = :downloadedSize, progress = :progress, status = :status
        WHERE id = :taskId
    """)
    suspend fun updateDownloadProgress(taskId: Long, downloadedSize: Long, progress: Int, status: String)

    /**
     * 删除下载任务
     */
    @Delete
    suspend fun deleteDownloadTask(downloadTask: DownloadTaskEntity)

    /**
     * 根据ID删除下载任务
     */
    @Query("DELETE FROM download_tasks WHERE id = :taskId")
    suspend fun deleteDownloadTaskById(taskId: Long)

    /**
     * 删除已完成的下载任务
     */
    @Query("DELETE FROM download_tasks WHERE status = 'completed'")
    suspend fun deleteCompletedDownloadTasks()

    /**
     * 删除失败的下载任务
     */
    @Query("DELETE FROM download_tasks WHERE status = 'failed'")
    suspend fun deleteFailedDownloadTasks()
}

/**
 * 热门搜索查询数据类
 */
data class PopularSearchQuery(
    val query: String,
    val searchCount: Int,
    val lastSearchTime: Long
)

/**
 * 搜索统计数据类
 */
data class SearchStatistics(
    val totalSearches: Int,
    val uniqueQueries: Int,
    val avgResults: Double,
    val avgResponseTime: Double
)