#!/bin/bash
set -e

echo "🐳 Docker Backend Test"
echo "======================"

# Stop any existing container
echo "Stopping existing containers..."
docker stop gpt-oss-backend-test 2>/dev/null || true
docker rm gpt-oss-backend-test 2>/dev/null || true

# Run container
echo "Starting backend container..."
docker run -d \
  --name gpt-oss-backend-test \
  -p 8002:8001 \
  -e VLLM_BASE_URL=http://localhost:8000 \
  -e VLLM_MODEL=test-model \
  -e LOG_LEVEL=INFO \
  -v /tmp:/tmp \
  gpt-oss-backend:latest

# Wait for container to start
echo "Waiting for container to start..."
sleep 5

# Test health endpoint
echo "Testing health endpoint..."
curl -s http://localhost:8002/health | jq '.'

# Test tools list
echo "Testing tools endpoint..."
curl -s http://localhost:8002/tools | jq '.total_tools'

# Test calculator
echo "Testing calculator tool..."
curl -s -X POST http://localhost:8002/execute \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "calculator", "parameters": {"expression": "2 + 2"}}' | jq '.data.result'

# Get container logs
echo "Container logs:"
docker logs gpt-oss-backend-test --tail 10

# Cleanup
echo "Cleaning up..."
docker stop gpt-oss-backend-test
docker rm gpt-oss-backend-test

echo "✅ Docker test completed!"