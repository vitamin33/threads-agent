#!/usr/bin/env python3
"""
Runner script for Historical PR Analysis
CRA-298 Implementation

This script analyzes your threads-agent repository PRs for portfolio validation.
"""

import asyncio
import os
from historical_pr_analyzer import HistoricalPRAnalyzer


async def analyze_threads_agent():
    """Analyze the threads-agent repository for portfolio metrics"""

    # Configuration
    OWNER = "vitamin33"  # Your GitHub username
    REPO = "threads-agent"  # Your repository name

    print("🚀 Starting Historical PR Analysis for Threads-Agent")
    print(f"Repository: {OWNER}/{REPO}")
    print("-" * 50)

    # Initialize analyzer
    analyzer = HistoricalPRAnalyzer(github_token=os.getenv("GITHUB_TOKEN"))

    try:
        # Run analysis
        pr_metrics, business_values = await analyzer.analyze_repository(OWNER, REPO)

        # Export results
        analyzer.export_results(pr_metrics, business_values)

        # Display key metrics for AI Job Strategy
        total_value = sum(bv.portfolio_value for bv in business_values)
        avg_roi = sum(bv.roi_percent for bv in business_values) / len(business_values)
        ai_ml_prs = [bv for bv in business_values if bv.value_category == "ai_ml"]
        infrastructure_prs = [
            bv for bv in business_values if bv.value_category == "infrastructure"
        ]

        print("\n" + "=" * 60)
        print("📊 AI JOB STRATEGY PORTFOLIO METRICS")
        print("=" * 60)
        print(f"Total Portfolio Value: ${total_value:,.2f}")
        print("Target Range: $200,000 - $350,000")
        print(
            f"Status: {'✅ VALIDATED' if 200000 <= total_value <= 350000 else '⚠️ NEEDS ADJUSTMENT'}"
        )
        print()
        print("Key Metrics for $170-210K Remote Jobs:")
        print(f"• Total PRs Analyzed: {len(pr_metrics)}")
        print(f"• Average ROI: {avg_roi:.1f}%")
        print(
            f"• AI/ML PRs: {len(ai_ml_prs)} (${sum(bv.portfolio_value for bv in ai_ml_prs):,.0f} value)"
        )
        print(
            f"• Infrastructure PRs: {len(infrastructure_prs)} (${sum(bv.portfolio_value for bv in infrastructure_prs):,.0f} value)"
        )

        # Top 5 achievements for resume
        top_achievements = sorted(
            business_values, key=lambda x: x.portfolio_value, reverse=True
        )[:5]
        print("\n🏆 TOP 5 RESUME-WORTHY ACHIEVEMENTS:")
        for i, bv in enumerate(top_achievements, 1):
            pr = next(pr for pr in pr_metrics if pr.pr_number == bv.pr_number)
            print(f"{i}. PR #{bv.pr_number}: {pr.title[:60]}...")
            print(
                f"   💰 Value: ${bv.portfolio_value:,.0f} | ROI: {bv.roi_percent:.0f}% | Category: {bv.value_category}"
            )

        print("\n📁 Results exported to: pr_analysis_results/")
        print("\n🎯 Next Steps for AI Job Strategy:")
        print("1. Add these metrics to your portfolio website")
        print("2. Create LinkedIn posts about top achievements")
        print("3. Use in resume: 'Delivered $XXXk in business value'")
        print("4. Blog about technical implementation details")

        return True

    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        print("Make sure GITHUB_TOKEN is set in your environment")
        return False


if __name__ == "__main__":
    success = asyncio.run(analyze_threads_agent())
    exit(0 if success else 1)
