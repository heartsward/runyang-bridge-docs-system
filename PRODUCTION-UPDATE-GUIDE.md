# 生产环境更新指南

## 🚀 推荐更新方法（选择其一）

### 方法1：完整安全更新（推荐）
```bash
# 在生产服务器上运行
update-production.bat
```
- ✅ 自动备份数据库和配置
- ✅ 安全停止和启动服务
- ✅ 验证更新结果
- ✅ 提供回滚方案

### 方法2：快速更新
```bash
# 适合紧急修复
quick-update.bat
```
- ⚡ 快速代码更新
- ⚡ 自动重启服务
- ⚠️  无备份，请谨慎使用

### 方法3：手动更新
如果自动脚本有问题，可以手动执行：

#### 步骤1：备份重要数据
```bash
# 创建备份目录
mkdir backup_manual

# 备份数据库
copy "backend\yunwei_docs.db" "backup_manual\"
copy "backend\users_data.json" "backup_manual\"
copy "backend\assets_data.json" "backup_manual\"
```

#### 步骤2：停止服务
```bash
# 停止现有服务
stop-services.bat

# 确认进程已停止
tasklist | findstr python
tasklist | findstr node
```

#### 步骤3：更新代码
```bash
# 检查当前状态
git status
git log --oneline -3

# 拉取最新代码
git fetch origin
git pull origin main

# 查看更新内容
git log --oneline -5
```

#### 步骤4：运行修复
```bash
# 进入后端目录
cd backend

# 激活虚拟环境（如果使用）
call venv\Scripts\activate.bat

# 运行datetime修复脚本
python fix_datetime.py

# 退出虚拟环境
call venv\Scripts\deactivate.bat

cd ..
```

#### 步骤5：重启服务
```bash
# 启动生产服务
start-production.bat

# 或启动开发服务
start-services.bat
```

#### 步骤6：验证更新
```bash
# 测试OCR功能
python diagnose-ocr.py

# 检查服务状态
curl http://localhost:8000/health

# 查看日志
type backend\logs\*.log
```

## 🔧 更新内容说明

### 本次更新修复的问题：
1. **PDF乱码检测算法失效** - 乱码文本未被识别，导致OCR从不触发
2. **OCR触发阈值过高** - 从40%降低到30%，提高检测灵敏度
3. **缺少快速乱码检测** - 添加明显乱码模式的快速识别

### 修复后的效果：
- ✅ PDF图片文档能正确识别乱码
- ✅ 自动触发OCR处理
- ✅ 返回正确的中文文本内容
- ✅ 不影响正常PDF文档处理

## 🚨 故障排除

### 如果更新失败：
```bash
# 回滚到上一版本
git reset --hard HEAD~1

# 恢复备份数据
copy "backup_*\yunwei_docs.db" "backend\"
copy "backup_*\users_data.json" "backend\"

# 重启服务
stop-services.bat
start-services.bat
```

### 如果服务无法启动：
1. 检查端口占用：`netstat -ano | findstr 8000`
2. 查看错误日志：`type backend\logs\*.log`
3. 检查虚拟环境：`backend\venv\Scripts\python.exe --version`
4. 测试基础功能：`python diagnose-ocr.py`

### 如果OCR仍不工作：
1. 验证Tesseract安装：`"C:\Program Files\Tesseract-OCR\tesseract.exe" --version`
2. 检查语言包：`tesseract --list-langs`
3. 手动测试：`python test-ocr-processing.py`

## 📞 技术支持

如果遇到问题：
1. 保存错误日志：`backend\logs\`
2. 检查Git状态：`git status`
3. 查看系统状态：`python diagnose-ocr.py`

---
📝 更新说明：修复PDF乱码检测算法，提高OCR触发灵敏度
🕒 最后更新：2025年8月19日