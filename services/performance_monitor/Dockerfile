# Performance Monitor Service
FROM python:3.12-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY services/performance_monitor/requirements.txt services/performance_monitor/
COPY services/common/requirements.txt services/common/

RUN pip install --no-cache-dir -r services/performance_monitor/requirements.txt
RUN pip install --no-cache-dir -r services/common/requirements.txt

# Copy application code
COPY services/common services/common
COPY services/performance_monitor services/performance_monitor

# Expose ports
EXPOSE 8085 9095

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8085/health || exit 1

# Run API server only for now
CMD ["uvicorn", "services.performance_monitor.api:app", "--host", "0.0.0.0", "--port", "8085"]