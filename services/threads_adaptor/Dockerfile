# services/threads_adaptor/Dockerfile
FROM python:3.12-slim-bookworm

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY services/threads_adaptor/requirements.txt ./services/threads_adaptor/
COPY services/common/requirements.txt ./services/common/
RUN pip install --no-cache-dir -r services/threads_adaptor/requirements.txt
RUN pip install --no-cache-dir -r services/common/requirements.txt

# Copy application code
COPY services/threads_adaptor ./services/threads_adaptor
COPY services/common ./services/common

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/health').raise_for_status()"

# Run the application
CMD ["uvicorn", "services.threads_adaptor.main:app", "--host", "0.0.0.0", "--port", "8080"]