# /services/orchestrator/Dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

# 1️⃣  Install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2️⃣  Copy only the service code (not the whole repo)
COPY services/orchestrator ./services/orchestrator

EXPOSE 8080
CMD ["uvicorn", "services.orchestrator.main:app", "--host", "0.0.0.0", "--port", "8080"]
