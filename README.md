# 润扬大桥运维文档管理系统

<div align="center">

![Logo](./frontend/public/runyang-logo.svg)

**智慧高速 · 匠心运维**

一个专为润扬大桥设计的现代化运维文档和资产管理平台

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.5+-brightgreen.svg)](https://vuejs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-red.svg)](https://fastapi.tiangolo.com)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8+-blue.svg)](https://typescriptlang.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[快速开始](#快速开始) • [功能特性](#功能特性) • [技术栈](#技术栈) • [API文档](#api文档) • [贡献指南](#贡献指南)

</div>

---

## 🚀 快速开始

### 系统要求
- **Python**: 3.8+ (推荐 3.9+)
- **Node.js**: 16+ (推荐 LTS 版本)
- **操作系统**: Windows 10+, macOS 10.15+, Ubuntu 18.04+
- **内存**: 4GB RAM (推荐 8GB+)
- **存储**: 10GB 可用空间

### 一键启动
```bash
# Windows 用户
start-services.bat

# Linux/macOS 用户
./start-services.sh
```

### 手动安装
```bash
# 1. 克隆项目
git clone https://github.com/heartsward/runyang-bridge-docs-system.git
cd runyang-bridge-docs-system

# 2. 安装后端依赖
cd backend
pip install -r requirements-windows.txt  # Windows
pip install -r requirements.txt          # Linux/macOS

# 3. 安装前端依赖
cd ../frontend
npm install

# 4. 启动后端服务 (端口: 8002)
cd ../backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload

# 5. 启动前端服务 (端口: 5173)
cd ../frontend
npm run dev
```

### 访问地址
- **前端界面**: http://localhost:5173
- **后端API**: http://localhost:8002
- **API文档**: http://localhost:8002/docs
- **交互式API**: http://localhost:8002/redoc

### 默认账户
- **管理员**: `admin` / `admin123`
- **普通用户**: 通过管理员创建

---

## ✨ 功能特性

### 📚 智能文档管理
- **多格式支持**: PDF、Word、Excel、文本、Markdown、图片等格式
- **智能OCR**: 自动识别扫描文档和图片中的文字
- **内容提取**: 自动提取文档内容用于全文搜索
- **在线预览**: 支持文档在线预览和下载
- **批量操作**: 支持批量上传、管理和分类
- **版本控制**: 文档版本历史和变更追踪

### 🔍 高效搜索系统
- **全文搜索**: 基于文档完整内容的智能搜索
- **权重排序**: 内容 > 标题 > 描述的智能排序算法
- **高亮显示**: 搜索结果关键词高亮
- **搜索建议**: 基于历史的智能搜索推荐
- **多维筛选**: 支持文档类型、上传时间等多维度筛选
- **搜索统计**: 搜索行为数据分析和统计

### 🖥️ 设备资产管理
- **全面设备管理**: 服务器、网络设备、存储设备、安全设备等
- **状态监控**: 设备运行状态、维护记录和生命周期管理
- **智能提取**: 从文档自动识别和提取设备信息
- **排序筛选**: 支持按设备类型、部门、网络位置、更新时间等排序
- **批量操作**: 支持批量导入、导出和删除
- **数据导出**: Excel/CSV 格式的详细数据导出
- **统计报表**: 资产分布、使用情况和成本分析

### 👥 用户权限管理
- **角色权限**: 超级管理员和普通用户的分级权限
- **用户管理**: 完整的用户信息管理和密码修改
- **访问控制**: 基于角色的功能访问控制
- **安全认证**: JWT Token 自动过期和密码 Bcrypt 加密
- **操作审计**: 关键操作日志记录和追踪

### 📊 数据分析与统计
- **使用统计**: 文档访问量、搜索热词、用户活跃度
- **资产统计**: 设备分布、状态统计、部门资产概览
- **可视化图表**: 数据趋势图和分布统计
- **性能监控**: 系统性能指标和使用情况
- **智能报表**: 自定义统计维度和导出功能

### 📱 移动端支持
- **Android 应用**: 完整的 Android 客户端 (开发中)
- **响应式设计**: Web 界面适配移动设备
- **触控优化**: 移动端交互体验优化
- **离线功能**: 文档下载和离线浏览 (规划中)

---

## 🏗️ 技术栈

### 前端技术
```
Vue 3 + TypeScript + Vite
├── UI 组件库: Naive UI 2.42+
├── 状态管理: Pinia
├── 路由管理: Vue Router 4
├── HTTP 客户端: Axios
├── 图标库: @vicons (Ionicons5 + Antd)
├── 类型检查: TypeScript 5.8+
└── 构建工具: Vite 7.0+
```

### 后端技术
```
FastAPI + Python 3.8+
├── ORM 框架: SQLAlchemy 2.0
├── 数据库: SQLite (生产可扩展至 PostgreSQL)
├── 认证系统: JWT + Bcrypt
├── 文档处理: PyPDF2, python-docx, openpyxl
├── OCR 引擎: Tesseract (可选)
├── Web 服务器: Uvicorn (ASGI)
├── 异步处理: AsyncIO
└── 数据验证: Pydantic V2
```

### 移动端技术 (Android)
```
Kotlin + Jetpack Compose
├── 架构模式: MVVM + Clean Architecture
├── 依赖注入: Dagger Hilt
├── 网络请求: Retrofit + OkHttp
├── 本地存储: Room Database
├── 响应式编程: Coroutines + Flow
└── UI 组件: Material Design 3
```

### 数据存储架构
```
多层数据持久化
├── 关系数据: SQLite 数据库 (用户、文档、资产元数据)
├── 文件存储: 本地文件系统 (文档原件和提取内容)
├── 配置存储: JSON 配置文件
├── 缓存数据: 内存缓存 (搜索结果、热点数据)
├── 会话数据: JWT Token (无状态认证)
└── 日志数据: 结构化日志文件
```

---

## 📋 项目结构

```
runyang-bridge-docs-system/
├── backend/                   # 后端 FastAPI 应用
│   ├── app/
│   │   ├── api/              # API 路由和端点
│   │   │   └── endpoints/    # 具体 API 端点
│   │   ├── core/             # 核心配置和工具
│   │   ├── crud/             # 数据库 CRUD 操作
│   │   ├── models/           # SQLAlchemy 数据模型
│   │   ├── schemas/          # Pydantic 数据模式
│   │   ├── services/         # 业务逻辑服务
│   │   └── utils/            # 工具函数
│   ├── uploads/              # 上传文件存储
│   ├── task_status/          # 后台任务状态
│   └── requirements*.txt     # Python 依赖
├── frontend/                  # 前端 Vue.js 应用
│   ├── src/
│   │   ├── components/       # Vue 组件
│   │   ├── views/            # 页面视图
│   │   ├── services/         # API 服务
│   │   ├── types/            # TypeScript 类型定义
│   │   └── router/           # 路由配置
│   ├── public/               # 静态资源
│   └── package.json          # Node.js 依赖
├── android/                   # Android 应用 (开发中)
│   ├── app/src/main/
│   │   ├── java/             # Kotlin 源代码
│   │   └── res/              # Android 资源
│   └── build.gradle.kts      # Android 构建配置
├── docs/                      # 项目文档
├── logs/                      # 应用日志
├── backups/                   # 数据备份
├── start-services.bat         # Windows 启动脚本
└── README.md                  # 项目说明
```

---

## 🔧 配置说明

### 后端配置
```python
# backend/app/core/config.py
class Settings:
    PROJECT_NAME = "润扬大桥运维文档管理系统"
    VERSION = "2.0.0"
    API_V1_STR = "/api/v1"
    
    # 数据库配置
    DATABASE_URL = "sqlite:///./yunwei_docs.db"
    
    # JWT 配置
    SECRET_KEY = "your-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 小时
    
    # 文件上传配置
    MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = [".pdf", ".doc", ".docx", ".xlsx", ".xls", ".txt", ".md"]
    
    # CORS 配置
    CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
```

### 前端配置
```typescript
// frontend/src/services/api.ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002'
const API_VERSION = '/api/v1'
```

---

## 📖 API 文档

### 认证接口
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/logout` - 用户登出  
- `GET /api/v1/auth/me` - 获取当前用户信息

### 文档管理接口
- `GET /api/v1/documents/` - 获取文档列表
- `POST /api/v1/documents/` - 创建文档
- `PUT /api/v1/documents/{id}` - 更新文档
- `DELETE /api/v1/documents/{id}` - 删除文档
- `GET /api/v1/documents/{id}/content` - 获取文档内容

### 资产管理接口
- `GET /api/v1/assets/` - 获取资产列表 (支持排序和筛选)
- `POST /api/v1/assets/` - 创建资产
- `PUT /api/v1/assets/{id}` - 更新资产
- `DELETE /api/v1/assets/{id}` - 删除资产
- `POST /api/v1/assets/batch/delete` - 批量删除资产
- `POST /api/v1/assets/export` - 导出资产数据
- `POST /api/v1/assets/file-extract` - 从文件提取资产

### 搜索接口
- `GET /api/v1/search/` - 全文搜索
- `GET /api/v1/search/suggestions` - 搜索建议

### 用户管理接口 (管理员)
- `GET /api/v1/settings/users` - 获取用户列表
- `POST /api/v1/settings/users` - 创建用户
- `PUT /api/v1/settings/users/{id}` - 更新用户 (包括密码修改)
- `DELETE /api/v1/settings/users/{id}` - 删除用户

详细的 API 文档请访问: http://localhost:8002/docs

---

## 🔒 安全特性

### 身份认证和授权
- **JWT Token**: 24小时自动过期，支持刷新机制
- **密码安全**: Bcrypt 哈希存储，强密码策略
- **角色权限**: 基于角色的访问控制 (RBAC)
- **会话管理**: 无状态Token认证，支持多设备登录

### 数据安全
- **输入验证**: 严格的参数验证和类型检查
- **文件安全**: 文件类型白名单和大小限制
- **SQL 防护**: SQLAlchemy ORM 防止 SQL 注入
- **XSS 防护**: 输入输出过滤和 HTML 转义

### 系统安全
- **错误处理**: 统一异常处理，避免敏感信息泄露
- **日志审计**: 关键操作记录和审计跟踪
- **CORS 配置**: 严格的跨域访问控制
- **数据备份**: 定期自动备份重要数据

---

## 🚀 部署指南

### 开发环境部署
```bash
# 1. 启动开发服务
start-services.bat  # Windows
./start-services.sh # Linux/macOS

# 2. 访问应用
# 前端: http://localhost:5173
# 后端: http://localhost:8002
```

### 生产环境部署
```bash
# 1. 构建前端
cd frontend
npm run build

# 2. 配置 Nginx (推荐)
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        try_files $uri $uri/ /index.html;
        root /path/to/frontend/dist;
    }
    
    location /api {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# 3. 使用 Gunicorn 运行后端
cd backend
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Docker 部署 (规划中)
```dockerfile
# 多阶段构建支持
FROM node:16 AS frontend-builder
FROM python:3.9 AS backend-runtime
# ... Docker 配置
```

---

## 📊 系统性能

### 处理能力指标
- **文档上传**: 单文件最大 10MB，支持 8+ 种格式
- **并发用户**: 支持 100+ 用户同时在线
- **搜索性能**: 平均响应时间 < 300ms
- **数据容量**: 支持 10,000+ 文档和 5,000+ 资产
- **文件处理**: 异步处理，不阻塞用户界面

### 性能优化特性
- **异步处理**: 文档解析和 OCR 异步执行
- **智能缓存**: 热点数据内存缓存机制
- **分页查询**: 大数据集自动分页处理
- **懒加载**: 前端组件和数据按需加载
- **代码分割**: 前端资源按路由分割
- **数据库优化**: 索引优化和查询性能调优

---

## 🎯 应用场景

### 运维文档知识库
- **技术文档**: 系统架构、配置手册、操作规范
- **故障手册**: 故障处理流程、解决方案知识库
- **维护记录**: 设备维护日志、系统更新记录
- **培训资料**: 新员工培训、技能提升材料

### 设备资产管理
- **设备档案**: 服务器、网络设备、安全设备信息
- **状态监控**: 设备运行状态、告警信息、性能指标
- **维护计划**: 设备保养计划、维护提醒、生命周期管理
- **成本分析**: 采购成本、维护成本、ROI 分析

### 智能运维分析
- **使用分析**: 文档访问热度、用户行为模式
- **趋势预测**: 设备故障预测、维护需求分析
- **效率优化**: 运维流程优化建议、自动化推荐
- **决策支持**: 数据驱动的运维决策支持

---

## 🔄 版本更新

### v2.0.0 (最新版本)
- ✅ **重大更新**: 完整重构资产管理模块
- ✅ **新功能**: 添加资产排序和筛选功能
- ✅ **修复**: 用户密码修改功能修复
- ✅ **优化**: 前端界面响应式设计改进
- ✅ **安全**: 加强 JWT 认证和密码安全

### v1.5.0
- ✅ **新功能**: OCR 文档识别功能
- ✅ **新功能**: 移动端 Android 应用框架
- ✅ **优化**: 搜索性能和准确性提升
- ✅ **修复**: 批量文件上传稳定性

### v1.0.0
- ✅ **核心功能**: 文档管理和搜索系统
- ✅ **基础功能**: 用户权限和认证系统
- ✅ **初始功能**: 资产管理基础功能

查看完整的 [版本更新日志](./docs/版本更新日志.md)

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！请阅读我们的 [贡献指南](./CONTRIBUTING.md) 了解详情。

### 如何贡献
1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 开发规范
- 遵循项目代码风格和规范
- 编写必要的测试用例
- 更新相关文档
- 提交清晰的 commit 信息

### 报告问题
- 使用 [Issues](https://github.com/heartsward/runyang-bridge-docs-system/issues) 报告 Bug
- 提供详细的复现步骤和环境信息
- 使用合适的标签分类问题

---

## 📞 技术支持

### 获取帮助
- 📖 **[用户手册](./docs/用户操作手册.md)** - 详细的功能使用指南
- 🏗️ **[开发文档](./docs/开发者文档.md)** - 技术实现和 API 文档
- ❓ **[常见问题](./docs/FAQ.md)** - 快速解决常见问题
- 🔄 **[更新日志](./docs/版本更新日志.md)** - 版本历史和更新内容

### 联系方式
- 📧 **项目仓库**: [GitHub Issues](https://github.com/heartsward/runyang-bridge-docs-system/issues)
- 💬 **功能建议**: [GitHub Discussions](https://github.com/heartsward/runyang-bridge-docs-system/discussions)
- 🐛 **Bug 报告**: [GitHub Issues](https://github.com/heartsward/runyang-bridge-docs-system/issues/new?template=bug_report.md)

---

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源。

---

## 🙏 致谢

感谢以下开源项目和技术的支持:

- [Vue.js](https://vuejs.org) - 渐进式 JavaScript 框架
- [FastAPI](https://fastapi.tiangolo.com) - 现代、快速的 Web 框架
- [Naive UI](https://www.naiveui.com) - Vue 3 组件库  
- [SQLAlchemy](https://www.sqlalchemy.org) - Python SQL 工具包
- [TypeScript](https://www.typescriptlang.org) - JavaScript 类型超集
- [Vite](https://vitejs.dev) - 下一代前端工具

---

<div align="center">

**润扬大桥运维文档管理系统** © 2024

**智慧高速 · 匠心运维**

*让运维管理更智能，让数据应用更高效*

[![GitHub stars](https://img.shields.io/github/stars/heartsward/runyang-bridge-docs-system?style=social)](https://github.com/heartsward/runyang-bridge-docs-system)
[![GitHub forks](https://img.shields.io/github/forks/heartsward/runyang-bridge-docs-system?style=social)](https://github.com/heartsward/runyang-bridge-docs-system)

</div>