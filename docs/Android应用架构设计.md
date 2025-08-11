# 润扬大桥运维文档管理系统 - Android应用架构设计

## 1. 项目概述

### 1.1 应用简介
基于Kotlin开发的Android客户端，为润扬大桥运维人员提供移动端文档管理和设备资产查询功能，支持语音查询和离线访问能力。

### 1.2 核心功能
- 用户认证与权限管理
- 服务器配置与连接管理
- 文档浏览、搜索和下载
- 设备资产状态查询和监控
- 语音查询与智能搜索
- 离线数据缓存
- 消息推送与通知

### 1.3 技术栈
- **开发语言**: Kotlin
- **架构模式**: MVVM + Clean Architecture
- **UI框架**: Jetpack Compose
- **网络请求**: Retrofit2 + OkHttp3
- **数据存储**: Room Database + DataStore
- **依赖注入**: Hilt
- **异步处理**: Coroutines + Flow
- **图片加载**: Coil
- **导航**: Navigation Compose
- **测试框架**: JUnit4/5 + Mockk

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        UI Layer                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐  │
│  │  Compose UI     │  │   Fragments     │  │   Activities  │  │
│  └─────────────────┘  └─────────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                      Presentation Layer                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐  │
│  │   ViewModels    │  │   UI States     │  │   UI Events   │  │
│  └─────────────────┘  └─────────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                       Domain Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐  │
│  │   Use Cases     │  │    Entities     │  │  Repositories │  │
│  └─────────────────┘  └─────────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                        Data Layer                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐  │
│  │   Repository    │  │   Data Sources  │  │   Database    │  │
│  │ Implementations │  │  (Remote/Local) │  │   (Room)      │  │
│  └─────────────────┘  └─────────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 模块划分

#### 2.2.1 核心模块结构
```
app/
├── src/main/java/com/runyang/bridge/maintenance/
│   ├── di/                    # 依赖注入模块
│   ├── ui/                    # UI层
│   │   ├── theme/            # 主题和样式
│   │   ├── common/           # 通用UI组件
│   │   ├── auth/             # 认证相关UI
│   │   ├── home/             # 主页面
│   │   ├── document/         # 文档管理UI
│   │   ├── asset/            # 资产管理UI
│   │   ├── search/           # 搜索功能UI
│   │   ├── voice/            # 语音查询UI
│   │   └── settings/         # 设置页面
│   ├── presentation/          # 表示层
│   │   └── viewmodel/        # ViewModels
│   ├── domain/               # 领域层
│   │   ├── entity/           # 实体类
│   │   ├── repository/       # Repository接口
│   │   └── usecase/          # 用例类
│   ├── data/                 # 数据层
│   │   ├── repository/       # Repository实现
│   │   ├── remote/           # 远程数据源
│   │   ├── local/            # 本地数据源
│   │   └── mapper/           # 数据映射器
│   └── util/                 # 工具类
```

## 3. 核心功能模块设计

### 3.1 认证管理模块

#### 3.1.1 功能特性
- 服务器地址配置和验证
- 用户登录与自动登录
- Token自动刷新机制
- 设备绑定和管理
- 安全退出登录

#### 3.1.2 核心类设计

```kotlin
// 认证用例
class LoginUseCase @Inject constructor(
    private val authRepository: AuthRepository,
    private val configRepository: ConfigRepository
) {
    suspend operator fun invoke(
        serverUrl: String,
        username: String, 
        password: String,
        deviceInfo: DeviceInfo
    ): Result<AuthToken>
}

// Token管理器
class TokenManager @Inject constructor(
    private val tokenStorage: TokenStorage,
    private val apiService: ApiService
) {
    suspend fun refreshTokenIfNeeded(): Result<AuthToken>
    fun isTokenValid(): Boolean
    suspend fun clearTokens()
}

// 认证ViewModel
@HiltViewModel
class AuthViewModel @Inject constructor(
    private val loginUseCase: LoginUseCase,
    private val tokenManager: TokenManager
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(AuthUiState())
    val uiState = _uiState.asStateFlow()
    
    fun login(serverUrl: String, username: String, password: String) {
        viewModelScope.launch {
            // 登录逻辑
        }
    }
}
```

