FROM python:3.12-slim-bookworm

# Set working directory
WORKDIR /app

# Install system dependencies for vLLM
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY services/vllm_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy common utilities
COPY services/common ./services/common

# Copy the vLLM service
COPY services/vllm_service ./services/vllm_service

# Expose port
EXPOSE 8090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8090/health || exit 1

# Run the service
CMD ["uvicorn", "services.vllm_service.main:app", "--host", "0.0.0.0", "--port", "8090"]