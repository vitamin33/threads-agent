from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.revenue.db.models import Base, Customer, Lead, RevenueEvent
from services.revenue.lead_capture import LeadCapture


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
def lead_capture(test_db):
    """Create LeadCapture with test database"""
    return LeadCapture(test_db)


class TestLeadCapture:
    def test_validate_and_score_email(self, lead_capture):
        """Test email validation and scoring"""
        # Valid corporate email
        result = lead_capture.validate_and_score_email("john@company.com")
        assert result["valid"] is True
        assert result["domain"] == "company.com"
        assert result["domain_score"] == 20  # Corporate score

        # Valid Gmail
        result = lead_capture.validate_and_score_email("user@gmail.com")
        assert result["valid"] is True
        assert result["domain_score"] == 10  # Gmail score

        # Invalid email
        result = lead_capture.validate_and_score_email("not-an-email")
        assert result["valid"] is False

    def test_capture_email_success(self, lead_capture, test_db):
        """Test successful email capture"""
        result = lead_capture.capture_email(
            email="test@example.com",
            source="organic",
            content_id=123,
            utm_params={"utm_source": "twitter", "utm_campaign": "launch"},
            metadata={"view_duration": 45},  # Quick engagement
        )

        assert result["success"] is True
        assert "lead_id" in result
        assert result["lead_score"] > 0

        # Verify lead was created
        lead = test_db.query(Lead).first()
        assert lead is not None
        assert lead.email == "test@example.com"
        assert lead.source == "organic"
        assert lead.content_id == 123
        assert lead.utm_source == "twitter"
        assert lead.utm_campaign == "launch"

        # Verify revenue event
        event = test_db.query(RevenueEvent).first()
        assert event is not None
        assert event.event_type == "lead_capture"
        assert event.customer_email == "test@example.com"

    def test_capture_duplicate_email(self, lead_capture, test_db):
        """Test duplicate email handling"""
        # First capture
        lead_capture.capture_email(email="test@example.com", source="organic")

        # Duplicate attempt
        result = lead_capture.capture_email(
            email="test@example.com", source="affiliate"
        )

        assert result["success"] is False
        assert "already registered" in result["error"]

        # Verify only one lead exists
        lead_count = test_db.query(Lead).count()
        assert lead_count == 1

    def test_lead_scoring(self, lead_capture):
        """Test lead scoring logic"""
        # High-value lead: corporate email, immediate engagement, affiliate source
        result = lead_capture.capture_email(
            email="executive@fortune500.com",
            source="affiliate",
            metadata={"view_duration": 30},  # Immediate signup
        )

        # Should have high score: 20 (corporate) + 20 (affiliate) + 25 (immediate)
        assert result["lead_score"] >= 65

        # Lower-value lead: gmail, delayed engagement, direct source
        result2 = lead_capture.capture_email(
            email="casual@gmail.com",
            source="direct",
            metadata={"view_duration": 3600},  # Signed up after 1 hour
        )

        # Should have lower score: 10 (gmail) + 10 (direct) + 5 (delayed)
        assert result2["lead_score"] <= 25

    def test_mark_conversion(self, lead_capture, test_db):
        """Test lead conversion"""
        # Create a lead
        lead_capture.capture_email(
            email="converter@example.com", source="organic", content_id=123
        )

        # Mark as converted
        success = lead_capture.mark_conversion("converter@example.com", 97.00)
        assert success is True

        # Verify lead was updated
        lead = test_db.query(Lead).filter_by(email="converter@example.com").first()
        assert lead.converted is True
        assert lead.conversion_date is not None

        # Verify customer was created
        customer = (
            test_db.query(Customer).filter_by(email="converter@example.com").first()
        )
        assert customer is not None
        assert float(customer.lifetime_value) == 97.00
        assert customer.acquisition_source == "organic"

        # Verify revenue event
        events = (
            test_db.query(RevenueEvent).filter_by(event_type="lead_conversion").all()
        )
        assert len(events) == 1
        assert float(events[0].amount) == 97.00

    def test_get_lead_analytics(self, lead_capture, test_db):
        """Test lead analytics"""
        # Create test data
        sources = ["organic", "organic", "affiliate", "direct"]
        for i, source in enumerate(sources):
            lead = Lead(
                email=f"test{i}@example.com",
                source=source,
                lead_score=20 + i * 10,
                captured_at=datetime.utcnow() - timedelta(days=i),
                converted=(i < 2),  # First 2 are converted
            )
            test_db.add(lead)
        test_db.commit()

        # Get analytics
        analytics = lead_capture.get_lead_analytics(days=30)

        assert analytics["total_leads"] == 4
        assert analytics["converted_leads"] == 2
        assert analytics["conversion_rate"] == 50.0
        assert analytics["average_lead_score"] > 0
        assert analytics["leads_by_source"]["organic"] == 2
        assert analytics["leads_by_source"]["affiliate"] == 1
        assert analytics["leads_by_source"]["direct"] == 1

    def test_export_leads(self, lead_capture, test_db):
        """Test lead export"""
        # Create test leads
        for i in range(3):
            lead = Lead(
                email=f"test{i}@example.com",
                source="organic",
                lead_score=50,
                converted=(i == 0),  # Only first is converted
            )
            test_db.add(lead)
        test_db.commit()

        # Export all
        all_leads = lead_capture.export_leads(converted_only=False)
        assert len(all_leads) == 3

        # Export converted only
        converted_leads = lead_capture.export_leads(converted_only=True)
        assert len(converted_leads) == 1
        assert converted_leads[0]["email"] == "test0@example.com"
