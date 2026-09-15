# LibreOffice 安装指南（Office 格式在线预览）

> **生效版本**:2026-09-15 起(阶段二十四)
> **前置文档**:`docs/系统架构文档.md` 第 2.4 节"提取链路"、第 3.5 节"预览链路"

## 为什么需要 LibreOffice?

润扬大桥运维文档管理系统在 2026-09-15 起新增 **Office 格式在线预览** 功能 —— 用户上传 .docx/.xlsx/.pptx 等 Office 文档后,在预览界面切到"原文件"模式可以直接在浏览器里查看(转 PDF + iframe 显示),无需下载到本地再打开。

**此功能依赖 LibreOffice 命令行转换能力**。如果未安装 LibreOffice:
- ❌ .docx / .xlsx / .pptx / .odt / .ods / .odp / .rtf / .epub 在浏览器内无法预览,只能下载到本地
- ✅ 其他格式不受影响:PDF 直接浏览器查看、图片直接显示、文本类(.txt/.md/.csv/.json/.xml/.html)走文本预览
- ✅ **不影响内容提取/智能搜索**(内容提取在阶段十九起改用 anydoc,完全脱离 LibreOffice)

**重要边界 — 与早期版本的关系**:
- 阶段十九之前:LibreOffice 同时承担"内容提取" + "Office 转 PDF"两个角色(全栈 LibreOffice)
- 阶段十九:anydoc 替换 LibreOffice 做内容提取(更快、零系统依赖);LibreOffice 全栈代码清零
- **阶段二十四**:LibreOffice 重新引入,**仅**承担"Office 转 PDF 预览"角色(任何doc 链路继续走 anydoc,与 LibreOffice 完全解耦)
- 两条链路独立运行:内容提取走 `extract_{doc_id}_*.json` 进度文件,预览转换走 `preview_convert_{doc_id}.json` 进度文件(互不干扰)

## 💻 Windows 安装

### 方法一:官网下载(推荐)
1. 访问官网:https://www.libreoffice.org/download/download/
2. 选择 **Windows x86_64** 版本下载
3. 运行下载的安装程序 (.msi 文件)
4. ⚠️ **关键步骤**:安装向导中**勾选"将 LibreOffice 添加到系统 PATH"**(默认未勾选)
5. 安装完成后**重启 cmd/PowerShell 窗口**(让新 PATH 生效)

### 方法二:包管理器
Chocolatey:
```powershell
choco install libreoffice
```
Winget:
```powershell
winget install TheDocumentFoundation.LibreOffice
```

### 验证安装
新开 cmd 窗口(必须新窗口,旧窗口 PATH 不更新),运行:
```cmd
soffice --version
```
预期输出形如 `LibreOffice 7.6.4.1 ...`。

如果提示"找不到 soffice",手动指定完整路径再试:
```cmd
"C:\Program Files\LibreOffice\program\soffice.exe" --version
```

如果完整路径可识别但 PATH 中的 `soffice` 不识别 → PATH 没生效 → 重启 cmd。

## 🐧 Linux 安装

### Ubuntu / Debian
仅装核心 + 3 个转换所需的组件(避免 ~400MB 全装):
```bash
sudo apt update
sudo apt install -y libreoffice-core libreoffice-writer libreoffice-calc libreoffice-impress
```

### CentOS / RHEL / Fedora
```bash
# CentOS / RHEL
sudo yum install -y libreoffice-core libreoffice-writer libreoffice-calc libreoffice-impress
# Fedora
sudo dnf install -y libreoffice-core libreoffice-writer libreoffice-calc libreoffice-impress
```

### Arch Linux
```bash
sudo pacman -S libreoffice
```

### 验证安装
```bash
soffice --version
```
预期输出形如 `LibreOffice 7.6.4.1 42 ...`。

## 🍎 macOS 安装

### 方法一:Homebrew(推荐)
```bash
brew install --cask libreoffice
```

### 方法二:官网下载
访问 https://www.libreoffice.org/download/download/ 下载 .dmg,拖入 Applications。

### 验证安装
```bash
/Applications/LibreOffice.app/Contents/MacOS/soffice --version
```

## 🔧 系统集成配置

### 系统如何查找 LibreOffice
后端启动时按以下顺序探测 soffice 路径(在 `backend/app/services/preview_converter.py`):

| 平台 | 探测路径 |
|------|----------|
| **Windows** | 1. `C:\Program Files\LibreOffice\program\soffice.exe`<br>3. `C:\Program Files (x86)\LibreOffice\program\soffice.exe`<br>4. 环境变量 `PATH` 中的 `soffice` |
| **Linux** | 1. `/usr/bin/soffice`<br>2. `/usr/bin/libreoffice`<br>3. `/opt/libreoffice/program/soffice`<br>4. 环境变量 `PATH` 中的 `soffice` |
| **macOS** | 1. `/Applications/LibreOffice.app/Contents/MacOS/soffice`<br>2. 环境变量 `PATH` 中的 `soffice` |

