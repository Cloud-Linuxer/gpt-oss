#!/bin/bash
set -e

echo "=== RTX 5090 (SM_120) ABI 수정 빌드 ==="
echo "✅ 변경사항:"
echo "   - vLLM 빌드 후 PyTorch 2.10 nightly 재설치"
echo "   - --force-reinstall --no-deps로 ABI 일치"

docker build \
    -f Dockerfile.rtx5090-fixed-abi \
    -t vllm-rtx5090:fixed-abi \
    --progress=plain \
    --build-arg MAX_JOBS=8 \
    . 2>&1 | tee /tmp/rtx5090-fixed-abi-build.log

echo ""
echo "✅ 빌드 완료!"
docker images vllm-rtx5090:fixed-abi
