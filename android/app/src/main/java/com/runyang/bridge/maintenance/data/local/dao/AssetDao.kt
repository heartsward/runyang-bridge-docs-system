package com.runyang.bridge.maintenance.data.local.dao

import androidx.paging.PagingSource
import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.runyang.bridge.maintenance.data.local.entity.AssetEntity
import kotlinx.coroutines.flow.Flow

/**
 * 资产数据访问对象
 */
@Dao
interface AssetDao {

    /**
     * 获取所有资产（分页）
     */
    @Query("SELECT * FROM assets ORDER BY created_at DESC")
    fun getAssetsPagingSource(): PagingSource<Int, AssetEntity>

    /**
     * 获取所有资产（Flow）
     */
    @Query("SELECT * FROM assets ORDER BY created_at DESC")
    fun getAllAssetsFlow(): Flow<List<AssetEntity>>

    /**
     * 获取所有资产（一次性）
     */
    @Query("SELECT * FROM assets ORDER BY created_at DESC")
    suspend fun getAllAssets(): List<AssetEntity>

    /**
     * 根据ID获取资产
     */
    @Query("SELECT * FROM assets WHERE id = :assetId")
    suspend fun getAssetById(assetId: Int): AssetEntity?

    /**
     * 根据ID获取资产（Flow）
     */
    @Query("SELECT * FROM assets WHERE id = :assetId")
    fun getAssetByIdFlow(assetId: Int): Flow<AssetEntity?>

    /**
     * 搜索资产
     */
    @Query("""
        SELECT * FROM assets 
        WHERE name LIKE '%' || :query || '%' 
        OR description LIKE '%' || :query || '%'
        OR location LIKE '%' || :query || '%'
        ORDER BY 
            CASE 
                WHEN name LIKE '%' || :query || '%' THEN 1
                WHEN description LIKE '%' || :query || '%' THEN 2
                ELSE 3
            END,
            created_at DESC
    """)
    suspend fun searchAssets(query: String): List<AssetEntity>

    /**
     * 搜索资产（分页）
     */
    @Query("""
        SELECT * FROM assets 
        WHERE name LIKE '%' || :query || '%' 
        OR description LIKE '%' || :query || '%'
        OR location LIKE '%' || :query || '%'
        ORDER BY 
            CASE 
                WHEN name LIKE '%' || :query || '%' THEN 1
                WHEN description LIKE '%' || :query || '%' THEN 2
                ELSE 3
            END,
            created_at DESC
    """)
    fun searchAssetsPagingSource(query: String): PagingSource<Int, AssetEntity>

    /**
     * 根据资产类型过滤
     */
    @Query("SELECT * FROM assets WHERE asset_type = :assetType ORDER BY created_at DESC")
    suspend fun getAssetsByType(assetType: String): List<AssetEntity>

    /**
     * 根据状态过滤
     */
    @Query("SELECT * FROM assets WHERE status = :status ORDER BY created_at DESC")
    suspend fun getAssetsByStatus(status: String): List<AssetEntity>

    /**
     * 根据位置过滤
     */
    @Query("SELECT * FROM assets WHERE location = :location ORDER BY created_at DESC")
    suspend fun getAssetsByLocation(location: String): List<AssetEntity>

    /**
     * 根据优先级过滤
     */
    @Query("SELECT * FROM assets WHERE priority = :priority ORDER BY created_at DESC")
    suspend fun getAssetsByPriority(priority: String): List<AssetEntity>

    /**
     * 获取异常状态的资产
     */
    @Query("SELECT * FROM assets WHERE status IN ('error', 'maintenance') ORDER BY priority DESC, created_at DESC")
    suspend fun getProblematicAssets(): List<AssetEntity>

    /**
     * 获取异常状态的资产（Flow）
     */
    @Query("SELECT * FROM assets WHERE status IN ('error', 'maintenance') ORDER BY priority DESC, created_at DESC")
    fun getProblematicAssetsFlow(): Flow<List<AssetEntity>>

    /**
     * 获取健康评分低的资产
     */
    @Query("SELECT * FROM assets WHERE health_score IS NOT NULL AND health_score < :threshold ORDER BY health_score ASC")
    suspend fun getUnhealthyAssets(threshold: Int = 70): List<AssetEntity>

