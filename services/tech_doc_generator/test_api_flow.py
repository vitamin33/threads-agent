#!/usr/bin/env python3
"""Test the API flow for LinkedIn manual publishing"""

import asyncio
import sys

sys.path.append(".")

from app.models.article import ArticleContent, Platform
from app.services.platform_publisher import PlatformPublisher


# Mock settings for testing
class MockSettings:
    def __init__(self):
        self.devto_api_key = None
        self.linkedin_access_token = None
        self.twitter_api_key = None
        self.threads_access_token = None

        # Add other required settings
        self.openai_api_key = "test"
        self.github_token = "test"


async def test_api_flow():
    """Test the full API flow for LinkedIn publishing"""

    print("🚀 Testing Full API Flow for LinkedIn Publishing")
    print("=" * 60)

    # Create sample article
    article = ArticleContent(
        title="How AI Transformed My Developer Portfolio",
        subtitle="From vague claims to concrete metrics",
        content="""
I used to struggle in interviews when asked about my impact. Now I have concrete numbers:
- Reduced infrastructure costs by $312/month
- Improved API response time by 2.3 seconds
- Increased code coverage from 45% to 87%

The Achievement Collector analyzes every PR and extracts business value automatically.
        """.strip(),
        insights=[
            "Automatic PR analysis saves 10 hours/week",
            "Concrete metrics increased interview success rate by 3x",
            "Portfolio now shows $47k/year in delivered value",
        ],
        tags=["ai", "portfolio", "career", "mlops"],
    )

    # Initialize publisher (it gets settings internally)
    publisher = PlatformPublisher()

    print("\n📤 Publishing to LinkedIn...")
    try:
        result = await publisher.publish_to_platform(
            platform=Platform.LINKEDIN, content=article
        )

        print("\n✅ Publishing Result:")
        print(f"Success: {result['success']}")
        if "platform" in result:
            print(f"Platform: {result['platform']}")
        if "draft_id" in result:
            print(f"Draft ID: {result['draft_id']}")
        if "manual_required" in result:
            print(f"Manual Required: {result['manual_required']}")

        print("\n📋 Instructions:")
        for i, instruction in enumerate(result["instructions"], 1):
            print(f"   {i}. {instruction}")

        print("\n📄 Generated Content:")
        print("-" * 60)
        print(
            result["content"][:500] + "..."
            if len(result["content"]) > 500
            else result["content"]
        )
        print("-" * 60)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_api_flow())
