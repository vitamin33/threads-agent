# Production-optimized Dockerfile for vLLM service with Apple Silicon support
FROM python:3.12-slim-bookworm

# Set working directory
WORKDIR /app

# Install system dependencies for vLLM and performance optimization
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libaio-dev \
    libnuma-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set environment variables for optimization
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Optimize for production
ENV FORCE_CPU=true
ENV VLLM_MODEL=meta-llama/Llama-3.1-8B-Instruct
ENV UVICORN_WORKERS=1
ENV UVICORN_WORKER_CLASS=uvicorn.workers.UvicornWorker

# Memory and performance settings
ENV MALLOC_ARENA_MAX=4
ENV PYTHONMALLOC=malloc

# Copy requirements first for better Docker layer caching
COPY services/vllm_service/requirements.txt .

# Install Python dependencies with optimizations
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy common utilities
COPY services/common ./services/common

# Copy the vLLM service
COPY services/vllm_service ./services/vllm_service

# Create non-root user for security
RUN groupadd -r vllm && useradd -r -g vllm vllm
RUN chown -R vllm:vllm /app
USER vllm

# Expose port
EXPOSE 8090

# Enhanced health check for production readiness
HEALTHCHECK --interval=30s --timeout=15s --start-period=300s --retries=5 \
    CMD curl -f http://localhost:8090/health | grep -q '"status":"healthy"' || exit 1

# Production startup with performance optimizations
CMD ["uvicorn", "services.vllm_service.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8090", \
     "--workers", "1", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--access-log", \
     "--log-level", "info", \
     "--loop", "asyncio"]