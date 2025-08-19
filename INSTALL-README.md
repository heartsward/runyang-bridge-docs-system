# Windows 环境安装指南

## 快速开始

运行安装选择脚本：
```cmd
choose-install.bat
```

## 安装选项

### 1. 基础安装 (install-basic.bat)
**推荐新用户使用**
- ✅ 系统核心功能
- ✅ 文档上传和浏览
- ✅ 基础搜索功能
- ✅ 中文文本处理
- ⏱️ 安装时间: 2-5分钟

**包含的包:**
- FastAPI, SQLAlchemy (Web框架)
- PyJWT, pydantic (认证和验证)
- jieba, scikit-learn (中文和ML)
- PyPDF2, python-docx (基础文档)

### 2. 完整安装 (install-complete.bat)
**推荐大多数用户使用**
- ✅ 所有基础功能
- ✅ 增强PDF处理 (PyMuPDF)
- ✅ 高级文档分析
- ✅ 完整搜索引擎
- ⏱️ 安装时间: 5-10分钟

**额外包含:**
- PyMuPDF (增强PDF处理)
- pandas, pdfplumber (数据分析)
- markdown (Markdown支持)

### 3. 增强安装 (install-enhanced-full.bat)
**适合高级用户**
- ✅ 完整安装的所有功能
- ✅ OCR文字识别能力
- ✅ 图像处理功能
- ✅ 高级NLP分析
- ⏱️ 安装时间: 10-20分钟

**额外包含:**
- opencv-python (图像处理)
- pytesseract (OCR识别)
- pdf2image (PDF转图像)
- nltk (自然语言处理)

## 手动安装

如果自动安装失败，可以手动运行：

```cmd
cd backend
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements-windows-basic.txt
call venv\Scripts\deactivate.bat

cd ..\frontend
npm install
```

## 启动服务

安装完成后运行：
```cmd
start-services.bat
```

访问：http://localhost:5173

## 故障排除

### Python包安装失败
1. 确保Python 3.8+已安装
2. 尝试基础安装: `install-basic.bat`
3. 手动安装核心包: `pip install fastapi uvicorn sqlalchemy`

### 前端安装失败
1. 确保Node.js 16+已安装
2. 清理缓存: `npm cache clean --force`
3. 重新安装: `npm install --legacy-peer-deps`

### OCR功能不可用
增强安装后还需要：
1. 安装 Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki
2. 安装 Poppler: https://poppler.freedesktop.org/
3. 将程序路径添加到系统PATH

## 依赖文件说明

- `requirements-windows-basic.txt` - 基础功能依赖
- `requirements-windows.txt` - 完整功能依赖  
- `requirements.txt` - 原始Linux/通用依赖

## 支持的文档格式

- PDF, Word (doc/docx), Excel (xls/xlsx)
- 文本文件 (txt, md)
- 图像文件 (jpg, png) - 需增强安装