"""Dev.to engagement metrics collector"""

import httpx
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


class DevToMetricsCollector:
    """Collect engagement metrics from dev.to articles"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://dev.to/api"

    async def get_article_metrics(self, article_url: str) -> Dict[str, Any]:
        """Get metrics for a specific dev.to article"""

        # Extract article ID from URL
        article_id = self._extract_article_id(article_url)
        if not article_id:
            raise ValueError(f"Could not extract article ID from URL: {article_url}")

        try:
            async with httpx.AsyncClient() as client:
                # Get article details
                response = await client.get(
                    f"{self.base_url}/articles/{article_id}",
                    headers=self._get_headers(),
                )

                if response.status_code == 200:
                    article_data = response.json()

                    metrics = {
                        "article_id": article_id,
                        "title": article_data.get("title", ""),
                        "published_at": article_data.get("published_at", ""),
                        "url": article_data.get("url", ""),
                        "tags": article_data.get("tag_list", []),
                        "reading_time_minutes": article_data.get(
                            "reading_time_minutes", 0
                        ),
                        "public_reactions_count": article_data.get(
                            "public_reactions_count", 0
                        ),
                        "comments_count": article_data.get("comments_count", 0),
                        "page_views_count": article_data.get("page_views_count", 0),
                        "positive_reactions_count": article_data.get(
                            "positive_reactions_count", 0
                        ),
                        "social_image": article_data.get("social_image", ""),
                        "collected_at": datetime.utcnow().isoformat(),
                    }

                    # Calculate engagement rate
                    if metrics["page_views_count"] > 0:
                        total_engagements = (
                            metrics["public_reactions_count"]
                            + metrics["comments_count"]
                        )
                        metrics["engagement_rate"] = (
                            total_engagements / metrics["page_views_count"]
                        ) * 100
                    else:
                        metrics["engagement_rate"] = 0.0

                    logger.info(
                        "devto_metrics_collected",
                        article_id=article_id,
                        views=metrics["page_views_count"],
                        reactions=metrics["public_reactions_count"],
                        comments=metrics["comments_count"],
                        engagement_rate=metrics["engagement_rate"],
                    )

                    return metrics

                else:
                    logger.error(
                        "devto_api_error",
                        status_code=response.status_code,
                        article_id=article_id,
                    )
                    return {"error": f"API returned status {response.status_code}"}

        except Exception as e:
            logger.error(
                "devto_collection_failed", article_url=article_url, error=str(e)
            )
            return {"error": str(e)}

    async def get_user_articles_metrics(
        self, username: str, days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """Get metrics for all user's articles in the last N days"""

        try:
            async with httpx.AsyncClient() as client:
                # Get user's articles
                response = await client.get(
                    f"{self.base_url}/articles",
                    params={"username": username, "per_page": 30},
                    headers=self._get_headers(),
                )

                if response.status_code == 200:
                    articles = response.json()
                    cutoff_date = datetime.utcnow() - timedelta(days=days_back)

                    metrics_list = []

                    for article in articles:
                        published_at = datetime.fromisoformat(
                            article.get("published_at", "").replace("Z", "+00:00")
                        )

                        if published_at >= cutoff_date:
                            # Get detailed metrics for each recent article
                            article_metrics = await self.get_article_metrics(
                                article["url"]
                            )
                            if "error" not in article_metrics:
                                metrics_list.append(article_metrics)

                            # Rate limiting - be nice to dev.to API
                            await asyncio.sleep(0.5)

                    return metrics_list

                else:
                    logger.error(
                        "devto_user_articles_error",
                        status_code=response.status_code,
                        username=username,
                    )
                    return []

        except Exception as e:
            logger.error(
                "devto_user_collection_failed", username=username, error=str(e)
            )
            return []

    def _extract_article_id(self, article_url: str) -> Optional[str]:
        """Extract article ID from dev.to URL"""

        # dev.to URLs can be in format:
        # https://dev.to/username/article-title-slug-1234
        # The ID is usually the last part after the final dash

        try:
            # Remove trailing slash
            url = article_url.rstrip("/")

            # Split by dashes and get the last part
            parts = url.split("-")

            # The last part should be numeric ID
            if parts[-1].isdigit():
                return parts[-1]

            # Alternative: extract from URL path
            if "/articles/" in url:
                path_part = url.split("/articles/")[-1]
                return path_part

            return None

        except Exception:
            return None

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for dev.to API requests"""

        headers = {
            "User-Agent": "ThreadsAgent/1.0 (Achievement Collector)",
            "Accept": "application/vnd.forem.api-v1+json",
        }

        if self.api_key:
            headers["api-key"] = self.api_key

        return headers


class DevToAchievementIntegration:
    """Integration between dev.to metrics and achievement system"""

    def __init__(self, devto_collector: DevToMetricsCollector):
        self.devto_collector = devto_collector

    async def sync_article_achievement(
        self, article_url: str, achievement_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Sync dev.to article metrics with achievement record"""

        # Get current metrics
        metrics = await self.devto_collector.get_article_metrics(article_url)

        if "error" in metrics:
            return {"success": False, "error": metrics["error"]}

        # Update achievement with latest metrics
        achievement_update = {
            "evidence": {
                "devto_metrics": metrics,
                "last_synced": datetime.utcnow().isoformat(),
            },
            "performance_improvement_pct": metrics.get("engagement_rate", 0),
            "time_saved_hours": metrics.get("reading_time_minutes", 0)
            / 60,  # Convert to hours
        }

        # Calculate dynamic business value based on engagement
        views = metrics.get("page_views_count", 0)
        engagement_rate = metrics.get("engagement_rate", 0)

        if views > 1000 and engagement_rate > 3:
            business_value = f"High-impact technical content: {views} views, {engagement_rate:.1f}% engagement"
        elif views > 500:
            business_value = f"Medium-impact technical content: {views} views"
        else:
            business_value = f"Technical content creation: {views} views"

        achievement_update["business_value"] = business_value

        logger.info(
            "devto_achievement_synced",
            achievement_id=achievement_id,
            views=views,
            engagement_rate=engagement_rate,
            business_value=business_value,
        )

        return {
            "success": True,
            "metrics": metrics,
            "achievement_update": achievement_update,
        }


# Example usage function
async def track_devto_article_example():
    """Example of how to track a dev.to article"""

    collector = DevToMetricsCollector()  # Add API key if available
    integration = DevToAchievementIntegration(collector)

    # Track specific article
    article_url = "https://dev.to/yourusername/your-article-slug-1234"
    result = await integration.sync_article_achievement(article_url)

    if result["success"]:
        print("✅ Article metrics synced successfully")
        print(f"Views: {result['metrics']['page_views_count']}")
        print(f"Reactions: {result['metrics']['public_reactions_count']}")
        print(f"Engagement: {result['metrics']['engagement_rate']:.1f}%")
    else:
        print(f"❌ Failed to sync: {result['error']}")


if __name__ == "__main__":
    asyncio.run(track_devto_article_example())
