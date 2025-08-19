package com.runyang.bridge.maintenance.ui.document

import androidx.compose.foundation.background
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
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.runyang.bridge.maintenance.domain.entity.Document
import com.runyang.bridge.maintenance.ui.theme.RunYangBridgeMaintenanceTheme
import kotlinx.coroutines.delay

/**
 * 文档详情界面
 * 显示文档的详细信息，支持预览、下载、收藏等操作
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DocumentDetailScreen(
    documentId: Int,
    onNavigateBack: () -> Unit,
    onPreviewDocument: (Document) -> Unit,
    viewModel: DocumentViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    
    // 模拟文档数据（实际应该从ViewModel根据ID获取）
    val document = remember {
        Document(
            id = documentId,
            title = "润扬大桥主缆维护手册",
            summary = "详细描述主缆的日常维护、检查要点和注意事项，包含安全操作规程和应急处理措施。本手册涵盖了主缆结构特点、维护周期、检查方法、常见问题处理等内容，是桥梁维护人员的重要参考资料。",
            fileType = "pdf",
            fileSize = 2048576,
            fileSizeDisplay = "2.0 MB",
            createdAt = "2024-01-15T10:30:00Z",
            updatedAt = "2024-01-15T10:30:00Z",
            category = "maintenance",
            tags = listOf("主缆", "维护", "安全", "检查", "规程"),
            downloadUrl = "https://example.com/doc1.pdf",
            previewUrl = null,
            isFavorite = false,
            isDownloaded = false
        )
    }

    var isDownloading by remember { mutableStateOf(false) }
    var downloadProgress by remember { mutableStateOf(0f) }
    var showDownloadDialog by remember { mutableStateOf(false) }

    // 模拟下载进度
    LaunchedEffect(isDownloading) {
        if (isDownloading) {
            for (i in 0..100 step 5) {
                downloadProgress = i / 100f
                delay(100)
            }
            isDownloading = false
            downloadProgress = 0f
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
                    text = "文档详情",
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
                // 分享按钮
                IconButton(onClick = { /* TODO: 实现分享功能 */ }) {
                    Icon(
                        imageVector = Icons.Filled.Share,
                        contentDescription = "分享"
                    )
                }
                // 更多操作
                IconButton(onClick = { /* TODO: 显示更多菜单 */ }) {
                    Icon(
                        imageVector = Icons.Filled.MoreVert,
                        contentDescription = "更多"
                    )
                }
            },
            colors = TopAppBarDefaults.topAppBarColors(
                containerColor = MaterialTheme.colorScheme.surface
            )
        )

        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // 文档标题和基本信息
            item {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Column(
                        modifier = Modifier.padding(20.dp)
                    ) {
                        // 标题
                        Text(
                            text = document.title,
                            style = MaterialTheme.typography.headlineSmall.copy(
                                fontWeight = FontWeight.Bold
                            ),
                            color = MaterialTheme.colorScheme.onSurface
                        )

                        Spacer(modifier = Modifier.height(12.dp))

                        // 文件类型和大小
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
                                modifier = Modifier.size(20.dp),
                                tint = MaterialTheme.colorScheme.primary
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = "${document.fileType.uppercase()} • ${document.fileSizeDisplay}",
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            Spacer(modifier = Modifier.weight(1f))
                            
                            // 状态标签
                            Surface(
                                shape = RoundedCornerShape(12.dp),
                                color = if (document.isDownloaded) {
                                    MaterialTheme.colorScheme.primaryContainer
                                } else {
                                    MaterialTheme.colorScheme.surfaceVariant
                                }
                            ) {
                                Text(
                                    text = document.getStatusDescription(),
                                    style = MaterialTheme.typography.bodySmall,
                                    color = if (document.isDownloaded) {
                                        MaterialTheme.colorScheme.onPrimaryContainer
                                    } else {
                                        MaterialTheme.colorScheme.onSurfaceVariant
                                    },
                                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                                )
                            }
                        }

                        Spacer(modifier = Modifier.height(16.dp))

                        // 创建和更新时间
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Column {
                                Text(
                                    text = "创建时间",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                                Text(
                                    text = "2024-01-15 10:30",
                                    style = MaterialTheme.typography.bodyMedium
                                )
                            }
                            Column {
                                Text(
                                    text = "更新时间",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                                Text(
                                    text = "2024-01-15 10:30",
                                    style = MaterialTheme.typography.bodyMedium
                                )
                            }
                        }
                    }
                }
            }

            // 操作按钮
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    // 预览按钮
                    if (document.isPreviewSupported) {
                        OutlinedButton(
                            onClick = { onPreviewDocument(document) },
                            modifier = Modifier.weight(1f),
                            shape = RoundedCornerShape(8.dp)
                        ) {
                            Icon(
                                imageVector = Icons.Filled.Visibility,
                                contentDescription = null,
                                modifier = Modifier.size(18.dp)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("预览")
                        }
                    }

                    // 下载按钮
                    Button(
                        onClick = { 
                            if (!document.isDownloaded) {
                                isDownloading = true
                            }
                        },
                        enabled = !isDownloading,
                        modifier = Modifier.weight(1f),
                        shape = RoundedCornerShape(8.dp)
                    ) {
                        if (isDownloading) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(18.dp),
                                strokeWidth = 2.dp,
                                color = MaterialTheme.colorScheme.onPrimary
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("下载中...")
                        } else {
                            Icon(
                                imageVector = if (document.isDownloaded) {
                                    Icons.Filled.CloudDone
                                } else {
                                    Icons.Filled.CloudDownload
                                },
                                contentDescription = null,
                                modifier = Modifier.size(18.dp)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(if (document.isDownloaded) "已下载" else "下载")
                        }
                    }

                    // 收藏按钮
                    IconButton(
                        onClick = { viewModel.toggleFavorite(document) },
                        modifier = Modifier
                            .background(
                                if (document.isFavorite) {
                                    MaterialTheme.colorScheme.primaryContainer
                                } else {
                                    MaterialTheme.colorScheme.surfaceVariant
                                },
                                CircleShape
                            )
                            .size(48.dp)
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
                            }
                        )
                    }
                }
            }

            // 下载进度
            if (isDownloading) {
                item {
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        colors = CardDefaults.cardColors(
                            containerColor = MaterialTheme.colorScheme.primaryContainer
                        )
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
                                    text = "正在下载...",
                                    style = MaterialTheme.typography.bodyMedium,
                                    fontWeight = FontWeight.Medium
                                )
                                Text(
                                    text = "${(downloadProgress * 100).toInt()}%",
                                    style = MaterialTheme.typography.bodyMedium
                                )
                            }
                            Spacer(modifier = Modifier.height(8.dp))
                            LinearProgressIndicator(
                                progress = downloadProgress,
                                modifier = Modifier.fillMaxWidth()
                            )
                        }
                    }
                }
            }

            // 文档摘要
            item {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Column(
                        modifier = Modifier.padding(20.dp)
                    ) {
                        Text(
                            text = "文档摘要",
                            style = MaterialTheme.typography.titleMedium.copy(
                                fontWeight = FontWeight.Bold
                            )
                        )
                        Spacer(modifier = Modifier.height(12.dp))
                        Text(
                            text = document.summary,
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            lineHeight = 20.sp
                        )
                    }
                }
            }

            // 标签
            if (document.tags.isNotEmpty()) {
                item {
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Column(
                            modifier = Modifier.padding(20.dp)
                        ) {
                            Text(
                                text = "相关标签",
                                style = MaterialTheme.typography.titleMedium.copy(
                                    fontWeight = FontWeight.Bold
                                )
                            )
                            Spacer(modifier = Modifier.height(12.dp))
                            LazyRow(
                                horizontalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                items(document.tags) { tag ->
                                    TagChip(tag = tag)
                                }
                            }
                        }
                    }
                }
            }

            // 相关操作
            item {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Column(
                        modifier = Modifier.padding(20.dp)
                    ) {
                        Text(
                            text = "更多操作",
                            style = MaterialTheme.typography.titleMedium.copy(
                                fontWeight = FontWeight.Bold
                            )
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        
                        // 操作项列表
                        ActionItem(
                            icon = Icons.Filled.History,
                            title = "查看历史版本",
                            subtitle = "查看文档的版本历史记录",
                            onClick = { /* TODO: 实现历史版本功能 */ }
                        )
                        
                        Divider(modifier = Modifier.padding(vertical = 12.dp))
                        
                        ActionItem(
                            icon = Icons.Filled.Comment,
                            title = "添加批注",
                            subtitle = "为文档添加个人批注",
                            onClick = { /* TODO: 实现批注功能 */ }
                        )
                        
                        Divider(modifier = Modifier.padding(vertical = 12.dp))
                        
                        ActionItem(
                            icon = Icons.Filled.Report,
                            title = "报告问题",
                            subtitle = "反馈文档相关问题",
                            onClick = { /* TODO: 实现问题反馈功能 */ }
                        )
                    }
                }
            }

            // 底部占位
            item {
                Spacer(modifier = Modifier.height(32.dp))
            }
        }
    }

    // 下载确认对话框
    if (showDownloadDialog) {
        AlertDialog(
            onDismissRequest = { showDownloadDialog = false },
            title = { Text("确认下载") },
            text = { Text("确定要下载这个文档吗？文件大小：${document.fileSizeDisplay}") },
            confirmButton = {
                TextButton(
                    onClick = {
                        showDownloadDialog = false
                        isDownloading = true
                    }
                ) {
                    Text("确定")
                }
            },
            dismissButton = {
                TextButton(onClick = { showDownloadDialog = false }) {
                    Text("取消")
                }
            }
        )
    }
}

/**
 * 操作项组件
 */
@Composable
fun ActionItem(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    title: String,
    subtitle: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .clickable { onClick() }
            .padding(vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Icon(
            imageVector = icon,
            contentDescription = null,
            modifier = Modifier.size(24.dp),
            tint = MaterialTheme.colorScheme.primary
        )
        Spacer(modifier = Modifier.width(16.dp))
        Column(
            modifier = Modifier.weight(1f)
        ) {
            Text(
                text = title,
                style = MaterialTheme.typography.titleSmall,
                color = MaterialTheme.colorScheme.onSurface
            )
            Text(
                text = subtitle,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
        Icon(
            imageVector = Icons.Filled.ChevronRight,
            contentDescription = null,
            modifier = Modifier.size(20.dp),
            tint = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

@Preview(showBackground = true)
@Composable
fun DocumentDetailScreenPreview() {
    RunYangBridgeMaintenanceTheme {
        DocumentDetailScreen(
            documentId = 1,
            onNavigateBack = {},
            onPreviewDocument = {}
        )
    }
}