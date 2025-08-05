# Build stage
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user \
    fastapi==0.109.0 \
    uvicorn==0.27.0 \
    pydantic==2.5.3 \
    pydantic-settings==2.1.0 \
    qdrant-client==1.7.3 \
    redis==5.0.1 \
    aiocache==0.12.2 \
    prometheus-client==0.19.0 \
    httpx==0.26.0 \
    numpy==1.26.3 \
    langchain==0.1.0 \
    langchain-openai==0.0.2 \
    tiktoken==0.5.2 \
    scikit-learn==1.4.0 \
    sentence-transformers==2.2.2 \
    nltk==3.8.1 \
    rouge-score==0.1.2 \
    pypdf==3.17.4 \
    beautifulsoup4==4.12.2 \
    markdown==3.5.1 \
    opentelemetry-api==1.22.0 \
    opentelemetry-sdk==1.22.0 \
    opentelemetry-instrumentation-fastapi==0.43b0

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/raguser/.local

# Make sure scripts in .local are usable
ENV PATH=/home/raguser/.local/bin:$PATH

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=0 \
    PYTHONIOENCODING=utf-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Create non-root user
RUN groupadd -r raguser && useradd -r -g raguser raguser

# Copy application code
COPY . /app/services/rag_pipeline/
# Copy common module if it exists
RUN mkdir -p /app/services/common

# Create necessary directories
RUN mkdir -p /app/cache/embeddings /app/cache/models /tmp \
    && chown -R raguser:raguser /app /tmp /home/raguser/.local

# Switch to non-root user
USER raguser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
WORKDIR /app/services/rag_pipeline/services/rag_pipeline
CMD ["python", "-m", "uvicorn", "main_simple:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1"]