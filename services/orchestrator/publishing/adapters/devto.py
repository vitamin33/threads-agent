"""Dev.to platform adapter implementation."""

import httpx
from typing import Dict, Any, List
from services.orchestrator.publishing.adapters.base import PlatformAdapter, PublishingResult
from services.orchestrator.db.models import ContentItem


class DevToAdapter(PlatformAdapter):
    """Platform adapter for publishing to Dev.to."""
    
    def __init__(self):
        super().__init__("dev.to")
        self.api_base_url = "https://dev.to/api"
    
    async def publish(
        self, 
        content_item: ContentItem, 
        platform_config: Dict[str, Any]
    ) -> PublishingResult:
        """Publish content to Dev.to."""
        try:
            # Validate before publishing
            if not await self.validate_content(content_item, platform_config):
                return PublishingResult(
                    success=False,
                    platform=self.platform_name,
                    error_message="Content validation failed"
                )
            
            # Format content for Dev.to
            formatted_content = self._format_content_for_devto(content_item)
            
            # Prepare API payload
            payload = {
                "article": {
                    "title": content_item.title,
                    "body_markdown": formatted_content,
                    "published": True,
                    "tags": self._filter_tags_for_devto(
                        content_item.content_metadata.get("tags", []) if content_item.content_metadata else []
                    ),
                    "description": content_item.content_metadata.get("description", content_item.title) if content_item.content_metadata else content_item.title
                }
            }
            
            headers = {
                "api-key": platform_config["api_key"],
                "Content-Type": "application/json"
            }
            
            # Make API request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/articles",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                
                result_data = response.json()
                
                return PublishingResult(
                    success=True,
                    platform=self.platform_name,
                    external_id=str(result_data.get("id")),
                    url=result_data.get("url"),
                    metadata={"published_at": result_data.get("published_at")}
                )
                
        except Exception as e:
            return PublishingResult(
                success=False,
                platform=self.platform_name,
                error_message=str(e)
            )
    
    async def validate_content(
        self, 
        content_item: ContentItem, 
        platform_config: Dict[str, Any]
    ) -> bool:
        """Validate that content meets Dev.to requirements."""
        # Check API key
        if not platform_config.get("api_key"):
            return False
            
        # Check title
        if not content_item.title or content_item.title.strip() == "":
            return False
        
        # Check content
        if not content_item.content or content_item.content.strip() == "":
            return False
            
        return True
    
    @property
    def supports_retry(self) -> bool:
        """Dev.to adapter supports retry operations."""
        return True
    
    def _format_content_for_devto(self, content_item: ContentItem) -> str:
        """Format content for Dev.to markdown format."""
        formatted = f"# {content_item.title}\n\n"
        formatted += content_item.content
        
        # Add any additional formatting specific to Dev.to
        return formatted
    
    def _filter_tags_for_devto(self, tags: List[str]) -> List[str]:
        """Filter and limit tags for Dev.to (max 4 tags)."""
        # Dev.to allows maximum 4 tags
        return tags[:4] if tags else []