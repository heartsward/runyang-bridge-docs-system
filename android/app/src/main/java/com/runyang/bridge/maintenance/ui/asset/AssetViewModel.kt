package com.runyang.bridge.maintenance.ui.asset

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.paging.PagingData
import androidx.paging.cachedIn
import com.runyang.bridge.maintenance.data.remote.api.ApiService
import com.runyang.bridge.maintenance.domain.entity.Asset
import com.runyang.bridge.maintenance.domain.entity.AssetSortType
import com.runyang.bridge.maintenance.domain.entity.AssetStatus
import com.runyang.bridge.maintenance.domain.entity.AssetType
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.emptyFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * 资产管理ViewModel
 * 处理资产列表、搜索、状态监控等功能
 */
@HiltViewModel
class AssetViewModel @Inject constructor(
    private val apiService: ApiService
) : ViewModel() {

    private val _uiState = MutableStateFlow(AssetUiState())
    val uiState: StateFlow<AssetUiState> = _uiState.asStateFlow()

    private val _searchQuery = MutableStateFlow("")
    val searchQuery: StateFlow<String> = _searchQuery.asStateFlow()

    private val _selectedType = MutableStateFlow<AssetType?>(null)
    val selectedType: StateFlow<AssetType?> = _selectedType.asStateFlow()

    private val _selectedStatus = MutableStateFlow<AssetStatus?>(null)
    val selectedStatus: StateFlow<AssetStatus?> = _selectedStatus.asStateFlow()

    private val _sortType = MutableStateFlow(AssetSortType.NAME_ASC)
    val sortType: StateFlow<AssetSortType> = _sortType.asStateFlow()

    private val _selectedAsset = MutableStateFlow<Asset?>(null)
    val selectedAsset: StateFlow<Asset?> = _selectedAsset.asStateFlow()

    // 分页数据流
    private var _assetsPagingFlow: Flow<PagingData<Asset>> = emptyFlow()
    val assetsPagingFlow: Flow<PagingData<Asset>>
        get() = _assetsPagingFlow.cachedIn(viewModelScope)

    // 统计数据
    private val _statisticsState = MutableStateFlow(AssetStatistics())
    val statisticsState: StateFlow<AssetStatistics> = _statisticsState.asStateFlow()

    init {
        // 初始化加载资产列表和统计数据
        loadAssets()
        loadStatistics()
    }

    /**
     * 加载资产列表
     */
    fun loadAssets() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            
            try {
                // TODO: 实现分页数据源
                // _assetsPagingFlow = assetRepository.getAssetsPaging(
                //     type = _selectedType.value?.value,
                //     status = _selectedStatus.value?.value,
                //     searchQuery = _searchQuery.value,
                //     sortType = _sortType.value
                // ).cachedIn(viewModelScope)
                
                _uiState.value = _uiState.value.copy(isLoading = false)
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = e.message ?: "加载资产失败"
                )
            }
        }
    }

    /**
     * 加载统计数据
     */
    fun loadStatistics() {
        viewModelScope.launch {
            try {
                // TODO: 从API获取统计数据
                // val stats = assetRepository.getAssetStatistics()
                
                // 模拟统计数据
                _statisticsState.value = AssetStatistics(
                    totalAssets = 156,
                    onlineAssets = 142,
                    offlineAssets = 8,
                    warningAssets = 6,
                    criticalAssets = 2,
                    averageHealth = 85.5f
                )
            } catch (e: Exception) {
                // 统计数据加载失败时使用默认值
                _statisticsState.value = AssetStatistics()
            }
        }
    }

    /**
     * 搜索资产
     */
    fun searchAssets(query: String) {
        _searchQuery.value = query
        loadAssets()
    }

    /**
     * 设置类型筛选
     */
    fun setAssetType(type: AssetType?) {
        _selectedType.value = type
        loadAssets()
    }

    /**
     * 设置状态筛选
     */
    fun setAssetStatus(status: AssetStatus?) {
        _selectedStatus.value = status
        loadAssets()
    }

    /**
     * 设置排序方式
     */
    fun setSortType(sortType: AssetSortType) {
        _sortType.value = sortType
        loadAssets()
    }

    /**
     * 清除搜索
     */
    fun clearSearch() {
        _searchQuery.value = ""
        loadAssets()
    }

    /**
     * 清除所有筛选
     */
    fun clearAllFilters() {
        _searchQuery.value = ""
        _selectedType.value = null
        _selectedStatus.value = null
        _sortType.value = AssetSortType.NAME_ASC
        loadAssets()
    }

    /**
     * 选择资产（用于详情页面）
     */
    fun selectAsset(asset: Asset) {
        _selectedAsset.value = asset
    }

    /**
     * 更新资产状态
     */
    fun updateAssetStatus(assetId: Int, newStatus: AssetStatus) {
        viewModelScope.launch {
            try {
                // TODO: 调用API更新资产状态
                // assetRepository.updateAssetStatus(assetId, newStatus.value)
                
                _uiState.value = _uiState.value.copy(
                    message = "资产状态更新成功"
                )
                
                // 重新加载数据
                loadAssets()
                loadStatistics()
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    error = e.message ?: "状态更新失败"
                )
            }
        }
    }

    /**
     * 执行健康检查
     */
    fun performHealthCheck(assetId: Int) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(performingHealthCheck = assetId)
            
            try {
                // TODO: 调用API执行健康检查
                // val result = assetRepository.performHealthCheck(assetId)
                
                // 模拟健康检查延迟
                kotlinx.coroutines.delay(3000)
                
                _uiState.value = _uiState.value.copy(
                    performingHealthCheck = null,
                    message = "健康检查完成"
                )
                
                // 重新加载数据
                loadAssets()
                loadStatistics()
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    performingHealthCheck = null,
                    error = e.message ?: "健康检查失败"
                )
            }
        }
    }

    /**
     * 创建维护记录
     */
    fun createMaintenanceRecord(assetId: Int, description: String, type: String) {
        viewModelScope.launch {
            try {
                // TODO: 调用API创建维护记录
                // assetRepository.createMaintenanceRecord(assetId, description, type)
                
                _uiState.value = _uiState.value.copy(
                    message = "维护记录创建成功"
                )
                
                // 重新加载资产数据
                loadAssets()
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    error = e.message ?: "创建维护记录失败"
                )
            }
        }
    }

    /**
     * 刷新资产列表
     */
    fun refresh() {
        loadAssets()
        loadStatistics()
    }

    /**
     * 清除错误消息
     */
    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }

    /**
     * 清除提示消息
     */
    fun clearMessage() {
        _uiState.value = _uiState.value.copy(message = null)
    }

    /**
     * 获取所有资产类型
     */
    fun getAllAssetTypes(): List<AssetType> {
        return AssetType.getAllTypes()
    }

    /**
     * 获取所有资产状态
     */
    fun getAllAssetStatuses(): List<AssetStatus> {
        return AssetStatus.getAllStatuses()
    }

    /**
     * 获取所有排序选项
     */
    fun getAllSortTypes(): List<AssetSortType> {
        return AssetSortType.values().toList()
    }

    /**
     * 根据状态获取资产数量（用于统计）
     */
    fun getAssetCountByStatus(status: AssetStatus): Int {
        return when (status) {
            AssetStatus.ONLINE -> statisticsState.value.onlineAssets
            AssetStatus.OFFLINE -> statisticsState.value.offlineAssets
            AssetStatus.WARNING -> statisticsState.value.warningAssets
            AssetStatus.ERROR -> statisticsState.value.criticalAssets
            else -> 0
        }
    }
}

/**
 * 资产UI状态
 */
data class AssetUiState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val message: String? = null,
    val performingHealthCheck: Int? = null,
    val isEmpty: Boolean = false
)

/**
 * 资产统计数据
 */
data class AssetStatistics(
    val totalAssets: Int = 0,
    val onlineAssets: Int = 0,
    val offlineAssets: Int = 0,
    val warningAssets: Int = 0,
    val criticalAssets: Int = 0,
    val averageHealth: Float = 0f
) {
    /**
     * 在线率百分比
     */
    val onlinePercentage: Float
        get() = if (totalAssets > 0) (onlineAssets.toFloat() / totalAssets) * 100 else 0f
    
    /**
     * 健康评级
     */
    val healthGrade: String
        get() = when (averageHealth) {
            in 90f..100f -> "优秀"
            in 80f..89f -> "良好"
            in 70f..79f -> "一般"
            in 60f..69f -> "较差"
            in 0f..59f -> "糟糕"
            else -> "未知"
        }
}