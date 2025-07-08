# /templates/service-template/Dockerfile
FROM python:3.12-slim-bookworm
WORKDIR /app
COPY . .
RUN pip install fastapi uvicorn[standard]
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
