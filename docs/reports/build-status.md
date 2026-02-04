# RTX 5090 빌드 상태

**업데이트**: 2025-10-20 13:22 KST

## 시작 시간
2025-10-20 09:40 KST

## FlashAttention3 빌드 (vllm-rtx5090:fa3)

### 상태: ❌ 빌드 실패

**실패 원인**: FlashAttention3 hopper/setup.py에서 setuptools import 실패

### 진행 단계
- [x] 시스템 패키지 설치
- [x] Python 3.11 설정
- [x] pip 업그레이드
- [x] PyTorch 2.10 nightly 다운로드 완료
- [x] FlashAttention3 소스 클론
- [❌] FA3 빌드 (setup.py 오류)

### 해결 방안
1. FlashAttention3 main 브랜치 사용 (hopper 디렉토리 제외)
2. 또는 v2 stable 브랜치 사용

### 예상 소요 시간
- PyTorch 다운로드: ~10분
- FA3 빌드: ~15분
- vLLM 빌드: ~10분
- **총 예상 시간: ~35-40분**

### 빌드 명령
```bash
./build-fa3.sh
```

### 로그 위치
`/tmp/fa3-build.log`

## FlashInfer 빌드 (vllm-rtx5090:flashinfer)

### 상태: ⚠️ 부분 성공 (ABI 문제)

**이미지 빌드**: ✅ 성공 (33.4GB)
**런타임 문제**: ❌ PyTorch ABI 불일치

### 진행 단계
- [x] Dockerfile 로드
- [x] 시스템 패키지 설치
- [x] Python 3.11 설정
- [x] pip 업그레이드
- [x] PyTorch 2.8.0 설치됨 (2.10 nightly 대신)
- [⚠️] FlashInfer 설치 실패 (소스 빌드 필요)
- [x] vLLM 빌드 완료
- [❌] ABI 불일치로 런타임 실패

### 문제
- vLLM이 PyTorch 2.10 nightly로 컴파일
- 런타임에 PyTorch 2.8.0 설치됨
- Symbol 불일치: `_ZN3c104cuda29c10_cuda_check_implementationEiPKcS2_jb`

### 예상 소요 시간
- **총 예상 시간: ~30-35분**

### 빌드 명령
```bash
docker build -f Dockerfile.rtx5090-flashinfer -t vllm-rtx5090:flashinfer .
```

### 로그 위치
`/tmp/flashinfer-build.log`

## 다음 단계
1. 빌드 완료 대기 (~40분)
2. 환경 검증: `docker run --rm --gpus all <image> /test_env.sh`
3. 종합 테스트: `./test-attention-backends.sh <image>`
4. 성능 벤치마크

## 모니터링
```bash
# 실시간 로그
tail -f /tmp/fa3-build.log
tail -f /tmp/flashinfer-build.log

# 빌드 프로세스
ps aux | grep docker

# 디스크 사용량
df -h
```

---
*업데이트: 자동 업데이트 없음 - 로그 파일 참조*