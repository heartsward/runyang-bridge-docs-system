# GitHub部署指南

> ⚠️ **文档时效提示（2026-09-14 里程碑体检）**：本文撰写于早期架构阶段，其中提到的 `backend/database_integrated_server.py` 入口与 `start-production*` / `restart-services` 等脚本**已不存在**。
> 当前真实后端入口为 **`uvicorn app.main:app`（端口 8002，FastAPI）**；服务脚本请用仓库根目录的 **`start-services.*` / `stop-services.*` / `install-complete.bat`**。
> 权威参考：[README](../README.md)、[生产环境脚本说明](生产环境脚本说明.md)、[AI-Wiki-MCP调用文档](AI-Wiki-MCP调用文档.md)。下文涉及上述文件处请按此口径理解。

## 📦 将项目上传到GitHub

### 1. 创建GitHub仓库
1. 登录GitHub，点击右上角的 "+" 号
2. 选择 "New repository"
3. 仓库名称建议：`runyang-bridge-docs-system`
4. 选择 "Public" 或 "Private"（根据需要）
5. **不要**勾选 "Add a README file"（项目已有README）
6. 点击 "Create repository"

### 2. 推送代码到GitHub
在项目根目录执行以下命令：

```bash
# 添加远程仓库（替换为你的GitHub用户名）
git remote add origin https://github.com/[your-username]/runyang-bridge-docs-system.git

# 添加所有文件到暂存区
git add .

# 创建首次提交
git commit -m "feat: 初始化润扬大桥运维文档管理系统

- 完整的前后端代码结构
- Vue 3 + FastAPI 技术栈
- 文档管理、资产管理、智能搜索功能
- 用户认证和权限管理
- 数据分析和AI智能建议
- 跨平台一键启动脚本
- 完整的系统文档
- 智能内容提取（anydoc 统一引擎）

🚀 Generated with Claude Code"

# 推送到GitHub（首次推送）
git branch -M main
git push -u origin main
```

## 🚀 从GitHub部署

### Windows部署
```bash
# 1. 克隆项目
git clone https://github.com/[your-username]/runyang-bridge-docs-system.git
cd runyang-bridge-docs-system

# 2. 复制环境配置并编辑
copy backend\.env.example backend\.env
copy frontend\.env.example frontend\.env
# 重要：编辑 .env 文件，修改 SECRET_KEY 等配置

# 3. 一键启动
start-production.bat
```

### Linux/macOS部署
```bash
# 1. 克隆项目
git clone https://github.com/[your-username]/runyang-bridge-docs-system.git
cd runyang-bridge-docs-system

# 2. 复制环境配置并编辑
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# 重要：编辑 .env 文件，修改 SECRET_KEY 等配置

# 3. 一键启动
chmod +x start-production.sh
./start-production.sh
```

## 🔒 安全配置必须修改

### 1. 生成新的SECRET_KEY
```bash
# 方法1：使用Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 方法2：使用OpenSSL
openssl rand -base64 32
```

### 2. 编辑配置文件
编辑 `backend/.env`：
```bash
# 替换为上面生成的密钥
SECRET_KEY=your-new-generated-secret-key-here

# 根据需要修改数据库配置
DATABASE_URL=sqlite:///./yunwei_docs.db

# 修改CORS设置（如果前后端不在同一服务器）
CORS_ORIGINS=http://your-domain.com:5173,http://localhost:5173
```

编辑 `frontend/.env`：
```bash
# 修改API地址（如果后端在不同服务器）
VITE_API_BASE_URL=http://your-backend-server:8002
```

## 📋 部署检查清单

### 部署前检查
- [ ] 已安装Python 3.8+
- [ ] 已安装Node.js 16+
- [ ] 已安装 anydoc（pip install firecrawl-anydoc）
- [ ] 已修改SECRET_KEY为安全的随机值
- [ ] 已配置正确的API地址和CORS设置
- [ ] 已设置防火墙规则（开放5173和8002端口）

