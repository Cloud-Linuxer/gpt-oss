#!/bin/bash

set -e

# Default values
MODEL_NAME=${MODEL_NAME:-"facebook/opt-125m"}
MAX_MODEL_LEN=${MAX_MODEL_LEN:-4096}
GPU_MEMORY_UTIL=${GPU_MEMORY_UTIL:-0.9}
TP_SIZE=${TP_SIZE:-1}
PORT=${PORT:-8000}

echo "Starting vLLM server..."
echo "Model: $MODEL_NAME"
echo "Max model length: $MAX_MODEL_LEN"
echo "GPU memory utilization: $GPU_MEMORY_UTIL"
echo "Tensor parallel size: $TP_SIZE"
echo "Port: $PORT"
echo ""

# Check if running in Docker or native
if [ -f /.dockerenv ]; then
    echo "Running in Docker container..."
    python3 -m vllm.entrypoints.openai.api_server \
        --model "$MODEL_NAME" \
        --dtype auto \
        --host 0.0.0.0 \
        --port "$PORT" \
        --max-model-len "$MAX_MODEL_LEN" \
        --gpu-memory-utilization "$GPU_MEMORY_UTIL" \
        --tensor-parallel-size "$TP_SIZE" \
        --enable-prefix-caching \
        --enable-chunked-prefill \
        --max-num-batched-tokens 32768 \
        --max-num-seqs 256
else
    echo "Running natively (not in Docker)..."
    # Ensure vLLM is installed
    if ! python3 -c "import vllm" 2>/dev/null; then
        echo "vLLM not installed. Please install with: pip install vllm"
        exit 1
    fi
    
    python3 -m vllm.entrypoints.openai.api_server \
        --model "$MODEL_NAME" \
        --dtype auto \
        --host 0.0.0.0 \
        --port "$PORT" \
        --max-model-len "$MAX_MODEL_LEN" \
        --gpu-memory-utilization "$GPU_MEMORY_UTIL" \
        --tensor-parallel-size "$TP_SIZE" \
        --enable-prefix-caching \
        --enable-chunked-prefill \
        --max-num-batched-tokens 32768 \
        --max-num-seqs 256
fi