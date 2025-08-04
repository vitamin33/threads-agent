#!/usr/bin/env python3
"""
Test script for Achievement Collector to Tech Doc Generator integration
"""

import asyncio
import httpx
from datetime import datetime
import json


async def test_integration():
    """Test the achievement to article integration"""
    
    # First, let's create a test achievement in the collector
    achievement_collector_url = "http://localhost:8090"
    tech_doc_url = "http://localhost:8091"  # Assuming tech doc runs on 8091
    
    print("🧪 Testing Achievement to Article Integration\n")
    
    # Step 1: Create a test achievement
    print("1️⃣ Creating test achievement...")
    
    achievement_data = {
        "title": "Implemented AI-Powered Content Pipeline",
        "description": "Built automated content generation system that integrates achievement tracking with technical documentation, reducing content creation time by 80%",
        "category": "automation",
        "impact_score": 92.5,
        "business_value": "Saves 15+ hours/week, enables consistent professional presence",
        "technical_details": {
            "technologies": ["Python", "FastAPI", "LangGraph", "OpenAI"],
            "architecture": "Microservices with async communication",
            "performance": "Processes achievements in <5 seconds"
        },
        "metrics": {
            "time_saved_hours_per_week": 15,
            "content_quality_score": 8.5,
            "automation_percentage": 80
        },
        "tags": ["ai", "automation", "content-generation", "mlops"],
        "portfolio_ready": True
    }
    
    try:
        async with httpx.AsyncClient() as client:
            # Create achievement
            response = await client.post(
                f"{achievement_collector_url}/achievements/",
                json=achievement_data
            )
            
            if response.status_code == 200:
                achievement = response.json()
                achievement_id = achievement["id"]
                print(f"✅ Created achievement ID: {achievement_id}")
                print(f"   Title: {achievement['title']}")
                print(f"   Impact Score: {achievement['impact_score']}")
            else:
                print(f"❌ Failed to create achievement: {response.status_code}")
                print(response.text)
                return
                
    except Exception as e:
        print(f"❌ Error connecting to achievement collector: {e}")
        print("   Make sure to port-forward: kubectl port-forward svc/achievement-collector 8090:8090")
        return
        
    # Step 2: Test the integration endpoints
    print("\n2️⃣ Testing article generation from achievement...")
    
    article_request = {
        "achievement_id": achievement_id,
        "article_types": ["case_study", "technical_deep_dive"],
        "platforms": ["linkedin", "devto"],
        "auto_publish": False
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{tech_doc_url}/api/achievement-articles/generate-from-achievement",
                json=article_request,
                timeout=30.0
            )
            
            if response.status_code == 200:
                articles = response.json()
                print(f"✅ Generated {len(articles)} articles:")
                for article in articles:
                    print(f"\n   📄 Article: {article['id']}")
                    print(f"      Type: {article['content']['article_type']}")
                    print(f"      Platform: {article['content']['platform']}")
                    print(f"      Insight Score: {article['insight_score']['overall_score']}")
                    print(f"      Title: {article['content']['title'][:60]}...")
            else:
                print(f"❌ Failed to generate articles: {response.status_code}")
                print(response.text)
                
    except httpx.ConnectError:
        print("❌ Could not connect to tech doc generator")
        print("   The service might not be running. Let's test the client directly...")
        
        # Test just the client
        print("\n3️⃣ Testing achievement client directly...")
        from services.tech_doc_generator.app.clients.achievement_client import AchievementClient
        
        client = AchievementClient(base_url=achievement_collector_url)
        async with client:
            # Test get achievement
            fetched = await client.get_achievement(achievement_id)
            if fetched:
                print(f"✅ Client can fetch achievement: {fetched.title}")
                
            # Test list achievements
            recent = await client.get_recent_achievements(days=1, min_impact_score=90)
            print(f"✅ Found {len(recent)} recent high-impact achievements")
            
            # Test by category
            automation_achievements = await client.get_by_category("automation", limit=5)
            print(f"✅ Found {len(automation_achievements)} automation achievements")
            
    except Exception as e:
        print(f"❌ Error testing integration: {e}")
        
    # Step 3: Test weekly highlights
    print("\n4️⃣ Testing weekly highlights generation...")
    
    try:
        # First, let's check what achievements we have
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{achievement_collector_url}/achievements/",
                params={"limit": 10, "skip": 0}
            )
            
            if response.status_code == 200:
                achievements = response.json()
                print(f"   Found {len(achievements)} total achievements")
                
                # Show top 3 by impact score
                if achievements:
                    sorted_achievements = sorted(
                        achievements, 
                        key=lambda x: x.get('impact_score', 0), 
                        reverse=True
                    )[:3]
                    
                    print("\n   Top achievements by impact:")
                    for ach in sorted_achievements:
                        print(f"   - {ach['title']} (Score: {ach.get('impact_score', 0)})")
                        
    except Exception as e:
        print(f"❌ Error checking achievements: {e}")
        
    print("\n✅ Integration test complete!")
    print("\n📝 Next steps:")
    print("   1. Port forward the services if not already done:")
    print("      kubectl port-forward svc/achievement-collector 8090:8090")
    print("      kubectl port-forward svc/tech-doc-generator 8091:8091")
    print("   2. Run the tech doc generator service locally if needed")
    print("   3. Use the achievement ID to test content generation")


if __name__ == "__main__":
    asyncio.run(test_integration())