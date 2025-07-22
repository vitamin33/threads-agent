# /services/viral_engine/Dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

# Install viral_engine dependencies
COPY services/viral_engine/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install common dependencies
COPY services/common/requirements.txt services/common/requirements.txt
RUN pip install --no-cache-dir -r services/common/requirements.txt

# Copy the service code
COPY services/common ./services/common
COPY services/viral_engine ./services/viral_engine

EXPOSE 8090
CMD ["uvicorn", "services.viral_engine.main:app", "--host", "0.0.0.0", "--port", "8090"]