# /services/fake_threads/Dockerfile
FROM python:3.12-slim-bookworm
WORKDIR /app
COPY services/fake_threads/requirements.txt ./fake_threads_requirements.txt
COPY services/common/requirements.txt ./common_requirements.txt
RUN pip install --no-cache-dir -r common_requirements.txt -r fake_threads_requirements.txt
COPY services/fake_threads ./services/fake_threads
COPY services/common ./services/common
EXPOSE 9009
CMD ["uvicorn", "services.fake_threads.main:app", "--host", "0.0.0.0", "--port", "9009"]
