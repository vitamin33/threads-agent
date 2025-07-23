from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.revenue.db.models import Base
from services.revenue.main import app, get_db


@pytest.fixture
def test_db():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


@pytest.fixture
def client(test_db):
    """Create test client with test database"""

    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


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
        assert "[Claude](" in data["enhanced_content"]
        assert len(data["injected_links"]) > 0

    def test_track_affiliate_click(self, client):
        """Test affiliate click tracking"""
        # First create a link
        inject_response = client.post(
            "/revenue/inject-affiliate-links",
            json={"content": "Check out Claude", "category": "ai_tools"},
        )
        link_id = inject_response.json()["injected_links"][0]["link_id"]

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
        # Add some test leads first
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
        assert len(data) == 2
        assert all("email" in lead for lead in data)
        assert all("source" in lead for lead in data)
