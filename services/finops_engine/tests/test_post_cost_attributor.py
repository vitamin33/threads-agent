"""
Test suite for PostCostAttributor - Per-Post Cost Attribution System (CRA-240)

Following TDD methodology to implement precise cost-post associations with:
- 95% accuracy target for cost attribution
- Full audit trail for cost tracking
- API endpoints to query cost by post_id
- Cost breakdown by component (OpenAI, Infrastructure, etc.)

Requirements:
1. Track costs per individual viral post with precise breakdown
2. Link costs to specific posts from generation through publication
3. Store cost-post associations in PostgreSQL
4. Provide API endpoints to query cost by post_id
"""

import pytest


class TestPostCostAttributor:
    """Test suite for PostCostAttributor class - core cost attribution functionality."""

    def test_post_cost_attributor_initialization(self):
        """Test that PostCostAttributor can be instantiated.

        This will fail because PostCostAttributor doesn't exist yet!
        """
        from services.finops_engine.post_cost_attributor import PostCostAttributor

        attributor = PostCostAttributor()

        assert attributor is not None
        assert hasattr(attributor, "get_post_cost_breakdown")
        assert hasattr(attributor, "track_cost_for_post")
        assert hasattr(attributor, "calculate_total_post_cost")

    @pytest.mark.asyncio
    async def test_get_post_cost_breakdown_returns_empty_for_unknown_post(self):
        """Test that getting cost breakdown for unknown post_id returns empty breakdown.

        This should be the simplest case that could fail.
        """
        from services.finops_engine.post_cost_attributor import PostCostAttributor

        attributor = PostCostAttributor()

        # Query cost breakdown for non-existent post
        breakdown = await attributor.get_post_cost_breakdown("unknown_post_123")

        # Should return empty but valid breakdown structure
        assert breakdown is not None
        assert breakdown["post_id"] == "unknown_post_123"
        assert breakdown["total_cost"] == 0.0
        assert breakdown["cost_breakdown"] == {}
        assert breakdown["accuracy_score"] >= 0.95  # 95% accuracy target
        assert "audit_trail" in breakdown

    @pytest.mark.asyncio
    async def test_get_post_cost_breakdown_returns_costs_for_known_post(self):
        """Test that getting cost breakdown for known post_id returns correct costs."""
        from services.finops_engine.post_cost_attributor import PostCostAttributor

        attributor = PostCostAttributor()

        # First, track some costs for a specific post
        post_id = "test_post_001"

        await attributor.track_cost_for_post(
            post_id=post_id,
            cost_type="openai_api",
            cost_amount=0.0125,
            metadata={
                "model": "gpt-4o",
                "operation": "hook_generation",
                "input_tokens": 1000,
                "output_tokens": 500,
            },
        )

        await attributor.track_cost_for_post(
            post_id=post_id,
            cost_type="kubernetes",
            cost_amount=0.0036,  # 3 minutes of pod usage
            metadata={
                "service": "persona_runtime",
                "duration_minutes": 3,
                "cpu_cores": 0.5,
                "memory_gb": 1.0,
            },
        )

        # Query cost breakdown
        breakdown = await attributor.get_post_cost_breakdown(post_id)

        # Verify breakdown structure and values
        assert breakdown["post_id"] == post_id
        assert breakdown["total_cost"] == 0.0161  # 0.0125 + 0.0036

        # Verify cost breakdown by type
        assert "openai_api" in breakdown["cost_breakdown"]
        assert "kubernetes" in breakdown["cost_breakdown"]
        assert breakdown["cost_breakdown"]["openai_api"] == 0.0125
        assert breakdown["cost_breakdown"]["kubernetes"] == 0.0036

        # Verify accuracy target
        assert breakdown["accuracy_score"] >= 0.95

        # Verify audit trail exists
        assert len(breakdown["audit_trail"]) == 2
        assert all("timestamp" in entry for entry in breakdown["audit_trail"])

    @pytest.mark.asyncio
    async def test_track_cost_for_post_stores_cost_event(self):
        """Test that tracking cost for post stores the cost event correctly."""
        from services.finops_engine.post_cost_attributor import PostCostAttributor

        attributor = PostCostAttributor()

        # Track a cost event
        result = await attributor.track_cost_for_post(
            post_id="test_post_002",
            cost_type="openai_api",
            cost_amount=0.0075,
            metadata={
                "model": "gpt-3.5-turbo-0125",
                "operation": "body_generation",
                "input_tokens": 1500,
                "output_tokens": 800,
                "persona_id": "ai_jesus",
            },
        )

        # Verify tracking was successful
        assert result is not None
        assert "event_id" in result
        assert result["post_id"] == "test_post_002"
        assert result["cost_amount"] == 0.0075
        assert result["stored_at"] is not None

    @pytest.mark.asyncio
    async def test_calculate_total_post_cost_aggregates_all_costs(self):
        """Test that calculating total cost aggregates all costs for a post."""
        from services.finops_engine.post_cost_attributor import PostCostAttributor

        attributor = PostCostAttributor()

        post_id = "test_post_003"

        # Track multiple cost events for the same post
        costs = [
            ("openai_api", 0.0125, {"model": "gpt-4o", "operation": "hook_generation"}),
            (
                "openai_api",
                0.0025,
                {"model": "gpt-3.5-turbo-0125", "operation": "body_generation"},
            ),
            (
                "kubernetes",
                0.0036,
                {"service": "persona_runtime", "duration_minutes": 3},
            ),
            (
                "vector_db",
                0.0001,
                {"operation": "similarity_search", "query_count": 500},
            ),
            ("monitoring", 0.0002, {"service": "prometheus", "duration_minutes": 5}),
        ]

        for cost_type, cost_amount, metadata in costs:
            await attributor.track_cost_for_post(
                post_id=post_id,
                cost_type=cost_type,
                cost_amount=cost_amount,
                metadata=metadata,
            )

        # Calculate total cost
        total_cost = await attributor.calculate_total_post_cost(post_id)

        # Verify total is sum of all costs
        expected_total = sum(cost[1] for cost in costs)
        assert abs(total_cost - expected_total) < 0.0001
        assert total_cost == 0.0189  # Verify exact calculation


