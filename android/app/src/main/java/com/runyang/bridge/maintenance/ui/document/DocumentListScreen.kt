package com.runyang.bridge.maintenance.ui.document

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
import com.runyang.bridge.maintenance.domain.entity.Document
import com.runyang.bridge.maintenance.domain.entity.DocumentCategory
import com.runyang.bridge.maintenance.domain.entity.DocumentSortType
import com.runyang.bridge.maintenance.ui.theme.RunYangBridgeMaintenanceTheme

/**
 * 文档列表界面
 * 支持搜索、筛选、排序和文档操作
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DocumentListScreen(
    onDocumentClick: (Document) -> Unit,
    onNavigateBack: () -> Unit,
    viewModel: DocumentViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    val searchQuery by viewModel.searchQuery.collectAsState()
    val selectedCategory by viewModel.selectedCategory.collectAsState()
    val sortType by viewModel.sortType.collectAsState()
    val focusManager = LocalFocusManager.current

    var showCategoryFilter by remember { mutableStateOf(false) }
    var showSortOptions by remember { mutableStateOf(false) }

    // 模拟文档数据（实际应该从ViewModel获取）
    val sampleDocuments = remember {
        listOf(
            Document(
                id = 1,
                title = "润扬大桥主缆维护手册",
                summary = "详细描述主缆的日常维护、检查要点和注意事项，包含安全操作规程和应急处理措施。",
                fileType = "pdf",
                fileSize = 2048576,
                fileSizeDisplay = "2.0 MB",
                createdAt = "2024-01-15T10:30:00Z",
                updatedAt = "2024-01-15T10:30:00Z",
                category = "maintenance",
                tags = listOf("主缆", "维护", "安全"),
                downloadUrl = "https://example.com/doc1.pdf",
                previewUrl = null
            ),
            Document(
                id = 2,
                title = "桥梁结构健康监测系统操作指南",
                summary = "监测系统的使用方法、数据分析技巧和故障排除指南。",
                fileType = "docx",
                fileSize = 1024000,
                fileSizeDisplay = "1.0 MB",
                createdAt = "2024-01-14T14:20:00Z",
                updatedAt = "2024-01-14T14:20:00Z",
                category = "technical",
                tags = listOf("监测", "系统", "操作"),
                downloadUrl = "https://example.com/doc2.docx",
                previewUrl = null,
                isDownloaded = true
            ),
            Document(
                id = 3,
                title = "应急预案处置流程",
                summary = "各类突发事件的应急处置流程和联系方式。",
                fileType = "pdf",
                fileSize = 512000,
                fileSizeDisplay = "512 KB",
                createdAt = "2024-01-13T09:15:00Z",
                updatedAt = "2024-01-13T09:15:00Z",
                category = "safety",
                tags = listOf("应急", "安全", "流程"),
                downloadUrl = "https://example.com/doc3.pdf",
                previewUrl = null,
                isFavorite = true
            )
        )
    }

    // 错误和消息处理
    LaunchedEffect(uiState.error) {
        uiState.error?.let {
            // 显示错误Toast或Snackbar
            viewModel.clearError()
        }
    }

    LaunchedEffect(uiState.message) {
        uiState.message?.let {
            // 显示成功Toast或Snackbar
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
                    text = "文档管理",
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
                // 排序按钮
                IconButton(onClick = { showSortOptions = true }) {
                    Icon(
                        imageVector = Icons.Filled.Sort,
                        contentDescription = "排序"
                    )
                }
                // 筛选按钮
                IconButton(onClick = { showCategoryFilter = true }) {
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
                onValueChange = viewModel::searchDocuments,
                placeholder = { 
                    Text("搜索文档标题、内容或标签...")
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

            // 分类筛选标签
            if (selectedCategory != null) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "筛选：",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    FilterChip(
                        onClick = { viewModel.setCategory(null) },
                        label = { Text(selectedCategory!!.displayName) },
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
            }

            // 文档列表
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
            } else if (sampleDocuments.isEmpty()) {
                // 空状态
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Icon(
                            imageVector = Icons.Filled.Description,
                            contentDescription = null,
                            modifier = Modifier.size(64.dp),
                            tint = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        Text(
                            text = "暂无文档",
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
                    items(sampleDocuments) { document ->
                        DocumentCard(
                            document = document,
                            onDocumentClick = onDocumentClick,
                            onDownloadClick = { viewModel.downloadDocument(it) },
                            onFavoriteClick = { viewModel.toggleFavorite(it) },
                            onPreviewClick = { viewModel.previewDocument(it) },
                            isDownloading = uiState.downloadingDocumentId == document.id
                        )
                    }
                }
            }
        }
    }

    // 分类筛选对话框
    if (showCategoryFilter) {
        CategoryFilterDialog(
            categories = viewModel.getAllCategories(),
            selectedCategory = selectedCategory,
            onCategorySelected = { category ->
                viewModel.setCategory(category)
                showCategoryFilter = false
            },
            onDismiss = { showCategoryFilter = false }
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
 * 文档卡片组件
 */
