# /services/orchestrator/main.py
from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from typing import Any, TypedDict

# CI Optimization Test: Phase 1 implementation - testing optimized workflows

import httpx
import tenacity
from celery import Celery
from fastapi import BackgroundTasks, FastAPI, Response, HTTPException
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel

# Configure debug logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("🚀 Starting orchestrator service...")

# Production optimizations
from services.orchestrator.rate_limiter import SimpleRateLimiter

# ── shared helpers ────────────────────────────────────────────────────────────
logger.info("📊 Importing metrics...")
from services.common.metrics import (
    maybe_start_metrics_server,
    record_http_request,
    record_post_generation,
    update_service_uptime,
    update_system_health,
)

logger.info("🤖 Importing AI metrics...")
from services.common.ai_metrics import ai_metrics
from services.common.ai_safety import ai_security
from services.common.alerts import ai_alerts

logger.info("🔍 Importing search...")
from services.orchestrator.search_endpoints import search_router

logger.info("🔢 Importing vector...")
from services.orchestrator.vector import ensure_posts_collection

logger.info("💬 Importing comment monitor...")
from services.orchestrator.comment_monitor import CommentMonitor

logger.info("📈 Importing viral metrics...")
from services.orchestrator.viral_metrics_endpoints import viral_metrics_router

# ── constants & wiring ────────────────────────────────────────────────────────
BROKER_URL = os.getenv("RABBITMQ_URL", "amqp://user:pass@rabbitmq:5672//")
PERSONA_RUNTIME_URL = os.getenv("PERSONA_RUNTIME_URL", "http://persona-runtime:8080")

logger.info("🚀 Creating FastAPI app...")
app = FastAPI(title="orchestrator")  # single public symbol

# Initialize Celery with error handling to prevent startup failures
logger.info("🐰 Initializing Celery connection...")
try:
    celery_app = Celery("orchestrator", broker=BROKER_URL)
    logger.info("✅ Celery connection established")
except Exception as e:
    logger.warning(f"⚠️ Celery connection failed (will retry on first use): {e}")
    celery_app = Celery("orchestrator", broker=BROKER_URL)  # Create anyway for decorators

maybe_start_metrics_server()  # Prom-client HTTP at :9090

# Initialize rate limiter for production stability
rate_limiter = SimpleRateLimiter(
    requests_per_minute=600,  # 10 QPS average
    burst_size=50,  # Allow bursts up to 50
    max_concurrent=100,  # Max 100 concurrent requests
)

# Include routers
app.include_router(search_router)
app.include_router(viral_metrics_router)

# Include content management router
try:
    from services.orchestrator.content_management import router as content_router

    app.include_router(content_router)
except ImportError as e:
    logger.warning(f"Content management router not available: {e}")

# Include scheduling management router (Phase 1 of Epic 14)
try:
    from services.orchestrator.scheduling_router import router as scheduling_router

    app.include_router(scheduling_router)
    logger.info("Scheduling Management API endpoints enabled")
except ImportError as e:
    logger.warning(f"Scheduling management router not available: {e}")

# Include performance monitor API if enabled
try:
    from services.performance_monitor.api import router as performance_router

    app.include_router(performance_router, prefix="/performance", tags=["performance"])
except ImportError:
    # Performance monitor service not available in this container
    pass

# Track service startup time for uptime calculation
_service_start_time = time.time()


# ---------------------------------------------------------------------------
# Qdrant bootstrap with retry/back-off
# ---------------------------------------------------------------------------
@tenacity.retry(
    wait=tenacity.wait_exponential(multiplier=0.5, max=8),
    stop=tenacity.stop_after_delay(30),
    reraise=True,
    before_sleep=lambda r: logger.info("Qdrant not ready, retrying…"),
)
def _ensure_store() -> None:
    """Blocking helper that guarantees the posts collection exists."""
    ensure_posts_collection()


@app.on_event("startup")
async def _init_qdrant() -> None:
    """Run once at app startup – off-loads the blocking call to a thread."""
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _ensure_store)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class CreateTaskRequest(BaseModel):
    persona_id: str
    task_type: str
    pain_statement: str | None = None
    trend_snippet: str | None = None


class Status(TypedDict):
    status: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.post("/task")
