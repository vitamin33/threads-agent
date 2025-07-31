"""Production KPI monitoring for Thompson Sampling variant selection."""

from prometheus_client import Counter, Histogram, Gauge
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Business KPI Metrics
ENGAGEMENT_RATE = Histogram(
    "variant_engagement_rate",
    "Actual engagement rate by variant",
    ["variant_id", "hook_style", "emotion"],
    buckets=[0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10, 0.15],
)

VARIANTS_KILLED_EARLY = Counter(
    "variants_killed_early_total",
    "Number of variants killed within 10 minutes",
    ["reason"],
)

PATTERN_USAGE = Gauge(
    "pattern_usage_7d", "Pattern usage count in last 7 days", ["pattern_hash"]
)

ENGAGEMENT_IMPROVEMENT = Gauge(
    "engagement_improvement_percent", "Percentage improvement over baseline"
)

COST_PER_POST = Histogram(
    "cost_per_post_dollars",
    "Cost per post in dollars",
    buckets=[0.005, 0.01, 0.015, 0.02, 0.025, 0.03],
)


class KPIMonitor:
    """Monitor business KPIs in production."""

    def __init__(self, db_session):
        self.db_session = db_session
        self.baseline_engagement = 0.04  # 4% baseline from historical data

    def check_early_kill_candidates(self):
        """Check for variants that should be killed after 10 minutes."""
        from services.orchestrator.db.models import VariantPerformance

        cutoff_time = datetime.utcnow() - timedelta(minutes=10)
        min_impressions = 10
        performance_threshold = 0.03  # 50% of 6% target

        # Find poor performers
        poor_performers = (
            self.db_session.query(VariantPerformance)
            .filter(
                VariantPerformance.created_at <= cutoff_time,
                VariantPerformance.impressions >= min_impressions,
                VariantPerformance.success_rate < performance_threshold,
            )
            .all()
        )

        for variant in poor_performers:
            logger.info(
                f"Killing variant {variant.variant_id} - "
                f"engagement: {variant.success_rate:.2%}, "
                f"impressions: {variant.impressions}"
            )

            # Mark as inactive (or delete)
            variant.is_active = False

            # Record metric
            VARIANTS_KILLED_EARLY.labels(reason="low_performance").inc()

        self.db_session.commit()
        return [v.variant_id for v in poor_performers]

    def calculate_engagement_improvement(self):
        """Calculate engagement improvement vs baseline."""
        from services.orchestrator.db.models import VariantPerformance

        # Get recent performance data (last 24 hours)
        cutoff = datetime.utcnow() - timedelta(hours=24)

        recent_variants = (
            self.db_session.query(VariantPerformance)
            .filter(
                VariantPerformance.last_used >= cutoff,
                VariantPerformance.impressions >= 100,  # Significant sample
            )
            .all()
        )

        if not recent_variants:
            return 0.0

        # Calculate weighted average engagement
        total_impressions = sum(v.impressions for v in recent_variants)
        total_engagements = sum(v.successes for v in recent_variants)

        current_engagement = (
            total_engagements / total_impressions if total_impressions > 0 else 0
        )

        # Calculate improvement
        improvement = (
            (current_engagement - self.baseline_engagement)
            / self.baseline_engagement
            * 100
        )

        # Record metric
        ENGAGEMENT_IMPROVEMENT.set(improvement)

        logger.info(
            f"Engagement improvement: {improvement:.1f}% "
            f"(current: {current_engagement:.2%}, baseline: {self.baseline_engagement:.2%})"
        )

        return improvement

    def track_pattern_fatigue(self):
        """Track pattern usage to detect fatigue."""
        from services.orchestrator.db.models import VariantPerformance

        cutoff = datetime.utcnow() - timedelta(days=7)

        # Count pattern usage
        recent_variants = (
            self.db_session.query(VariantPerformance)
            .filter(VariantPerformance.last_used >= cutoff)
            .all()
        )

        pattern_counts = {}
        for variant in recent_variants:
            # Extract pattern (hook_style + emotion)
            dims = variant.dimensions
            pattern = (
                f"{dims.get('hook_style', 'unknown')}_{dims.get('emotion', 'unknown')}"
            )
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

        # Update metrics
        for pattern, count in pattern_counts.items():
            PATTERN_USAGE.labels(pattern_hash=pattern).set(count)

            if count >= 3:  # Overused threshold
                logger.warning(f"Pattern '{pattern}' used {count} times in 7 days")

        return pattern_counts

    def track_cost_per_post(self, variants_generated, e3_cache_hits, e3_cache_misses):
        """Track cost per post request."""
        # Cost calculation based on actual usage
        COST_PER_1K_TOKENS_CHEAP = 0.0005
        COST_PER_1K_TOKENS_EXPENSIVE = 0.03
        AVG_TOKENS_PER_VARIANT = 150
        E3_TOKENS_PER_PREDICTION = 200

        generation_cost = (
            variants_generated
            * AVG_TOKENS_PER_VARIANT
            * COST_PER_1K_TOKENS_CHEAP
            / 1000
        )

        e3_cost = (
            e3_cache_misses
            * E3_TOKENS_PER_PREDICTION
            * COST_PER_1K_TOKENS_EXPENSIVE
            / 1000
        )

        total_cost = generation_cost + e3_cost

        # Record metric
        COST_PER_POST.observe(total_cost)

        if total_cost > 0.02:
            logger.warning(f"Cost per post ${total_cost:.4f} exceeds $0.02 target!")

        return total_cost


# Alerting rules for Prometheus/AlertManager
ALERTING_RULES = """
groups:
  - name: thompson_sampling_kpis
    interval: 5m
    rules:
      - alert: LowEngagementImprovement
        expr: engagement_improvement_percent < 10
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Engagement improvement below 15% target"
          description: "Current improvement: {{ $value }}%"
      
      - alert: HighCostPerPost
        expr: histogram_quantile(0.95, cost_per_post_dollars) > 0.02
        for: 30m
        labels:
          severity: critical
        annotations:
          summary: "Cost per post exceeding $0.02"
          description: "95th percentile cost: ${{ $value }}"
      
      - alert: PatternFatigue
        expr: pattern_usage_7d > 5
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Pattern '{{ $labels.pattern_hash }}' overused"
          description: "Used {{ $value }} times in last 7 days"
"""