@Composable
fun DocumentCard(
    document: Document,
    onDocumentClick: (Document) -> Unit,
    onDownloadClick: (Document) -> Unit,
    onFavoriteClick: (Document) -> Unit,
    onPreviewClick: (Document) -> Unit,
    isDownloading: Boolean = false,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier
            .fillMaxWidth()
            .clickable { onDocumentClick(document) },
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            // 标题和收藏按钮
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top
            ) {
                Text(
                    text = document.title,
                    style = MaterialTheme.typography.titleMedium.copy(
                        fontWeight = FontWeight.Medium
                    ),
                    modifier = Modifier.weight(1f),
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis
                )
                
                IconButton(
                    onClick = { onFavoriteClick(document) },
                    modifier = Modifier.size(24.dp)
                ) {
                    Icon(
                        imageVector = if (document.isFavorite) {
                            Icons.Filled.Favorite
                        } else {
                            Icons.Filled.FavoriteBorder
                        },
                        contentDescription = if (document.isFavorite) "取消收藏" else "添加收藏",
                        tint = if (document.isFavorite) {
                            Color.Red
                        } else {
                            MaterialTheme.colorScheme.onSurfaceVariant
                        },
                        modifier = Modifier.size(20.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // 摘要
            Text(
                text = document.summary,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis
            )

            Spacer(modifier = Modifier.height(12.dp))

            // 标签
            if (document.tags.isNotEmpty()) {
                LazyRow(
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    items(document.tags.take(3)) { tag ->
                        TagChip(tag = tag)
                    }
                    if (document.tags.size > 3) {
                        item {
                            TagChip(tag = "+${document.tags.size - 3}")
                        }
                    }
                }
                
                Spacer(modifier = Modifier.height(12.dp))
            }

            // 底部信息和操作按钮
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                // 文件信息
                Column {
                    Row(
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            imageVector = when (document.fileExtension) {
                                "pdf" -> Icons.Filled.PictureAsPdf
                                "doc", "docx" -> Icons.Filled.Description
                                else -> Icons.Filled.InsertDriveFile
                            },
                            contentDescription = null,
                            modifier = Modifier.size(16.dp),
                            tint = MaterialTheme.colorScheme.primary
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text(
                            text = document.fileType.uppercase(),
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.primary
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = document.fileSizeDisplay,
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                    
                    Text(
                        text = document.getStatusDescription(),
                        style = MaterialTheme.typography.bodySmall,
                        color = if (document.isDownloaded) {
                            MaterialTheme.colorScheme.primary
                        } else {
                            MaterialTheme.colorScheme.onSurfaceVariant
                        }
                    )
                }

                // 操作按钮
                Row(
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    // 预览按钮
                    if (document.isPreviewSupported) {
                        IconButton(
                            onClick = { onPreviewClick(document) },
                            modifier = Modifier.size(32.dp)
                        ) {
                            Icon(
                                imageVector = Icons.Filled.Visibility,
                                contentDescription = "预览",
                                modifier = Modifier.size(20.dp)
                            )
                        }
                    }

                    // 下载按钮
                    IconButton(
                        onClick = { onDownloadClick(document) },
                        enabled = !isDownloading,
                        modifier = Modifier.size(32.dp)
                    ) {
                        if (isDownloading) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(16.dp),
                                strokeWidth = 2.dp
                            )
                        } else {
                            Icon(
                                imageVector = if (document.isDownloaded) {
                                    Icons.Filled.CloudDone
                                } else {
                                    Icons.Filled.CloudDownload
                                },
                                contentDescription = if (document.isDownloaded) "已下载" else "下载",
                                modifier = Modifier.size(20.dp),
                                tint = if (document.isDownloaded) {
                                    MaterialTheme.colorScheme.primary
                                } else {
                                    MaterialTheme.colorScheme.onSurfaceVariant
                                }
                            )
                        }
                    }
                }
            }
        }
    }
}

/**
 * 标签芯片组件
 */
@Composable
fun TagChip(
    tag: String,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(16.dp),
        color = MaterialTheme.colorScheme.surfaceVariant
    ) {
        Text(
            text = tag,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
        )
    }
}

/**
 * 分类筛选对话框
 */
@Composable
fun CategoryFilterDialog(
    categories: List<DocumentCategory>,
    selectedCategory: DocumentCategory?,
    onCategorySelected: (DocumentCategory?) -> Unit,
    onDismiss: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("选择文档分类") },
        text = {
            LazyColumn {
                item {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { onCategorySelected(null) }
                            .padding(vertical = 12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        RadioButton(
                            selected = selectedCategory == null,
                            onClick = { onCategorySelected(null) }
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("全部分类")
                    }
                }
                
                items(categories) { category ->
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { onCategorySelected(category) }
                            .padding(vertical = 12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        RadioButton(
                            selected = selectedCategory == category,
                            onClick = { onCategorySelected(category) }
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(category.displayName)
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
    sortTypes: List<DocumentSortType>,
    selectedSortType: DocumentSortType,
    onSortTypeSelected: (DocumentSortType) -> Unit,
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

@Preview(showBackground = true)
@Composable
fun DocumentListScreenPreview() {
    RunYangBridgeMaintenanceTheme {
        DocumentListScreen(
            onDocumentClick = {},
            onNavigateBack = {}
        )
    }
}