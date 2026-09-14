# AI Wiki MCP 调用文档

> 本文是 **AI 工作台（WorkBuddy 等）调用 AI Wiki MCP 的权威参考**：如何接入、12 个工具各自怎么用、参数与返回格式、典型问法。
> 维护说明：工具清单必须与 `backend/app/services/wiki/mcp_server.py` 的 `register_tools` 保持一致，增删工具时同步更新本文。

## 1. 接入

**接入地址**：`http://<host>:8002/mcp`（HTTP transport，FastMCP）。

WorkBuddy 配置示例（`mcp_config.json`）：

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

> 局域网/远程使用时把 `localhost` 换成服务器 IP。MCP 端点本身**不做鉴权**（与系统其他接口一致，依赖部署在内网），因此不要把 8002 端口直接暴露到公网。

## 2. 工具总览（12 个）

| 域 | Tool | 用途 | 一句话问法 |
|----|------|------|-----------|
| 知识库 | `search_kb` | 全文检索文档 | "搜索所有关于网络安全的文档" |
| 知识库 | `get_doc` | 取单文档元数据 + 标签 | "doc 86 是什么文档" |
| 知识库 | `get_doc_content` | 取文档 MD 正文 | "把 doc 86 的正文给我" |
| 知识库 | `list_backlinks` | 反向链接（谁引用了它） | "哪些文档引用了 doc 86" |
| 知识库 | `list_tags` | 标签浏览 | "列出所有标签" |
| 知识库 | `generate_report` | 按主题/标签生成报告骨架 | "生成一份网络拓扑报告" |
| 图片 | `get_doc_images` | 列出某文档的图片 | "doc 86 里有哪些图" |
| 图片 | `search_images` | 按关键词搜图片 | "找所有网络拓扑图" |
| 图片 | `list_categories` | 业务分类浏览 | "有哪些业务分类" |
| **资产** | `search_assets` | 搜设备（含地址/账号密码） | "收费网堡垒机的地址和密码是多少" |
| **资产** | `get_asset` | 按 ID 取单台全字段 | "asset 41 的全部信息" |
| **资产** | `list_assets` | 设备轻量清单（无密码） | "收费网有哪些设备" |

## 3. 知识库域工具

### `search_kb`
```
入参: query(关键词，可空)  top_k=5  tag?  doc_type?(pdf/docx/…)  category?(运维报告/应急预案/操作规程/资产台账/拓扑与配置/会议纪要/培训材料/其他)
返回: [ { doc_id, path, title, snippet, images(已提取图片数) }, … ]
```
文档检索主入口。`query`、`tag`、`category` 可同时生效（AND）。

### `get_doc`
```
入参: doc_id
返回: 元数据 dict（title/path/doc_type/tags/related/extracted_at…）；不存在返回 { error }
```

### `get_doc_content`
```
入参: doc_id  max_chars=50000
返回: { doc_id, content(截断到 max_chars), truncated, length }
```
取 MD 副本正文，供 LLM 阅读/总结/引用。

### `list_backlinks`
```
入参: doc_id
返回: [ { src_doc_id, anchor, path, title } ]   # 引用了该文档的其他文档
```

### `list_tags`
```
入参: prefix(可选前缀过滤)
返回: [ { tag, doc_count } ]   # 按文档数排序
```

### `generate_report`
```
入参: topic?  tag?  max_docs=10  format="markdown"|"summary"
返回: { report(Markdown 骨架), doc_count, sources[ {doc_id,title,snippet} ], format }
```

## 4. 图片域工具

### `get_doc_images`
```
入参: doc_id
返回: [ { file, page, caption(AI 中文描述), url } ]
```
`url` 指向 `GET /api/v1/wiki/images/{doc_id}/{file}`，**下载需带** `Authorization: Bearer <token>`。

### `search_images`
```
入参: query(中文关键词)  top_k=10  doc_id?(限定某文档)
返回: [ { doc_id, title, file, page, caption, url } ]
```
匹配图片 AI 描述 + 文件名 + 所属文档标题。≥3 字走全文索引，1-2 字走子串匹配。

### `list_categories`
```
入参: 无
返回: [ { doc_category, doc_count } ]   # 受控词表共 8 类
```

## 5. 设备资产域工具（重点）

> 数据源：系统「设备资产管理」的 `assets` 表。账号密码在库内为**明文存储**，与 Web 端资产导出口径一致；**只在确认到具体某台设备时才返回密码**（见下方返回格式）。