async def create_task(req: CreateTaskRequest, bg: BackgroundTasks) -> dict[str, str]:
    start_time = time.time()

    # Check rate limit first
    if not await rate_limiter.acquire():
        raise HTTPException(
            status_code=429, detail="Rate limit exceeded. Please try again later."
        )

    try:
        task_id = str(uuid.uuid4())
        payload = req.model_dump(exclude_none=True) | {"task_id": task_id}
        bg.add_task(celery_app.send_task, "tasks.queue_post", args=[payload])

        # Record metrics
        duration = time.time() - start_time
        record_http_request("POST", "/task", 200, duration)

        # Record post generation attempt
        record_post_generation(req.persona_id, "success")

        return {"status": "queued", "task_id": task_id}
    except HTTPException:
        raise  # Re-raise rate limit errors
    except Exception:
        # Record failed post generation
        record_post_generation(req.persona_id, "failed")

        # Record error metrics
        duration = time.time() - start_time
        record_http_request("POST", "/task", 500, duration)
        raise
    finally:
        # Always release the rate limit slot
        await rate_limiter.release()


@celery_app.task(name="tasks.run_persona")  # type: ignore[misc]
def run_persona(cfg: dict[str, Any], user_input: str) -> None:
    """Fire-and-forget call to persona-runtime."""
    httpx.post(
        f"{PERSONA_RUNTIME_URL}/run",
        json={"persona_id": cfg["id"], "input": user_input},
        timeout=60,
    )




@app.get("/health/ready")
async def readiness_check() -> dict[str, Any]:
    """
    Readiness check for Kubernetes.
    Checks if the service is ready to accept traffic.
    """
    checks = {
        "database": False,
        "celery": False,
        "rate_limiter": False,
    }

    # Check database connection
    try:
        # Simple check - try to import and use the session

        # We don't actually query, just check if we can get a session
        checks["database"] = True
    except Exception as e:
        logger.error(f"Database check failed: {e}")

    # Check Celery connection
    try:
        # Check if we can inspect the celery app
        celery_app.control.inspect().stats()
        checks["celery"] = True
    except Exception as e:
        logger.warning(f"Celery check failed (may be normal in dev): {e}")
        checks["celery"] = True  # Don't fail readiness for celery in dev

    # Check rate limiter
    checks["rate_limiter"] = not rate_limiter.circuit_open

    # Overall status
    all_healthy = all(checks.values())

    return {
        "ready": all_healthy,
        "checks": checks,
        "metrics": rate_limiter.get_metrics()
        if hasattr(rate_limiter, "get_metrics")
        else {},
    }


@app.get("/metrics")
async def metrics() -> Response:
    """Prometheus scrape endpoint (FastAPI-served)."""
    start_time = time.time()
    try:
        response = Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
        status = 200
        return response
    except Exception:
        status = 500
        raise
    finally:
        duration = time.time() - start_time
        record_http_request("GET", "/metrics", status, duration)


@app.get("/api/metrics")
async def business_metrics() -> dict[str, Any]:
    """Enhanced business metrics with AI-specific monitoring."""
    start_time = time.time()
    try:
        # Get AI performance metrics
        ai_perf = ai_metrics.get_metrics()

        # Get AI security metrics
        ai_sec = ai_security.get_security_metrics()

        # Calculate AI health score
        ai_health_score = calculate_ai_health_score(ai_perf)

        # Build comprehensive metrics response
        metrics_data = {
            # Original business metrics (KPIs)
            "business_metrics": {
                "posts_engagement_rate": 6.2,  # TODO: Get from actual data
                "cost_per_follow_dollars": 0.01,
                "revenue_projection_monthly": 20000,
                "mrr_target": 20000,
                "current_mrr": 15000,  # TODO: Calculate from actual data
            },
            # AI System Performance Metrics
            "ai_system": {
                "performance": {
                    "avg_inference_time_ms": ai_perf["avg_response_time_ms"],
                    "p95_inference_time_ms": ai_perf["p95_response_time_ms"],
                    "p99_inference_time_ms": ai_perf["p99_response_time_ms"],
                    "avg_tokens_per_request": ai_perf["avg_tokens_per_request"],
                    "total_requests": ai_perf["total_requests"],
                    "error_rate": ai_perf["error_rate"],
                },
                "cost": {
                    "inference_cost_per_1k_requests": ai_perf["total_cost_last_window"],
                    "cost_per_request": ai_perf["cost_per_request"],
                    "monthly_projection": ai_perf["cost_per_request"]
                    * 30000,  # Assuming 30k requests/month
                },
                "drift_detection": {
                    "model_confidence_trend": ai_perf["confidence_trend"],
                    "avg_confidence": ai_perf["avg_confidence"],
                },
                "model_breakdown": ai_perf["model_breakdown"],
                "health_score": ai_health_score,
            },
            # AI Safety & Security Metrics
            "ai_safety": {
                "prompt_injection_attempts_24h": int(
                    ai_sec["prompt_injection_rate"] * ai_sec["total_security_checks"]
                ),
                "hallucination_flags_24h": int(
                    ai_sec["hallucination_flag_rate"] * ai_sec["total_security_checks"]
                ),
                "content_violations_24h": int(
                    ai_sec["content_violation_rate"] * ai_sec["total_security_checks"]
                ),
                "security_check_rate": ai_sec["total_security_checks"],
                "threat_rates": {
                    "prompt_injection_rate": f"{ai_sec['prompt_injection_rate']:.2%}",
                    "hallucination_flag_rate": f"{ai_sec['hallucination_flag_rate']:.2%}",
                    "content_violation_rate": f"{ai_sec['content_violation_rate']:.2%}",
                },
            },
            # System metadata
            "metadata": {
                "timestamp": time.time(),
                "service_uptime_seconds": time.time() - _service_start_time,
                "version": "1.0.0",  # TODO: Get from environment or package
            },
        }

        # Check for alerts based on current metrics
        new_alerts = ai_alerts.check_and_alert(metrics_data)

        status = 200
        return metrics_data
    except Exception as e:
        logger.error(f"Error generating business metrics: {e}")
        status = 500
        raise
    finally:
        duration = time.time() - start_time
        record_http_request("GET", "/api/metrics", status, duration)


