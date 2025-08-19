# CORS配置示例和最佳实践

## 🎯 快速配置指南

### 场景1：开发测试环境
```env
# 在 backend/.env 中修改以下配置：
# 自动检测本机IP + localhost（推荐开发环境）
CORS_MODE=auto
CORS_AUTO_DETECT=true
CORS_INCLUDE_LOCALHOST=true
```

### 场景2：局域网部署
```env
# 在 backend/.env 中修改以下配置：
CORS_MODE=auto
CORS_AUTO_DETECT=true
CORS_INCLUDE_LOCALHOST=true
CORS_EXTRA_PORTS=3000,8080
```

### 场景3：指定服务器部署
```env
# 在 backend/.env 中修改以下配置：
CORS_MODE=manual
CORS_CUSTOM_ORIGINS=http://192.168.1.100:5173,http://192.168.1.100:5174
```

### 场景4：生产环境（域名）
```env
# 在 backend/.env 中修改以下配置：
CORS_MODE=manual
CORS_CUSTOM_ORIGINS=https://docs.company.com,https://admin.company.com
CORS_AUTO_DETECT=false
CORS_INCLUDE_LOCALHOST=false
```

### 场景5：混合环境
```env
# 在 backend/.env 中修改以下配置：
CORS_MODE=mixed
CORS_CUSTOM_ORIGINS=https://external-service.com
CORS_AUTO_DETECT=true
CORS_INCLUDE_LOCALHOST=true
```

## 🔧 配置模式详解

### AUTO模式 - 智能自动配置
```env
# 在 backend/.env 中配置：
CORS_MODE=auto
CORS_AUTO_DETECT=true        # 自动检测本机IP
CORS_INCLUDE_LOCALHOST=true  # 包含localhost地址
CORS_INCLUDE_HTTPS=true      # 包含HTTPS变体
CORS_EXTRA_PORTS=3000,8080   # 额外端口
CORS_CUSTOM_ORIGINS=https://app.com # 额外手动添加的地址
```

**生成的CORS源示例：**
- http://localhost:5173
- http://localhost:5174  
- http://127.0.0.1:5173
- http://192.168.66.99:5173 (自动检测)
- https://192.168.66.99:5173
- https://app.com (手动添加)

### MANUAL模式 - 完全手动控制
```env
# 在 backend/.env 中配置：
CORS_MODE=manual
CORS_CUSTOM_ORIGINS=http://192.168.1.100:5173,http://192.168.1.101:5173,https://docs.company.com
```

**特点：**
- 仅使用 CORS_CUSTOM_ORIGINS 中指定的地址
- 不执行IP自动检测
- 提供最精确的控制


## 🚀 启动脚本自动配置

### Windows
```batch
# 自动检测并配置
start-production-universal.bat

# 指定IP地址
start-production-universal.bat 192.168.1.100

# 自动模式（开发用）
set CORS_MODE=auto && start-production-universal.bat
```

### Linux/macOS
```bash
# 自动检测并配置
./start-production-universal.sh

# 指定IP地址
./start-production-universal.sh 192.168.1.100

# 手动模式
export CORS_MODE=manual
export CORS_ORIGINS="http://192.168.1.100:5173,http://192.168.1.100:5174"
./start-production-universal.sh
```

## 🔍 故障排除

### 问题1：CORS错误仍然出现
**检查项：**
1. 确认 CORS_MODE 配置正确
2. 检查 CORS_ORIGINS 格式（使用逗号分隔，无空格）
3. 确认协议（http/https）匹配
4. 检查端口号是否正确

**调试命令：**
```bash
# 查看实际配置的CORS源
curl http://localhost:8002/api/v1/ -v
# 查看控制台日志中的 [CORS] 信息
```

### 问题2：无法从其他电脑访问
**解决步骤：**
1. 确认 `CORS_AUTO_DETECT=true` 或手动添加客户端IP
2. 检查服务器防火墙设置
3. 确认 SERVER_HOST=0.0.0.0
4. 测试网络连通性

### 问题3：自动检测IP不准确
**解决方案：**
```env
# 关闭自动检测，手动指定
CORS_MODE=manual
CORS_ORIGINS=http://正确的IP:5173,http://正确的IP:5174
```

## 📋 配置验证清单

### 开发环境
- [ ] CORS_MODE=auto
- [ ] CORS_AUTO_DETECT=true
- [ ] CORS_INCLUDE_LOCALHOST=true
- [ ] 可以从 localhost 访问
- [ ] 可以从其他电脑访问（如需要）

### 测试环境
- [ ] CORS_MODE=auto
- [ ] CORS_ORIGINS 包含测试域名/IP
- [ ] 自动检测功能正常

### 生产环境
- [ ] CORS_MODE=manual
- [ ] CORS_ORIGINS 仅包含必要域名
- [ ] CORS_AUTO_DETECT=false
- [ ] CORS_INCLUDE_LOCALHOST=false
- [ ] 使用 HTTPS

## 💡 最佳实践

1. **开发环境**：使用 `CORS_MODE=auto` 快速开发
2. **测试环境**：使用 `CORS_MODE=auto` 或 `CORS_MODE=mixed` 灵活配置
3. **生产环境**：使用 `CORS_MODE=manual` 精确控制
4. **安全原则**：仅允许必要的域名和端口
5. **日志监控**：关注控制台中的 [CORS] 日志信息

## 🔄 配置迁移

### 从旧版本升级
如果你的系统使用旧的硬编码CORS配置，迁移到新系统：

**步骤1：备份现有配置**
```bash
cp backend/.env backend/.env.backup
```

**步骤2：使用新配置格式**
```env
# 旧配置 (不再支持)
ALLOW_ALL_ORIGINS=true

# 新配置
CORS_MODE=auto  # 更安全的开发环境配置
CORS_AUTO_DETECT=true
CORS_INCLUDE_LOCALHOST=true
```

**步骤3：测试验证**
启动系统并验证所有客户端都能正常访问。