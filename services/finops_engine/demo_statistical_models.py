#!/usr/bin/env python3
"""
Demonstration of Statistical Models for Anomaly Detection

Shows how to use StatisticalModel, TrendModel, SeasonalModel, and FatigueModel
for comprehensive anomaly detection in the threads-agent system.
"""

from models import StatisticalModel, TrendModel, SeasonalModel, FatigueModel
from datetime import datetime, timedelta
import random


def demo_statistical_models():
    """Demonstrate all statistical models working together."""
    print("=== Statistical Models for Anomaly Detection Demo ===\n")

    # Initialize all models
    statistical = StatisticalModel(window_size=50, threshold=2.0)
    trend = TrendModel(lookback_hours=24, trend_threshold=0.3)
    seasonal = SeasonalModel(period_hours=168)  # Weekly pattern
    fatigue = FatigueModel(decay_factor=0.9, fatigue_threshold=0.7)

    print("1. Setting up baseline data...")

    # Simulate 7 days of historical data
    now = datetime.now()
    base_engagement = 100.0

    for day in range(7):
        for hour in range(24):
            timestamp = now - timedelta(days=day, hours=hour)

            # Simulate daily engagement pattern (higher during day, lower at night)
            daily_multiplier = 0.5 + 0.5 * abs(12 - hour) / 12
            # Add some weekly variation (weekends higher)
            weekly_multiplier = 1.2 if timestamp.weekday() >= 5 else 1.0
            # Add random noise
            noise = random.uniform(0.9, 1.1)

            engagement = base_engagement * daily_multiplier * weekly_multiplier * noise

            # Add to all models
            statistical.add_data_point(engagement)
            trend.add_hourly_data(timestamp, engagement)
            seasonal.add_seasonal_data(timestamp, engagement)

    # Record some pattern usage
    patterns = ["viral_hook", "question_hook", "story_hook", "stat_hook"]
    for i, pattern in enumerate(patterns):
        for usage in range(random.randint(1, 5)):
            usage_time = now - timedelta(hours=random.randint(1, 48))
            fatigue.record_pattern_usage(pattern, usage_time)

    print("✓ Added 168 hours (7 days) of baseline data")
    print(f"✓ Statistical model stats: {statistical.get_statistics()}")
    print(f"✓ Trend model baseline: {trend.calculate_baseline():.2f}")
    print(f"✓ Seasonal model metrics: {seasonal.get_seasonal_metrics()}")
    print(f"✓ Fatigue model metrics: {fatigue.get_fatigue_metrics()}")

    print("\n2. Testing current engagement values...")

    # Test different scenarios
    test_scenarios = [
        ("Normal engagement", 120.0),
        ("High engagement", 180.0),
        ("Low engagement", 40.0),
        ("Extreme drop", 10.0),
    ]

    current_time = now

    for scenario_name, test_value in test_scenarios:
        print(f"\n--- {scenario_name}: {test_value} ---")

        # Test with all models
        stat_anomaly = statistical.is_anomaly(test_value)
        stat_score = statistical.calculate_anomaly_score(test_value)

        trend_break = trend.detect_trend_break(test_value)
        trend_baseline = trend.calculate_baseline()

        seasonal_anomaly = seasonal.is_seasonal_anomaly(current_time, test_value)
        seasonal_baseline = seasonal.get_seasonal_baseline(current_time)

        print(
            f"  Statistical: {'🚨 ANOMALY' if stat_anomaly else '✓ Normal'} (score: {stat_score:.2f})"
        )
        print(
            f"  Trend: {'🚨 BREAK' if trend_break else '✓ Normal'} (baseline: {trend_baseline:.2f})"
        )
        print(
            f"  Seasonal: {'🚨 ANOMALY' if seasonal_anomaly else '✓ Normal'} (baseline: {seasonal_baseline:.2f})"
        )

    print("\n3. Testing pattern fatigue...")

    for pattern in patterns:
        is_fatigued = fatigue.is_pattern_fatigued(pattern)
        score = fatigue.calculate_fatigue_score(pattern)
        print(
            f"  {pattern}: {'🚨 FATIGUED' if is_fatigued else '✓ Fresh'} (score: {score:.2f})"
        )

    print("\n4. Comprehensive anomaly detection example...")

    # Simulate a real-time check
    current_engagement = 45.0  # Suspicious low value
    current_pattern = "viral_hook"

    print(
        f"\nChecking engagement: {current_engagement} with pattern '{current_pattern}'"
    )

    anomalies = []

    if statistical.is_anomaly(current_engagement):
        anomalies.append(
            f"Statistical anomaly (z-score: {statistical.calculate_anomaly_score(current_engagement):.2f})"
        )

    if trend.detect_trend_break(current_engagement):
        anomalies.append(
            f"Trend break detected (baseline: {trend.calculate_baseline():.2f})"
        )

    if seasonal.is_seasonal_anomaly(current_time, current_engagement):
        anomalies.append(
            f"Seasonal anomaly (expected: {seasonal.get_seasonal_baseline(current_time):.2f})"
        )

    if fatigue.is_pattern_fatigued(current_pattern):
        anomalies.append(
            f"Pattern fatigue detected (score: {fatigue.calculate_fatigue_score(current_pattern):.2f})"
        )

    if anomalies:
        print("🚨 ALERT: Anomalies detected!")
        for anomaly in anomalies:
            print(f"  - {anomaly}")
        print("\nRecommendations:")
        if any("Statistical" in a for a in anomalies):
            print("  • Investigate sudden engagement drop")
        if any("Trend" in a for a in anomalies):
            print("  • Check for system issues or external factors")
        if any("Seasonal" in a for a in anomalies):
            print("  • Unusual pattern for this time - verify posting schedule")
        if any("Pattern fatigue" in a for a in anomalies):
            print("  • Consider using different content patterns")
    else:
        print("✓ All systems normal - no anomalies detected")

    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    demo_statistical_models()
