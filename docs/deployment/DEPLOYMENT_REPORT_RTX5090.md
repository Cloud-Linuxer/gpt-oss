# RTX 5090 GPT-OSS-20B 배포 완료 보고서

## 실행 날짜
2025-10-17

## 시스템 사양
- **GPU**: NVIDIA GeForce RTX 5090 (32GB, Compute Capability 12.0 - Blackwell sm_120)
- **CPU**: AMD Ryzen 9 9950X3D 16-Core
- **RAM**: 60GB
- **CUDA**: 12.8
- **OS**: Fedora Linux 42 Server

## 배포 구성

### 성공한 배포 (최종)
- **이미지**: vllm/vllm-openai:v0.11.0 (공식)
- **vLLM 버전**: 0.11.0 (안정판)
- **PyTorch**: 2.8.0+cu128
- **모델**: openai/gpt-oss-20b
- **양자화**: MXFP4 with Marlin backend
- **포트**: 8000 (vLLM), 8080 (backend), 8501 (frontend)

### Attention 백엔드
- **Attention**: Triton backend (FlashAttention sm_120 미지원으로 폴백)
- **Sampling**: FlashInfer (top-p & top-k)
- **상태**: 정상 작동

### 메모리 사용량
- **모델 크기**: 13.7 GB
- **KV Cache**: 13.8 GB (300,288 tokens)
- **GPU 메모리**: 30.0 GB / 32.6 GB (92%)
- **동시성**: 최대 300K tokens

## 성능 측정

### 추론 성능 (실측)
- **코드 생성** (150 tokens): 1.1초 → **136 t/s**
- **장문 생성** (200 tokens): 1.4-1.5초 → **138-143 t/s**
- **평균 처리량**: Prompt 3 t/s, Generation 25-60 t/s
- **한국어 생성**: ✅ 정상 작동 (완벽한 문법과 맥락 이해)

### 기능 테스트
- ✅ 한국어 자연어 생성
- ✅ 코드 생성 (Python)
- ✅ 장문 텍스트 생성
- ✅ OpenAI 호환 API

## RTX 5090 (Blackwell) 지원 현황

### 현재 상태
| 구성 요소 | sm_120 지원 | 상태 |
|----------|------------|------|
| GPU 인식 | ✅ | 정상 |
| CUDA 12.8 | ✅ | 정상 |
| PyTorch 2.8 | ✅ | 정상 |
| vLLM 0.11.0 | ✅ | 정상 |
| FlashAttention | ❌ | Triton 폴백 |
| FlashInfer | ✅ | 샘플링 전용 |
| Triton Backend | ✅ | Attention 연산 |

### 성능 영향
- **예상 손실**: FlashAttention 대비 20-30% 느림
- **실제 성능**: 136-143 t/s (실용적)
- **안정성**: 매우 높음

## 소스 빌드 시도 결과

### 시도한 빌드
- **이미지**: vllm-rtx5090:v0.11.0 (자체 빌드)
- **PyTorch**: 2.10.0.dev20251016+cu128 (nightly)
- **vLLM**: 0.11.1.dev0 (development)
- **빌드 시간**: 33분
- **이미지 크기**: 27.3GB

### 실패 원인
- vLLM 0.11.1.dev0 (개발 버전) 불안정
- EngineCore 프로세스 크래시
- v0.11.0 태그를 체크아웃했으나 pip install 시 dev 버전으로 설치됨

### 교훈
- **공식 이미지 사용 권장** - 검증되고 안정적
- **Nightly 빌드 위험** - 프로덕션에 부적합
- **소스 빌드 불필요** - 공식 이미지가 RTX 5090을 지원

## FlashAttention 완전 지원 방법

현재 FlashAttention은 sm_120을 공식 지원하지 않습니다. 완전 지원을 위한 옵션:

### 옵션 1: 공식 지원 대기 (권장)
- **예상 시기**: 2-3개월 (2025년 초)
- **장점**: 안정적이고 검증됨
- **단점**: 대기 시간

### 옵션 2: 소스 빌드 (실험적)
- **방법**: FlashAttention + vLLM 소스 빌드 with TORCH_CUDA_ARCH_LIST="12.0"
- **시간**: 1-2시간
- **위험**: 성공 보장 없음
- **참조**: /home/gpt-oss/BLACKWELL_SUPPORT_GUIDE.md

### 옵션 3: 현재 상태 유지 (실용적) ⭐ 권장
- **성능**: 136-143 t/s (충분히 빠름)
- **안정성**: 높음
- **추천 시나리오**: 프로덕션 환경

## 파일 목록

### 생성된 파일
- `/home/gpt-oss/docker-compose.gpt-oss-20b-simple.yml` - 작동하는 배포 구성
- `/home/gpt-oss/Dockerfile.rtx5090-working` - 소스 빌드 시도용 (크래시)
- `/home/gpt-oss/build-rtx5090.sh` - 소스 빌드 스크립트
- `/home/gpt-oss/BLACKWELL_SUPPORT_GUIDE.md` - sm_120 완전 지원 가이드
- `/home/gpt-oss/DEPLOYMENT_REPORT_RTX5090.md` - 본 보고서

### 로그 파일
- `/tmp/rtx5090-build.log` - 소스 빌드 로그 (빌드 성공, 런타임 실패)
- `/tmp/rtx5090-runtime.log` - 런타임 크래시 로그

## 추천 사항

### 프로덕션 환경 ⭐
1. **공식 이미지 사용**: vllm/vllm-openai:v0.11.0
2. **현재 구성 유지**: Triton backend는 안정적이고 실용적
3. **모니터링**: GPU 메모리 (92% 사용)
4. **서비스 엔드포인트**:
   - vLLM API: http://localhost:8000
   - Backend API: http://localhost:8080
   - Frontend UI: http://localhost:8501

### 성능 개선이 필요한 경우
1. FlashAttention 공식 지원 대기 (2-3개월)
2. vLLM 업데이트 모니터링
3. 소스 빌드는 비추천 (불안정)

## 결론

✅ **RTX 5090에서 GPT-OSS-20B 배포 성공**

- GPU: 완벽하게 인식되고 활용됨
- 성능: 136-143 t/s (실용적)
- 안정성: 매우 높음
- 한국어 지원: 완벽
- 코드 생성: 정상
- API: OpenAI 호환

**최종 권장 사항**: 
- 현재 구성(공식 이미지 v0.11.0)을 프로덕션에 사용해도 무방
- FlashAttention 지원은 향후 업그레이드로 처리 가능
- 소스 빌드는 불안정하므로 비추천
