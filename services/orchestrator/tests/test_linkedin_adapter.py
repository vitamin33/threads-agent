"""
Tests for LinkedIn Platform Adapter.

This module tests the LinkedIn adapter implementation including:
- Content formatting for LinkedIn posts
- Manual publishing workflow (due to API restrictions)
- Content validation and preparation
- LinkedIn-specific character limits and formatting
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

from services.orchestrator.publishing.adapters.linkedin import LinkedInAdapter
from services.orchestrator.publishing.adapters.base import PublishingResult
from services.orchestrator.db.models import ContentItem


class TestLinkedInAdapter:
    """Test LinkedIn platform adapter functionality."""

    def test_linkedin_adapter_initialization(self):
        """Test that LinkedInAdapter initializes correctly."""
        # This will fail - LinkedInAdapter doesn't exist yet
        adapter = LinkedInAdapter()
        
        assert adapter.platform_name == "linkedin"
        assert adapter.supports_retry is False  # Manual publishing doesn't support auto-retry

    @pytest.mark.asyncio
    async def test_linkedin_content_validation_success(self, sample_content_item):
        """Test successful content validation for LinkedIn."""
        # This will fail - validation method doesn't exist yet
        adapter = LinkedInAdapter()
        platform_config = {}  # LinkedIn doesn't need API key for manual publishing
        
        is_valid = await adapter.validate_content(sample_content_item, platform_config)
        
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_linkedin_content_validation_too_long(self):
        """Test content validation fails when content is too long for LinkedIn."""
        # This will fail - validation doesn't check length yet
        adapter = LinkedInAdapter()
        platform_config = {}
        
        # LinkedIn has a 3000 character limit
        long_content = "A" * 3001
        content_item = ContentItem(
            id=1,
            title="Test Post",
            content=long_content,
            content_type="post",
            author_id="test_author",
            status="ready"
        )
        
        is_valid = await adapter.validate_content(content_item, platform_config)
        
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_linkedin_publish_creates_draft(self, sample_content_item):
        """Test that LinkedIn 'publishing' creates a draft for manual posting."""
        # This will fail - publish method doesn't exist yet
        adapter = LinkedInAdapter()
        platform_config = {}
        
        result = await adapter.publish(sample_content_item, platform_config)
        
        assert isinstance(result, PublishingResult)
        assert result.success is True
        assert result.platform == "linkedin"
        assert "draft" in result.metadata
        assert "formatted_content" in result.metadata

    @pytest.mark.asyncio
    async def test_linkedin_content_formatting(self, sample_content_item):
        """Test that content is properly formatted for LinkedIn."""
        # This will fail - formatting method doesn't exist yet
        adapter = LinkedInAdapter()
        
        formatted_content = adapter._format_content_for_linkedin(sample_content_item)
        
        assert isinstance(formatted_content, str)
        assert len(formatted_content) <= 3000  # LinkedIn character limit
        assert "🚀" in formatted_content  # Should include engaging emoji
        assert "#" in formatted_content  # Should include hashtags
        
        # Should have professional tone
        assert any(word in formatted_content.lower() for word in ["insights", "experience", "thoughts"])

    def test_linkedin_hashtag_formatting(self):
        """Test that hashtags are properly formatted for LinkedIn."""
        # This will fail - hashtag formatting doesn't exist yet
        adapter = LinkedInAdapter()
        
        tags = ["python", "web development", "api-design", "machine learning"]
        formatted_hashtags = adapter._format_hashtags_for_linkedin(tags)
        
        assert isinstance(formatted_hashtags, list)
        # Should remove spaces and special characters
        assert "#python" in formatted_hashtags
        assert "#webdevelopment" in formatted_hashtags
        assert "#apidesign" in formatted_hashtags
        assert "#machinelearning" in formatted_hashtags
        
        # Should limit to reasonable number (5-7 hashtags)
        assert len(formatted_hashtags) <= 7

    def test_linkedin_content_length_optimization(self):
        """Test that long content is optimized for LinkedIn."""
        # This will fail - content optimization doesn't exist yet
        adapter = LinkedInAdapter()
        
        long_content = "This is a very long article. " * 200  # Way too long for LinkedIn
        
        optimized_content = adapter._optimize_content_length(
            title="Test Article",
            content=long_content,
            max_length=3000
        )
        
        assert len(optimized_content) <= 3000
        assert "..." in optimized_content  # Should indicate truncation
        assert optimized_content.endswith("...")

    @pytest.mark.asyncio
    async def test_linkedin_publish_includes_call_to_action(self, sample_content_item):
        """Test that LinkedIn posts include appropriate call-to-action."""
        # This will fail - CTA generation doesn't exist yet
        adapter = LinkedInAdapter()
        platform_config = {}
        
        result = await adapter.publish(sample_content_item, platform_config)
        
        formatted_content = result.metadata["formatted_content"]
        
        # Should include professional CTA
        cta_indicators = [
            "What's your experience",
            "Share your thoughts",
            "Let me know",
            "What do you think"
        ]
        
        assert any(cta in formatted_content for cta in cta_indicators)


@pytest.fixture
def sample_content_item():
    """Create a sample ContentItem for testing."""
    return ContentItem(
        id=1,
        title="Building Scalable AI Systems: Lessons from Production",
        content="In my experience building AI systems at scale, I've learned that the biggest challenges aren't always technical. Here are the key insights that helped our team build robust AI pipelines that serve millions of requests daily.",
        content_type="article",
        author_id="test_author",
        status="ready",
        content_metadata={
            "tags": ["ai", "machine learning", "scalability", "production", "engineering"],
            "description": "Key insights from building AI systems at scale",
            "industry_focus": "technology"
        },
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )