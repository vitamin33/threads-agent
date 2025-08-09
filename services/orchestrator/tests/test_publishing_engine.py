"""
Tests for Multi-Platform Publishing Engine MVP.

This module tests the core publishing engine functionality including:
- Platform adapter interfaces
- Async publishing with Celery
- Retry mechanisms and error handling
- Status tracking and updates
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch

from services.orchestrator.publishing.engine import PublishingEngine
from services.orchestrator.publishing.adapters.base import (
    PublishingResult,
)
from services.orchestrator.db.models import ContentItem


class TestPublishingEngine:
    """Test the core Publishing Engine functionality."""

    def test_publishing_engine_initialization(self):
        """Test that PublishingEngine initializes with platform adapters."""
        # This will fail - PublishingEngine doesn't exist yet
        engine = PublishingEngine()

        assert engine is not None
        assert hasattr(engine, "adapters")
        assert len(engine.adapters) > 0

    def test_platform_adapter_interface_exists(self):
        """Test that PlatformAdapter base class defines required interface."""
        # Test with MockAdapter which implements the interface
        from services.orchestrator.publishing.adapters.mock import MockAdapter

        adapter = MockAdapter("test_platform")

        assert adapter.platform_name == "test_platform"
        assert hasattr(adapter, "publish")
        assert hasattr(adapter, "validate_content")
        assert hasattr(adapter, "supports_retry")

    @pytest.mark.asyncio
    async def test_publishing_result_structure(self):
        """Test that PublishingResult contains required fields."""
        # This will fail - PublishingResult doesn't exist yet
        result = PublishingResult(
            success=True,
            platform="dev.to",
            external_id="12345",
            url="https://dev.to/article/12345",
        )

        assert result.success is True
        assert result.platform == "dev.to"
        assert result.external_id == "12345"
        assert result.url == "https://dev.to/article/12345"
        assert result.error_message is None

    @pytest.mark.asyncio
    async def test_engine_publishes_to_single_platform(self, sample_content_item):
        """Test that engine can publish content to a single platform."""
        # This will fail - methods don't exist yet
        engine = PublishingEngine()

        result = await engine.publish_to_platform(
            content_item=sample_content_item,
            platform="dev.to",
            platform_config={"api_key": "test_key"},
        )

        assert isinstance(result, PublishingResult)
        assert result.platform == "dev.to"

    @pytest.mark.asyncio
    async def test_engine_handles_publishing_failure(self, sample_content_item):
        """Test that engine properly handles publishing failures."""
        # This will fail - error handling doesn't exist yet
        engine = PublishingEngine()

        # Mock adapter to raise an exception
        with patch.object(engine, "_get_adapter") as mock_get_adapter:
            mock_adapter = Mock()
            mock_adapter.publish = AsyncMock(side_effect=Exception("API Error"))
            mock_get_adapter.return_value = mock_adapter

            result = await engine.publish_to_platform(
                content_item=sample_content_item,
                platform="dev.to",
                platform_config={"api_key": "test_key"},
            )

            assert result.success is False
            assert "API Error" in result.error_message


@pytest.fixture
def sample_content_item():
    """Create a sample ContentItem for testing."""
    return ContentItem(
        id=1,
        title="Test Article",
        content="This is test content for publishing",
        content_type="article",
        author_id="test_author",
        status="ready",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
