package com.runyang.bridge.maintenance.di

import com.runyang.bridge.maintenance.data.local.datastore.SettingsDataStore
import com.runyang.bridge.maintenance.data.local.datastore.TokenDataStore
import com.runyang.bridge.maintenance.data.repository.AssetRepositoryImpl
import com.runyang.bridge.maintenance.data.repository.AuthRepositoryImpl
import com.runyang.bridge.maintenance.data.repository.DocumentRepositoryImpl
import com.runyang.bridge.maintenance.data.repository.SearchRepositoryImpl
import com.runyang.bridge.maintenance.data.repository.SettingsRepositoryImpl
import com.runyang.bridge.maintenance.domain.repository.AssetRepository
import com.runyang.bridge.maintenance.domain.repository.AuthRepository
import com.runyang.bridge.maintenance.domain.repository.DocumentRepository
import com.runyang.bridge.maintenance.domain.repository.SearchRepository
import com.runyang.bridge.maintenance.domain.repository.SettingsRepository
import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

/**
 * 数据模块 - 绑定Repository实现
 */
@Module
@InstallIn(SingletonComponent::class)
abstract class DataModule {

    @Binds
    @Singleton
    abstract fun bindAuthRepository(
        authRepositoryImpl: AuthRepositoryImpl
    ): AuthRepository

    @Binds
    @Singleton
    abstract fun bindDocumentRepository(
        documentRepositoryImpl: DocumentRepositoryImpl
    ): DocumentRepository

    @Binds
    @Singleton
    abstract fun bindAssetRepository(
        assetRepositoryImpl: AssetRepositoryImpl
    ): AssetRepository

    @Binds
    @Singleton
    abstract fun bindSearchRepository(
        searchRepositoryImpl: SearchRepositoryImpl
    ): SearchRepository

    @Binds
    @Singleton
    abstract fun bindSettingsRepository(
        settingsRepositoryImpl: SettingsRepositoryImpl
    ): SettingsRepository
}

/**
 * DataStore模块 - 提供DataStore相关依赖
 */
@Module
@InstallIn(SingletonComponent::class)
object DataStoreModule {

    // TokenDataStore和SettingsDataStore将在它们的类中使用@Singleton注解
    // 这里不需要额外的提供方法，Hilt会自动处理
}