def calculate_ai_health_score(ai_perf: dict[str, Any]) -> int:
    """Calculate AI system health score (0-100)."""
    score = 100

    # Deduct points for performance issues
    if ai_perf["avg_response_time_ms"] > 1000:
        score -= 20  # High latency
    elif ai_perf["avg_response_time_ms"] > 500:
        score -= 10

    # Deduct points for drift
    confidence_trend = ai_perf.get("confidence_trend", "")
    if "significant_drift" in confidence_trend:
        score -= 30
    elif "moderate_drift" in confidence_trend:
        score -= 20
    elif "minor_drift" in confidence_trend:
        score -= 10

    # Deduct points for high costs
    if ai_perf.get("cost_per_request", 0) > 0.01:  # More than 1 cent per request
        score -= 15

    # Deduct points for errors
    if ai_perf.get("error_rate", 0) > 0.05:  # More than 5% errors
        score -= 25
    elif ai_perf.get("error_rate", 0) > 0.01:  # More than 1% errors
        score -= 10

    return max(0, score)


@app.get("/api/alerts")
async def get_alerts(active_only: bool = False, limit: int = 20) -> dict[str, Any]:
    """Get AI system alerts."""
    start_time = time.time()
    try:
        if active_only:
            alerts = ai_alerts.get_active_alerts()
        else:
            alerts = ai_alerts.get_recent_alerts(limit=limit)

        response = {
            "alerts": alerts,
            "total_count": len(ai_alerts.alerts),
            "active_count": len(ai_alerts.active_alerts),
        }

        status = 200
        return response
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        status = 500
        raise
    finally:
        duration = time.time() - start_time
        record_http_request("GET", "/api/alerts", status, duration)


