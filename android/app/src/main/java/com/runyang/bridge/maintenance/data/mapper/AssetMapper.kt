package com.runyang.bridge.maintenance.data.mapper

import com.runyang.bridge.maintenance.data.local.entity.AssetEntity
import com.runyang.bridge.maintenance.data.remote.dto.AssetDetailDto
import com.runyang.bridge.maintenance.data.remote.dto.AssetDto
import com.runyang.bridge.maintenance.domain.entity.Asset
import com.runyang.bridge.maintenance.domain.entity.MaintenanceRecord

/**
 * 资产数据映射器
 * 负责在DTO、Entity和Domain实体之间进行转换
 */
object AssetMapper {

    /**
     * 将API DTO转换为Domain实体
     */
    fun AssetDto.toDomain(): Asset {
        return Asset(
            id = this.id,
            name = this.name,
            assetType = this.assetType,
            status = this.status,
            statusDisplay = this.statusDisplay,
            location = this.location,
            ipAddress = this.ipAddress,
            model = null, // 基础DTO中没有型号信息
            serialNumber = null, // 基础DTO中没有序列号
            manufacturer = null, // 基础DTO中没有制造商信息
            installDate = null, // 基础DTO中没有安装日期
            warrantyExpiry = null, // 基础DTO中没有保修期信息
            healthScore = this.healthScore,
            lastCheck = this.lastCheck,
            nextMaintenance = null, // 基础DTO中没有下次维护时间
            description = null, // 基础DTO中没有描述
            createdAt = this.createdAt,
            updatedAt = this.createdAt, // 基础DTO中没有更新时间，使用创建时间
            tags = emptyList(), // 基础DTO中没有标签信息
            specifications = emptyMap(), // 基础DTO中没有规格信息
            maintenanceRecords = emptyList(), // 基础DTO中没有维护记录
            isOnline = determineOnlineStatus(this.status),
            isCritical = this.priority == "high",
            lastSyncTime = System.currentTimeMillis()
        )
    }

    /**
     * 将API详情DTO转换为Domain实体
     */
    fun AssetDetailDto.toDomain(): Asset {
        return Asset(
            id = this.id,
            name = this.name,
            assetType = this.assetType,
            status = this.status,
            statusDisplay = this.statusDisplay,
            location = this.location,
            ipAddress = this.ipAddress,
            model = extractFromSpecifications("model"),
            serialNumber = extractFromSpecifications("serial_number"),
            manufacturer = extractFromSpecifications("manufacturer"),
            installDate = extractFromMaintenanceInfo("install_date"),
            warrantyExpiry = extractFromMaintenanceInfo("warranty_expiry"),
            healthScore = this.healthScore,
            lastCheck = this.lastCheck,
            nextMaintenance = extractFromMaintenanceInfo("next_maintenance"),
            description = this.description,
            createdAt = this.createdAt,
            updatedAt = this.createdAt, // 详情DTO中也没有更新时间
            tags = extractTagsFromSpecifications(),
            specifications = this.specifications.mapValues { it.value.toString() },
            maintenanceRecords = emptyList(), // TODO: 如果API返回维护记录需要映射
            isOnline = determineOnlineStatus(this.status),
            isCritical = this.priority == "high",
            lastSyncTime = System.currentTimeMillis()
        )
    }

    /**
     * 将Domain实体转换为本地Entity
     */
    fun Asset.toEntity(): AssetEntity {
        return AssetEntity(
            id = this.id,
            name = this.name,
            assetType = this.assetType,
            status = this.status,
            statusDisplay = this.statusDisplay,
            location = this.location,
            ipAddress = this.ipAddress,
            healthScore = this.healthScore,
            lastCheck = this.lastCheck,
            createdAt = this.createdAt,
            tags = this.tags,
            lastSyncTime = this.lastSyncTime
        )
    }

