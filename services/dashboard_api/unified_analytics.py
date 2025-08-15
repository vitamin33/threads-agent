"""Unified analytics dashboard that aggregates all platform metrics"""

from datetime import datetime
from typing import Any, Dict, List
import httpx


class AnalyticsAggregationService:
    """Service to aggregate analytics from all platforms"""

    def __init__(self):
        self.tech_doc_generator_url = "http://tech-doc-generator:8000"

    async def collect_all_platform_metrics(self) -> Dict[str, Any]:
        """Collect metrics from all platforms"""
        # For now, return mock data - will be enhanced to call actual collectors
        return {
            "linkedin": {
                "metrics": {"profile_views": 0, "post_engagement": 0},
                "conversion_data": {"serbyn_pro_visits": 0, "job_inquiries": 0},
                "collected_at": datetime.utcnow().isoformat(),
            },
            "twitter": {
                "metrics": {"impressions": 0, "retweets": 0},
                "conversion_data": {"serbyn_pro_visits": 0, "job_inquiries": 0},
                "collected_at": datetime.utcnow().isoformat(),
            },
            "medium": {
                "metrics": {"read_ratio": 0.0, "claps": 0},
                "conversion_data": {"serbyn_pro_visits": 0, "job_inquiries": 0},
                "collected_at": datetime.utcnow().isoformat(),
            },
            "github": {
                "metrics": {"profile_visits": 0, "repository_traffic": 0},
                "conversion_data": {"serbyn_pro_visits": 0, "job_inquiries": 0},
                "collected_at": datetime.utcnow().isoformat(),
            },
            "threads": {
                "metrics": {"engagement_metrics": 0, "reach": 0},
                "conversion_data": {"serbyn_pro_visits": 0, "job_inquiries": 0},
                "collected_at": datetime.utcnow().isoformat(),
            },
            "devto": {
                "metrics": {"page_views_count": 0, "public_reactions_count": 0},
                "conversion_data": {"serbyn_pro_visits": 0, "job_inquiries": 0},
                "collected_at": datetime.utcnow().isoformat(),
            },
        }

    async def calculate_conversion_summary(self, platform_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate aggregated conversion summary"""
        total_visits = 0
        total_inquiries = 0
        
        for platform, data in platform_metrics.items():
            conversion_data = data.get("conversion_data", {})
            total_visits += conversion_data.get("serbyn_pro_visits", 0)
            total_inquiries += conversion_data.get("job_inquiries", 0)
        
        overall_conversion_rate = (total_inquiries / total_visits * 100) if total_visits > 0 else 0.0
        
        return {
            "total_serbyn_pro_visits": total_visits,
            "total_job_inquiries": total_inquiries,
            "overall_conversion_rate": overall_conversion_rate,
            "best_converting_platform": await self.identify_best_platform(platform_metrics),
            "platform_breakdown": {
                platform: {
                    "serbyn_pro_visits": data.get("conversion_data", {}).get("serbyn_pro_visits", 0),
                    "job_inquiries": data.get("conversion_data", {}).get("job_inquiries", 0),
                    "conversion_rate": (
                        data.get("conversion_data", {}).get("job_inquiries", 0) /
                        data.get("conversion_data", {}).get("serbyn_pro_visits", 1) * 100
                    ) if data.get("conversion_data", {}).get("serbyn_pro_visits", 0) > 0 else 0.0
                }
                for platform, data in platform_metrics.items()
            }
        }

    async def identify_best_platform(self, platform_metrics: Dict[str, Any]) -> str:
        """Identify the best performing platform based on job inquiries"""
        best_platform = "linkedin"  # Default
        max_inquiries = 0
        
        for platform, data in platform_metrics.items():
            inquiries = data.get("conversion_data", {}).get("job_inquiries", 0)
            if inquiries > max_inquiries:
                max_inquiries = inquiries
                best_platform = platform
        
        return best_platform

    async def calculate_roi_analysis(self) -> Dict[str, Any]:
        """Calculate ROI analysis for content marketing"""
        return {
            "total_content_pieces": 0,
            "total_engagement": 0,
            "estimated_time_investment_hours": 0,
            "lead_generation_value": 0,
            "roi_percentage": 0.0,
            "cost_per_lead": 0.0,
            "recommendations": [
                "Focus on high-converting platforms",
                "Optimize content for engagement",
                "Track conversion attribution better"
            ]
        }

    async def get_platform_ranking(self) -> Dict[str, Any]:
        """Get platform performance ranking"""
        return {
            "ranking": [
                {
                    "platform": "linkedin",
                    "rank": 1,
                    "score": 0.0,
                    "engagement_rate": 0.0,
                    "conversion_rate": 0.0,
                    "reach": 0
                }
            ],
            "criteria": [
                "conversion_rate",
                "engagement_rate",
                "reach",
                "lead_quality"
            ]
        }


class ConversionTracker:
    """Service to track conversions from content to leads"""

    def __init__(self):
        self.conversion_store = {}  # In-memory store for TDD, will use DB later
        self.lead_store = {}

    async def track_conversion(self, conversion_event: Dict[str, Any]) -> Dict[str, Any]:
        """Track a conversion from content to website visit"""
        conversion_id = f"conv_{len(self.conversion_store) + 1}"
        
        self.conversion_store[conversion_id] = {
            **conversion_event,
            "conversion_id": conversion_id,
            "tracked_at": datetime.utcnow().isoformat()
        }
        
        return {
            "success": True,
            "conversion_id": conversion_id,
            "platform": conversion_event.get("source_platform", "unknown")
        }

    async def track_lead_conversion(self, lead_event: Dict[str, Any]) -> Dict[str, Any]:
        """Track a conversion from website visit to lead"""
        lead_id = f"lead_{len(self.lead_store) + 1}"
        
        # Find the original conversion to attribute platform
        attributed_platform = "unknown"
        source_conversion_id = lead_event.get("source_conversion_id")
        if source_conversion_id and source_conversion_id in self.conversion_store:
            attributed_platform = self.conversion_store[source_conversion_id].get("source_platform", "unknown")
        
        self.lead_store[lead_id] = {
            **lead_event,
            "lead_id": lead_id,
            "attributed_platform": attributed_platform,
            "tracked_at": datetime.utcnow().isoformat()
        }
        
        return {
            "success": True,
            "lead_id": lead_id,
            "attributed_platform": attributed_platform
        }

    async def get_attribution_chain(self, lead_id: str) -> Dict[str, Any]:
        """Get full attribution chain from content to lead"""
        lead_data = self.lead_store.get(lead_id, {})
        source_conversion_id = lead_data.get("source_conversion_id")
        
        conversion_data = {}
        if source_conversion_id:
            conversion_data = self.conversion_store.get(source_conversion_id, {})
        
        return {
            "content_source": conversion_data.get("content_url", "unknown"),
            "platform": conversion_data.get("source_platform", "unknown"),
            "content_url": conversion_data.get("content_url", "unknown"),
            "website_visit_timestamp": conversion_data.get("timestamp", "unknown"),
            "lead_conversion_timestamp": lead_data.get("timestamp", "unknown"),
            "total_conversion_time_hours": 0.5  # Placeholder calculation
        }