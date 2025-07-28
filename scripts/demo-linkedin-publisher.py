#!/usr/bin/env python3
"""Demo script for LinkedIn publisher functionality."""

import os
import sys
import asyncio

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


async def demo_linkedin_publisher():
    """Demonstrate LinkedIn publisher functionality."""
    from services.achievement_collector.publishers.linkedin_publisher import (
        LinkedInPublisher,
    )
    from services.achievement_collector.db.config import get_db, engine
    from services.achievement_collector.db.models import Base, Achievement

    print("🔍 LinkedIn Publisher Demo\n")

    # Create tables if needed
    Base.metadata.create_all(bind=engine)

    # Create publisher
    publisher = LinkedInPublisher()

    # Check configuration
    if publisher.is_configured():
        print("✅ LinkedIn is configured")
        print(f"   Person URN: {publisher.person_urn}")
    else:
        print("⚠️  LinkedIn not configured. Set these environment variables:")
        print("   - LINKEDIN_ACCESS_TOKEN")
        print("   - LINKEDIN_PERSON_URN")
        print("\n   Demo will continue with mock functionality...\n")

    # Get achievements from database
    db = next(get_db())
    try:
        # Get portfolio-ready achievements
        achievements = (
            db.query(Achievement)
            .filter(
                Achievement.portfolio_ready.is_(True), Achievement.impact_score >= 70
            )
            .order_by(Achievement.impact_score.desc())
            .limit(3)
            .all()
        )

        print(f"📊 Found {len(achievements)} portfolio-ready achievements:\n")

        for ach in achievements:
            print(f"🏆 {ach.title}")
            print(f"   Category: {ach.category}")
            print(f"   Impact: {ach.impact_score}/100")
            print(f"   Skills: {', '.join(ach.skills_demonstrated[:3])}")

            # Generate post content
            if publisher.is_configured():
                print("\n   🤖 Generating LinkedIn post...")
                content = await publisher._generate_post_content(ach)
                print("\n   📝 Post Preview (first 200 chars):")
                print(f"   {content['text'][:200]}...")
            else:
                # Show fallback post
                post = publisher._generate_fallback_post(ach)
                print("\n   📝 Fallback Post Preview:")
                print(f"   {post[:200]}...")

            print("\n" + "-" * 60 + "\n")

        # Demonstrate batch publishing logic
        print("📤 Batch Publishing Logic:")
        print("1. Check recent posts to avoid duplicates")
        print("2. Filter achievements by impact score (>= 70)")
        print("3. Generate engaging content with AI")
        print("4. Post to LinkedIn with proper formatting")
        print("5. Update database with post IDs")
        print("6. Wait between posts to avoid rate limits")

        # Show what would be published
        if achievements:
            print(f"\n✨ Would publish {min(3, len(achievements))} achievements")
            print("   (Limited to 3 per batch to avoid spam)")

    finally:
        db.close()

    print("\n✅ LinkedIn Publisher demo completed!")


async def main():
    """Run the demo."""
    print("🚀 Achievement Collector - LinkedIn Publisher Demo\n")

    # Set up test database
    os.environ["DATABASE_URL"] = f"sqlite:///{project_root}/test_achievements.db"

    await demo_linkedin_publisher()


if __name__ == "__main__":
    asyncio.run(main())
