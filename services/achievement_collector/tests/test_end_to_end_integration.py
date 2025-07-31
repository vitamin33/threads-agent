"""Test end-to-end system integration and pipeline for CRA-303."""

import asyncio
import time
from unittest.mock import patch, AsyncMock

import pytest

from services.historical_pr_analyzer import HistoricalPRAnalyzer
from services.portfolio_validator import PortfolioValidator
from mlops.mlflow_registry import MLflowRegistry
from ai_pipeline.intelligent_llm_router import IntelligentLLMRouter


class TestEndToEndIntegration:
    """Test complete pipeline integration from GitHub to portfolio."""

    def test_pipeline_components_exist(self):
        """Test that all pipeline components are available."""
        # Given: Component imports
        assert HistoricalPRAnalyzer is not None
        assert PortfolioValidator is not None
        assert MLflowRegistry is not None
        assert IntelligentLLMRouter is not None

    @pytest.mark.asyncio
    async def test_complete_pipeline_execution(self):
        """Test end-to-end pipeline from PR analysis to portfolio generation."""
        from pipeline.end_to_end_integration import EndToEndPipeline

        # Given: Mock data and components
        mock_pr_data = [
            {
                "number": 1,
                "title": "feat: Add authentication",
                "additions": 500,
                "deletions": 100,
                "business_value": {
                    "impact": "HIGH",
                    "value": "$50,000",
                    "description": "Critical security feature",
                },
            }
        ]

        with patch.object(
            HistoricalPRAnalyzer, "analyze_repository_history", new_callable=AsyncMock
        ) as mock_analyze:
            mock_analyze.return_value = {
                "total_prs": 1,
                "analyzed_prs": 1,
                "pr_analyses": mock_pr_data,
            }

            # When: Running complete pipeline
            pipeline = EndToEndPipeline()
            result = await pipeline.run_complete_pipeline("owner/repo")

            # Then: Pipeline should complete successfully
            assert result["status"] == "success"
            assert result["stages_completed"] == 4
            assert "portfolio_value" in result
            assert result["execution_time"] < 300  # <5 minutes

    def test_pipeline_data_flow_integrity(self):
        """Test data integrity through pipeline stages."""
        from pipeline.end_to_end_integration import EndToEndPipeline

        # Given: Pipeline instance
        pipeline = EndToEndPipeline()

        # Test data transformation at each stage
        pr_data = {"number": 1, "title": "Test PR", "additions": 100}

        # Stage 1: PR enrichment
        enriched = pipeline.enrich_pr_data(pr_data)
        assert "achievement_id" in enriched
        assert enriched["source_type"] == "github_pr"

        # Stage 2: Business value calculation
        with_value = pipeline.calculate_business_value(enriched)
        assert "business_value" in with_value
        assert "impact_score" in with_value

        # Stage 3: Model prediction
        with_prediction = pipeline.apply_ml_models(with_value)
        assert "predicted_impact" in with_prediction
        assert "confidence_score" in with_prediction

    def test_pipeline_error_recovery(self):
        """Test pipeline handles errors gracefully."""
        from pipeline.end_to_end_integration import EndToEndPipeline

        pipeline = EndToEndPipeline()

        # Test recovery from GitHub API failure
        with patch.object(
            pipeline, "_fetch_github_data", side_effect=Exception("API Error")
        ):
            result = pipeline.run_with_recovery("owner/repo")
            assert result["status"] == "partial_success"
            assert "GitHub API Error" in result["errors"]
            assert result["recovery_actions_taken"] > 0

    def test_pipeline_performance_benchmarks(self):
        """Test pipeline meets performance requirements."""
        from pipeline.end_to_end_integration import EndToEndPipeline

        pipeline = EndToEndPipeline()

        # Test API response time
        start = time.time()
        status = pipeline.get_pipeline_status()
        response_time = (time.time() - start) * 1000

        assert response_time < 200  # <200ms requirement
        assert status["healthy"] is True

        # Test concurrent request handling
        async def concurrent_test():
            tasks = []
            for i in range(10):
                task = pipeline.process_pr_async({"number": i})
                tasks.append(task)

            start = time.time()
            results = await asyncio.gather(*tasks)
            total_time = time.time() - start

            assert len(results) == 10
            assert total_time < 5  # Should handle 10 requests in <5 seconds

        asyncio.run(concurrent_test())

    def test_monitoring_integration(self):
        """Test monitoring and metrics collection."""
        from pipeline.end_to_end_integration import EndToEndPipeline

        pipeline = EndToEndPipeline()

        # Given: Pipeline with monitoring enabled
        pipeline.enable_monitoring()

        # When: Running pipeline operations
        pipeline.process_pr({"number": 1, "title": "Test"})

        # Then: Metrics should be collected
        metrics = pipeline.get_metrics()
        assert "pipeline_executions_total" in metrics
        assert "pipeline_duration_seconds" in metrics
        assert "pipeline_errors_total" in metrics
        assert metrics["pipeline_executions_total"] > 0

    def test_health_checks_and_validation(self):
        """Test automated health checks."""
        from pipeline.end_to_end_integration import EndToEndPipeline

        pipeline = EndToEndPipeline()

        # Run health checks
        health = pipeline.run_health_checks()

        assert health["database"]["status"] == "healthy"
        assert health["mlflow"]["status"] == "healthy"
        assert health["llm_router"]["status"] == "healthy"
        assert health["overall_status"] == "healthy"

    @pytest.mark.asyncio
    async def test_scalability_with_large_dataset(self):
        """Test system handles large datasets efficiently."""
        from pipeline.end_to_end_integration import EndToEndPipeline

        pipeline = EndToEndPipeline()

        # Generate large dataset
        large_pr_set = []
        for i in range(1000):
            large_pr_set.append(
                {
                    "number": i,
                    "title": f"PR {i}",
                    "additions": i * 10,
                    "deletions": i * 5,
                }
            )

        # Process in batches
        start = time.time()
        results = await pipeline.process_batch_async(large_pr_set, batch_size=100)
        processing_time = time.time() - start

        assert len(results) == 1000
        assert processing_time < 300  # <5 minutes for 1000 PRs
        assert all(r["status"] == "success" for r in results)

    def test_production_configuration(self):
        """Test production deployment configuration."""
        from pipeline.end_to_end_integration import EndToEndPipeline

        # Test production config
        prod_config = EndToEndPipeline.get_production_config()

        assert prod_config["database"]["pool_size"] >= 10
        assert prod_config["database"]["max_overflow"] >= 20
        assert prod_config["monitoring"]["prometheus_enabled"] is True
        assert prod_config["monitoring"]["alert_rules"] is not None
        assert prod_config["error_handling"]["retry_count"] >= 3
        assert prod_config["error_handling"]["circuit_breaker_enabled"] is True

    def test_system_architecture_documentation(self):
        """Test that system architecture is properly documented."""
        from pipeline.end_to_end_integration import EndToEndPipeline

        # Get architecture documentation
        docs = EndToEndPipeline.get_architecture_docs()

        assert "components" in docs
        assert "data_flow" in docs
        assert "deployment" in docs
        assert "monitoring" in docs

        # Verify all components documented
        components = docs["components"]
        assert "historical_pr_analyzer" in components
        assert "portfolio_validator" in components
        assert "mlflow_registry" in components
        assert "llm_router" in components
