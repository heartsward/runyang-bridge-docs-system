package com.runyang.bridge.maintenance.domain.repository

import com.runyang.bridge.maintenance.domain.entity.Document
import kotlinx.coroutines.flow.Flow

interface SearchRepository {
    suspend fun search(query: String): Flow<List<Document>>
    suspend fun saveSearchHistory(query: String)
    suspend fun getSearchHistory(): Flow<List<String>>
    suspend fun clearSearchHistory()
}