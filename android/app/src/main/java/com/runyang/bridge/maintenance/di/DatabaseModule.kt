package com.runyang.bridge.maintenance.di

import android.content.Context
import androidx.room.Room
import com.runyang.bridge.maintenance.data.local.database.AppDatabase
import com.runyang.bridge.maintenance.data.local.dao.AssetDao
import com.runyang.bridge.maintenance.data.local.dao.DocumentDao
import com.runyang.bridge.maintenance.data.local.dao.SearchHistoryDao
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

/**
 * 数据库模块 - 提供Room数据库相关依赖
 */
@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    /**
     * 提供Room数据库实例
     */
    @Provides
    @Singleton
    fun provideAppDatabase(@ApplicationContext context: Context): AppDatabase {
        return Room.databaseBuilder(
            context.applicationContext,
            AppDatabase::class.java,
            "runyang_bridge_database"
        )
            .fallbackToDestructiveMigration() // 开发阶段使用，生产环境需要实现Migration
            .build()
    }

    /**
     * 提供文档DAO
     */
    @Provides
    fun provideDocumentDao(database: AppDatabase): DocumentDao = 
        database.documentDao()

    /**
     * 提供资产DAO
     */
    @Provides
    fun provideAssetDao(database: AppDatabase): AssetDao = 
        database.assetDao()

    /**
     * 提供搜索历史DAO
     */
    @Provides
    fun provideSearchHistoryDao(database: AppDatabase): SearchHistoryDao = 
        database.searchHistoryDao()
}