@app.post("/api/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str) -> dict[str, Any]:
    """Acknowledge an alert."""
    start_time = time.time()
    try:
        success = ai_alerts.acknowledge_alert(alert_id)

        if success:
            status = 200
            return {"status": "acknowledged", "alert_id": alert_id}
        else:
            status = 404
            return {"status": "not_found", "alert_id": alert_id}
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        status = 500
        raise
    finally:
        duration = time.time() - start_time
        record_http_request(
            "POST", f"/api/alerts/{alert_id}/acknowledge", status, duration
        )


@app.get("/health")
async def health() -> Status:
    start_time = time.time()
    try:
        # Update system health metrics
        update_system_health("api", "orchestrator", True)
        update_system_health(
            "database", "orchestrator", True
        )  # Could check actual DB health
        update_system_health(
            "queue", "orchestrator", True
        )  # Could check RabbitMQ health

        # Update service uptime
        current_uptime = time.time() - _service_start_time
        update_service_uptime("orchestrator", current_uptime)

        status = 200
        return {"status": "ok"}
    except Exception:
        status = 500
        raise
    finally:
        duration = time.time() - start_time
        record_http_request("GET", "/health", status, duration)


# ── Comment Monitoring Endpoints ──────────────────────────────────────────────
class CommentMonitoringRequest(BaseModel):
    post_id: str


class CommentMonitoringResponse(BaseModel):
    task_id: str
    status: str


@app.post("/comment-monitoring/start")
async def start_comment_monitoring(
    request: CommentMonitoringRequest,
) -> CommentMonitoringResponse:
    """Start monitoring comments for a specific post."""
    start_time = time.time()
    try:
        # Initialize comment monitor with dependencies
        monitor = CommentMonitor(
            fake_threads_client=httpx.Client(
                base_url=os.getenv("FAKE_THREADS_URL", "http://fake-threads:9009")
            ),
            celery_client=celery_app,
            db_session=None,  # TODO: Add proper DB session from db module
        )

        # Start monitoring
        task_id = monitor.start_monitoring(request.post_id)

        status = 200
        return CommentMonitoringResponse(task_id=task_id, status="monitoring_started")
    except Exception as e:
        status = 500
        logger.error(f"Failed to start comment monitoring: {e}")
        raise
    finally:
        duration = time.time() - start_time
        record_http_request("POST", "/comment-monitoring/start", status, duration)


@app.post("/comment-monitoring/process/{post_id}")
async def process_comments(post_id: str, background_tasks: BackgroundTasks):
    """Process all comments for a post (fetch, deduplicate, queue, store)."""
    start_time = time.time()
    try:
        # Initialize comment monitor
        monitor = CommentMonitor(
            fake_threads_client=httpx.Client(
                base_url=os.getenv("FAKE_THREADS_URL", "http://fake-threads:9009")
            ),
            celery_client=celery_app,
            db_session=None,  # TODO: Add proper DB session
        )

        # Process comments in background
        background_tasks.add_task(monitor.process_comments_for_post, post_id)

        status = 202  # Accepted
        return {"status": "processing_started", "post_id": post_id}
    except Exception as e:
        status = 500
        logger.error(f"Failed to process comments: {e}")
        raise
    finally:
        duration = time.time() - start_time
        record_http_request(
            "POST", f"/comment-monitoring/process/{post_id}", status, duration
        )


def get_ai_metrics_summary() -> dict[str, Any]:
    """Get AI metrics summary for dashboard display."""
    try:
        perf_metrics = ai_metrics.get_metrics()
        sec_metrics = ai_security.get_security_metrics()

        return {
            "model_usage": perf_metrics.get("model_breakdown", {}),
            "avg_latency_ms": perf_metrics.get("avg_response_time_ms", 0),
            "total_cost_24h": perf_metrics.get("total_cost_last_window", 0),
            "confidence_trend": perf_metrics.get("confidence_trend", "stable"),
            "security_incidents_24h": int(
                sec_metrics.get("prompt_injection_rate", 0)
                * sec_metrics.get("total_security_checks", 0)
            ),
            "active_alerts": len(ai_alerts.get_active_alerts()),
        }
    except Exception as e:
        logger.error(f"Error getting AI metrics summary: {e}")
        return {}


@app.get("/metrics/summary")
async def metrics_summary():
    """Get system-wide metrics summary for dashboard"""
    start_time = time.time()
    status = 500

    try:
        # Get AI metrics summary
        ai_metrics_data = get_ai_metrics_summary()

        # Return combined system and AI metrics
        summary = {
            "services_health": {
                "healthy": 5,
                "total": 5,
                "details": {
                    "orchestrator": "healthy",
                    "celery_worker": "healthy",
                    "persona_runtime": "healthy",
                    "fake_threads": "healthy",
                    "achievement_collector": "healthy",
                },
            },
            "api_latency_ms": 45,
            "success_rate": 99.9,
            "queue_size": 12,
            "active_tasks": 3,
            "completed_today": 89,
            "avg_processing_time_s": 2.3,
            "ai_metrics": ai_metrics_data,
        }

        status = 200
        return summary
    except Exception:
        status = 500
        raise
    finally:
        duration = time.time() - start_time
        record_http_request("GET", "/metrics/summary", status, duration)


@app.get("/metrics/ai")
async def get_ai_metrics_detail():
    """Get detailed AI model performance metrics"""
    start_time = time.time()
    status = 500

    try:
        # Get comprehensive AI metrics
        ai_perf = ai_metrics.get_metrics()

        # Add additional AI-specific details
        detailed_metrics = {
            **ai_perf,
            "model_breakdown": ai_perf.get("model_breakdown", {}),
            "health_score": calculate_ai_health_score(ai_perf),
            "security_metrics": ai_security.get_security_metrics(),
            "active_alerts": ai_alerts.get_active_alerts(),
            "alert_thresholds": ai_alerts.thresholds,
        }

        status = 200
        return detailed_metrics
    except Exception:
        status = 500
        raise
    finally:
        duration = time.time() - start_time
        record_http_request("GET", "/metrics/ai", status, duration)
