"""Unit tests for LinkedIn publisher."""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from services.achievement_collector.publishers.linkedin_publisher import (
    LinkedInPublisher,
)
from services.achievement_collector.db.models import Achievement


class TestLinkedInPublisher:
    """Test LinkedIn publisher functionality."""

    @pytest.fixture
    def publisher(self):
        """Create LinkedIn publisher instance."""
        with patch.dict(
            "os.environ",
            {
                "LINKEDIN_CLIENT_ID": "test_client_id",
                "LINKEDIN_CLIENT_SECRET": "test_secret",
                "LINKEDIN_ACCESS_TOKEN": "test_token",
                "LINKEDIN_PERSON_URN": "urn:li:person:12345",
            },
        ):
            return LinkedInPublisher()

    @pytest.fixture
    def mock_achievement(self):
        """Create a mock achievement."""
        achievement = Mock(spec=Achievement)
        achievement.id = 1
        achievement.title = "Implemented OAuth2 Authentication"
        achievement.description = "Built secure OAuth2 flow with JWT tokens"
        achievement.category = "feature"
        achievement.skills_demonstrated = ["Python", "OAuth2", "Security", "JWT"]
        achievement.impact_score = 85.0
        achievement.complexity_score = 75.0
        achievement.portfolio_ready = True
        achievement.metrics_after = {
            "lines_added": 500,
            "test_coverage": 95,
            "security_score": 98,
        }
        achievement.linkedin_post_id = None
        achievement.linkedin_published_at = None
        return achievement

    def test_initialization(self, publisher):
        """Test publisher initialization."""
        assert publisher.client_id == "test_client_id"
        assert publisher.access_token == "test_token"
        assert publisher.person_urn == "urn:li:person:12345"
        assert publisher.is_configured() is True

    def test_not_configured(self):
        """Test when LinkedIn is not configured."""
        publisher = LinkedInPublisher()
        assert publisher.is_configured() is False

    def test_generate_fallback_post(self, publisher, mock_achievement):
        """Test fallback post generation."""
        post = publisher._generate_fallback_post(mock_achievement)

        assert mock_achievement.title in post
        assert "Python" in post
        assert "#SoftwareEngineering" in post
        assert "#Feature" in post
        assert len(post) <= 1300  # LinkedIn limit

    def test_format_metrics(self, publisher):
        """Test metrics formatting."""
        metrics = {
            "lines_added": 1500,
            "test_coverage": 92,
            "performance_improvement": 35,
            "issues_resolved": 8,
            "extra_metric": "ignored",
        }

        formatted = publisher._format_metrics(metrics)

        assert "1,500 lines of code added" in formatted
        assert "92% test coverage" in formatted
        assert "35% performance boost" in formatted
        assert "extra_metric" not in formatted  # Should limit to 3

    @pytest.mark.asyncio
    async def test_generate_post_content_with_ai(self, publisher, mock_achievement):
        """Test post content generation with AI."""
        mock_ai_response = """🚀 Just completed a major security upgrade!

Implemented a robust OAuth2 authentication system with JWT tokens, enhancing our application's security posture.

Key achievements:
✅ Built secure token-based authentication
✅ Achieved 95% test coverage
✅ Improved security score to 98/100

Technologies used: Python • OAuth2 • JWT • Security Best Practices

Looking forward to implementing more security features!

#OAuth2 #SecurityEngineering #Python #Authentication #SoftwareDevelopment"""

        with patch.object(
            publisher.ai_analyzer, "generate_linkedin_content", new_callable=AsyncMock
        ) as mock_ai:
            mock_ai.return_value = mock_ai_response

            content = await publisher._generate_post_content(mock_achievement)

            assert content["text"].startswith("🚀")
            assert "OAuth2" in content["text"]
            assert content["achievement_id"] == 1
            assert content["category"] == "feature"

    @pytest.mark.asyncio
    async def test_generate_post_content_fallback(self, publisher, mock_achievement):
        """Test post content generation when AI fails."""
        with patch.object(
            publisher.ai_analyzer, "generate_linkedin_content", new_callable=AsyncMock
        ) as mock_ai:
            mock_ai.return_value = None  # AI failure

            content = await publisher._generate_post_content(mock_achievement)

            # Should use fallback
            assert mock_achievement.title in content["text"]
            assert "Python" in content["text"]
            assert "📊 Key Metrics:" in content["text"]

    @pytest.mark.asyncio
    async def test_create_linkedin_post_success(self, publisher):
        """Test successful LinkedIn post creation."""
        content = {
            "text": "Test post content",
            "achievement_id": 1,
            "category": "feature",
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.headers = {"X-RestLi-Id": "urn:li:share:123456"}
            mock_client.post.return_value = mock_response

            post_id = await publisher._create_linkedin_post(content)

            assert post_id == "urn:li:share:123456"
            mock_client.post.assert_called_once()

            # Check API call
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "https://api.linkedin.com/v2/ugcPosts"
            assert call_args[1]["headers"]["Authorization"] == "Bearer test_token"
            assert content["text"] in str(call_args[1]["json"])

    @pytest.mark.asyncio
    async def test_create_linkedin_post_failure(self, publisher):
        """Test LinkedIn post creation failure."""
        content = {"text": "Test post"}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Bad request"
            mock_client.post.return_value = mock_response

            post_id = await publisher._create_linkedin_post(content)

            assert post_id is None

    def test_should_publish(self, publisher, mock_achievement):
        """Test publish decision logic."""
        recent_posts = []

        # Should publish portfolio-ready achievement
        assert publisher.should_publish(mock_achievement, recent_posts) is True

        # Should not publish if not portfolio ready
        mock_achievement.portfolio_ready = False
        assert publisher.should_publish(mock_achievement, recent_posts) is False
        mock_achievement.portfolio_ready = True

        # Should not publish if impact score too low
        mock_achievement.impact_score = 50
        assert publisher.should_publish(mock_achievement, recent_posts) is False
        mock_achievement.impact_score = 85

        # Should not publish if already posted
        recent_posts = [
            {
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": "Just finished: Implemented OAuth2 Authentication"
                        }
                    }
                }
            }
        ]
        assert publisher.should_publish(mock_achievement, recent_posts) is False

    @pytest.mark.asyncio
    async def test_publish_achievement_success(self, publisher, mock_achievement):
        """Test publishing a single achievement."""
        with patch.object(
            publisher, "_generate_post_content", new_callable=AsyncMock
        ) as mock_gen:
            with patch.object(
                publisher, "_create_linkedin_post", new_callable=AsyncMock
            ) as mock_create:
                mock_gen.return_value = {"text": "Test post", "achievement_id": 1}
                mock_create.return_value = "urn:li:share:123456"

                post_id = await publisher.publish_achievement(mock_achievement)

                assert post_id == "urn:li:share:123456"
                mock_gen.assert_called_once_with(mock_achievement)
                mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_batch(self, publisher):
        """Test batch publishing."""
        # Create mock database and achievements
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query

        # Create test achievements
        achievements = []
        for i in range(3):
            ach = Mock(spec=Achievement)
            ach.id = i + 1
            ach.title = f"Achievement {i + 1}"
            ach.portfolio_ready = True
            ach.impact_score = 75 + i * 5
            ach.linkedin_post_id = None
            achievements.append(ach)

        mock_query.all.return_value = achievements

        with patch.object(
            publisher, "get_recent_posts", new_callable=AsyncMock
        ) as mock_recent:
            with patch.object(
                publisher, "publish_achievement", new_callable=AsyncMock
            ) as mock_publish:
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    mock_recent.return_value = []
                    mock_publish.side_effect = [
                        "post1",
                        "post2",
                        None,
                    ]  # Third one fails

                    await publisher.publish_batch(mock_db, limit=3)

                    # Should have tried to publish 3 achievements
                    assert mock_publish.call_count == 3

                    # Should have updated the successful ones
                    assert achievements[0].linkedin_post_id == "post1"
                    assert achievements[1].linkedin_post_id == "post2"
                    assert achievements[2].linkedin_post_id is None

                    # Should have committed changes
                    assert mock_db.commit.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
