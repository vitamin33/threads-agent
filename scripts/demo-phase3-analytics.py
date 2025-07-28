#!/usr/bin/env python3
"""
Demo script for Phase 3.1 Analytics Features.
Shows how to use the analytics modules directly.
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.achievement_collector.analytics.career_predictor import CareerPredictor
from services.achievement_collector.analytics.industry_benchmark import (
    IndustryBenchmarker,
)
from services.achievement_collector.analytics.performance_dashboard import (
    PerformanceDashboard,
)
from services.achievement_collector.db.models import Achievement


def create_sample_achievements():
    """Create sample achievements for demo."""
    achievements = []

    # Recent high-impact achievement
    achievements.append(
        Achievement(
            title="Implemented Phase 3.1 Analytics for Achievement Collector",
            description="Developed advanced analytics including career prediction, industry benchmarking, and performance dashboards",
            category="feature",
            impact_score=90,
            complexity_score=85,
            skills_demonstrated=[
                "Python",
                "FastAPI",
                "AI/ML",
                "Data Analytics",
                "SQLAlchemy",
            ],
            business_value="Enables data-driven career decisions and strategic planning",
            started_at=datetime.utcnow() - timedelta(days=7),
            completed_at=datetime.utcnow(),
            duration_hours=56,
            source_type="manual",
            source_id="phase3_1",
        )
    )

    # Previous achievements
    for i in range(5):
        achievements.append(
            Achievement(
                title=f"Optimized {['Database', 'API', 'CI/CD', 'Search', 'Caching'][i]} Performance",
                description=f"Improved system performance by {20 + i * 10}%",
                category="optimization",
                impact_score=70 + i * 5,
                complexity_score=60 + i * 4,
                skills_demonstrated=["Python", "Performance Tuning", "Monitoring"],
                business_value=f"${(i + 1) * 10000} annual savings",
                started_at=datetime.utcnow() - timedelta(days=30 * (6 - i)),
                completed_at=datetime.utcnow() - timedelta(days=30 * (6 - i) - 7),
                duration_hours=40,
                source_type="manual",
                source_id=f"opt_{i}",
            )
        )

    return achievements


async def demo_career_prediction():
    """Demo career prediction features."""
    print("\n🔮 CAREER PREDICTION DEMO")
    print("=" * 50)

    predictor = CareerPredictor()
    achievements = create_sample_achievements()

    # Analyze skill progression
    skills = predictor._analyze_skill_progression(achievements)
    print("\n📊 Skill Progression:")
    for skill_name, prog in list(skills.items())[:3]:
        print(
            f"  • {skill_name}: Level {prog.current_level}/10 "
            f"(Growth: {prog.growth_rate:.2f}/month)"
        )

    # Calculate career velocity
    velocity = predictor._calculate_career_velocity(achievements)
    print(f"\n🚀 Career Velocity: {velocity}x industry average")

    # Mock prediction (since we don't have a real DB session)
    print("\n🎯 Career Predictions:")
    print("  • Next Role: Senior Staff Engineer (85% confidence)")
    print("  • Timeline: 12-18 months")
    print("  • Required Skills: System Design, Team Leadership")
    print("  • Salary Range: $180k - $220k")


def demo_industry_benchmarking():
    """Demo industry benchmarking features."""
    print("\n📈 INDUSTRY BENCHMARKING DEMO")
    print("=" * 50)

    benchmarker = IndustryBenchmarker()
    achievements = create_sample_achievements()

    # Calculate metrics
    metrics = benchmarker._calculate_user_metrics(achievements, 180)

    print("\n📊 Your Metrics vs Industry:")
    for metric_name, value in list(metrics.items())[:4]:
        benchmark = benchmarker._benchmark_metric(metric_name, value)
        print(f"  • {metric_name}: {value:.1f}")
        print(f"    - Industry Avg: {benchmark.industry_average}")
        print(f"    - Your Percentile: {benchmark.percentile}%")
        print(f"    - Status: {benchmark.trend}")

    # Skill market analysis
    skills = ["AI/ML", "Python", "Kubernetes"]
    market_data = benchmarker.analyze_skill_market(skills)

    print("\n💼 Skill Market Analysis:")
    for skill_data in market_data:
        print(f"  • {skill_data.skill_name}:")
        print(f"    - Demand/Supply Ratio: {skill_data.market_ratio:.1f}")
        print(f"    - Avg Premium: {skill_data.average_premium}%")
        print(f"    - Outlook: {skill_data.future_outlook}")


def demo_performance_dashboard():
    """Demo performance dashboard features."""
    print("\n📊 PERFORMANCE DASHBOARD DEMO")
    print("=" * 50)

    dashboard = PerformanceDashboard()
    achievements = create_sample_achievements()

    # Generate metrics
    avg_impact = dashboard._calculate_average_impact(achievements)
    velocity = dashboard._calculate_career_velocity(achievements)
    skill_count = dashboard._count_unique_skills(achievements)

    print("\n📈 Dashboard Summary:")
    print(f"  • Total Achievements: {len(achievements)}")
    print(f"  • Average Impact Score: {avg_impact:.1f}")
    print(f"  • Career Velocity: {velocity}x")
    print(f"  • Unique Skills: {skill_count}")

    # Category distribution
    dist = dashboard._calculate_category_distribution(achievements)
    print("\n🗂️ Achievement Categories:")
    for category, count in dist.items():
        print(f"  • {category}: {count} achievements")

    # Milestones
    milestones = dashboard._identify_career_milestones(achievements)
    print(f"\n🏆 Career Milestones: {len(milestones)} identified")
    for milestone in milestones[:3]:
        print(f"  • {milestone.title} ({milestone.impact})")

    # Momentum score
    momentum = dashboard._calculate_momentum_score(achievements)
    print(f"\n⚡ Current Momentum Score: {momentum}/100")


async def main():
    """Run all demos."""
    print("🎯 ACHIEVEMENT COLLECTOR - PHASE 3.1 ANALYTICS DEMO")
    print("=" * 60)
    print("Demonstrating advanced analytics capabilities\n")

    await demo_career_prediction()
    print("\n" + "-" * 60)

    demo_industry_benchmarking()
    print("\n" + "-" * 60)

    demo_performance_dashboard()

    print("\n" + "=" * 60)
    print("✅ Demo completed! These features are now available via REST API.")
    print("\nAPI Endpoints:")
    print("  • GET  /analytics/career-prediction")
    print("  • GET  /analytics/industry-benchmark")
    print("  • POST /analytics/compensation-benchmark")
    print("  • GET  /analytics/dashboard-metrics")
    print("  • GET  /analytics/executive-summary")
    print("  • GET  /analytics/trending-skills")


if __name__ == "__main__":
    asyncio.run(main())
