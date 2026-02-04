# RTX 5090 커스텀 vLLM 빌드 조사 보고서

## 문제 요약
PyTorch 2.10 nightly로 빌드한 커스텀 vLLM 이미지가 첫 추론 요청 시 EngineCore 크래시

## 발견 사항

### 1. 빌드 성공 여부
- ✅ PyTorch 2.10.0.dev20251016+cu128 설치 성공
- ✅ SM_120 CUDA 커널 컴파일 성공
  ```
  Building CUDA object: scaled_mm_c3x_sm120.cu.o
  Building CUDA object: nvfp4_scaled_mm_sm120_kernels.cu.o
  ```
- ✅ vLLM 0.11.0 소스 빌드 성공 (33GB 이미지)
- ✅ ABI 문제 해결 (PyTorch 재설치로 해결)

### 2. 런타임 동작
#### 성공한 부분:
- ✅ 모델 로딩: 13.7GB in 2.78 seconds
- ✅ KV Cache 할당: 275,440 tokens
- ✅ API 서버 시작: http://0.0.0.0:8000
- ✅ 서버 health check 통과

#### 실패 지점:
- ❌ 첫 추론 요청 시 EngineCore 프로세스 즉시 종료
- ❌ Python traceback 없음 (silent crash)
- ❌ CUDA 커널 에러 없음 (dmesg 확인)

### 3. Attention Backend 테스트 결과

#### FLASH_ATTN 백엔드:
```
ERROR: AssertionError: Sinks are only supported in FlashAttention 3
```
- FlashAttention 3 패키지가 설치되어 있지 않음
- Dockerfile에서 `pip uninstall -y flash-attn` 실행했기 때문

#### TRITON_ATTN 백엔드:
```
✅ Using Triton backend on V1 engine
✅ 서버 시작 성공
❌ 첫 추론에서 EngineCore 크래시 (에러 메시지 없음)
```

### 4. 공식 이미지와 비교

| 구성 요소 | 공식 이미지 (작동) | 커스텀 빌드 (크래시) |
|----------|------------------|-------------------|
| PyTorch | **2.8.0+cu128** | **2.10.0.dev+cu128** |
| CUDA | 12.8 | 12.8 |
| vLLM | 0.11.0 | 0.11.0 |
| FlashInfer | ✅ 설치됨 | ❌ 없음 |
| Attention Backend | Triton | Triton |
| Marlin Backend | ✅ | ✅ |

### 5. 핵심 차이점
1. **PyTorch 버전**: 2.8.0 stable vs 2.10.0 nightly
2. **FlashInfer 패키지**: 공식 이미지는 FlashInfer 설치됨

공식 이미지 로그:
```
Using FlashInfer for top-p & top-k sampling  ← 중요!
Using Triton backend on V1 engine
Using Marlin backend
```

커스텀 빌드 로그:
```
FlashInfer is not available. Falling back to PyTorch-native  ← 문제!
Using Triton backend on V1 engine
Using Marlin backend
```

## 가설

### 가설 1: PyTorch 2.10 nightly 버그
- PyTorch 2.10 nightly가 SM_120에서 런타임 버그가 있을 가능성
- 컴파일은 성공하지만 실제 실행 시 segfault
- 공식 이미지는 안정 버전 2.8.0 사용

### 가설 2: FlashInfer 의존성
- FlashInfer가 top-p/top-k 샘플링에 필수일 수 있음
- 없으면 PyTorch-native fallback이 SM_120에서 문제 발생
- 공식 이미지는 FlashInfer 설치되어 있음

### 가설 3: vLLM 공식 이미지 특수 패치
- vLLM 0.11.0 공식 이미지에 RTX 5090용 특수 패치가 있을 수 있음
- 소스 빌드만으로는 동일한 동작 불가능

## 해결 시도 계획

### 시도 1: PyTorch 2.8.0 + FlashInfer (진행 중)
```dockerfile
# Dockerfile.rtx5090-pytorch28
RUN pip install torch==2.8.0 torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu128

RUN TORCH_CUDA_ARCH_LIST="12.0" pip install --no-build-isolation -v -e .

RUN pip install flashinfer -i https://flashinfer.ai/whl/cu128/torch2.8/
```

**기대 결과**: 공식 이미지와 동일한 환경 → 정상 작동 예상

### 시도 2: PyTorch 2.10 nightly + FlashInfer
만약 시도 1이 성공하면, PyTorch 2.10으로 다시 테스트

### 시도 3: 공식 이미지 분석
공식 이미지의 정확한 빌드 과정 역공학

## 기술적 통찰

### SM_120 커널 컴파일 vs 실행
- CUDA 커널이 컴파일되는 것과 실제 실행 가능한 것은 다름
- PyTorch 2.10 nightly의 SM_120 지원이 컴파일 타임에만 존재하고 런타임에는 불안정할 수 있음

### Silent Crash 패턴
- Python traceback이 없는 크래시 = C++/CUDA 레벨 에러
- 가능한 원인:
  1. Segmentation fault in CUDA kernel
  2. Invalid memory access
  3. CUDA API 호출 실패
  4. C++ exception not caught

### 사용자 가이드와의 괴리
사용자 가이드:
```
PyTorch: 2.9 cu128 또는 2.10 nightly cu128
```

실제 작동:
```
공식 이미지: PyTorch 2.8.0 cu128
```

**→ 사용자 가이드가 이상적인 요구사항이지만, 실제로는 2.8.0이 더 안정적**

## 다음 단계
1. ✅ PyTorch 2.8.0 + FlashInfer 빌드 (진행 중)
2. ⏳ 빌드 완료 후 추론 테스트
3. ⏳ 성능 비교 (공식 vs 커스텀)
4. ⏳ 결과에 따라 최종 Dockerfile 확정
