package com.runyang.bridge.maintenance.domain.entity

import android.os.Parcelable
import kotlinx.parcelize.Parcelize
import kotlinx.serialization.Serializable

/**
 * 资产实体类
 * 领域层的资产数据模型
 */
@Parcelize
@Serializable
data class Asset(
    val id: Int,
    val name: String,
    val assetType: String,
    val status: String,
    val statusDisplay: String,
    val location: String?,
    val ipAddress: String?,
    val model: String?,
    val serialNumber: String?,
    val manufacturer: String?,
    val installDate: String?,
    val warrantyExpiry: String?,
    val healthScore: Int?,
    val lastCheck: String?,
    val nextMaintenance: String?,
    val description: String?,
    val createdAt: String,
    val updatedAt: String,
    val tags: List<String>,
    val specifications: Map<String, String>,
    val maintenanceRecords: List<MaintenanceRecord>,
    val isOnline: Boolean = false,
    val isCritical: Boolean = false,
    val lastSyncTime: Long = System.currentTimeMillis()
) : Parcelable {
    
    /**
     * 获取状态颜色
     */
    fun getStatusColor(): AssetStatusColor {
        return when (status.lowercase()) {
            "running", "online", "active" -> AssetStatusColor.SUCCESS
            "warning", "maintenance", "degraded" -> AssetStatusColor.WARNING
            "error", "failed", "offline", "critical" -> AssetStatusColor.ERROR
            "unknown", "pending" -> AssetStatusColor.INFO
            else -> AssetStatusColor.DEFAULT
        }
    }
    
    /**
     * 获取资产类型图标
     */
    val typeIcon: String
        get() = when (assetType.lowercase()) {
            "server" -> "ic_server"
            "network" -> "ic_network"
            "sensor" -> "ic_sensors"
            "camera" -> "ic_camera"
            "bridge" -> "ic_bridge"
            "cable" -> "ic_cable"
            "controller" -> "ic_controller"
            "monitor" -> "ic_monitor"
            "database" -> "ic_database"
            "storage" -> "ic_storage"
            else -> "ic_device_unknown"
        }
    
    /**
     * 是否需要维护
     */
    val needsMaintenance: Boolean
        get() {
            if (nextMaintenance.isNullOrBlank()) return false
            // TODO: 实现日期比较逻辑
            return false
        }
    
    /**
     * 获取健康评级
     */
    fun getHealthGrade(): String {
        return when (healthScore) {
            in 90..100 -> "优秀"
            in 80..89 -> "良好"
            in 70..79 -> "一般"
            in 60..69 -> "较差"
            in 0..59 -> "糟糕"
            else -> "未知"
        }
    }
    
    /**
     * 获取健康评级颜色
     */
    fun getHealthColor(): AssetStatusColor {
        return when (healthScore) {
            in 90..100 -> AssetStatusColor.SUCCESS
            in 80..89 -> AssetStatusColor.SUCCESS
            in 70..79 -> AssetStatusColor.WARNING
            in 60..69 -> AssetStatusColor.WARNING
            in 0..59 -> AssetStatusColor.ERROR
            else -> AssetStatusColor.DEFAULT
        }
    }
    
    /**
     * 获取位置显示文本
     */
    fun getLocationDisplay(): String {
        return location?.takeIf { it.isNotBlank() } ?: "位置未知"
    }
    
    /**
     * 获取规格参数文本
     */
    fun getSpecificationsText(): String {
        return if (specifications.isEmpty()) {
            "暂无规格信息"
        } else {
            specifications.entries.take(3).joinToString(", ") { "${it.key}: ${it.value}" }
        }
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
}

/**
 * 维护记录
 */
@Parcelize
@Serializable
data class MaintenanceRecord(
    val id: Int,
    val assetId: Int,
    val type: String,
    val description: String,
    val performedBy: String,
    val performedAt: String,
    val cost: Double?,
    val status: String,
    val notes: String?
) : Parcelable

/**
 * 资产状态颜色枚举
 */
enum class AssetStatusColor {
    SUCCESS,    // 绿色 - 正常运行
    WARNING,    // 橙色 - 警告状态
    ERROR,      // 红色 - 错误/离线
    INFO,       // 蓝色 - 信息状态
    DEFAULT     // 默认色 - 未知状态
}

/**
 * 资产类型枚举
 */
enum class AssetType(val displayName: String, val value: String) {
    SERVER("服务器", "server"),
    NETWORK("网络设备", "network"),
    SENSOR("传感器", "sensor"),
    CAMERA("监控摄像", "camera"),
    BRIDGE_STRUCTURE("桥梁结构", "bridge"),
    CABLE("缆索", "cable"),
    CONTROLLER("控制器", "controller"),
    MONITOR("监视器", "monitor"),
    DATABASE("数据库", "database"),
    STORAGE("存储设备", "storage"),
    OTHER("其他设备", "other");
    
    companion object {
        fun fromValue(value: String): AssetType {
            return values().find { it.value == value } ?: OTHER
        }
        
        fun getAllTypes(): List<AssetType> {
            return values().toList()
        }
    }
}

/**
 * 资产状态枚举
 */
enum class AssetStatus(val displayName: String, val value: String) {
    RUNNING("运行中", "running"),
    ONLINE("在线", "online"),
    OFFLINE("离线", "offline"),
    MAINTENANCE("维护中", "maintenance"),
    ERROR("故障", "error"),
    WARNING("警告", "warning"),
    UNKNOWN("未知", "unknown"),
    PENDING("待确认", "pending");
    
    companion object {
        fun fromValue(value: String): AssetStatus {
            return values().find { it.value == value } ?: UNKNOWN
        }
        
        fun getAllStatuses(): List<AssetStatus> {
            return values().toList()
        }
    }
}

/**
 * 资产排序类型
 */
enum class AssetSortType(val displayName: String, val value: String) {
    NAME_ASC("名称A-Z", "name_asc"),
    NAME_DESC("名称Z-A", "name_desc"),
    STATUS_ASC("状态排序", "status_asc"),
    HEALTH_DESC("健康评分(高到低)", "health_desc"),
    HEALTH_ASC("健康评分(低到高)", "health_asc"),
    LAST_CHECK_DESC("最近检查", "last_check_desc"),
    CREATE_TIME_DESC("最新创建", "created_desc"),
    UPDATE_TIME_DESC("最近更新", "updated_desc");
    
    companion object {
        fun fromValue(value: String): AssetSortType {
            return values().find { it.value == value } ?: NAME_ASC
        }
    }
}