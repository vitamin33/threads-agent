#!/usr/bin/env python3
"""
Automated publishing workflow script
Fetches achievements → Generates content → Publishes to platforms
"""

import asyncio
import httpx
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TECH_DOC_API = os.getenv("TECH_DOC_API_URL", "http://localhost:8001")
DEVTO_API_KEY = os.getenv("DEVTO_API_KEY")
THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")


async def run_publishing_workflow(test_mode: bool = True):
    """Execute the complete auto-publishing workflow"""

    print("🚀 Starting Auto-Publishing Workflow\n")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # 1. Preview what content will be generated
            print("📋 Fetching recent achievements and generating preview...")
            preview_response = await client.get(
                f"{TECH_DOC_API}/api/auto-publish/achievement-preview",
                params={"days_lookback": 14, "min_business_value": 50000},
            )

            if preview_response.status_code != 200:
                print(f"❌ Failed to generate preview: {preview_response.text}")
                return

            preview = preview_response.json()

            if not preview["success"]:
                print(f"❌ {preview['message']}")
                return

            # Display preview
            print("\n✅ Content Preview:")
            print(f"   Title: {preview['preview']['title']}")
            print(f"   Word Count: {preview['preview']['word_count']}")
            print(f"   Insights: {len(preview['preview']['insights'])}")
            print(f"   Code Examples: {preview['preview']['code_examples']}")
            print(f"   Tags: {', '.join(preview['preview']['tags'])}")
            print(f"   Business Value: ${preview['total_business_value']:,.0f}")
            print(f"\n   Preview: {preview['preview']['first_paragraph'][:200]}...")

            # 2. Ask for confirmation
            if not test_mode:
                confirm = input("\n📢 Proceed with publishing? (y/n): ")
                if confirm.lower() != "y":
                    print("❌ Publishing cancelled")
                    return

            # 3. Determine available platforms
            platforms = []

            if DEVTO_API_KEY:
                platforms.append("devto")
                print("✅ Dev.to API key found")
            else:
                print("⚠️  Dev.to API key not found")

            if THREADS_ACCESS_TOKEN:
                platforms.append("threads")
                print("✅ Threads access token found")
            else:
                print("⚠️  Threads access token not found")

            platforms.append("linkedin")  # Always include for manual workflow
            print("✅ LinkedIn manual workflow available")

            if not platforms:
                print("\n❌ No publishing platforms configured!")
                return

            # 4. Execute auto-publish
            print(f"\n🚀 Publishing to: {', '.join(platforms)}")
            print(f"   Test Mode: {test_mode}")

            publish_response = await client.post(
                f"{TECH_DOC_API}/api/auto-publish/achievement-content",
                params={
                    "platforms": platforms,
                    "test_mode": test_mode,
                    "days_lookback": 14,
                    "min_business_value": 50000,
                },
            )

            if publish_response.status_code != 200:
                print(f"\n❌ Publishing failed: {publish_response.text}")
                return

            result = publish_response.json()

            # 5. Display results
            print(f"\n📊 Publishing Results:")
            print(f"   Status: {result['result']['status']}")

            if result["result"]["content"]:
                print(f"\n   📝 Generated Content:")
                print(f"      Title: {result['result']['content']['title']}")
                print(f"      Word Count: {result['result']['content']['word_count']}")
                print(f"      Insights: {result['result']['content']['insights']}")

            print(f"\n   🌐 Platform Results:")
            for platform, platform_result in result["result"]["platforms"].items():
                if platform_result.get("success"):
                    print(f"      ✅ {platform}: Success")
                    if platform == "devto":
                        print(f"         URL: {platform_result.get('url')}")
                        print(f"         ID: {platform_result.get('id')}")
                    elif platform == "linkedin":
                        print(f"         Draft ID: {platform_result.get('draft_id')}")
                        print(
                            f"         Instructions: {platform_result.get('message')}"
                        )
                    elif platform == "threads":
                        print(f"         Post ID: {platform_result.get('id')}")
                        print(f"         URL: {platform_result.get('url')}")
                else:
                    print(f"      ❌ {platform}: {platform_result.get('error')}")

            print(f"\n✅ Workflow completed successfully!")

        except Exception as e:
            print(f"\n❌ Workflow error: {str(e)}")


async def check_platform_status():
    """Check status of all publishing platforms"""

    print("🔍 Checking Platform Configuration\n")

    # Check Dev.to
    if DEVTO_API_KEY:
        print(f"✅ Dev.to API Key: {DEVTO_API_KEY[:10]}...")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://dev.to/api/users/me", headers={"api-key": DEVTO_API_KEY}
                )
                if response.status_code == 200:
                    user = response.json()
                    print(f"   Connected as: @{user.get('username')}")
                else:
                    print(f"   ❌ Invalid API key")
        except Exception as e:
            print(f"   ❌ Connection error: {e}")
    else:
        print("❌ Dev.to API Key: Not configured")

    # Check Threads
    if THREADS_ACCESS_TOKEN:
        print(f"\n✅ Threads Access Token: {THREADS_ACCESS_TOKEN[:20]}...")
        threads_user_id = os.getenv("THREADS_USER_ID")
        if threads_user_id:
            print(f"   User ID: {threads_user_id}")
        else:
            print("   ❌ THREADS_USER_ID not configured")
    else:
        print("\n❌ Threads Access Token: Not configured")

    # LinkedIn is always manual
    print("\n✅ LinkedIn: Manual workflow (no API key needed)")

    # Check service availability
    print(f"\n🔍 Checking Tech Doc Generator Service...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{TECH_DOC_API}/health")
            if response.status_code == 200:
                print(f"✅ Service is healthy at {TECH_DOC_API}")
            else:
                print(f"❌ Service unhealthy: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to service: {e}")
        print(f"   Make sure tech_doc_generator is running on {TECH_DOC_API}")


async def main():
    """Main entry point"""

    import argparse

    parser = argparse.ArgumentParser(description="Auto-publish achievement content")
    parser.add_argument(
        "--check", action="store_true", help="Check platform configuration"
    )
    parser.add_argument(
        "--publish", action="store_true", help="Run publishing workflow"
    )
    parser.add_argument(
        "--live", action="store_true", help="Publish live (not test mode)"
    )

    args = parser.parse_args()

    if args.check:
        await check_platform_status()
    elif args.publish:
        await run_publishing_workflow(test_mode=not args.live)
    else:
        # Default: check status then ask to publish
        await check_platform_status()
        print("\n" + "=" * 50)
        proceed = input("\nProceed with test publishing? (y/n): ")
        if proceed.lower() == "y":
            await run_publishing_workflow(test_mode=True)


if __name__ == "__main__":
    asyncio.run(main())
