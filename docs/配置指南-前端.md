# 前端环境配置指南

本文档详细介绍润扬大桥运维文档管理系统前端的环境配置方法。

## 🔧 环境配置文件

系统提供了多个环境配置模板，根据部署环境选择合适的配置：

| 文件 | 用途 | 说明 |
|------|------|------|
| `.env` | 当前活跃配置 | 根据环境复制对应模板 |
| `.env.development` | 开发环境模板 | 本地开发使用 |
| `.env.production` | 生产环境模板 | 生产部署使用 |

## 🚀 快速配置

### 开发环境

```bash
cd frontend
cp .env.development .env
npm run dev
```

### 生产环境

```bash
cd frontend
cp .env.production .env
npm run build
```

## 📋 配置项详解

### API配置

```env
# 后端API基础地址
VITE_API_BASE_URL=http://localhost:8002

# API超时时间（毫秒）
VITE_API_TIMEOUT=30000

# API重试配置
VITE_API_RETRY_ENABLED=true
VITE_API_RETRY_COUNT=3
```

**常用配置示例：**
- 开发环境：`http://localhost:8002`
- 局域网访问：`http://192.168.1.100:8002`
- 生产环境（Nginx反向代理）：`/api`
- 生产环境（直接域名）：`https://api.runyang.com`

### 应用信息

```env
# 应用标题
VITE_APP_TITLE=润扬大桥运维文档管理系统

# 应用版本
VITE_APP_VERSION=2.2.0

# 应用描述
VITE_APP_DESCRIPTION=基于Vue3的运维文档管理系统
```

### 文件上传配置

```env
# 最大文件大小（字节），默认10MB
VITE_MAX_FILE_SIZE=10485760

# 允许的文件类型
VITE_ALLOWED_FILE_TYPES=pdf,doc,docx,txt,md,xls,xlsx,csv,jpg,jpeg,png
```

### 构建配置

```env
# 是否生成source map
VITE_BUILD_SOURCEMAP=false

# 是否启用代码压缩
VITE_BUILD_MINIFY=true

# 是否开启gzip压缩
VITE_BUILD_GZIP=true
```

### 功能开关

```env
# 调试模式（显示详细错误信息）
VITE_DEBUG_MODE=false

# 性能监控信息显示
VITE_SHOW_PERFORMANCE=false

# 自动保存功能
VITE_AUTO_SAVE_ENABLED=true
VITE_AUTO_SAVE_INTERVAL=300
```

### 主题配置

```env
# 默认主题
VITE_DEFAULT_THEME=light

# 是否启用主题切换
VITE_THEME_SWITCH_ENABLED=true

# 主色调
VITE_PRIMARY_COLOR=#1890ff
```

### 安全配置

```env
# 是否强制HTTPS
VITE_FORCE_HTTPS=false

# 允许的主机名
VITE_ALLOWED_HOSTS=localhost,127.0.0.1,docs.runyang.com
```

## 🌍 部署场景配置

### 场景1：本地开发

```env
# 复制开发环境配置
cp .env.development .env

# 主要配置
VITE_API_BASE_URL=http://localhost:8002
VITE_DEBUG_MODE=true
VITE_BUILD_SOURCEMAP=true
VITE_DEPLOY_ENV=development
```

### 场景2：局域网部署

```env
# 修改API地址为服务器IP
VITE_API_BASE_URL=http://192.168.1.100:8002
VITE_DEBUG_MODE=false
VITE_DEPLOY_ENV=staging
VITE_ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.100
```

### 场景3：Nginx反向代理

```env
# 使用相对路径，通过Nginx代理
VITE_API_BASE_URL=/api
VITE_DEPLOY_ENV=production
VITE_DEBUG_MODE=false
VITE_BUILD_SOURCEMAP=false
VITE_FORCE_HTTPS=true
```

### 场景4：独立域名部署

```env
# API使用独立域名
VITE_API_BASE_URL=https://api.runyang.com
VITE_DEPLOY_ENV=production
VITE_FORCE_HTTPS=true
VITE_ALLOWED_HOSTS=docs.runyang.com,api.runyang.com
```

