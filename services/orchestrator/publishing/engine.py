"""Core Publishing Engine for multi-platform content distribution."""

from typing import Dict, List, Optional
from services.orchestrator.publishing.adapters.base import PlatformAdapter, PublishingResult
from services.orchestrator.db.models import ContentItem


class PublishingEngine:
    """Main engine for publishing content across multiple platforms."""
    
    def __init__(self):
        self.adapters: Dict[str, PlatformAdapter] = {}
        self._register_default_adapters()
    
    def _register_default_adapters(self):
        """Register default platform adapters."""
        # Register real adapters for MVP Phase 1
        from services.orchestrator.publishing.adapters.devto import DevToAdapter
        from services.orchestrator.publishing.adapters.linkedin import LinkedInAdapter
        from services.orchestrator.publishing.adapters.mock import MockAdapter
        
        # MVP Phase 1: Real implementations
        self.adapters["dev.to"] = DevToAdapter()
        self.adapters["linkedin"] = LinkedInAdapter()
        
        # Mock implementations for other platforms
        mock_platforms = ["twitter", "threads", "medium"]
        for platform in mock_platforms:
            self.adapters[platform] = MockAdapter(platform)
    
    async def publish_to_platform(
        self,
        content_item: ContentItem,
        platform: str,
        platform_config: Dict[str, str]
    ) -> PublishingResult:
        """Publish content to a specific platform."""
        adapter = self._get_adapter(platform)
        
        try:
            result = await adapter.publish(content_item, platform_config)
            return result
        except Exception as e:
            return PublishingResult(
                success=False,
                platform=platform,
                error_message=str(e)
            )
    
    def _get_adapter(self, platform: str) -> PlatformAdapter:
        """Get the adapter for a specific platform."""
        if platform not in self.adapters:
            # For now, create a mock adapter
            from services.orchestrator.publishing.adapters.mock import MockAdapter
            self.adapters[platform] = MockAdapter(platform)
        
        return self.adapters[platform]