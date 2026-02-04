#!/bin/bash
# vLLM Nightly 성능 벤치마크

echo "=== vLLM Nightly RTX 5090 성능 벤치마크 ==="
echo "시작 시간: $(date)"
echo ""

for i in {1..10}; do
  START=$(date +%s%N)
  RESPONSE=$(curl -s -X POST http://localhost:8006/v1/completions \
    -H "Content-Type: application/json" \
    -d '{
      "model": "openai/gpt-oss-20b",
      "prompt": "Write a detailed explanation about artificial intelligence:",
      "max_tokens": 200,
      "temperature": 0.7
    }')
  END=$(date +%s%N)

  TOKENS=$(echo $RESPONSE | grep -o '"completion_tokens":[0-9]*' | grep -o '[0-9]*')
  ELAPSED=$(( ($END - $START) / 1000000 ))

  if [ ! -z "$TOKENS" ] && [ "$TOKENS" -gt 0 ]; then
    TOKENSEC=$(echo "scale=2; $TOKENS * 1000 / $ELAPSED" | bc)
    echo "Run $i: $TOKENS tokens in ${ELAPSED}ms = $TOKENSEC t/s"
  else
    echo "Run $i: Failed"
  fi

  sleep 1
done

echo ""
echo "벤치마크 완료: $(date)"
