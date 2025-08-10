#!/usr/bin/env python3
"""
Example usage of the Multi-Platform Publishing Engine.

This script demonstrates how to use the publishing engine to distribute
content across multiple platforms with proper error handling.

Run from project root: python services/orchestrator/publishing/example_usage.py
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../"))

from services.orchestrator.publishing.engine import PublishingEngine
from services.orchestrator.db.models import ContentItem


async def main():
    """Demonstrate publishing engine usage."""

    print("🚀 Multi-Platform Publishing Engine Demo")
    print("=" * 50)

    # Initialize the publishing engine
    engine = PublishingEngine()

    print(f"📝 Registered platforms: {list(engine.adapters.keys())}")
    print()

    # Create sample content
    content_item = ContentItem(
        id=1,
        title="Building Scalable AI Systems: A Production Guide",
        content="""
In my experience building AI systems that serve millions of requests daily, 
I've learned that scalability isn't just about handling more data—it's about 
building systems that remain reliable, maintainable, and cost-effective as they grow.

Here are the key principles that made the difference:

1. **Design for Failure**: Every component will fail eventually
2. **Implement Circuit Breakers**: Prevent cascading failures
3. **Monitor Everything**: You can't fix what you can't see
4. **Optimize for the Common Case**: 80/20 rule applies to AI systems too
5. **Plan for Data Drift**: Models degrade over time

These lessons came from real production challenges, and implementing them 
transformed our AI pipeline from fragile prototype to robust production system.
        """.strip(),
        content_type="article",
        author_id="demo_author",
        status="ready",
        content_metadata={
            "tags": ["ai", "machine-learning", "scalability", "production", "systems"],
            "description": "Essential guide to building AI systems that scale",
            "industry_focus": "technology",
        },
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    print(f"📄 Content: {content_item.title}")
    print(f"📊 Tags: {content_item.content_metadata['tags']}")
    print()

    # Test Dev.to publishing (would need real API key)
    print("🔧 Testing Dev.to Publishing:")
    print("-" * 30)

    devto_result = await engine.publish_to_platform(
        content_item=content_item,
        platform="dev.to",
        platform_config={"api_key": "demo_key"},  # Would be real API key in production
    )

    print(f"✅ Success: {devto_result.success}")
    print(f"🌐 Platform: {devto_result.platform}")
    if devto_result.success:
        print(f"🔗 URL: {devto_result.url}")
        print(f"🆔 External ID: {devto_result.external_id}")
    else:
        print(f"❌ Error: {devto_result.error_message}")
    print()

    # Test LinkedIn publishing (manual workflow)
    print("💼 Testing LinkedIn Publishing:")
    print("-" * 30)

    linkedin_result = await engine.publish_to_platform(
        content_item=content_item,
        platform="linkedin",
        platform_config={},  # No API key needed for manual workflow
    )

    print(f"✅ Success: {linkedin_result.success}")
    print(f"🌐 Platform: {linkedin_result.platform}")
    if linkedin_result.success and linkedin_result.metadata:
        print(f"📝 Draft Created: {linkedin_result.metadata.get('draft', False)}")
        print(
            f"📋 Manual Posting Required: {linkedin_result.metadata.get('manual_posting_required', False)}"
        )

        # Show formatted content preview
        formatted_content = linkedin_result.metadata.get("formatted_content", "")
        preview = (
            formatted_content[:200] + "..."
            if len(formatted_content) > 200
            else formatted_content
        )
        print(f"📖 Preview: {preview}")
    print()

    # Test mock platform (Twitter example)
    print("🐦 Testing Mock Platform (Twitter):")
    print("-" * 35)

    twitter_result = await engine.publish_to_platform(
        content_item=content_item,
        platform="twitter",
        platform_config={"api_key": "demo_key"},
    )

    print(f"✅ Success: {twitter_result.success}")
    print(f"🌐 Platform: {twitter_result.platform}")
    print(f"🔗 Mock URL: {twitter_result.url}")
    print()

    # Demonstrate content validation
    print("🔍 Testing Content Validation:")
    print("-" * 30)

    # Test with invalid content (empty title)
    invalid_content = ContentItem(
        id=2,
        title="",  # Empty title should fail validation
        content="Valid content",
        content_type="article",
        author_id="demo_author",
        status="ready",
    )

    validation_result = await engine.publish_to_platform(
        content_item=invalid_content,
        platform="dev.to",
        platform_config={"api_key": "demo_key"},
    )

    print(f"❌ Invalid Content Result: {validation_result.success}")
    print(f"📝 Error Message: {validation_result.error_message}")
    print()

    # Show adapter capabilities
    print("⚙️ Adapter Capabilities:")
    print("-" * 25)

    for platform_name, adapter in engine.adapters.items():
        retry_support = "✅" if adapter.supports_retry else "❌"
        print(f"{platform_name:12} | Retry Support: {retry_support}")

    print()
    print("🎉 Demo Complete!")
    print("\nNext Steps:")
    print("1. Set up real API keys for production use")
    print("2. Configure Celery for async processing")
    print("3. Set up ContentSchedule records for scheduled publishing")
    print("4. Monitor publishing results and performance")


if __name__ == "__main__":
    asyncio.run(main())
