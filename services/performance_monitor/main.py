"""Main entry point for Performance Monitor service."""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from celery import Celery

from services.performance_monitor.api import router
from services.orchestrator.db.models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Celery configuration
celery_app = Celery(
    "performance_monitor",
    broker=os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672//"),
    include=["services.performance_monitor.tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes
    task_soft_time_limit=540,  # 9 minutes
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    logger.info("Starting Performance Monitor service...")
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    yield
    logger.info("Shutting down Performance Monitor service...")


# Create FastAPI app
app = FastAPI(
    title="Performance Monitor Service",
    version="0.1.0",
    description="Monitors variant performance and makes early kill decisions",
    lifespan=lifespan
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes probes."""
    return {
        "status": "healthy",
        "service": "performance-monitor",
        "version": "0.1.0"
    }


# Prometheus metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from services.performance_monitor.metrics import get_metrics
    from fastapi.responses import Response
    
    metrics_data = get_metrics()
    return Response(content=metrics_data, media_type="text/plain")


# Dependency to get DB session
def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Include API router
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8085)