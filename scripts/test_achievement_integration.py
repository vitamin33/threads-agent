#!/usr/bin/env python3
"""
Direct Achievement Collector Integration Test
Tests creating achievements with business value metrics
"""

import json
import urllib.request
import urllib.parse


def test_achievement_creation():
    """Test creating a single achievement with business metrics"""

    # Sample achievement based on your PR #91 (RAG Pipeline)
    achievement_data = {
        "title": "RAG Pipeline + Achievement Calculation Transparency",
        "description": """Production-ready RAG system with Qdrant integration, vector embeddings, and real-time search capabilities.
        
Business Impact: $43,680 portfolio value with 360% ROI
• Cost Savings: $36,000/year
• Productivity: 64 hours saved
• Performance: 105% improvement""",
        "category": "ai_ml_implementation",
        "impact_score": 95,  # High impact
        "technical_details": {
            "pr_number": 91,
            "lines_changed": 1700,
            "files_changed": 25,
            "implementation_time": "40 hours",
            "technologies": ["Python", "Qdrant", "FastAPI", "LangChain"],
        },
        "business_value": "$43,680 annual value | 360% ROI | $36,000 cost savings",
        "metrics": {
            "portfolio_value": 43680,
            "roi_percent": 360,
            "cost_savings": 36000,
            "productivity_hours": 64,
            "performance_improvement": 105,
        },
        "skills_demonstrated": [
            "Python",
            "RAG Systems",
            "Vector Databases",
            "AI/ML",
            "System Architecture",
            "Performance Optimization",
        ],
        "portfolio_ready": True,
        "tags": ["ai_ml", "rag", "high_value", "interview_ready"],
        "pr_number": "91",
        "completed_at": "2025-08-05T12:00:00Z",
    }

    print("🧪 Testing Achievement Collector Integration")
    print("=" * 60)

    # Check if API is running
    try:
        response = urllib.request.urlopen("http://localhost:8001/health")
        if response.status == 200:
            print("✅ Achievement Collector API is running")
    except:
        print("❌ Achievement Collector not running on port 8001")
        print("   Start with: just dev-start")
        return False

    # Create achievement
    try:
        data = json.dumps(achievement_data).encode("utf-8")
        request = urllib.request.Request(
            "http://localhost:8001/achievements",
            data=data,
            headers={"Content-Type": "application/json"},
        )

        with urllib.request.urlopen(request) as response:
            if response.status in [200, 201]:
                result = json.loads(response.read())
                print(f"✅ Created achievement #{result.get('id', 'N/A')}")
                print(f"   Title: {result.get('title', '')[:50]}...")
                print(
                    f"   Value: ${result.get('metrics', {}).get('portfolio_value', 0):,.0f}"
                )
                print(f"   ROI: {result.get('metrics', {}).get('roi_percent', 0)}%")
                return True
            else:
                print(f"❌ Failed to create achievement: {response.status}")
                return False

    except Exception as e:
        print(f"❌ Error creating achievement: {e}")
        return False


def test_portfolio_summary():
    """Test fetching portfolio summary with metrics"""
    print("\n🧪 Testing Portfolio Summary")
    print("=" * 60)

    try:
        # Get all achievements
        response = urllib.request.urlopen("http://localhost:8001/achievements")
        if response.status == 200:
            achievements = json.loads(response.read())

            # Calculate portfolio metrics
            total_value = 0
            total_roi = 0
            ai_ml_count = 0

            for achievement in achievements:
                metrics = achievement.get("metrics", {})
                if metrics:
                    total_value += metrics.get("portfolio_value", 0)
                    total_roi += metrics.get("roi_percent", 0)

                if achievement.get("category") == "ai_ml_implementation":
                    ai_ml_count += 1

            if achievements:
                avg_roi = total_roi / len(achievements)
                print("✅ Portfolio Summary:")
                print(f"   Total Achievements: {len(achievements)}")
                print(f"   Total Portfolio Value: ${total_value:,.0f}")
                print(f"   Average ROI: {avg_roi:.1f}%")
                print(f"   AI/ML Achievements: {ai_ml_count}")

                # Show top achievement
                if achievements:
                    top = max(
                        achievements,
                        key=lambda x: x.get("metrics", {}).get("portfolio_value", 0),
                    )
                    print("\n📊 Top Achievement:")
                    print(f"   {top.get('title', 'N/A')}")
                    print(
                        f"   Value: ${top.get('metrics', {}).get('portfolio_value', 0):,.0f}"
                    )

            return True

    except Exception as e:
        print(f"❌ Error fetching portfolio: {e}")
        return False


def test_pr_analysis_endpoint():
    """Test the PR analysis endpoint"""
    print("\n🧪 Testing PR Analysis Endpoint")
    print("=" * 60)

    # Test with a known PR
    pr_number = "92"  # Your AI Job Week 2 PR

    try:
        request = urllib.request.Request(
            f"http://localhost:8001/pr-analysis/value-metrics/{pr_number}",
            headers={"Content-Type": "application/json"},
        )

        with urllib.request.urlopen(request) as response:
            if response.status == 200:
                data = json.loads(response.read())
                print(f"✅ PR #{pr_number} Analysis:")

                if "metrics" in data:
                    metrics = data["metrics"]
                    print(f"   ROI: {metrics.get('roi', 0):.0f}%")
                    print(
                        f"   Value Score: {metrics.get('kpis', {}).get('business_value_score', 0)}/10"
                    )
                else:
                    print("   (Analysis endpoint returned data)")

                return True

    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"⚠️  PR #{pr_number} not analyzed yet")
        else:
            print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Error testing PR analysis: {e}")

    return False


def main():
    """Run all integration tests"""
    print("🚀 ACHIEVEMENT COLLECTOR INTEGRATION TEST")
    print("Testing business value metrics integration\n")

    tests_passed = 0
    tests_total = 3

    # Test 1: Create achievement
    if test_achievement_creation():
        tests_passed += 1

    # Test 2: Portfolio summary
    if test_portfolio_summary():
        tests_passed += 1

    # Test 3: PR analysis endpoint
    if test_pr_analysis_endpoint():
        tests_passed += 1

    # Summary
    print("\n" + "=" * 60)
    print(f"🏁 TEST RESULTS: {tests_passed}/{tests_total} passed")

    if tests_passed == tests_total:
        print("✅ All integration tests passed!")
        print("\n🎯 Your Achievement Collector is ready for:")
        print("   • Storing PR analysis results")
        print("   • Tracking portfolio value")
        print("   • Generating tech documentation")
        print("   • Creating portfolio website")
    else:
        print("⚠️  Some tests failed, but core functionality may still work")

    print("\n📝 Next Steps:")
    print("1. Import all historical PRs: python3 integrate_historical_prs.py")
    print("2. Generate tech docs from achievements")
    print("3. Export portfolio metrics for website")
    print("4. Use in job applications!")


if __name__ == "__main__":
    main()
