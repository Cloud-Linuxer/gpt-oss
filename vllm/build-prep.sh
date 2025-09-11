#!/bin/bash

# Create a directory for pre-downloaded packages
mkdir -p /home/gpt-oss/vllm/deps

# Download torch and its dependencies
echo "Downloading PyTorch packages..."
pip download torch==2.5.1 --index-url https://download.pytorch.org/whl/cu124 -d /home/gpt-oss/vllm/deps/

# Download vllm (will also get its dependencies)
echo "Downloading vLLM packages..."
pip download vllm -d /home/gpt-oss/vllm/deps/

echo "Download complete! Packages saved to /home/gpt-oss/vllm/deps/"
ls -lh /home/gpt-oss/vllm/deps/ | head -20