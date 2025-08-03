#!/usr/bin/env python3
"""
Comprehensive component testing script for Achievement Collector System.
Tests all major components individually to ensure they work correctly.
"""

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path
import pytest

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that all our components can be imported successfully."""
    print("🔍 Testing imports...")

    try:
        from services.achievement_collector.services.historical_pr_analyzer import (
            HistoricalPRAnalyzer,  # noqa: F401
        )

        print("✅ Historical PR Analyzer import successful")
    except ImportError as e:
        print(f"❌ Historical PR Analyzer import failed: {e}")
        assert False

    try:
        from services.achievement_collector.services.portfolio_validator import (
            PortfolioValidator,  # noqa: F401
        )

        print("✅ Portfolio Validator import successful")
    except ImportError as e:
        print(f"❌ Portfolio Validator import failed: {e}")
        assert False

    try:
        from services.achievement_collector.mlops.mlflow_registry import MLflowRegistry  # noqa: F401

        print("✅ MLflow Registry import successful")
    except ImportError as e:
        print(f"❌ MLflow Registry import failed: {e}")
        assert False

    try:
        from services.achievement_collector.ai_pipeline.intelligent_llm_router import (
            IntelligentLLMRouter,  # noqa: F401
        )

        print("✅ LLM Router import successful")
    except ImportError as e:
        print(f"❌ LLM Router import failed: {e}")
        assert False

    try:
        from services.achievement_collector.pipeline.end_to_end_integration import (
            EndToEndPipeline,  # noqa: F401
        )

        print("✅ End-to-End Pipeline import successful")
    except ImportError as e:
        print(f"❌ End-to-End Pipeline import failed: {e}")
        assert False

    try:
        from services.achievement_collector.models import Achievement, PRAchievement  # noqa: F401

        print("✅ Database models import successful")
    except ImportError as e:
        print(f"❌ Database models import failed: {e}")
        assert False

    assert True  # All imports successful


@pytest.mark.asyncio
async def test_historical_pr_analyzer():
    """Test Historical PR Analyzer functionality."""
    print("\n📊 Testing Historical PR Analyzer...")

    try:
        from services.achievement_collector.services.historical_pr_analyzer import (
            HistoricalPRAnalyzer,
        )

        # Test initialization
        analyzer = HistoricalPRAnalyzer(github_token="test-token")
        print("✅ Analyzer initialization successful")

        # Test mock data processing
        mock_pr_data = {
            "number": 123,
            "title": "Add new feature",
            "additions": 150,
            "deletions": 50,
            "changed_files": 5,
        }

        # Test business impact analysis (without API call)
        impact = await analyzer.analyze_business_impact(mock_pr_data)
        print(f"✅ Business impact analysis successful: {impact}")

        assert True  # Test passed

    except Exception as e:
        print(f"❌ Historical PR Analyzer test failed: {e}")
        assert False


@pytest.mark.asyncio
async def test_portfolio_validator():
    """Test Portfolio Validator functionality."""
    print("\n💼 Testing Portfolio Validator...")

    try:
        from services.achievement_collector.services.portfolio_validator import (
            PortfolioValidator,
        )

        # Test initialization
        validator = PortfolioValidator()
        print("✅ Portfolio Validator initialization successful")

        # Test with sample achievements
        sample_achievements = [
            {
                "title": "Implement OAuth2 Authentication",
                "category": "feature",
                "impact_score": 85,
                "business_value": {
                    "time_saved_hours": 100,
                    "cost_reduction": 15000,
                    "revenue_impact": 10000,
                },
                "time_investment": 40,
            },
            {
                "title": "Optimize Database Queries",
                "category": "performance",
                "impact_score": 92,
                "business_value": {
                    "time_saved_hours": 80,
                    "cost_reduction": 20000,
                    "revenue_impact": 15000,
                },
                "time_investment": 32,
            },
        ]

        # Test portfolio validation
        result = validator.calculate_portfolio_value(sample_achievements)
        print(
            f"✅ Portfolio validation successful: Total value ${result['total_value']:,.2f}"
        )

        assert True  # Test passed

    except Exception as e:
        print(f"❌ Portfolio Validator test failed: {e}")
        assert False


@pytest.mark.asyncio
async def test_mlflow_registry():
    """Test MLflow Registry functionality."""
    print("\n🤖 Testing MLflow Registry...")

    try:
        from services.achievement_collector.mlops.mlflow_registry import MLflowRegistry

        # Test initialization
        registry = MLflowRegistry()
        print("✅ MLflow Registry initialization successful")

        # Test model registration (mock)
        success = await registry.register_model(
            model_name="test_model",
            model_version="1.0.0",
            accuracy=0.95,
            metadata={"test": True},
        )
        print(f"✅ Model registration test: {success}")

        # Test model listing
        models = await registry.list_models()
        print(f"✅ Model listing successful: Found {len(models)} models")

        assert True  # Test passed

    except Exception as e:
        print(f"❌ MLflow Registry test failed: {e}")
        assert False


@pytest.mark.asyncio
async def test_llm_router():
    """Test LLM Router functionality."""
    print("\n🧠 Testing LLM Router...")

    try:
        from services.achievement_collector.ai_pipeline.intelligent_llm_router import (
            IntelligentLLMRouter,
        )

        # Test initialization
        config = {
            "providers": {
                "openai": {"models": ["gpt-4", "gpt-3.5-turbo"], "api_key": "test-key"},
                "anthropic": {"models": ["claude-3-opus"], "api_key": "test-key"},
            },
            "routing_strategy": "balanced",
            "fallback_enabled": True,
        }
        router = IntelligentLLMRouter(config)
        print("✅ LLM Router initialization successful")

        # Test routing decision (without API call)
        decision = await router.route_query(
            query="Test query for business analysis",
            max_cost_per_request=0.01,
            quality_threshold=0.9,
        )
        print(f"✅ Routing decision successful: {decision.selected_model}")

        assert True  # Test passed

    except Exception as e:
        print(f"❌ LLM Router test failed: {e}")
        assert False


def test_database_models():
    """Test database models functionality."""
    print("\n🗄️ Testing Database Models...")

    try:
        from models import Achievement, PRAchievement

        # Test model creation
        Achievement(
            title="Test Achievement",
            description="Test description",
            category="feature",
            impact_score=85.0,
            business_value="25000",
            created_at=datetime.now(timezone.utc),
        )
        print("✅ Achievement model creation successful")

        PRAchievement(
            achievement_id=1,
            pr_number=123,
            title="Test PR",
            merge_timestamp=datetime.now(timezone.utc),
        )
        print("✅ PR Achievement model creation successful")

        assert True  # Test passed

    except Exception as e:
        print(f"❌ Database models test failed: {e}")
        assert False


@pytest.mark.asyncio
async def test_end_to_end_pipeline():
    """Test End-to-End Pipeline functionality."""
    print("\n🔗 Testing End-to-End Pipeline...")

    try:
        from services.achievement_collector.pipeline.end_to_end_integration import (
            EndToEndPipeline,
        )

        # Test initialization
        pipeline = EndToEndPipeline()
        print("✅ Pipeline initialization successful")

        # Test health checks
        health = pipeline.run_health_checks()
        print(f"✅ Health check successful: {health['overall_status']}")

        # Test metrics collection
        metrics = pipeline.get_metrics()
        print(f"✅ Metrics collection successful: {len(metrics)} metrics")

        assert True  # Test passed

    except Exception as e:
        print(f"❌ End-to-End Pipeline test failed: {e}")
        assert False


async def main():
    """Run all component tests."""
    print("🚀 Starting Achievement Collector System Component Tests")
    print("=" * 60)

    # Track results
    results = []

    # Test imports first
    import_success = test_imports()
    results.append(("Imports", import_success))

    if not import_success:
        print("\n❌ Import tests failed. Cannot proceed with other tests.")
        return

    # Test each component
    test_functions = [
        ("Historical PR Analyzer", test_historical_pr_analyzer),
        ("Portfolio Validator", test_portfolio_validator),
        ("MLflow Registry", test_mlflow_registry),
        ("LLM Router", test_llm_router),
        ("Database Models", lambda: test_database_models()),
        ("End-to-End Pipeline", test_end_to_end_pipeline),
    ]

    for name, test_func in test_functions:
        try:
            if asyncio.iscoroutinefunction(test_func):
                success = await test_func()
            else:
                success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ {name} test failed with exception: {e}")
            results.append((name, False))

    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {name}")

    print(f"\nOverall: {passed}/{total} tests passed ({passed / total * 100:.1f}%)")

    if passed == total:
        print("🎉 All tests passed! System is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    asyncio.run(main())
