# MiniMax连接问题诊断指南

## 问题：点击测试连接显示连接失败

### 已修复的问题

1. **URL重复问题**：修复了MiniMax provider中的URL构建逻辑，避免路径重复
2. **响应解析问题**：改进了对MiniMax响应的兼容性处理

### 诊断步骤

#### 1. 使用诊断工具

我们提供了一个专门的诊断工具来帮助排查问题：

```bash
cd D:\资产管理系统\runyang-bridge-docs-system\backend
python diagnose_minimax.py
```

这个工具会：
- 检查后端服务状态
- 直接测试MiniMax API连接（绕过后端）
- 通过后端测试MiniMax API连接
- 提供详细的错误分析和解决方案

#### 2. 常见问题排查

**A. API Key问题**

错误信息：
- "API Key未配置"
- "API Key无效"
- HTTP 401

解决方案：
1. 确认从正确的渠道获取API Key：
   - Token Plan: https://platform.minimaxi.com/user-center/payment/token-plan
   - 按量计费: https://platform.minimaxi.com/user-center/basic-information/interface-key
2. 复制完整的API Key（不要有多余的空格）
3. 确认API Key没有过期

**B. 模型名称问题**

错误信息：
- "模型不存在"
- "计划不支持该模型"
- HTTP 404或状态码2013

解决方案：
1. 确认使用正确的模型名称：
   - 标准版: `MiniMax-M2.7`
   - 极速版: `MiniMax-M2.7-highspeed`
2. 检查您的订阅计划是否支持该模型

**C. API URL配置问题**

错误信息：
- 连接超时
- DNS解析失败
- HTTP 404或500

解决方案：
1. 确认使用正确的API URL：
   - 标准: `https://api.minimaxi.com/v1/chat/completions`
   - 基础URL: `https://api.minimaxi.com/v1`
2. 检查网络连接
3. 检查防火墙设置

**D. 订阅计划问题**

错误信息：
- "您的MiniMax计划不支持该模型"
- HTTP 403或状态码2061

解决方案：
1. 登录MiniMax平台查看您的订阅状态
2. 确认订阅的Token Plan包含所需模型
3. 如果按量计费，确保账户有足够余额

**E. 网络连接问题**

错误信息：
- "请求超时"
- "连接失败"

解决方案：
1. 检查网络连接
2. 尝试更换网络环境
3. 检查代理设置
4. 尝试使用其他API服务验证网络

### 正确的配置格式

在前端配置界面，应该使用以下格式：

```
Provider: MiniMax
API Key: sk-xxxxxxxxxxxxxxxxxxxx
API URL: https://api.minimaxi.com/v1/chat/completions
Model: MiniMax-M2.7
Group ID: (留空或填写您的group_id)
```

### 快速测试命令

如果你想快速测试API Key是否有效：

```bash
cd D:\资产管理系统\runyang-bridge-docs-system\backend

# 修改test_minimax_connection.py中的API_KEY
# 然后运行:
python test_minimax_connection.py
```

### 获取帮助

如果以上步骤都无法解决问题：

1. 查看MiniMax官方文档: https://platform.minimaxi.com/docs
2. 检查MiniMax控制台中的使用情况和计费
3. 查看后端日志获取详细错误信息

### 联系支持

MiniMax官方支持:
- 邮箱: Model@minimaxi.com
- GitHub Issues: https://github.com/MiniMax-AI/MiniMax-M2/issues

### 代码修复内容

本次修复了以下文件：

1. **app/core/config.py** - 更新默认API URL和模型名称
2. **app/services/ai/providers/minimax_provider.py** - 修复URL构建逻辑
3. **app/services/ai/ai_config_service.py** - 修复时间戳处理

修复后请重启后端服务以应用更改。

---

**最后更新**: 2026-04-11
**版本**: 1.0
