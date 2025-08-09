"""LinkedIn platform adapter implementation.

Since LinkedIn's API doesn't allow automated posting for individual developers,
this adapter creates formatted content drafts for manual publishing.
"""

import re
from typing import Dict, Any, List
from services.orchestrator.publishing.adapters.base import (
    PlatformAdapter,
    PublishingResult,
)
from services.orchestrator.db.models import ContentItem


class LinkedInAdapter(PlatformAdapter):
    """Platform adapter for LinkedIn manual publishing workflow."""

    def __init__(self):
        super().__init__("linkedin")
        self.max_content_length = 3000  # LinkedIn character limit

    async def publish(
        self, content_item: ContentItem, platform_config: Dict[str, Any]
    ) -> PublishingResult:
        """Create formatted content draft for manual LinkedIn publishing."""
        try:
            # Validate before processing
            if not await self.validate_content(content_item, platform_config):
                return PublishingResult(
                    success=False,
                    platform=self.platform_name,
                    error_message="Content validation failed",
                )

            # Format content for LinkedIn
            formatted_content = self._format_content_for_linkedin(content_item)

            # Create draft result
            return PublishingResult(
                success=True,
                platform=self.platform_name,
                external_id=f"draft_{content_item.id}",
                url=None,  # No URL until manually posted
                metadata={
                    "draft": True,
                    "formatted_content": formatted_content,
                    "manual_posting_required": True,
                    "instructions": "Copy the formatted content and post manually on LinkedIn",
                },
            )

        except Exception as e:
            return PublishingResult(
                success=False, platform=self.platform_name, error_message=str(e)
            )

    async def validate_content(
        self, content_item: ContentItem, platform_config: Dict[str, Any]
    ) -> bool:
        """Validate that content meets LinkedIn requirements."""
        # Check title
        if not content_item.title or content_item.title.strip() == "":
            return False

        # Check content
        if not content_item.content or content_item.content.strip() == "":
            return False

        # Check total length (title + content should be under LinkedIn limit)
        total_content = f"{content_item.title}\n\n{content_item.content}"
        if len(total_content) > self.max_content_length:
            return False

        return True

    @property
    def supports_retry(self) -> bool:
        """LinkedIn manual publishing doesn't support automatic retry."""
        return False

    def _format_content_for_linkedin(self, content_item: ContentItem) -> str:
        """Format content for LinkedIn professional posting."""
        # Start with engaging hook
        formatted = f"🚀 {content_item.title}\n\n"

        # Optimize content length
        content_to_use = self._optimize_content_length(
            title=content_item.title,
            content=content_item.content,
            max_length=self.max_content_length,
        )

        formatted += content_to_use

        # Add call to action
        formatted += "\n\nWhat's your experience with similar challenges? Share your thoughts! 💭\n\n"

        # Add hashtags
        if content_item.content_metadata and content_item.content_metadata.get("tags"):
            hashtags = self._format_hashtags_for_linkedin(
                content_item.content_metadata["tags"]
            )
            formatted += " ".join(hashtags)

        # Ensure we're under the character limit
        if len(formatted) > self.max_content_length:
            formatted = formatted[: self.max_content_length - 3] + "..."

        return formatted

    def _format_hashtags_for_linkedin(self, tags: List[str]) -> List[str]:
        """Format hashtags for LinkedIn (remove spaces, special chars, limit count)."""
        formatted_hashtags = []

        for tag in tags[:7]:  # Limit to 7 hashtags for professional appearance
            # Remove spaces and special characters, convert to camelCase
            clean_tag = re.sub(r"[^a-zA-Z0-9]", "", tag)
            if clean_tag:
                formatted_hashtags.append(f"#{clean_tag.lower()}")

        return formatted_hashtags

    def _optimize_content_length(
        self, title: str, content: str, max_length: int
    ) -> str:
        """Optimize content length for LinkedIn while preserving meaning."""
        # Reserve space for title, CTAs, and hashtags
        reserved_space = len(title) + 200  # Approximate space for formatting
        available_space = max_length - reserved_space

        if len(content) <= available_space:
            return content

        # Truncate at sentence boundary if possible
        truncated = content[: available_space - 3]

        # Try to end at a sentence
        last_period = truncated.rfind(".")
        last_exclamation = truncated.rfind("!")
        last_question = truncated.rfind("?")

        last_sentence_end = max(last_period, last_exclamation, last_question)

        if (
            last_sentence_end > available_space * 0.7
        ):  # If we can preserve at least 70% of content
            truncated = truncated[: last_sentence_end + 1]

        # Always add ... if we truncated the content
        if len(content) > available_space:
            if not truncated.endswith("..."):
                truncated = truncated + "..."

        return truncated
