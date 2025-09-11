#!/bin/bash

# 의존성 파일 저장 디렉토리
DEPS_DIR="./deps"
WHEELS_DIR="$DEPS_DIR/wheels"
MODELS_DIR="../models"

echo "=== 의존성 사전 다운로드 스크립트 ==="

# 디렉토리 생성
mkdir -p "$WHEELS_DIR"
mkdir -p "$MODELS_DIR"

# Python 패키지 다운로드
echo "1. Python 패키지 다운로드 중..."
pip download --no-deps -d "$WHEELS_DIR" \
    torch==2.5.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

pip download -d "$WHEELS_DIR" \
    transformers \
    accelerate \
    sentencepiece \
    protobuf \
    ray[serve]

# vllm은 별도로 다운로드 (의존성 문제 회피)
pip download --no-deps -d "$WHEELS_DIR" vllm

echo "패키지 다운로드 완료: $WHEELS_DIR"
ls -lh "$WHEELS_DIR" | head -10

# 모델 다운로드 (옵션)
if [ ! -z "$MODEL_NAME" ]; then
    echo "2. 모델 다운로드 중: $MODEL_NAME"
    python3 -c "
from transformers import AutoModelForCausalLM, AutoTokenizer
import os

model_name = os.environ.get('MODEL_NAME', 'facebook/opt-125m')
cache_dir = '../models'

print(f'Downloading model: {model_name}')
tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir)
model = AutoModelForCausalLM.from_pretrained(model_name, cache_dir=cache_dir)
print(f'Model downloaded to: {cache_dir}')
"
fi

echo "=== 사전 다운로드 완료 ==="
echo "빌드 시 ./deps 디렉토리의 파일들을 사용합니다"