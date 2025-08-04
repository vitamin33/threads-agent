#!/usr/bin/env python3
"""
Test script for new achievement_collector integration endpoints
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta


async def test_integration_endpoints():
    """Test the new tech-doc-integration endpoints"""
    
    base_url = "http://localhost:8090"
    
    print("🧪 Testing Achievement Collector Integration Endpoints\n")
    
    async with httpx.AsyncClient() as client:
        # Test 1: Get recent highlights
        print("1️⃣ Testing /tech-doc-integration/recent-highlights...")
        try:
            response = await client.post(
                f"{base_url}/tech-doc-integration/recent-highlights",
                params={
                    "days": 30,
                    "min_impact_score": 70,
                    "limit": 5
                }
            )
            
            if response.status_code == 200:
                highlights = response.json()
                print(f"✅ Found {len(highlights)} recent highlights")
                for h in highlights[:3]:
                    print(f"   - {h['title']} (Score: {h['impact_score']})")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                
        except httpx.ConnectError:
            print("❌ Could not connect. Make sure to run:")
            print("   kubectl port-forward svc/achievement-collector 8090:8090")
            return
            
        # Test 2: Batch get achievements
        print("\n2️⃣ Testing /tech-doc-integration/batch-get...")
        try:
            # First get some IDs
            list_response = await client.get(f"{base_url}/achievements/", params={"limit": 5})
            if list_response.status_code == 200:
                achievements = list_response.json()
                if achievements:
                    ids = [a['id'] for a in achievements[:3]]
                    
                    response = await client.post(
                        f"{base_url}/tech-doc-integration/batch-get",
                        json={"achievement_ids": ids}
                    )
                    
                    if response.status_code == 200:
                        batch = response.json()
                        print(f"✅ Batch retrieved {len(batch)} achievements")
                        for a in batch:
                            print(f"   - ID {a['id']}: {a['title']}")
                    else:
                        print(f"❌ Error: {response.status_code}")
                        
        except Exception as e:
            print(f"❌ Error: {e}")
            
        # Test 3: Company targeted achievements
        print("\n3️⃣ Testing /tech-doc-integration/company-targeted...")
        try:
            for company in ["notion", "anthropic", "jasper"]:
                response = await client.post(
                    f"{base_url}/tech-doc-integration/company-targeted",
                    params={
                        "company_name": company,
                        "limit": 3
                    }
                )
                
                if response.status_code == 200:
                    targeted = response.json()
                    print(f"✅ Found {len(targeted)} achievements for {company}")
                    if targeted:
                        print(f"   Top match: {targeted[0]['title']} (Score: {targeted[0]['impact_score']})")
                        
        except Exception as e:
            print(f"❌ Error: {e}")
            
        # Test 4: Content opportunities
        print("\n4️⃣ Testing /tech-doc-integration/stats/content-opportunities...")
        try:
            response = await client.get(f"{base_url}/tech-doc-integration/stats/content-opportunities")
            
            if response.status_code == 200:
                stats = response.json()
                print("✅ Content opportunity stats:")
                print(f"   Total content-ready: {stats['total_content_ready']}")
                print(f"   High-impact opportunities: {stats['high_impact_opportunities']}")
                print(f"   Recent achievements: {stats['recent_achievements']}")
                print(f"   Unprocessed: {stats['unprocessed_achievements']}")
                print(f"   Content generation rate: {stats['content_generation_rate']}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            
        # Test 5: Filter with multiple criteria
        print("\n5️⃣ Testing /tech-doc-integration/filter...")
        try:
            filter_request = {
                "categories": ["automation", "feature"],
                "min_impact_score": 75,
                "portfolio_ready_only": True,
                "days_back": 90,
                "tags": ["ai", "ml"]
            }
            
            response = await client.post(
                f"{base_url}/tech-doc-integration/filter",
                json=filter_request,
                params={"page": 1, "per_page": 10}
            )
            
            if response.status_code == 200:
                filtered = response.json()
                print(f"✅ Found {len(filtered)} achievements matching filters")
                for a in filtered[:3]:
                    print(f"   - {a['title']} ({a['category']}, Score: {a['impact_score']})")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
            
        # Test 6: Content-ready summaries
        print("\n6️⃣ Testing /tech-doc-integration/content-ready...")
        try:
            response = await client.get(
                f"{base_url}/tech-doc-integration/content-ready",
                params={"limit": 10}
            )
            
            if response.status_code == 200:
                summaries = response.json()
                print(f"✅ Found {len(summaries)} content-ready achievements")
                
                # Group by category
                by_category = {}
                for s in summaries:
                    cat = s['category']
                    if cat not in by_category:
                        by_category[cat] = 0
                    by_category[cat] += 1
                    
                print("   By category:")
                for cat, count in by_category.items():
                    print(f"   - {cat}: {count}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
            
    print("\n✅ Integration endpoint tests complete!")
    print("\n📝 Summary:")
    print("   - New endpoints provide optimized access for content generation")
    print("   - Batch operations reduce API calls")
    print("   - Company targeting enables personalized content")
    print("   - Content opportunity stats help track progress")


if __name__ == "__main__":
    asyncio.run(test_integration_endpoints())