# 🔄 润扬大桥运维文档管理系统 - 版本更新指南

## 📋 快速参考

### 🚀 开发端 (代码提交者)

当您修改了代码需要发布新版本时：

```bash
# Windows
update-version.bat

# Linux/macOS  
./update-version.sh
```

**功能**: 自动提交代码、创建版本标签、推送到GitHub

---

### 🏭 生产端 (部署服务器)

当需要更新到最新版本时：

```bash
# Windows
deploy-update.bat

# Linux/macOS
./deploy-update.sh
```

**功能**: 安全停止服务、更新代码、备份配置、重启服务

---

### 🔍 配置检测

检查配置文件是否需要更新：

```bash
# Windows
check-config-changes.bat

# Linux/macOS
./check-config-changes.sh
```

**功能**: 检测配置文件差异、依赖更新、提供修复建议

---

### 🏥 服务健康检查

检查系统运行状态：

```bash
# Windows
check-service-health.bat

# Linux/macOS
./check-service-health.sh
```

**功能**: 检查服务状态、端口监听、API响应、日志状态

---

## 🛠️ 详细使用说明

### 1. 开发端版本发布流程

#### 使用自动化脚本 (推荐)
1. 确保代码修改完成
2. 运行 `update-version.bat` 或 `./update-version.sh`
3. 选择版本类型：
   - `1 (patch)`: Bug修复、小优化
   - `2 (minor)`: 新功能、功能增强  
   - `3 (major)`: 重大架构变更
4. 输入更新说明
5. 脚本自动完成：
   - 添加所有文件到Git
   - 创建标准化提交信息
   - 生成版本标签 (v1.0.x)
   - 推送到GitHub

#### 手动发布流程
```bash
git add .
git commit -m "feat: 更新描述

- 版本更新类型
- 主要功能变更
- 修复的问题

🚀 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git tag -a v1.0.x -m "版本描述"
git push origin main
git push origin v1.0.x
```

### 2. 生产端安全更新流程

#### 使用自动化脚本 (推荐)
1. 运行 `deploy-update.bat` 或 `./deploy-update.sh`
2. 脚本自动执行：
   - 检查网络连接
   - 显示待更新内容
   - 用户确认后继续
   - 备份当前配置和数据
   - 优雅停止服务
   - 拉取最新代码
   - 检测配置变更
   - 恢复配置文件
   - 重新启动服务
   - 验证服务状态

#### 手动更新流程
```bash
# 1. 备份
mkdir backup_$(date +%Y%m%d_%H%M%S)
cp backend/.env frontend/.env *.db backup_*/

# 2. 停止服务
./stop-services.sh  # 或 .bat

# 3. 更新代码
git pull origin main

# 4. 检查配置
git diff HEAD~1 backend/.env.example
git diff HEAD~1 frontend/.env.example

# 5. 更新依赖
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# 6. 启动服务
./start-production.sh  # 或 .bat
```

### 3. 配置变更检测与处理

#### 自动检测
运行 `check-config-changes.bat` 或 `./check-config-changes.sh`

#### 检测内容
- ✅ 后端配置文件 (.env vs .env.example)
- ✅ 前端配置文件 (.env vs .env.example)  
- ✅ Python依赖文件 (requirements.txt)
- ✅ Node.js依赖文件 (package.json)

#### 处理建议
1. **配置差异**: 手动合并新配置项到现有 .env 文件
2. **依赖变更**: 运行相应的依赖更新命令
3. **缺失配置**: 从模板重新创建配置文件

---

## 🆘 故障处理

### 更新失败回滚

#### 快速回滚到上一版本
```bash
git reset --hard HEAD~1
./start-production.sh  # 或 .bat
```

#### 回滚到指定版本
```bash
git tag -l  # 查看所有版本
git checkout v1.0.5  # 回滚到指定版本
./start-production.sh
```

### 配置恢复

#### 从备份恢复
```bash
# 查找备份目录
ls backup_*/

# 恢复配置
cp backup_YYYYMMDD_HHMMSS/backend.env.backup backend/.env
cp backup_YYYYMMDD_HHMMSS/frontend.env.backup frontend/.env
```

### 服务异常处理

#### 检查服务状态
```bash
# 检查端口占用
netstat -tlnp | grep :8002  # 后端
netstat -tlnp | grep :5173  # 前端

# 查看服务日志
tail -f logs/backend.log
tail -f logs/frontend.log
```

#### 手动重启服务
```bash
./stop-services.sh   # 停止所有服务
./start-production.sh  # 重新启动
```

---

## 📊 版本管理最佳实践

### 开发端最佳实践

1. **定期提交**: 避免一次性提交过多更改
2. **清晰描述**: 使用有意义的提交信息
3. **测试验证**: 本地测试通过后再发布
4. **版本规划**: 合理选择版本类型

### 生产端最佳实践

1. **计划更新**: 选择业务低峰期进行更新
2. **备份优先**: 始终在更新前创建完整备份
3. **分阶段验证**: 更新后逐步验证各功能模块
4. **监控观察**: 更新后持续监控系统状态

### 团队协作最佳实践

1. **通知机制**: 更新前通知相关用户
2. **文档更新**: 及时更新变更日志和文档
3. **权限管理**: 明确版本发布权限和流程
4. **应急预案**: 准备快速回滚和恢复方案

---

## 🔧 脚本说明

### update-version.bat / update-version.sh
- **用途**: 开发端版本发布
- **功能**: Git提交、版本标签、推送GitHub
- **适用**: 代码修改后的版本发布

### deploy-update.bat / deploy-update.sh  
- **用途**: 生产端安全更新
- **功能**: 备份、更新、配置检查、服务重启
- **适用**: 生产服务器版本更新

### check-config-changes.bat / check-config-changes.sh
- **用途**: 配置变更检测
- **功能**: 对比配置文件、检查依赖变更
- **适用**: 更新前后的配置验证

### start-production.bat / start-production.sh
- **用途**: 系统启动
- **功能**: 依赖检查、环境配置、服务启动
- **适用**: 初始部署和服务重启

### stop-services.bat / stop-services.sh
- **用途**: 系统停止
- **功能**: 优雅停止所有服务进程
- **适用**: 系统维护和更新前准备

---

## 📞 技术支持

如遇到版本更新问题：

1. **查看日志**: 检查 logs/ 目录下的错误日志
2. **配置检查**: 运行配置检测脚本验证设置
3. **网络诊断**: 确认GitHub连接正常
4. **权限验证**: 检查文件和目录访问权限
5. **回滚恢复**: 必要时执行版本回滚操作

---

**润扬大桥运维文档管理系统** © 2024 | 智慧高速 · 匠心运维