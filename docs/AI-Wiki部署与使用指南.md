# AI Wiki 部署与使用指南（阶段十）

> 让 WorkBuddy（或其他 AI 客户端）能查询你系统的所有文档。

## 架构

```
┌──────────────────────────┐         ┌──────────────────────────────────────┐
│  主应用 (FastAPI)         │         │  WorkBuddy (或其他 MCP 客户端)        │
│  http://localhost:8002    │  HTTP   │  AI Wiki 客户端                       │
│  · 文档上传/预览/搜索    │◀───────▶│  · 调 search_kb / get_doc_content / │
│  · 提取内容为 MD 副本    │  MCP    │    list_backlinks / list_tags /     │
│  · SQLite FTS5 索引       │ /mcp/   │    generate_report                  │
│  · FastMCP 暴露 6 tools  │         │                                      │
└──────────────────────────┘         └──────────────────────────────────────┘
```

## 存储

- MD 副本：`backend/wiki/{doc_id}.md`（YAML frontmatter + Markdown 正文）
- 索引数据库：`backend/wiki/index.db`（SQLite + FTS5）
- 原文件：`backend/uploads/`（与原系统一致，不动）

## MD 副本格式

```markdown
---
title: 江苏交控网络安全培训会议七项工作建议  ← AI 生成
source_file: 阶段十-W1-final3
doc_type: docx
extracted_at: '2026-09-11T20:08:15'
tags:                                                  ← AI 生成
- 网络安全
- 江苏交控
- 培训会议
- 工作建议
- 风险整改
related: []
---

# 江苏交控网络安全培训会议七项工作建议

[完整正文...]
```

**所有字段由 AI 自动生成**（除非 `AI_METADATA_ENABLED=false` 关闭）。

## 后端 API

| Method | Path | 用途 |
|--------|------|------|
| `POST` | `/api/v1/wiki/rebuild` | 全量重建索引 |
| `GET` | `/api/v1/wiki/search?q=...&tag=...&top_k=5` | 关键词检索 |
| `GET` | `/api/v1/wiki/doc/{id}` | 取元数据 |
| `GET` | `/api/v1/wiki/doc/{id}/backlinks` | 反向链接 |
| `GET` | `/api/v1/wiki/doc/{id}/markdown` | 读 MD 副本（前端编辑器） |
| `PUT` | `/api/v1/wiki/doc/{id}/markdown` | 保存 MD 副本 |
| `GET` | `/api/v1/wiki/doc/{id}/markdown?download` | 同上但带 Content-Disposition |
| `GET` | `/api/v1/wiki/download/{id}?type=original\|markdown` | 下载文件 |
| `GET` | `/api/v1/wiki/tags?prefix=...` | 标签列表 |
| `GET` | `/api/v1/wiki/stats` | 索引统计 |
| `POST` | `/api/v1/wiki/report` | 按主题生成报告 |

## MCP Tools（给 WorkBuddy 调用）

**接入地址**：`http://localhost:8002/mcp`（HTTP transport）

**WorkBuddy 配置示例**（`mcp_config.json`）：
```json
{
  "mcpServers": {
    "ai-wiki": {
      "url": "http://localhost:8002/mcp",
      "transport": "http"
    }
  }
}
```

**暴露的 6 个 tools**：

| Tool | 输入 | 输出 |
|------|------|------|
| `search_kb` | `query, top_k, tag, doc_type` | 文档列表（含 snippet） |
| `get_doc` | `doc_id` | 文档元数据 + tags |
| `get_doc_content` | `doc_id, max_chars` | MD 副本完整内容 |
| `list_backlinks` | `doc_id` | 引用此文档的其他文档列表 |
| `list_tags` | `prefix` | 标签 + 文档数 |
| `generate_report` | `topic, tag, max_docs` | Markdown 报告骨架 |

## 配置开关（`backend/.env`）

```bash
# 是否启用 AI 自动生成 title/tags（Q5 开关）
AI_METADATA_ENABLED=true
```

## 重跑索引

任何时候可以调用：
```bash
curl -X POST http://localhost:8002/api/v1/wiki/rebuild \
  -H "Authorization: Bearer $TOKEN"
```

## 上传 + 自动 MD 副本 + 自动索引

每次上传文件，后台任务自动：
1. 提取内容（Markdown）
2. AI 生成 title + tags
3. 写入 `backend/wiki/{doc_id}.md`
4. 写入 `backend/wiki/index.db` 索引

## 已验证的端到端测试

- ✅ 上传 docx → wiki/86.md 生成（带 frontmatter）
- ✅ FTS5 检索"网络安全"返回正确结果
- ✅ MCP HTTP 端点工作（initialize + tools/call）
- ✅ get_doc 取完整元数据 + tags
- ✅ 保存 MD 后索引自动重建
- ✅ 生成报告骨架（按 tag 分组）
- ✅ 下载原文件/MD 两种类型

## 已知限制

- 链接匹配基于 wikilink 文本与文件名匹配（简化算法）
- 中文搜索效果依赖 FTS5 unicode61 分词（够用但非最优）
- 大批量重建索引较慢（SQLite 单线程）
- 暂未实现向量检索（需要语义召回时再加）

## WorkBuddy 调用示例

配置完 MCP 后，可以直接对 WorkBuddy 说：

```
"搜索所有关于网络安全的文档"
"找一下提到防火墙的资料"
"生成一份关于网络拓扑的报告"
"列出所有标签"
```

WorkBuddy 会自动调用 `search_kb` / `get_doc_content` / `generate_report` 等 tool。