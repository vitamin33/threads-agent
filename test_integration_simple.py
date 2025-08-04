#!/usr/bin/env python3
"""
Simple integration test for PR value analyzer and achievement collector.
"""

import json
import os


def create_mock_analysis():
    """Create a mock PR analysis result for testing."""
    analysis = {
        "pr_number": "91",
        "timestamp": "2025-01-25T10:00:00",
        "business_metrics": {
            "throughput_improvement_percent": 150.5,
            "infrastructure_savings_estimate": 80000,
            "user_experience_score": 9,
            "roi_year_one_percent": 234,
            "payback_period_months": 5.1,
        },
        "technical_metrics": {
            "performance": {
                "peak_rps": 673.9,
                "latency_ms": 50,
                "success_rate": 100,
                "test_coverage": 95,
            },
            "code_metrics": {
                "files_changed": 25,
                "lines_added": 1500,
                "lines_deleted": 200,
                "code_churn": 1700,
            },
            "innovation_score": 8.5,
        },
        "achievement_tags": [
            "high_performance_implementation",
            "cost_optimization",
            "kubernetes_deployment",
            "production_ready",
        ],
        "kpis": {
            "performance_score": 6.739,
            "quality_score": 9.5,
            "business_value_score": 7.8,
            "innovation_score": 8.5,
            "overall_score": 8.1,
        },
        "future_impact": {
            "revenue_impact_3yr": 425000,
            "competitive_advantage": "high",
            "market_differentiation": "performance_leader",
        },
    }

    # Save analysis file
    with open("pr_91_value_analysis.json", "w") as f:
        json.dump(analysis, f, indent=2)

    # Save achievement format
    os.makedirs(".achievements", exist_ok=True)
    achievement_data = {
        "pr_number": "91",
        "timestamp": analysis["timestamp"],
        "tags": analysis["achievement_tags"],
        "metrics": {
            **analysis["business_metrics"],
            **analysis["technical_metrics"]["performance"],
            "innovation_score": analysis["technical_metrics"]["innovation_score"],
        },
        "kpis": analysis["kpis"],
        "integration_ready": True,
        "schema_version": "2.0",
    }

    with open(".achievements/pr_91_achievement.json", "w") as f:
        json.dump(achievement_data, f, indent=2)

    return analysis


def test_integration():
    """Test the integration components."""
    print("🚀 Testing PR Value Analyzer Integration")
    print("=" * 50)

    # Create mock data
    print("\n📊 Creating mock PR analysis data...")
    analysis = create_mock_analysis()
    print("   ✅ Created pr_91_value_analysis.json")
    print("   ✅ Created .achievements/pr_91_achievement.json")

    # Display key metrics
    print("\n📈 Key Metrics:")
    print(f"   Overall Score: {analysis['kpis']['overall_score']}/10")
    print(f"   ROI: {analysis['business_metrics']['roi_year_one_percent']}%")
    print(
        f"   Infrastructure Savings: ${analysis['business_metrics']['infrastructure_savings_estimate']:,}"
    )
    print(f"   Peak RPS: {analysis['technical_metrics']['performance']['peak_rps']}")

    # Check if qualifies for achievement
    print("\n🎯 Achievement Status:")
    score = analysis["kpis"]["overall_score"]
    if score >= 6.0:
        print(f"   ✅ Qualifies for achievement (score: {score})")
        if score >= 7.0:
            print("   🌟 Portfolio ready!")
    else:
        print(f"   ❌ Below threshold (score: {score})")

    # Show integration points
    print("\n🔗 Integration Points:")
    print("   1. GitHub Webhook → processes PR merge")
    print("   2. PR Value Analyzer → calculates metrics")
    print("   3. Achievement Collector → creates enriched achievement")
    print("   4. GitHub Actions → posts analysis comment")

    # Test file structure
    print("\n📁 Verifying File Structure:")
    files_to_check = [
        "scripts/pr-value-analyzer.py",
        "scripts/enrich-achievements-with-pr-value.py",
        ".github/workflows/pr-value-analysis.yml",
        "services/achievement_collector/services/pr_value_analyzer_integration.py",
        "services/achievement_collector/api/routes/pr_analysis.py",
        "docs/achievement-pr-value-integration.md",
    ]

    all_files_exist = True
    for file in files_to_check:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file}")
            all_files_exist = False

    # Summary
    print("\n" + "=" * 50)
    if all_files_exist:
        print("✅ All integration components are in place!")
    else:
        print("⚠️  Some files are missing")

    print("\n📋 Next Steps:")
    print(
        "1. Start achievement collector: cd services/achievement_collector && uvicorn main:app"
    )
    print("2. Run API tests: python3 test_pr_value_integration_api.py")
    print("3. Create a test PR to verify GitHub Actions workflow")
    print(
        "4. Enrich historical PRs: python3 scripts/enrich-achievements-with-pr-value.py"
    )


if __name__ == "__main__":
    test_integration()