### 3.2 网络层架构

#### 3.2.1 API服务设计

```kotlin
// 基础API接口
interface ApiService {
    @POST("auth/login")
    suspend fun login(@Body request: LoginRequest): LoginResponse
    
    @POST("mobile/auth/refresh")
    suspend fun refreshToken(@Body request: RefreshTokenRequest): AuthResponse
    
    @GET("mobile/documents/")
    suspend fun getDocuments(
        @Query("page") page: Int,
        @Query("size") size: Int,
        @Query("search") search: String?
    ): DocumentListResponse
    
    @GET("mobile/assets/")
    suspend fun getAssets(
        @Query("page") page: Int,
        @Query("size") size: Int,
        @Query("asset_type") assetType: String?
    ): AssetListResponse
    
    @POST("voice/query")
    suspend fun voiceQuery(@Body request: VoiceQueryRequest): VoiceQueryResponse
}

// 网络请求拦截器
class AuthInterceptor @Inject constructor(
    private val tokenManager: TokenManager
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val original = chain.request()
        val token = tokenManager.getAccessToken()
        
        val request = if (token != null) {
            original.newBuilder()
                .header("Authorization", "Bearer $token")
                .build()
        } else {
            original
        }
        
        return chain.proceed(request)
    }
}
```

#### 3.2.2 网络状态管理

```kotlin
// 网络状态监听器
class NetworkStatusTracker @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val _networkStatus = MutableStateFlow(NetworkStatus.Unknown)
    val networkStatus = _networkStatus.asStateFlow()
    
    fun startTracking() {
        val connectivityManager = context.getSystemService<ConnectivityManager>()
        // 网络状态监听实现
    }
}

// 离线优先Repository实现
class DocumentRepositoryImpl @Inject constructor(
    private val remoteDataSource: DocumentRemoteDataSource,
    private val localDataSource: DocumentLocalDataSource,
    private val networkStatusTracker: NetworkStatusTracker
) : DocumentRepository {
    
    override fun getDocuments(page: Int, size: Int): Flow<PagingData<Document>> {
        return Pager(
            config = PagingConfig(pageSize = size),
            remoteMediator = DocumentRemoteMediator(
                remoteDataSource, localDataSource
            )
        ) {
            localDataSource.getDocumentsPagingSource()
        }.flow
    }
}
```

### 3.3 数据存储架构

#### 3.3.1 Room数据库设计

```kotlin
// 文档实体
@Entity(tableName = "documents")
data class DocumentEntity(
    @PrimaryKey val id: Int,
    val title: String,
    val summary: String,
    val fileType: String,
    val fileSize: Long?,
    val createdAt: String,
    val updatedAt: String,
    val tags: List<String>,
    val isFavorite: Boolean = false,
    val isDownloaded: Boolean = false,
    val localFilePath: String? = null,
    val lastSyncTime: Long = System.currentTimeMillis()
)

// 资产实体
@Entity(tableName = "assets")
data class AssetEntity(
    @PrimaryId val id: Int,
    val name: String,
    val assetType: String,
    val status: String,
    val statusDisplay: String,
    val location: String?,
    val ipAddress: String?,
    val healthScore: Int?,
    val lastCheck: String?,
    val createdAt: String,
    val tags: List<String>,
    val lastSyncTime: Long = System.currentTimeMillis()
)

// 数据库DAO
@Dao
interface DocumentDao {
    @Query("SELECT * FROM documents ORDER BY createdAt DESC")
    fun getDocumentsPagingSource(): PagingSource<Int, DocumentEntity>
    
    @Query("SELECT * FROM documents WHERE title LIKE :query OR summary LIKE :query")
    suspend fun searchDocuments(query: String): List<DocumentEntity>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertDocuments(documents: List<DocumentEntity>)
    
    @Update
    suspend fun updateDocument(document: DocumentEntity)
    
    @Query("DELETE FROM documents WHERE lastSyncTime < :threshold")
    suspend fun deleteOldDocuments(threshold: Long)
}

// 数据库主类
@Database(
    entities = [DocumentEntity::class, AssetEntity::class],
    version = 1,
    exportSchema = false
)
@TypeConverters(Converters::class)
abstract class AppDatabase : RoomDatabase() {
    abstract fun documentDao(): DocumentDao
    abstract fun assetDao(): AssetDao
}
```

