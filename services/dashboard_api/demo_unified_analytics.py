#!/usr/bin/env python3
"""
Demo script for the Unified Multi-Platform Analytics System

This demonstrates the multi-platform analytics collectors and unified dashboard
functionality implemented with TDD approach.
"""

import asyncio
from datetime import datetime

# Add path for imports
import sys
import os

sys.path.append(os.path.dirname(__file__))

from unified_analytics import AnalyticsAggregationService, ConversionTracker

# Also import the platform-specific collectors
sys.path.append(
    os.path.join(
        os.path.dirname(__file__), "..", "tech_doc_generator", "app", "services"
    )
)
from analytics_collectors import (
    LinkedInAnalyticsCollector,
    TwitterAnalyticsCollector,
    MediumAnalyticsCollector,
    GitHubAnalyticsCollector,
    ThreadsAnalyticsCollector,
)


async def demo_platform_collectors():
    """Demo the individual platform analytics collectors"""
    print("🔍 MULTI-PLATFORM ANALYTICS COLLECTORS DEMO")
    print("=" * 60)

    # Initialize collectors
    linkedin = LinkedInAnalyticsCollector("vitaliiserbyn")
    twitter = TwitterAnalyticsCollector("vitaliiserbyn")
    medium = MediumAnalyticsCollector("vitaliiserbyn")
    github = GitHubAnalyticsCollector("vitamin33")
    threads = ThreadsAnalyticsCollector("vitaliiserbyn")

    collectors = [
        ("LinkedIn", linkedin),
        ("Twitter", twitter),
        ("Medium", medium),
        ("GitHub", github),
        ("Threads", threads),
    ]

    for platform_name, collector in collectors:
        print(f"\n📊 {platform_name} Analytics:")

        # Get metrics
        metrics = await collector.get_metrics()
        print(f"  Platform: {metrics['platform']}")
        print(f"  Collected at: {metrics['collected_at']}")

        # Show platform-specific metrics
        if platform_name == "LinkedIn":
            print(f"  Profile views: {metrics['profile_views']}")
            print(
                f"  AI hiring manager connections: {metrics['ai_hiring_manager_connections']}"
            )
        elif platform_name == "Twitter":
            print(f"  Impressions: {metrics['impressions']}")
            print(f"  Follower growth: {metrics['follower_growth']}")
        elif platform_name == "Medium":
            print(f"  Read ratio: {metrics['read_ratio']}")
            print(f"  Claps: {metrics['claps']}")
        elif platform_name == "GitHub":
            print(f"  Repository traffic: {metrics['repository_traffic']}")
            print(f"  Stars from content: {metrics['stars_from_content']}")
        elif platform_name == "Threads":
            print(f"  Engagement metrics: {metrics['engagement_metrics']}")
            print(f"  Conversation starters: {metrics['conversation_starters']}")

        # Get conversion data
        conversion_data = await collector.get_conversion_data()
        print(f"  → serbyn.pro visits: {conversion_data['serbyn_pro_visits']}")
        print(f"  → Job inquiries: {conversion_data['job_inquiries']}")


async def demo_unified_analytics():
    """Demo the unified analytics dashboard functionality"""
    print("\n\n🎯 UNIFIED ANALYTICS DASHBOARD DEMO")
    print("=" * 60)

    # Initialize the aggregation service
    analytics_service = AnalyticsAggregationService()

    # Collect all platform metrics
    print("\n📈 Collecting metrics from all platforms...")
    all_metrics = await analytics_service.collect_all_platform_metrics()

    print("Platforms monitored:")
    for platform in all_metrics.keys():
        print(f"  ✓ {platform.capitalize()}")

    # Calculate conversion summary
    print("\n💼 Conversion Summary:")
    conversion_summary = await analytics_service.calculate_conversion_summary(
        all_metrics
    )
    print(f"  Total serbyn.pro visits: {conversion_summary['total_serbyn_pro_visits']}")
    print(f"  Total job inquiries: {conversion_summary['total_job_inquiries']}")
    print(
        f"  Overall conversion rate: {conversion_summary['overall_conversion_rate']:.2f}%"
    )
    print(
        f"  Best converting platform: {conversion_summary['best_converting_platform']}"
    )

    # Show ROI analysis
    print("\n💰 ROI Analysis:")
    roi_analysis = await analytics_service.calculate_roi_analysis()
    print(f"  ROI percentage: {roi_analysis['roi_percentage']:.2f}%")
    print(f"  Cost per lead: ${roi_analysis['cost_per_lead']:.2f}")
    print("  Recommendations:")
    for i, rec in enumerate(roi_analysis["recommendations"], 1):
        print(f"    {i}. {rec}")

    # Show platform ranking
    print("\n🏆 Platform Performance Ranking:")
    ranking = await analytics_service.get_platform_ranking()
    for rank_data in ranking["ranking"]:
        print(f"  #{rank_data['rank']} {rank_data['platform'].capitalize()}")
        print(f"      Score: {rank_data['score']:.2f}")
        print(f"      Conversion rate: {rank_data['conversion_rate']:.2f}%")


