# /services/conversation_engine/Dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

COPY services/conversation_engine/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/common/requirements.txt services/common/requirements.txt
RUN pip install --no-cache-dir -r services/common/requirements.txt

# Copy the service code
COPY services/common ./services/common
COPY services/conversation_engine ./services/conversation_engine

EXPOSE 8080
CMD ["uvicorn", "services.conversation_engine.main:app", "--host", "0.0.0.0", "--port", "8080"]