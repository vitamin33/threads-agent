"""Multi-platform analytics collectors for conversion tracking"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict


class BaseAnalyticsCollector(ABC):
    """Base abstract class for all analytics collectors"""

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return the platform name"""
        pass

    @abstractmethod
    async def get_metrics(self) -> Dict[str, Any]:
        """Get metrics for this platform"""
        pass

    @abstractmethod
    async def get_conversion_data(self) -> Dict[str, Any]:
        """Get conversion tracking data"""
        pass


class LinkedInAnalyticsCollector(BaseAnalyticsCollector):
    """LinkedIn analytics collector"""

    def __init__(self, profile_id: str):
        self.profile_id = profile_id

    @property
    def platform_name(self) -> str:
        return "linkedin"

    async def get_metrics(self) -> Dict[str, Any]:
        """Get LinkedIn metrics"""
        return {
            "profile_views": 0,
            "post_engagement": 0,
            "connection_requests": 0,
            "ai_hiring_manager_connections": 0,
            "platform": "linkedin",
            "collected_at": datetime.utcnow().isoformat(),
        }

    async def get_conversion_data(self) -> Dict[str, Any]:
        """Get LinkedIn conversion data"""
        return {
            "source_platform": "linkedin",
            "serbyn_pro_visits": 0,
            "job_inquiries": 0,
            "content_to_visit_conversion_rate": 0.0,
        }


class TwitterAnalyticsCollector(BaseAnalyticsCollector):
    """Twitter analytics collector"""

    def __init__(self, username: str):
        self.username = username

    @property
    def platform_name(self) -> str:
        return "twitter"

    async def get_metrics(self) -> Dict[str, Any]:
        """Get Twitter metrics"""
        return {
            "impressions": 0,
            "retweets": 0,
            "profile_visits": 0,
            "follower_growth": 0,
            "platform": "twitter",
            "collected_at": datetime.utcnow().isoformat(),
        }

    async def get_conversion_data(self) -> Dict[str, Any]:
        """Get Twitter conversion data"""
        return {
            "source_platform": "twitter",
            "serbyn_pro_visits": 0,
            "job_inquiries": 0,
            "content_to_visit_conversion_rate": 0.0,
        }


class MediumAnalyticsCollector(BaseAnalyticsCollector):
    """Medium analytics collector"""

    def __init__(self, username: str):
        self.username = username

    @property
    def platform_name(self) -> str:
        return "medium"

    async def get_metrics(self) -> Dict[str, Any]:
        """Get Medium metrics"""
        return {
            "read_ratio": 0.0,
            "claps": 0,
            "follower_conversion": 0,
            "profile_visits": 0,
            "platform": "medium",
            "collected_at": datetime.utcnow().isoformat(),
        }

    async def get_conversion_data(self) -> Dict[str, Any]:
        """Get Medium conversion data"""
        return {
            "source_platform": "medium",
            "serbyn_pro_visits": 0,
            "job_inquiries": 0,
            "content_to_visit_conversion_rate": 0.0,
        }


class GitHubAnalyticsCollector(BaseAnalyticsCollector):
    """GitHub analytics collector"""

    def __init__(self, username: str):
        self.username = username

    @property
    def platform_name(self) -> str:
        return "github"

    async def get_metrics(self) -> Dict[str, Any]:
        """Get GitHub metrics"""
        return {
            "profile_visits": 0,
            "repository_traffic": 0,
            "stars_from_content": 0,
            "platform": "github",
            "collected_at": datetime.utcnow().isoformat(),
        }

    async def get_conversion_data(self) -> Dict[str, Any]:
        """Get GitHub conversion data"""
        return {
            "source_platform": "github",
            "serbyn_pro_visits": 0,
            "job_inquiries": 0,
            "content_to_visit_conversion_rate": 0.0,
        }


class ThreadsAnalyticsCollector(BaseAnalyticsCollector):
    """Threads analytics collector"""

    def __init__(self, username: str):
        self.username = username

    @property
    def platform_name(self) -> str:
        return "threads"

    async def get_metrics(self) -> Dict[str, Any]:
        """Get Threads metrics"""
        return {
            "engagement_metrics": 0,
            "reach": 0,
            "conversation_starters": 0,
            "platform": "threads",
            "collected_at": datetime.utcnow().isoformat(),
        }

    async def get_conversion_data(self) -> Dict[str, Any]:
        """Get Threads conversion data"""
        return {
            "source_platform": "threads",
            "serbyn_pro_visits": 0,
            "job_inquiries": 0,
            "content_to_visit_conversion_rate": 0.0,
        }
