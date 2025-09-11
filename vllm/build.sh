#!/bin/bash

set -e

echo "Building vLLM Docker image for RTX 5090..."

# Check if .env exists, if not copy from example
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
fi

# Build the Docker image
docker build -t vllm-rtx5090:latest .

echo "Build complete!"
echo ""
echo "To run vLLM, use:"
echo "  docker-compose up -d"
echo ""
echo "To check logs:"
echo "  docker-compose logs -f vllm"
echo ""
echo "To stop:"
echo "  docker-compose down"