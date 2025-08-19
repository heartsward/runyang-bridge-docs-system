# LibreOffice 安装指南

## 为什么需要LibreOffice？

润扬大桥运维文档管理系统使用LibreOffice来提取Word、Excel等Office文档的文本内容，以支持智能搜索功能。如果没有安装LibreOffice，系统将无法：

- 提取Word文档 (.doc, .docx) 的文本内容
- 提取Excel表格 (.xls, .xlsx) 的文本内容  
- 在搜索中包含这些文档的内容
- 生成文档的AI摘要和分析

## 💻 Windows 安装

### 方法一：官网下载 (推荐)
1. 访问官网：https://www.libreoffice.org/download/download/
2. 点击 "Download LibreOffice"
3. 选择 Windows x86_64 版本下载
4. 运行下载的安装程序 (.msi文件)
5. 按照安装向导完成安装

### 方法二：包管理器
如果使用Chocolatey：
```powershell
choco install libreoffice
```

如果使用Winget：
```powershell
winget install TheDocumentFoundation.LibreOffice
```

### 验证安装
打开命令提示符 (cmd)，运行：
```cmd
"C:\Program Files\LibreOffice\program\soffice.exe" --version
```

## 🐧 Linux 安装

### Ubuntu / Debian
```bash
sudo apt update
sudo apt install libreoffice
```

### CentOS / RHEL / Fedora
CentOS/RHEL:
```bash
sudo yum install libreoffice
```

Fedora:
```bash
sudo dnf install libreoffice
```

### Arch Linux
```bash
sudo pacman -S libreoffice
```

### 从官网安装
1. 访问：https://www.libreoffice.org/download/download/
2. 选择 Linux x86_64 (deb) 或 Linux x86_64 (rpm)
3. 下载并安装对应的包

### 验证安装
```bash
libreoffice --version
# 或
soffice --version
```

## 🍎 macOS 安装

### 方法一：官网下载 (推荐)
1. 访问官网：https://www.libreoffice.org/download/download/
2. 点击 "Download LibreOffice"
3. 下载 macOS x86_64 版本 (.dmg文件)
4. 双击 .dmg 文件挂载
5. 将 LibreOffice.app 拖拽到 Applications 文件夹

### 方法二：Homebrew
```bash
brew install --cask libreoffice
```

### 验证安装
```bash
/Applications/LibreOffice.app/Contents/MacOS/soffice --version
```

## 🔧 系统集成配置

安装完成后，系统会自动检测LibreOffice的安装位置。系统会按以下顺序查找：

### Windows
1. `C:\Program Files\LibreOffice\program\soffice.exe`
2. `C:\Program Files (x86)\LibreOffice\program\soffice.exe`
3. 环境变量PATH中的 `soffice.exe`

### Linux
1. `/usr/bin/libreoffice`
2. `/usr/bin/soffice`
3. `/opt/libreoffice/program/soffice`
4. 环境变量PATH中的 `libreoffice` 或 `soffice`

### macOS
1. `/Applications/LibreOffice.app/Contents/MacOS/soffice`
2. 环境变量PATH中的 `soffice`

## ⚠️ 常见问题

### Q: 安装后系统仍然提示找不到LibreOffice？
A: 
1. 确认安装路径是否正确
2. 重启系统或重新启动文档管理系统
3. 检查环境变量PATH中是否包含LibreOffice路径

### Q: 可以使用WPS Office代替吗？
A: 不可以。系统专门调用LibreOffice的命令行接口，WPS Office不兼容。

### Q: LibreOffice版本有要求吗？
A: 建议使用最新稳定版本，理论上支持LibreOffice 6.0+。

### Q: 安装后需要配置什么吗？
A: 不需要特殊配置，系统会自动调用LibreOffice的headless模式。

### Q: LibreOffice占用空间大吗？
A: 完整安装约需要1.5-2GB空间，如果仅用于文档转换，可以选择最小安装。

## 🔍 功能测试

安装完成后，可以通过以下方式测试：

1. 上传一个Word或Excel文档到系统
2. 等待几秒钟让系统提取内容
3. 尝试搜索文档中的关键词
4. 如果能搜索到内容，说明LibreOffice配置成功

## 📞 技术支持

如果在安装过程中遇到问题：

1. 检查系统启动日志中是否有LibreOffice相关错误
2. 确认下载的LibreOffice版本与操作系统匹配
3. 尝试手动运行LibreOffice命令行验证安装
4. 查看系统文档或联系技术支持

---

*LibreOffice是开源免费的办公软件套件，由The Document Foundation开发维护*