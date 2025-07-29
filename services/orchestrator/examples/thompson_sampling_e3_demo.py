#!/usr/bin/env python3
"""
Demo script showing Thompson Sampling with E3 Engagement Predictor integration.

This demonstrates how E3 predictions are used as informed priors for better
variant selection, especially for new variants with no performance history.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from services.orchestrator.thompson_sampling import (
    select_top_variants_with_engagement_predictor,
)


def main():
    """Run demo of Thompson Sampling with E3 integration."""

    # Example variants with different quality levels and performance history
    variants = [
        {
            "variant_id": "proven_winner",
            "dimensions": {
                "hook_style": "question",
                "emotion": "curiosity",
                "length": "short",
                "cta": "learn_more",
            },
            "performance": {
                "impressions": 1000,
                "successes": 80,  # 8% engagement rate
            },
            "sample_content": "Ever wondered why 90% of startups fail? Here's the shocking truth...",
        },
        {
            "variant_id": "underperformer",
            "dimensions": {
                "hook_style": "statement",
                "emotion": "neutral",
                "length": "long",
                "cta": "follow_now",
            },
            "performance": {
                "impressions": 500,
                "successes": 10,  # 2% engagement rate
            },
            "sample_content": "Business is important for the economy.",
        },
        {
            "variant_id": "new_high_quality",
            "dimensions": {
                "hook_style": "story",
                "emotion": "excitement",
                "length": "medium",
                "cta": "share_thoughts",
            },
            "performance": {
                "impressions": 0,
                "successes": 0,  # No history yet
            },
            "sample_content": "I was broke at 25. By 30, I built a $10M business. Here's the counterintuitive strategy that changed everything...",
        },
        {
            "variant_id": "new_low_quality",
            "dimensions": {
                "hook_style": "command",
                "emotion": "urgency",
                "length": "short",
                "cta": "buy_now",
            },
            "performance": {
                "impressions": 0,
                "successes": 0,  # No history yet
            },
            "sample_content": "Buy now.",
        },
        {
            "variant_id": "new_medium_quality",
            "dimensions": {
                "hook_style": "question",
                "emotion": "curiosity",
                "length": "medium",
                "cta": "comment_below",
            },
            "performance": {
                "impressions": 0,
                "successes": 0,  # No history yet
            },
            "sample_content": "What's your biggest productivity challenge? I'm curious to hear your thoughts.",
        },
    ]

    print("🎯 Thompson Sampling with E3 Engagement Predictor Demo\n")
    print("📊 Variant Performance:")
    print("-" * 60)

    for variant in variants:
        perf = variant["performance"]
        if perf["impressions"] > 0:
            engagement_rate = (perf["successes"] / perf["impressions"]) * 100
            print(
                f"{variant['variant_id']:20} | {perf['impressions']:4} impressions | {engagement_rate:.1f}% ER"
            )
        else:
            print(f"{variant['variant_id']:20} | No history (NEW)")

    print("\n🤖 Running variant selection with E3 predictions...")

    # Select top 3 variants using E3-enhanced Thompson Sampling
    selected = select_top_variants_with_engagement_predictor(variants, top_k=3)

    print("\n✅ Selected variants (top 3):")
    print("-" * 60)

    for i, variant_id in enumerate(selected, 1):
        variant = next(v for v in variants if v["variant_id"] == variant_id)
        print(f"{i}. {variant_id}")
        print(f"   Hook: {variant['sample_content'][:60]}...")
        print()

    print("\n💡 Key Insights:")
    print("- E3 helps identify high-quality new variants without waiting for data")
    print("- Proven winners still get selected based on their track record")
    print("- Low-quality content (even with no history) gets deprioritized")
    print("- The algorithm balances exploration of new variants with exploitation")


if __name__ == "__main__":
    main()
