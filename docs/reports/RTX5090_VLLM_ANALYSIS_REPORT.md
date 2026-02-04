# RTX 5090 vLLM 커스텀 빌드 분석 보고서

## 1. Executive Summary

### 현재 상황
- **문제**: RTX 5090 (SM_120/Blackwell)에서 커스텀 vLLM 빌드가 EngineCore 세그폴트로 실패
- **공식 이미지**: vLLM 0.11.0 정상 작동 (136-143 t/s) - Triton 백엔드 사용
- **목표**: FlashAttention3 통합으로 성능 30-40% 향상 (목표: 180-200 t/s)

### 핵심 발견사항
1. 모든 어텐션 백엔드 실패 → CUDA/드라이버/ABI 불일치
2. 세그폴트 패턴: `segfault at a ip 00000000005266a0` (널 포인터 + 0xa 오프셋)
3. mxfp4 양자화는 bfloat16만 지원 (float16 불가)

## 2. 기술 환경

### 하드웨어
- **GPU**: NVIDIA GeForce RTX 5090 (32GB VRAM)
- **아키텍처**: Blackwell (SM_120, Compute Capability 12.0)
- **메모리 대역폭**: 1008 GB/s
- **드라이버**: 575.64.05

### 소프트웨어 요구사항
- **CUDA**: 12.8+ (Blackwell 지원)
- **PyTorch**: 2.10+ nightly (SM_120 커널 포함)
- **Python**: 3.11
- **vLLM**: 0.11.0

## 3. 실패 분석

### 3.1 테스트 결과

| 백엔드 | 모델 로딩 | 서버 시작 | 추론 | 실패 원인 |
|--------|-----------|-----------|------|-----------|
| FLASH_ATTN | - | - | - | 초기화 중 데드락 |
| TRITON_ATTN | ✅ 13.7GB | ✅ | ❌ | 추론 시 세그폴트 |
| FLASHINFER | - | - | - | 모듈 미설치 |

### 3.2 세그폴트 분석
```
[Mon Oct 20 09:40:29 2025] VLLM::EngineCor[1836528]: segfault at a ip 00000000005266a0
```
- **주소 0xa**: 널 포인터 + 작은 오프셋 (가상 함수 호출)
- **일관된 IP**: 동일한 코드 경로에서 반복 실패
- **타이밍**: 모델 로딩 성공 후 첫 추론에서 실패

### 3.3 근본 원인
1. **ABI 불일치**: vLLM C++ 익스텐션이 PyTorch 2.10 헤더로 컴파일되었으나 런타임 불일치
2. **SM_120 커널 문제**: RTX 5090용 어텐션 커널 미성숙
3. **빌드 프로세스 오류**: PyTorch 재설치로 인한 심볼 불일치

## 4. FlashAttention3 통합 전략

### 4.1 FA3 장점
- H100/H200에서 30-40% 성능 향상 입증
- 메모리 효율적 접근 패턴
- RTX 5090의 1008 GB/s 대역폭 최적 활용

### 4.2 구현 과제
- FA3는 현재 SM_90 (H100/H200)까지만 공식 지원
- SM_120 (Blackwell) 커널 컴파일 필요
- 소스 빌드 필수

## 5. 해결 방안

### 방안 1: FlashAttention3 소스 빌드
```dockerfile
# FA3 소스에서 SM_120 지원 추가
RUN git clone https://github.com/Dao-AILab/flash-attention.git && \
    cd flash-attention && \
    # setup.py 수정: SM_120 추가
    sed -i 's/9.0a/9.0a;12.0a/' setup.py && \
    TORCH_CUDA_ARCH_LIST="12.0" MAX_JOBS=16 \
    pip install -e .
```

### 방안 2: FlashInfer 통합
```dockerfile
# FlashInfer는 추론 최적화 특화
RUN pip install flashinfer -i https://flashinfer.ai/whl/cu128/torch2.10/
```

### 방안 3: vLLM Nightly
```dockerfile
# 최신 Blackwell 지원 포함 가능성
FROM vllm/vllm-openai:nightly
```

## 6. 다음 단계 액션 플랜

### Phase 1: FlashAttention3 빌드 (우선순위: 높음)
1. 새 Dockerfile 작성 (Dockerfile.rtx5090-fa3)
2. PyTorch 2.10 nightly 단일 설치
3. FA3 소스 빌드 with SM_120
4. vLLM 빌드 및 통합
5. 성능 테스트

### Phase 2: FlashInfer 백업 (우선순위: 중간)
1. 기존 이미지에 FlashInfer 추가
2. VLLM_ATTENTION_BACKEND=FLASHINFER 테스트
3. 성능 비교

### Phase 3: vLLM Nightly (우선순위: 낮음)
1. Nightly 이미지 풀
2. RTX 5090 호환성 테스트
3. 공식 지원 확인

