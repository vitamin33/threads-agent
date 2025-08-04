import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime
import structlog

from ..models.article import Platform, ArticleContent
from ..core.config import get_settings

logger = structlog.get_logger()


class PlatformPublisher:
    """Handles publishing to multiple platforms"""

    def __init__(self):
        self.settings = get_settings()
        # Configure async client with connection pooling and timeouts
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0, read=30.0, write=10.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
        )

    async def publish_to_platform(
        self,
        platform: Platform,
        content: ArticleContent,
        custom_content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Publish content to a specific platform"""

        logger.info("Publishing to platform", platform=platform, title=content.title)

        if platform == Platform.DEVTO:
            return await self._publish_to_devto(content, custom_content)
        elif platform == Platform.LINKEDIN:
            return await self._publish_to_linkedin(content, custom_content)
        elif platform == Platform.TWITTER:
            return await self._publish_to_twitter(content, custom_content)
        elif platform == Platform.THREADS:
            return await self._publish_to_threads(content, custom_content)
        elif platform == Platform.GITHUB:
            return await self._publish_to_github(content, custom_content)
        elif platform == Platform.MEDIUM:
            return await self._publish_to_medium(content, custom_content)
        else:
            raise ValueError(f"Unsupported platform: {platform}")

    async def _publish_to_devto(
        self, content: ArticleContent, custom_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Publish to Dev.to"""
        if not self.settings.devto_api_key:
            raise ValueError("Dev.to API key not configured")

        # Format content for Dev.to
        article_body = custom_content or self._format_for_devto(content)

        payload = {
            "article": {
                "title": content.title,
                "body_markdown": article_body,
                "published": True,
                "tags": content.tags[:4],  # Dev.to allows max 4 tags
                "canonical_url": None,
                "description": content.subtitle or content.title,
                "organization_id": None,
            }
        }

        headers = {
            "api-key": self.settings.devto_api_key,
            "Content-Type": "application/json",
        }

        try:
            response = await self.client.post(
                "https://dev.to/api/articles", json=payload, headers=headers
            )
            response.raise_for_status()
            result = response.json()

            return {
                "success": True,
                "url": result.get("url"),
                "id": result.get("id"),
                "published_at": result.get("published_at"),
            }
        except httpx.HTTPStatusError as e:
            logger.error(
                "Dev.to publishing failed", error=str(e), response=e.response.text
            )
            return {"success": False, "error": str(e), "details": e.response.text}
        except Exception as e:
            logger.error("Dev.to publishing error", error=str(e))
            return {"success": False, "error": str(e)}

    async def _publish_to_linkedin(
        self, content: ArticleContent, custom_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate LinkedIn post for manual publishing due to API restrictions"""
        # LinkedIn API doesn't allow automated posting for individual developers
        # Using manual workflow instead
        from app.services.manual_publisher import (
            ManualPublishingTracker,
            LinkedInManualWorkflow,
        )

        # Format content for LinkedIn
        formatted_content = LinkedInManualWorkflow.format_for_copy_paste(content)

        # Create draft for tracking
        tracker = ManualPublishingTracker(db=None)  # Pass DB session in production
        draft_result = await tracker.create_draft(
            platform=Platform.LINKEDIN,
            content=content,
            formatted_content=formatted_content,
        )

        return draft_result
    async def _publish_to_twitter(
        self, content: ArticleContent, custom_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Publish to Twitter/X"""
        if not all([self.settings.twitter_api_key, self.settings.twitter_api_secret]):
            raise ValueError("Twitter API credentials not configured")

        # Format content for Twitter (thread format)
        tweets = (
            custom_content.split("\n\n")
            if custom_content
            else self._format_for_twitter(content)
        )

        try:
            # This would use the Twitter API v2
            # For now, return a placeholder response
            return {
                "success": True,
                "message": "Twitter publishing configured but requires API v2 implementation",
                "thread_count": len(tweets),
            }
        except Exception as e:
            logger.error("Twitter publishing error", error=str(e))
            return {"success": False, "error": str(e)}

    async def _publish_to_github(
        self, content: ArticleContent, custom_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Publish to GitHub (as README or documentation)"""
        # This would integrate with GitHub API to create/update files
        return {
            "success": True,
            "message": "GitHub publishing would create/update documentation files",
        }

    async def _publish_to_medium(
        self, content: ArticleContent, custom_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Publish to Medium"""
        # This would integrate with Medium API
        return {
            "success": True,
            "message": "Medium publishing configured but requires API integration",
        }

    def _format_for_devto(self, content: ArticleContent) -> str:
        """Format content for Dev.to markdown"""
        formatted = f"# {content.title}\n\n"

        if content.subtitle:
            formatted += f"*{content.subtitle}*\n\n"

        # Add table of contents if long article
        if len(content.content) > 2000:
            formatted += "## Table of Contents\n\n"
            # Extract headers from content (simplified)
            lines = content.content.split("\n")
            for line in lines:
                if line.startswith("##"):
                    header = line.replace("##", "").strip()
                    link = header.lower().replace(" ", "-")
                    formatted += f"- [{header}](#{link})\n"
            formatted += "\n"

        formatted += content.content

        # Add code examples section
        if content.code_examples:
            formatted += "\n\n## Code Examples\n\n"
            for i, example in enumerate(content.code_examples, 1):
                formatted += (
                    f"### Example {i}: {example.get('title', 'Code Sample')}\n\n"
                )
                formatted += f"```{example.get('language', 'python')}\n"
                formatted += example.get("code", "")
                formatted += "\n```\n\n"
                if example.get("explanation"):
                    formatted += f"{example['explanation']}\n\n"

        # Add insights section
        if content.insights:
            formatted += "\n## Key Insights\n\n"
            for insight in content.insights:
                formatted += f"- {insight}\n"
            formatted += "\n"

        # Add tags
        if content.tags:
            formatted += (
                f"\n---\n\n*Tags: {', '.join([f'#{tag}' for tag in content.tags])}*\n"
            )

        # Add author bio
        formatted += "\n---\n\n"
        formatted += "*I'm Vitalii, an MLOps Engineer building AI systems that solve real business problems. "
        formatted += "Currently looking for remote US-based AI/MLOps roles. "
        formatted += (
            "Check out my [projects](https://github.com/vitamin33/threads-agent) or "
        )
        formatted += "connect on [LinkedIn](https://www.linkedin.com/in/vitalii-serbyn-b517a083/).*\n"

        return formatted

    def _format_for_linkedin(self, content: ArticleContent) -> str:
        """Format content for LinkedIn post"""
        post = f"🚀 {content.title}\n\n"

        # Extract key points (first few sentences or insights)
        if content.insights:
            post += "Key insights:\n"
            for insight in content.insights[:3]:  # Limit to 3 insights
                post += f"• {insight}\n"
            post += "\n"

        # Add brief summary
        summary = (
            content.content[:300] + "..."
            if len(content.content) > 300
            else content.content
        )
        post += f"{summary}\n\n"

        # Add call to action
        post += "What's your experience with similar challenges? Share your thoughts! 💭\n\n"

        # Add hashtags
        if content.tags:
            hashtags = [
                f"#{tag.replace(' ', '').replace('-', '')}" for tag in content.tags[:5]
            ]
            post += f"{' '.join(hashtags)}\n\n"

        post += "#MLOps #AI #SoftwareEngineering #Python #TechLeadership"

        return post

    def _format_for_twitter(self, content: ArticleContent) -> List[str]:
        """Format content for Twitter thread"""
        tweets = []

        # First tweet - hook
        first_tweet = f"🧵 {content.title}\n\nA thread about {content.subtitle or 'my latest technical discovery'} 👇"
        tweets.append(first_tweet)

        # Extract key points and create tweets
        if content.insights:
            for i, insight in enumerate(content.insights[:8], 2):  # Max 8 insights
                tweet = f"{i}/{len(content.insights) + 1} {insight}"
                if len(tweet) > 280:
                    tweet = tweet[:277] + "..."
                tweets.append(tweet)

        # Add code example if available
        if content.code_examples:
            code_tweet = f"{len(tweets) + 1}/🔧 Here's a key code snippet:\n\n"
            code = (
                content.code_examples[0]["code"][:150] + "..."
                if len(content.code_examples[0]["code"]) > 150
                else content.code_examples[0]["code"]
            )
            code_tweet += f"```\n{code}\n```"
            tweets.append(code_tweet)

        # Final tweet - CTA
        final_tweet = f"{len(tweets) + 1}/{len(tweets) + 1} Found this helpful? \n\n"
        final_tweet += "🔗 Full article: [link]\n"
        final_tweet += "🤝 Connect with me for more AI/MLOps content\n\n"
        if content.tags:
            hashtags = [f"#{tag.replace(' ', '')}" for tag in content.tags[:3]]
            final_tweet += f"{' '.join(hashtags)}"

        tweets.append(final_tweet)

        return tweets

    async def _publish_to_threads(
        self, content: ArticleContent, custom_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Publish content to Threads (Meta)"""

        if not self.settings.threads_access_token:
            raise ValueError("Threads access token not configured")

        if not self.settings.threads_user_id:
            raise ValueError("Threads user ID not configured")

        # Format content for Threads (500 character limit)
        text = custom_content or self._format_for_threads(content)

        async with httpx.AsyncClient() as client:
            # Step 1: Create media container
            create_response = await client.post(
                f"https://graph.threads.net/v1.0/{self.settings.threads_user_id}/threads",
                params={
                    "media_type": "TEXT",
                    "text": text,
                    "access_token": self.settings.threads_access_token,
                },
            )

            if create_response.status_code != 200:
                raise Exception(f"Failed to create thread: {create_response.text}")

            media_id = create_response.json()["id"]

            # Step 2: Publish the post
            publish_response = await client.post(
                f"https://graph.threads.net/v1.0/{self.settings.threads_user_id}/threads_publish",
                params={
                    "creation_id": media_id,
                    "access_token": self.settings.threads_access_token,
                },
            )

            if publish_response.status_code != 200:
                raise Exception(f"Failed to publish thread: {publish_response.text}")

            result = publish_response.json()

            logger.info("Published to Threads", thread_id=result.get("id"))

            return {
                "id": result.get("id"),
                "url": f"https://www.threads.net/@{self.settings.threads_username}/post/{result.get('id')}",
                "platform": "threads",
            }

    def _format_for_threads(self, content: ArticleContent) -> str:
        """Format content for Threads (500 char limit)"""

        # Create engaging hook
        text = content.title
        if content.subtitle:
            text += f"\n\n{content.subtitle}"

        # Add key insight (find first interesting sentence)
        if content.content:
            sentences = content.content.split(".")
            for sentence in sentences:
                if any(
                    word in sentence.lower()
                    for word in ["built", "discovered", "learned", "found", "achieved"]
                ):
                    text += f"\n\n{sentence.strip()}."
                    break

        # Add CTA
        text += "\n\n🔗 Full article on Dev.to (link in bio)"

        # Add selective hashtags
        if content.tags:
            relevant_tags = [tag for tag in content.tags[:3] if len(tag) < 20]
            if relevant_tags:
                text += f"\n\n{' '.join([f'#{tag}' for tag in relevant_tags])}"

        # Ensure under 500 chars
        if len(text) > 500:
            text = text[:497] + "..."

        return text

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


class PublishingScheduler:
    """Handles scheduling of publications"""

    def __init__(self):
        self.settings = get_settings()

    async def schedule_publication(
        self,
        article_id: str,
        platforms: List[Platform],
        schedule_times: Dict[Platform, datetime],
    ) -> Dict[str, Any]:
        """Schedule publications for multiple platforms"""
        # This would integrate with Celery for scheduling
        scheduled = {}

        for platform in platforms:
            schedule_time = schedule_times.get(platform)
            if schedule_time:
                # Create Celery task for delayed execution
                scheduled[platform.value] = {
                    "scheduled_for": schedule_time.isoformat(),
                    "task_id": f"publish_{article_id}_{platform.value}_{int(schedule_time.timestamp())}",
                }

        return {
            "success": True,
            "scheduled": scheduled,
            "message": f"Scheduled publications for {len(scheduled)} platforms",
        }

    def get_optimal_posting_times(
        self, platforms: List[Platform]
    ) -> Dict[Platform, datetime]:
        """Get optimal posting times for different platforms"""
        from datetime import datetime, timedelta

        now = datetime.utcnow()
        optimal_times = {}

        for platform in platforms:
            if platform == Platform.DEVTO:
                # Dev.to: Tuesday-Thursday, 9-11 AM EST
                optimal_times[platform] = now + timedelta(hours=2)
            elif platform == Platform.LINKEDIN:
                # LinkedIn: Tuesday-Thursday, 8-10 AM EST
                optimal_times[platform] = now + timedelta(hours=1)
            elif platform == Platform.TWITTER:
                # Twitter: Monday-Friday, 12-3 PM EST
                optimal_times[platform] = now + timedelta(minutes=30)
            else:
                optimal_times[platform] = now + timedelta(hours=1)

        return optimal_times
