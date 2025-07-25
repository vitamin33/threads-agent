# /services/orchestrator/Dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

# Install PostgreSQL client for migrations
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY services/orchestrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/common/requirements.txt services/common/requirements.txt
RUN pip install --no-cache-dir -r services/common/requirements.txt

# 2️⃣ copy the service code
COPY services/common ./services/common
COPY services/orchestrator ./services/orchestrator
COPY services/celery_worker ./services/celery_worker
COPY services/orchestrator/db ./services/orchestrator/db

EXPOSE 8080
CMD ["uvicorn", "services.orchestrator.main:app", "--host", "0.0.0.0", "--port", "8080"]
