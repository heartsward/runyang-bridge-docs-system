# GitHub部署指南

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
- LibreOffice集成文档内容提取

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
- [ ] 已安装LibreOffice（用于文档内容提取）
- [ ] 已修改SECRET_KEY为安全的随机值
- [ ] 已配置正确的API地址和CORS设置
- [ ] 已设置防火墙规则（开放5173和8002端口）

### 部署后验证
- [ ] 前端页面能正常访问 (http://localhost:5173)
- [ ] 后端API能正常访问 (http://localhost:8002)
- [ ] 能正常登录系统（admin/admin123）
- [ ] 能正常上传和搜索文档
- [ ] LibreOffice文档提取功能正常工作

## 🔄 版本更新

### 更新到最新版本
```bash
# 停止服务
./stop-services.sh  # 或 stop-services.bat

# 拉取最新代码
git pull origin main

# 检查是否有新的配置项
git diff HEAD~1 backend/.env.example
git diff HEAD~1 frontend/.env.example

# 更新依赖（如果有变化）
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# 重新启动服务
./start-production.sh  # 或 start-production.bat
```

### 版本回退（如有问题）
```bash
# 查看提交历史
git log --oneline -10

# 回退到指定版本（替换为实际的commit hash）
git checkout <commit-hash>

# 如果需要创建新分支
git checkout -b rollback-version

# 重新启动服务
./start-production.sh
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

2. **LibreOffice未找到**
   ```bash
   # Ubuntu/Debian
   sudo apt install libreoffice
   
   # 验证安装
   libreoffice --version
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