### `search_assets` —— 查设备地址 / 账号密码的主入口
```
入参:
  query                 搜索关键词（设备名/IP/主机名/序列号/型号/厂商/服务名/应用/部门/位置/数据中心/MAC/标签/备注，14 字段模糊匹配，可空）
  top_k = 10            最多返回几条
  asset_type?           按类型过滤：server/network/storage/security/database/application/other（及中文类型如"信息系统"）
  network_location?     按所处网络过滤：office(办公网)/monitoring(监控网)/billing(收费网)/other
  status?               按状态过滤：active(在用)/inactive(停用)/maintenance(维护中)/retired(已退役)
```

**返回按命中数自适应**（为减少 AI 往返轮次设计）：

- **命中 1 台** → 直接返回该设备**全部字段的 dict**，一次调用即可回答"XX 设备的地址/账号密码是多少"。
- **命中 ≥2 台** → 返回摘要 + 提示：
  ```json
  {
    "total": 6,
    "assets": [
      { "id": 41, "name": "收费网调度中心核心路由器", "ip_address": "10.9.0.1",
        "hostname": null, "asset_type": "network", "status": "active", "network_location": "billing" }
    ],
    "hint": "多台命中：以上为摘要。要某台的全部信息（含账号密码）请调 get_asset(asset_id)。"
  }
  ```
  摘要**不含 username/password**（避免一次把多台设备密码全吐出来）。
- **命中 0 台** → `{ "total": 0, "assets": [] }`

单台全字段（命中唯一时返回）字段含义：
- 标识：`id` / `name` 设备名 / `asset_type` 类型 / `device_model` 型号 / `manufacturer` 厂商 / `serial_number` 序列号
- 网络：`ip_address` 地址 / `mac_address` / `hostname` 主机名 / `port` / `network_location` 所处网络
- **认证：`username` 用户名 / `password` 密码 / `ssh_key` SSH 密钥**
- 位置：`location` 物理位置 / `rack_position` 机柜 / `datacenter` 数据中心
- 配置：`os_version` / `cpu` / `memory` / `storage`
- 管理：`status` 状态 / `department` 部门 / `service_name` 服务 / `application` 应用 / `purpose` 用途
- 维护：`purchase_date` 采购日期 / `warranty_expiry` 保修到期 / `last_maintenance` / `next_maintenance`
- 其他：`notes` 备注 / `tags` 标签 / `source_file` 来源文件 / `source_document_id` / `created_at` / `updated_at`

### `get_asset`
```
入参: asset_id
返回: 单台设备全部字段（含 username / password）；不存在返回 { error: "设备不存在: asset_id=…" }
```
多台命中时，用摘要里的 `id` 调本工具取详情。

### `list_assets`
```
入参: asset_type?  network_location?  status?  limit=200
返回: [ { id, name, ip_address, hostname, asset_type, status, network_location } ]   # 轻量清单，不含账号密码
```
用于"有哪些设备 / 某网络都有什么"概览问题。要某台密码请转 `search_assets`（精确到一台）或 `get_asset`。

## 6. 典型问法 → 工具映射

| 用户问法 | 应调工具 |
|---------|---------|
| "收费网堡垒机的地址、用户名和密码是多少" | `search_assets(query="收费网堡垒机")`（唯一命中直接给全字段） |
| "172.16.8.106 这台设备的信息" | `search_assets(query="172.16.8.106")` |
| "收费网有哪些设备" | `list_assets(network_location="billing")` |
| "asset 41 的全部信息" | `get_asset(41)` |
| "安全设备里有哪些防火墙" | `search_assets(query="防火墙", asset_type="security")` |
| "找一下提到网络安全的资料" | `search_kb(query="网络安全")` |
| "找所有网络拓扑图" | `search_images(query="网络拓扑")` |
| "生成一份网络拓扑报告" | `generate_report(topic="网络拓扑")` |

## 7. 鉴权与图片下载

- MCP 工具调用本身：无需 token（端点不鉴权，依赖内网部署）。
- **图片下载例外**：`get_doc_images` / `search_images` 返回的 `url` 需 `Authorization: Bearer <token>`。token 用系统登录接口 `POST /api/v1/auth/login`（form: `username`/`password`）获取。

## 8. 已知限制

- 链接匹配基于 wikilink 文本与文件名匹配（简化算法）。
- 中文检索效果依赖 SQLite FTS5 unicode61 分词（够用但非最优）。
- 大批量重建索引较慢（SQLite 单线程）；暂未实现向量/语义检索。
- 资产查询为结构化 `LIKE` 模糊匹配（当前 ~百台量级毫秒级）；资产增长到数千台后再评估加 FTS5 全文索引。
