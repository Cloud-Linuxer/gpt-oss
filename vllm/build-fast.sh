#!/bin/bash

echo "=== 빠른 Docker 빌드 스크립트 ==="

# 1. 의존성 파일이 없으면 다운로드
if [ ! -d "./deps/wheels" ] || [ -z "$(ls -A ./deps/wheels 2>/dev/null)" ]; then
    echo "의존성 파일이 없습니다. 다운로드를 시작합니다..."
    chmod +x download-deps.sh
    ./download-deps.sh
else
    echo "사전 다운로드된 의존성 파일 사용"
    ls -lh ./deps/wheels | head -5
fi

# 2. Docker 빌드 (캐시 활용)
echo "Docker 이미지 빌드 시작..."
DOCKER_BUILDKIT=1 docker build \
    -f Dockerfile.fast \
    -t vllm-rtx5090:fast \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    --cache-from vllm-rtx5090:fast \
    .

if [ $? -eq 0 ]; then
    echo "=== 빌드 완료 ==="
    echo "이미지: vllm-rtx5090:fast"
    echo ""
    echo "실행 방법:"
    echo "  docker run --gpus all -p 8000:8000 vllm-rtx5090:fast \\"
    echo "    --model facebook/opt-125m --host 0.0.0.0"
else
    echo "빌드 실패!"
    exit 1
fi