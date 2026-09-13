#!/bin/bash
# 统一 AI 服务启动脚本（阶段七简化版）
# 推荐：用 llama.cpp server 跑 Qwen3-VL
# 用法：
#   ./scripts/start_ai_services.sh llama-cpp    # 启动 llama.cpp server（默认）
#   ./scripts/start_ai_services.sh ollama       # 启动 Ollama
#   ./scripts/start_ai_services.sh vllm         # 启动 vLLM
#   ./scripts/start_ai_services.sh stop         # 停止 llama.cpp server

set -e

WHAT="${1:-llama-cpp}"

start_llama_cpp() {
  echo "=== 启动 llama.cpp server (端口 8080) ==="
  echo "需要准备："
  echo "  - Qwen3-VL-8B-Instruct-Q5_K_M.gguf"
  echo "  - mmproj-Qwen3-VL-8B-Instruct-F16.gguf"
  echo ""
  echo "如未启动，先安装 llama.cpp 并下载模型："
  echo "  https://github.com/ggerganov/llama.cpp"
  echo "  https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct-GGUF"
  echo ""

  MODEL="${LLAMA_MODEL:-Qwen3-VL-8B-Instruct-Q5_K_M.gguf}"
  MMPROJ="${LLAMA_MMPROJ:-mmproj-Qwen3-VL-8B-Instruct-F16.gguf}"
  PORT="${LLAMA_PORT:-8080}"

  if [ ! -f "$MODEL" ]; then
    echo "ERROR: 模型文件不存在: $MODEL"
    echo "请设置 LLAMA_MODEL 环境变量或放入当前目录"
    exit 1
  fi

  if [ ! -f "$MMPROJ" ]; then
    echo "ERROR: mmproj 文件不存在: $MMPROJ"
    exit 1
  fi

  nohup llama-server \
    -m "$MODEL" \
    --mmproj "$MMPROJ" \
    --host 0.0.0.0 \
    --port "$PORT" \
    -ngl 99 \
    -c 32768 \
    --image-min-tokens 1024 \
    > /tmp/llama-server.log 2>&1 &

  echo "  llama.cpp server 在 http://localhost:$PORT"
  echo "  测试: curl http://localhost:$PORT/v1/models"
}

start_ollama() {
  echo "=== 启动 Ollama (端口 11434) ==="
  if ! command -v ollama &>/dev/null; then
    echo "ERROR: ollama 未安装"
    exit 1
  fi
  ollama serve &
  sleep 3
  ollama pull qwen3-vl:8b
  echo "  Ollama 在 http://localhost:11434"
}

start_vllm() {
  echo "=== 启动 vLLM (端口 8000) ==="
  if ! command -v nvidia-smi &>/dev/null; then
    echo "ERROR: nvidia-smi 不可用，需要 NVIDIA GPU"
    exit 1
  fi
  python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen3-VL-8B-Instruct \
    --port 8000 \
    --limit-mm-per-prompt image=4 \
    --gpu-memory-utilization 0.85 \
    > /tmp/vllm.log 2>&1 &
  echo "  vLLM 在 http://localhost:8000/v1"
}

stop_all() {
  echo "=== 停止所有 AI 服务 ==="
  pkill -f "llama-server" 2>/dev/null || true
  pkill -f "ollama serve" 2>/dev/null || true
  pkill -f "vllm" 2>/dev/null || true
  echo "  已停止"
}

case "$WHAT" in
  llama-cpp) start_llama_cpp ;;
  ollama)    start_ollama ;;
  vllm)      start_vllm ;;
  stop)      stop_all ;;
  *)
    echo "用法: $0 {llama-cpp|ollama|vllm|stop}"
    exit 1
    ;;
esac

echo ""
echo "完成后启动主应用："
echo "  cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8002"
echo "  主应用 .env 配置："
echo "    AI_SERVICE_ENABLED=true"
echo "    AI_SERVICE_PROVIDER=openai"
echo "    AI_SERVICE_URL=http://localhost:8080/v1"
echo "    AI_SERVICE_MODEL=qwen3-vl-8b"