#### 3.3.2 偏好设置管理

```kotlin
// 设置数据类
@Serializable
data class AppSettings(
    val serverUrl: String = "",
    val username: String = "",
    val rememberLogin: Boolean = false,
    val enableVoiceQuery: Boolean = true,
    val cacheExpiry: Int = 24, // 小时
    val downloadWifiOnly: Boolean = true,
    val notificationEnabled: Boolean = true
)

// 设置管理器
class SettingsManager @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "settings")
    
    val settings: Flow<AppSettings> = context.dataStore.data.map { preferences ->
        AppSettings(
            serverUrl = preferences[SERVER_URL_KEY] ?: "",
            username = preferences[USERNAME_KEY] ?: "",
            rememberLogin = preferences[REMEMBER_LOGIN_KEY] ?: false,
            enableVoiceQuery = preferences[VOICE_QUERY_KEY] ?: true,
            cacheExpiry = preferences[CACHE_EXPIRY_KEY] ?: 24,
            downloadWifiOnly = preferences[DOWNLOAD_WIFI_ONLY_KEY] ?: true,
            notificationEnabled = preferences[NOTIFICATION_ENABLED_KEY] ?: true
        )
    }
    
    suspend fun updateServerUrl(url: String) {
        context.dataStore.edit { preferences ->
            preferences[SERVER_URL_KEY] = url
        }
    }
}
```

### 3.4 UI层设计

#### 3.4.1 Compose UI组件

```kotlin
// 文档列表组件
@Composable
fun DocumentList(
    documents: LazyPagingItems<Document>,
    onDocumentClick: (Document) -> Unit,
    onDownloadClick: (Document) -> Unit,
    modifier: Modifier = Modifier
) {
    LazyColumn(
        modifier = modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        items(documents) { document ->
            document?.let {
                DocumentCard(
                    document = it,
                    onDocumentClick = onDocumentClick,
                    onDownloadClick = onDownloadClick
                )
            }
        }
    }
}

// 文档卡片组件
@Composable
fun DocumentCard(
    document: Document,
    onDocumentClick: (Document) -> Unit,
    onDownloadClick: (Document) -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier
            .fillMaxWidth()
            .clickable { onDocumentClick(document) },
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
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
                    text = document.title,
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.weight(1f)
                )
                
                IconButton(onClick = { onDownloadClick(document) }) {
                    Icon(
                        imageVector = if (document.isDownloaded) {
                            Icons.Default.CloudDone
                        } else {
                            Icons.Default.CloudDownload
                        },
                        contentDescription = "下载文档"
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(8.dp))
            
            Text(
                text = document.summary,
                style = MaterialTheme.typography.bodyMedium,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Chip(
                    onClick = { },
                    label = { Text(document.fileType) }
                )
                
                Text(
                    text = document.fileSizeDisplay,
                    style = MaterialTheme.typography.bodySmall
                )
            }
        }
    }
}

// 语音搜索组件
@Composable
fun VoiceSearchBar(
    query: String,
    onQueryChange: (String) -> Unit,
    onSearch: () -> Unit,
    onVoiceSearch: () -> Unit,
    isListening: Boolean = false,
    modifier: Modifier = Modifier
) {
    OutlinedTextField(
        value = query,
        onValueChange = onQueryChange,
        placeholder = { Text("搜索文档或设备...") },
        leadingIcon = {
            Icon(Icons.Default.Search, contentDescription = "搜索")
        },
        trailingIcon = {
            IconButton(onClick = onVoiceSearch) {
                Icon(
                    imageVector = if (isListening) Icons.Default.Mic else Icons.Default.MicNone,
                    contentDescription = "语音搜索",
                    tint = if (isListening) MaterialTheme.colorScheme.primary else LocalContentColor.current
                )
            }
        },
        keyboardOptions = KeyboardOptions(
            imeAction = ImeAction.Search
        ),
        keyboardActions = KeyboardActions(
            onSearch = { onSearch() }
        ),
        modifier = modifier.fillMaxWidth()
    )
}
```

