package com.runyang.bridge.maintenance.domain.repository

import androidx.paging.PagingData
import com.runyang.bridge.maintenance.domain.entity.Asset
import com.runyang.bridge.maintenance.domain.entity.AssetSortType
import com.runyang.bridge.maintenance.domain.entity.AssetStatus
import com.runyang.bridge.maintenance.domain.entity.AssetType
import com.runyang.bridge.maintenance.domain.entity.MaintenanceRecord
import com.runyang.bridge.maintenance.ui.asset.AssetStatistics
import kotlinx.coroutines.flow.Flow

/**
 * 资产Repository接口
 * 定义资产数据操作的抽象接口
 */
interface AssetRepository {

    /**
     * 获取分页资产列表
     */
    fun getAssetsPaging(
        type: String? = null,
        status: String? = null,
        searchQuery: String? = null,
        sortType: AssetSortType = AssetSortType.NAME_ASC
    ): Flow<PagingData<Asset>>

    /**
     * 根据ID获取资产详情
     */
    suspend fun getAssetById(assetId: Int): Result<Asset>

    /**
     * 搜索资产
     */
    suspend fun searchAssets(
        query: String,
        type: String? = null,
        status: String? = null,
        page: Int = 1,
        size: Int = 20
    ): Result<List<Asset>>

    /**
     * 更新资产状态
     */
    suspend fun updateAssetStatus(assetId: Int, newStatus: String): Result<Unit>

    /**
     * 执行健康检查
     */
    suspend fun performHealthCheck(assetId: Int): Result<HealthCheckResult>

    /**
     * 获取资产统计信息
     */
    suspend fun getAssetStatistics(): Result<AssetStatistics>

    /**
     * 根据状态获取资产列表
     */
    suspend fun getAssetsByStatus(status: AssetStatus): Flow<List<Asset>>

    /**
     * 根据类型获取资产列表
     */
    suspend fun getAssetsByType(type: AssetType): Flow<List<Asset>>

    /**
     * 获取关键资产列表
     */
    suspend fun getCriticalAssets(): Flow<List<Asset>>

    /**
     * 获取离线资产列表
     */
    suspend fun getOfflineAssets(): Flow<List<Asset>>

    /**
     * 获取需要维护的资产列表
     */
    suspend fun getAssetsNeedingMaintenance(): Flow<List<Asset>>

    /**
     * 创建维护记录
     */
    suspend fun createMaintenanceRecord(
        assetId: Int,
        type: String,
        description: String,
        performedBy: String,
        cost: Double? = null,
        notes: String? = null
    ): Result<MaintenanceRecord>

    /**
     * 获取资产的维护记录
     */
    suspend fun getMaintenanceRecords(assetId: Int): Result<List<MaintenanceRecord>>

    /**
     * 更新资产信息
     */
    suspend fun updateAsset(asset: Asset): Result<Unit>

    /**
     * 同步资产数据
     */
    suspend fun syncAssets(): Result<Unit>

    /**
     * 清除过期缓存
     */
    suspend fun clearExpiredCache(): Result<Unit>

    /**
     * 获取资产健康趋势数据
     */
    suspend fun getAssetHealthTrend(
        assetId: Int,
        days: Int = 30
    ): Result<List<HealthTrendPoint>>

    /**
     * 获取资产位置信息
     */
    suspend fun getAssetLocations(): Result<List<AssetLocation>>

    /**
     * 根据位置获取资产
     */
    suspend fun getAssetsByLocation(location: String): Flow<List<Asset>>

    /**
     * 批量更新资产状态
     */
    suspend fun batchUpdateAssetStatus(
        assetIds: List<Int>,
        newStatus: String
    ): Result<BatchUpdateResult>

    /**
     * 导出资产数据
     */
    suspend fun exportAssetData(
        format: ExportFormat,
        filters: AssetExportFilters
    ): Result<String>

    /**
     * 获取资产性能指标
     */
    suspend fun getAssetMetrics(assetId: Int): Result<AssetMetrics>
}

/**
 * 健康检查结果
 */
data class HealthCheckResult(
    val assetId: Int,
    val previousScore: Int?,
    val newScore: Int,
    val checkTime: String,
    val issues: List<String> = emptyList(),
    val recommendations: List<String> = emptyList()
)

/**
 * 健康趋势数据点
 */
data class HealthTrendPoint(
    val date: String,
    val healthScore: Int,
    val status: String
)

/**
 * 资产位置信息
 */
data class AssetLocation(
    val location: String,
    val assetCount: Int,
    val onlineCount: Int,
    val offlineCount: Int
)

/**
 * 批量更新结果
 */
data class BatchUpdateResult(
    val successCount: Int,
    val failedCount: Int,
    val failedAssetIds: List<Int> = emptyList(),
    val errors: List<String> = emptyList()
)

/**
 * 导出格式
 */
enum class ExportFormat {
    CSV, JSON, EXCEL
}

/**
 * 资产导出过滤器
 */
data class AssetExportFilters(
    val types: List<String> = emptyList(),
    val statuses: List<String> = emptyList(),
    val locations: List<String> = emptyList(),
    val healthScoreRange: Pair<Int, Int>? = null,
    val dateRange: Pair<String, String>? = null
)

/**
 * 资产性能指标
 */
data class AssetMetrics(
    val assetId: Int,
    val uptimePercentage: Float,
    val averageResponseTime: Float? = null,
    val errorRate: Float? = null,
    val throughput: Float? = null,
    val lastUpdateTime: String
)