# RTX 5090 (sm_120) 완전 지원 가이드

## 현재 상태
- ❌ FlashAttention: sm_120 미지원 → Triton 우회
- ⚠️ 성능: 20-30% 저하

## 해결 방법

### Option 1: FlashAttention 3.x 소스 빌드 (권장)

#### 1-1. FlashAttention GitHub에서 sm_120 지원 확인
```bash
# FlashAttention 레포 확인
git clone https://github.com/Dao-AILab/flash-attention.git
cd flash-attention
git log --oneline | grep -i "blackwell\|sm_120\|5090"
```

#### 1-2. sm_120 지원 버전으로 빌드
```bash
# 환경 설정
export TORCH_CUDA_ARCH_LIST="12.0"
export MAX_JOBS=8

# FlashAttention 빌드
pip install packaging ninja
cd csrc/flash_attn
python setup.py install
```

#### 1-3. vLLM에 적용
```bash
# vLLM 재빌드
cd /path/to/vllm
TORCH_CUDA_ARCH_LIST="12.0" pip install -e . --no-build-isolation
```

### Option 2: vLLM + FlashAttention 소스 빌드 Docker

#### 2-1. Dockerfile 생성
```dockerfile
FROM nvidia/cuda:12.8.0-devel-ubuntu22.04

# PyTorch nightly with CUDA 12.8
RUN pip install --pre torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/nightly/cu128

# FlashAttention with sm_120
ENV TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0;12.0"
RUN pip install packaging ninja wheel
RUN git clone https://github.com/Dao-AILab/flash-attention.git && \
    cd flash-attention && \
    MAX_JOBS=8 pip install -v . --no-build-isolation

# vLLM with sm_120
RUN git clone https://github.com/vllm-project/vllm.git && \
    cd vllm && \
    TORCH_CUDA_ARCH_LIST="12.0" MAX_JOBS=8 pip install -v .
```

#### 2-2. 빌드 및 실행
```bash
docker build -f Dockerfile.blackwell -t vllm-blackwell:latest .
docker run --gpus all -p 8000:8000 vllm-blackwell:latest
```

### Option 3: PyTorch Nightly + 최신 라이브러리

```bash
# PyTorch nightly (최신 CUDA 지원)
pip install --pre torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/nightly/cu128

# FlashAttention nightly
pip install flash-attn --no-build-isolation \
    --extra-index-url https://flash-attn.github.io/flash-attn/

# vLLM nightly
pip install vllm-nightly
```

### Option 4: 공식 지원 대기

FlashAttention 및 vLLM 공식 릴리스에서 sm_120 지원 추가 대기
- 예상 시기: 2025년 초 (RTX 5090 출시 후 몇 달)
- 추적: 
  - https://github.com/Dao-AILab/flash-attention/issues
  - https://github.com/vllm-project/vllm/issues

## 성능 향상 예상

현재 Triton → FlashAttention 전환 시:
- Prompt Throughput: 9.9 → 15-20 tokens/s (50-100% 향상)
- Generation Throughput: 20 → 30-40 tokens/s (50-100% 향상)
- Latency: 20-30% 감소

## 리스크

### 소스 빌드 리스크
- ⚠️ 빌드 시간: 30분 ~ 2시간
- ⚠️ 실패 가능성: CUDA/PyTorch 버전 충돌
- ⚠️ 안정성: 테스트되지 않은 조합

### 권장 접근
1. **현재 유지**: 안정적인 v0.11.0 사용
2. **테스트 환경**: 별도 컨테이너에서 소스 빌드 테스트
3. **공식 대기**: 2-3개월 후 공식 지원 사용

## 현재 최적 설정 (우회)

Triton backend로도 충분한 성능:
- ✅ 안정성: 검증됨
- ✅ 성능: 실용적 (9.9/20 t/s)
- ✅ 메모리 효율: MXFP4 양자화
