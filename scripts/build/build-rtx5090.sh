#!/bin/bash
set -e

echo "=== RTX 5090 vLLM 빌드 (작동 확인된 설정) ==="
echo
echo "✅ 빌드 구성:"
echo "   - PyTorch 2.9.0 nightly + CUDA 12.8"
echo "   - vLLM 0.11.0 소스 빌드"
echo "   - FlashAttention v2 (자동 포함)"
echo "   - TORCH_CUDA_ARCH_LIST=12.0"
echo
echo "⏱️  예상 시간: 30-45분"
echo "💾 필요 공간: ~15GB"
echo

# 이전 로그 백업
if [ -f /tmp/rtx5090-build.log ]; then
    mv /tmp/rtx5090-build.log /tmp/rtx5090-build.log.bak
    echo "📝 이전 로그 백업: /tmp/rtx5090-build.log.bak"
fi

echo
echo "🔨 빌드 시작..."
echo

# Docker 빌드 실행
docker build \
    -f Dockerfile.rtx5090-working \
    -t vllm-rtx5090:v0.11.0 \
    --progress=plain \
    --build-arg MAX_JOBS=8 \
    . 2>&1 | tee /tmp/rtx5090-build.log

BUILD_EXIT_CODE=${PIPESTATUS[0]}

echo
if [ $BUILD_EXIT_CODE -eq 0 ]; then
    echo "✅ 빌드 완료!"
    echo
    echo "📦 이미지: vllm-rtx5090:v0.11.0"
    echo "📋 로그: /tmp/rtx5090-build.log"
    echo
    echo "🧪 테스트 명령:"
    echo "  docker run --gpus all -p 8002:8000 \\"
    echo "    -v /home/gpt-oss/models:/models \\"
    echo "    vllm-rtx5090:v0.11.0"
    echo

    # 이미지 크기 확인
    echo "📊 이미지 정보:"
    docker images vllm-rtx5090:v0.11.0 --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
else
    echo "❌ 빌드 실패 (종료 코드: $BUILD_EXIT_CODE)"
    echo "📋 로그 확인: /tmp/rtx5090-build.log"
    echo
    echo "마지막 20줄:"
    tail -20 /tmp/rtx5090-build.log
    exit 1
fi