#### 3.4.2 导航架构

```kotlin
// 导航目的地
sealed class Screen(val route: String) {
    object Splash : Screen("splash")
    object Login : Screen("login")
    object Home : Screen("home")
    object Documents : Screen("documents")
    object DocumentDetail : Screen("document_detail/{documentId}") {
        fun createRoute(documentId: Int) = "document_detail/$documentId"
    }
    object Assets : Screen("assets")
    object AssetDetail : Screen("asset_detail/{assetId}") {
        fun createRoute(assetId: Int) = "asset_detail/$assetId"
    }
    object Search : Screen("search")
    object VoiceQuery : Screen("voice_query")
    object Settings : Screen("settings")
}

// 主导航
@Composable
fun MainNavigation(
    navController: NavHostController,
    startDestination: String
) {
    NavHost(
        navController = navController,
        startDestination = startDestination
    ) {
        composable(Screen.Splash.route) {
            SplashScreen(
                onNavigateToLogin = {
                    navController.navigate(Screen.Login.route) {
                        popUpTo(Screen.Splash.route) { inclusive = true }
                    }
                },
                onNavigateToHome = {
                    navController.navigate(Screen.Home.route) {
                        popUpTo(Screen.Splash.route) { inclusive = true }
                    }
                }
            )
        }
        
        composable(Screen.Login.route) {
            LoginScreen(
                onNavigateToHome = {
                    navController.navigate(Screen.Home.route) {
                        popUpTo(Screen.Login.route) { inclusive = true }
                    }
                }
            )
        }
        
        composable(Screen.Home.route) {
            HomeScreen(
                onNavigateToDocuments = {
                    navController.navigate(Screen.Documents.route)
                },
                onNavigateToAssets = {
                    navController.navigate(Screen.Assets.route)
                },
                onNavigateToVoiceQuery = {
                    navController.navigate(Screen.VoiceQuery.route)
                }
            )
        }
        
        // 其他路由定义...
    }
}
```

## 4. 特色功能设计

### 4.1 语音查询功能

#### 4.1.1 语音识别集成
```kotlin
// 语音识别管理器
class SpeechRecognitionManager @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val speechRecognizer = SpeechRecognizer.createSpeechRecognizer(context)
    
    fun startListening(
        onResult: (String) -> Unit,
        onError: (String) -> Unit
    ) {
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.CHINESE.language)
            putExtra(RecognizerIntent.EXTRA_CALLING_PACKAGE, context.packageName)
        }
        
        speechRecognizer.setRecognitionListener(object : RecognitionListener {
            override fun onResults(results: Bundle?) {
                val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                matches?.firstOrNull()?.let { onResult(it) }
            }
            
            override fun onError(error: Int) {
                onError("语音识别错误: $error")
            }
            
            // 其他回调方法实现...
        })
        
        speechRecognizer.startListening(intent)
    }
}

// 语音查询ViewModel
@HiltViewModel
class VoiceQueryViewModel @Inject constructor(
    private val voiceQueryUseCase: VoiceQueryUseCase,
    private val speechRecognitionManager: SpeechRecognitionManager
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(VoiceQueryUiState())
    val uiState = _uiState.asStateFlow()
    
    fun startVoiceRecognition() {
        _uiState.update { it.copy(isListening = true) }
        
        speechRecognitionManager.startListening(
            onResult = { query ->
                _uiState.update { it.copy(isListening = false, queryText = query) }
                performVoiceQuery(query)
            },
            onError = { error ->
                _uiState.update { it.copy(isListening = false, error = error) }
            }
        )
    }
    
    private fun performVoiceQuery(query: String) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            
            voiceQueryUseCase(query)
                .onSuccess { result ->
                    _uiState.update { 
                        it.copy(
                            isLoading = false,
                            queryResult = result,
                            error = null
                        )
                    }
                }
                .onFailure { exception ->
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            error = exception.message
                        )
                    }
                }
        }
    }
}
```

### 4.2 离线缓存策略

