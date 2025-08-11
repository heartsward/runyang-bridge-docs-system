package com.runyang.bridge.maintenance.data.local.database

import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.TypeConverters
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase
import com.runyang.bridge.maintenance.data.local.converter.Converters
import com.runyang.bridge.maintenance.data.local.dao.AssetDao
import com.runyang.bridge.maintenance.data.local.dao.DocumentDao
import com.runyang.bridge.maintenance.data.local.dao.SearchHistoryDao
import com.runyang.bridge.maintenance.data.local.entity.AssetEntity
import com.runyang.bridge.maintenance.data.local.entity.CacheMetadataEntity
import com.runyang.bridge.maintenance.data.local.entity.DocumentEntity
import com.runyang.bridge.maintenance.data.local.entity.DownloadTaskEntity
import com.runyang.bridge.maintenance.data.local.entity.SearchHistoryEntity

/**
 * 应用数据库主类
 * 使用Room数据库框架
 */
@Database(
    entities = [
        DocumentEntity::class,
        AssetEntity::class,
        SearchHistoryEntity::class,
        CacheMetadataEntity::class,
        DownloadTaskEntity::class
    ],
    version = DATABASE_VERSION,
    exportSchema = true,
    autoMigrations = [
        // 这里可以定义自动迁移规则
    ]
)
@TypeConverters(Converters::class)
abstract class AppDatabase : RoomDatabase() {

    abstract fun documentDao(): DocumentDao
    abstract fun assetDao(): AssetDao
    abstract fun searchHistoryDao(): SearchHistoryDao

    companion object {
        const val DATABASE_NAME = "runyang_bridge_database"
        const val DATABASE_VERSION = 1

        /**
         * 数据库创建回调
         */
        val CREATE_CALLBACK = object : Callback() {
            override fun onCreate(db: SupportSQLiteDatabase) {
                super.onCreate(db)
                // 在这里可以插入初始数据
                // 例如默认的资产类型、文档分类等
            }

            override fun onOpen(db: SupportSQLiteDatabase) {
                super.onOpen(db)
                // 数据库每次打开时的回调
                // 可以进行一些清理工作
            }
        }

        /**
         * 数据库迁移规则
         * 从版本1到版本2的迁移示例
         */
        val MIGRATION_1_2 = object : Migration(1, 2) {
            override fun migrate(database: SupportSQLiteDatabase) {
                // 添加新列的示例
                // database.execSQL("ALTER TABLE documents ADD COLUMN new_column TEXT")
            }
        }

        /**
         * 获取数据库构建器
         */
        fun getDatabaseBuilder(
            context: android.content.Context,
            databaseName: String = DATABASE_NAME
        ): Builder<AppDatabase> {
            return Room.databaseBuilder(
                context.applicationContext,
                AppDatabase::class.java,
                databaseName
            )
                .addCallback(CREATE_CALLBACK)
                .addMigrations(
                    // MIGRATION_1_2 // 添加迁移规则
                )
                // 在调试模式下允许主线程查询（不推荐在生产环境使用）
                .apply {
                    if (com.runyang.bridge.maintenance.BuildConfig.DEBUG_MODE) {
                        // allowMainThreadQueries() // 仅用于调试
                    }
                }
                // 启用WAL模式以提高并发性能
                .setJournalMode(JournalMode.WAL)
                // 设置查询执行器
                .setQueryExecutor { command ->
                    // 可以自定义查询执行器
                    command.run()
                }
        }
    }

    /**
     * 清理数据库
     * 删除过期数据和缓存
     */
    suspend fun cleanup() {
        val currentTime = System.currentTimeMillis()
        val oneWeekAgo = currentTime - (7 * 24 * 60 * 60 * 1000) // 一周前
        val oneMonthAgo = currentTime - (30 * 24 * 60 * 60 * 1000) // 一个月前

        runInTransaction {
            // 清理过期的搜索历史（保留一个月）
            searchHistoryDao().deleteExpiredSearchHistory(oneMonthAgo)
            
            // 清理过期的缓存元数据
            searchHistoryDao().deleteExpiredCacheMetadata(currentTime)
            
            // 清理LRU缓存（保留最近使用的1000个）
            searchHistoryDao().cleanupLRUCache(1000)
            
            // 清理已完成的下载任务（保留一周）
            if (oneWeekAgo > 0) {
                // 可以添加基于时间的清理逻辑
            }
        }
    }

    /**
     * 获取数据库统计信息
     */
    suspend fun getDatabaseStats(): DatabaseStats {
        return DatabaseStats(
            documentCount = documentDao().getDocumentCount(),
            assetCount = assetDao().getAssetCount(),
            searchHistoryCount = searchHistoryDao().getAllSearchHistoryFlow().let { 0 }, // 需要实现计数查询
            cacheSize = searchHistoryDao().getAllCacheMetadata().size,
            downloadTaskCount = searchHistoryDao().getAllDownloadTasksFlow().let { 0 } // 需要实现计数查询
        )
    }

    /**
     * 数据库完整性检查
     */
    suspend fun checkIntegrity(): DatabaseIntegrityResult {
        return try {
            // 执行PRAGMA integrity_check
            val result = query("PRAGMA integrity_check", null)
            result.use { cursor ->
                if (cursor.moveToFirst()) {
                    val integrityResult = cursor.getString(0)
                    DatabaseIntegrityResult(
                        isHealthy = integrityResult == "ok",
                        message = integrityResult
                    )
                } else {
                    DatabaseIntegrityResult(false, "无法检查数据库完整性")
                }
            }
        } catch (e: Exception) {
            DatabaseIntegrityResult(false, "数据库完整性检查失败: ${e.message}")
        }
    }
}

/**
 * 数据库统计信息
 */
data class DatabaseStats(
    val documentCount: Int,
    val assetCount: Int,
    val searchHistoryCount: Int,
    val cacheSize: Int,
    val downloadTaskCount: Int
)

/**
 * 数据库完整性检查结果
 */
data class DatabaseIntegrityResult(
    val isHealthy: Boolean,
    val message: String
)