#!/bin/bash
set -e

echo "Building vLLM with PyTorch 2.9.0 + CUDA 12.8 for RTX 5090..."
echo "=================================================="

# Image name
IMAGE_NAME="vllm-rtx5090:torch29"

# Build with BuildKit for better caching
export DOCKER_BUILDKIT=1

# Build the Docker image
echo "Starting Docker build..."
docker build \
    --progress=plain \
    -f Dockerfile.torch29 \
    -t ${IMAGE_NAME} \
    .

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    echo "Image: ${IMAGE_NAME}"
    
    # Show image info
    docker images | grep ${IMAGE_NAME}
    
    echo ""
    echo "To test CUDA capability detection:"
    echo "docker run --gpus all ${IMAGE_NAME} python -c \"import torch; print(torch.cuda.get_device_capability())\""
    
    echo ""
    echo "To run vLLM server:"
    echo "docker run --gpus all -p 8000:8000 -v \$PWD/models:/models ${IMAGE_NAME} \\"
    echo "  python -m vllm.entrypoints.openai.api_server \\"
    echo "  --model /models/your-model \\"
    echo "  --host 0.0.0.0"
else
    echo "❌ Build failed!"
    exit 1
fi