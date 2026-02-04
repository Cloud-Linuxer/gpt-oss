#!/bin/bash
# RTX 5090 optimized deployment for Qwen3-Next-80B-A3B-Instruct

set -e

echo "=== RTX 5090 Optimized Qwen3-Next-80B Deployment ==="
echo "Using PyTorch nightly + CUDA 12.8 for Blackwell (sm_120) support"
echo

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check GPU
echo "🔍 Checking RTX 5090..."
nvidia-smi --query-gpu=name,compute_cap,memory.total --format=csv,noheader
echo

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker compose -f docker-compose.qwen.yml down 2>/dev/null || true

# Build the image
echo -e "${BLUE}🔨 Building RTX 5090 optimized Docker image...${NC}"
echo "This will:"
echo "  - Install PyTorch nightly with CUDA 12.8"
echo "  - Build vLLM from source with sm_120 support"
echo "  - Configure Triton attention backend"
echo "  - Apply RTX 5090 safety settings"
echo

docker build -f Dockerfile.rtx5090 -t qwen3-rtx5090:latest . || {
    echo -e "${RED}❌ Build failed. Checking for common issues...${NC}"
    echo "  - Ensure Docker has enough disk space"
    echo "  - Check internet connectivity for package downloads"
    exit 1
}

# Start services
echo -e "${GREEN}🚀 Starting services with RTX 5090 optimizations...${NC}"
docker compose -f docker-compose.qwen.yml up -d

# Monitor startup
echo "⏳ Waiting for model to load (this may take 5-10 minutes)..."
echo "   Model size: ~160GB"
echo "   Using CPU offloading: 80GB"
echo

# Check health with longer timeout for large model
MAX_RETRIES=60  # 10 minutes
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ vLLM service is ready!${NC}"
        break
    fi
    echo -n "."
    sleep 10
    RETRY_COUNT=$((RETRY_COUNT + 1))

    # Show logs every 2 minutes
    if [ $((RETRY_COUNT % 12)) -eq 0 ]; then
        echo
        echo "📋 Current status:"
        docker logs qwen3-next-vllm --tail 5 2>&1 | grep -v "^$"
        echo
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}❌ Service failed to start within 10 minutes${NC}"
    echo "Checking logs for issues..."
    docker logs qwen3-next-vllm --tail 50
    exit 1
fi

# Display status
echo
echo "=== Deployment Status ==="
docker compose -f docker-compose.qwen.yml ps
echo

# RTX 5090 specific notes
echo -e "${BLUE}=== RTX 5090 Configuration ===${NC}"
echo "✅ PyTorch nightly with CUDA 12.8"
echo "✅ vLLM built from source with sm_120 support"
echo "✅ Triton attention backend (FlashAttention fallback)"
echo "✅ CUDA graphs disabled for stability"
echo "✅ CPU offloading enabled (80GB)"
echo

echo "=== Access Information ==="
echo "📍 API: http://localhost:8000"
echo "📍 Backend: http://localhost:8080"
echo "📍 Frontend: http://localhost:8501"
echo

echo "=== Test Commands ==="
echo "# Test API"
echo 'curl -X POST http://localhost:8000/v1/completions \'
echo '  -H "Content-Type: application/json" \'
echo '  -d "{"model": "Qwen/Qwen3-Next-80B-A3B-Instruct", "prompt": "Hello", "max_tokens": 50}"'
echo

echo -e "${GREEN}🎉 RTX 5090 optimized deployment complete!${NC}"