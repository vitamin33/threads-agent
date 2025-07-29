"""Prometheus metrics scraper for automatic achievement generation."""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict

import httpx

from ..api.schemas import AchievementCreate
from ..db.config import get_db
from ..api.routes.achievements import create_achievement_sync


class PrometheusScaper:
    """Scrapes Prometheus metrics and creates achievements from KPI improvements."""

    def __init__(self):
        self.prometheus_url = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
        self.scrape_interval = int(os.getenv("SCRAPE_INTERVAL_HOURS", "24"))

        # KPI thresholds for achievement generation
        self.kpi_thresholds = {
            "posts_engagement_rate": 0.06,  # 6% engagement
            "revenue_projection_monthly": 20000,  # $20k MRR
            "cost_per_follow_dollars": 0.01,  # $0.01 per follow
            "content_generation_latency_seconds": 2.0,  # 2s generation
            "posts_generated_total": 100,  # 100 posts milestone
            "http_request_duration_seconds": 0.5,  # 500ms response time
        }

        # Track previous values to detect improvements
        self.previous_values = {}

    async def scrape_and_track_achievements(self):
        """Main loop to scrape metrics and create achievements."""
        while True:
            try:
                await self._scrape_metrics()
                await asyncio.sleep(
                    self.scrape_interval * 3600
                )  # Convert hours to seconds
            except Exception as e:
                print(f"Error in scraper loop: {e}")
                await asyncio.sleep(300)  # Retry in 5 minutes

    async def _scrape_metrics(self):
        """Scrape current metrics from Prometheus."""
        metrics = await self._query_prometheus_metrics()

        for metric_name, current_value in metrics.items():
            if metric_name in self.kpi_thresholds:
                await self._check_and_create_achievement(
                    metric_name, current_value, self.kpi_thresholds[metric_name]
                )

    async def _query_prometheus_metrics(self) -> Dict[str, float]:
        """Query Prometheus for current metric values."""
        metrics = {}

        # Define queries for each KPI
        queries = {
            "posts_engagement_rate": "avg(posts_engagement_rate)",
            "revenue_projection_monthly": 'revenue_projection_monthly{source="current_run_rate"}',
            "cost_per_follow_dollars": "avg(cost_per_follow_dollars)",
            "content_generation_latency_seconds": "avg(content_generation_latency_seconds)",
            "posts_generated_total": "sum(posts_generated_total)",
            "http_request_duration_seconds": "avg(http_request_duration_seconds)",
            "error_rate": 'sum(rate(http_requests_total{status_code=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))',
            "uptime": "avg_over_time(up[7d])",
        }

        async with httpx.AsyncClient() as client:
            for metric_name, query in queries.items():
                try:
                    response = await client.get(
                        f"{self.prometheus_url}/api/v1/query", params={"query": query}
                    )
                    data = response.json()

                    if data["status"] == "success" and data["data"]["result"]:
                        value = float(data["data"]["result"][0]["value"][1])
                        metrics[metric_name] = value
                except Exception as e:
                    print(f"Error querying {metric_name}: {e}")

        return metrics

    async def _check_and_create_achievement(
        self, metric_name: str, current_value: float, threshold: float
    ):
        """Check if metric improvement warrants an achievement."""
        previous = self.previous_values.get(metric_name, None)

        # Different logic for different metric types
        if metric_name in [
            "posts_engagement_rate",
            "revenue_projection_monthly",
            "uptime",
        ]:
            # Higher is better
            if current_value >= threshold and (
                previous is None or current_value > previous * 1.1
            ):
                await self._create_metric_achievement(
                    metric_name, current_value, threshold, "exceeded"
                )

        elif metric_name in [
            "cost_per_follow_dollars",
            "content_generation_latency_seconds",
            "error_rate",
        ]:
            # Lower is better
            if current_value <= threshold and (
                previous is None or current_value < previous * 0.9
            ):
                await self._create_metric_achievement(
                    metric_name, current_value, threshold, "reduced"
                )

        elif metric_name == "posts_generated_total":
            # Milestone-based
            milestones = [100, 500, 1000, 5000, 10000]
            for milestone in milestones:
                if current_value >= milestone and (
                    previous is None or previous < milestone
                ):
                    await self._create_milestone_achievement(
                        metric_name, current_value, milestone
                    )

        # Update previous value
        self.previous_values[metric_name] = current_value

    async def _create_metric_achievement(
        self, metric_name: str, value: float, threshold: float, achievement_type: str
    ):
        """Create achievement for metric improvement."""

        # Format metric name for display
        display_name = metric_name.replace("_", " ").title()

        # Calculate improvement percentage
        if metric_name in self.previous_values:
            previous = self.previous_values[metric_name]
            if achievement_type == "exceeded":
                improvement = ((value - previous) / previous) * 100
            else:  # reduced
                improvement = ((previous - value) / previous) * 100
        else:
            improvement = 0

        achievement_data = AchievementCreate(
            title=f"KPI Achievement: {display_name}",
            category="performance",
            description=f"{achievement_type.capitalize()} {display_name} target: {value:.2f} (target: {threshold:.2f})",
            started_at=datetime.utcnow() - timedelta(hours=self.scrape_interval),
            completed_at=datetime.utcnow(),
            source_type="prometheus",
            source_id=f"kpi-{metric_name}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            tags=["prometheus", "kpi", "performance", "monitoring"],
            skills_demonstrated=[
                "Performance Analysis",
                "Metrics Monitoring",
                "Prometheus",
                "DevOps",
            ],
            metrics_after={
                "metric_name": metric_name,
                "achieved_value": value,
                "target_value": threshold,
                "improvement_percentage": improvement,
                "timestamp": datetime.utcnow().isoformat(),
            },
            business_value=self._calculate_business_value(metric_name, value),
            impact_score=min(90.0, 50.0 + improvement),
            complexity_score=70.0,
        )

        db = next(get_db())
        try:
            achievement = create_achievement_sync(db, achievement_data)
            print(f"Created achievement for {metric_name}: {value}")
            return achievement
        finally:
            db.close()

    async def _create_milestone_achievement(
        self, metric_name: str, value: float, milestone: int
    ):
        """Create achievement for reaching a milestone."""
        achievement_data = AchievementCreate(
            title=f"Milestone: {milestone} {metric_name.replace('_total', '').replace('_', ' ').title()}",
            category="milestone",
            description=f"Reached {milestone} milestone for {metric_name.replace('_', ' ')}",
            started_at=datetime.utcnow() - timedelta(days=7),  # Assume week to reach
            completed_at=datetime.utcnow(),
            source_type="prometheus",
            source_id=f"milestone-{metric_name}-{milestone}",
            tags=["milestone", "growth", "automation", "content"],
            skills_demonstrated=[
                "Content Generation",
                "AI Integration",
                "Automation",
                "Growth Engineering",
            ],
            metrics_after={
                "metric_name": metric_name,
                "milestone": milestone,
                "current_total": int(value),
                "timestamp": datetime.utcnow().isoformat(),
            },
            business_value=self._calculate_milestone_value(metric_name, milestone),
            impact_score=80.0,
            complexity_score=60.0,
        )

        db = next(get_db())
        try:
            achievement = create_achievement_sync(db, achievement_data)
            print(f"Created milestone achievement for {metric_name}: {milestone}")
            return achievement
        finally:
            db.close()

    def _generate_impact_statement(
        self, metric: str, value: float, improvement: float
    ) -> str:
        """Generate impact statement based on metric type and improvement."""
        impact_templates = {
            "posts_engagement_rate": f"Achieved {value * 100:.1f}% engagement rate, {improvement:.0f}% improvement - driving viral content success",
            "revenue_projection_monthly": f"Reached ${value:.0f} MRR projection, {improvement:.0f}% growth - approaching profitability targets",
            "cost_per_follow_dollars": f"Reduced cost to ${value:.3f} per follower, {improvement:.0f}% efficiency gain - optimizing acquisition",
            "content_generation_latency_seconds": f"Optimized generation to {value:.1f}s, {improvement:.0f}% faster - enhancing user experience",
            "error_rate": f"Reduced error rate to {value * 100:.2f}%, {improvement:.0f}% improvement - increasing reliability",
            "uptime": f"Maintained {value * 100:.1f}% uptime - ensuring platform stability",
        }

        return impact_templates.get(metric, f"Improved {metric} by {improvement:.0f}%")

    def _calculate_business_value(self, metric: str, value: float) -> str:
        """Calculate business value statement for achievements."""
        value_calculations = {
            "posts_engagement_rate": f"${value * 10000:.0f} monthly value from {value * 100:.1f}% engagement",
            "revenue_projection_monthly": f"${value:.0f} direct monthly revenue impact",
            "cost_per_follow_dollars": f"${(0.01 - value) * 100000:.0f} saved annually vs baseline",
            "content_generation_latency_seconds": f"{(5.0 - value) * 1000:.0f} hours saved monthly on generation",
            "error_rate": f"${(1 - value) * 5000:.0f} monthly value from reliability",
            "uptime": f"${value * 50000:.0f} annual value from platform availability",
        }

        return value_calculations.get(metric, "Significant operational value")

    def _calculate_milestone_value(self, metric: str, milestone: int) -> str:
        """Calculate value for milestone achievements."""
        if "posts" in metric:
            return f"${milestone * 0.50:.0f} content value created"
        elif "users" in metric:
            return f"${milestone * 10:.0f} lifetime value potential"
        else:
            return f"Reached {milestone} scale milestone"
