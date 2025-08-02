"""
Main FastAPI application for viral metrics service.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from services.viral_metrics.api import router as viral_metrics_router

# Create FastAPI app
app = FastAPI(
    title="Viral Metrics Service",
    description="Real-time viral content metrics collection and analysis",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(viral_metrics_router)

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "viral-metrics",
        "version": "1.0.0",
        "status": "operational"
    }

# Health check endpoint (for Kubernetes)
@app.get("/health")
async def health():
    return {"status": "healthy"}

# Readiness check endpoint (for Kubernetes)
@app.get("/ready")
async def ready():
    # TODO: Add actual readiness checks (DB connection, etc.)
    return {"status": "ready"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)