import os
from contextlib import asynccontextmanager
from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.common.metrics import maybe_start_metrics_server
from services.revenue.db.models import Base


@pytest.fixture(scope="module")
def test_engine(worker_id):
    """Create test engine with thread safety for SQLite"""
    # Use check_same_thread=False for SQLite in tests
    # Use a unique database file per test worker for parallel execution
    db_file = f"test_revenue_{worker_id}.db" if worker_id else "test_revenue.db"
    engine = create_engine(
        f"sqlite:///{db_file}", connect_args={"check_same_thread": False}
    )
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()
    # Clean up the test database file
    if os.path.exists(db_file):
        os.remove(db_file)


@pytest.fixture
def test_db(test_engine):
    """Create test database session"""
    SessionLocal = sessionmaker(bind=test_engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def client(test_db, test_engine):
    """Create test client with test database"""

    # Create a test app with lifespan that doesn't create database
    @asynccontextmanager
    async def test_lifespan(app: FastAPI):
        maybe_start_metrics_server()
        # Don't create tables here - they're already created in test_engine fixture
        yield

    # Import FastAPI app components
    from services.revenue.main import (
        capture_lead,
        convert_lead,
        inject_affiliate_links,
        track_affiliate_click,
        track_affiliate_conversion,
        create_subscription,
        cancel_subscription,
        stripe_webhook,
        get_revenue_analytics,
        get_affiliate_stats,
        get_lead_funnel,
        get_subscription_metrics,
        get_revenue_forecast,
        export_leads,
        health,
        metrics,
        global_exception_handler,
        get_db,
    )

    # Create new app for testing
    test_app = FastAPI(
        title="Revenue Service Test",
        lifespan=test_lifespan,
    )

    # Copy all routes from the main app
    test_app.get("/health")(health)
    test_app.get("/metrics")(metrics)
    test_app.post("/revenue/capture-lead")(capture_lead)
    test_app.post("/revenue/lead/{email}/convert")(convert_lead)
    test_app.post("/revenue/inject-affiliate-links")(inject_affiliate_links)
    test_app.post("/revenue/track-click")(track_affiliate_click)
    test_app.post("/revenue/track-conversion")(track_affiliate_conversion)
    test_app.post("/revenue/create-subscription")(create_subscription)
    test_app.delete("/revenue/subscription/{subscription_id}")(cancel_subscription)
    test_app.post("/revenue/stripe-webhook")(stripe_webhook)
    test_app.get("/revenue/analytics")(get_revenue_analytics)
    test_app.get("/revenue/affiliate-stats")(get_affiliate_stats)
    test_app.get("/revenue/lead-funnel")(get_lead_funnel)
    test_app.get("/revenue/subscription-metrics")(get_subscription_metrics)
    test_app.get("/revenue/forecast")(get_revenue_forecast)
    test_app.get("/revenue/leads/export")(export_leads)
    test_app.exception_handler(Exception)(global_exception_handler)

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    test_app.dependency_overrides[get_db] = override_get_db

    with TestClient(test_app) as test_client:
        yield test_client

    test_app.dependency_overrides.clear()


class TestRevenueAPI:
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "revenue"}

    def test_capture_lead_success(self, client):
        """Test successful lead capture"""
        response = client.post(
            "/revenue/capture-lead",
            json={
                "email": "test@example.com",
                "source": "organic",
                "content_id": 123,
                "utm_source": "twitter",
                "utm_campaign": "launch",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "lead_id" in data
        assert data["lead_score"] > 0

    def test_capture_lead_invalid_email(self, client):
        """Test lead capture with invalid email"""
        response = client.post(
            "/revenue/capture-lead", json={"email": "not-an-email", "source": "organic"}
        )

        assert response.status_code == 422  # Pydantic validation error

    def test_capture_duplicate_lead(self, client):
        """Test duplicate lead capture"""
        # First capture
        client.post(
            "/revenue/capture-lead",
            json={"email": "duplicate@example.com", "source": "organic"},
        )

        # Duplicate attempt
        response = client.post(
            "/revenue/capture-lead",
            json={"email": "duplicate@example.com", "source": "affiliate"},
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_inject_affiliate_links(self, client):
        """Test affiliate link injection"""
        response = client.post(
            "/revenue/inject-affiliate-links",
            json={
                "content": "I use Claude for AI tasks every day",
                "category": "ai_tools",
                "content_id": 123,
                "max_links": 2,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "enhanced_content" in data
        # Check for link pattern with case-insensitive matching
        assert "[claude](" in data["enhanced_content"].lower()
        assert len(data["injected_links"]) > 0

    def test_track_affiliate_click(self, client):
        """Test affiliate click tracking"""
        # First create a link - use lowercase to match merchant name
        inject_response = client.post(
            "/revenue/inject-affiliate-links",
            json={
                "content": "Check out claude for AI assistance",
                "category": "ai_tools",
            },
        )

        # Check if link was created
        assert inject_response.status_code == 200
        injected_links = inject_response.json()["injected_links"]

        # Should have injected links now
        assert len(injected_links) > 0, "No links were injected"

        link_id = injected_links[0]["link_id"]

        # Track click
        response = client.post(
            "/revenue/track-click",
            json={"link_id": link_id, "referrer": "https://threads.net"},
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_track_nonexistent_link(self, client):
        """Test tracking click on nonexistent link"""
        response = client.post("/revenue/track-click", json={"link_id": 999999})

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch("stripe.Customer.create")
    @patch("stripe.PaymentMethod.attach")
    @patch("stripe.Customer.modify")
    @patch("stripe.Subscription.create")
    def test_create_subscription(
        self,
        mock_sub_create,
        mock_customer_modify,
        mock_payment_attach,
        mock_customer_create,
        client,
    ):
        """Test subscription creation"""
        # Mock Stripe responses
        mock_customer_create.return_value = Mock(id="cus_test")
        mock_payment_attach.return_value = Mock(id="pm_test")
        mock_sub_create.return_value = Mock(
            id="sub_test",
            status="active",
            items=Mock(data=[Mock(price=Mock(id="price_test"))]),
        )

        response = client.post(
            "/revenue/create-subscription",
            json={
                "email": "subscriber@example.com",
                "tier": "pro",
                "payment_method_id": "pm_test123",
                "trial_days": 7,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["tier"] == "pro"
        assert "features" in data

    def test_get_revenue_analytics(self, client):
        """Test revenue analytics endpoint"""
        response = client.get("/revenue/analytics?days=30")

        assert response.status_code == 200
        data = response.json()
        assert "total_revenue" in data
        assert "current_mrr" in data
        assert "revenue_by_type" in data

    def test_get_affiliate_stats(self, client):
        """Test affiliate stats endpoint"""
        response = client.get("/revenue/affiliate-stats?days=30")

        assert response.status_code == 200
        data = response.json()
        assert "total_clicks" in data
        assert "total_conversions" in data
        assert "category_performance" in data

    def test_get_lead_funnel(self, client):
        """Test lead funnel endpoint"""
        response = client.get("/revenue/lead-funnel?days=30")

        assert response.status_code == 200
        data = response.json()
        assert "funnel" in data
        assert "source_performance" in data
        assert "avg_days_to_convert" in data

    def test_get_subscription_metrics(self, client):
        """Test subscription metrics endpoint"""
        response = client.get("/revenue/subscription-metrics")

        assert response.status_code == 200
        data = response.json()
        assert "tier_distribution" in data
        assert "total_mrr" in data
        assert "net_growth_30d" in data

    def test_get_revenue_forecast(self, client):
        """Test revenue forecast endpoint"""
        response = client.get("/revenue/forecast?months=12")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 12
        if data:
            assert "projected_mrr" in data[0]
            assert "projected_total_revenue" in data[0]

    def test_export_leads(self, client):
        """Test lead export endpoint"""
        # Get initial count of leads
        initial_response = client.get("/revenue/leads/export")
        initial_count = len(initial_response.json())

        # Add some test leads
        client.post(
            "/revenue/capture-lead",
            json={"email": "export1@example.com", "source": "organic"},
        )
        client.post(
            "/revenue/capture-lead",
            json={"email": "export2@example.com", "source": "affiliate"},
        )

        # Export all leads
        response = client.get("/revenue/leads/export")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == initial_count + 2  # Should have 2 more than initial
        assert all("email" in lead for lead in data)
        assert all("source" in lead for lead in data)

        # Check our specific leads are in the export
        emails = [lead["email"] for lead in data]
        assert "export1@example.com" in emails
        assert "export2@example.com" in emails
