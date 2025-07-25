# Achievement Collector Service - Main Application

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from services.achievement_collector.api.routes import (
    achievements,
    analysis,
    portfolio,
    webhooks,
)
from services.achievement_collector.core.config import settings
from services.achievement_collector.core.logging import setup_logging
from services.achievement_collector.db.config import engine
from services.achievement_collector.db.models import Base

# Setup logging
logger = setup_logging(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events"""
    # Startup
    logger.info("Starting Achievement Collector Service")

    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")

    yield

    # Shutdown
    logger.info("Shutting down Achievement Collector Service")


# Create FastAPI app
app = FastAPI(
    title="Achievement Collector",
    description="Professional achievement tracking and portfolio generation",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(achievements.router, prefix="/achievements", tags=["achievements"])
app.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
app.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "achievement-collector",
        "version": "1.0.0",
    }


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint"""
    return {
        "service": "Achievement Collector",
        "description": "Professional achievement tracking and portfolio generation",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
    }
