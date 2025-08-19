"""Tests for multi-platform analytics collectors"""

import pytest

# This will fail initially since we haven't implemented the collectors yet
pytest.importorskip("services.tech_doc_generator.app.services.analytics_collectors")


class TestBaseAnalyticsCollector:
    """Test the base analytics collector interface"""

    def test_base_collector_has_required_methods(self):
        """Test that base collector defines required interface methods"""
        from services.tech_doc_generator.app.services.analytics_collectors import (
            BaseAnalyticsCollector,
        )

        # Base collector should be abstract and define required methods
        assert hasattr(BaseAnalyticsCollector, "get_metrics")
        assert hasattr(BaseAnalyticsCollector, "get_conversion_data")
        assert hasattr(BaseAnalyticsCollector, "platform_name")


class TestLinkedInAnalyticsCollector:
    """Test LinkedIn analytics collector"""

    @pytest.fixture
    def linkedin_collector(self):
        """Create LinkedIn collector instance"""
        from services.tech_doc_generator.app.services.analytics_collectors import (
            LinkedInAnalyticsCollector,
        )

        return LinkedInAnalyticsCollector(profile_id="vitaliiserbyn")

    @pytest.mark.asyncio
    async def test_get_profile_metrics_returns_expected_structure(
        self, linkedin_collector
    ):
        """Test that LinkedIn collector returns metrics in expected format"""
        metrics = await linkedin_collector.get_metrics()

        # Should return dict with required LinkedIn metrics
        assert isinstance(metrics, dict)
        assert "profile_views" in metrics
        assert "post_engagement" in metrics
        assert "connection_requests" in metrics
        assert "ai_hiring_manager_connections" in metrics
        assert "platform" in metrics
        assert metrics["platform"] == "linkedin"
        assert "collected_at" in metrics

    @pytest.mark.asyncio
    async def test_get_conversion_data_tracks_serbyn_pro_visits(
        self, linkedin_collector
    ):
        """Test that LinkedIn collector tracks conversions to serbyn.pro"""
        conversion_data = await linkedin_collector.get_conversion_data()

        # Should track conversions from LinkedIn content to serbyn.pro
        assert isinstance(conversion_data, dict)
        assert "source_platform" in conversion_data
        assert conversion_data["source_platform"] == "linkedin"
        assert "serbyn_pro_visits" in conversion_data
        assert "job_inquiries" in conversion_data
        assert "content_to_visit_conversion_rate" in conversion_data


class TestTwitterAnalyticsCollector:
    """Test Twitter analytics collector"""

    @pytest.fixture
    def twitter_collector(self):
        """Create Twitter collector instance"""
        from services.tech_doc_generator.app.services.analytics_collectors import (
            TwitterAnalyticsCollector,
        )

        return TwitterAnalyticsCollector(username="vitaliiserbyn")

    @pytest.mark.asyncio
    async def test_get_metrics_returns_twitter_specific_data(self, twitter_collector):
        """Test that Twitter collector returns Twitter-specific metrics"""
        metrics = await twitter_collector.get_metrics()

        assert isinstance(metrics, dict)
        assert "impressions" in metrics
        assert "retweets" in metrics
        assert "profile_visits" in metrics
        assert "follower_growth" in metrics
        assert "platform" in metrics
        assert metrics["platform"] == "twitter"


class TestMediumAnalyticsCollector:
    """Test Medium analytics collector"""

    @pytest.fixture
    def medium_collector(self):
        """Create Medium collector instance"""
        from services.tech_doc_generator.app.services.analytics_collectors import (
            MediumAnalyticsCollector,
        )

        return MediumAnalyticsCollector(username="vitaliiserbyn")

    @pytest.mark.asyncio
    async def test_get_metrics_returns_medium_specific_data(self, medium_collector):
        """Test that Medium collector returns Medium-specific metrics"""
        metrics = await medium_collector.get_metrics()

        assert isinstance(metrics, dict)
        assert "read_ratio" in metrics
        assert "claps" in metrics
        assert "follower_conversion" in metrics
        assert "profile_visits" in metrics
        assert "platform" in metrics
        assert metrics["platform"] == "medium"


class TestGitHubAnalyticsCollector:
    """Test GitHub analytics collector"""

    @pytest.fixture
    def github_collector(self):
        """Create GitHub collector instance"""
        from services.tech_doc_generator.app.services.analytics_collectors import (
            GitHubAnalyticsCollector,
        )

        return GitHubAnalyticsCollector(username="vitamin33")

    @pytest.mark.asyncio
    async def test_get_metrics_returns_github_specific_data(self, github_collector):
        """Test that GitHub collector returns GitHub-specific metrics"""
        metrics = await github_collector.get_metrics()

        assert isinstance(metrics, dict)
        assert "profile_visits" in metrics
        assert "repository_traffic" in metrics
        assert "stars_from_content" in metrics
        assert "platform" in metrics
        assert metrics["platform"] == "github"


class TestThreadsAnalyticsCollector:
    """Test Threads analytics collector"""

    @pytest.fixture
    def threads_collector(self):
        """Create Threads collector instance"""
        from services.tech_doc_generator.app.services.analytics_collectors import (
            ThreadsAnalyticsCollector,
        )

        return ThreadsAnalyticsCollector(username="vitaliiserbyn")

    @pytest.mark.asyncio
    async def test_get_metrics_returns_threads_specific_data(self, threads_collector):
        """Test that Threads collector returns Threads-specific metrics"""
        metrics = await threads_collector.get_metrics()

        assert isinstance(metrics, dict)
        assert "engagement_metrics" in metrics
        assert "reach" in metrics
        assert "conversation_starters" in metrics
        assert "platform" in metrics
        assert metrics["platform"] == "threads"
