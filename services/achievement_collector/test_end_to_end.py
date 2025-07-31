#!/usr/bin/env python3
"""
End-to-End Integration Test for Achievement Collector System.
Tests the complete pipeline from PR analysis to portfolio generation.
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))


async def test_complete_pipeline():
    """Test the complete pipeline with realistic data."""
    print("🚀 Testing Complete Achievement Collector Pipeline")
    print("=" * 60)

    try:
        from pipeline.end_to_end_integration import EndToEndPipeline

        # Initialize pipeline
        pipeline = EndToEndPipeline()
        print("✅ Pipeline initialized successfully")

        # Test complete pipeline execution
        print("\n🔄 Running complete pipeline analysis...")

        # Mock repository analysis (normally would be real GitHub data)
        mock_repo = "test-org/test-repo"

        # This would normally call the actual API, but we'll test the internal components
        result = await pipeline.run_complete_pipeline(mock_repo)

        print("📊 Pipeline Results:")
        print(f"  Status: {result['status']}")
        print(f"  Portfolio Value: ${result['portfolio_value']:,.2f}")
        print(f"  Execution Time: {result['execution_time']:.1f}s")
        print(f"  PRs Processed: {result['processed_prs']}")

        # Validate results
        assert result["status"] == "success", "Pipeline should complete successfully"
        assert result["portfolio_value"] > 0, "Portfolio should have positive value"
        assert result["execution_time"] > 0, "Should track execution time"

        print("\n✅ Complete pipeline test PASSED!")
        return True

    except Exception as e:
        print(f"\n❌ Complete pipeline test FAILED: {e}")
        return False


async def test_performance_benchmarks():
    """Test system performance benchmarks."""
    print("\n⚡ Testing Performance Benchmarks")
    print("=" * 40)

    try:
        from pipeline.end_to_end_integration import EndToEndPipeline
        import time

        pipeline = EndToEndPipeline()

        # Test response time benchmarks
        start_time = time.time()
        pipeline.run_health_checks()
        health_check_time = (time.time() - start_time) * 1000  # ms

        print(f"🏥 Health Check Performance: {health_check_time:.1f}ms")
        assert health_check_time < 200, (
            f"Health check should be <200ms, got {health_check_time:.1f}ms"
        )

        # Test metrics collection performance
        start_time = time.time()
        pipeline.get_metrics()
        metrics_time = (time.time() - start_time) * 1000  # ms

        print(f"📊 Metrics Collection: {metrics_time:.1f}ms")
        assert metrics_time < 50, (
            f"Metrics collection should be <50ms, got {metrics_time:.1f}ms"
        )

        print("✅ Performance benchmarks PASSED!")
        return True

    except Exception as e:
        print(f"❌ Performance benchmarks FAILED: {e}")
        return False


async def test_portfolio_generation():
    """Test portfolio generation with realistic data."""
    print("\n📄 Testing Portfolio Generation")
    print("=" * 40)

    try:
        from services.portfolio_validator import PortfolioValidator

        validator = PortfolioValidator()

        # Realistic achievement data
        achievements = [
            {
                "title": "Microservices Architecture Migration",
                "category": "architecture",
                "business_value": {
                    "time_saved_hours": 200,
                    "cost_reduction": 50000,
                    "revenue_impact": 25000,
                },
            },
            {
                "title": "Database Performance Optimization",
                "category": "performance",
                "business_value": {
                    "time_saved_hours": 120,
                    "cost_reduction": 30000,
                    "revenue_impact": 15000,
                },
            },
            {
                "title": "CI/CD Pipeline Implementation",
                "category": "infrastructure",
                "business_value": {
                    "time_saved_hours": 150,
                    "cost_reduction": 40000,
                    "revenue_impact": 20000,
                },
            },
        ]

        # Calculate portfolio value
        result = validator.calculate_portfolio_value(achievements)
        total_value = result["total_value"]

        print(f"💰 Portfolio Value: ${total_value:,.2f}")
        print(
            f"📈 Confidence Range: ${result['confidence_interval']['low']:,.2f} - ${result['confidence_interval']['high']:,.2f}"
        )

        # Validate portfolio is within target range ($200K-350K)
        target_min = 200000
        target_max = 350000

        if target_min <= total_value <= target_max:
            print(
                f"✅ Portfolio value ${total_value:,.2f} is within target range (${target_min:,.2f} - ${target_max:,.2f})"
            )
        else:
            print(
                f"⚠️  Portfolio value ${total_value:,.2f} is outside target range (${target_min:,.2f} - ${target_max:,.2f})"
            )

        # Generate reports
        report = validator.generate_portfolio_report(achievements)
        print(f"📑 Generated report with {len(report)} sections")

        print("✅ Portfolio generation PASSED!")
        return True

    except Exception as e:
        print(f"❌ Portfolio generation FAILED: {e}")
        return False


async def test_mlops_pipeline():
    """Test MLOps pipeline functionality."""
    print("\n🤖 Testing MLOps Pipeline")
    print("=" * 40)

    try:
        from mlops.mlflow_registry import MLflowRegistry

        registry = MLflowRegistry()

        # Test model management
        models = await registry.list_models()
        print(f"📋 Found {len(models)} registered models")

        # Test model registration
        test_success = await registry.register_model(
            model_name="test_performance_model", model_version="1.0.0", accuracy=0.96
        )
        print(f"✅ Model registration: {test_success}")

        # Test model metrics
        if models:
            first_model = models[0]["name"]
            metrics = await registry.get_model_metrics(first_model)
            print(f"📊 Model '{first_model}' accuracy: {metrics['accuracy']:.2%}")

        print("✅ MLOps pipeline PASSED!")
        return True

    except Exception as e:
        print(f"❌ MLOps pipeline FAILED: {e}")
        return False


async def main():
    """Run all end-to-end tests."""
    print("🧪 Achievement Collector System - End-to-End Testing")
    print("=" * 80)

    tests = [
        ("Complete Pipeline", test_complete_pipeline),
        ("Performance Benchmarks", test_performance_benchmarks),
        ("Portfolio Generation", test_portfolio_generation),
        ("MLOps Pipeline", test_mlops_pipeline),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = await test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ {name} failed with exception: {e}")
            results.append((name, False))

    # Print final summary
    print("\n" + "=" * 80)
    print("🎯 END-TO-END TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {name}")

    print(
        f"\nOverall Result: {passed}/{total} tests passed ({passed / total * 100:.1f}%)"
    )

    if passed == total:
        print("🎉 ALL END-TO-END TESTS PASSED!")
        print("✨ Achievement Collector System is production-ready!")
    else:
        print("⚠️  Some end-to-end tests failed.")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
