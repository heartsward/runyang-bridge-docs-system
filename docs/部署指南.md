# 润扬大桥运维文档管理系统 - 通用部署指南

## 🚀 一键部署（推荐）

### Windows 服务器
```bash
# 1. 下载系统代码到服务器
# 2. 运行通用启动脚本
start-production-universal.bat

# 可选：指定IP地址
start-production-universal.bat 192.168.1.100
```

### Linux/Unix 服务器  
```bash
# 1. 下载系统代码到服务器
# 2. 给脚本执行权限
chmod +x start-production-universal.sh

# 3. 运行启动脚本
./start-production-universal.sh

# 可选：指定IP地址
./start-production-universal.sh 192.168.1.100
```

## 🔧 手动部署

### 1. 环境要求检查
```bash
# Python 3.8+
python --version

# Node.js 16+
node --version

# 可选：LibreOffice（文档内容提取）
soffice --version
```

### 2. 复制通用配置
```bash
# 复制后端配置
cp .env.universal backend/.env

# 复制前端配置  
cp frontend/.env.universal frontend/.env
```

### 3. 修改关键配置
编辑 `backend/.env`：
```bash
# 修改安全密钥（必须！）
SECRET_KEY=your-unique-secret-key-here

# 可选：指定CORS源
CORS_ORIGINS=http://192.168.1.100:5173,http://192.168.1.100:5174
```

### 4. 安装依赖和构建
```bash
# 安装后端依赖
cd backend && pip install -r requirements.txt

# 安装前端依赖并构建
cd ../frontend && npm install && npm run build
```

### 5. 启动服务
```bash
# 启动后端（后台运行）
cd backend && nohup python database_integrated_server.py &

# 启动前端（开发服务器）
cd frontend && npm run dev
```

## 🌐 网络配置说明

### 自动IP检测
系统会自动检测服务器IP地址并配置CORS，支持：
- 本地访问：`http://localhost:5173`
- 局域网访问：`http://服务器IP:5173`

### CORS配置详解

系统提供了灵活的CORS配置模式，完全通过环境变量控制：

#### 🔧 配置模式

**1. 自动模式（推荐）**
```bash
# 自动检测本机IP并配置CORS
CORS_MODE=auto
CORS_AUTO_DETECT=true
CORS_INCLUDE_LOCALHOST=true
```

**2. 手动模式**  
```bash
# 仅使用指定的地址
CORS_MODE=manual
CORS_ORIGINS=http://192.168.1.100:5173,http://192.168.1.100:5174,https://mydomain.com
```

**3. 开发模式**
```bash
# 允许所有来源（仅开发环境）
CORS_MODE=dev
```

#### 🛠️ 配置方式

**方式1：启动时指定IP（推荐）**
```bash
# Windows
start-production-universal.bat 192.168.1.100

# Linux
./start-production-universal.sh 192.168.1.100
```
脚本会自动设置 `CORS_MODE=auto` 并包含指定IP

**方式2：环境变量配置**
```bash
# 完全手动控制
export CORS_MODE=manual
export CORS_ORIGINS=http://192.168.1.100:5173,http://192.168.1.100:5174

# 或者自动+手动组合
export CORS_MODE=auto
export CORS_ORIGINS=https://mydomain.com  # 额外添加域名
export CORS_AUTO_DETECT=true
```

**方式3：配置文件指定**
编辑 `backend/.env`：
```env
CORS_MODE=manual
CORS_ORIGINS=http://192.168.1.100:5173,http://192.168.1.100:5174
CORS_AUTO_DETECT=false
CORS_INCLUDE_LOCALHOST=true
CORS_INCLUDE_HTTPS=true
CORS_EXTRA_PORTS=3000,8080,9000
```

