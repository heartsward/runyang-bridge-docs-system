package com.runyang.bridge.maintenance.ui.asset

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.runyang.bridge.maintenance.domain.entity.Asset
import com.runyang.bridge.maintenance.domain.entity.AssetSortType
import com.runyang.bridge.maintenance.domain.entity.AssetStatus
import com.runyang.bridge.maintenance.domain.entity.AssetStatusColor
import com.runyang.bridge.maintenance.domain.entity.AssetType
import com.runyang.bridge.maintenance.domain.entity.MaintenanceRecord
import com.runyang.bridge.maintenance.ui.theme.RunYangBridgeMaintenanceTheme

/**
 * 资产列表界面
 * 支持搜索、筛选、排序和资产状态监控
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AssetListScreen(
    onAssetClick: (Asset) -> Unit,
    onNavigateBack: () -> Unit,
    viewModel: AssetViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    val statisticsState by viewModel.statisticsState.collectAsState()
    val searchQuery by viewModel.searchQuery.collectAsState()
    val selectedType by viewModel.selectedType.collectAsState()
    val selectedStatus by viewModel.selectedStatus.collectAsState()
    val sortType by viewModel.sortType.collectAsState()
    val focusManager = LocalFocusManager.current

    var showTypeFilter by remember { mutableStateOf(false) }
    var showStatusFilter by remember { mutableStateOf(false) }
    var showSortOptions by remember { mutableStateOf(false) }

    // 模拟资产数据
    val sampleAssets = remember {
        listOf(
            Asset(
                id = 1,
                name = "主服务器-01",
                assetType = "server",
                status = "running",
                statusDisplay = "运行中",
                location = "机房A-01",
                ipAddress = "192.168.1.100",
                model = "Dell PowerEdge R740",
                serialNumber = "SN001234567",
                manufacturer = "Dell",
                installDate = "2023-01-15",
                warrantyExpiry = "2026-01-15",
                healthScore = 95,
                lastCheck = "2024-01-15T10:30:00Z",
                nextMaintenance = "2024-02-15",
                description = "核心业务服务器，处理主要业务逻辑",
                createdAt = "2023-01-15T10:30:00Z",
                updatedAt = "2024-01-15T10:30:00Z",
                tags = listOf("核心", "服务器", "业务"),
                specifications = mapOf(
                    "CPU" to "Intel Xeon Gold 6248R",
                    "内存" to "128GB DDR4",
                    "存储" to "2TB SSD"
                ),
                maintenanceRecords = emptyList(),
                isOnline = true,
                isCritical = true
            ),
            Asset(
                id = 2,
                name = "网络交换机-A1",
                assetType = "network",
                status = "warning",
                statusDisplay = "警告",
                location = "网络机柜-A",
                ipAddress = "192.168.1.10",
                model = "Cisco Catalyst 2960",
                serialNumber = "SN987654321",
                manufacturer = "Cisco",
                installDate = "2023-02-10",
                warrantyExpiry = "2026-02-10",
                healthScore = 75,
                lastCheck = "2024-01-14T15:45:00Z",
                nextMaintenance = "2024-01-20",
                description = "核心网络交换设备",
                createdAt = "2023-02-10T10:30:00Z",
                updatedAt = "2024-01-14T15:45:00Z",
                tags = listOf("网络", "交换机", "核心"),
                specifications = mapOf(
                    "端口数" to "48",
                    "速率" to "1Gbps",
                    "协议" to "IEEE 802.3"
                ),
                maintenanceRecords = emptyList(),
                isOnline = true,
                isCritical = false
            ),
            Asset(
                id = 3,
                name = "温度传感器-T01",
                assetType = "sensor",
                status = "offline",
                statusDisplay = "离线",
                location = "桥梁南端",
                ipAddress = null,
                model = "TempSense Pro",
                serialNumber = "TS123456789",
                manufacturer = "SensorTech",
                installDate = "2023-03-01",
                warrantyExpiry = "2025-03-01",
                healthScore = 0,
                lastCheck = "2024-01-10T08:20:00Z",
                nextMaintenance = "2024-01-25",
                description = "监测桥梁结构温度变化",
                createdAt = "2023-03-01T10:30:00Z",
                updatedAt = "2024-01-10T08:20:00Z",
                tags = listOf("传感器", "温度", "监测"),
                specifications = mapOf(
                    "测量范围" to "-40°C ~ +85°C",
                    "精度" to "±0.1°C",
                    "通信" to "LoRa"
                ),
                maintenanceRecords = emptyList(),
                isOnline = false,
                isCritical = false
            )
        )
    }

    // 错误和消息处理
    LaunchedEffect(uiState.error) {
        uiState.error?.let {
            viewModel.clearError()
        }
    }

    LaunchedEffect(uiState.message) {
        uiState.message?.let {
            viewModel.clearMessage()
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
    ) {
        // 顶部应用栏
        TopAppBar(
            title = { 
                Text(
                    text = "设备资产",
                    style = MaterialTheme.typography.titleLarge.copy(
                        fontWeight = FontWeight.Bold
                    )
                )
            },
            navigationIcon = {
                IconButton(onClick = onNavigateBack) {
                    Icon(
                        imageVector = Icons.Filled.ArrowBack,
                        contentDescription = "返回"
                    )
                }
            },
            actions = {
                // 刷新按钮
                IconButton(onClick = { viewModel.refresh() }) {
                    Icon(
                        imageVector = Icons.Filled.Refresh,
                        contentDescription = "刷新"
                    )
                }
                // 排序按钮
                IconButton(onClick = { showSortOptions = true }) {
                    Icon(
                        imageVector = Icons.Filled.Sort,
                        contentDescription = "排序"
                    )
                }
                // 筛选按钮
                IconButton(onClick = { /* 显示筛选选项 */ }) {
                    Icon(
                        imageVector = Icons.Filled.FilterList,
                        contentDescription = "筛选"
                    )
                }
            },
            colors = TopAppBarDefaults.topAppBarColors(
                containerColor = MaterialTheme.colorScheme.surface
            )
        )

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // 搜索栏
            OutlinedTextField(
                value = searchQuery,
                onValueChange = viewModel::searchAssets,
                placeholder = { 
                    Text("搜索设备名称、型号或位置...")
                },
                leadingIcon = {
                    Icon(
                        imageVector = Icons.Filled.Search,
                        contentDescription = "搜索"
                    )
                },
                trailingIcon = {
                    if (searchQuery.isNotEmpty()) {
                        IconButton(onClick = viewModel::clearSearch) {
                            Icon(
                                imageVector = Icons.Filled.Clear,
                                contentDescription = "清除搜索"
                            )
                        }
                    }
                },
                keyboardOptions = KeyboardOptions(
                    imeAction = ImeAction.Search
                ),
                keyboardActions = KeyboardActions(
                    onSearch = { focusManager.clearFocus() }
                ),
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp)
            )

            // 统计卡片
            StatisticsCard(
                statistics = statisticsState,
                onStatusClick = { status ->
                    viewModel.setAssetStatus(status)
                }
            )

            // 筛选标签
            if (selectedType != null || selectedStatus != null) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "筛选：",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    
                    selectedType?.let { type ->
                        FilterChip(
                            onClick = { viewModel.setAssetType(null) },
                            label = { Text(type.displayName) },
                            selected = true,
                            trailingIcon = {
                                Icon(
                                    imageVector = Icons.Filled.Close,
                                    contentDescription = "移除筛选",
                                    modifier = Modifier.size(16.dp)
                                )
                            }
                        )
                    }
                    
                    selectedStatus?.let { status ->
                        FilterChip(
                            onClick = { viewModel.setAssetStatus(null) },
                            label = { Text(status.displayName) },
                            selected = true,
                            trailingIcon = {
                                Icon(
                                    imageVector = Icons.Filled.Close,
                                    contentDescription = "移除筛选",
                                    modifier = Modifier.size(16.dp)
                                )
                            }
                        )
                    }
                    
                    Spacer(modifier = Modifier.weight(1f))
                    
                    TextButton(onClick = { viewModel.clearAllFilters() }) {
                        Text("清除全部")
                    }
                }
            }

            // 快速筛选按钮
            LazyRow(
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                item {
                    FilterChip(
                        onClick = { showTypeFilter = true },
                        label = { Text("设备类型") },
                        selected = selectedType != null,
                        leadingIcon = {
                            Icon(
                                imageVector = Icons.Filled.Category,
                                contentDescription = null,
                                modifier = Modifier.size(16.dp)
                            )
                        }
                    )
                }
                
                item {
                    FilterChip(
                        onClick = { showStatusFilter = true },
                        label = { Text("设备状态") },
                        selected = selectedStatus != null,
                        leadingIcon = {
                            Icon(
                                imageVector = Icons.Filled.Circle,
                                contentDescription = null,
                                modifier = Modifier.size(16.dp)
                            )
                        }
                    )
                }
                
                item {
                    FilterChip(
                        onClick = { viewModel.setAssetStatus(AssetStatus.OFFLINE) },
                        label = { Text("仅显示离线") },
                        selected = selectedStatus == AssetStatus.OFFLINE
                    )
                }
                
                item {
                    FilterChip(
                        onClick = { viewModel.setAssetStatus(AssetStatus.WARNING) },
                        label = { Text("仅显示警告") },
                        selected = selectedStatus == AssetStatus.WARNING
                    )
                }
            }

            // 资产列表
            if (uiState.isLoading) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        CircularProgressIndicator()
                        Spacer(modifier = Modifier.height(16.dp))
                        Text(
                            text = "加载中...",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            } else if (sampleAssets.isEmpty()) {
                // 空状态
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Icon(
                            imageVector = Icons.Filled.DeviceHub,
                            contentDescription = null,
                            modifier = Modifier.size(64.dp),
                            tint = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        Text(
                            text = "暂无设备",
                            style = MaterialTheme.typography.titleMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "尝试调整搜索条件或筛选选项",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            } else {
                LazyColumn(
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    items(sampleAssets) { asset ->
                        AssetCard(
                            asset = asset,
                            onAssetClick = onAssetClick,
                            onHealthCheckClick = { viewModel.performHealthCheck(it.id) },
                            onStatusUpdateClick = { asset, status ->
                                viewModel.updateAssetStatus(asset.id, status)
                            },
                            isPerformingHealthCheck = uiState.performingHealthCheck == asset.id
                        )
                    }
                }
            }
        }
    }

    // 设备类型筛选对话框
    if (showTypeFilter) {
        AssetTypeFilterDialog(
            types = viewModel.getAllAssetTypes(),
            selectedType = selectedType,
            onTypeSelected = { type ->
                viewModel.setAssetType(type)
                showTypeFilter = false
            },
            onDismiss = { showTypeFilter = false }
        )
    }

    // 设备状态筛选对话框
    if (showStatusFilter) {
        AssetStatusFilterDialog(
            statuses = viewModel.getAllAssetStatuses(),
            selectedStatus = selectedStatus,
            onStatusSelected = { status ->
                viewModel.setAssetStatus(status)
                showStatusFilter = false
            },
            onDismiss = { showStatusFilter = false }
        )
    }

    // 排序选项对话框
    if (showSortOptions) {
        SortOptionsDialog(
            sortTypes = viewModel.getAllSortTypes(),
            selectedSortType = sortType,
            onSortTypeSelected = { sortType ->
                viewModel.setSortType(sortType)
                showSortOptions = false
            },
            onDismiss = { showSortOptions = false }
        )
    }
}

