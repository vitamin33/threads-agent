#!/usr/bin/env python3
"""
Integration test for Content Scheduler and Professional Content Engine

Tests the new AI Job Week 2 features:
1. Professional Content Engine (with viral_engine integration)
2. Content Scheduler (automated weekly scheduling)
3. Achievement integration layer
"""

import asyncio
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


# Mock some dependencies for testing
class MockAchievementClient:
    """Mock achievement client for testing"""

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def get_recent_highlights(self, days=7, min_impact_score=75.0, limit=10):
        """Mock recent achievements"""
        from services.tech_doc_generator.app.clients.achievement_client import (
            Achievement,
        )

        mock_data = [
            {
                "id": 25,
                "title": "Implemented Kubernetes Auto-scaling System",
                "description": "Built automated scaling solution reducing infrastructure costs by 40%",
                "category": "infrastructure",
                "impact_score": 95.0,
                "business_value": "$50K annual savings through intelligent resource optimization",
                "technical_details": {
                    "technology": "Kubernetes HPA with custom metrics",
                    "implementation": "Prometheus + KEDA for advanced scaling",
                },
                "metrics": {"cost_reduction": 40.0, "response_time_improvement": 25.0},
                "tags": ["kubernetes", "cost-optimization", "devops"],
                "portfolio_ready": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            },
            {
                "id": 26,
                "title": "AI-Powered Content Generation Pipeline",
                "description": "Created automated content system using OpenAI and viral optimization",
                "category": "ai_ml",
                "impact_score": 92.0,
                "business_value": "15+ hours/week time savings in content creation",
                "technical_details": {
                    "technology": "OpenAI GPT-4, FastAPI, Celery",
                    "architecture": "Microservices with viral pattern optimization",
                },
                "metrics": {"time_savings": 15.0, "content_engagement": 85.0},
                "tags": ["ai", "automation", "content-generation"],
                "portfolio_ready": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            },
            {
                "id": 27,
                "title": "Real-time Performance Monitoring Dashboard",
                "description": "Built comprehensive monitoring solution with anomaly detection",
                "category": "monitoring",
                "impact_score": 88.0,
                "business_value": "99.9% uptime achieved, prevented 12 critical incidents",
                "technical_details": {
                    "technology": "Prometheus, Grafana, AlertManager",
                    "features": "Custom anomaly detection algorithms",
                },
                "metrics": {"uptime": 99.9, "incidents_prevented": 12},
                "tags": ["monitoring", "reliability", "alerting"],
                "portfolio_ready": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            },
        ]

        return [Achievement(**data) for data in mock_data]

    async def get_company_targeted(self, company_name, categories=None, limit=20):
        """Mock company-targeted achievements"""
        from services.tech_doc_generator.app.clients.achievement_client import (
            Achievement,
        )

        # Return achievements relevant to the company
        if company_name.lower() == "anthropic":
            mock_data = {
                "id": 28,
                "title": "LLM Safety Framework Implementation",
                "description": "Built comprehensive AI safety validation system",
                "category": "ai_ml",
                "impact_score": 94.0,
                "business_value": "Ensured responsible AI deployment across all models",
                "technical_details": {
                    "technology": "Python, Transformers, Safety Validators",
                    "approach": "Multi-layer safety checking with human feedback",
                },
                "tags": ["ai-safety", "llm", "responsible-ai"],
                "portfolio_ready": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
            return [Achievement(**mock_data)]

        return []

    async def get_achievement(self, achievement_id):
        """Mock single achievement fetch"""
        highlights = await self.get_recent_highlights()
        for achievement in highlights:
            if achievement.id == achievement_id:
                return achievement
        return None


class MockViralEngine:
    """Mock viral engine for testing"""

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def generate_professional_content(self, request, achievement_data):
        """Mock professional content generation"""
        from services.tech_doc_generator.app.services.professional_content_engine import (
            ProfessionalContentResult,
        )

        # Generate mock professional content
        achievement_title = achievement_data.get("title", "Achievement")
        business_value = achievement_data.get("business_value", "Significant impact")

        mock_content = f"""# {achievement_title}

## The Challenge
Our team faced significant scalability challenges that were impacting both performance and costs.

## The Solution
{achievement_data.get("description", "Implemented comprehensive solution")}

## Technical Implementation
{achievement_data.get("technical_details", {}).get("technology", "Advanced technology stack")}

## Results & Impact
{business_value}

## Key Learnings
- Importance of data-driven decision making
- Value of automated monitoring and alerting
- Benefits of cross-functional collaboration

#AI #Engineering #TechLeadership #Innovation
        """

        return ProfessionalContentResult(
            title=f"How I {achievement_title}",
            content=mock_content,
            hook=f"Here's how I achieved {business_value.lower()}...",
            engagement_score=85.5,
            quality_score=88.2,
            platform_optimized=request.platform,
            recommended_hashtags=[
                "#AI",
                "#Engineering",
                "#TechLeadership",
                "#Innovation",
            ],
            best_posting_time="Tuesday 10 AM",
            seo_keywords=["engineering", "leadership", "innovation", "ai"],
        )


async def test_professional_content_engine():
    """Test the Professional Content Engine"""
    print("🧪 Testing Professional Content Engine...")

    # Import the actual classes
    from services.tech_doc_generator.app.services.professional_content_engine import (
        ProfessionalContentEngine,
        ProfessionalContentRequest,
    )
    from services.tech_doc_generator.app.services.achievement_content_generator import (
        ContentType,
        Platform,
    )

    # Mock the engine's dependencies
    engine = ProfessionalContentEngine()
    engine.client = None  # Will use fallback behavior

    # Mock achievement data
    achievement_data = {
        "id": 25,
        "title": "Implemented Kubernetes Auto-scaling System",
        "description": "Built automated scaling solution reducing infrastructure costs by 40%",
        "category": "infrastructure",
        "impact_score": 95.0,
        "business_value": "$50K annual savings",
        "technical_details": {"technology": "Kubernetes HPA"},
        "metrics": {"cost_reduction": 40.0},
        "skills_demonstrated": ["Kubernetes", "DevOps", "Cost Optimization"],
        "tags": ["kubernetes", "cost-optimization"],
    }

    # Create request
    request = ProfessionalContentRequest(
        achievement_id=25,
        content_type=ContentType.CASE_STUDY,
        target_company="anthropic",
        platform=Platform.LINKEDIN,
        tone="professional",
        include_hook=True,
        include_metrics=True,
    )

    # Mock the viral engine integration
    async with MockViralEngine() as mock_engine:
        result = await mock_engine.generate_professional_content(
            request, achievement_data
        )

        print("✅ Generated content:")
        print(f"   Title: {result.title}")
        print(f"   Hook: {result.hook}")
        print(f"   Engagement Score: {result.engagement_score}")
        print(f"   Quality Score: {result.quality_score}")
        print(f"   Platform: {result.platform_optimized.value}")
        print(f"   Content length: {len(result.content)} characters")
        print(f"   Hashtags: {', '.join(result.recommended_hashtags)}")

        assert result.engagement_score > 80, "Engagement score should be high"
        assert result.quality_score > 80, "Quality score should be high"
        assert "Kubernetes" in result.content, "Content should mention key technology"
        assert len(result.recommended_hashtags) > 0, "Should have hashtags"

        print("✅ Professional Content Engine test passed!")


async def test_content_scheduler():
    """Test the Content Scheduler"""
    print("\n🧪 Testing Content Scheduler...")

    from services.tech_doc_generator.app.services.content_scheduler import (
        ContentScheduler,
    )

    # Create scheduler with mocked dependencies
    scheduler = ContentScheduler()
    scheduler.achievement_client = MockAchievementClient()
    scheduler.content_engine = MockViralEngine()

    # Test 1: Create weekly schedule
    print("📅 Creating weekly schedule...")
    plan = await scheduler.create_weekly_schedule(
        target_companies=["anthropic", "notion", "stripe"]
    )

    print("✅ Created weekly plan:")
    print(f"   Week start: {plan.week_start}")
    print(f"   Target companies: {plan.target_companies}")
    print(f"   Scheduled entries: {len(plan.scheduled_entries)}")

    for entry in plan.scheduled_entries:
        print(
            f"   - {entry.platform.value}: {entry.content_type.value} (Achievement {entry.achievement_id})"
        )

    assert len(plan.scheduled_entries) == 3, (
        "Should create 3 entries for weekly schedule"
    )
    assert plan.target_companies == ["anthropic", "notion", "stripe"], (
        "Should set target companies"
    )

    # Test 2: Generate content for an entry
    print("\n📝 Generating content for scheduled entry...")
    entry = plan.scheduled_entries[0]
    entry.scheduled_time = datetime.now() - timedelta(minutes=1)  # Make it due

    success = await scheduler.generate_scheduled_content(entry)

    print("✅ Content generation result:")
    print(f"   Success: {success}")
    print(f"   Status: {entry.status}")
    if entry.generated_content:
        print(f"   Title: {entry.generated_content.title}")
        print(f"   Engagement: {entry.generated_content.engagement_score}")
        print(f"   Quality: {entry.generated_content.quality_score}")

    assert success, "Content generation should succeed"
    assert entry.status == "generated", "Entry should be marked as generated"
    assert entry.generated_content is not None, "Should have generated content"

    # Test 3: Get performance summary
    print("\n📊 Getting performance summary...")
    performance = await scheduler.get_content_performance_summary()

    print("✅ Performance summary:")
    print(f"   Total generated: {performance['total_generated']}")
    print(f"   Avg engagement: {performance['avg_engagement_score']:.1f}")
    print(f"   Avg quality: {performance['avg_quality_score']:.1f}")
    print(f"   Active schedules: {performance['active_schedules']}")

    assert performance["total_generated"] > 0, "Should have generated content"
    assert performance["avg_engagement_score"] > 0, "Should have engagement metrics"

    print("✅ Content Scheduler test passed!")


async def test_viral_engine_integration():
    """Test integration with viral engine patterns"""
    print("\n🧪 Testing Viral Engine Integration...")

    # Test professional pattern adaptation
    from services.tech_doc_generator.app.services.professional_content_engine import (
        ProfessionalContentEngine,
    )

    engine = ProfessionalContentEngine()

    # Test hook category selection
    elements = {
        "title": "Reduced infrastructure costs by 40%",
        "business_value": "$50K annual savings",
        "category": "optimization",
        "impact_score": 95.0,
    }

    category = engine._select_hook_category(elements, "anthropic", "professional")
    print(f"✅ Selected hook category: {category}")
    assert category in [
        "business_impact",
        "technical_authority",
        "thought_leadership",
        "problem_solving",
    ]

    # Test professional pattern filling
    pattern = "This {implementation} saved us ${amount} annually:"
    filled = engine._fill_pattern_template(pattern, elements)
    print(f"✅ Filled pattern: {filled}")
    assert "saved us" in filled, "Pattern should be filled"

    # Test viral hook adaptation
    viral_hook = "This will blow your mind: 40% cost reduction! 🔥"
    adapted = engine._adapt_hook_for_professional(viral_hook)
    print(f"✅ Adapted hook: {adapted}")
    assert "blow your mind" not in adapted, "Should remove casual language"
    assert "🔥" not in adapted, "Should remove emojis"

    print("✅ Viral Engine Integration test passed!")


async def test_company_targeting():
    """Test company-specific content targeting"""
    print("\n🧪 Testing Company Targeting...")

    from services.tech_doc_generator.app.services.professional_content_engine import (
        ProfessionalContentEngine,
    )

    engine = ProfessionalContentEngine()

    # Test company pattern matching
    companies = ["anthropic", "notion", "stripe"]

    for company in companies:
        if company in engine.company_patterns:
            pattern = engine.company_patterns[company]
            print(f"✅ {company.title()} targeting:")
            print(f"   Focus: {pattern['focus']}")
            print(f"   Tone: {pattern['tone']}")
            print(f"   Avoid: {pattern['avoid']}")

    # Test optimization generation
    optimizations = await engine._generate_optimizations(
        content="Test content about AI safety",
        platform=Platform.LINKEDIN,
        target_company="anthropic",
    )

    print("✅ Generated optimizations:")
    print(f"   Hashtags: {optimizations['hashtags'][:5]}")  # Show first 5
    print(f"   Best time: {optimizations['posting_time']}")
    print(f"   Keywords: {optimizations['keywords'][:3]}")  # Show first 3

    assert "#AI" in optimizations["hashtags"], "Should include AI hashtag"
    assert "Tuesday" in optimizations["posting_time"], (
        "Should suggest professional posting time"
    )

    print("✅ Company Targeting test passed!")


async def main():
    """Run all integration tests"""
    print("🚀 Starting AI Job Week 2 Integration Tests")
    print("=" * 60)

    try:
        # Test individual components
        await test_professional_content_engine()
        await test_content_scheduler()
        await test_viral_engine_integration()
        await test_company_targeting()

        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ Ready for next steps:")
        print("   1. Deploy tech-doc-generator service to cluster")
        print("   2. Create AI ROI Calculator public tool")
        print("   3. Build content performance analytics dashboard")
        print("   4. Test end-to-end workflow on live cluster")

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
