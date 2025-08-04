"""Main FastAPI application for RAG Pipeline Service."""

import os
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest
from prometheus_fastapi_instrumentator import Instrumentator

from services.rag_pipeline.api.routes import router as api_router
from services.rag_pipeline.core.vector_storage import VectorStorageManager
from services.rag_pipeline.core.embedding_service import (
    EmbeddingService,
    EmbeddingCache,
)
from services.rag_pipeline.retrieval.retrieval_pipeline import (
    RetrievalPipeline,
    RetrievalConfig,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Metrics
rag_requests = Counter(
    "rag_requests_total", "Total number of RAG requests", ["operation", "status"]
)

rag_latency = Histogram("rag_latency_seconds", "RAG operation latency", ["operation"])


class AppState:
    """Application state for dependency injection."""

    def __init__(self):
        self.vector_storage: Optional[VectorStorageManager] = None
        self.embedding_service: Optional[EmbeddingService] = None
        self.retrieval_pipeline: Optional[RetrievalPipeline] = None


app_state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting RAG Pipeline Service...")

    # Initialize services
    try:
        # Vector storage
        qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
        app_state.vector_storage = VectorStorageManager(
            url=qdrant_url, collection_name="rag_documents"
        )

        # Embedding service with cache
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        embedding_cache = EmbeddingCache(redis_url=redis_url)
        app_state.embedding_service = EmbeddingService(
            api_key=os.getenv("OPENAI_API_KEY"), cache=embedding_cache
        )

        # Retrieval pipeline
        retrieval_config = RetrievalConfig(
            top_k=int(os.getenv("RAG_TOP_K", "10")),
            rerank_top_k=int(os.getenv("RAG_RERANK_TOP_K", "5")),
            min_relevance_score=float(os.getenv("RAG_MIN_SCORE", "0.7")),
        )

        app_state.retrieval_pipeline = RetrievalPipeline(
            vector_storage=app_state.vector_storage,
            embedding_service=app_state.embedding_service,
            config=retrieval_config,
        )

        logger.info("All services initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

    yield

    # Cleanup
    logger.info("Shutting down RAG Pipeline Service...")


# Create FastAPI app
app = FastAPI(
    title="RAG Pipeline Service",
    description="Production-grade Retrieval Augmented Generation pipeline",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus instrumentation
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "rag-pipeline", "version": "0.1.0"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return generate_latest()


def get_vector_storage() -> VectorStorageManager:
    """Dependency to get vector storage."""
    if not app_state.vector_storage:
        raise HTTPException(status_code=503, detail="Vector storage not initialized")
    return app_state.vector_storage


def get_embedding_service() -> EmbeddingService:
    """Dependency to get embedding service."""
    if not app_state.embedding_service:
        raise HTTPException(status_code=503, detail="Embedding service not initialized")
    return app_state.embedding_service


def get_retrieval_pipeline() -> RetrievalPipeline:
    """Dependency to get retrieval pipeline."""
    if not app_state.retrieval_pipeline:
        raise HTTPException(
            status_code=503, detail="Retrieval pipeline not initialized"
        )
    return app_state.retrieval_pipeline


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
