#!/usr/bin/env python3
"""
Script to track your published dev.to article

Usage:
    python track_devto_article.py --url "your-devto-article-url" --title "Your Article Title"
"""

import asyncio
import httpx
import argparse
from datetime import datetime
import json


async def track_devto_article(article_url: str, title: str):
    """Track a published dev.to article"""

    print("🚀 Tracking Dev.to Article")
    print("=" * 50)
    print(f"📄 Title: {title}")
    print(f"🔗 URL: {article_url}")
    print()

    # Extract article info (in production, this would parse the dev.to article)
    print("📋 Please provide additional article details:")

    # Get tags from user input
    tags_input = input("Enter article tags (comma-separated): ").strip()
    article_tags = (
        [tag.strip() for tag in tags_input.split(",")]
        if tags_input
        else ["technical-writing"]
    )

    # Get reading time estimate
    reading_time_input = input("Estimated reading time (minutes, default 5): ").strip()
    try:
        reading_time = int(reading_time_input) if reading_time_input else 5
    except ValueError:
        reading_time = 5

    # Get publication date
    pub_date_input = input("Publication date (YYYY-MM-DD, default today): ").strip()
    if pub_date_input:
        try:
            pub_date = datetime.strptime(pub_date_input, "%Y-%m-%d").isoformat()
        except ValueError:
            pub_date = datetime.now().isoformat()
    else:
        pub_date = datetime.now().isoformat()

    # Prepare tracking data
    tracking_data = {
        "title": title,
        "url": article_url,
        "published_date": pub_date,
        "tags": article_tags,
        "reading_time_minutes": reading_time,
    }

    # Send to tech-doc-generator service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8001/manual-publish/devto/track-published",
                json=tracking_data,
                timeout=10.0,
            )

            if response.status_code == 200:
                result = response.json()
                print("✅ Article tracked successfully!")
                print(f"📋 Tracking ID: {result['tracking_id']}")
                print()
                print("📈 Next Steps:")
                for step in result["next_steps"]:
                    print(f"   • {step}")
                print()

                # Show analytics endpoint
                tracking_id = result["tracking_id"]
                print(
                    f"📊 Analytics URL: http://localhost:8001/manual-publish/devto/analytics/{tracking_id}"
                )

                return result

            else:
                print(f"❌ Failed to track article: {response.status_code}")
                print(f"Response: {response.text}")
                return None

    except httpx.ConnectError:
        print("❌ Could not connect to tech-doc-generator service")
        print("Make sure the service is running on http://localhost:8001")
        return None

    except Exception as e:
        print(f"❌ Error tracking article: {str(e)}")
        return None


async def get_devto_analytics(tracking_id: str):
    """Get analytics for tracked dev.to article"""

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://localhost:8001/manual-publish/devto/analytics/{tracking_id}",
                timeout=10.0,
            )

            if response.status_code == 200:
                analytics = response.json()

                print("📊 Current Analytics:")
                print(f"   👀 Views: {analytics['current_metrics']['views']:,}")
                print(f"   ❤️  Reactions: {analytics['current_metrics']['reactions']}")
                print(f"   💬 Comments: {analytics['current_metrics']['comments']}")
                print(
                    f"   📈 Engagement Rate: {analytics['current_metrics']['engagement_rate']}%"
                )
                print(
                    f"   ⏱️  Reading Time: {analytics['current_metrics']['reading_time']} min"
                )
                print()

                return analytics

            else:
                print(f"❌ Failed to get analytics: {response.status_code}")
                return None

    except Exception as e:
        print(f"❌ Error getting analytics: {str(e)}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Track dev.to article")
    parser.add_argument("--url", required=True, help="Dev.to article URL")
    parser.add_argument("--title", required=True, help="Article title")
    parser.add_argument("--analytics", help="Get analytics for tracking ID")

    args = parser.parse_args()

    if args.analytics:
        # Get analytics for existing tracking ID
        asyncio.run(get_devto_analytics(args.analytics))
    else:
        # Track new article
        result = asyncio.run(track_devto_article(args.url, args.title))

        if result:
            print("\n🎯 AI Job Strategy Impact:")
            print("   • Content creation demonstrates technical communication skills")
            print("   • Published articles show thought leadership")
            print("   • Engagement metrics prove ability to reach developer audience")
            print("   • Achievement added to portfolio tracking system")


if __name__ == "__main__":
    main()