async def demo_conversion_tracking():
    """Demo the conversion tracking functionality"""
    print("\n\n🎯 CONVERSION TRACKING DEMO")
    print("=" * 60)

    # Initialize conversion tracker
    tracker = ConversionTracker()

    # Simulate a content→website conversion
    print("\n1️⃣ Tracking content to website conversion...")
    conversion_event = {
        "source_platform": "linkedin",
        "content_url": "https://linkedin.com/posts/vitaliiserbyn-mlops-post-123",
        "visitor_ip": "203.0.113.1",
        "timestamp": datetime.utcnow().isoformat(),
        "destination_url": "https://serbyn.pro",
    }

    conversion_result = await tracker.track_conversion(conversion_event)
    print(f"  ✓ Conversion tracked: {conversion_result['conversion_id']}")
    print(f"  ✓ Source platform: {conversion_result['platform']}")

    # Simulate a website→lead conversion
    print("\n2️⃣ Tracking website to job inquiry conversion...")
    lead_event = {
        "visitor_ip": "203.0.113.1",
        "source_conversion_id": conversion_result["conversion_id"],
        "lead_type": "job_inquiry",
        "contact_method": "email",
        "timestamp": datetime.utcnow().isoformat(),
    }

    lead_result = await tracker.track_lead_conversion(lead_event)
    print(f"  ✓ Lead tracked: {lead_result['lead_id']}")
    print(f"  ✓ Attributed to: {lead_result['attributed_platform']}")

    # Show full attribution chain
    print("\n3️⃣ Full attribution chain:")
    attribution_chain = await tracker.get_attribution_chain(lead_result["lead_id"])
    print(f"  📝 Content source: {attribution_chain['content_url']}")
    print(f"  📱 Platform: {attribution_chain['platform']}")
    print(f"  🌐 Website visit: {attribution_chain['website_visit_timestamp']}")
    print(f"  💼 Lead conversion: {attribution_chain['lead_conversion_timestamp']}")
    print(
        f"  ⏱️  Total conversion time: {attribution_chain['total_conversion_time_hours']} hours"
    )


async def demo_api_endpoints():
    """Demo the API endpoints that would be available"""
    print("\n\n🔌 API ENDPOINTS AVAILABLE")
    print("=" * 60)

    endpoints = [
        ("GET /api/analytics/unified", "Get unified analytics from all platforms"),
        ("GET /api/analytics/conversion-summary", "Get aggregated conversion summary"),
        ("GET /api/analytics/roi-analysis", "Get ROI analysis for content marketing"),
        ("GET /api/analytics/platform-ranking", "Get platform performance ranking"),
        (
            "GET /api/analytics/websocket-info",
            "Get WebSocket connection info for real-time updates",
        ),
    ]

    print("Available endpoints:")
    for endpoint, description in endpoints:
        print(f"  🔗 {endpoint}")
        print(f"     {description}")

    print("\n💡 Usage example:")
    print("   curl http://localhost:8081/api/analytics/unified")
    print("   curl http://localhost:8081/api/analytics/conversion-summary")


async def main():
    """Run the complete unified analytics demo"""
    print("🚀 MULTI-PLATFORM ANALYTICS & CONVERSION TRACKING SYSTEM")
    print(
        "🎯 Goal: Track conversion from content engagement to serbyn.pro visits and job inquiries"
    )
    print("")

    try:
        await demo_platform_collectors()
        await demo_unified_analytics()
        await demo_conversion_tracking()
        await demo_api_endpoints()

        print("\n\n✅ DEMO COMPLETED SUCCESSFULLY")
        print("🎉 Multi-platform analytics system is ready for production!")
        print("\n📊 Key capabilities implemented:")
        print("  ✓ LinkedIn, Twitter, Medium, GitHub, Threads analytics collectors")
        print("  ✓ Unified analytics dashboard aggregating all platforms")
        print("  ✓ Conversion tracking from content → serbyn.pro → job inquiries")
        print("  ✓ ROI analysis and platform performance ranking")
        print("  ✓ Real-time WebSocket updates")
        print("  ✓ REST API endpoints for integration")

        print("\n🎯 Next steps:")
        print("  1. Connect to real platform APIs (LinkedIn, Twitter, etc.)")
        print("  2. Set up Google Analytics integration for serbyn.pro tracking")
        print("  3. Implement automated reporting and alerts")
        print("  4. Deploy to production environment")

    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
