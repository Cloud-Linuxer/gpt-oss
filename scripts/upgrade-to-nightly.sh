#!/bin/bash
set -e

echo "=== vLLM Nightly로 업그레이드 ==="
echo

# 현재 컨테이너 중지
echo "🛑 현재 컨테이너 중지..."
docker compose -f docker-compose.gpt-oss-20b-simple.yml down

# Nightly 이미지 pull
echo "📥 vLLM nightly 이미지 다운로드..."
docker pull vllm/vllm-openai:nightly

# docker-compose 파일 백업
cp docker-compose.gpt-oss-20b-simple.yml docker-compose.gpt-oss-20b-simple.yml.backup

# Nightly 버전으로 변경
sed -i 's|vllm/vllm-openai:v0.11.0|vllm/vllm-openai:nightly|g' docker-compose.gpt-oss-20b-simple.yml

echo "✅ 설정 업데이트 완료"
echo
echo "배포하려면:"
echo "  docker compose -f docker-compose.gpt-oss-20b-simple.yml up -d"
echo
echo "원래 버전으로 복구하려면:"
echo "  mv docker-compose.gpt-oss-20b-simple.yml.backup docker-compose.gpt-oss-20b-simple.yml"
