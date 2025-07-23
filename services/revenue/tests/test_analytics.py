from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.revenue.analytics import RevenueAnalytics
from services.revenue.db.models import (
    AffiliateLink,
    Base,
    Customer,
    Lead,
    RevenueEvent,
    Subscription,
)


@pytest.fixture
def test_db():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def analytics(test_db):
    """Create RevenueAnalytics with test database"""
    return RevenueAnalytics(test_db)


@pytest.fixture
def sample_data(test_db):
    """Create sample data for analytics tests"""
    # Revenue events
    events = [
        ("subscription", 97.00, datetime.utcnow() - timedelta(days=5)),
        ("subscription", 29.00, datetime.utcnow() - timedelta(days=10)),
        ("affiliate_commission", 15.50, datetime.utcnow() - timedelta(days=2)),
        ("affiliate_commission", 25.00, datetime.utcnow() - timedelta(days=7)),
        ("lead_conversion", 0.00, datetime.utcnow() - timedelta(days=3)),
    ]

    for event_type, amount, created_at in events:
        event = RevenueEvent(
            event_type=event_type, amount=amount, created_at=created_at
        )
        test_db.add(event)

    # Active subscriptions
    subscriptions = [
        ("basic", 29.00, "active"),
        ("pro", 97.00, "active"),
        ("enterprise", 297.00, "active"),
        ("basic", 29.00, "canceled"),
    ]

    for tier, amount, status in subscriptions:
        sub = Subscription(
            stripe_subscription_id=f"sub_{tier}_{status}",
            stripe_customer_id="cus_test",
            customer_email=f"{tier}@example.com",
            tier=tier,
            status=status,
            monthly_amount=amount,
            created_at=datetime.utcnow() - timedelta(days=30),
        )
        test_db.add(sub)

    # Customers
    for i in range(5):
        customer = Customer(
            email=f"customer{i}@example.com",
            acquisition_date=datetime.utcnow() - timedelta(days=20 - i),
        )
        test_db.add(customer)

    test_db.commit()


class TestRevenueAnalytics:
    def test_get_revenue_summary(self, analytics, sample_data):
        """Test revenue summary analytics"""
        summary = analytics.get_revenue_summary(days=30)

        assert summary["period_days"] == 30
        assert summary["total_revenue"] > 0
        assert "subscription" in summary["revenue_by_type"]
        assert "affiliate_commission" in summary["revenue_by_type"]
        assert summary["current_mrr"] == 29.00 + 97.00 + 297.00  # Active subscriptions
        assert summary["projected_annual_revenue"] == summary["current_mrr"] * 12
        assert summary["total_customers"] == 5
        assert summary["new_customers"] == 5  # All created within 30 days
        assert summary["arpu"] > 0

    def test_get_affiliate_performance(self, analytics, test_db):
        """Test affiliate performance analytics"""
        # Create affiliate links
        links = [
            ("ai_tools", "claude", 100, 5, 250.00),
            ("ai_tools", "chatgpt", 80, 3, 150.00),
            ("productivity", "notion", 50, 2, 100.00),
        ]

        for category, merchant, clicks, conversions, revenue in links:
            link = AffiliateLink(
                link_url=f"https://{merchant}.com?ref=test",
                category=category,
                merchant=merchant,
                click_count=clicks,
                conversion_count=conversions,
                revenue_generated=revenue,
            )
            test_db.add(link)
        test_db.commit()

        # Get performance
        performance = analytics.get_affiliate_performance(days=30)

        assert performance["total_clicks"] == 230
        assert performance["total_conversions"] == 10
        assert performance["total_revenue"] == 500.00
        assert performance["overall_conversion_rate"] == pytest.approx(4.35, 0.01)

        # Check category performance
        ai_tools_perf = next(
            cat
            for cat in performance["category_performance"]
            if cat["category"] == "ai_tools"
        )
        assert ai_tools_perf["clicks"] == 180
        assert ai_tools_perf["revenue"] == 400.00

        # Check top merchants
        assert len(performance["top_merchants"]) == 3
        assert performance["top_merchants"][0]["merchant"] == "claude"

    def test_get_lead_funnel_metrics(self, analytics, test_db):
        """Test lead funnel analytics"""
        # Create leads with different scores and conversion status
        leads = [
            ("lead1@example.com", 45, True, datetime.utcnow() - timedelta(days=5)),
            ("lead2@example.com", 35, True, datetime.utcnow() - timedelta(days=3)),
            ("lead3@example.com", 25, False, datetime.utcnow() - timedelta(days=10)),
            ("lead4@example.com", 15, False, datetime.utcnow() - timedelta(days=7)),
        ]

        for email, score, converted, captured_at in leads:
            lead = Lead(
                email=email,
                source="organic",
                lead_score=score,
                converted=converted,
                captured_at=captured_at,
                conversion_date=captured_at + timedelta(days=2) if converted else None,
            )
            test_db.add(lead)
        test_db.commit()

        # Get funnel metrics
        funnel = analytics.get_lead_funnel_metrics(days=30)

        assert funnel["funnel"]["total_leads"] == 4
        assert funnel["funnel"]["qualified_leads"] == 2  # Score >= 30
        assert funnel["funnel"]["converted_leads"] == 2
        assert funnel["funnel"]["conversion_rate"] == 50.0
        assert funnel["avg_days_to_convert"] == 2.0

    def test_get_subscription_metrics(self, analytics, sample_data):
        """Test subscription metrics"""
        metrics = analytics.get_subscription_metrics()

        # Check tier distribution
        assert (
            len(metrics["tier_distribution"]) == 3
        )  # basic, pro, enterprise (active only)

        basic_tier = next(
            tier for tier in metrics["tier_distribution"] if tier["tier"] == "basic"
        )
        assert basic_tier["active_subscriptions"] == 1
        assert basic_tier["mrr"] == 29.00

        assert metrics["total_mrr"] == 423.00  # 29 + 97 + 297

    def test_get_revenue_forecast(self, analytics, test_db):
        """Test revenue forecasting"""
        # Add some historical revenue data
        for i in range(3):
            event = RevenueEvent(
                event_type="subscription",
                amount=100.00 * (1 + i * 0.1),  # Growing revenue
                created_at=datetime.utcnow() - timedelta(days=30 * (3 - i)),
            )
            test_db.add(event)
        test_db.commit()

        # Get forecast
        forecast = analytics.get_revenue_forecast(months=6)

        assert len(forecast) == 6
        assert all("projected_mrr" in month for month in forecast)
        assert all("projected_total_revenue" in month for month in forecast)
        assert all("cumulative_revenue" in month for month in forecast)

        # Should show growth trend
        assert forecast[5]["projected_mrr"] > forecast[0]["projected_mrr"]
