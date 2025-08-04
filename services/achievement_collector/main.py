# Achievement Collector Service - Main Application

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from services.achievement_collector.api.routes import (
    achievements,
    analysis,
    analytics,
    export,
    portfolio,
    webhooks,
    pr_analysis,
    tech_doc_integration,
)
from services.achievement_collector.services.threads_integration import (
    ThreadsIntegration,
)
from services.achievement_collector.services.prometheus_scraper import PrometheusScaper
from services.achievement_collector.services.ai_analyzer import AIAnalyzer
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
app.include_router(analytics.router)
app.include_router(export.router)
app.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(pr_analysis.router, prefix="/pr-analysis", tags=["pr-analysis"])
app.include_router(tech_doc_integration.router, tags=["tech-doc-integration"])

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
        "phase": "2.0 - Integration & Automation",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
        "integrations": {
            "threads_agent": "/threads/track",
            "prometheus": "/prometheus/scrape",
            "ai_analysis": "/analyze/deep",
        },
    }


# Phase 2: Integration & Automation Endpoints
threads_integration = ThreadsIntegration()
prometheus_scraper = PrometheusScaper()
ai_analyzer = AIAnalyzer()


@app.post("/threads/track")
async def track_viral_post(post_data: Dict[str, Any]) -> Dict[str, Any]:
    """Track viral posts from threads-agent as achievements."""
    try:
        achievement = await threads_integration.track_viral_post(post_data)
        if achievement:
            return {"status": "created", "achievement_id": achievement.id}
        else:
            return {"status": "skipped", "reason": "Below viral threshold"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/prometheus/scrape")
async def manual_prometheus_scrape() -> Dict[str, Any]:
    """Manually trigger Prometheus metrics scraping."""
    try:
        await prometheus_scraper._scrape_metrics()
        return {"status": "completed", "message": "Metrics scraped successfully"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/prometheus/status")
async def prometheus_status() -> Dict[str, Any]:
    """Get Prometheus scraper status."""
    return {
        "status": "active",
        "interval_hours": prometheus_scraper.scrape_interval,
        "thresholds": prometheus_scraper.kpi_thresholds,
        "last_values": prometheus_scraper.previous_values,
    }


@app.post("/analyze/deep/{achievement_id}")
async def deep_analysis(achievement_id: int) -> Dict[str, Any]:
    """Perform deep AI analysis on an achievement."""
    from services.achievement_collector.api.routes.achievements import get_achievement
    from services.achievement_collector.db.config import get_db

    db = next(get_db())
    try:
        achievement = get_achievement(db, achievement_id)
        if not achievement:
            return {"status": "error", "error": "Achievement not found"}

        analysis = await ai_analyzer.analyze_achievement_impact(achievement)
        return {"status": "completed", "analysis": analysis}
    finally:
        db.close()


@app.get("/analyze/career-insights")
async def career_insights() -> Dict[str, Any]:
    """Get AI-powered career insights from all achievements."""
    from services.achievement_collector.api.routes.achievements import get_achievements
    from services.achievement_collector.db.config import get_db

    db = next(get_db())
    try:
        achievements_list = get_achievements(db, skip=0, limit=100)
        insights = await ai_analyzer.generate_career_insights(achievements_list)
        return {"status": "completed", "insights": insights}
    finally:
        db.close()


@app.post("/threads/kpi-milestone")
async def track_kpi_milestone(milestone_data: Dict[str, Any]) -> Dict[str, Any]:
    """Track KPI milestones from metrics."""
    try:
        metric_name = milestone_data.get("metric_name")
        value = milestone_data.get("value")
        target = milestone_data.get("target")

        achievement = await threads_integration.track_kpi_milestone(
            metric_name, value, target
        )
        if achievement:
            return {"status": "created", "achievement_id": achievement.id}
        else:
            return {"status": "skipped", "reason": "Below target threshold"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
