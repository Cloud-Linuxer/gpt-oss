#!/bin/bash
# RTX 5090 FlashAttention3 빌드 스크립트

set -e

echo "=== RTX 5090 FA3 Build Script ==="
echo "목표: FlashAttention3 with SM_120 support"
echo ""

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 빌드 시작 시간
START_TIME=$(date +%s)

# 이미지 이름
IMAGE_NAME="vllm-rtx5090:fa3"
DOCKERFILE="Dockerfile.rtx5090-fa3"

# 기존 컨테이너 정리
echo -e "${YELLOW}정리: 기존 테스트 컨테이너${NC}"
docker ps -a | grep "vllm-fa3-test" && docker rm -f vllm-fa3-test || true

# Docker 빌드
echo -e "${GREEN}빌드 시작: ${IMAGE_NAME}${NC}"
echo "BuildKit 캐시 활용..."

DOCKER_BUILDKIT=1 docker build \
    --progress=plain \
    -f ${DOCKERFILE} \
    -t ${IMAGE_NAME} \
    . 2>&1 | tee /tmp/fa3-build.log

# 빌드 완료 확인
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 빌드 성공!${NC}"

    # 이미지 정보
    echo -e "\n${YELLOW}이미지 정보:${NC}"
    docker images | grep "vllm-rtx5090.*fa3"

    # 빌드 시간 계산
    END_TIME=$(date +%s)
    BUILD_TIME=$((END_TIME - START_TIME))
    echo -e "\n${GREEN}빌드 시간: ${BUILD_TIME}초 ($(($BUILD_TIME / 60))분)${NC}"

    # 테스트 실행 옵션
    echo -e "\n${YELLOW}테스트 실행 명령어:${NC}"
    echo "docker run --rm --gpus all ${IMAGE_NAME} /test_env.sh"
    echo ""
    echo "docker run -d --name vllm-fa3-test \\"
    echo "  --gpus all \\"
    echo "  -p 8003:8000 \\"
    echo "  -v /home/gpt-oss/models:/models \\"
    echo "  ${IMAGE_NAME}"

else
    echo -e "${RED}❌ 빌드 실패!${NC}"
    echo -e "${YELLOW}로그 확인: /tmp/fa3-build.log${NC}"
    exit 1
fi