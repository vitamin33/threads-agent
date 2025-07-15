# /services/persona_runtime/Dockerfile
FROM python:3.12-slim-bookworm

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY services/persona_runtime/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/common ./services/common
COPY services/persona_runtime ./services/persona_runtime

EXPOSE 8080
CMD ["uvicorn", "services.persona_runtime.main:app", "--host", "0.0.0.0", "--port", "8080"]
