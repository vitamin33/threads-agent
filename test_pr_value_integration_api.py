#!/usr/bin/env python3
"""
Test script for PR Value Integration API endpoints.

This script tests the integration between PR value analyzer and achievement collector.
"""

import requests
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
TEST_PR_NUMBER = "91"  # The CRA-320 RAG Pipeline PR


def test_api_endpoint(
    endpoint: str, method: str = "GET", data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Test an API endpoint and return the response."""
    url = f"{BASE_URL}{endpoint}"

    print(f"\n🔍 Testing {method} {endpoint}...")

    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")

        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("   ✅ Success")
            return result
        else:
            print(f"   ❌ Failed: {response.text}")
            return None

    except requests.ConnectionError:
        print("   ❌ Connection failed - is the achievement collector running?")
        return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def print_metrics(metrics: Dict[str, Any]):
    """Pretty print metrics."""
    if not metrics:
        return

    print("\n📊 Metrics:")
    for key, value in metrics.items():
        if isinstance(value, (int, float)):
            if "percent" in key:
                print(f"   {key}: {value:.1f}%")
            elif "estimate" in key or "impact" in key:
                print(f"   {key}: ${value:,.0f}")
            else:
                print(f"   {key}: {value}")
        else:
            print(f"   {key}: {value}")


def main():
    """Run integration tests."""
    print("🚀 PR Value Integration API Test Suite")
    print("=" * 50)

    # Test 1: Health check
    health = test_api_endpoint("/health")
    if health:
        print(f"   Service: {health.get('service')}")
        print(f"   Status: {health.get('status')}")

    # Test 2: Get PR value metrics (preview without creating achievement)
    print("\n📈 Test 2: Get PR Value Metrics")
    metrics = test_api_endpoint(f"/pr-analysis/value-metrics/{TEST_PR_NUMBER}")
    if metrics:
        print(f"   PR Number: {metrics.get('pr_number')}")
        print(f"   Overall Score: {metrics.get('overall_score')}/10")
        print(
            f"   Qualifies for Achievement: {metrics.get('qualifies_for_achievement')}"
        )

        if metrics.get("business_metrics"):
            print_metrics(metrics["business_metrics"])

        if metrics.get("technical_metrics"):
            print("\n🔧 Technical Metrics:")
            perf = metrics["technical_metrics"].get("performance", {})
            for key, value in perf.items():
                print(f"   {key}: {value}")

    # Test 3: Get analysis thresholds
    print("\n📏 Test 3: Get Analysis Thresholds")
    thresholds = test_api_endpoint("/pr-analysis/thresholds")
    if thresholds:
        print(f"   Minimum Score: {thresholds.get('min_overall_score')}")
        print(f"   Portfolio Ready: {thresholds.get('portfolio_ready_threshold')}")
        print("\n   Score Levels:")
        for level, score in thresholds.get("score_levels", {}).items():
            print(f"      {level}: {score}")

    # Test 4: Analyze PR and create achievement
    print("\n🎯 Test 4: Analyze PR and Create Achievement")
    achievement = test_api_endpoint(
        f"/pr-analysis/analyze/{TEST_PR_NUMBER}", method="POST"
    )
    if achievement:
        print(f"   Achievement ID: {achievement.get('id')}")
        print(f"   Title: {achievement.get('title')}")
        print(f"   Category: {achievement.get('category')}")
        print(f"   Impact Score: {achievement.get('impact_score')}")
        print(f"   Portfolio Ready: {achievement.get('portfolio_ready')}")

        # Show some metrics
        if achievement.get("metrics_after"):
            print_metrics(achievement["metrics_after"])

    # Test 5: Batch analysis
    print("\n📦 Test 5: Batch Analysis")
    batch_result = test_api_endpoint(
        "/pr-analysis/batch-analyze",
        method="POST",
        data={"pr_numbers": ["90", "91", "92"]},
    )
    if batch_result:
        print(f"   Total Processed: {batch_result.get('total_processed')}")
        results = batch_result.get("results", {})
        print(f"   Successful: {len(results.get('successful', []))}")
        print(f"   Skipped: {len(results.get('skipped', []))}")
        print(f"   Failed: {len(results.get('failed', []))}")

        # Show successful results
        for success in results.get("successful", []):
            print(f"\n   ✅ PR #{success['pr_number']}:")
            print(f"      Achievement ID: {success['achievement_id']}")
            print(f"      Score: {success['score']}/10")

    # Test 6: Check webhook endpoints
    print("\n🔗 Test 6: Webhook Endpoints")
    webhook_health = test_api_endpoint("/webhooks/health")
    if webhook_health:
        print(f"   GitHub Configured: {webhook_health.get('github_configured')}")
        print(
            f"   Supported Events: {', '.join(webhook_health.get('supported_events', []))}"
        )

    # Test 7: Check existing achievements
    print("\n📚 Test 7: Check Existing Achievements")
    achievements = test_api_endpoint("/achievements?source_type=github_pr&limit=5")
    if achievements:
        print(f"   Found {len(achievements)} GitHub PR achievements")

        for ach in achievements[:3]:  # Show first 3
            print(f"\n   📌 {ach.get('title')}")
            print(f"      Source: {ach.get('source_id')}")
            print(f"      Score: {ach.get('impact_score')}")

            # Check if has value analysis
            metadata = ach.get("metadata", {})
            if metadata.get("value_analysis"):
                print("      ✅ Has value analysis")
            else:
                print("      ⚠️  No value analysis")

    print("\n" + "=" * 50)
    print("✅ Integration tests completed!")
    print("\nNext steps:")
    print("1. Run a real PR through the GitHub webhook")
    print("2. Check GitHub Actions workflow execution")
    print("3. Run the enrichment script for historical PRs")


if __name__ == "__main__":
    main()