#### 4.2.1 缓存管理
```kotlin
// 缓存策略接口
interface CacheStrategy<T> {
    suspend fun shouldRefresh(cachedData: T?): Boolean
    suspend fun getCachedData(): T?
    suspend fun saveData(data: T)
    suspend fun clearExpiredData()
}

// 文档缓存策略
class DocumentCacheStrategy @Inject constructor(
    private val documentDao: DocumentDao,
    private val settingsManager: SettingsManager
) : CacheStrategy<List<Document>> {
    
    override suspend fun shouldRefresh(cachedData: List<Document>?): Boolean {
        if (cachedData.isNullOrEmpty()) return true
        
        val settings = settingsManager.settings.first()
        val expiryTime = System.currentTimeMillis() - (settings.cacheExpiry * 60 * 60 * 1000)
        
        return cachedData.any { it.lastSyncTime < expiryTime }
    }
    
    override suspend fun getCachedData(): List<Document>? {
        return documentDao.getAllDocuments().map { it.toDomain() }
    }
    
    override suspend fun saveData(data: List<Document>) {
        val entities = data.map { it.toEntity().copy(lastSyncTime = System.currentTimeMillis()) }
        documentDao.insertDocuments(entities)
    }
    
    override suspend fun clearExpiredData() {
        val settings = settingsManager.settings.first()
        val expiryTime = System.currentTimeMillis() - (settings.cacheExpiry * 60 * 60 * 1000)
        documentDao.deleteOldDocuments(expiryTime)
    }
}
```

#### 4.2.2 文件下载管理
```kotlin
// 文件下载管理器
class FileDownloadManager @Inject constructor(
    @ApplicationContext private val context: Context,
    private val apiService: ApiService
) {
    private val downloadManager = context.getSystemService<DownloadManager>()!!
    
    suspend fun downloadDocument(document: Document): Result<String> {
        return try {
            val downloadsDir = File(context.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS), "documents")
            if (!downloadsDir.exists()) downloadsDir.mkdirs()
            
            val fileName = "${document.id}_${document.title}.${document.fileType}"
            val file = File(downloadsDir, fileName)
            
            if (file.exists()) {
                Result.success(file.absolutePath)
            } else {
                val response = apiService.downloadDocument(document.id)
                val inputStream = response.byteStream()
                val outputStream = file.outputStream()
                
                inputStream.use { input ->
                    outputStream.use { output ->
                        input.copyTo(output)
                    }
                }
                
                Result.success(file.absolutePath)
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    fun getDownloadedDocuments(): List<File> {
        val downloadsDir = File(context.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS), "documents")
        return downloadsDir.listFiles()?.toList() ?: emptyList()
    }
}
```

## 5. 性能优化策略

### 5.1 内存管理
- 使用`Paging3`实现分页加载，避免一次性加载大量数据
- 图片使用`Coil`进行懒加载和缓存
- 适当使用`remember`和`LaunchedEffect`优化Compose重组
- 实现内存泄漏检测和监控

### 5.2 网络优化
- 实现请求缓存和去重机制
- 使用OkHttp的连接池和Keep-Alive
- 根据网络状态调整请求策略
- 实现断点续传功能

### 5.3 电池优化
- 合理使用Background工作
- 实现智能同步策略
- 优化定位和传感器使用
- 使用WorkManager管理后台任务

## 6. 安全设计

### 6.1 数据安全
- 使用EncryptedSharedPreferences存储敏感信息
- 实现证书绑定(Certificate Pinning)
- 对本地数据库进行加密
- 实现数据传输加密

### 6.2 身份验证
- 支持生物识别登录(指纹/人脸)
- 实现设备绑定验证
- Token自动刷新和安全存储
- 登录状态监控和异常检测

## 7. 测试策略