### 场景5：CDN加速

```env
# 使用CDN加速静态资源
VITE_API_BASE_URL=/api
VITE_CDN_BASE_URL=https://cdn.runyang.com
VITE_DEPLOY_ENV=production
VITE_BUILD_GZIP=true
```

## 🔄 配置切换脚本

### 自动配置脚本

创建 `frontend/scripts/setup-env.sh`：

```bash
#!/bin/bash

# 前端环境配置脚本

ENV_TYPE=${1:-"development"}
API_URL=${2:-""}

echo "配置前端环境: $ENV_TYPE"

case $ENV_TYPE in
    "dev"|"development")
        cp .env.development .env
        if [[ -n "$API_URL" ]]; then
            sed -i "s|VITE_API_BASE_URL=.*|VITE_API_BASE_URL=$API_URL|g" .env
        fi
        echo "✅ 开发环境配置完成"
        ;;
    "prod"|"production")
        cp .env.production .env
        if [[ -n "$API_URL" ]]; then
            sed -i "s|VITE_API_BASE_URL=.*|VITE_API_BASE_URL=$API_URL|g" .env
        fi
        echo "✅ 生产环境配置完成"
        ;;
    "local")
        cp .env.development .env
        sed -i "s|VITE_API_BASE_URL=.*|VITE_API_BASE_URL=http://localhost:8002|g" .env
        echo "✅ 本地环境配置完成"
        ;;
    *)
        echo "❌ 未知环境类型: $ENV_TYPE"
        echo "支持的环境: development, production, local"
        exit 1
        ;;
esac

echo "当前API地址: $(grep VITE_API_BASE_URL .env)"
```

### 使用方法

```bash
# 开发环境
bash scripts/setup-env.sh development

# 生产环境
bash scripts/setup-env.sh production

# 自定义API地址
bash scripts/setup-env.sh development http://192.168.1.100:8002

# 本地环境
bash scripts/setup-env.sh local
```

## 🔍 配置验证

### 验证脚本

创建 `frontend/scripts/check-config.js`：

```javascript
#!/usr/bin/env node

// 前端配置验证脚本
const fs = require('fs');
const path = require('path');

function loadEnv() {
    const envPath = path.join(__dirname, '../.env');
    if (!fs.existsSync(envPath)) {
        console.error('❌ .env 文件不存在');
        return null;
    }

    const env = {};
    const content = fs.readFileSync(envPath, 'utf-8');
    content.split('\n').forEach(line => {
        line = line.trim();
        if (line && !line.startsWith('#')) {
            const [key, value] = line.split('=');
            if (key && value) {
                env[key.trim()] = value.trim();
            }
        }
    });
    return env;
}

function validateConfig(env) {
    const issues = [];
    const warnings = [];

    // 必需配置检查
    const required = ['VITE_API_BASE_URL', 'VITE_APP_TITLE', 'VITE_APP_VERSION'];
    required.forEach(key => {
        if (!env[key]) {
            issues.push(`缺少必需配置: ${key}`);
        }
    });

    // API URL格式检查
    if (env.VITE_API_BASE_URL) {
        const apiUrl = env.VITE_API_BASE_URL;
        if (!apiUrl.startsWith('http') && !apiUrl.startsWith('/')) {
            issues.push(`API地址格式错误: ${apiUrl}`);
        }
        if (apiUrl.endsWith('/')) {
            warnings.push(`API地址不应以/结尾: ${apiUrl}`);
        }
    }

    // 文件大小检查
    if (env.VITE_MAX_FILE_SIZE) {
        const size = parseInt(env.VITE_MAX_FILE_SIZE);
        if (size > 52428800) { // 50MB
            warnings.push(`文件大小限制过大: ${Math.round(size/1024/1024)}MB`);
        }
    }

    // 调试模式检查
    if (env.VITE_DEPLOY_ENV === 'production' && env.VITE_DEBUG_MODE === 'true') {
        warnings.push('生产环境不应启用调试模式');
    }

    return { issues, warnings };
}

function main() {
    console.log('🔍 检查前端配置...\n');

    const env = loadEnv();
    if (!env) {
        process.exit(1);
    }

    const { issues, warnings } = validateConfig(env);

    console.log('📋 当前配置:');
    console.log(`  API地址: ${env.VITE_API_BASE_URL || '未设置'}`);
    console.log(`  应用标题: ${env.VITE_APP_TITLE || '未设置'}`);
    console.log(`  版本: ${env.VITE_APP_VERSION || '未设置'}`);
    console.log(`  部署环境: ${env.VITE_DEPLOY_ENV || '未设置'}`);
    console.log(`  调试模式: ${env.VITE_DEBUG_MODE || 'false'}`);
    console.log('');

    if (issues.length > 0) {
        console.log('❌ 配置错误:');
        issues.forEach(issue => console.log(`  - ${issue}`));
        console.log('');
    }

    if (warnings.length > 0) {
        console.log('⚠️  配置警告:');
        warnings.forEach(warning => console.log(`  - ${warning}`));
        console.log('');
    }

    if (issues.length === 0) {
        console.log('✅ 配置验证通过');
        process.exit(0);
    } else {
        console.log('❌ 配置验证失败');
        process.exit(1);
    }
}

main();
```

