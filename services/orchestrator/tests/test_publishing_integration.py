"""
Integration tests for the Multi-Platform Publishing Engine.

This module tests the complete publishing workflow from ContentSchedule
creation through to successful publication across multiple platforms.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone, timedelta

from services.orchestrator.publishing.engine import PublishingEngine
from services.orchestrator.publishing.tasks import publish_content_task, publish_scheduled_content_task
from services.orchestrator.db.models import ContentItem, ContentSchedule


class TestPublishingIntegration:
    """Test end-to-end publishing workflows."""

    @pytest.mark.asyncio
    async def test_end_to_end_devto_publishing(self):
        """Test complete DevTo publishing workflow."""
        # Create content item
        content_item = ContentItem(
            id=1,
            title="How to Build AI Systems at Scale",
            content="In this comprehensive guide, we'll explore the key principles and practices for building robust AI systems that can handle production workloads.",
            content_type="article",
            author_id="test_author",
            status="ready",
            content_metadata={
                "tags": ["ai", "machine-learning", "scalability", "production"],
                "description": "A guide to scalable AI systems"
            }
        )
        
        # Initialize publishing engine
        engine = PublishingEngine()
        
        # Verify DevTo adapter is registered
        assert "dev.to" in engine.adapters
        assert engine.adapters["dev.to"].platform_name == "dev.to"
        
        # Test content validation
        devto_adapter = engine.adapters["dev.to"]
        platform_config = {"api_key": "test_api_key"}
        
        is_valid = await devto_adapter.validate_content(content_item, platform_config)
        assert is_valid is True
        
        # Test content formatting
        formatted_content = devto_adapter._format_content_for_devto(content_item)
        assert isinstance(formatted_content, str)
        assert content_item.title in formatted_content
        assert formatted_content.startswith("# ")
        
        # Test tag filtering
        filtered_tags = devto_adapter._filter_tags_for_devto(content_item.content_metadata["tags"])
        assert len(filtered_tags) <= 4
        assert filtered_tags == ["ai", "machine-learning", "scalability", "production"]

    @pytest.mark.asyncio
    async def test_end_to_end_linkedin_publishing(self):
        """Test complete LinkedIn publishing workflow."""
        # Create content item
        content_item = ContentItem(
            id=2,
            title="5 Lessons from Building Production AI Pipelines",
            content="After building AI systems that serve millions of requests daily, here are the key insights that made the difference between proof-of-concept and production success.",
            content_type="post",
            author_id="test_author",
            status="ready",
            content_metadata={
                "tags": ["ai", "production", "lessons learned", "engineering", "scale"]
            }
        )
        
        # Initialize publishing engine
        engine = PublishingEngine()
        
        # Verify LinkedIn adapter is registered
        assert "linkedin" in engine.adapters
        assert engine.adapters["linkedin"].platform_name == "linkedin"
        
        # Test content validation
        linkedin_adapter = engine.adapters["linkedin"]
        platform_config = {}  # LinkedIn doesn't need API key for manual publishing
        
        is_valid = await linkedin_adapter.validate_content(content_item, platform_config)
        assert is_valid is True
        
        # Test content formatting
        formatted_content = linkedin_adapter._format_content_for_linkedin(content_item)
        assert isinstance(formatted_content, str)
        assert len(formatted_content) <= 3000  # LinkedIn limit
        assert "🚀" in formatted_content  # Should have engaging emoji
        assert "What's your experience" in formatted_content  # Should have CTA
        assert "#ai" in formatted_content  # Should have hashtags
        
        # Test hashtag formatting
        hashtags = linkedin_adapter._format_hashtags_for_linkedin(content_item.content_metadata["tags"])
        assert "#ai" in hashtags
        assert "#production" in hashtags
        assert "#lessonslearned" in hashtags  # Should remove spaces

    @patch('services.orchestrator.publishing.tasks.get_db_session')
    @patch('httpx.AsyncClient')
    def test_devto_publishing_task_integration(self, mock_httpx, mock_get_db):
        """Test DevTo publishing through Celery task."""
        # Mock database session and schedule
        mock_db = Mock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        
        # Create mock content schedule
        content_item = ContentItem(
            id=1,
            title="Test Article",
            content="Test content for DevTo publishing",
            content_type="article",
            author_id="test_author",
            status="ready",
            content_metadata={"tags": ["test", "tutorial"]}
        )
        
        schedule = ContentSchedule(
            id=1,
            content_item_id=1,
            platform="dev.to",
            scheduled_time=datetime.now(timezone.utc),
            status="scheduled",
            platform_config={"api_key": "test_key"},
            retry_count=0,
            max_retries=3
        )
        schedule.content_item = content_item
        
        mock_db.query.return_value.filter.return_value.first.return_value = schedule
        
        # Mock successful DevTo API response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 12345,
            "url": "https://dev.to/test/article-12345",
            "published_at": "2024-01-01T00:00:00Z"
        }
        mock_response.raise_for_status.return_value = None
        
        mock_httpx.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        # Execute publishing task
        result = publish_content_task(schedule_id=1)
        
        # Verify successful publication
        assert result["success"] is True
        assert result["platform"] == "dev.to"
        assert result["external_id"] == "12345"
        assert result["url"] == "https://dev.to/test/article-12345"
        
        # Verify schedule was updated
        assert schedule.status == "published"
        assert schedule.published_at is not None
        mock_db.commit.assert_called_once()

    @patch('services.orchestrator.publishing.tasks.get_db_session')
    def test_linkedin_publishing_task_integration(self, mock_get_db):
        """Test LinkedIn publishing through Celery task."""
        # Mock database session and schedule
        mock_db = Mock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        
        # Create mock content schedule
        content_item = ContentItem(
            id=2,
            title="Professional LinkedIn Post",
            content="This is professional content formatted for LinkedIn sharing.",
            content_type="post",
            author_id="test_author",
            status="ready",
            content_metadata={"tags": ["professional", "networking", "career"]}
        )
        
        schedule = ContentSchedule(
            id=2,
            content_item_id=2,
            platform="linkedin",
            scheduled_time=datetime.now(timezone.utc),
            status="scheduled",
            platform_config={},  # No API key needed
            retry_count=0,
            max_retries=3
        )
        schedule.content_item = content_item
        
        mock_db.query.return_value.filter.return_value.first.return_value = schedule
        
        # Execute publishing task
        result = publish_content_task(schedule_id=2)
        
        # Verify successful draft creation
        assert result["success"] is True
        assert result["platform"] == "linkedin"
        assert result["external_id"] == "draft_2"
        
        # Verify schedule was updated (LinkedIn is "published" as draft)
        assert schedule.status == "published"
        assert schedule.published_at is not None
        mock_db.commit.assert_called_once()

    @patch('services.orchestrator.publishing.tasks.get_db_session')
    @patch('services.orchestrator.publishing.tasks.publish_content_task.delay')
    def test_scheduled_content_processing_integration(self, mock_delay, mock_get_db):
        """Test that scheduled content processing finds and queues content correctly."""
        # Mock database session
        mock_db = Mock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        
        # Create overdue schedules
        now = datetime.now(timezone.utc)
        
        schedule1 = Mock()
        schedule1.id = 1
        schedule1.scheduled_time = now - timedelta(minutes=10)  # 10 minutes overdue
        schedule1.status = "scheduled"
        
        schedule2 = Mock()
        schedule2.id = 2
        schedule2.scheduled_time = now - timedelta(minutes=5)   # 5 minutes overdue
        schedule2.status = "scheduled"
        
        schedule3 = Mock()
        schedule3.id = 3
        schedule3.scheduled_time = now + timedelta(minutes=30)  # Future - shouldn't be processed
        schedule3.status = "scheduled"
        
        # Only return overdue schedules
        mock_db.query.return_value.filter.return_value.all.return_value = [schedule1, schedule2]
        
        # Execute scheduled content task
        result = publish_scheduled_content_task()
        
        # Verify results
        assert result["processed_count"] == 2
        assert result["scheduled_count"] == 2
        
        # Verify individual publishing tasks were scheduled
        assert mock_delay.call_count == 2
        mock_delay.assert_any_call(schedule_id=1)
        mock_delay.assert_any_call(schedule_id=2)

    def test_adapter_interface_compatibility(self):
        """Test that all adapters implement the required interface correctly."""
        engine = PublishingEngine()
        
        # Test all registered adapters
        for platform_name, adapter in engine.adapters.items():
            # Check required attributes
            assert hasattr(adapter, 'platform_name')
            assert hasattr(adapter, 'publish')
            assert hasattr(adapter, 'validate_content')
            assert hasattr(adapter, 'supports_retry')
            
            # Check platform name matches
            assert adapter.platform_name == platform_name
            
            # Check supports_retry returns boolean
            assert isinstance(adapter.supports_retry, bool)

    def test_engine_error_handling_robustness(self):
        """Test that the engine handles various error conditions gracefully."""
        engine = PublishingEngine()
        
        # Verify we have the expected number of adapters initially
        expected_platforms = {"dev.to", "linkedin", "twitter", "threads", "medium"}
        assert set(engine.adapters.keys()) == expected_platforms
        
        # Test getting non-existent adapter (this will add it to the registry)
        unknown_adapter = engine._get_adapter("unknown_platform")
        assert unknown_adapter is not None
        assert unknown_adapter.platform_name == "unknown_platform"
        
        # Now we should have one more adapter
        assert len(engine.adapters) == 6