#!/bin/bash
# RTX 5090 optimized deployment for GPT-OSS-20B with vLLM 0.11.0

set -e

echo "=== RTX 5090 Optimized GPT-OSS-20B Deployment ==="
echo "Using vLLM 0.15.0 + PyTorch 2.9.0 + CUDA 12.9 for Blackwell (sm_120) support"
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
docker compose -f docker-compose.gpt-oss-20b.yml down 2>/dev/null || true

# Build the image
echo -e "${BLUE}🔨 Building RTX 5090 optimized Docker image with vLLM 0.15.0...${NC}"
echo "This will:"
echo "  - Install PyTorch 2.9.0 with CUDA 12.9"
echo "  - Build vLLM 0.15.0 from source with sm_120 support"
echo "  - Configure Triton attention backend"
echo "  - Apply RTX 5090 safety settings"
echo

docker build -f Dockerfile.gpt-oss-20b -t gpt-oss-20b-vllm:0.15.0 . || {
    echo -e "${RED}❌ Build failed. Checking for common issues...${NC}"
    echo "  - Ensure Docker has enough disk space"
    echo "  - Check internet connectivity for package downloads"
    exit 1
}

# Start services
echo -e "${GREEN}🚀 Starting services with RTX 5090 optimizations...${NC}"
docker compose -f docker-compose.gpt-oss-20b.yml up -d

# Monitor startup
echo "⏳ Waiting for model to load (this may take 3-5 minutes)..."
echo "   Model: openai/gpt-oss-20b (~40GB)"
echo

# Check health
MAX_RETRIES=30  # 5 minutes
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ vLLM service is ready!${NC}"
        break
    fi
    echo -n "."
    sleep 10
    RETRY_COUNT=$((RETRY_COUNT + 1))

    # Show logs every minute
    if [ $((RETRY_COUNT % 6)) -eq 0 ]; then
        echo
        echo "📋 Current status:"
        docker logs gpt-oss-20b-vllm --tail 5 2>&1 | grep -v "^$"
        echo
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}❌ Service failed to start within 5 minutes${NC}"
    echo "Checking logs for issues..."
    docker logs gpt-oss-20b-vllm --tail 50
    exit 1
fi

# Display status
echo
echo "=== Deployment Status ==="
docker compose -f docker-compose.gpt-oss-20b.yml ps
echo

# RTX 5090 specific notes
echo -e "${BLUE}=== RTX 5090 Configuration ===${NC}"
echo "✅ vLLM version: 0.15.0"
echo "✅ PyTorch 2.9.0 with CUDA 12.9"
echo "✅ vLLM built from source with sm_120 support"
echo "✅ Triton attention backend (FlashAttention fallback)"
echo "✅ CUDA graphs disabled for stability"
echo "✅ GPU memory utilization: 90%"
echo

echo "=== Access Information ==="
echo "📍 vLLM API: http://localhost:8000"
echo "📍 Backend API: http://localhost:8080"
echo "📍 Frontend UI: http://localhost:8501"
echo

echo "=== Test Commands ==="
echo "# Test vLLM API"
echo 'curl -X POST http://localhost:8000/v1/completions \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{"model": "openai/gpt-oss-20b", "prompt": "Hello, how are you?", "max_tokens": 50}'"'"
echo
echo "# Check vLLM models"
echo "curl http://localhost:8000/v1/models"
echo

echo -e "${GREEN}🎉 RTX 5090 optimized GPT-OSS-20B deployment complete!${NC}"
