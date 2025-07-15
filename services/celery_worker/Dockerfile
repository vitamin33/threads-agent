# /services/celery_worker/Dockerfile
FROM python:3.12-slim-bookworm
WORKDIR /app

COPY services/celery_worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/common ./services/common
COPY services/celery_worker ./services/celery_worker
CMD ["celery", "-A", "services.celery_worker.main", "worker", "-l", "info"]
