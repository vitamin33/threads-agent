"""Threads-agent integration for automatic achievement tracking."""

import os
from datetime import datetime
from typing import Dict, List, Optional

import httpx

from ..api.schemas import AchievementCreate
from ..db.config import get_db
from ..api.routes.achievements import create_achievement_sync


class ThreadsIntegration:
    """Integrates with threads-agent to track viral content achievements."""

    def __init__(self):
        self.orchestrator_url = os.getenv(
            "ORCHESTRATOR_URL", "http://orchestrator:8080"
        )
        self.threads_url = os.getenv(
            "THREADS_ADAPTOR_URL", "http://threads-adaptor:8000"
        )

    async def track_viral_post(self, post_data: Dict) -> Optional[Dict]:
        """Create achievement from viral post (>6% engagement)."""
        engagement_rate = post_data.get("engagement_rate", 0)

        if engagement_rate < 0.06:  # Only track viral posts
            return None

        # Calculate metrics for viral content
        views = post_data.get("views", 0)
        # Future: can use likes and shares for enhanced scoring
        # likes = post_data.get("likes", 0)
        # shares = post_data.get("shares", 0)

        achievement_data = AchievementCreate(
            title=f"Viral Post: {post_data.get('hook', 'Untitled')[:50]}",
            category="content",
            description=f"Created viral content with {engagement_rate * 100:.1f}% engagement rate",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            source_type="threads",
            source_id=f"viral-post-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            tags=["viral-content", "engagement", "ai-generated"],
            skills_demonstrated=["Content Creation", "AI Integration", "Social Media"],
            business_value=f"${self._estimate_revenue(views, engagement_rate):.2f} estimated revenue",
        )

        db = next(get_db())
        try:
            achievement = create_achievement_sync(db, achievement_data)
            return achievement
        finally:
            db.close()

    async def track_kpi_milestone(
        self, metric_name: str, value: float, target: float
    ) -> Optional[Dict]:
        """Track KPI milestones as achievements."""
        if value < target:
            return None

        achievement_data = AchievementCreate(
            title=f"KPI Milestone: {metric_name}",
            category="business",
            description=f"Achieved {metric_name} target: {value:.2f} (target: {target:.2f})",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            source_type="threads",
            source_id=f"kpi-{metric_name}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            tags=["kpi", "milestone", "metrics"],
            skills_demonstrated=[
                "Performance Analysis",
                "KPI Management",
                "Business Intelligence",
            ],
            business_value=self._estimate_kpi_value(metric_name, value),
        )

        db = next(get_db())
        try:
            achievement = create_achievement_sync(db, achievement_data)
            return achievement
        finally:
            db.close()

    async def fetch_recent_posts(self, hours: int = 24) -> List[Dict]:
        """Fetch recent posts from threads-adaptor."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.threads_url}/posts", params={"hours": hours}
            )
            return response.json()

    async def fetch_metrics(self) -> Dict:
        """Fetch current metrics from orchestrator."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.orchestrator_url}/metrics")
            return self._parse_prometheus_metrics(response.text)

    def _calculate_impact(self, engagement_rate: float, views: int) -> str:
        """Calculate impact description for viral content."""
        if engagement_rate > 0.15:
            return "Exceptional viral reach with breakthrough engagement"
        elif engagement_rate > 0.10:
            return "High viral impact with strong audience resonance"
        elif engagement_rate > 0.06:
            return "Solid viral performance exceeding industry benchmarks"
        else:
            return "Good content performance with viral potential"

    def _estimate_revenue(self, views: int, engagement_rate: float) -> float:
        """Estimate revenue from viral content."""
        # Rough calculation: $0.01 per engaged view
        engaged_views = views * engagement_rate
        return engaged_views * 0.01

    def _calculate_kpi_impact(self, metric: str, value: float, target: float) -> str:
        """Calculate impact for KPI achievements."""
        percentage = (value / target - 1) * 100

        if percentage > 50:
            return f"Exceeded target by {percentage:.0f}% - exceptional performance"
        elif percentage > 20:
            return f"Surpassed target by {percentage:.0f}% - strong achievement"
        else:
            return f"Met target with {percentage:.0f}% overperformance"

    def _estimate_kpi_value(self, metric: str, value: float) -> str:
        """Estimate business value of KPI achievement."""
        value_map = {
            "revenue": f"${value:.2f} direct revenue impact",
            "engagement": f"${value * 1000:.2f} estimated value from engagement",
            "cost_per_follow": f"${(0.01 - value) * 10000:.2f} saved vs target",
            "posts_generated": f"${value * 0.50:.2f} content value created",
        }

        for key, template in value_map.items():
            if key in metric.lower():
                return template

        return "Significant business impact"

    def _parse_prometheus_metrics(self, metrics_text: str) -> Dict:
        """Parse Prometheus metrics text format."""
        metrics = {}
        for line in metrics_text.split("\n"):
            if line.startswith("#") or not line.strip():
                continue

            parts = line.split(" ")
            if len(parts) >= 2:
                metric_name = parts[0].split("{")[0]
                try:
                    value = float(parts[-1])
                    metrics[metric_name] = value
                except ValueError:
                    continue

        return metrics
