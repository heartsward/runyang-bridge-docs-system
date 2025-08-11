# 网络配置说明

## 问题描述
从其他电脑访问系统时出现"failed to fetch"错误。

## 原因分析
1. 后端服务只监听localhost (127.0.0.1)，不接受外部网络访问
2. CORS配置未包含局域网IP地址

## 解决方案

### 1. 后端配置修改
已修改以下配置文件：

**backend/app/core/config.py**:
```python
BACKEND_CORS_ORIGINS: list = [
    "http://localhost:5173", 
    "http://localhost:5174", 
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://192.168.66.99:5173",    # 新增
    "http://192.168.66.99:5174",    # 新增  
    "http://192.168.66.99:8002"     # 新增
]
```

**backend/database_integrated_server.py**:
```python
uvicorn.run(
    app,
    host="0.0.0.0",  # 改为监听所有网卡
    port=8002,
    reload=False,
    log_level="info",
    access_log=True
)
```

### 2. 重启服务
修改配置后需要重启后端服务：
```bash
# 停止现有服务 (Ctrl+C)
# 重新启动
python backend/database_integrated_server.py
```

### 3. 访问方式
其他电脑可通过以下地址访问：
- **Web前端**: http://192.168.66.99:5173
- **API接口**: http://192.168.66.99:8002
- **API文档**: http://192.168.66.99:8002/docs

### 4. 防火墙设置
确保Windows防火墙允许8002和5173端口的入站连接：
```bash
# 管理员命令行执行
netsh advfirewall firewall add rule name="Backend API" dir=in action=allow port=8002 protocol=tcp
netsh advfirewall firewall add rule name="Frontend Web" dir=in action=allow port=5173 protocol=tcp
```

## 测试验证
从其他电脑执行以下命令测试连接：
```bash
# 测试后端API
curl http://192.168.66.99:8002/api/v1/
# 测试前端访问
浏览器访问: http://192.168.66.99:5173
```

## 注意事项
- 修改配置后必须重启服务
- 确保网络连通性（ping 192.168.66.99）
- 检查防火墙和安全软件设置