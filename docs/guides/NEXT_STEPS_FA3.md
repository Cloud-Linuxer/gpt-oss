# RTX 5090 FlashAttention3 통합 - 다음 단계

## 준비된 솔루션

### 1. FlashAttention3 빌드 (최우선)
```bash
# FA3 소스 빌드 (SM_120 지원)
./build-fa3.sh

# 빌드 완료 후 테스트
docker run --rm --gpus all vllm-rtx5090:fa3 /test_env.sh
```

**특징:**
- FA3 소스에서 직접 빌드
- SM_120 (RTX 5090) 지원 추가
- 예상 성능: 180-200 t/s

### 2. FlashInfer 통합 (백업)
```bash
# FlashInfer 특화 빌드
docker build -f Dockerfile.rtx5090-flashinfer -t vllm-rtx5090:flashinfer .

# 테스트
docker run --rm --gpus all vllm-rtx5090:flashinfer /test_env.sh
```

**특징:**
- 추론 특화 어텐션 구현
- 동적 시퀀스 길이 최적화
- 예상 성능: 160-180 t/s

### 3. 종합 테스트 스크립트
```bash
# 모든 어텐션 백엔드 자동 테스트
./test-attention-backends.sh vllm-rtx5090:fa3

# 결과 확인
cat /home/gpt-oss/attention_backend_test_results.md
```

**테스트 항목:**
- FLASH_ATTN
- FLASHINFER
- TRITON_ATTN
- TORCH_SDPA

## 즉시 실행 가능한 명령

### 옵션 1: FA3 빌드 시작
```bash
cd /home/gpt-oss
./build-fa3.sh
```

### 옵션 2: FlashInfer 빌드
```bash
cd /home/gpt-oss
docker build -f Dockerfile.rtx5090-flashinfer -t vllm-rtx5090:flashinfer .
```

### 옵션 3: vLLM Nightly 테스트
```bash
# 최신 nightly 이미지 풀
docker pull vllm/vllm-openai:nightly

# RTX 5090에서 테스트
docker run -d --name vllm-nightly-test \
  --gpus all \
  -p 8005:8000 \
  -v /home/gpt-oss/models:/models \
  -e HF_HOME=/models \
  -e VLLM_WORKER_MULTIPROC_METHOD=spawn \
  vllm/vllm-openai:nightly \
  --model openai/gpt-oss-20b \
  --dtype bfloat16 \
  --max-model-len 2048
```

## 문제 해결 체크리스트

### 빌드 실패 시
1. CUDA 버전 확인: `nvidia-smi` (12.8 필요)
2. 메모리 확인: `free -h` (최소 32GB)
3. 디스크 공간: `df -h` (최소 50GB)
4. 로그 확인: `/tmp/fa3-build.log`

### 런타임 실패 시
1. dmesg 확인: `sudo dmesg -T | grep -i segfault`
2. 컨테이너 로그: `docker logs <container-name>`
3. 환경 변수 확인: `docker exec <container> env | grep VLLM`
4. GPU 상태: `nvidia-smi --query-gpu=index,memory.used,temperature.gpu --format=csv`

## 성능 벤치마크 명령

```bash
# 간단한 벤치마크
time curl -X POST http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-oss-20b",
    "prompt": "Write a detailed explanation of quantum computing",
    "max_tokens": 500,
    "temperature": 0.7
  }'

# 처리량 측정
for i in {1..10}; do
  curl -s -X POST http://localhost:8000/v1/completions \
    -H "Content-Type: application/json" \
    -d '{"model":"openai/gpt-oss-20b","prompt":"Test","max_tokens":100}' \
    | jq -r '.usage.completion_tokens'
done | awk '{sum+=$1} END {print "평균 토큰/요청:", sum/NR}'
```

## 현재 상태 요약

✅ **완료:**
- 분석 보고서 작성
- FA3 Dockerfile 작성
- FlashInfer Dockerfile 작성
- 테스트 스크립트 준비
- 빌드 스크립트 준비

⏳ **대기 중:**
- FA3 빌드 실행
- FlashInfer 테스트
- vLLM nightly 테스트
- 성능 벤치마크

## 권장 실행 순서

1. **즉시:** FA3 빌드 시작 (`./build-fa3.sh`)
2. **병렬:** FlashInfer 빌드 (다른 터미널에서)
3. **빌드 후:** 종합 테스트 스크립트 실행
4. **최종:** 성능 벤치마크 및 비교

---
*준비 완료: 2025년 10월 20일*