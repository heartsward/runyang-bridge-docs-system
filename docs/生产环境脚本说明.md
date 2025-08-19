# 生产环境启动脚本使用说明

## 脚本概述

本项目提供了完整的生产环境启动和停止脚本，支持Windows和Linux系统。

## Windows脚本

### 1. 快速启动脚本：`start-production-simple.bat`
**特点：**
- 不进行环境检测，直接启动服务
- 适合生产环境快速启动
- 自动显示服务访问信息
- 支持自动打开浏览器

**使用方法：**
```cmd
# 双击运行或在命令行中执行
start-production-simple.bat
```

**启动的服务：**
- 后端服务：http://localhost:8002
- 前端服务：http://localhost:5173

### 2. 完整启动脚本：`start-production.bat`
**特点：**
- 检查Python、Node.js、LibreOffice环境
- 自动安装依赖
- 配置生产环境
- 构建前端应用

**使用方法：**
```cmd
# 双击运行或在命令行中执行
start-production.bat
```

### 3. 停止服务脚本：`stop-production.bat`
**特点：**
- 智能停止所有相关服务
- 清理临时文件和PID文件
- 检查端口占用情况
- 显示详细的停止结果

**使用方法：**
```cmd
# 双击运行或在命令行中执行
stop-production.bat
```

## Linux脚本

### 1. 快速启动脚本：`start-production-simple.sh`
**特点：**
- 彩色输出，界面友好
- 自动检测端口占用
- 后台运行服务
- 实时监控服务状态

**使用方法：**
```bash
# 添加执行权限
chmod +x start-production-simple.sh

# 运行脚本
./start-production-simple.sh
```

### 2. 停止服务脚本：`stop-production.sh`
**特点：**
- 多种停止策略（PID文件、进程名、端口）
- 智能进程终止（TERM -> KILL）
- 系统资源状态显示
- 详细的清理报告

**使用方法：**
```bash
# 添加执行权限
chmod +x stop-production.sh

# 运行脚本
./stop-production.sh
```

## API端点说明

### 核心服务端点
- **前端界面**: http://localhost:5173
- **后端API**: http://localhost:8002
- **API文档**: http://localhost:8002/docs

### 移动端API端点
- **移动端认证**: http://localhost:8002/api/v1/mobile/auth/login
- **文档接口**: http://localhost:8002/api/v1/mobile/documents/
- **资产接口**: http://localhost:8002/api/v1/mobile/assets/
- **语音查询**: http://localhost:8002/api/v1/voice/query

### 系统管理端点
- **系统信息**: http://localhost:8002/api/v1/system/info
- **健康检查**: http://localhost:8002/api/v1/system/health
- **数据分析**: http://localhost:8002/api/v1/analytics/summary
- **用户设置**: http://localhost:8002/api/v1/settings/profile

## 默认登录信息

```
用户名: admin
密码:   admin123
```

**⚠️ 重要提醒：首次登录后请立即修改默认密码**

## 脚本特性对比

| 特性 | start-production.bat | start-production-simple.bat | start-production-simple.sh |
|------|---------------------|----------------------------|---------------------------|
| 环境检测 | ✅ 完整检测 | ❌ 无检测 | ❌ 无检测 |
| 依赖安装 | ✅ 自动安装 | ❌ 需手动 | ❌ 需手动 |
| 快速启动 | ❌ 较慢 | ✅ 快速 | ✅ 快速 |
| 端口检测 | ❌ 基本 | ✅ 智能 | ✅ 智能 |
| 状态监控 | ❌ 无 | ❌ 基本 | ✅ 实时 |
| 彩色输出 | ❌ 无 | ❌ 无 | ✅ 彩色 |
| 进程管理 | ❌ 基本 | ✅ PID管理 | ✅ 高级管理 |

## 故障排除

### 常见问题

1. **端口占用错误**
   ```bash
   # 查看端口占用
   netstat -ano | findstr :8002  # Windows
   lsof -i :8002                 # Linux
   
   # 停止占用进程
   taskkill /pid <PID> /f        # Windows
   kill -9 <PID>                 # Linux
   ```

2. **服务启动失败**
   - 检查Python/Node.js是否安装
   - 检查依赖是否安装完整
   - 查看日志文件：`logs/backend.log`, `logs/frontend.log`

3. **权限问题**（Linux）
   ```bash
   # 添加执行权限
   chmod +x *.sh
   
   # 检查文件权限
   ls -la *.sh
   ```

4. **数据库问题**
   - 检查数据库文件：`backend/yunwei_docs.db`
   - 查看后端日志了解具体错误
   - 如需重置，备份后删除数据库文件

### 日志位置

- **系统日志**: `logs/` 目录
- **后端日志**: `logs/backend.log`
- **前端日志**: `logs/frontend.log`
- **PID文件**: `logs/*.pid`

### 服务健康检查

```bash
# 快速健康检查
curl http://localhost:8002/api/v1/system/health

# 详细系统信息
curl http://localhost:8002/api/v1/system/info
```

## 部署建议

### 生产环境部署
1. 使用进程管理器（如systemd、PM2）
2. 配置反向代理（如Nginx）
3. 设置SSL证书
4. 配置日志轮转
5. 设置自动备份

### 安全配置
1. 修改默认端口
2. 配置防火墙规则
3. 使用强密码
4. 定期更新依赖
5. 监控系统日志

## 技术支持

如遇到问题，请：
1. 检查日志文件
2. 运行健康检查
3. 查看GitHub Issues
4. 联系技术支持团队

---

**版本**: 1.0.0  
**更新时间**: 2025-01-08  
**维护者**: Claude Code Team