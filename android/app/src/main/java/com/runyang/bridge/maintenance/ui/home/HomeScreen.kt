package com.runyang.bridge.maintenance.ui.home

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
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.runyang.bridge.maintenance.ui.auth.AuthViewModel
import com.runyang.bridge.maintenance.ui.theme.RunYangBridgeMaintenanceTheme

/**
 * 主界面
 * 展示系统功能模块和快捷操作
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    onLogout: () -> Unit,
    authViewModel: AuthViewModel = hiltViewModel()
) {
    val authState by authViewModel.authState.collectAsState()
    
    // 功能模块数据
    val functionModules = remember {
        listOf(
            FunctionModule("文档管理", Icons.Filled.Description, Color(0xFF2196F3), "管理运维文档"),
            FunctionModule("设备资产", Icons.Filled.Hardware, Color(0xFF4CAF50), "查看设备信息"),
            FunctionModule("语音查询", Icons.Filled.Mic, Color(0xFFFF9800), "语音智能搜索"),
            FunctionModule("系统监控", Icons.Filled.Monitor, Color(0xFF9C27B0), "实时状态监控"),
            FunctionModule("报告生成", Icons.Filled.Assessment, Color(0xFFE91E63), "生成运维报告"),
            FunctionModule("用户管理", Icons.Filled.People, Color(0xFF607D8B), "管理用户权限")
        )
    }

    // 快捷统计数据
    val quickStats = remember {
        listOf(
            QuickStat("设备总数", "156", "台", Color(0xFF4CAF50)),
            QuickStat("文档数量", "2,341", "份", Color(0xFF2196F3)),
            QuickStat("今日查询", "87", "次", Color(0xFFFF9800)),
            QuickStat("在线用户", "23", "人", Color(0xFF9C27B0))
        )
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
    ) {
        // 顶部导航栏
        TopAppBar(
            title = {
                Column {
                    Text(
                        text = "润扬大桥运维系统",
                        style = MaterialTheme.typography.titleLarge.copy(
                            fontWeight = FontWeight.Bold
                        )
                    )
                    Text(
                        text = "欢迎回来，${authState.username.ifBlank { "管理员" }}",
                        style = MaterialTheme.typography.bodySmall.copy(
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    )
                }
            },
            actions = {
                IconButton(onClick = { /* TODO: 打开通知 */ }) {
                    Icon(
                        Icons.Filled.Notifications,
                        contentDescription = "通知"
                    )
                }
                IconButton(onClick = onLogout) {
                    Icon(
                        Icons.Filled.ExitToApp,
                        contentDescription = "退出登录"
                    )
                }
            },
            colors = TopAppBarDefaults.topAppBarColors(
                containerColor = MaterialTheme.colorScheme.surface,
                titleContentColor = MaterialTheme.colorScheme.onSurface
            )
        )

        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // 快捷统计卡片
            item {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp)
                    ) {
                        Text(
                            text = "系统概览",
                            style = MaterialTheme.typography.titleMedium.copy(
                                fontWeight = FontWeight.Bold
                            ),
                            modifier = Modifier.padding(bottom = 12.dp)
                        )
                        
                        LazyRow(
                            horizontalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            items(quickStats) { stat ->
                                QuickStatCard(stat = stat)
                            }
                        }
                    }
                }
            }

            // 功能模块标题
            item {
                Text(
                    text = "功能模块",
                    style = MaterialTheme.typography.titleMedium.copy(
                        fontWeight = FontWeight.Bold
                    ),
                    modifier = Modifier.padding(horizontal = 4.dp)
                )
            }

            // 功能模块网格
            items(functionModules.chunked(2)) { rowModules ->
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    rowModules.forEach { module ->
                        FunctionModuleCard(
                            module = module,
                            modifier = Modifier.weight(1f),
                            onClick = { /* TODO: 导航到对应功能 */ }
                        )
                    }
                    // 如果行中只有一个模块，添加占位符
                    if (rowModules.size == 1) {
                        Spacer(modifier = Modifier.weight(1f))
                    }
                }
            }

            // 底部占位
            item {
                Spacer(modifier = Modifier.height(32.dp))
            }
        }
    }
}

/**
 * 快捷统计卡片
 */
@Composable
fun QuickStatCard(
    stat: QuickStat,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.width(120.dp),
        colors = CardDefaults.cardColors(
            containerColor = stat.color.copy(alpha = 0.1f)
        ),
        shape = RoundedCornerShape(8.dp)
    ) {
        Column(
            modifier = Modifier.padding(12.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = stat.value,
                style = MaterialTheme.typography.headlineSmall.copy(
                    fontWeight = FontWeight.Bold,
                    color = stat.color
                )
            )
            Text(
                text = stat.unit,
                style = MaterialTheme.typography.bodySmall.copy(
                    color = stat.color
                ),
                fontSize = 10.sp
            )
            Text(
                text = stat.label,
                style = MaterialTheme.typography.bodySmall.copy(
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                ),
                fontSize = 11.sp,
                textAlign = TextAlign.Center
            )
        }
    }
}

/**
 * 功能模块卡片
 */
@Composable
fun FunctionModuleCard(
    module: FunctionModule,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier
            .height(120.dp)
            .clickable { onClick() },
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Box(
                modifier = Modifier
                    .size(48.dp)
                    .background(
                        module.color.copy(alpha = 0.15f),
                        CircleShape
                    ),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = module.icon,
                    contentDescription = module.name,
                    tint = module.color,
                    modifier = Modifier.size(24.dp)
                )
            }
            
            Spacer(modifier = Modifier.height(8.dp))
            
            Text(
                text = module.name,
                style = MaterialTheme.typography.titleSmall.copy(
                    fontWeight = FontWeight.Medium
                ),
                textAlign = TextAlign.Center,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )
            
            Text(
                text = module.description,
                style = MaterialTheme.typography.bodySmall.copy(
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                ),
                textAlign = TextAlign.Center,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                fontSize = 10.sp
            )
        }
    }
}

/**
 * 功能模块数据类
 */
data class FunctionModule(
    val name: String,
    val icon: ImageVector,
    val color: Color,
    val description: String
)

/**
 * 快捷统计数据类
 */
data class QuickStat(
    val label: String,
    val value: String,
    val unit: String,
    val color: Color
)

@Preview(showBackground = true)
@Composable
fun HomeScreenPreview() {
    RunYangBridgeMaintenanceTheme {
        HomeScreen(onLogout = {})
    }
}

@Preview(showBackground = true)
@Composable
fun FunctionModuleCardPreview() {
    RunYangBridgeMaintenanceTheme {
        FunctionModuleCard(
            module = FunctionModule("文档管理", Icons.Filled.Description, Color(0xFF2196F3), "管理运维文档"),
            onClick = {},
            modifier = Modifier.width(150.dp)
        )
    }
}

@Preview(showBackground = true)
@Composable
fun QuickStatCardPreview() {
    RunYangBridgeMaintenanceTheme {
        QuickStatCard(
            stat = QuickStat("设备总数", "156", "台", Color(0xFF4CAF50))
        )
    }
}