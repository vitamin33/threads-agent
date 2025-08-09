"""Mock adapter for testing purposes."""

from typing import Dict, Any
from services.orchestrator.publishing.adapters.base import (
    PlatformAdapter,
    PublishingResult,
)
from services.orchestrator.db.models import ContentItem


class MockAdapter(PlatformAdapter):
    """Mock platform adapter for testing."""

    async def publish(
        self, content_item: ContentItem, platform_config: Dict[str, Any]
    ) -> PublishingResult:
        """Mock publish operation."""
        return PublishingResult(
            success=True,
            platform=self.platform_name,
            external_id="mock_12345",
            url=f"https://{self.platform_name}.com/mock/12345",
        )

    async def validate_content(
        self, content_item: ContentItem, platform_config: Dict[str, Any]
    ) -> bool:
        """Mock validation - always returns True."""
        return True

    @property
    def supports_retry(self) -> bool:
        """Mock adapter supports retry."""
        return True