## 7. 성능 목표

| 구성 | 현재 성능 | 목표 성능 | 개선율 |
|------|-----------|-----------|--------|
| 공식 vLLM (Triton) | 136-143 t/s | - | Baseline |
| 커스텀 + FA3 | - | 180-200 t/s | +30-40% |
| 커스텀 + FlashInfer | - | 160-180 t/s | +20-30% |

## 8. 리스크 및 대응

### 리스크
1. **FA3 SM_120 미지원**: 커널 컴파일 실패 가능성
2. **ABI 호환성**: PyTorch/CUDA 버전 충돌 지속
3. **시간 투자**: 소스 빌드 장시간 소요

### 대응 방안
1. 단계별 빌드로 실패 지점 격리
2. 컨테이너 레이어 캐싱 활용
3. 병렬 빌드 전략 (FA3, FlashInfer 동시)

## 9. 최종 결과 ✅

### 성공한 솔루션: vLLM Nightly

**이미지**: `vllm/vllm-openai:nightly` (v0.11.1rc2.dev161)
**성능**: **262.9 t/s** (평균, 260-264 t/s 범위)
**개선율**: **+92%** vs 공식 v0.11.0 (136-143 t/s)

### 핵심 발견사항

1. **vLLM Nightly가 RTX 5090을 완벽 지원**
   - FlashInfer autotuning 자동 적용
   - CUDA graphs 최적화 (81개 capture)
   - torch.compile 활성화
   - Marlin FP4 백엔드 사용

2. **커스텀 빌드 실패 원인**
   - PyTorch ABI 불일치 (빌드 vs 런타임 버전)
   - FA3 hopper 버전 불안정 (setup.py 오류)
   - vLLM 의존성 관리 복잡성

3. **성능 비교**
   - 공식 v0.11.0: 136-143 t/s (Triton 백엔드)
   - **Nightly v0.11.1rc2: 260-264 t/s** (FlashInfer + 최적화)
   - 목표 180-200 t/s를 **30% 초과 달성**

### 벤치마크 결과
```
Run 1: 200 tokens in 767ms = 260.75 t/s
Run 2: 200 tokens in 760ms = 263.15 t/s
Run 3: 200 tokens in 762ms = 262.46 t/s
Run 4: 200 tokens in 760ms = 263.15 t/s
Run 5: 200 tokens in 759ms = 263.50 t/s
Run 6: 200 tokens in 765ms = 261.43 t/s
Run 7: 200 tokens in 758ms = 263.85 t/s
Run 8: 200 tokens in 759ms = 263.50 t/s
Run 9: 200 tokens in 760ms = 263.15 t/s
Run 10: 200 tokens in 757ms = 264.20 t/s

평균: 262.9 t/s
```

## 10. 권장사항

### 즉시 적용 가능 (프로덕션 ready)
```bash
docker run -d --name gpt-oss-20b-vllm \
  --gpus all \
  -p 8000:8000 \
  -v /home/gpt-oss/models:/models \
  -e HF_HOME=/models \
  -e VLLM_WORKER_MULTIPROC_METHOD=spawn \
  vllm/vllm-openai:nightly \
  --model openai/gpt-oss-20b \
  --dtype bfloat16 \
  --max-model-len 8192 \
  --trust-remote-code
```

### 향후 개선 기회
- vLLM 0.12 stable 릴리스 모니터링
- FlashAttention3 SM_120 공식 지원 대기
- CUDA 12.9+ 업데이트 시 재테스트
- 더 긴 시퀀스 길이 테스트 (16K, 32K)

## 11. 결론

RTX 5090에서 vLLM nightly 이미지 사용 시 공식 v0.11.0 대비 **92% 성능 향상**을 달성했습니다.

- ❌ 커스텀 빌드: ABI 복잡성으로 실용적이지 않음
- ✅ **공식 nightly: 최적의 솔루션** (262.9 t/s)
- 🎯 목표 초과 달성: 180-200 t/s 목표를 30% 초과

**최종 권장**: vLLM nightly 이미지를 프로덕션에 즉시 적용

## 10. 부록: 디버그 로그

### 성공한 구성
- 이미지: vllm-rtx5090:fixed-abi
- 크기: 33GB
- PyTorch: 2.10.0.dev20251016+cu128
- CUDA: 12.8
- 모델 로딩: ✅ 13.7GB
- KV 캐시: ✅ 275,440 토큰
- 서버 시작: ✅
- 추론: ❌ (세그폴트)

### 주요 환경 변수
```bash
VLLM_WORKER_MULTIPROC_METHOD=spawn
VLLM_TORCH_COMPILE=0
CUDA_LAUNCH_BLOCKING=1
VLLM_ATTENTION_BACKEND=TRITON_ATTN
```

---
*작성일: 2025년 10월 20일*
*작성자: Claude Code*