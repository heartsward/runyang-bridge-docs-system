# 域名访问配置指南

## 概述
本指南说明如何配置系统支持域名访问，以 `docs.runyang.com` 为例。

## 1. 后端配置 (推荐方案)

### 1.1 修改 database_integrated_server.py

在文件开头添加环境变量读取逻辑：

```python
# 在第91行左右，替换硬编码的cors_origins配置
import os

# 从环境变量读取CORS配置
cors_origins_env = os.getenv("CORS_ORIGINS", "")
if cors_origins_env:
    cors_origins = [origin.strip() for origin in cors_origins_env.split(",")]
else:
    # 保留默认IP配置
    cors_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173", 
        "http://192.168.66.99:5173",
        "http://192.168.134.1:5173",
        "http://192.168.19.1:5173"
    ]

print(f"[CORS] 允许的源: {cors_origins}")
```

### 1.2 修改 backend/.env

```env
# 添加域名CORS配置
CORS_ORIGINS=http://localhost:5173,https://docs.runyang.com,http://docs.runyang.com,http://192.168.66.99:5173

# 如果使用反向代理，后端可以只监听本地
SERVER_HOST=127.0.0.1
SERVER_PORT=8002
```

## 2. 前端配置

### 2.1 创建生产环境配置 .env.production

```env
# 生产环境API配置 - 使用域名
VITE_API_BASE_URL=https://docs.runyang.com:8002

# 如果使用Nginx代理，可以统一端口
# VITE_API_BASE_URL=https://docs.runyang.com

# 应用配置
VITE_APP_TITLE=润扬大桥运维文档管理系统
VITE_APP_DESCRIPTION=润扬大桥智慧高速运维文档管理平台

# 生产优化
VITE_DROP_CONSOLE=true
VITE_DROP_DEBUGGER=true
VITE_BUILD_SOURCEMAP=false
```

### 2.2 构建生产版本

```bash
cd frontend
npm run build
```

## 3. Nginx服务器配置 (推荐)

### 3.1 方案A: 分离端口 (简单)

```nginx
server {
    listen 80;
    server_name docs.runyang.com;
    
    # HTTP重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name docs.runyang.com;
    
    # SSL配置
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # 前端静态文件
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
        
        # 缓存静态资源
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}

# 后端API服务器 - 8002端口
server {
    listen 8002 ssl;
    server_name docs.runyang.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 3.2 方案B: 统一端口 (推荐)

```nginx
server {
    listen 80;
    server_name docs.runyang.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name docs.runyang.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # 前端静态文件
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
        
        # 静态资源缓存
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS处理（如果需要）
        add_header Access-Control-Allow-Origin "https://docs.runyang.com";
        add_header Access-Control-Allow-Credentials true;
    }
}
```

**如果使用方案B，需要修改前端配置：**
```env
# .env.production
VITE_API_BASE_URL=https://docs.runyang.com
```

## 4. SSL证书配置

### 4.1 Let's Encrypt免费证书

```bash
# 安装certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d docs.runyang.com

# 自动续期
sudo crontab -e
# 添加：0 12 * * * /usr/bin/certbot renew --quiet
```

### 4.2 自签名证书（仅测试用）

```bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/docs.runyang.com.key \
    -out /etc/ssl/certs/docs.runyang.com.crt
```

## 5. 系统服务配置

### 5.1 创建systemd服务文件

```ini
# /etc/systemd/system/runyang-docs.service
[Unit]
Description=Runyang Bridge Document Management System
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/yunweiruanjian/backend
Environment=PATH=/usr/local/bin
ExecStart=/usr/local/bin/python3 database_integrated_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
sudo systemctl enable runyang-docs
sudo systemctl start runyang-docs
sudo systemctl status runyang-docs
```

## 6. 部署检查清单

- [ ] 域名DNS解析正确
- [ ] 后端CORS配置包含域名
- [ ] 前端API地址配置正确
- [ ] SSL证书配置完成
- [ ] Nginx配置测试通过 (`nginx -t`)
- [ ] 防火墙端口开放 (80, 443, 8002)
- [ ] 后端服务运行正常
- [ ] 前端构建完成并部署

## 7. 故障排查

### 7.1 CORS错误
- 检查后端CORS配置是否包含域名
- 确认协议(http/https)匹配
- 查看浏览器开发者工具Network标签

### 7.2 API连接失败
- 检查防火墙设置
- 确认后端服务运行状态
- 验证API地址配置

### 7.3 SSL证书问题
- 检查证书有效性：`openssl x509 -in cert.pem -text -noout`
- 验证证书链完整性
- 确认证书域名匹配

## 8. 安全建议

1. 使用HTTPS加密传输
2. 定期更新SSL证书
3. 限制CORS源只包含必要域名
4. 配置适当的Content Security Policy
5. 启用HSTS (HTTP Strict Transport Security)
6. 定期备份数据库和上传文件