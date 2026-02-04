#!/bin/bash
# RTX 5090 어텐션 백엔드 테스트 스크립트
# 모든 백엔드를 체계적으로 테스트

set -e

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 테스트 설정
IMAGE_NAME=${1:-"vllm-rtx5090:fa3"}
MODEL="openai/gpt-oss-20b"
PORT=8004

echo -e "${BLUE}=== RTX 5090 어텐션 백엔드 종합 테스트 ===${NC}"
echo -e "이미지: ${IMAGE_NAME}"
echo -e "모델: ${MODEL}"
echo ""

# 테스트할 백엔드 목록
BACKENDS=("FLASH_ATTN" "FLASHINFER" "TRITON_ATTN" "TORCH_SDPA")

# 결과 저장 파일
RESULT_FILE="/home/gpt-oss/attention_backend_test_results.md"
echo "# RTX 5090 어텐션 백엔드 테스트 결과" > $RESULT_FILE
echo "" >> $RESULT_FILE
echo "테스트 시간: $(date)" >> $RESULT_FILE
echo "이미지: $IMAGE_NAME" >> $RESULT_FILE
echo "" >> $RESULT_FILE
echo "| 백엔드 | 시작 | 로딩 | 추론 | 성능(t/s) | 상태 |" >> $RESULT_FILE
echo "|--------|------|------|------|-----------|------|" >> $RESULT_FILE

# 각 백엔드 테스트
for BACKEND in "${BACKENDS[@]}"; do
    echo -e "\n${YELLOW}테스트: $BACKEND${NC}"

    # 기존 컨테이너 정리
    docker rm -f test-$BACKEND 2>/dev/null || true

    # 컨테이너 시작
    echo "컨테이너 시작..."
    docker run -d --name test-$BACKEND \
        --gpus all \
        -p ${PORT}:8000 \
        -v /home/gpt-oss/models:/models \
        -e HF_HOME=/models \
        -e VLLM_WORKER_MULTIPROC_METHOD=spawn \
        -e VLLM_TORCH_COMPILE=0 \
        -e CUDA_LAUNCH_BLOCKING=1 \
        -e VLLM_ATTENTION_BACKEND=$BACKEND \
        $IMAGE_NAME \
        python -m vllm.entrypoints.openai.api_server \
            --model $MODEL \
            --dtype bfloat16 \
            --max-model-len 2048 \
            --host 0.0.0.0 \
            --port 8000 \
            --trust-remote-code \
            --enforce-eager \
            --disable-custom-all-reduce 2>&1 | tee /tmp/${BACKEND}_start.log &

    # 시작 대기
    sleep 5

    # 시작 상태 확인
    if docker ps | grep -q test-$BACKEND; then
        START_STATUS="✅"
        echo -e "${GREEN}✅ 컨테이너 시작됨${NC}"
    else
        START_STATUS="❌"
        echo -e "${RED}❌ 컨테이너 시작 실패${NC}"
        echo "| $BACKEND | $START_STATUS | - | - | - | 시작 실패 |" >> $RESULT_FILE
        continue
    fi

    # 모델 로딩 대기 (최대 60초)
    echo "모델 로딩 대기..."
    LOADING_STATUS="❌"
    for i in {1..60}; do
        if docker logs test-$BACKEND 2>&1 | grep -q "Application startup complete"; then
            LOADING_STATUS="✅"
            echo -e "${GREEN}✅ 모델 로딩 완료 (${i}초)${NC}"
            break
        fi

        # EngineCore 죽음 확인
        if docker logs test-$BACKEND 2>&1 | grep -q "EngineCore.*died"; then
            LOADING_STATUS="❌"
            echo -e "${RED}❌ EngineCore 죽음${NC}"
            break
        fi

        sleep 1
    done

    if [ "$LOADING_STATUS" == "❌" ]; then
        echo "| $BACKEND | $START_STATUS | $LOADING_STATUS | - | - | 로딩 실패 |" >> $RESULT_FILE
        docker logs test-$BACKEND 2>&1 | tail -20 > /tmp/${BACKEND}_error.log
        continue
    fi

    # 추론 테스트
    echo "추론 테스트..."
    INFERENCE_STATUS="❌"
    PERFORMANCE="-"

    START_TIME=$(date +%s%N)
    RESPONSE=$(curl -s -X POST http://localhost:${PORT}/v1/completions \
        -H "Content-Type: application/json" \
        -d '{
            "model": "'$MODEL'",
            "prompt": "The capital of France is",
            "max_tokens": 50,
            "temperature": 0.1
        }' --max-time 10 2>&1 || echo "FAILED")
    END_TIME=$(date +%s%N)

    if echo "$RESPONSE" | grep -q "choices"; then
        INFERENCE_STATUS="✅"
        echo -e "${GREEN}✅ 추론 성공${NC}"

        # 응답 시간 계산
        ELAPSED=$((($END_TIME - $START_TIME) / 1000000))
        TOKENS=$(echo "$RESPONSE" | grep -oP '"completion_tokens":\s*\K\d+' || echo "0")

        if [ "$TOKENS" -gt 0 ]; then
            PERFORMANCE=$(echo "scale=2; $TOKENS * 1000 / $ELAPSED" | bc)
            echo -e "${GREEN}성능: ${PERFORMANCE} tokens/s${NC}"
        fi

        echo "$RESPONSE" | jq '.' > /tmp/${BACKEND}_response.json 2>/dev/null || true
    else
        echo -e "${RED}❌ 추론 실패${NC}"
        echo "$RESPONSE" > /tmp/${BACKEND}_inference_error.log
    fi

    # 결과 기록
    if [ "$INFERENCE_STATUS" == "✅" ]; then
        STATUS="정상 작동"
    else
        STATUS="추론 실패"
    fi

    echo "| $BACKEND | $START_STATUS | $LOADING_STATUS | $INFERENCE_STATUS | $PERFORMANCE | $STATUS |" >> $RESULT_FILE

    # 컨테이너 정리
    docker stop test-$BACKEND 2>/dev/null || true
    docker rm test-$BACKEND 2>/dev/null || true

    echo "---"
done

# 최종 결과 출력
echo -e "\n${BLUE}=== 테스트 결과 ===${NC}"
cat $RESULT_FILE

# 로그 파일 위치
echo -e "\n${YELLOW}로그 파일 위치:${NC}"
echo "- 결과 요약: $RESULT_FILE"
echo "- 개별 로그: /tmp/*_*.log"

# 가장 성능 좋은 백엔드 찾기
echo -e "\n${GREEN}추천 설정:${NC}"
if grep -q "✅.*✅.*✅" $RESULT_FILE; then
    BEST=$(grep "✅.*✅.*✅" $RESULT_FILE | head -1 | cut -d'|' -f2 | tr -d ' ')
    echo "VLLM_ATTENTION_BACKEND=$BEST"
else
    echo -e "${RED}작동하는 백엔드를 찾지 못했습니다.${NC}"
fi