#!/usr/bin/env python3
"""
Test script for A/B Testing Infrastructure
Run this after deployment to verify the system works
"""

import asyncio
import sys
from pathlib import Path

# Add services to path
sys.path.append(str(Path(__file__).parent.parent))

from services.orchestrator.experiments import (
    ExperimentManager,
    StatisticalAnalyzer,
    ThompsonSampling,
)
from services.orchestrator.scheduler import ExperimentScheduler


async def test_statistical_analyzer():
    """Test statistical calculations"""
    print("🧮 Testing Statistical Analyzer...")

    analyzer = StatisticalAnalyzer()

    # Test sample size calculation
    sample_size = analyzer.calculate_sample_size(
        baseline_rate=0.05,
        minimum_effect=0.2,  # 20% improvement
        power=0.8,
        alpha=0.05,
    )
    print(f"  Required sample size: {sample_size}")

    # Test significance testing
    control_data = {"engagements_total": 50, "impressions_total": 1000}
    variant_data = {"engagements_total": 72, "impressions_total": 1000}

    result = analyzer.test_significance(control_data, variant_data)
    print(f"  P-value: {result['p_value']:.4f}")
    print(f"  Effect size: {result['effect_size']:.2%}")
    print(f"  Is significant: {result['is_significant']}")

    # Test Bayesian analysis
    prob = analyzer.calculate_bayesian_probability(control_data, variant_data)
    print(f"  Bayesian probability variant > control: {prob:.2%}")


def test_thompson_sampling():
    """Test multi-armed bandit"""
    print("\n🎰 Testing Thompson Sampling...")

    bandit = ThompsonSampling(3)

    # Simulate some data
    # Variant 0: poor (2% engagement)
    # Variant 1: good (6% engagement)
    # Variant 2: excellent (8% engagement)

    performance = [0.02, 0.06, 0.08]

    # Simulate 1000 pulls
    for _ in range(1000):
        selected = bandit.select_variant()
        success = np.random.random() < performance[selected]
        bandit.update(selected, success)

    # Check final allocation
    win_probs = bandit.get_win_probabilities()
    print(f"  Win probabilities: {[f'{p:.2%}' for p in win_probs]}")
    print(f"  Best variant should be #2: {win_probs.index(max(win_probs))}")


async def test_experiment_manager():
    """Test experiment creation and management"""
    print("\n🧪 Testing Experiment Manager...")

    manager = ExperimentManager()

    # Create test experiment
    experiment_id = manager.create_experiment(
        name="Test Hook Patterns",
        variant_ids=["test-variant-1", "test-variant-2"],
        persona_id="ai-jesus",
        config={"min_sample_size": 50, "max_duration_hours": 24},
    )

    print(f"  Created experiment: {experiment_id}")

    # Start experiment
    success = manager.start_experiment(experiment_id)
    print(f"  Started experiment: {success}")

    # Get stats
    stats = manager.get_experiment_stats(experiment_id)
    print(f"  Experiment status: {stats.get('status', 'Not found')}")
    print(f"  Variant count: {len(stats.get('variants', []))}")


def test_scheduler():
    """Test posting scheduler"""
    print("\n📅 Testing Posting Scheduler...")

    scheduler = ExperimentScheduler()

    # Get next posts (this will be empty without active experiments)
    posts = scheduler.schedule_next_posts(time_window_hours=1)
    print(f"  Scheduled posts: {len(posts)}")

    if posts:
        for i, post in enumerate(posts[:3]):  # Show first 3
            print(f"    {i + 1}. {post.persona_id} at {post.scheduled_time}")
            print(f"       Priority: {post.priority:.1f}")
    else:
        print("    No active experiments to schedule")


async def test_integration():
    """Test full integration workflow"""
    print("\n🔄 Testing Integration Workflow...")

    # This would test the full flow:
    # 1. Generate variants
    # 2. Create experiment
    # 3. Start experiment
    # 4. Schedule posts
    # 5. Update with results
    # 6. Check significance

    print("  Integration test would require full deployment")
    print("  Use API endpoints once system is running:")
    print("    POST /experiments/create")
    print("    POST /experiments/{id}/start")
    print("    GET /experiments/{id}/stats")
    print("    GET /experiments/scheduler/next-posts")


if __name__ == "__main__":
    print("🧪 Testing A/B Testing Infrastructure...")
    print("=" * 50)

    # Import numpy for Thompson sampling test
    try:
        import numpy as np

        # Run tests
        asyncio.run(test_statistical_analyzer())
        test_thompson_sampling()
        asyncio.run(test_experiment_manager())
        test_scheduler()
        asyncio.run(test_integration())

        print("\n✅ All tests completed!")
        print("\n🚀 Next steps:")
        print("  1. Deploy database migrations")
        print("  2. Start orchestrator service")
        print("  3. Create experiments via API")
        print("  4. Monitor with /experiments/{id}/stats")

    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("Install: pip install numpy scipy")
