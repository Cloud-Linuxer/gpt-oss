#!/bin/bash
set -e

echo "=== RTX 5090 (sm_120) 완전 지원 빌드 ==="
echo
echo "⚠️  주의사항:"
echo "   - 빌드 시간: 1-2시간"
echo "   - 디스크 공간: ~20GB 필요"
echo "   - 성공 보장 없음 (실험적)"
echo
echo "FlashAttention + vLLM을 sm_120 지원으로 소스 빌드합니다."
echo
read -p "계속하시겠습니까? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "취소됨"
    exit 0
fi

echo
echo "빌드 시작..."
docker build -f Dockerfile.blackwell-full -t gpt-oss-20b-blackwell:latest . \
    --progress=plain 2>&1 | tee /tmp/blackwell-build.log

echo
echo "빌드 완료!"
echo "로그: /tmp/blackwell-build.log"
echo
echo "테스트 실행:"
echo "  docker run --gpus all -p 8002:8000 gpt-oss-20b-blackwell:latest"
