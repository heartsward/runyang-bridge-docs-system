# Android应用测试方案

## 概述
本文档为润扬大桥运维文档管理系统Android应用提供完整的测试计划和测试方法。

## 1. 构建测试

### 1.1 基础构建验证
```bash
# 进入android目录
cd android

# 清理构建缓存
./gradlew clean

# 执行Debug构建
./gradlew app:assembleDebug

# 验证APK生成
ls -la app/build/outputs/apk/debug/
```

### 1.2 Release构建测试
```bash
# 构建Release版本
./gradlew app:assembleRelease

# 验证Release APK
ls -la app/build/outputs/apk/release/
```

## 2. 单元测试

### 2.1 运行所有单元测试
```bash
# 运行单元测试
./gradlew test

# 运行特定模块的测试
./gradlew app:testDebugUnitTest

# 查看测试报告
open app/build/reports/tests/testDebugUnitTest/index.html
```

### 2.2 测试覆盖率
```bash
# 生成测试覆盖率报告
./gradlew app:testDebugUnitTestCoverage

# 查看覆盖率报告
open app/build/reports/coverage/test/debug/index.html
```

## 3. 集成测试

### 3.1 仪器化测试（需要Android设备或模拟器）
```bash
# 启动Android设备或模拟器
# 运行仪器化测试
./gradlew app:connectedDebugAndroidTest

# 查看测试报告
open app/build/reports/androidTests/connected/index.html
```

### 3.2 UI测试
```bash
# 运行UI测试
./gradlew app:connectedDebugAndroidTest -Pandroid.testInstrumentationRunnerArguments.class=com.runyang.bridge.maintenance.ui.*Test
```

## 4. 静态代码分析

### 4.1 Lint检查
```bash
# 运行Lint检查
./gradlew app:lintDebug

# 查看Lint报告
open app/build/reports/lint-results-debug.html
```

### 4.2 代码风格检查
```bash
# 如果配置了ktlint
./gradlew ktlintCheck

# 自动修复代码风格问题
./gradlew ktlintFormat
```

## 5. 功能测试方案

### 5.1 手动测试清单

#### 5.1.1 应用启动测试
- [ ] 冷启动正常
- [ ] 热启动正常
- [ ] 启动画面显示正确
- [ ] 权限请求正常

#### 5.1.2 文档管理功能测试
- [ ] 文档列表加载
- [ ] 文档搜索功能
- [ ] 文档筛选功能
- [ ] 文档详情查看
- [ ] 文档分页加载
- [ ] 网络错误处理
- [ ] 空数据状态

#### 5.1.3 设备资产管理测试
- [ ] 资产列表显示
- [ ] 资产状态筛选
- [ ] 资产搜索功能
- [ ] 资产详情查看
- [ ] 资产状态更新
- [ ] 健康评分显示

#### 5.1.4 导航测试
- [ ] 底部导航切换
- [ ] 页面跳转正常
- [ ] 返回按钮功能
- [ ] 深度链接（如果有）

#### 5.1.5 数据同步测试
- [ ] 数据刷新功能
- [ ] 离线数据缓存
- [ ] 网络恢复时同步
- [ ] 数据冲突处理

### 5.2 性能测试
```bash
# 使用Android Studio的Profiler
# 或使用命令行工具
adb shell dumpsys meminfo com.runyang.bridge.maintenance
adb shell dumpsys cpuinfo | grep com.runyang.bridge.maintenance
```

### 5.3 兼容性测试
- Android版本：API 24+ (Android 7.0+)
- 屏幕尺寸：手机、平板
- 网络环境：WiFi、4G/5G、弱网络

## 6. 自动化测试环境配置

### 6.1 Android模拟器设置
```bash
# 列出可用的系统镜像
sdkmanager --list | grep system-images

# 创建AVD
avdmanager create avd -n test_device -k "system-images;android-30;google_apis;x86_64"

# 启动模拟器
emulator -avd test_device
```

### 6.2 CI/CD集成（GitHub Actions示例）
```yaml
name: Android CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up JDK 11
      uses: actions/setup-java@v3
      with:
        java-version: '11'
        distribution: 'temurin'

    - name: Grant execute permission for gradlew
      run: chmod +x android/gradlew

    - name: Run unit tests
      run: cd android && ./gradlew test

    - name: Run lint
      run: cd android && ./gradlew lintDebug

    - name: Build debug APK
      run: cd android && ./gradlew assembleDebug
```

## 7. 问题排查指南

### 7.1 构建失败
1. 检查Java版本（需要JDK 11+）
2. 清理并重新构建：`./gradlew clean build`
3. 检查依赖冲突
4. 查看完整错误日志：`./gradlew build --stacktrace`

### 7.2 测试失败
1. 检查模拟器状态
2. 验证网络连接
3. 清理测试缓存：`./gradlew cleanTestDebugUnitTest`
4. 检查测试数据和Mock配置

### 7.3 性能问题
1. 使用Android Studio Profiler
2. 检查内存泄漏
3. 优化图片加载
4. 检查网络请求效率

## 8. 测试数据准备

### 8.1 Mock数据配置
- 配置测试用的API响应
- 准备不同状态的测试数据
- 模拟网络错误情况

### 8.2 测试账户
- 创建测试用户账户
- 配置不同权限级别
- 准备测试环境配置

## 9. 测试报告

### 9.1 生成综合测试报告
```bash
# 运行所有测试并生成报告
./gradlew clean test connectedDebugAndroidTest lintDebug

# 收集所有报告
find app/build/reports -name "*.html" -type f
```

### 9.2 持续监控
- 设置自动化测试定期运行
- 监控应用崩溃率
- 跟踪性能指标
- 收集用户反馈

## 10. 下一步行动

1. **立即可执行的测试**：
   ```bash
   cd android
   ./gradlew clean
   ./gradlew app:assembleDebug
   ./gradlew test
   ./gradlew app:lintDebug
   ```

2. **设备测试准备**：
   - 安装Android Studio
   - 创建Android模拟器
   - 连接真实设备进行测试

3. **完善测试套件**：
   - 添加更多单元测试
   - 编写UI自动化测试
   - 配置持续集成

4. **性能优化**：
   - 使用Profiler分析性能
   - 优化启动时间
   - 减少内存使用

通过以上测试方案，可以全面验证Android应用的功能性、性能和稳定性，确保应用质量符合生产环境要求。