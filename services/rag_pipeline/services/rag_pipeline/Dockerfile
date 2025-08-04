# Build stage - Optimized for AI dependencies
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies for numpy, scipy, ML libraries
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install in order for better caching
COPY requirements.txt .

# Install dependencies with optimized settings
RUN pip install --no-cache-dir --user \
    --compile \
    --no-warn-script-location \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt

# Runtime stage - Optimized for production
FROM python:3.12-slim

WORKDIR /app

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libopenblas0 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Performance environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=0 \
    PYTHONIOENCODING=utf-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Optimize Python for production
ENV PYTHONOPTIMIZE=2

# NumPy/BLAS optimization
ENV OPENBLAS_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=1 \
    OMP_NUM_THREADS=1

# Create non-root user for security
RUN groupadd -r raguser && useradd -r -g raguser raguser

# Copy application code with proper ownership
COPY --chown=raguser:raguser . .

# Copy common module if it exists (handled in build context)

# Create necessary directories
RUN mkdir -p /app/cache/embeddings /app/cache/models /tmp \
    && chown -R raguser:raguser /app/cache /tmp

# Switch to non-root user
USER raguser

# Expose port
EXPOSE 8000

# Optimized health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Pre-compile Python files for faster startup
RUN python -m compileall -b . || true

# Run with optimized uvicorn settings
CMD ["python", "-m", "uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--loop", "asyncio", \
     "--http", "httptools", \
     "--access-log", \
     "--backlog", "2048"]