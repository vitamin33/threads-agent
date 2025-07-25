import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.revenue.affiliate_manager import AffiliateLinkInjector, AffiliateMerchant
from services.revenue.db.models import AffiliateLink, Base, RevenueEvent


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
def affiliate_injector(test_db):
    """Create AffiliateLinkInjector with test database"""
    return AffiliateLinkInjector(test_db, affiliate_id="test123")


class TestAffiliateLinkInjector:
    def test_analyze_content_topics(self, affiliate_injector):
        """Test content topic analysis"""
        # Test AI content
        content = "I've been using ChatGPT and Claude for my daily AI tasks"
        topics = affiliate_injector.analyze_content_topics(content)
        assert "ai_tools" in topics

        # Test productivity content
        content = "My productivity workflow with Notion has improved dramatically"
        topics = affiliate_injector.analyze_content_topics(content)
        assert "productivity" in topics

        # Test multiple categories
        content = "Using AI tools like ChatGPT alongside Notion for productivity"
        topics = affiliate_injector.analyze_content_topics(content)
        assert "ai_tools" in topics
        assert "productivity" in topics

    def test_generate_affiliate_url(self, affiliate_injector):
        """Test affiliate URL generation"""
        merchant = AffiliateMerchant("test", "https://example.com", "ref", "test")

        # Basic URL
        url = affiliate_injector.generate_affiliate_url(merchant)
        assert "https://example.com?ref=test123" == url

        # URL with content ID
        url = affiliate_injector.generate_affiliate_url(merchant, content_id=42)
        assert "https://example.com?ref=test123&content_id=42" == url

        # URL that already has query params
        merchant.base_url = "https://example.com?source=app"
        url = affiliate_injector.generate_affiliate_url(merchant)
        assert "https://example.com?source=app&ref=test123" == url

    def test_inject_contextual_links(self, affiliate_injector, test_db):
        """Test contextual link injection"""
        content = "I love using Claude for AI tasks and Notion for organizing my work"

        enhanced_content, links = affiliate_injector.inject_contextual_links(
            content, topic_category="ai_tools", content_id=1, max_links=2
        )

        # Check that links were injected
        assert "[claude](" in enhanced_content
        assert len(links) == 1  # Only Claude from ai_tools category

        # Check database records
        affiliate_links = test_db.query(AffiliateLink).all()
        assert len(affiliate_links) == 1
        assert affiliate_links[0].merchant == "claude"
        assert affiliate_links[0].content_id == 1

    def test_inject_links_with_max_limit(self, affiliate_injector):
        """Test max links limit"""
        content = "ChatGPT, Claude, Midjourney, and Perplexity are all great AI tools"

        enhanced_content, links = affiliate_injector.inject_contextual_links(
            content, topic_category="ai_tools", max_links=2
        )

        # Should only inject 2 links despite 4 matches
        assert len(links) == 2

    def test_track_click(self, affiliate_injector, test_db):
        """Test click tracking"""
        # Create a link
        link = AffiliateLink(
            link_url="https://example.com?ref=test123", category="test", merchant="test"
        )
        test_db.add(link)
        test_db.commit()

        # Track click
        success = affiliate_injector.track_click(
            link.id, referrer="https://threads.net"
        )
        assert success is True

        # Verify click was recorded
        test_db.refresh(link)
        assert link.click_count == 1

        # Verify revenue event
        events = test_db.query(RevenueEvent).all()
        assert len(events) == 1
        assert events[0].event_type == "affiliate_click"

    def test_track_conversion(self, affiliate_injector, test_db):
        """Test conversion tracking"""
        # Create a link with clicks
        link = AffiliateLink(
            link_url="https://example.com?ref=test123",
            category="test",
            merchant="test",
            click_count=5,
        )
        test_db.add(link)
        test_db.commit()

        # Track conversion
        commission = 15.50
        success = affiliate_injector.track_conversion(
            link.id, commission, customer_email="test@example.com"
        )
        assert success is True

        # Verify conversion was recorded
        test_db.refresh(link)
        assert link.conversion_count == 1
        assert float(link.revenue_generated) == commission

        # Verify revenue event
        events = test_db.query(RevenueEvent).all()
        assert len(events) == 1
        assert events[0].event_type == "affiliate_commission"
        assert float(events[0].amount) == commission
        assert events[0].customer_email == "test@example.com"

    def test_get_top_performing_links(self, affiliate_injector, test_db):
        """Test getting top performing links"""
        # Create links with different performance
        links_data = [
            ("merchant1", 100, 10, 500.00),
            ("merchant2", 50, 2, 50.00),
            ("merchant3", 200, 20, 1000.00),
        ]

        for merchant, clicks, conversions, revenue in links_data:
            link = AffiliateLink(
                link_url=f"https://{merchant}.com?ref=test123",
                category="test",
                merchant=merchant,
                click_count=clicks,
                conversion_count=conversions,
                revenue_generated=revenue,
            )
            test_db.add(link)
        test_db.commit()

        # Get top performing
        top_links = affiliate_injector.get_top_performing_links(limit=2)

        assert len(top_links) == 2
        assert top_links[0]["merchant"] == "merchant3"  # Highest revenue
        assert top_links[0]["revenue"] == 1000.00
        assert top_links[0]["conversion_rate"] == 10.0  # 20/200 * 100

        assert top_links[1]["merchant"] == "merchant1"
        assert top_links[1]["revenue"] == 500.00
