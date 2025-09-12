# Frontend Dockerfile for Galaxy Chat Tool Integration  
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install httpx for proxy communication
RUN pip install --no-cache-dir httpx==0.28.1

# Copy integrated frontend
COPY frontend_integrated.py .

# Expose Streamlit port
EXPOSE 8501

# Environment variables for proxy connection
ENV PROXY_URL=http://gpt-oss-tool-proxy:8001/v1/chat/completions
ENV PROXY_BASE=http://gpt-oss-tool-proxy:8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run integrated frontend
CMD ["streamlit", "run", "frontend_integrated.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--server.fileWatcherType=none"]
