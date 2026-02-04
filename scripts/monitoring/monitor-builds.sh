#!/bin/bash
# 빌드 모니터링 스크립트

echo "=== RTX 5090 빌드 진행 상황 ==="
echo "시작 시간: $(date)"
echo ""

while true; do
    clear
    echo "=== 빌드 모니터링 ($(date +%H:%M:%S)) ==="
    echo ""

    # FA3 빌드 상태
    echo "📦 FlashAttention3 빌드:"
    if [ -f /tmp/fa3-build.log ]; then
        LAST_LINE=$(tail -n 1 /tmp/fa3-build.log)
        LINE_COUNT=$(wc -l < /tmp/fa3-build.log)
        echo "  로그 라인: $LINE_COUNT"
        echo "  최근: ${LAST_LINE:0:100}..."

        # 진행 단계 확인
        if grep -q "Installing collected packages" /tmp/fa3-build.log; then
            echo "  ✅ PyTorch 설치 완료"
        elif grep -q "Downloading.*torch.*cp311" /tmp/fa3-build.log; then
            echo "  🔄 PyTorch 다운로드 중"
        fi

        if grep -q "flash-attention" /tmp/fa3-build.log; then
            echo "  🔄 FlashAttention3 빌드 중"
        fi

        if grep -q "Successfully built.*vllm" /tmp/fa3-build.log; then
            echo "  ✅ vLLM 빌드 완료"
        fi
    else
        echo "  대기 중..."
    fi

    echo ""

    # FlashInfer 빌드 상태
    echo "📦 FlashInfer 빌드:"
    if [ -f /tmp/flashinfer-build.log ]; then
        LAST_LINE=$(tail -n 1 /tmp/flashinfer-build.log)
        LINE_COUNT=$(wc -l < /tmp/flashinfer-build.log)
        echo "  로그 라인: $LINE_COUNT"
        echo "  최근: ${LAST_LINE:0:100}..."

        if grep -q "flashinfer" /tmp/flashinfer-build.log; then
            echo "  🔄 FlashInfer 처리 중"
        fi
    else
        echo "  대기 중..."
    fi

    echo ""
    echo "---"
    echo "Ctrl+C로 종료 (빌드는 계속 진행됨)"

    sleep 300  # 5분마다 업데이트
done