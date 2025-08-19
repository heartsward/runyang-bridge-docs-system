# 润扬大桥运维文档管理系统

<div align="center">

**智慧高速 · 匠心运维**

一个专为润扬大桥设计的现代化运维文档管理平台

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js-16+-green.svg)](https://nodejs.org)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.0-brightgreen.svg)](https://vuejs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-red.svg)](https://fastapi.tiangolo.com)

</div>

## 🌟 系统特性

### 核心功能
- 📄 **智能文档管理** - 支持多格式文档上传、预览、分类管理
- 🔍 **全文智能搜索** - 基于内容的智能搜索，支持关键词高亮
- 🏗️ **设备资产管理** - 完整的资产生命周期管理
- 📊 **数据分析面板** - 用户行为分析、使用统计、AI智能建议
- 👥 **用户权限管理** - 基于角色的访问控制
- 🔒 **安全认证** - JWT身份验证、密码加密存储

### 技术特色
- 🚀 **高性能架构** - 异步处理、智能缓存
- 📱 **响应式设计** - 支持多终端设备访问
- 🔄 **实时同步** - 数据持久化、状态实时更新
- 🎨 **现代UI设计** - 基于Naive UI的美观界面

## 🛠️ 技术栈

### 后端技术
- **框架**: FastAPI + SQLAlchemy + Alembic
- **数据库**: SQLite (可扩展至PostgreSQL/MySQL)
- **认证**: JWT + Bcrypt密码加密
- **文档处理**: PyPDF2 + python-docx + openpyxl
- **异步任务**: 内置任务队列系统

### 前端技术
- **框架**: Vue 3 + TypeScript + Vite
- **UI组件**: Naive UI
- **状态管理**: Composition API
- **图标**: @vicons/ionicons5 + @vicons/antd
- **HTTP客户端**: Axios

## 📋 系统要求

### 最低配置
- **操作系统**: Windows 10/11, Ubuntu 18.04+, CentOS 7+, macOS 10.15+
- **Python**: 3.8 或更高版本
- **Node.js**: 16 或更高版本
- **LibreOffice**: 最新版本 (用于文档内容提取)
- **内存**: 4GB RAM
- **存储**: 10GB 可用空间

### 推荐配置
- **内存**: 8GB+ RAM
- **存储**: 20GB+ 可用空间
- **网络**: 稳定的网络连接

## 🚀 快速部署

### 方式一：一键部署 (推荐)

#### Windows
```bash
# 1. 克隆项目
git clone https://github.com/heartsward/runyang-bridge-docs-system.git
cd runyang-bridge-docs-system

# 2. 安装环境依赖
install-environment.bat

# 3. 启动服务
start-services.bat
```

#### Linux/macOS
```bash
# 1. 克隆项目
git clone https://github.com/heartsward/runyang-bridge-docs-system.git
cd runyang-bridge-docs-system

# 2. 安装环境依赖
./install-environment.sh

# 3. 启动服务
./start-services.sh
```

### 方式二：手动部署

如果需要自定义配置，可以手动部署：

#### 1. 环境准备
```bash
# 1. 安装Python依赖
cd backend
pip install -r requirements.txt

# 2. 安装Node.js依赖  
cd ../frontend
npm install

# 3. 安装LibreOffice (用于文档内容提取)
# Windows: https://www.libreoffice.org/download/download/
# Ubuntu/Debian: sudo apt install libreoffice
# CentOS/RHEL: sudo yum install libreoffice
# macOS: brew install --cask libreoffice
```

#### 2. 手动启动服务
```bash
# 启动后端服务 (端口8002)
cd backend  
python database_integrated_server.py

# 启动前端服务 (端口5173) - 在新终端中运行
cd frontend
npm run dev
```

#### 3. 停止服务
```bash
# Windows
stop-services.bat

# Linux/macOS  
./stop-services.sh
```

## 👤 默认用户

系统预置管理员账户：
- **用户名**: `admin`
- **密码**: `admin123`
- **权限**: 系统管理员

首次登录后请立即修改默认密码。

## ⚠️ 重要提醒

**LibreOffice依赖**: 系统需要LibreOffice来提取Word、Excel等文档的文本内容用于搜索。

- 如果启动脚本提示缺少LibreOffice，请按提示安装
- 详细安装指南：[INSTALL_LIBREOFFICE.md](./INSTALL_LIBREOFFICE.md)
- 没有LibreOffice时系统仍可运行，但文档内容提取功能将受限

## 🔒 安全说明

- 所有API接口都有身份验证保护
- 密码使用bcrypt加密存储
- JWT Token自动过期机制
- 文件上传类型和大小限制
- SQL注入防护
- XSS攻击防护

## 📊 性能特性

- 异步文档处理，不阻塞主线程
- 智能缓存机制，提升访问速度
- 分页查询，处理大量数据
- 文件压缩和优化
- 数据库索引优化

## 🆘 故障排除

### 常见问题

**Q: 服务启动失败**
A: 检查端口占用、Python版本、依赖安装

**Q: 文档上传失败**
A: 检查文件格式、大小限制、存储空间

**Q: 搜索结果为空**
A: 确认文档内容已提取、搜索关键词正确

**Q: 前端无法连接后端**
A: 检查API地址配置、CORS设置、防火墙

---

<div align="center">

## 📦 GitHub部署

### 创建GitHub仓库
1. 在GitHub创建新仓库：`runyang-bridge-docs-system`
2. 将本地代码推送到GitHub：
```bash
git remote add origin https://github.com/[your-username]/runyang-bridge-docs-system.git
git branch -M main
git push -u origin main
```

### 克隆部署
其他服务器可直接克隆部署：
```bash
git clone https://github.com/[your-username]/runyang-bridge-docs-system.git
cd runyang-bridge-docs-system
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# 编辑配置文件后执行启动脚本
```

### 🔄 版本更新

#### 自动化更新 (推荐)
```bash
# 生产服务器安全更新
Windows: deploy-update.bat
Linux:   ./deploy-update.sh

# 开发端版本发布
Windows: update-version.bat  
Linux:   ./update-version.sh

# 配置变更检测
Windows: check-config-changes.bat
Linux:   ./check-config-changes.sh

# 服务健康检查  
Windows: check-service-health.bat
Linux:   ./check-service-health.sh
```

#### 手动更新
```bash
git pull origin main  # 拉取最新代码
# 重启服务应用更新
```

**详细说明**: 参见 [VERSION_UPDATE_GUIDE.md](./VERSION_UPDATE_GUIDE.md)

---

<div align="center">

**润扬大桥运维文档管理系统** © 2024

智慧高速 · 匠心运维

</div>
