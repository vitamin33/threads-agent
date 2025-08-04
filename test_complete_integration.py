#!/usr/bin/env python3
"""
Test complete integration between achievement_collector and tech_doc_generator
"""

import asyncio
import httpx


async def test_complete_integration():
    """Test the full integration flow"""

    print("🧪 Testing Complete Achievement → Article Integration\n")

    achievement_url = "http://localhost:8090"
    tech_doc_url = "http://localhost:8091"

    async with httpx.AsyncClient() as client:
        # Step 1: Check integration endpoints exist
        print("1️⃣ Verifying integration endpoints...")
        try:
            # Check achievement collector endpoints
            ac_response = await client.get(f"{achievement_url}/docs")
            if ac_response.status_code == 200:
                print("✅ Achievement Collector API is accessible")

            # Test new integration endpoint
            test_response = await client.get(
                f"{achievement_url}/tech-doc-integration/content-ready"
            )
            if test_response.status_code == 200:
                ready = test_response.json()
                print(f"✅ Found {len(ready)} content-ready achievements")
            else:
                print("⚠️  Integration endpoints not yet deployed")

        except httpx.ConnectError:
            print("❌ Services not accessible. Run port-forward commands:")
            print("   kubectl port-forward svc/achievement-collector 8090:8090")
            print("   kubectl port-forward svc/tech-doc-generator 8091:8091")
            return

        # Step 2: Test optimized batch operations
        print("\n2️⃣ Testing optimized batch operations...")

        # Get some achievement IDs
        list_resp = await client.get(
            f"{achievement_url}/achievements/", params={"limit": 5}
        )
        if list_resp.status_code == 200:
            achievements = list_resp.json()
            if achievements:
                ids = [a["id"] for a in achievements[:3]]

                # Test batch get
                batch_resp = await client.post(
                    f"{achievement_url}/tech-doc-integration/batch-get",
                    json={"achievement_ids": ids},
                )

                if batch_resp.status_code == 200:
                    batch = batch_resp.json()
                    print(f"✅ Batch endpoint returned {len(batch)} achievements")

        # Step 3: Test content generation from achievement
        print("\n3️⃣ Testing content generation from achievement...")

        if achievements:
            # Pick the highest impact achievement
            best = max(achievements, key=lambda x: x.get("impact_score", 0))

            print(f"   Using achievement: {best['title']}")
            print(f"   Impact Score: {best.get('impact_score', 0)}")

            # Simulate tech_doc_generator request
            article_request = {
                "achievement_id": best["id"],
                "article_types": ["case_study", "technical_deep_dive"],
                "platforms": ["linkedin", "devto"],
            }

            print(
                f"   Would generate {len(article_request['article_types'])} x {len(article_request['platforms'])} = {len(article_request['article_types']) * len(article_request['platforms'])} articles"
            )

        # Step 4: Test company-targeted content
        print("\n4️⃣ Testing company-targeted content...")

        companies = ["notion", "anthropic", "jasper"]
        for company in companies:
            resp = await client.post(
                f"{achievement_url}/tech-doc-integration/company-targeted",
                params={"company_name": company, "limit": 3},
            )

            if resp.status_code == 200:
                targeted = resp.json()
                print(
                    f"✅ {company.capitalize()}: {len(targeted)} relevant achievements"
                )
                if targeted:
                    print(f"   Top match: {targeted[0]['title']}")

        # Step 5: Test content opportunities stats
        print("\n5️⃣ Checking content generation opportunities...")

        stats_resp = await client.get(
            f"{achievement_url}/tech-doc-integration/stats/content-opportunities"
        )
        if stats_resp.status_code == 200:
            stats = stats_json()
            print("📊 Content Opportunity Analysis:")
            print(f"   Total content-ready: {stats['total_content_ready']}")
            print(f"   High-impact (80+): {stats['high_impact_opportunities']}")
            print(f"   Recent (30 days): {stats['recent_achievements']}")
            print(f"   Unprocessed: {stats['unprocessed_achievements']}")

            if stats["total_content_ready"] > 0:
                potential_articles = (
                    stats["total_content_ready"] * 3
                )  # Average 3 articles per achievement
                print(
                    f"\n💡 Potential: ~{potential_articles} articles from your achievements!"
                )

    print("\n✅ Integration test complete!")
    print("\n🚀 Next Steps:")
    print("   1. Deploy the updated services to k8s")
    print("   2. Set up automated content generation schedule")
    print("   3. Configure company-specific portfolios")
    print("   4. Enable multi-platform publishing")


async def test_client_integration():
    """Test the updated client with new endpoints"""

    print("\n🧪 Testing Updated Achievement Client\n")

    import sys

    sys.path.append(".")

    from services.tech_doc_generator.app.clients.achievement_client import (
        AchievementClient,
    )

    client = AchievementClient(base_url="http://localhost:8090")

    async with client:
        # Test 1: Batch operations
        print("1️⃣ Testing batch operations...")
        achievements = await client.batch_get_achievements([24, 25, 26])
        print(f"✅ Batch fetched {len(achievements)} achievements")

        # Test 2: Recent highlights
        print("\n2️⃣ Testing recent highlights...")
        highlights = await client.get_recent_highlights(days=30, min_impact_score=70)
        print(f"✅ Found {len(highlights)} recent highlights")
        for h in highlights[:3]:
            print(f"   - {h.title} (Score: {h.impact_score})")

        # Test 3: Company targeted
        print("\n3️⃣ Testing company targeting...")
        for company in ["notion", "anthropic"]:
            targeted = await client.get_company_targeted(company)
            print(f"✅ {company.capitalize()}: {len(targeted)} relevant achievements")

    print("\n✅ Client integration test complete!")


if __name__ == "__main__":
    print("Choose test:")
    print("1. Test complete integration flow")
    print("2. Test updated client")

    choice = input("\nEnter choice (1 or 2): ").strip()

    if choice == "1":
        asyncio.run(test_complete_integration())
    elif choice == "2":
        asyncio.run(test_client_integration())
    else:
        print("Invalid choice")
