#!/bin/bash
# Simple deployment using official vLLM v0.11.0 image
set -e

echo "=== GPT-OSS-20B vLLM 0.11.0 Simple Deployment ==="
echo "Using official vllm/vllm-openai:v0.11.0 image"
echo

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check GPU
echo "🔍 Checking RTX 5090..."
nvidia-smi --query-gpu=name,compute_cap,memory.total --format=csv,noheader
echo

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker compose -f docker-compose.gpt-oss-20b-simple.yml down 2>/dev/null || true
echo

# Pull official image
echo -e "${BLUE}📥 Pulling vllm/vllm-openai:v0.11.0...${NC}"
docker pull vllm/vllm-openai:v0.11.0
echo

# Start services
echo -e "${GREEN}🚀 Starting services...${NC}"
docker compose -f docker-compose.gpt-oss-20b-simple.yml up -d
echo

# Monitor startup
echo "⏳ Waiting for model to load (this may take 3-5 minutes)..."
echo "   Model: openai/gpt-oss-20b (~40GB)"
echo

# Check health
MAX_RETRIES=30
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
    echo "Checking logs..."
    docker logs gpt-oss-20b-vllm --tail 50
    exit 1
fi

# Display status
echo
echo "=== Deployment Status ==="
docker compose -f docker-compose.gpt-oss-20b-simple.yml ps
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

echo -e "${GREEN}🎉 Deployment complete!${NC}"