class TestPostCostAnalysisModel:
    """Test suite for PostCostAnalysis database model."""

    def test_post_cost_analysis_model_exists(self):
        """Test that PostCostAnalysis database model exists and has required fields.

        This will fail because the model doesn't exist yet!
        """
        from services.finops_engine.models import PostCostAnalysis

        # Verify model exists and has required fields
        assert hasattr(PostCostAnalysis, "__table__")

        # Check required columns exist
        columns = [col.name for col in PostCostAnalysis.__table__.columns]
        required_columns = [
            "id",
            "post_id",
            "cost_type",
            "cost_amount",
            "cost_metadata",
            "accuracy_score",
            "created_at",
            "updated_at",
        ]

        for required_col in required_columns:
            assert required_col in columns, f"Missing required column: {required_col}"

    def test_post_cost_analysis_model_creation(self):
        """Test creating a PostCostAnalysis model instance."""
        from services.finops_engine.models import PostCostAnalysis

        # Create model instance
        cost_entry = PostCostAnalysis(
            post_id="test_post_004",
            cost_type="openai_api",
            cost_amount=0.0125,
            metadata={
                "model": "gpt-4o",
                "operation": "hook_generation",
                "input_tokens": 1000,
                "output_tokens": 500,
                "persona_id": "ai_jesus",
            },
            accuracy_score=0.98,
        )

        # Verify instance properties
        assert cost_entry.post_id == "test_post_004"
        assert cost_entry.cost_type == "openai_api"
        assert cost_entry.cost_amount == 0.0125
        assert cost_entry.accuracy_score == 0.98
        assert cost_entry.metadata["model"] == "gpt-4o"

    def test_post_cost_analysis_model_relationships(self):
        """Test that PostCostAnalysis model has proper relationships/indexes."""
        from services.finops_engine.models import PostCostAnalysis

        # Check that indexes exist for performance
        indexes = PostCostAnalysis.__table__.indexes
        index_columns = set()
        for index in indexes:
            for col in index.columns:
                index_columns.add(col.name)

        # Should have indexes on commonly queried columns
        expected_indexed_columns = {"post_id", "cost_type", "created_at"}
        assert expected_indexed_columns.issubset(index_columns), (
            f"Missing required indexes. Expected: {expected_indexed_columns}, Found: {index_columns}"
        )


