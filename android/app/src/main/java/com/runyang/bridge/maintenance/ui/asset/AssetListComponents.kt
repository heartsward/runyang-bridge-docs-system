package com.runyang.bridge.maintenance.ui.asset

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.runyang.bridge.maintenance.domain.entity.Asset
import com.runyang.bridge.maintenance.domain.entity.AssetSortType
import com.runyang.bridge.maintenance.domain.entity.AssetStatus
import com.runyang.bridge.maintenance.domain.entity.AssetStatusColor
import com.runyang.bridge.maintenance.domain.entity.AssetType
import com.runyang.bridge.maintenance.domain.entity.MaintenanceRecord
import com.runyang.bridge.maintenance.ui.theme.RunYangBridgeMaintenanceTheme

/**
 * 资产卡片组件
 */
@Composable
fun AssetCard(
    asset: Asset,
    onAssetClick: (Asset) -> Unit,
    onHealthCheckClick: (Asset) -> Unit,
    onStatusUpdateClick: (Asset, AssetStatus) -> Unit,
    isPerformingHealthCheck: Boolean = false,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier
            .fillMaxWidth()
            .clickable { onAssetClick(asset) },
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            // 顶部信息
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top
            ) {
                Column(
                    modifier = Modifier.weight(1f)
                ) {
                    // 设备名称
                    Text(
                        text = asset.name,
                        style = MaterialTheme.typography.titleMedium.copy(
                            fontWeight = FontWeight.Bold
                        ),
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                    
                    Spacer(modifier = Modifier.height(4.dp))
                    
                    // 设备类型和位置
                    Row(
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            imageVector = getAssetTypeIcon(asset.assetType),
                            contentDescription = null,
                            modifier = Modifier.size(16.dp),
                            tint = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text(
                            text = getAssetTypeDisplayName(asset.assetType),
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        if (!asset.location.isNullOrBlank()) {
                            Text(
                                text = " • ${asset.location}",
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                }
                
                // 状态标识
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    // 在线状态指示器
                    if (asset.isOnline) {
                        Box(
                            modifier = Modifier
                                .size(8.dp)
                                .background(Color(0xFF4CAF50), CircleShape)
                        )
                    }
                    
                    // 状态标签
                    Surface(
                        shape = RoundedCornerShape(12.dp),
                        color = getStatusColor(asset.getStatusColor())
                    ) {
                        Text(
                            text = asset.statusDisplay,
                            style = MaterialTheme.typography.bodySmall.copy(
                                fontWeight = FontWeight.Medium
                            ),
                            color = Color.White,
                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            // 描述信息
            if (!asset.description.isNullOrBlank()) {
                Text(
                    text = asset.description!!,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis
                )
                Spacer(modifier = Modifier.height(12.dp))
            }

            // 健康评分和关键信息
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                // 健康评分
                if (asset.healthScore != null) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            imageVector = Icons.Filled.Favorite,
                            contentDescription = "健康评分",
                            modifier = Modifier.size(16.dp),
                            tint = getStatusColor(asset.getHealthColor())
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text(
                            text = "${asset.healthScore}分",
                            style = MaterialTheme.typography.bodyMedium.copy(
                                fontWeight = FontWeight.Medium
                            ),
                            color = getStatusColor(asset.getHealthColor())
                        )
                        Text(
                            text = " (${asset.getHealthGrade()})",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
                
                // 关键设备标识
                if (asset.isCritical) {
                    Surface(
                        shape = RoundedCornerShape(8.dp),
                        color = Color(0xFFFF5722).copy(alpha = 0.1f)
                    ) {
                        Row(
                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(
                                imageVector = Icons.Filled.Warning,
                                contentDescription = null,
                                modifier = Modifier.size(12.dp),
                                tint = Color(0xFFFF5722)
                            )
                            Spacer(modifier = Modifier.width(2.dp))
                            Text(
                                text = "关键",
                                style = MaterialTheme.typography.bodySmall,
                                color = Color(0xFFFF5722),
                                fontSize = 10.sp
                            )
                        }
                    }
                }
            }

            // 技术规格（如果有）
            if (asset.specifications.isNotEmpty()) {
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = asset.getSpecificationsText(),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
            }

            // 标签
            if (asset.tags.isNotEmpty()) {
                Spacer(modifier = Modifier.height(8.dp))
                LazyRow(
                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    items(asset.tags.take(3)) { tag ->
                        Surface(
                            shape = RoundedCornerShape(12.dp),
                            color = MaterialTheme.colorScheme.surfaceVariant
                        ) {
                            Text(
                                text = tag,
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                            )
                        }
                    }
                    if (asset.tags.size > 3) {
                        item {
                            Surface(
                                shape = RoundedCornerShape(12.dp),
                                color = MaterialTheme.colorScheme.surfaceVariant
                            ) {
                                Text(
                                    text = "+${asset.tags.size - 3}",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                    modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                )
                            }
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            // 底部操作和信息
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                // 最后检查时间
                Column {
                    Text(
                        text = "最后检查",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Text(
                        text = formatDateTime(asset.lastCheck),
                        style = MaterialTheme.typography.bodySmall.copy(
                            fontWeight = FontWeight.Medium
                        ),
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                
                // 操作按钮
                Row(
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    // 健康检查按钮
                    IconButton(
                        onClick = { onHealthCheckClick(asset) },
                        enabled = !isPerformingHealthCheck,
                        modifier = Modifier.size(36.dp)
                    ) {
                        if (isPerformingHealthCheck) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(16.dp),
                                strokeWidth = 2.dp
                            )
                        } else {
                            Icon(
                                imageVector = Icons.Filled.HealthAndSafety,
                                contentDescription = "健康检查",
                                modifier = Modifier.size(18.dp)
                            )
                        }
                    }
                    
                    // 更多操作按钮
                    IconButton(
                        onClick = { /* TODO: 显示更多操作菜单 */ },
                        modifier = Modifier.size(36.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Filled.MoreVert,
                            contentDescription = "更多操作",
                            modifier = Modifier.size(18.dp)
                        )
                    }
                }
            }
        }
    }
}

/**
 * 设备类型筛选对话框
 */
@Composable
fun AssetTypeFilterDialog(
    types: List<AssetType>,
    selectedType: AssetType?,
    onTypeSelected: (AssetType?) -> Unit,
    onDismiss: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("选择设备类型") },
        text = {
            LazyColumn {
                item {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { onTypeSelected(null) }
                            .padding(vertical = 12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        RadioButton(
                            selected = selectedType == null,
                            onClick = { onTypeSelected(null) }
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("全部类型")
                    }
                }
                
                items(types) { type ->
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { onTypeSelected(type) }
                            .padding(vertical = 12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        RadioButton(
                            selected = selectedType == type,
                            onClick = { onTypeSelected(type) }
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Icon(
                            imageVector = getAssetTypeIcon(type.value),
                            contentDescription = null,
                            modifier = Modifier.size(20.dp),
                            tint = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(type.displayName)
                    }
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text("确定")
            }
        }
    )
}

/**
 * 设备状态筛选对话框
 */
@Composable
fun AssetStatusFilterDialog(
    statuses: List<AssetStatus>,
    selectedStatus: AssetStatus?,
    onStatusSelected: (AssetStatus?) -> Unit,
    onDismiss: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("选择设备状态") },
        text = {
            LazyColumn {
                item {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { onStatusSelected(null) }
                            .padding(vertical = 12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        RadioButton(
                            selected = selectedStatus == null,
                            onClick = { onStatusSelected(null) }
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("全部状态")
                    }
                }
                
                items(statuses) { status ->
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { onStatusSelected(status) }
                            .padding(vertical = 12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        RadioButton(
                            selected = selectedStatus == status,
                            onClick = { onStatusSelected(status) }
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Box(
                            modifier = Modifier
                                .size(12.dp)
                                .background(
                                    getStatusColorFromStatus(status),
                                    CircleShape
                                )
                        )
                        Spacer(modifier = Modifier.width(12.dp))
                        Text(status.displayName)
                    }
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text("确定")
            }
        }
    )
}

/**
 * 排序选项对话框
 */
@Composable
fun SortOptionsDialog(
    sortTypes: List<AssetSortType>,
    selectedSortType: AssetSortType,
    onSortTypeSelected: (AssetSortType) -> Unit,
    onDismiss: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("排序方式") },
        text = {
            LazyColumn {
                items(sortTypes) { sortType ->
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { onSortTypeSelected(sortType) }
                            .padding(vertical = 12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        RadioButton(
                            selected = selectedSortType == sortType,
                            onClick = { onSortTypeSelected(sortType) }
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(sortType.displayName)
                    }
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text("确定")
            }
        }
    )
}

// 辅助函数

/**
 * 根据资产类型获取图标
 */
private fun getAssetTypeIcon(assetType: String): androidx.compose.ui.graphics.vector.ImageVector {
    return when (assetType.lowercase()) {
        "server" -> Icons.Filled.Computer
        "network" -> Icons.Filled.Router
        "sensor" -> Icons.Filled.Sensors
        "camera" -> Icons.Filled.Videocam
        "bridge" -> Icons.Filled.Bridge
        "cable" -> Icons.Filled.Cable
        "controller" -> Icons.Filled.ControlCamera
        "monitor" -> Icons.Filled.Monitor
        "database" -> Icons.Filled.Storage
        "storage" -> Icons.Filled.Save
        else -> Icons.Filled.DeviceHub
    }
}

/**
 * 根据资产类型获取显示名称
 */
private fun getAssetTypeDisplayName(assetType: String): String {
    return AssetType.fromValue(assetType).displayName
}

/**
 * 根据状态颜色枚举获取颜色
 */
private fun getStatusColor(statusColor: AssetStatusColor): Color {
    return when (statusColor) {
        AssetStatusColor.SUCCESS -> Color(0xFF4CAF50)
        AssetStatusColor.WARNING -> Color(0xFFFF9800)
        AssetStatusColor.ERROR -> Color(0xFFF44336)
        AssetStatusColor.INFO -> Color(0xFF2196F3)
        AssetStatusColor.DEFAULT -> Color(0xFF9E9E9E)
    }
}

/**
 * 根据状态枚举获取颜色
 */
private fun getStatusColorFromStatus(status: AssetStatus): Color {
    return when (status) {
        AssetStatus.RUNNING, AssetStatus.ONLINE -> Color(0xFF4CAF50)
        AssetStatus.WARNING, AssetStatus.MAINTENANCE -> Color(0xFFFF9800)
        AssetStatus.ERROR, AssetStatus.OFFLINE -> Color(0xFFF44336)
        AssetStatus.PENDING -> Color(0xFF2196F3)
        AssetStatus.UNKNOWN -> Color(0xFF9E9E9E)
    }
}

/**
 * 格式化日期时间
 */
private fun formatDateTime(dateTime: String?): String {
    if (dateTime.isNullOrBlank()) return "未知"
    
    // TODO: 实现真正的日期格式化
    // 这里简化处理，实际应该使用 kotlinx.datetime 或其他日期库
    return try {
        val parts = dateTime.split("T")
        if (parts.size >= 2) {
            val date = parts[0]
            val time = parts[1].take(5) // 取前5位 HH:mm
            "$date $time"
        } else {
            dateTime
        }
    } catch (e: Exception) {
        "格式错误"
    }
}

@Preview(showBackground = true)
@Composable
fun AssetCardPreview() {
    RunYangBridgeMaintenanceTheme {
        AssetCard(
            asset = Asset(
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
            onAssetClick = {},
            onHealthCheckClick = {},
            onStatusUpdateClick = { _, _ -> }
        )
    }
}