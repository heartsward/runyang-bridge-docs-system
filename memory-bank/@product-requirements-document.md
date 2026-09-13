# @product-requirements-document.md — 产品需求文档

> ⚠️ AI 在写任何代码前必须完整阅读本文件。
> 来源：`README.md` + `docs/系统架构文档.md` + `docs/用户操作手册.md` 综合提取。
> 形式：非游戏项目，因此采用 **PRD** 而非 GDD。

---

## 一、产品一句话定义

**润扬大桥运维资产管理系统** —— 一个专为桥梁运维场景设计的**现代化文档 + 资产 + 搜索一体化平台**，集 AI 能力、AI Wiki MCP 数据服务与权限管理于一体。

---

## 二、目标用户与场景

| 角色 | 典型场景 |
|------|----------|
| 运维工程师 | 上传/查阅技术文档、故障手册、维护记录；搜索定位 |
| 设备管理员 | 录入/维护设备档案、查看生命周期与状态 |
| 系统管理员 | 管理用户、配置 AI、查看系统统计、备份 |
| AI 工作台用户（WorkBuddy 等） | 通过 AI Wiki MCP 检索知识库、生成报告 |

---

## 三、核心功能（功能性需求）

### F1 智能文档管理
- 多格式支持：PDF / Word / Excel / 文本 / Markdown / 图片
- 自动 OCR 与内容提取（中文 + Unicode 表格字符支持）
- 在线预览与下载
- 批量上传、批量分类、批量删除
- 文档版本与变更追踪
- 元数据：标题、描述、标签、分类、上传时间

### F2 高效搜索
- 全文搜索（基于提取出的完整内容）
- 权重排序：内容 > 标题 > 描述
- 关键词高亮显示
- 搜索建议（基于历史热词）
- 多维筛选：文档类型、上传时间、分类
- 搜索行为统计

### F3 设备资产管理
- 全类型：服务器 / 网络 / 存储 / 安全 / 其他
- 字段：类型、部门、网络位置、状态、维护记录、采购信息
- 状态监控、生命周期、批量导入导出（Excel/CSV）
- 从文档自动识别并提取资产信息（AI 抽取）
- 统计报表：分布、状态、成本分析

### F4 用户与权限
- 角色：超级管理员 / 普通用户
- 用户 CRUD、改密
- JWT（24h）+ Bcrypt 哈希
- 关键操作审计日志

### F5 数据分析
- 文档访问量、搜索热词、用户活跃度
- 设备分布与状态统计
- 趋势图、性能监控指标

### F6 移动端 — 已移除（2026-09-12）
- 原计划：Kotlin + Compose + Hilt + Room + Retrofit（`android/` 目录）
- **已整体移除**（用户决策）：后期由 AI 工作台（WorkBuddy 等）通过 **AI Wiki MCP**（`/mcp`）接入做数据查询与利用，不再开发 Android 客户端
- 后端移动端 API（`/api/v1/mobile/*`）、`schemas/mobile.py`、mobile 专属 JWT 函数已同步删除

### F7 AI 集成
- **统一多模态 AI 服务**：llama.cpp + Qwen3-VL（HTTP 远程调用，OpenAI 兼容 / Ollama 双协议）
- 文档/图片智能提取（VLM 优先 → pymupdf → OCR 兜底链）
- AI 元数据生成（title/tags，可开关）
- **AI Wiki MCP**：6 个 tools 供 AI 工作台查询知识库（`/mcp`）
- 配置入口：前端 SettingsView"统一 AI 多模态服务"卡片 + `/api/v1/settings/extraction-config`

---

## 四、非目标（Non-Goals）

> "正交性"原则要求明确**不做什么**，避免范围蔓延。

- ❌ 不替代专业 OA / 工单系统（如需工单流转需另立项目）
- ❌ 不做实时通信/聊天
- ❌ 不做桥梁结构监测的 IoT 实时数据采集（仅做运维文档与档案）
- ❌ 不做文档多人协同编辑（仅版本快照）
- ❌ 不替代财务系统的成本核算（仅做只读统计）
- ❌ 不做横向多租户（当前为单租户部署）
- ❌ 不再开发移动端客户端（2026-09-12 起，由 AI 工作台 + AI Wiki MCP 替代）

---

## 五、关键约束与质量属性

| 属性 | 目标 |
|------|------|
| 性能 | 搜索平均 < 300ms；单文档 ≤ 10MB；100+ 并发用户 |
| 容量 | 10,000+ 文档、5,000+ 资产 |
| 安全 | JWT + Bcrypt；CORS 白名单；SQL 注入防护；XSS 过滤；类型白名单 |
| 兼容 | Win10+ / Ubuntu 18.04+ / macOS 10.15+ |
| 可扩展 | SQLite → PostgreSQL 可平滑迁移；多 AI Provider 抽象 |
| 可观测 | 结构化日志、任务状态文件、关键操作审计 |

---

## 六、默认账户（不可悄悄改动）

- 管理员：`admin` / `admin123`（**仅首次部署使用，部署后必须改密**）

---

## 七、API 概览（详情见 `docs/API接口文档.md`）

```
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
GET    /api/v1/auth/me
GET    /api/v1/documents/
PUT    /api/v1/documents/{id}
DELETE /api/v1/documents/{id}
GET    /api/v1/documents/{id}/content
GET    /api/v1/assets/                # 支持排序与筛选
POST   /api/v1/assets/batch/delete
POST   /api/v1/assets/export
POST   /api/v1/assets/file-extract    # 从文件抽取资产
GET    /api/v1/search/
GET    /api/v1/search/suggestions
GET    /api/v1/settings/users         # 管理员
POST   /api/v1/settings/users
PUT    /api/v1/settings/users/{id}
DELETE /api/v1/settings/users/{id}
```

---

## 八、未来路线图（来自 README v2.0.0 / 版本更新日志）

- 已完成 v1.0 → v2.0（资产重构、AI 集成、密码修复）
- 已完成：AI Wiki 系统（MD 副本 + FTS5 + MCP 6 tools）；Android 客户端与移动端 API 移除（2026-09-12）
- 计划：Docker 化部署、生产环境 Kubernetes 编排、MCP tools 扩展（按数据利用需求）

---

_生成时间：2026-09-11_
_下次更新时机：每完成一个里程碑或产品需求变更后_