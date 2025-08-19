package com.runyang.bridge.maintenance.ui.document

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.paging.PagingData
import androidx.paging.cachedIn
import com.runyang.bridge.maintenance.data.remote.api.ApiService
import com.runyang.bridge.maintenance.domain.entity.Document
import com.runyang.bridge.maintenance.domain.entity.DocumentCategory
import com.runyang.bridge.maintenance.domain.entity.DocumentSortType
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.emptyFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * 文档管理ViewModel
 * 处理文档列表、搜索、下载等功能
 */
@HiltViewModel
class DocumentViewModel @Inject constructor(
    private val apiService: ApiService
) : ViewModel() {

    private val _uiState = MutableStateFlow(DocumentUiState())
    val uiState: StateFlow<DocumentUiState> = _uiState.asStateFlow()

    private val _searchQuery = MutableStateFlow("")
    val searchQuery: StateFlow<String> = _searchQuery.asStateFlow()

    private val _selectedCategory = MutableStateFlow<DocumentCategory?>(null)
    val selectedCategory: StateFlow<DocumentCategory?> = _selectedCategory.asStateFlow()

    private val _sortType = MutableStateFlow(DocumentSortType.CREATE_TIME_DESC)
    val sortType: StateFlow<DocumentSortType> = _sortType.asStateFlow()

    // 分页数据流
    private var _documentsPagingFlow: Flow<PagingData<Document>> = emptyFlow()
    val documentsPagingFlow: Flow<PagingData<Document>>
        get() = _documentsPagingFlow.cachedIn(viewModelScope)

    init {
        // 初始化加载文档列表
        loadDocuments()
    }

    /**
     * 加载文档列表
     */
    fun loadDocuments() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            
            try {
                // TODO: 实现分页数据源
                // _documentsPagingFlow = documentRepository.getDocumentsPaging(
                //     category = _selectedCategory.value?.value,
                //     searchQuery = _searchQuery.value,
                //     sortType = _sortType.value
                // ).cachedIn(viewModelScope)
                
                _uiState.value = _uiState.value.copy(isLoading = false)
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = e.message ?: "加载文档失败"
                )
            }
        }
    }

    /**
     * 搜索文档
     */
    fun searchDocuments(query: String) {
        _searchQuery.value = query
        loadDocuments()
    }

    /**
     * 设置分类筛选
     */
    fun setCategory(category: DocumentCategory?) {
        _selectedCategory.value = category
        loadDocuments()
    }

    /**
     * 设置排序方式
     */
    fun setSortType(sortType: DocumentSortType) {
        _sortType.value = sortType
        loadDocuments()
    }

    /**
     * 清除搜索
     */
    fun clearSearch() {
        _searchQuery.value = ""
        loadDocuments()
    }

    /**
     * 下载文档
     */
    fun downloadDocument(document: Document) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(downloadingDocumentId = document.id)
            
            try {
                // TODO: 实现文档下载逻辑
                // val result = documentRepository.downloadDocument(document)
                // if (result.isSuccess) {
                //     _uiState.value = _uiState.value.copy(
                //         downloadingDocumentId = null,
                //         message = "文档下载成功"
                //     )
                // } else {
                //     _uiState.value = _uiState.value.copy(
                //         downloadingDocumentId = null,
                //         error = result.exceptionOrNull()?.message ?: "下载失败"
                //     )
                // }
                
                // 模拟下载延迟
                kotlinx.coroutines.delay(2000)
                _uiState.value = _uiState.value.copy(
                    downloadingDocumentId = null,
                    message = "文档下载成功"
                )
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    downloadingDocumentId = null,
                    error = e.message ?: "下载失败"
                )
            }
        }
    }

    /**
     * 收藏/取消收藏文档
     */
    fun toggleFavorite(document: Document) {
        viewModelScope.launch {
            try {
                // TODO: 实现收藏功能
                // documentRepository.toggleFavorite(document.id, !document.isFavorite)
                _uiState.value = _uiState.value.copy(
                    message = if (document.isFavorite) "已取消收藏" else "已添加收藏"
                )
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    error = e.message ?: "操作失败"
                )
            }
        }
    }

    /**
     * 预览文档
     */
    fun previewDocument(document: Document) {
        viewModelScope.launch {
            if (!document.isPreviewSupported) {
                _uiState.value = _uiState.value.copy(
                    error = "该文件类型不支持预览"
                )
                return@launch
            }

            _uiState.value = _uiState.value.copy(previewingDocument = document)
            
            try {
                // TODO: 实现文档预览逻辑
                // 可能需要获取预览URL或下载文档内容
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    previewingDocument = null,
                    error = e.message ?: "预览失败"
                )
            }
        }
    }

    /**
     * 关闭预览
     */
    fun closePreview() {
        _uiState.value = _uiState.value.copy(previewingDocument = null)
    }

    /**
     * 刷新文档列表
     */
    fun refresh() {
        loadDocuments()
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
     * 获取所有分类
     */
    fun getAllCategories(): List<DocumentCategory> {
        return DocumentCategory.getAllCategories()
    }

    /**
     * 获取所有排序选项
     */
    fun getAllSortTypes(): List<DocumentSortType> {
        return DocumentSortType.values().toList()
    }
}

/**
 * 文档UI状态
 */
data class DocumentUiState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val message: String? = null,
    val downloadingDocumentId: Int? = null,
    val previewingDocument: Document? = null,
    val isEmpty: Boolean = false
)