/**
 * 统计卡片组件
 */
@Composable
fun StatisticsCard(
    statistics: AssetStatistics,
    onStatusClick: (AssetStatus) -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "设备概览",
                    style = MaterialTheme.typography.titleMedium.copy(
                        fontWeight = FontWeight.Bold
                    )
                )
                
                // 总设备数
                Surface(
                    shape = RoundedCornerShape(16.dp),
                    color = MaterialTheme.colorScheme.primaryContainer
                ) {
                    Text(
                        text = "总计 ${statistics.totalAssets}",
                        style = MaterialTheme.typography.bodyMedium.copy(
                            fontWeight = FontWeight.Medium
                        ),
                        color = MaterialTheme.colorScheme.onPrimaryContainer,
                        modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // 状态统计
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                StatusStatItem(
                    label = "在线",
                    count = statistics.onlineAssets,
                    color = Color(0xFF4CAF50),
                    modifier = Modifier.weight(1f),
                    onClick = { onStatusClick(AssetStatus.ONLINE) }
                )
                
                StatusStatItem(
                    label = "离线",
                    count = statistics.offlineAssets,
                    color = Color(0xFFF44336),
                    modifier = Modifier.weight(1f),
                    onClick = { onStatusClick(AssetStatus.OFFLINE) }
                )
                
                StatusStatItem(
                    label = "警告",
                    count = statistics.warningAssets,
                    color = Color(0xFFFF9800),
                    modifier = Modifier.weight(1f),
                    onClick = { onStatusClick(AssetStatus.WARNING) }
                )
                
                StatusStatItem(
                    label = "故障",
                    count = statistics.criticalAssets,
                    color = Color(0xFFE91E63),
                    modifier = Modifier.weight(1f),
                    onClick = { onStatusClick(AssetStatus.ERROR) }
                )
            }

            Spacer(modifier = Modifier.height(16.dp))

            // 健康评分
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "平均健康评分",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Row(
                        verticalAlignment = Alignment.Baseline
                    ) {
                        Text(
                            text = "${statistics.averageHealth.toInt()}",
                            style = MaterialTheme.typography.headlineMedium.copy(
                                fontWeight = FontWeight.Bold
                            ),
                            color = when {
                                statistics.averageHealth >= 80 -> Color(0xFF4CAF50)
                                statistics.averageHealth >= 60 -> Color(0xFFFF9800)
                                else -> Color(0xFFF44336)
                            }
                        )
                        Text(
                            text = " / 100",
                            style = MaterialTheme.typography.bodyLarge,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
                
                Column(
                    horizontalAlignment = Alignment.End
                ) {
                    Text(
                        text = "在线率",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Text(
                        text = "${statistics.onlinePercentage.toInt()}%",
                        style = MaterialTheme.typography.headlineMedium.copy(
                            fontWeight = FontWeight.Bold
                        ),
                        color = if (statistics.onlinePercentage >= 95) {
                            Color(0xFF4CAF50)
                        } else {
                            Color(0xFFFF9800)
                        }
                    )
                }
            }
        }
    }
}

/**
 * 状态统计项组件
 */
@Composable
fun StatusStatItem(
    label: String,
    count: Int,
    color: Color,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.clickable { onClick() },
        colors = CardDefaults.cardColors(
            containerColor = color.copy(alpha = 0.1f)
        ),
        shape = RoundedCornerShape(8.dp)
    ) {
        Column(
            modifier = Modifier.padding(12.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = count.toString(),
                style = MaterialTheme.typography.titleLarge.copy(
                    fontWeight = FontWeight.Bold
                ),
                color = color
            )
            Text(
                text = label,
                style = MaterialTheme.typography.bodySmall,
                color = color,
                textAlign = TextAlign.Center
            )
        }
    }
}

// 继续在下一部分实现其他组件...

@Preview(showBackground = true)
@Composable
fun AssetListScreenPreview() {
    RunYangBridgeMaintenanceTheme {
        AssetListScreen(
            onAssetClick = {},
            onNavigateBack = {}
        )
    }
}