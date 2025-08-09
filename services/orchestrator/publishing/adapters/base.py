"""Base platform adapter interface and result structures."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any
from services.orchestrator.db.models import ContentItem


@dataclass
class PublishingResult:
    """Result of a publishing operation to a platform."""

    success: bool
    platform: str
    external_id: Optional[str] = None
    url: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PlatformAdapter(ABC):
    """Base interface for all platform adapters."""

    def __init__(self, platform_name: str):
        self.platform_name = platform_name

    @abstractmethod
    async def publish(
        self, content_item: ContentItem, platform_config: Dict[str, Any]
    ) -> PublishingResult:
        """Publish content to the platform."""
        pass

    @abstractmethod
    async def validate_content(
        self, content_item: ContentItem, platform_config: Dict[str, Any]
    ) -> bool:
        """Validate that content meets platform requirements."""
        pass

    @property
    @abstractmethod
    def supports_retry(self) -> bool:
        """Whether this adapter supports retry operations."""
        pass
