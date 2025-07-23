#!/usr/bin/env python3
"""
Test script for the Variant Generation Engine
Run this after deploying to verify the system works
"""

import asyncio
import json
from pathlib import Path
import sys

# Add services to path
sys.path.append(str(Path(__file__).parent.parent))

from services.viral_engine.hook_optimizer import ViralHookEngine


async def test_variant_generation():
    """Test the variant generation with different personas and topics"""
    
    engine = ViralHookEngine()
    
    test_cases = [
        {
            "persona_id": "ai-jesus",
            "topic": "finding inner peace in a chaotic world",
            "category": "inspiration"
        },
        {
            "persona_id": "ai-elon",
            "topic": "the future of AI and humanity",
            "category": "technology"
        }
    ]
    
    for test in test_cases:
        print(f"\n{'='*60}")
        print(f"Testing: {test['persona_id']} - {test['topic']}")
        print(f"{'='*60}")
        
        # Generate variants
        variants = await engine.generate_variants(
            persona_id=test["persona_id"],
            base_content=test["topic"],
            topic_category=test["category"],
            variant_count=5,
            include_emotion_variants=True
        )
        
        # Display results
        for i, variant in enumerate(variants, 1):
            print(f"\nVariant {i}:")
            print(f"  Pattern: {variant['pattern']} ({variant['pattern_category']})")
            print(f"  Emotion: {variant.get('emotion_modifier', 'None')}")
            print(f"  Hook: {variant['content']}")
            print(f"  Expected ER: {variant['expected_er']:.1%}")
    
    # Show pattern distribution
    print(f"\n{'='*60}")
    print("Pattern Usage Summary:")
    print(f"{'='*60}")
    
    analytics = await engine.get_pattern_performance("ai-jesus")
    print(json.dumps(analytics, indent=2))


if __name__ == "__main__":
    print("🧪 Testing Variant Generation Engine...")
    asyncio.run(test_variant_generation())
    print("\n✅ Test complete!")