    /**
     * 获取健康评分低的资产（Flow）
     */
    @Query("SELECT * FROM assets WHERE health_score IS NOT NULL AND health_score < :threshold ORDER BY health_score ASC")
    fun getUnhealthyAssetsFlow(threshold: Int = 70): Flow<List<AssetEntity>>

    /**
     * 根据健康评分排序
     */
    @Query("SELECT * FROM assets WHERE health_score IS NOT NULL ORDER BY health_score DESC")
    suspend fun getAssetsByHealthScore(): List<AssetEntity>

    /**
     * 获取最近检查的资产
     */
    @Query("SELECT * FROM assets WHERE last_check IS NOT NULL ORDER BY last_check DESC LIMIT :limit")
    suspend fun getRecentlyCheckedAssets(limit: Int = 20): List<AssetEntity>

    /**
     * 获取资产总数
     */
    @Query("SELECT COUNT(*) FROM assets")
    suspend fun getAssetCount(): Int

    /**
     * 获取资产总数（Flow）
     */
    @Query("SELECT COUNT(*) FROM assets")
    fun getAssetCountFlow(): Flow<Int>

    /**
     * 插入资产
     */
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAsset(asset: AssetEntity)

    /**
     * 插入多个资产
     */
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAssets(assets: List<AssetEntity>)

    /**
     * 更新资产
     */
    @Update
    suspend fun updateAsset(asset: AssetEntity)

    /**
     * 删除资产
     */
    @Delete
    suspend fun deleteAsset(asset: AssetEntity)

    /**
     * 根据ID删除资产
     */
    @Query("DELETE FROM assets WHERE id = :assetId")
    suspend fun deleteAssetById(assetId: Int)

    /**
     * 删除所有资产
     */
    @Query("DELETE FROM assets")
    suspend fun deleteAllAssets()

    /**
     * 删除过期缓存
     */
    @Query("DELETE FROM assets WHERE last_sync_time < :threshold")
    suspend fun deleteExpiredAssets(threshold: Long)

    /**
     * 根据同步时间获取需要更新的资产
     */
    @Query("SELECT * FROM assets WHERE last_sync_time < :threshold")
    suspend fun getAssetsNeedingUpdate(threshold: Long): List<AssetEntity>

    /**
     * 获取不同资产类型的统计
     */
    @Query("""
        SELECT asset_type, COUNT(*) as count 
        FROM assets 
        GROUP BY asset_type 
        ORDER BY count DESC
    """)
    suspend fun getAssetTypeStatistics(): List<AssetTypeCount>

    /**
     * 获取不同状态的统计
     */
    @Query("""
        SELECT status, COUNT(*) as count 
        FROM assets 
        GROUP BY status 
        ORDER BY count DESC
    """)
    suspend fun getStatusStatistics(): List<StatusCount>

    /**
     * 获取不同位置的统计
     */
    @Query("""
        SELECT location, COUNT(*) as count 
        FROM assets 
        WHERE location IS NOT NULL
        GROUP BY location 
        ORDER BY count DESC
    """)
    suspend fun getLocationStatistics(): List<LocationCount>

    /**
     * 获取健康评分统计
     */
    @Query("""
        SELECT 
            CASE 
                WHEN health_score >= 90 THEN 'excellent'
                WHEN health_score >= 80 THEN 'good'
                WHEN health_score >= 70 THEN 'fair'
                WHEN health_score >= 60 THEN 'poor'
                ELSE 'critical'
            END as health_category,
            COUNT(*) as count
        FROM assets 
        WHERE health_score IS NOT NULL
        GROUP BY health_category
        ORDER BY 
            CASE health_category
                WHEN 'excellent' THEN 1
                WHEN 'good' THEN 2
                WHEN 'fair' THEN 3
                WHEN 'poor' THEN 4
                ELSE 5
            END
    """)
    suspend fun getHealthScoreStatistics(): List<HealthScoreCount>
}

/**
 * 资产类型统计数据类
 */
data class AssetTypeCount(
    val assetType: String,
    val count: Int
)

/**
 * 状态统计数据类
 */
data class StatusCount(
    val status: String,
    val count: Int
)

/**
 * 位置统计数据类
 */
data class LocationCount(
    val location: String,
    val count: Int
)

/**
 * 健康评分统计数据类
 */
data class HealthScoreCount(
    val healthCategory: String,
    val count: Int
)