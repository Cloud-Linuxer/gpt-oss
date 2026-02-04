# RTX 5090 커스텀 빌드 시도 결과

## 날짜: 2025-10-17

## 요약: ❌ 커스텀 빌드 실패, 공식 이미지 사용 권장

---

## 시도한 빌드

### 1️⃣ 소스 빌드 (vLLM 0.11.1.dev0)
- **이미지**: vllm-rtx5090:v0.11.0
- **빌드**: ✅ 성공 (33분, 27.3GB)
- **실행**: ❌ **실패** (EngineCore 크래시)
- **PyTorch**: 2.10.0.dev (nightly)
- **vLLM**: 0.11.1.dev0 (dev 버전 설치됨)

### 2️⃣ Wheel 빌드 (vLLM 0.11.0 stable)
- **이미지**: vllm-rtx5090:stable  
- **빌드**: ✅ 성공 (5-10분, 29.2GB)
- **실행**: ❌ **실패** (EngineCore 크래시)
- **PyTorch**: 2.8.0+cu128
- **vLLM**: 0.11.0 (안정 버전)

## 실패 상황

**공통 문제**:
```
✅ 모델 로딩 성공 (13.7GB)
✅ KV Cache 할당 성공 (275K tokens)
✅ API 서버 시작 성공
❌ 첫 추론 요청: EngineCore died unexpectedly
```

**오류**:
```
ERROR: Engine core proc EngineCore_DP0 died unexpectedly
vllm.v1.engine.exceptions.EngineDeadError
```

## 공식 이미지 비교

| 항목 | 공식 이미지 ✅ | 커스텀 빌드 ❌ |
|------|----------------|----------------|
| 이미지 | vllm/vllm-openai:v0.11.0 | vllm-rtx5090:stable |
| PyTorch | 2.8.0+cu128 | 2.8.0+cu128 |
| vLLM | 0.11.0 | 0.11.0 |
| 모델 로딩 | ✅ | ✅ |
| 추론 실행 | ✅ 136-143 t/s | ❌ 크래시 |
| 안정성 | ⭐⭐⭐⭐⭐ | ❌ |

**결론**: 동일한 버전인데도 공식 이미지만 작동!

## 가능한 원인

1. **PyTorch 빌드 옵션 차이**: Wheel vs 공식 빌드
2. **CUDA 라이브러리 버전**: 세부 패키지 버전 차이
3. **시스템 라이브러리**: Python 환경 차이
4. **vLLM 컴파일 플래그**: 공식 이미지의 특별한 패치/설정

## 최종 결론

### ❌ 커스텀 빌드 포기

**이유**:
- 빌드 성공해도 **사용 불가**
- 디버깅 **불가능** (오류 원인 불명)
- 시간 낭비 (빌드 + 실패)
- 유지보수 부담

### ✅ 공식 이미지 사용 권장

**프로덕션 권장**: `vllm/vllm-openai:v0.11.0`

**장점**:
- 검증됨, 안정적
- RTX 5090 완벽 지원
- 136-143 t/s (실용적)
- 즉시 사용 가능
- 공식 지원

---

## 추가 시도 (2025-10-17 추가)

### 3️⃣ PyTorch 2.10 Nightly + SM_120 커널 빌드 (Dockerfile.rtx5090-correct)
- **빌드**: ✅ 성공 (약 35분, 31.2GB)
- **PyTorch**: 2.10.0.dev20251016+cu128
- **SM_120 커널**: ✅ 컴파일 확인됨
  - `scaled_mm_c3x_sm120.cu.o` ✅
  - `scaled_mm_sm120_fp8.cu.o` ✅
  - `nvfp4_scaled_mm_sm120_kernels.cu.o` ✅
- **ABI 문제**: ❌ PyTorch 다운그레이드로 symbol mismatch 발생
- **결과**: 런타임 ImportError

### 4️⃣ PyTorch 2.10 Nightly 재설치 수정 (Dockerfile.rtx5090-simple-fix / vllm-rtx5090:fixed)
- **빌드**: ✅ 성공 (캐시 활용, 빠름)
- **PyTorch**: 2.10.0.dev20251016+cu128 ✅ 유지
- **모델 로딩**: ✅ 성공 (13.7GB)
- **KV Cache**: ✅ 성공 (275K tokens)
- **API 서버**: ✅ 성공
- **추론**: ❌ **EngineCore 크래시 (이전과 동일)**
- **결과**: 빌드 성공, 런타임 실패

## 근본 원인 분석

**공통 실패 패턴**:
1. 모든 커스텀 빌드가 동일한 실패 지점을 보임
2. 모델 로딩, KV Cache, API 서버는 정상 작동
3. 첫 추론 요청에서 EngineCore 프로세스 크래시
4. 커널 오류 없음 (dmesg 확인)

**가능한 원인**:
1. 공식 이미지의 미공개 패치 또는 빌드 설정
2. 특정 라이브러리 버전 조합의 미묘한 호환성 문제
3. vLLM의 특정 컴파일 플래그 또는 환경 변수
4. PyTorch nightly의 특정 빌드 버전 차이

**SM_120 커널 확인**:
- ✅ 커스텀 빌드에서 SM_120 전용 커널이 정상적으로 컴파일됨
- ✅ PyTorch 2.10 nightly cu128 사용 확인
- ✅ TORCH_CUDA_ARCH_LIST="12.0" 적용 확인
- ❌ 그럼에도 런타임 크래시 발생

## 생성된 파일

- `Dockerfile.rtx5090-stable` - Wheel 빌드 (런타임 실패)
- `Dockerfile.rtx5090-working` - 소스 빌드 (런타임 실패)
- `Dockerfile.rtx5090-fixed` - 버전 고정 (미시도)
- `Dockerfile.rtx5090-correct` - PyTorch 2.10 nightly + SM_120 (ABI 문제)
- `Dockerfile.rtx5090-simple-fix` - PyTorch 재설치 (런타임 크래시)
- `build-stable.sh` - 빌드 스크립트
- `build-rtx5090-correct.sh` - 올바른 빌드 스크립트
- `/tmp/rtx5090-stable-build.log` - Stable 빌드 로그
- `/tmp/rtx5090-correct-build.log` - Correct 빌드 로그
- `/tmp/stable-build-test.log` - 크래시 로그

