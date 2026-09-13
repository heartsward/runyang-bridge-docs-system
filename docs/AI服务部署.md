# 统一 AI 服务部署指南（阶段七）

本系统支持用一个多模态 AI 服务（如 Qwen3-VL）同时处理 **PDF 解析 + 图片 OCR + 图片理解**。

## 推荐方案：llama.cpp 本地 server

你已经熟悉 llama.cpp。**强烈推荐**用 llama.cpp 跑 Qwen3-VL 多模态模型。

### 1. 准备模型文件

需要两个 GGUF 文件：
- 主模型（如 `Qwen3-VL-8B-Instruct-Q5_K_M.gguf`）
- 多模态投影器（`mmproj-Qwen3-VL-8B-Instruct-F16.gguf`）

从 HuggingFace 下载：
- `https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct-GGUF`

### 2. 启动 llama-server

```bash
llama-server \
  -m Qwen3-VL-8B-Instruct-Q5_K_M.gguf \
  --mmproj mmproj-Qwen3-VL-8B-Instruct-F16.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  -ngl 99 \
  -c 32768 \
  --image-min-tokens 1024
```

⚠️ **关键**：`--image-min-tokens 1024` 必须加，否则 Qwen-VL grounding 会出错。

验证：
```bash
curl http://localhost:8080/v1/models
# 返回模型列表
```

### 3. 配置主应用

在主应用 `backend/.env`：
```bash
AI_SERVICE_ENABLED=true
AI_SERVICE_PROVIDER=openai
AI_SERVICE_URL=http://localhost:8080/v1
AI_SERVICE_MODEL=qwen3-vl-8b
AI_SERVICE_TIMEOUT=120
AI_FALLBACK_TO_LOCAL=true
```

或在浏览器 SettingsView 里配置（无需改文件）。

### 4. 启动主应用

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8002
```

## 备选方案

### A. Ollama

```bash
# 拉取 Qwen3-VL（需 Ollama >= 0.3.12）
ollama pull qwen3-vl:8b

# 提供 OpenAI 兼容端点
# Ollama 默认在 http://localhost:11434
# 主应用配置：
AI_SERVICE_PROVIDER=ollama
AI_SERVICE_URL=http://localhost:11434
```

### B. vLLM（生产环境推荐）

```bash
pip install vllm
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3-VL-8B-Instruct \
  --port 8000 \
  --limit-mm-per-prompt image=4 \
  --gpu-memory-utilization 0.85
```

主应用配置：
```bash
AI_SERVICE_PROVIDER=openai
AI_SERVICE_URL=http://localhost:8000/v1
AI_SERVICE_MODEL=Qwen/Qwen3-VL-8B-Instruct
```

### C. 在线 DashScope（最简单）

```bash
AI_SERVICE_PROVIDER=openai
AI_SERVICE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
AI_SERVICE_MODEL=qwen-vl-plus
AI_SERVICE_API_KEY=你的_DashScope_API_Key
```

## 后端如何调用

主应用 PDF 提取流程：
1. 用 pymupdf 把每页 PDF 转 PNG（2x 分辨率）
2. 每 5 页一组，送 llama.cpp server 的 `/v1/chat/completions`
3. llama.cpp 用 Qwen3-VL 把图片理解成 Markdown
4. 后端合并多页输出

调用示例：
```python
import base64, requests

# PDF 第 1 页转 PNG
page_png_bytes = ...  # 来自 pymupdf

payload = {
    "model": "qwen3-vl-8b",
    "messages": [{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64.b64encode(page_png_bytes).decode()}"}},
            {"type": "text", "text": "你是文档解析引擎。请严格按原文提取以下文档内容，输出纯净 Markdown..."}
        ]
    }],
    "temperature": 0.1,
    "max_tokens": 4096
}

r = requests.post("http://localhost:8080/v1/chat/completions", json=payload, timeout=120)
content = r.json()["choices"][0]["message"]["content"]
```

## 性能对比（每页 1 张图）

| 方案 | 速度 | 显存 | 质量 |
|------|------|------|------|
| llama.cpp + Qwen3-VL-8B (Q5) | ~10s/页 | ~10GB | 优秀 |
| Ollama + qwen3-vl:8b | ~8s/页 | ~10GB | 优秀 |
| vLLM + Qwen3-VL-8B | ~3s/页（高并发）| ~16GB | 优秀 |
| DashScope qwen-vl-plus | ~2s/页（云） | 0 | 优秀 |

## 故障排查

| 现象 | 排查 |
|------|------|
| AI 调用超时 | 检查 timeout、URL、网络 |
| AI 返回 5xx | llama.cpp server 日志 |
| VLM 提取乱码 | 加 `--image-min-tokens 1024` |
| 图片加载失败 | 检查图片格式（PNG/JPG/WebP）|
| AI 失败后没降级 | 检查 `AI_FALLBACK_TO_LOCAL=true` |

## 参考

- [llama.cpp 文档](https://github.com/ggerganov/llama.cpp)
- [Qwen3-VL](https://github.com/QwenLM/Qwen2.5-VL) (注意：Qwen3-VL 仓库可能还在迁移)
- [vLLM 多模态](https://docs.vllm.ai/en/latest/serving/multimodal.html)