### 自定义路径(可选)
如果 LibreOffice 装在非默认路径,在 `backend/.env` 加:
```bash
# 阶段二十四:LibreOffice 自定义可执行文件路径(可选)
LIBREOFFICE_BIN_PATH=/custom/path/to/soffice
```

不填则用上面探测路径。

## ⚠️ 常见问题

### Q: 装了但提示"找不到 LibreOffice"
1. **重启终端/服务** — PATH 在新进程才生效(改完 .env 也要重启后端,见本节 Q2)
2. **检查 PATH**:Windows `echo %PATH%` / Linux `echo $PATH`,确认包含 LibreOffice 路径
3. **显式指定**:在 `.env` 设 `LIBREOFFICE_BIN_PATH=/full/path/to/soffice`

### Q: 改了 .env 还没生效?
后端 `Settings` 单例 import 时只读一次 .env,改完 .env 必须**手动重启后端**:
```bash
# Windows
start-services.bat  # 会先 stop 再 start
# 或者直接重启后端进程
venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8002
```

### Q: 转换时报 "source file could not be loaded" 或 LibreOffice 卡死?
LibreOffice **同一用户不能同时开多个实例**(single-instance 设计)。后端会用文件锁防并发,如果仍卡死:
1. **Windows**:任务管理器结束所有 `soffice.exe` 进程
2. **Linux**: `pkill -f soffice`

### Q: 转换大 .xlsx 慢(超过 60s)?
正常。.xlsx 转 PDF 比 .docx 慢很多(复杂表格/图表)。后端默认超时 120s,前端会显示"正在转换 X%..."。
- 如果文件超过 100MB 且转换超时 → 在 `.env` 调高超时:
  ```bash
  PREVIEW_CONVERT_TIMEOUT=300  # 单位秒
  ```

### Q: 可以用 WPS Office 代替吗?
**不可以**。本系统专调 LibreOffice 的 `soffice --headless --convert-to pdf` 命令行接口,WPS 不兼容。

### Q: 版本要求?
LibreOffice **6.0+** 即可。本地实测 LibreOffice 7.6。

### Q: 占用多大空间?
- Windows 完整安装:约 **1.5-2GB**
- Linux 仅装核心 + 3 组件:约 **400MB**
- macOS:约 **1.5GB**

## 🔍 功能测试

### 1. 后端能识别 LibreOffice
重启后端后,日志应出现:
```
[PreviewConverter] LibreOffice 已找到: /usr/bin/soffice (LibreOffice 7.6.4.1)
```
如果看到 `[PreviewConverter] ⚠️ LibreOffice 未安装` → 见上文"装了但提示找不到"。

### 2. 单文档转换测试
通过 API 端点(需要 JWT,登录后从 `/auth/me` 拿):
```bash
curl -H "Authorization: Bearer <token>" \
     http://localhost:8002/api/v1/documents/6/converted-pdf \
     --output test.pdf
```
- 首调:会触发 LibreOffice 转换,大文件需等几十秒
- 返回 PDF 文件即成功

### 3. 前端可视化测试
1. 上传一个 .docx 文档到系统
2. 进入"文档管理 → 预览"或"智能搜索 → 预览"
3. 切到"原文件"模式
4. 首次会显示"正在转换为 PDF (LibreOffice)..." + loading 旋转;转完后 iframe 显示 PDF
5. 二次切到"原文件"应秒出(命中缓存)

### 4. 进度通道独立性验证
同一文档同时观察两条进度:
- 内容提取进度:`/api/v1/tasks/document/{id}/extraction-status`(走 `extract_{id}_*.json`)
- 预览转换进度:`/api/v1/documents/{id}/conversion-status`(走 `preview_convert_{id}.json`)

两者互不干扰:同一秒调用两次得到不同的 status/progress 字典。

## 📞 技术支持

如果在安装或运行中遇到问题:
1. 看后端启动日志(`backend/logs/` 或终端输出),搜 `PreviewConverter` / `LibreOffice` 关键字
2. `soffice --headless --convert-to pdf --outdir /tmp test.docx` 手测能否转出 PDF
3. 在 Issues 区附日志 + 文档类型 + LibreOffice 版本

---

*LibreOffice 是开源免费的办公软件套件,由 The Document Foundation 开发维护。本系统仅使用其命令行 PDF 转换能力,与 LibreOffice 主项目无商业关联。*