### 运行验证

```bash
cd frontend
node scripts/check-config.js
```

## 🛠️ 开发工具配置

### VS Code配置

创建 `frontend/.vscode/settings.json`：

```json
{
  "typescript.preferences.importModuleSpecifier": "relative",
  "vue.codeActions.enabled": false,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "files.associations": {
    ".env*": "dotenv"
  }
}
```

### ESLint配置

在 `frontend/.eslintrc.js` 中添加环境变量规则：

```javascript
module.exports = {
  // ... 其他配置
  rules: {
    // 环境变量命名规范
    'vue/custom-event-name-casing': 'off',
    // 允许console（开发环境）
    'no-console': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'warn' : 'off'
  },
  // 环境变量类型检查
  env: {
    node: true,
    'vue/setup-compiler-macros': true
  }
}
```

## 🔄 动态配置加载

### 运行时配置

创建 `frontend/src/config/index.ts`：

```typescript
// 运行时配置管理
interface AppConfig {
  apiBaseUrl: string;
  appTitle: string;
  appVersion: string;
  maxFileSize: number;
  allowedFileTypes: string[];
  debugMode: boolean;
  deployEnv: string;
}

export const config: AppConfig = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || '/api',
  appTitle: import.meta.env.VITE_APP_TITLE || '运维文档管理系统',
  appVersion: import.meta.env.VITE_APP_VERSION || '1.0.0',
  maxFileSize: Number(import.meta.env.VITE_MAX_FILE_SIZE) || 10485760,
  allowedFileTypes: (import.meta.env.VITE_ALLOWED_FILE_TYPES || 'pdf,doc,docx').split(','),
  debugMode: import.meta.env.VITE_DEBUG_MODE === 'true',
  deployEnv: import.meta.env.VITE_DEPLOY_ENV || 'development'
};

// 配置验证
export function validateConfig(): boolean {
  const required: (keyof AppConfig)[] = ['apiBaseUrl', 'appTitle'];
  
  for (const key of required) {
    if (!config[key]) {
      console.error(`Missing required config: ${key}`);
      return false;
    }
  }
  
  return true;
}

// 开发环境配置输出
if (config.debugMode) {
  console.log('📋 App Config:', config);
}
```

## 📝 最佳实践

### 1. 环境隔离

- 不同环境使用不同的配置文件
- 敏感信息不放入版本控制
- 生产环境关闭调试功能

### 2. 配置验证

- 启动前验证必需配置
- 提供配置检查脚本
- 记录配置变更

### 3. 部署自动化

- 使用脚本自动切换环境
- 构建时验证配置完整性
- 提供配置模板和示例

### 4. 错误处理

- API连接失败时的降级策略
- 配置错误时的友好提示
- 提供配置帮助信息

通过以上配置，前端可以灵活适应不同的部署环境和需求。