# /services/celery_worker/Dockerfile
FROM python:3.12-slim-bookworm
WORKDIR /app

COPY services/celery_worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/common/requirements.txt services/common/requirements.txt
RUN pip install --no-cache-dir -r services/common/requirements.txt

COPY services/common ./services/common
COPY services/celery_worker ./services/celery_worker

CMD sh -c "celery -A services.celery_worker.main worker -l info --concurrency=\${CELERY_WORKER_CONCURRENCY:-2} --max-memory-per-child=\${CELERY_WORKER_MAX_MEMORY_PER_CHILD:-50000}"
