"""
Tests for Dev.to Platform Adapter.

This module tests the Dev.to adapter implementation including:
- Content formatting for Dev.to
- API integration and error handling
- Rate limiting and retry logic
- Content validation
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

from services.orchestrator.publishing.adapters.devto import DevToAdapter
from services.orchestrator.publishing.adapters.base import PublishingResult
from services.orchestrator.db.models import ContentItem


class TestDevToAdapter:
    """Test Dev.to platform adapter functionality."""

    def test_devto_adapter_initialization(self):
        """Test that DevToAdapter initializes correctly."""
        # This will fail - DevToAdapter doesn't exist yet
        adapter = DevToAdapter()
        
        assert adapter.platform_name == "dev.to"
        assert adapter.supports_retry is True

    @pytest.mark.asyncio
    async def test_devto_content_validation_success(self, sample_content_item):
        """Test successful content validation for Dev.to."""
        # This will fail - validation method doesn't exist yet
        adapter = DevToAdapter()
        platform_config = {"api_key": "test_key"}
        
        is_valid = await adapter.validate_content(sample_content_item, platform_config)
        
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_devto_content_validation_missing_title(self):
        """Test content validation fails when title is missing."""
        # This will fail - validation doesn't check title yet
        adapter = DevToAdapter()
        platform_config = {"api_key": "test_key"}
        
        content_item = ContentItem(
            id=1,
            title="",  # Empty title should fail validation
            content="Valid content",
            content_type="article",
            author_id="test_author",
            status="ready"
        )
        
        is_valid = await adapter.validate_content(content_item, platform_config)
        
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_devto_content_validation_missing_api_key(self, sample_content_item):
        """Test content validation fails when API key is missing."""
        # This will fail - validation doesn't check API key yet
        adapter = DevToAdapter()
        platform_config = {}  # Missing API key
        
        is_valid = await adapter.validate_content(sample_content_item, platform_config)
        
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_devto_publish_success(self, sample_content_item):
        """Test successful publishing to Dev.to."""
        # This will fail - publish method doesn't exist yet
        adapter = DevToAdapter()
        platform_config = {"api_key": "test_key"}
        
        # Mock the HTTP client
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "id": 12345,
                "url": "https://dev.to/test/article-12345",
                "published_at": "2024-01-01T00:00:00Z"
            }
            mock_response.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await adapter.publish(sample_content_item, platform_config)
            
            assert isinstance(result, PublishingResult)
            assert result.success is True
            assert result.platform == "dev.to"
            assert result.external_id == "12345"
            assert result.url == "https://dev.to/test/article-12345"

    @pytest.mark.asyncio
    async def test_devto_publish_api_error(self, sample_content_item):
        """Test publishing handles API errors properly."""
        # This will fail - error handling doesn't exist yet
        adapter = DevToAdapter()
        platform_config = {"api_key": "test_key"}
        
        # Mock HTTP client to return error
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 422
            mock_response.text = "Validation failed: Title can't be blank"
            mock_response.raise_for_status.side_effect = Exception("422 Unprocessable Entity")
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await adapter.publish(sample_content_item, platform_config)
            
            assert isinstance(result, PublishingResult)
            assert result.success is False
            assert result.platform == "dev.to"
            assert "422 Unprocessable Entity" in result.error_message

    @pytest.mark.asyncio
    async def test_devto_content_formatting(self, sample_content_item):
        """Test that content is properly formatted for Dev.to."""
        # This will fail - formatting method doesn't exist yet
        adapter = DevToAdapter()
        
        formatted_content = adapter._format_content_for_devto(sample_content_item)
        
        assert isinstance(formatted_content, str)
        assert sample_content_item.title in formatted_content
        assert sample_content_item.content in formatted_content
        # Dev.to uses markdown format
        assert formatted_content.startswith("# ")

    def test_devto_tag_filtering(self):
        """Test that tags are properly filtered for Dev.to (max 4 tags)."""
        # This will fail - tag filtering doesn't exist yet
        adapter = DevToAdapter()
        
        # Dev.to allows maximum 4 tags
        many_tags = ["python", "web", "api", "tutorial", "beginner", "advanced"]
        filtered_tags = adapter._filter_tags_for_devto(many_tags)
        
        assert len(filtered_tags) <= 4
        assert all(tag in many_tags for tag in filtered_tags)


@pytest.fixture
def sample_content_item():
    """Create a sample ContentItem for testing."""
    return ContentItem(
        id=1,
        title="How to Build a Multi-Platform Publishing Engine",
        content="This is a comprehensive guide on building a publishing engine that can distribute content across multiple platforms like Dev.to, LinkedIn, and more.",
        content_type="article",
        author_id="test_author",
        status="ready",
        content_metadata={
            "tags": ["python", "web", "api", "tutorial", "automation"],
            "description": "Learn to build a publishing engine"
        },
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )