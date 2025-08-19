# 润扬大桥运维文档管理系统 - Android APP 测试计划

## 测试概述

### 测试目标
确保Android APP在各种环境和条件下能够稳定运行，提供良好的用户体验，满足润扬大桥运维文档管理的业务需求。

### 测试范围
- 文档管理功能
- 设备资产管理功能
- 用户认证与授权
- 网络请求与数据同步
- UI/UX交互体验
- 性能与兼容性

## 测试环境配置

### 硬件要求
- Android设备：API Level 24+ (Android 7.0+)
- 内存：至少2GB RAM
- 存储：至少100MB可用空间
- 网络：支持WiFi和移动网络

### 软件要求
- Android Studio 2023.3.1+
- Gradle 8.13
- JDK 17
- Android SDK 34

### 测试数据准备
```json
{
  "test_documents": [
    {
      "id": 1,
      "title": "桥梁检查报告_2024Q1",
      "summary": "第一季度桥梁结构检查详细报告",
      "fileType": "PDF",
      "uploadDate": "2024-01-15T10:30:00Z",
      "tags": ["检查", "结构", "季度报告"]
    },
    {
      "id": 2,
      "title": "设备维护手册_主缆",
      "summary": "主缆系统维护操作指南",
      "fileType": "DOC",
      "uploadDate": "2024-02-01T14:20:00Z",
      "tags": ["维护", "主缆", "操作指南"]
    }
  ],
  "test_assets": [
    {
      "id": 101,
      "name": "主塔传感器A1",
      "assetType": "传感器",
      "status": "运行中",
      "healthScore": 95,
      "location": "主塔A区域"
    },
    {
      "id": 102,
      "name": "照明系统B2",
      "assetType": "照明设备",
      "status": "维护中",
      "healthScore": 78,
      "location": "桥面B段"
    }
  ]
}
```

## 测试类型和策略

### 1. 单元测试 (Unit Tests)

#### 1.1 领域层测试
- **Document实体测试**：验证数据模型的属性和方法
- **Asset实体测试**：验证状态计算和颜色映射
- **用例测试**：验证业务逻辑的正确性

#### 1.2 数据层测试
- **Repository测试**：验证数据获取和缓存逻辑
- **网络请求测试**：使用MockWebServer模拟API响应
- **数据库操作测试**：Room数据库的CRUD操作

#### 1.3 表现层测试
- **ViewModel测试**：验证状态管理和UI逻辑
- **导航测试**：验证页面跳转和参数传递

### 2. 集成测试 (Integration Tests)

#### 2.1 模块间集成
- **数据流测试**：从Repository到ViewModel到UI的完整数据流
- **依赖注入测试**：Hilt容器的正确配置和依赖解析
- **数据库迁移测试**：Room数据库的版本升级

#### 2.2 API集成测试
- **网络连接测试**：验证与后端API的通信
- **认证流程测试**：登录、token刷新、权限验证
- **数据同步测试**：本地缓存与远程数据的同步

### 3. UI测试 (UI/Espresso Tests)

#### 3.1 功能测试
- **文档列表页面**：搜索、筛选、分页加载
- **文档详情页面**：内容显示、操作按钮
- **资产管理页面**：列表展示、状态筛选
- **登录页面**：表单验证、错误处理

#### 3.2 交互测试
- **手势操作**：滑动、点击、长按
- **键盘输入**：搜索框、表单填写
- **导航操作**：底部导航栏、返回按钮

### 4. 性能测试

#### 4.1 启动性能
- **冷启动时间**：应用首次启动到可用的时间
- **热启动时间**：应用从后台恢复的时间
- **内存使用**：启动时的内存占用

#### 4.2 运行性能
- **列表滚动**：长列表的流畅度测试
- **图片加载**：文档预览图的加载性能
- **网络请求**：API响应时间和重试机制

### 5. 兼容性测试

#### 5.1 设备兼容性
- **屏幕尺寸**：手机、平板不同分辨率
- **Android版本**：API 24-34的兼容性
- **硬件特性**：相机、存储权限

#### 5.2 网络兼容性
- **网络状态**：WiFi、4G/5G、断网恢复
- **网络质量**：弱网环境下的表现

