#!/bin/bash
set -e

echo "=== RTX 5090 (SM_120) 올바른 빌드 ==="
echo
echo "✅ 빌드 구성:"
echo "   - PyTorch 2.10 nightly cu128 (SM_120 커널 포함)"
echo "   - vLLM 0.11.0 소스 빌드"
echo "   - TORCH_CUDA_ARCH_LIST=\"12.0\""
echo "   - FlashAttention 외부 패키지 제거"
echo
echo "⏱️  예상 시간: 30-40분"
echo "💾 필요 공간: ~15GB"
echo

# 로그 백업
if [ -f /tmp/rtx5090-correct-build.log ]; then
    mv /tmp/rtx5090-correct-build.log /tmp/rtx5090-correct-build.log.bak
fi

echo "🔨 빌드 시작..."
echo

docker build \
    -f Dockerfile.rtx5090-correct \
    -t vllm-rtx5090:correct \
    --progress=plain \
    --build-arg MAX_JOBS=8 \
    . 2>&1 | tee /tmp/rtx5090-correct-build.log

BUILD_EXIT_CODE=${PIPESTATUS[0]}

echo
if [ $BUILD_EXIT_CODE -eq 0 ]; then
    echo "✅ 빌드 완료!"
    echo
    echo "📦 이미지: vllm-rtx5090:correct"
    echo "📋 로그: /tmp/rtx5090-correct-build.log"
    echo
    echo "🧪 버전 확인:"
    docker run --rm vllm-rtx5090:correct python -c \
        "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.version.cuda}'); print(f'Device Cap: {torch.cuda.get_device_capability(0) if torch.cuda.is_available() else \"N/A\"}')" 2>/dev/null || true
    echo
    echo "📊 이미지 정보:"
    docker images vllm-rtx5090:correct --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
else
    echo "❌ 빌드 실패 (종료 코드: $BUILD_EXIT_CODE)"
    echo "📋 로그: /tmp/rtx5090-correct-build.log"
    exit 1
fi
