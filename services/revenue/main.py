import os
from contextlib import asynccontextmanager
from typing import Dict, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import generate_latest
from prometheus_client.core import REGISTRY
from prometheus_client.openmetrics.exposition import CONTENT_TYPE_LATEST
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from services.common.metrics import maybe_start_metrics_server
from services.revenue.affiliate_manager import AffiliateLinkInjector
from services.revenue.analytics import RevenueAnalytics
from services.revenue.db.models import Base
from services.revenue.lead_capture import LeadCapture
from services.revenue.stripe_integration import RevenueManager


# Pydantic models for API
class LeadCaptureRequest(BaseModel):
    email: EmailStr
    source: str
    content_id: Optional[int] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    metadata: Optional[Dict] = None


class AffiliateLinkRequest(BaseModel):
    content: str
    category: Optional[str] = None
    content_id: Optional[int] = None
    max_links: int = 3


class SubscriptionRequest(BaseModel):
    email: EmailStr
    tier: str
    payment_method_id: str
    trial_days: int = 0


class AffiliateClickRequest(BaseModel):
    link_id: int
    referrer: Optional[str] = None


class AffiliateConversionRequest(BaseModel):
    link_id: int
    commission_amount: float
    customer_email: Optional[str] = None


# Database setup
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/threads_agent"
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    maybe_start_metrics_server()
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown
    pass


# Create FastAPI app
app = FastAPI(
    title="Revenue Service",
    description="Stripe + Affiliate + Lead Capture for Threads Agent Stack",
    version="1.0.0",
    lifespan=lifespan,
)


# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "revenue"}


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


# Lead capture endpoints
@app.post("/revenue/capture-lead")
async def capture_lead(
    request: LeadCaptureRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Capture a lead with attribution tracking"""
    lead_capture = LeadCapture(db)

    result = lead_capture.capture_email(
        email=request.email,
        source=request.source,
        content_id=request.content_id,
        utm_params={
            "utm_source": request.utm_source,
            "utm_medium": request.utm_medium,
            "utm_campaign": request.utm_campaign,
        },
        metadata=request.metadata,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@app.post("/revenue/lead/{email}/convert")
async def convert_lead(
    email: str, conversion_value: float = 0.0, db: Session = Depends(get_db)
):
    """Mark a lead as converted"""
    lead_capture = LeadCapture(db)
    success = lead_capture.mark_conversion(email, conversion_value)

    if not success:
        raise HTTPException(status_code=404, detail="Lead not found")

    return {"success": True, "email": email}


# Affiliate endpoints
@app.post("/revenue/inject-affiliate-links")
async def inject_affiliate_links(
    request: AffiliateLinkRequest, db: Session = Depends(get_db)
):
    """Inject contextual affiliate links into content"""
    injector = AffiliateLinkInjector(db)

    enhanced_content, links = injector.inject_contextual_links(
        content=request.content,
        topic_category=request.category,
        content_id=request.content_id,
        max_links=request.max_links,
    )

    return {"enhanced_content": enhanced_content, "injected_links": links}


@app.post("/revenue/track-click")
async def track_affiliate_click(
    request: AffiliateClickRequest, db: Session = Depends(get_db)
):
    """Track affiliate link click"""
    injector = AffiliateLinkInjector(db)
    success = injector.track_click(request.link_id, request.referrer)

    if not success:
        raise HTTPException(status_code=404, detail="Link not found")

    return {"success": True}


@app.post("/revenue/track-conversion")
async def track_affiliate_conversion(
    request: AffiliateConversionRequest, db: Session = Depends(get_db)
):
    """Track affiliate conversion"""
    injector = AffiliateLinkInjector(db)
    success = injector.track_conversion(
        request.link_id, request.commission_amount, request.customer_email
    )

    if not success:
        raise HTTPException(status_code=404, detail="Link not found")

    return {"success": True}


# Subscription endpoints
@app.post("/revenue/create-subscription")
async def create_subscription(
    request: SubscriptionRequest, db: Session = Depends(get_db)
):
    """Create a new subscription"""
    revenue_manager = RevenueManager(db)

    result = revenue_manager.create_subscription(
        email=request.email,
        tier=request.tier,
        payment_method_id=request.payment_method_id,
        trial_days=request.trial_days,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@app.delete("/revenue/subscription/{subscription_id}")
async def cancel_subscription(
    subscription_id: int, immediate: bool = False, db: Session = Depends(get_db)
):
    """Cancel a subscription"""
    revenue_manager = RevenueManager(db)

    result = revenue_manager.cancel_subscription(subscription_id, immediate)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@app.post("/revenue/stripe-webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhooks"""
    revenue_manager = RevenueManager(db)

    payload = await request.body()
    signature = request.headers.get("stripe-signature")

    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")

    result = revenue_manager.handle_webhook(payload, signature)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


# Analytics endpoints
@app.get("/revenue/analytics")
async def get_revenue_analytics(days: int = 30, db: Session = Depends(get_db)):
    """Get comprehensive revenue analytics"""
    analytics = RevenueAnalytics(db)
    return analytics.get_revenue_summary(days)


@app.get("/revenue/affiliate-stats")
async def get_affiliate_stats(days: int = 30, db: Session = Depends(get_db)):
    """Get affiliate program performance"""
    analytics = RevenueAnalytics(db)
    return analytics.get_affiliate_performance(days)


@app.get("/revenue/lead-funnel")
async def get_lead_funnel(days: int = 30, db: Session = Depends(get_db)):
    """Get lead funnel metrics"""
    analytics = RevenueAnalytics(db)
    return analytics.get_lead_funnel_metrics(days)


@app.get("/revenue/subscription-metrics")
async def get_subscription_metrics(db: Session = Depends(get_db)):
    """Get subscription metrics"""
    analytics = RevenueAnalytics(db)
    return analytics.get_subscription_metrics()


@app.get("/revenue/forecast")
async def get_revenue_forecast(months: int = 12, db: Session = Depends(get_db)):
    """Get revenue forecast"""
    analytics = RevenueAnalytics(db)
    return analytics.get_revenue_forecast(months)


@app.get("/revenue/leads/export")
async def export_leads(converted_only: bool = False, db: Session = Depends(get_db)):
    """Export lead data"""
    lead_capture = LeadCapture(db)
    return lead_capture.export_leads(converted_only)


# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500, content={"detail": f"Internal server error: {str(exc)}"}
    )
