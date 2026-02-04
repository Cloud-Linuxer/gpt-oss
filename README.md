# GPT-OSS Deployment Project

ArgoCD/GitOps 기반 대규모 언어모델(LLM) 서비스 배포 프로젝트

## 개요

vLLM을 활용한 고성능 LLM 서비스 배포 및 관리 시스템
- **주요 모델**: GPT-OSS-20B, Qwen3 Next
- **인프라**: RTX 5090 (32GB VRAM), CUDA 12.9
- **스택**: vLLM 0.15.0 + FastAPI + Streamlit

## 빠른 시작

### GPT-OSS-20B 배포
```bash
docker-compose -f docker/compose/docker-compose.gpt-oss-20b.yml up -d
```

### 서비스 접속
- **vLLM API**: http://localhost:8000
- **Backend API**: http://localhost:8080
- **Frontend UI**: http://localhost:8501

## 프로젝트 구조

상세한 디렉토리 구조는 [PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) 참조

```
/home/gpt-oss/
├── backend/          # Backend API 서비스
├── frontend/         # Streamlit 프론트엔드
├── vllm/            # vLLM 설정 및 스크립트
├── docker/          # Docker 설정
│   ├── gpt-oss-20b/     # 프로덕션 설정
│   ├── qwen3/           # Qwen3 설정
│   └── compose/         # Docker Compose 파일
├── scripts/         # 빌드/배포/테스트 스크립트
└── docs/            # 문서
```

## 시스템 사양

- **CPU**: AMD Ryzen 9 9950X3D (16코어/32스레드, 최대 5.75GHz)
- **RAM**: 60GB
- **GPU**: NVIDIA RTX 5090 (32GB VRAM, CUDA 12.9)
- **스토리지**: 1.9TB (1.5TB 사용 가능)
- **OS**: Fedora Linux 42 Server

## 주요 명령어

### 빌드
```bash
bash scripts/build/build-stable.sh
```

### 배포
```bash
bash scripts/deploy/deploy-gpt-oss-20b.sh
```

### 테스트
```bash
bash scripts/test/test-attention-backends.sh
```

### 모니터링
```bash
docker logs -f gpt-oss-20b-vllm
bash scripts/monitoring/monitor-builds.sh
```

## 문서

- [프로젝트 구조](docs/PROJECT_STRUCTURE.md) - 전체 디렉토리 구조
- [배포 가이드](docs/deployment/) - 배포 관련 문서
- [분석 리포트](docs/reports/) - 성능 및 빌드 분석
- [사용자 가이드](docs/guides/) - 모델별 설정 가이드

## 개발 워크플로우

1. **Feature Branch 생성**
   ```bash
   git checkout -b feature/your-feature
   ```

2. **변경사항 커밋**
   ```bash
   git add .
   git commit -m "Descriptive message"
   ```

3. **푸시 및 PR**
   ```bash
   git push origin feature/your-feature
   ```

## ArgoCD GitOps

이 저장소는 ArgoCD를 통한 자동화된 배포를 지원합니다.

### ArgoCD 설정
1. 저장소를 GitHub에 푸시
2. ArgoCD에 애플리케이션 등록
3. 자동 동기화 활성화

## 환경 변수

`.env` 파일 생성 (git에서 제외됨):
```bash
HF_TOKEN=your_huggingface_token
CUDA_VISIBLE_DEVICES=0
```

## 라이센스

프로젝트별 라이센스 참조

## 기여

이슈 및 PR 환영합니다.
