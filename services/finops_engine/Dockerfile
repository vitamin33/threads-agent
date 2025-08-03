FROM python:3.12-slim-bookworm

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY services/finops_engine/requirements.txt services/finops_engine/
COPY services/common/requirements.txt services/common/

# Install dependencies
RUN pip install --no-cache-dir -r services/finops_engine/requirements.txt
RUN pip install --no-cache-dir -r services/common/requirements.txt

# Copy application code
COPY services/common services/common
COPY services/finops_engine services/finops_engine

# Expose port
EXPOSE 8095

# Run the FastAPI app
CMD ["uvicorn", "services.finops_engine.fastapi_app:app", "--host", "0.0.0.0", "--port", "8095"]