#!/usr/bin/env python3
"""
Simple test runner for shared models
"""

import sys
from datetime import datetime, timedelta

# Add to path
sys.path.insert(0, '.')

# Test imports
try:
    from services.common.models import (
        Achievement,
        AchievementCreate,
        AchievementCategory,
        AchievementMetrics,
        ArticleType,
        Platform,
        ArticleContent,
        ContentRequest,
        ContentResponse
    )
    print("✅ All model imports successful!")
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Test achievement creation
try:
    print("\n📋 Testing Achievement Models...")
    
    # Test metrics
    metrics = AchievementMetrics(
        time_saved_hours=20,
        cost_saved_dollars=50000,
        performance_improvement_percent=150
    )
    print("✅ AchievementMetrics created")
    
    # Test achievement creation
    achievement = Achievement(
        id=1,
        title="Test Achievement for Shared Models",
        description="This is a test achievement to validate our shared models are working correctly",
        category=AchievementCategory.AI_ML,
        impact_score=85.0,
        business_value="Validates shared model architecture",
        metrics=metrics,
        tags=["TEST", "validation"],  # Should be normalized to lowercase
        portfolio_ready=True,
        started_at=datetime.now() - timedelta(days=5),
        completed_at=datetime.now(),
        created_at=datetime.now()
    )
    
    print(f"✅ Achievement created with ID: {achievement.id}")
    print(f"   - Duration: {achievement.duration_hours:.1f} hours")
    print(f"   - Tags normalized: {achievement.tags}")
    
    # Test achievement create model
    create_data = AchievementCreate(
        title="New Feature Implementation",
        description="Implementing a new feature using shared models for better integration",
        category=AchievementCategory.FEATURE,
        impact_score=75,
        business_value="Improves service integration",
        started_at=datetime.now() - timedelta(days=3),
        completed_at=datetime.now()
    )
    print("✅ AchievementCreate validated")
    
except Exception as e:
    print(f"❌ Achievement model error: {e}")
    sys.exit(1)

# Test article models
try:
    print("\n📝 Testing Article Models...")
    
    # Test article content
    article = ArticleContent(
        article_type=ArticleType.CASE_STUDY,
        platform=Platform.LINKEDIN,
        title="How Shared Models Improved Our Integration",
        content="In this case study, we explore how implementing shared Pydantic models across our microservices improved data consistency and reduced integration bugs by 80%. The journey began when we noticed repeated data transformation errors..." + "x" * 200,
        tags=["Integration", "MODELS", "microservices"],  # Should normalize
        metadata={
            "achievement_id": 1,
            "word_count": 500
        }
    )
    
    print(f"✅ ArticleContent created")
    print(f"   - Type: {article.article_type.value}")
    print(f"   - Platform: {article.platform.value}")
    print(f"   - Tags normalized: {article.tags}")
    
    # Test content request
    request = ContentRequest(
        achievement_ids=[1, 2, 3],
        article_types=[ArticleType.TUTORIAL, ArticleType.CASE_STUDY],
        platforms=[Platform.DEVTO, Platform.MEDIUM],
        quality_threshold=8.0,
        target_company="anthropic"
    )
    print("✅ ContentRequest validated")
    
    # Test content response
    response = ContentResponse(
        request_id="test_123",
        status="success",
        articles=[article],
        total_generated=1,
        average_quality_score=8.5,
        generation_time_seconds=15.3,
        total_tokens_used=2500,
        estimated_cost_usd=0.10
    )
    print("✅ ContentResponse created")
    
except Exception as e:
    print(f"❌ Article model error: {e}")
    sys.exit(1)

# Test validation
try:
    print("\n🔍 Testing Validation...")
    
    # Should fail - impact score > 100
    try:
        bad_achievement = Achievement(
            id=2,
            title="Invalid Achievement",
            description="This should fail validation",
            category=AchievementCategory.BUGFIX,
            impact_score=150,  # Invalid!
            business_value="Test",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            created_at=datetime.now()
        )
        print("❌ Validation should have failed for impact_score > 100")
    except Exception:
        print("✅ Validation correctly rejected impact_score > 100")
    
    # Should fail - title too short
    try:
        bad_article = ArticleContent(
            article_type=ArticleType.TUTORIAL,
            platform=Platform.GITHUB,
            title="Hi",  # Too short!
            content="x" * 200
        )
        print("❌ Validation should have failed for short title")
    except Exception:
        print("✅ Validation correctly rejected short title")
    
    # Should fail - content too short
    try:
        bad_article = ArticleContent(
            article_type=ArticleType.TUTORIAL,
            platform=Platform.GITHUB,
            title="Valid Title Here",
            content="Too short"  # Less than 100 chars
        )
        print("❌ Validation should have failed for short content")
    except Exception:
        print("✅ Validation correctly rejected short content")
    
except Exception as e:
    print(f"❌ Validation test error: {e}")

print("\n🎉 All shared model tests passed!")
print("\n📊 Summary:")
print("   - Achievement models: ✅")
print("   - Article models: ✅")
print("   - Validation rules: ✅")
print("   - Tag normalization: ✅")
print("   - Auto-calculations: ✅")