    /**
     * 将本地Entity转换为Domain实体
     */
    fun AssetEntity.toDomain(): Asset {
        return Asset(
            id = this.id,
            name = this.name,
            assetType = this.assetType,
            status = this.status,
            statusDisplay = this.statusDisplay,
            location = this.location,
            ipAddress = this.ipAddress,
            model = null, // Entity中没有型号信息
            serialNumber = null, // Entity中没有序列号
            manufacturer = null, // Entity中没有制造商信息
            installDate = null, // Entity中没有安装日期
            warrantyExpiry = null, // Entity中没有保修期信息
            healthScore = this.healthScore,
            lastCheck = this.lastCheck,
            nextMaintenance = null, // Entity中没有下次维护时间
            description = null, // Entity中没有描述
            createdAt = this.createdAt,
            updatedAt = this.createdAt, // Entity中没有更新时间
            tags = this.tags,
            specifications = emptyMap(), // Entity中没有规格信息
            maintenanceRecords = emptyList(), // Entity中没有维护记录
            isOnline = determineOnlineStatus(this.status),
            isCritical = false, // Entity中没有关键标识
            lastSyncTime = this.lastSyncTime
        )
    }

    /**
     * 批量转换DTO列表为Domain列表
     */
    fun List<AssetDto>.toDomainList(): List<Asset> {
        return this.map { it.toDomain() }
    }

    /**
     * 批量转换Entity列表为Domain列表
     */
    fun List<AssetEntity>.toDomainListFromEntity(): List<Asset> {
        return this.map { it.toDomain() }
    }

    /**
     * 批量转换Domain列表为Entity列表
     */
    fun List<Asset>.toEntityList(): List<AssetEntity> {
        return this.map { it.toEntity() }
    }

    /**
     * 合并远程和本地资产数据
     * 优先使用远程数据，但保留本地的同步时间
     */
    fun mergeRemoteAndLocal(remote: Asset, local: AssetEntity?): Asset {
        return if (local != null) {
            remote.copy(lastSyncTime = System.currentTimeMillis())
        } else {
            remote.copy(lastSyncTime = System.currentTimeMillis())
        }
    }

    /**
     * 检查资产是否需要同步
     */
    fun Asset.needsSync(lastSyncThreshold: Long = 5 * 60 * 1000L): Boolean {
        // 资产数据更新频率较高，设置为5分钟
        return (System.currentTimeMillis() - this.lastSyncTime) > lastSyncThreshold
    }

    /**
     * 根据状态判断设备是否在线
     */
    private fun determineOnlineStatus(status: String): Boolean {
        return when (status.lowercase()) {
            "running", "online", "active", "normal" -> true
            "offline", "error", "failed", "disconnected" -> false
            else -> false // 对于unknown、pending等状态，默认认为离线
        }
    }

    /**
     * 从规格信息中提取特定字段
     */
    private fun AssetDetailDto.extractFromSpecifications(key: String): String? {
        return this.specifications[key]?.toString()
    }

    /**
     * 从维护信息中提取特定字段
     */
    private fun AssetDetailDto.extractFromMaintenanceInfo(key: String): String? {
        return this.maintenanceInfo[key]?.toString()
    }

    /**
     * 从规格信息中提取标签
     */
    private fun AssetDetailDto.extractTagsFromSpecifications(): List<String> {
        val tags = mutableListOf<String>()
        
        // 添加资产类型作为标签
        tags.add(this.assetType)
        
        // 添加优先级作为标签
        if (this.priority.isNotBlank()) {
            tags.add(this.priority)
        }
        
        // 从规格信息中提取可能的标签
        this.specifications["tags"]?.let { tagsValue ->
            when (tagsValue) {
                is List<*> -> {
                    tagsValue.mapNotNull { it?.toString() }.forEach { tag ->
                        if (tag.isNotBlank()) tags.add(tag)
                    }
                }
                is String -> {
                    tagsValue.split(",", ";").forEach { tag ->
                        val trimmedTag = tag.trim()
                        if (trimmedTag.isNotBlank()) tags.add(trimmedTag)
                    }
                }
            }
        }
        
        return tags.distinct()
    }

    /**
     * 创建维护记录映射（如果API返回维护记录数据）
     */
    fun mapMaintenanceRecord(data: Map<String, Any>): MaintenanceRecord? {
        return try {
            MaintenanceRecord(
                id = (data["id"] as? Number)?.toInt() ?: return null,
                assetId = (data["asset_id"] as? Number)?.toInt() ?: return null,
                type = data["type"]?.toString() ?: "",
                description = data["description"]?.toString() ?: "",
                performedBy = data["performed_by"]?.toString() ?: "",
                performedAt = data["performed_at"]?.toString() ?: "",
                cost = (data["cost"] as? Number)?.toDouble(),
                status = data["status"]?.toString() ?: "",
                notes = data["notes"]?.toString()
            )
        } catch (e: Exception) {
            null
        }
    }
}