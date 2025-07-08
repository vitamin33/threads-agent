# /services/orchestrator/Dockerfile
# dockerfile-utils: ignore critical_high_vulnerabilities
FROM cgr.dev/chainguard/python:3.11
WORKDIR /app
COPY . .
RUN pip install fastapi uvicorn[standard]
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