### 部署后验证
- [ ] 前端页面能正常访问 (http://localhost:5173)
- [ ] 后端API能正常访问 (http://localhost:8002)
- [ ] 能正常登录系统（admin/admin123）
- [ ] 能正常上传和搜索文档
- [ ] 文档内容提取功能正常（anydoc 自动接管所有格式）

## 🔄 版本更新管理

### 📦 开发端版本发布 (代码提交者使用)

#### 自动化版本发布脚本 (推荐)
```bash
# Windows
update-version.bat

# Linux/macOS  
chmod +x update-version.sh
./update-version.sh
```

**脚本功能**:
- ✅ 自动检查Git状态和网络连接
- ✅ 智能版本类型选择 (补丁/功能/重大)
- ✅ 自动创建版本标签 (v1.0.x 格式)
- ✅ 一键提交并推送到GitHub
- ✅ 生成标准化提交信息

#### 手动版本发布流程
```bash
# 1. 检查当前状态
git status
git pull origin main

# 2. 添加所有更改
git add .

# 3. 创建提交 (标准格式)
git commit -m "feat: 描述本次更新内容

- 补丁/功能/重大版本更新
- 系统功能优化和bug修复
- 文档和配置更新

🚀 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# 4. 创建版本标签
git tag -a v1.0.x -m "版本描述"

# 5. 推送到GitHub
git push origin main
git push origin v1.0.x
```

---

### 🚀 生产端安全更新 (部署服务器使用)

#### 自动化安全更新脚本 (推荐)
```bash
# Windows
deploy-update.bat

# Linux/macOS
chmod +x deploy-update.sh  
./deploy-update.sh
```

**脚本功能**:
- ✅ 网络连接和仓库状态检查
- ✅ 自动配置文件备份保护
- ✅ 优雅的服务停止和启动
- ✅ 配置变更检测和提醒
- ✅ 服务状态验证
- ✅ 失败自动回滚机制

#### 手动安全更新流程
```bash
# 1. 停止服务
./stop-services.sh  # 或 stop-services.bat

# 2. 备份重要文件
mkdir backup_$(date +%Y%m%d_%H%M%S)
cp backend/.env frontend/.env *.db backup_*/

# 3. 拉取最新代码
git fetch origin
git pull origin main

# 4. 检查配置文件变更
git diff HEAD~1 backend/.env.example
git diff HEAD~1 frontend/.env.example

# 5. 更新依赖（如有变化）
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# 6. 重新启动服务
./start-production.sh  # 或 start-production.bat

# 7. 验证服务状态
curl http://localhost:8002/health
curl http://localhost:5173
```

---

### 🔙 版本回退机制

#### 快速回滚 (紧急情况)
```bash
# 查看最近提交历史
git log --oneline -10

# 回滚到上一个版本
git reset --hard HEAD~1

# 重新启动服务  
./start-production.sh
```

#### 指定版本回滚
```bash
# 查看所有版本标签
git tag -l

# 回滚到指定标签版本
git checkout v1.0.5

# 如果需要创建新分支
git checkout -b rollback-v1.0.5

# 重新启动服务
./start-production.sh
```

#### 恢复备份配置
```bash
# 查看备份目录
ls backup_*/

# 恢复配置文件
cp backup_YYYYMMDD_HHMMSS/backend.env.backup backend/.env
cp backup_YYYYMMDD_HHMMSS/frontend.env.backup frontend/.env

# 恢复数据库 (如果需要)
cp backup_YYYYMMDD_HHMMSS/database.backup yunwei_docs.db
```

---

### 📊 版本更新最佳实践

#### 开发端最佳实践
1. **版本类型选择**:
   - `patch`: Bug修复、小优化
   - `minor`: 新功能、功能增强  
   - `major`: 重大架构变更、破坏性更新

2. **提交信息规范**:
   - 使用清晰的中文描述
   - 包含变更类型和影响范围
   - 遵循Git提交信息最佳实践

3. **发布前检查**:
   - 确保本地测试通过
   - 检查是否有遗漏的配置文件
   - 验证依赖包版本兼容性

#### 生产端最佳实践
1. **更新时机选择**:
   - 选择业务低峰期进行更新
   - 预留充足的回滚时间窗口
   - 提前通知相关用户

2. **安全措施**:
   - 始终创建配置和数据备份
   - 验证服务启动状态
   - 监控系统运行指标

3. **应急预案**:
   - 准备快速回滚方案
   - 保持备份文件的完整性
   - 建立问题上报机制

---

### 🔍 更新故障排除

#### 常见问题及解决方案

**1. 代码拉取失败**
```bash
# 检查网络连接
ping github.com

# 检查远程仓库配置
git remote -v

# 重置本地更改后重试
git stash && git pull origin main
```

**2. 服务启动失败**
```bash  
# 检查端口占用
netstat -tlnp | grep :8002
netstat -tlnp | grep :5173

# 查看服务日志
tail -f logs/backend.log
tail -f logs/frontend.log

# 手动启动调试
cd backend && python database_integrated_server.py
cd frontend && npm run dev
```

**3. 配置文件冲突**
```bash
# 对比配置差异
git diff backend/.env.example backend/.env
git diff frontend/.env.example frontend/.env

# 手动合并配置
# 编辑 .env 文件，添加新的配置项
```

**4. 依赖包更新失败**
```bash
# 清理并重新安装 Python 依赖
cd backend && pip cache purge && pip install -r requirements.txt

# 清理并重新安装 Node.js 依赖  
cd frontend && rm -rf node_modules && npm install
```

## 🌐 生产环境优化

### 1. 使用PostgreSQL数据库
```bash
# 安装PostgreSQL
sudo apt install postgresql postgresql-contrib  # Ubuntu
brew install postgresql  # macOS

# 创建数据库
sudo -u postgres createdb yunwei_docs

# 修改backend/.env
DATABASE_URL=postgresql://username:password@localhost:5432/yunwei_docs
```

### 2. 使用Nginx反向代理
创建 `/etc/nginx/sites-available/yunwei-docs`：
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/project/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # 后端API
    location /api/ {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 文档下载
    location /docs/ {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. 使用PM2进行进程管理
```bash
# 安装PM2
npm install -g pm2

# 创建启动配置 ecosystem.config.js
module.exports = {
  apps: [
    {
      name: 'yunwei-backend',
      cwd: './backend',
      script: 'python',
      args: 'database_integrated_server.py',
      interpreter: 'none'
    },
    {
      name: 'yunwei-frontend',
      cwd: './frontend',
      script: 'npm',
      args: 'run preview',
      interpreter: 'none'
    }
  ]
};

# 启动服务
pm2 start ecosystem.config.js

# 设置开机启动
pm2 startup
pm2 save
```

## 🔍 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 检查端口使用情况
   netstat -tlnp | grep :8002
   netstat -tlnp | grep :5173
   
   # 杀死占用进程
   kill -9 <PID>
   ```

2. **内容提取引擎 anydoc 未安装/加载**
   ```bash
   pip install firecrawl-anydoc
   pip list | grep firecrawl-anydoc
   # 验证:能 import anydoc；后端启动日志可见 "anydoc 可用"
   ```

3. **数据库连接失败**
   - 检查数据库文件路径
   - 确认数据库服务运行状态
   - 检查连接字符串格式

4. **前端无法连接后端**
   - 检查CORS设置
   - 确认API地址配置
   - 检查防火墙设置

### 日志查看
```bash
# 系统日志
tail -f logs/backend.log
tail -f logs/frontend.log

# 实时监控
pm2 logs  # 如果使用PM2
```

---

**提示**: 首次部署建议在测试环境验证所有功能正常后再部署到生产环境。