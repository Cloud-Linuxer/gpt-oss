#!/bin/bash
set -e

echo "=== RTX 5090 안정 버전 빌드 ==="
echo
echo "방법 선택:"
echo "  1) Wheel 사용 (빠름, 5-10분) ⭐ 권장"
echo "  2) 소스 빌드 (느림, 30-40분)"
echo
read -p "선택 (1 또는 2): " choice

case $choice in
    1)
        DOCKERFILE="Dockerfile.rtx5090-stable"
        TAG="vllm-rtx5090:stable"
        echo "✅ Wheel 버전 빌드 (vllm==0.11.0)"
        ;;
    2)
        DOCKERFILE="Dockerfile.rtx5090-fixed"
        TAG="vllm-rtx5090:fixed"
        echo "✅ 소스 빌드 (버전 고정)"
        ;;
    *)
        echo "❌ 잘못된 선택"
        exit 1
        ;;
esac

echo
echo "🔨 빌드 시작: $TAG"
echo "📝 로그: /tmp/rtx5090-stable-build.log"
echo

docker build \
    -f $DOCKERFILE \
    -t $TAG \
    --progress=plain \
    . 2>&1 | tee /tmp/rtx5090-stable-build.log

if [ $? -eq 0 ]; then
    echo
    echo "✅ 빌드 완료!"
    echo "📦 이미지: $TAG"
    echo
    echo "🧪 테스트 실행:"
    echo "  docker run --gpus all --rm -p 8002:8000 \\"
    echo "    -v /home/gpt-oss/models:/models \\"
    echo "    $TAG"
    echo
    docker images $TAG
else
    echo "❌ 빌드 실패"
    exit 1
fi
