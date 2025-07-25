# Achievement Collector Service
FROM python:3.12-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY services/achievement_collector/requirements.txt services/achievement_collector/
COPY services/common/requirements.txt services/common/

RUN pip install --no-cache-dir -r services/achievement_collector/requirements.txt
RUN pip install --no-cache-dir -r services/common/requirements.txt

# Copy common modules
COPY services/common services/common

# Copy achievement collector service
COPY services/achievement_collector services/achievement_collector

# Create portfolio output directory
RUN mkdir -p /app/portfolios

# Expose ports
EXPOSE 8090 9090

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8090/health || exit 1

# Run the service
CMD ["uvicorn", "services.achievement_collector.main:app", "--host", "0.0.0.0", "--port", "8090"]