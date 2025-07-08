# /services/celery_worker/Dockerfile
FROM python:3.12-slim-bookworm
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services ./services
ENV PYTHONPATH=/app
CMD ["celery", "-A", "services.celery_worker.main", "worker", "--loglevel=info"]
