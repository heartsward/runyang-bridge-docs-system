# 生产环境安装指南

## 🚀 快速安装（推荐）

### 1. 完整生产环境安装
```bash
# Windows
install-production.bat

# Linux/Mac
./install-production.sh
```

此脚本会：
- ✅ 安装所有必需的Python依赖
- ✅ 安装OCR相关组件（pytesseract, pdf2image, opencv）
- ✅ 修复datetime.utcnow()弃用警告
- ✅ 构建前端生产版本
- ✅ 验证所有功能模块
- ✅ 创建生产启动脚本

## 🔧 手动安装步骤

### 前置要求
- Python 3.8+
- Node.js 16+
- Tesseract OCR程序

### 后端安装
```bash
cd backend

# 创建虚拟环境
python -m venv venv
call venv\Scripts\activate.bat  # Windows
source venv/bin/activate        # Linux/Mac

# 安装生产环境依赖
pip install -r requirements-production.txt
```

### 前端安装
```bash
cd frontend
npm install
npm run build
```

## 🛠️ 已修复的生产环境问题

### 1. DateTime弃用警告
**问题**: 
```
DeprecationWarning: datetime.datetime.utcnow() is deprecated
```

**修复**: 
- 所有 `datetime.utcnow()` 已替换为 `datetime.now(timezone.utc)`
- 自动添加 `timezone` 导入

### 2. OCR功能缺失
**问题**: 
```
缺少OCR依赖包，请安装: pip install pytesseract pillow pdf2image
OpenCV未安装，图像预处理功能将受限
```

**修复**: 
- 添加 `pytesseract>=0.3.10`
- 添加 `pdf2image>=1.16.0`
- 添加 `opencv-python-headless>=4.7.0`（无GUI版本）

### 3. PDF识别问题
**修复**: 
- 完整的OCR回退机制
- 智能乱码检测算法
- 多层PDF文本提取策略

## 📋 依赖文件说明

| 文件 | 用途 | 说明 |
|------|------|------|
| `requirements-production.txt` | 生产环境完整依赖 | 包含OCR等所有功能 |
| `requirements-windows.txt` | Windows环境依赖 | 包含Windows特定配置 |
| `requirements.txt` | 基础依赖 | 最小化安装 |

## 🚀 启动命令

### 生产环境
```bash
# 集成数据库模式（推荐）
start-production.bat
# 访问: http://localhost:8000

# 或手动启动
cd backend
call venv\Scripts\activate.bat
python database_integrated_server.py
```

### 开发环境
```bash
# 前后端分离模式
start-services.bat
# 后端: http://localhost:8000
# 前端: http://localhost:5173
```

## ✅ 验证安装

运行以下命令验证功能：

```bash
cd backend
call venv\Scripts\activate.bat

# 验证OCR功能
python -c "from app.services.enhanced_content_extractor import EnhancedContentExtractor; print('OCR可用:', EnhancedContentExtractor().has_ocr)"

# 测试乱码检测
python test-garbled-detection.py

# 测试PDF处理
python test-pdf-ocr-fallback.py path/to/test.pdf
```

## 🐛 故障排除

### OCR不工作
1. 确保安装Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
2. 检查PATH环境变量包含Tesseract
3. 验证中文语言包: `tesseract --list-langs` 应包含 `chi_sim`

### DateTime警告
- 运行 `install-production.bat` 会自动修复
- 或手动更新代码中的datetime调用

### 前端构建失败
- 确保Node.js版本 >= 16
- 删除 `node_modules` 后重新安装
- 使用 `npm run build` 而非 `npm run build-with-types`（临时跳过类型检查）

## 📞 技术支持

如果遇到问题：
1. 查看日志文件 `logs/`
2. 运行安装脚本的详细输出
3. 检查系统要求是否满足

---
📝 最后更新: 2025年8月19日
🔧 版本: 生产环境 v1.2