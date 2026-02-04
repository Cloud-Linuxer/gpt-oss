# GPT-OSS Project Structure

## Overview
Organized workspace structure for GPT-OSS deployment with ArgoCD/GitOps setup.

## Directory Structure

```
/home/gpt-oss/
├── backend/              # Backend services and API
├── frontend/             # Frontend Streamlit application
├── vllm/                 # vLLM configuration and scripts
├── models/               # Model storage directory
├── docker/               # Docker configurations
│   ├── gpt-oss-20b/      # GPT-OSS-20B model Docker files
│   ├── qwen3/            # Qwen3 model Docker files
│   ├── rtx5090-experimental/  # RTX 5090 experimental builds
│   └── compose/          # Docker Compose configurations
├── scripts/              # Utility scripts
│   ├── build/            # Build scripts
│   ├── deploy/           # Deployment scripts
│   ├── test/             # Testing scripts
│   └── monitoring/       # Monitoring scripts
├── docs/                 # Documentation
│   ├── deployment/       # Deployment reports and guides
│   ├── architecture/     # Architecture documentation
│   ├── guides/           # User guides and tutorials
│   └── reports/          # Analysis and status reports
└── .env                  # Environment variables (not tracked)
```

## Active Deployments

### GPT-OSS-20B (Production)
- **Docker Compose**: `docker/compose/docker-compose.gpt-oss-20b.yml`
- **Dockerfile**: `docker/gpt-oss-20b/Dockerfile.gpt-oss-20b`
- **vLLM Version**: 0.15.0
- **Model**: openai/gpt-oss-20b
- **Services**:
  - vLLM API: port 8000
  - Backend: port 8080
  - Frontend: port 8501

### Qwen3 Next (Experimental)
- **Docker Compose**: `docker/compose/docker-compose.qwen.yml`
- **Dockerfiles**: `docker/qwen3/`
- **Support Scripts**: `docker/qwen3/qwen3_next_support.py`, `vllm_qwen3_startup.py`

## Scripts Reference

### Build Scripts (`scripts/build/`)
- `build-rtx5090.sh` - Standard RTX 5090 build
- `build-stable.sh` - Stable production build
- `build-blackwell.sh` - Blackwell architecture build
- `build-fa3.sh` - FlashAttention 3 build
- `build-pytorch28.sh` - PyTorch 2.8 build

### Deploy Scripts (`scripts/deploy/`)
- `deploy-gpt-oss-20b.sh` - Deploy GPT-OSS-20B service
- `deploy-qwen.sh` - Deploy Qwen3 service
- `deploy-rtx5090.sh` - Deploy RTX 5090 experimental
- `deploy-simple.sh` - Simple deployment

### Test Scripts (`scripts/test/`)
- `benchmark-nightly.sh` - Nightly benchmarking
- `test-attention-backends.sh` - Test attention mechanisms
- `test-flashattn-build.sh` - FlashAttention build tests

### Monitoring Scripts (`scripts/monitoring/`)
- `monitor-builds.sh` - Monitor build processes

## Documentation

### Deployment Documentation (`docs/deployment/`)
- `DEPLOYMENT_REPORT_RTX5090.md` - RTX 5090 deployment analysis
- `DEPLOYMENT_REPORT_RTX5090_Qwen3Next80B.md` - Qwen3 Next deployment

### Guides (`docs/guides/`)
- `BLACKWELL_SUPPORT_GUIDE.md` - Blackwell architecture support
- `NEXT_STEPS_FA3.md` - FlashAttention 3 implementation
- `README-qwen.md` - Qwen model setup guide

### Reports (`docs/reports/`)
- `BLACKWELL_STATUS.md` - Blackwell support status
- `CUSTOM_BUILD_INVESTIGATION.md` - Custom build analysis
- `CUSTOM_BUILD_RESULTS.md` - Build results
- `RTX5090_VLLM_ANALYSIS_REPORT.md` - vLLM RTX 5090 analysis
- `FINAL_SUMMARY.md` - Project summary
- `build-status.md` - Current build status

## System Specifications
- **CPU**: AMD Ryzen 9 9950X3D 16-Core (32 threads, up to 5.75 GHz)
- **RAM**: 60GB
- **GPU**: NVIDIA GeForce RTX 5090 (32GB VRAM, CUDA 12.9)
- **Storage**: 1.9TB (1.5TB available)
- **OS**: Fedora Linux 42 Server Edition
- **Kernel**: 6.15.10

## Quick Start

### Deploy GPT-OSS-20B
```bash
cd /home/gpt-oss
docker-compose -f docker/compose/docker-compose.gpt-oss-20b.yml up -d
```

### Run Tests
```bash
bash scripts/test/test-attention-backends.sh
```

### Monitor Services
```bash
docker ps
docker logs -f gpt-oss-20b-vllm
```

## Git Workflow
- **Main Branch**: `main`
- **Commit Format**: Descriptive messages focusing on "why"
- **Pre-commit**: Run linting and tests before committing

## Environment Variables
Create `.env` file (not tracked in git):
```bash
HF_TOKEN=your_huggingface_token
CUDA_VISIBLE_DEVICES=0
```

## Notes
- All experimental RTX 5090 builds are in `docker/rtx5090-experimental/`
- Production-ready configurations use official vLLM Docker images
- Model files stored in `/home/gpt-oss/models/` directory
