# syntax=docker/dockerfile:1.7

############################
# Builder
############################
FROM nvidia/cuda:12.8.0-devel-ubuntu24.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv python3-pip git build-essential ninja-build cmake curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# venv로 PEP 668 회피
RUN python3 -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
RUN python -m pip install -U pip wheel setuptools

# PyTorch nightly (CUDA 12.8) — Blackwell 필수
RUN python -m pip install --pre torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/nightly/cu128

# FlashInfer 백엔드 (패키지명: flashinfer-python)
RUN python -m pip install --no-cache-dir flashinfer-python

# vLLM (gpt-oss 전용 빌드)
RUN python -m pip install --pre "vllm==0.10.1+gptoss" \
    --extra-index-url https://wheels.vllm.ai/gpt-oss/ \
    --extra-index-url https://download.pytorch.org/whl/nightly/cu128 \
    --index-strategy unsafe-best-match

############################
# Runtime
############################
FROM nvidia/cuda:12.8.0-runtime-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive \
    PATH=/opt/venv/bin:$PATH \
    VLLM_ATTENTION_BACKEND=FLASHINFER \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv python3-pip ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
WORKDIR /workspace
EXPOSE 8000

# 모델 캐시는 /models로 마운트하면 됨
ENTRYPOINT ["vllm", "serve"]
CMD ["openai/gpt-oss-20b",\
     "--dtype","bfloat16", \
     "--gpu-memory-utilization","0.92", \
     "--download-dir","/models", \
     "--host","0.0.0.0", \
     "--port","8000"]

