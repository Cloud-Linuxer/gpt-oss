#!/bin/bash
set -e

echo "=== RTX 5090 - PyTorch 2.8.0 stable + FlashInfer ===" echo "변경사항:"
echo "  - PyTorch 2.8.0 cu128 (공식 이미지와 동일)"
echo "  - FlashInfer 설치 (공식 이미지에 있는 패키지)"
echo "  - TORCH_CUDA_ARCH_LIST=12.0"

docker build \
    -f Dockerfile.rtx5090-pytorch28 \
    -t vllm-rtx5090:pytorch28 \
    --progress=plain \
    --build-arg MAX_JOBS=8 \
    . 2>&1 | tee /tmp/pytorch28-build.log

echo ""
echo "✅ 빌드 완료!"
docker images vllm-rtx5090:pytorch28
