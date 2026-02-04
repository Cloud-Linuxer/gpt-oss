# RTX 5090 (Blackwell) 지원 상태

## 현재 구성 (vLLM 0.11.0 공식 이미지)
- ✅ GPU 인식: RTX 5090 (sm_120)
- ✅ CUDA 12.8 호환
- ⚠️ Attention: Triton (FlashAttention 미지원)
- ⚠️ CUDA Graphs: Disabled
- ✅ Quantization: MXFP4 with Marlin

## 성능 영향
- Triton backend는 FlashAttention보다 느림 (약 20-30% 성능 저하)
- CUDA graphs 미사용으로 배치 처리 성능 저하
- 단일 요청 처리는 정상적으로 작동

## 완전한 블랙웰 지원 방법

### Option 1: FlashAttention 3.0+ 소스 빌드 (권장)
```bash
# FlashAttention 3.0+ with sm_120 support
pip install flash-attn --no-build-isolation \
  --extra-index-url https://flash-attn.github.io/flash-attn/
```

### Option 2: vLLM Nightly Build
```bash
docker pull vllm/vllm-openai:nightly
# or
pip install vllm-nightly
```

### Option 3: 소스에서 빌드 (최적화)
```bash
# PyTorch nightly + vLLM source build
TORCH_CUDA_ARCH_LIST="12.0" pip install -e .
```

## 현재 설정으로 사용 가능 여부
✅ **예, 사용 가능합니다!**
- 추론은 정상 작동
- 성능은 최적화되지 않았지만 실용적
- 한국어, 코드 생성 모두 정상

## 성능 측정 결과
- Prompt Throughput: 9.9 tokens/s
- Generation Throughput: 20.0 tokens/s
- GPU Memory: 30GB / 32GB (92%)