#### 🔍 配置参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `CORS_MODE` | `auto` | 配置模式：auto/manual/dev |
| `CORS_ORIGINS` | `""` | 手动指定的源（逗号分隔） |
| `CORS_AUTO_DETECT` | `true` | 是否自动检测IP |
| `CORS_INCLUDE_LOCALHOST` | `true` | 是否包含localhost |
| `CORS_INCLUDE_HTTPS` | `true` | 是否包含HTTPS变体 |
| `CORS_EXTRA_PORTS` | `3000,8080,9000` | 额外端口 |

## 🔒 安全配置

### 生产环境必改项
1. **SECRET_KEY**: 修改为随机字符串
2. **DEBUG**: 设为 false
3. **CORS_MODE**: 生产环境建议使用 `manual` 模式
4. **CORS_ORIGINS**: 只允许必要的域名，避免使用 `dev` 模式
5. **默认密码**: 首次登录后立即修改

#### 🔐 生产环境CORS配置示例
```env
# 生产环境安全配置
CORS_MODE=manual
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
CORS_AUTO_DETECT=false
CORS_INCLUDE_LOCALHOST=false
CORS_INCLUDE_HTTPS=true
```

### 防火墙配置
确保开放必要端口：
```bash
# Linux (firewalld)
firewall-cmd --add-port=8002/tcp --permanent
firewall-cmd --add-port=5173/tcp --permanent
firewall-cmd --reload

# Linux (ufw)
ufw allow 8002
ufw allow 5173

# Windows
netsh advfirewall firewall add rule name="Backend" dir=in port=8002 protocol=tcp action=allow
netsh advfirewall firewall add rule name="Frontend" dir=in port=5173 protocol=tcp action=allow
```

## 📊 监控和日志

### 查看服务状态
```bash
# 查看进程
ps aux | grep python
ps aux | grep node

# Windows
tasklist | findstr python
tasklist | findstr node
```

### 查看日志
```bash
# 后端日志
tail -f logs/backend.log

# 前端日志  
tail -f logs/frontend.log

# Windows
type logs\backend.log
type logs\frontend.log
```

### 停止服务
```bash
# Linux
./stop-production.sh

# Windows  
stop-production.bat

# 手动停止
kill $(cat backend.pid)
kill $(cat frontend.pid)
```

## 🛠️ 故障排除

### 常见问题

**Q: "Failed to fetch" 错误**
A: 检查：
1. 后端服务是否启动 (端口8002)
2. CORS配置是否包含访问来源
3. 防火墙是否开放端口
4. IP地址是否正确

**Q: 无法从其他电脑访问**
A: 检查：
1. 服务器host设置为 `0.0.0.0`
2. CORS包含客户端IP
3. 网络连通性 (`ping 服务器IP`)
4. 防火墙配置

**Q: 文档内容无法提取**
A: 安装LibreOffice：
```bash
# Ubuntu/Debian
sudo apt install libreoffice

# CentOS/RHEL
sudo yum install libreoffice

# Windows
# 访问 https://www.libreoffice.org/download/
```

### 测试连接
```bash
# 测试后端API
curl http://服务器IP:8002/api/v1/

# 测试前端页面
curl -I http://服务器IP:5173/

# 从其他电脑测试
ping 服务器IP
telnet 服务器IP 8002
```

## 📋 部署检查清单

- [ ] Python 3.8+ 已安装
- [ ] Node.js 16+ 已安装  
- [ ] 复制并修改配置文件
- [ ] 修改SECRET_KEY
- [ ] 安装所有依赖
- [ ] 构建前端应用
- [ ] 启动后端服务 (端口8002)
- [ ] 启动前端服务 (端口5173)
- [ ] 测试本地访问
- [ ] 测试远程访问
- [ ] 修改默认密码
- [ ] 配置防火墙
- [ ] 设置服务自启动（可选）

## 🔄 版本更新

```bash
# 拉取最新代码
git pull origin main

# 更新依赖
cd backend && pip install -r requirements.txt
cd frontend && npm install

# 重新构建和重启
npm run build
./restart-services.sh
```

---

💡 **提示**: 使用通用启动脚本可以自动处理大部分配置，适合快速部署和测试环境。