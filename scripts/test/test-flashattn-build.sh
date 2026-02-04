#!/bin/bash
# FlashAttention sm_120 빌드 테스트 스크립트

set -e

echo "=== FlashAttention sm_120 빌드 테스트 ==="
echo
echo "⚠️  주의: 이 스크립트는 테스트용입니다"
echo "    실제 빌드는 30분~2시간 소요됩니다"
echo

# 임시 디렉토리 생성
WORK_DIR="/tmp/flashattn-test"
mkdir -p $WORK_DIR
cd $WORK_DIR

echo "1. FlashAttention 레포 클론..."
if [ ! -d "flash-attention" ]; then
    git clone --depth 1 https://github.com/Dao-AILab/flash-attention.git
fi

cd flash-attention

echo "2. sm_120 지원 확인..."
if grep -r "12.0\|sm_120" setup.py csrc/ 2>/dev/null; then
    echo "✅ sm_120 참조 발견!"
else
    echo "❌ sm_120 명시적 지원 없음"
    echo "   → 수동으로 TORCH_CUDA_ARCH_LIST 설정 필요"
fi

echo
echo "3. 빌드 명령 (실행하지 않음):"
echo "   export TORCH_CUDA_ARCH_LIST='12.0'"
echo "   export MAX_JOBS=8"
echo "   pip install packaging ninja"
echo "   pip install . --no-build-isolation"
echo
echo "실제로 빌드하시겠습니까? (y/N)"