class TestCostAttributionAccuracy:
    """Test suite for verifying 95% accuracy target for cost attribution."""

    @pytest.mark.asyncio
    async def test_cost_attribution_accuracy_calculation(self):
        """Test that accuracy score is calculated correctly.

        Accuracy should be based on how precisely costs are linked to posts.
        """
        from services.finops_engine.post_cost_attributor import PostCostAttributor

        attributor = PostCostAttributor()

        # Track cost with high confidence metadata
        await attributor.track_cost_for_post(
            post_id="test_post_005",
            cost_type="openai_api",
            cost_amount=0.0125,
            metadata={
                "model": "gpt-4o",
                "operation": "hook_generation",
                "input_tokens": 1000,
                "output_tokens": 500,
                "persona_id": "ai_jesus",
                "request_id": "req_123",  # High confidence linking
                "correlation_id": "corr_456",  # Full trace correlation
            },
        )

        # Get breakdown and verify accuracy
        breakdown = await attributor.get_post_cost_breakdown("test_post_005")

        # High-confidence metadata should yield high accuracy
        assert breakdown["accuracy_score"] >= 0.95
        assert breakdown["accuracy_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_cost_attribution_accuracy_with_incomplete_metadata(self):
        """Test accuracy score with incomplete metadata (lower confidence)."""
        from services.finops_engine.post_cost_attributor import PostCostAttributor

        attributor = PostCostAttributor()

        # Track cost with minimal metadata (lower confidence)
        await attributor.track_cost_for_post(
            post_id="test_post_006",
            cost_type="kubernetes",
            cost_amount=0.0036,
            metadata={
                "service": "persona_runtime",
                # Missing correlation_id, request_id, etc.
            },
        )

        # Get breakdown and verify accuracy
        breakdown = await attributor.get_post_cost_breakdown("test_post_006")

        # Incomplete metadata should still meet 95% target but may be lower
        assert breakdown["accuracy_score"] >= 0.95

        # Verify accuracy breakdown details
        assert "accuracy_details" in breakdown
        assert "confidence_factors" in breakdown["accuracy_details"]

    @pytest.mark.asyncio
    async def test_cost_attribution_audit_trail_completeness(self):
        """Test that audit trail provides complete cost tracking history."""
        from services.finops_engine.post_cost_attributor import PostCostAttributor

        attributor = PostCostAttributor()

        post_id = "test_post_007"

        # Track costs at different stages of post lifecycle
        lifecycle_costs = [
            (
                "openai_api",
                0.0050,
                {"operation": "trend_research", "stage": "research"},
            ),
            ("openai_api", 0.0075, {"operation": "hook_generation", "stage": "hook"}),
            ("openai_api", 0.0025, {"operation": "body_generation", "stage": "body"}),
            (
                "kubernetes",
                0.0036,
                {"operation": "post_generation", "stage": "processing"},
            ),
            (
                "vector_db",
                0.0001,
                {"operation": "deduplication", "stage": "validation"},
            ),
        ]

        for cost_type, cost_amount, metadata in lifecycle_costs:
            await attributor.track_cost_for_post(
                post_id=post_id,
                cost_type=cost_type,
                cost_amount=cost_amount,
                metadata=metadata,
            )

        # Get breakdown and verify audit trail
        breakdown = await attributor.get_post_cost_breakdown(post_id)

        # Verify complete audit trail
        assert len(breakdown["audit_trail"]) == 5

        # Verify chronological order
        timestamps = [entry["timestamp"] for entry in breakdown["audit_trail"]]
        assert timestamps == sorted(timestamps)

        # Verify all lifecycle stages are captured
        stages = {entry["metadata"]["stage"] for entry in breakdown["audit_trail"]}
        expected_stages = {"research", "hook", "body", "processing", "validation"}
        assert stages == expected_stages


class TestCostAttributionAPI:
    """Test suite for REST API endpoints for cost attribution queries."""

    def test_cost_attribution_api_initialization(self):
        """Test that cost attribution API endpoints can be initialized.

        This will fail because the API doesn't exist yet!
        """
        from services.finops_engine.cost_attribution_api import CostAttributionAPI

        api = CostAttributionAPI()

        assert api is not None
        assert hasattr(api, "get_post_cost_breakdown")
        assert hasattr(api, "get_post_cost_summary")
        assert hasattr(api, "get_cost_breakdown_by_date_range")

    @pytest.mark.asyncio
    async def test_get_post_cost_breakdown_endpoint(self):
        """Test GET /costs/post/{post_id} endpoint returns cost breakdown."""
        from services.finops_engine.cost_attribution_api import CostAttributionAPI
        from fastapi.testclient import TestClient

        api = CostAttributionAPI()
        app = api.create_app()
        client = TestClient(app)

        # Mock some cost data for testing
        post_id = "test_post_api_001"

        # Make API request
        response = client.get(f"/costs/post/{post_id}")

        # Verify response structure
        assert response.status_code == 200
        data = response.json()

        assert "post_id" in data
        assert "total_cost" in data
        assert "cost_breakdown" in data
        assert "accuracy_score" in data
        assert "audit_trail" in data

        # Verify data types
        assert isinstance(data["total_cost"], float)
        assert isinstance(data["cost_breakdown"], dict)
        assert isinstance(data["accuracy_score"], float)
        assert isinstance(data["audit_trail"], list)

    @pytest.mark.asyncio
    async def test_get_post_cost_summary_endpoint(self):
        """Test GET /costs/post/{post_id}/summary endpoint returns summary."""
        from services.finops_engine.cost_attribution_api import CostAttributionAPI
        from fastapi.testclient import TestClient

        api = CostAttributionAPI()
        app = api.create_app()
        client = TestClient(app)

        post_id = "test_post_api_002"

        # Make API request
        response = client.get(f"/costs/post/{post_id}/summary")

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert "post_id" in data
        assert "total_cost" in data
        assert "primary_cost_type" in data
        assert "cost_efficiency_rating" in data

    @pytest.mark.asyncio
    async def test_get_cost_breakdown_by_date_range_endpoint(self):
        """Test GET /costs/breakdown endpoint with date range filtering."""
        from services.finops_engine.cost_attribution_api import CostAttributionAPI
        from fastapi.testclient import TestClient

        api = CostAttributionAPI()
        app = api.create_app()
        client = TestClient(app)

        # Make API request with date range
        response = client.get(
            "/costs/breakdown",
            params={
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-01-02T00:00:00Z",
                "persona_id": "ai_jesus",
            },
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert "total_posts" in data
        assert "total_cost" in data
        assert "average_cost_per_post" in data
        assert "cost_breakdown_by_type" in data
        assert "posts" in data


class TestCostAttributionIntegration:
    """Integration tests for cost attribution with existing ViralFinOpsEngine."""

    @pytest.mark.asyncio
    async def test_integration_with_viral_finops_engine(self):
        """Test that PostCostAttributor integrates with existing ViralFinOpsEngine.

        This ensures cost attribution works with the existing cost tracking system.
        """
        from services.finops_engine.viral_finops_engine import ViralFinOpsEngine

        # Initialize ViralFinOpsEngine (includes integrated PostCostAttributor)
        engine = ViralFinOpsEngine()

        post_id = "integration_test_001"
        persona_id = "ai_jesus"

        # Track costs through ViralFinOpsEngine (existing system)
        await engine.track_openai_cost(
            model="gpt-4o",
            input_tokens=1000,
            output_tokens=500,
            operation="hook_generation",
            persona_id=persona_id,
            post_id=post_id,
        )

        # Verify integrated PostCostAttributor can access the same data
        breakdown = await engine.post_cost_attributor.get_post_cost_breakdown(post_id)

        assert breakdown["post_id"] == post_id
        assert breakdown["total_cost"] > 0
        assert "openai_api" in breakdown["cost_breakdown"]
        assert breakdown["accuracy_score"] >= 0.95

    @pytest.mark.asyncio
    async def test_cost_attribution_meets_performance_requirements(self):
        """Test that cost attribution meets sub-second performance requirements."""
        from services.finops_engine.post_cost_attributor import PostCostAttributor
        import time

        attributor = PostCostAttributor()

        post_id = "performance_test_001"

        # Track multiple costs
        for i in range(10):
            await attributor.track_cost_for_post(
                post_id=post_id,
                cost_type="openai_api",
                cost_amount=0.001,
                metadata={"operation": f"test_{i}"},
            )

        # Measure query performance
        start_time = time.time()
        breakdown = await attributor.get_post_cost_breakdown(post_id)
        end_time = time.time()

        # Verify sub-second performance
        query_latency_ms = (end_time - start_time) * 1000
        assert query_latency_ms < 500, (
            f"Query latency {query_latency_ms:.2f}ms exceeds 500ms requirement"
        )

        # Verify correct aggregation
        assert breakdown["total_cost"] == 0.01  # 10 * 0.001