### 7.1 单元测试
```kotlin
// ViewModel测试示例
@ExperimentalCoroutinesApi
class DocumentViewModelTest {
    
    @get:Rule
    val mainDispatcherRule = MainDispatcherRule()
    
    @Mock
    private lateinit var getDocumentsUseCase: GetDocumentsUseCase
    
    private lateinit var viewModel: DocumentViewModel
    
    @Before
    fun setup() {
        MockKAnnotations.init(this)
        viewModel = DocumentViewModel(getDocumentsUseCase)
    }
    
    @Test
    fun `when loadDocuments called, should update uiState with documents`() = runTest {
        // Given
        val expectedDocuments = listOf(
            Document(id = 1, title = "测试文档1"),
            Document(id = 2, title = "测试文档2")
        )
        coEvery { getDocumentsUseCase(any()) } returns Result.success(expectedDocuments)
        
        // When
        viewModel.loadDocuments()
        
        // Then
        val uiState = viewModel.uiState.value
        assertEquals(expectedDocuments, uiState.documents)
        assertFalse(uiState.isLoading)
    }
}
```

### 7.2 UI测试
```kotlin
// Compose UI测试示例
@RunWith(AndroidJUnit4::class)
class DocumentScreenTest {
    
    @get:Rule
    val composeTestRule = createComposeRule()
    
    @Test
    fun documentScreen_displaysDocuments() {
        val testDocuments = listOf(
            Document(id = 1, title = "测试文档1", summary = "摘要1"),
            Document(id = 2, title = "测试文档2", summary = "摘要2")
        )
        
        composeTestRule.setContent {
            DocumentScreen(
                documents = testDocuments,
                onDocumentClick = { },
                onDownloadClick = { }
            )
        }
        
        composeTestRule.onNodeWithText("测试文档1").assertIsDisplayed()
        composeTestRule.onNodeWithText("测试文档2").assertIsDisplayed()
    }
}
```

## 8. 部署和发布

### 8.1 构建配置
```gradle
// build.gradle (Module: app)
android {
    compileSdk 34
    
    defaultConfig {
        applicationId "com.runyang.bridge.maintenance"
        minSdk 24
        targetSdk 34
        versionCode 1
        versionName "1.0.0"
    }
    
    buildTypes {
        debug {
            isDebuggable = true
            applicationIdSuffix = ".debug"
            versionNameSuffix = "-debug"
            buildConfigField("String", "API_BASE_URL", "\"http://192.168.1.100:8000/api/v1/\"")
        }
        
        release {
            isMinifyEnabled = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
            buildConfigField("String", "API_BASE_URL", "\"https://api.runyang-bridge.com/api/v1/\"")
        }
    }
    
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    
    kotlinOptions {
        jvmTarget = "17"
    }
    
    buildFeatures {
        compose = true
        buildConfig = true
    }
    
    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.8"
    }
}
```

### 8.2 版本管理
- 使用语义化版本控制
- 实现自动版本号更新
- 配置多环境构建
- 设置代码签名和混淆

## 9. 项目进度规划

### Phase 1: 基础框架搭建 (2周)
- [x] 项目初始化和架构设计
- [ ] 依赖注入配置
- [ ] 网络层实现
- [ ] 数据层基础框架
- [ ] 基础UI组件库

### Phase 2: 核心功能开发 (3周)
- [ ] 用户认证模块
- [ ] 文档管理功能
- [ ] 资产查询功能
- [ ] 搜索功能实现
- [ ] 离线缓存机制

### Phase 3: 高级功能开发 (2周)
- [ ] 语音查询功能
- [ ] 文件下载管理
- [ ] 推送通知
- [ ] 设置和配置

### Phase 4: 测试和优化 (1周)
- [ ] 单元测试编写
- [ ] UI测试编写
- [ ] 性能测试和优化
- [ ] 安全测试

### Phase 5: 发布准备 (1周)
- [ ] 构建配置优化
- [ ] 应用签名配置
- [ ] 应用商店资料准备
- [ ] 用户手册编写

## 10. 总结

这个Android应用架构设计采用了现代化的开发技术栈和最佳实践，确保了应用的可维护性、可扩展性和用户体验。通过Clean Architecture的分层设计，实现了业务逻辑与UI的解耦；通过MVVM模式和Compose的结合，提供了响应式的用户界面；通过完善的缓存和网络策略，确保了在各种网络环境下的稳定运行。

该架构设计为润扬大桥运维管理系统的移动端提供了坚实的技术基础，支持未来功能的持续扩展和优化。