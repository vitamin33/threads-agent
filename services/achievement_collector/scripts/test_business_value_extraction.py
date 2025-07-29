#!/usr/bin/env python3
"""
Test the business value extraction with real database.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from services.achievement_collector.db.config import get_db
from services.achievement_collector.db.models import Achievement
from services.achievement_collector.services.ai_analyzer import AIAnalyzer


async def test_extraction():
    """Test business value extraction on recent achievements."""
    db = next(get_db())
    analyzer = AIAnalyzer()
    
    try:
        # Get a recent achievement without business value
        achievement = db.query(Achievement).filter(
            Achievement.source_type == "github_pr",
            (Achievement.business_value == None) | (Achievement.business_value == "")
        ).order_by(Achievement.id.desc()).first()
        
        if not achievement:
            print("No achievements found without business value")
            return
        
        print(f"\n🔍 Testing on achievement {achievement.id}:")
        print(f"   Title: {achievement.title}")
        print(f"   Description: {achievement.description[:200]}...")
        print(f"   Current business_value: {achievement.business_value}")
        
        # Test extraction
        print("\n📊 Extracting business value...")
        value_dict = await analyzer.extract_business_value(achievement.description)
        
        if value_dict:
            print(f"\n✅ Extracted value:")
            print(f"   Total: ${value_dict.get('total_value', 0):,.0f} {value_dict.get('currency', 'USD')}")
            print(f"   Period: {value_dict.get('period', 'unknown')}")
            print(f"   Type: {value_dict.get('type', 'unknown')}")
            print(f"   Method: {value_dict.get('extraction_method', 'unknown')}")
            
            # Test update
            print("\n💾 Updating achievement...")
            updated = await analyzer.update_achievement_business_value(db, achievement)
            
            if updated:
                print(f"✅ Updated successfully!")
                print(f"   New business_value: {achievement.business_value}")
                print(f"   Time saved: {achievement.time_saved_hours} hours")
                print(f"   Performance improvement: {achievement.performance_improvement_pct}%")
            else:
                print("❌ Update failed")
        else:
            print("❌ No value extracted")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "test":
        print("⚠️  Using offline extraction (no OpenAI API key)")
    else:
        print("✅ Using AI-powered extraction")
    
    asyncio.run(test_extraction())