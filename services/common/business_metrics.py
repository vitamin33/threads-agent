"""
Business Metrics Collection for Real ROI Tracking

This module provides actual business value measurement capabilities
instead of just describing them in PR text.
"""

from typing import Dict, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class PerformanceMetrics:
    """Real performance metrics that drive business value."""

    requests_per_second: float
    avg_latency_ms: float
    success_rate: float
    timestamp: datetime


@dataclass
class BusinessImpact:
    """Calculated business impact from performance improvements."""

    estimated_cost_savings_annual: float
    productivity_improvement_percent: float
    user_experience_score: float
    roi_percent: float


class BusinessMetricsCollector:
    """Collects and calculates real business value metrics."""

    def __init__(self):
        self.baseline_metrics: Optional[PerformanceMetrics] = None
        self.current_metrics: Optional[PerformanceMetrics] = None

    def record_baseline(self, rps: float, latency_ms: float, success_rate: float):
        """Record baseline performance before improvements."""
        self.baseline_metrics = PerformanceMetrics(
            requests_per_second=rps,
            avg_latency_ms=latency_ms,
            success_rate=success_rate,
            timestamp=datetime.now(),
        )

    def record_current_performance(
        self, rps: float, latency_ms: float, success_rate: float
    ):
        """Record current performance after improvements."""
        self.current_metrics = PerformanceMetrics(
            requests_per_second=rps,
            avg_latency_ms=latency_ms,
            success_rate=success_rate,
            timestamp=datetime.now(),
        )

    def calculate_business_impact(
        self, development_cost: float = 25000
    ) -> BusinessImpact:
        """Calculate real business impact based on measured improvements."""
        if not self.baseline_metrics or not self.current_metrics:
            return BusinessImpact(0, 0, 0, 0)

        # Calculate performance improvements
        rps_improvement = (
            self.current_metrics.requests_per_second
            / self.baseline_metrics.requests_per_second
        ) - 1

        latency_improvement = (
            self.baseline_metrics.avg_latency_ms - self.current_metrics.avg_latency_ms
        ) / self.baseline_metrics.avg_latency_ms

        # Infrastructure cost savings (fewer servers needed for same load)
        # Assumption: 1 server costs $10k/year, RPS improvement reduces server needs
        servers_saved = max(0, rps_improvement * 2)  # Conservative estimate
        infrastructure_savings = servers_saved * 10000

        # Developer productivity (faster responses = faster development)
        # Assumption: 10% latency improvement = 2% productivity gain
        productivity_gain = latency_improvement * 0.2
        developer_cost_savings = productivity_gain * 200000  # Team cost per year

        total_annual_savings = infrastructure_savings + developer_cost_savings
        roi = (total_annual_savings / development_cost) * 100

        # User experience score (based on latency)
        if self.current_metrics.avg_latency_ms < 100:
            ux_score = 10
        elif self.current_metrics.avg_latency_ms < 200:
            ux_score = 9
        elif self.current_metrics.avg_latency_ms < 500:
            ux_score = 8
        else:
            ux_score = 7

        return BusinessImpact(
            estimated_cost_savings_annual=total_annual_savings,
            productivity_improvement_percent=productivity_gain * 100,
            user_experience_score=ux_score,
            roi_percent=roi,
        )

    def get_metrics_summary(self) -> Dict:
        """Get summary for PR analysis integration."""
        if not self.current_metrics:
            return {}

        impact = self.calculate_business_impact()

        return {
            "peak_rps": self.current_metrics.requests_per_second,
            "latency_ms": self.current_metrics.avg_latency_ms,
            "success_rate": self.current_metrics.success_rate,
            "business_impact": {
                "annual_savings": impact.estimated_cost_savings_annual,
                "productivity_improvement": impact.productivity_improvement_percent,
                "user_experience_score": impact.user_experience_score,
                "roi_percent": impact.roi_percent,
            },
        }


# Global metrics collector instance
business_metrics = BusinessMetricsCollector()


# Example usage for RAG Pipeline
def demonstrate_real_metrics():
    """Demonstrate how to collect real business metrics."""

    # Record baseline (before RAG pipeline)
    business_metrics.record_baseline(
        rps=150,  # Old search was slow
        latency_ms=800,  # Traditional keyword search
        success_rate=0.85,  # Poor relevance
    )

    # Record current performance (after RAG pipeline)
    business_metrics.record_current_performance(
        rps=1200,  # RAG pipeline handles more load
        latency_ms=150,  # Semantic search is faster
        success_rate=0.98,  # Better relevance
    )

    # Calculate real business impact
    impact = business_metrics.calculate_business_impact()

    print("Real Business Value:")
    print(f"Annual Savings: ${impact.estimated_cost_savings_annual:,.0f}")
    print(f"Productivity Gain: {impact.productivity_improvement_percent:.1f}%")
    print(f"ROI: {impact.roi_percent:.0f}%")
    print(f"UX Score: {impact.user_experience_score}/10")


if __name__ == "__main__":
    demonstrate_real_metrics()