## 测试用例执行

### 执行命令

#### 单元测试
```bash
# 运行所有单元测试
./gradlew test

# 运行特定模块测试
./gradlew :app:testDebugUnitTest

# 生成测试报告
./gradlew testDebugUnitTest --tests "*DocumentTest*"
```

#### 集成测试
```bash
# 运行集成测试
./gradlew connectedAndroidTest

# 运行特定集成测试
./gradlew connectedDebugAndroidTest --tests "*RepositoryTest*"
```

#### UI测试
```bash
# 运行UI测试
./gradlew connectedAndroidTest --tests "*ScreenTest*"

# 使用Firebase Test Lab (如果配置)
gcloud firebase test android run --type robo --app app-debug.apk
```

### 测试覆盖率
```bash
# 生成覆盖率报告
./gradlew createDebugCoverageReport

# 查看覆盖率报告
open app/build/reports/coverage/debug/index.html
```

## 缺陷管理

### 缺陷等级分类
- **P0-阻塞**：应用崩溃、无法启动、数据丢失
- **P1-严重**：核心功能异常、性能严重下降
- **P2-一般**：次要功能问题、UI显示异常
- **P3-轻微**：文字错误、优化建议

### 缺陷报告模板
```
标题：[模块] 简要描述问题
等级：P0/P1/P2/P3
环境：Android版本、设备型号、APP版本
复现步骤：
1. 打开APP
2. 点击文档列表
3. 执行搜索操作
4. 观察结果

期望结果：显示搜索结果列表
实际结果：应用崩溃/无响应/显示错误
附件：截图、日志文件
```

## 自动化测试流程

### CI/CD集成
```yaml
# GitHub Actions 示例
name: Android CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Setup JDK 17
      uses: actions/setup-java@v3
      with:
        java-version: '17'
        distribution: 'temurin'
    - name: Run Unit Tests
      run: ./gradlew test
    - name: Run Connected Tests
      run: ./gradlew connectedAndroidTest
    - name: Upload Test Reports
      uses: actions/upload-artifact@v3
      with:
        name: test-reports
        path: app/build/reports/
```

### 测试数据管理
- **Mock数据**：使用WireMock模拟API响应
- **测试数据库**：使用Room in-memory数据库
- **UI测试数据**：使用Espresso的IdlingResource管理异步操作

## 测试时间安排

### 测试阶段
1. **单元测试**：2天
2. **集成测试**：2天  
3. **UI测试**：3天
4. **性能测试**：1天
5. **兼容性测试**：2天
6. **回归测试**：1天

### 测试里程碑
- **阶段1**：基础功能测试完成
- **阶段2**：性能和兼容性测试完成
- **阶段3**：完整回归测试通过
- **发布准备**：所有P0/P1缺陷修复完成

## 验收标准

### 功能验收
- [ ] 文档管理功能正常运行
- [ ] 设备资产管理功能正常运行
- [ ] 用户认证流程完整
- [ ] 网络异常处理正确

### 性能验收
- [ ] 应用启动时间 < 3秒
- [ ] 列表滚动帧率 > 55fps
- [ ] 内存使用 < 200MB
- [ ] 网络请求响应时间 < 2秒

### 质量验收
- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试覆盖率 > 70%
- [ ] UI测试覆盖核心用户流程
- [ ] 无P0/P1级别缺陷

## 工具和框架

### 测试框架
- **JUnit 5**：单元测试框架
- **Mockito**：Mock对象框架
- **Espresso**：UI自动化测试
- **Robolectric**：Android单元测试运行环境

### 辅助工具
- **Jacoco**：代码覆盖率统计
- **LeakCanary**：内存泄漏检测
- **Firebase Test Lab**：云端设备测试
- **Charles/Proxy**：网络请求调试

### Mock工具
- **WireMock**：HTTP Mock服务器
- **MockWebServer**：OkHttp Mock服务器
- **Hilt Test**：依赖注入测试支持

这个测试计划涵盖了Android APP开发的各个测试层面，确保应用的质量和稳定性。你可以根据实际项目进度和资源情况调整测试范围和时间安排。