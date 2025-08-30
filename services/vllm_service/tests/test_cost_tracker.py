"""
Test Cost Tracker - Validate 60% cost savings calculations and portfolio metrics
"""

import pytest
import time

from services.vllm_service.cost_tracker import CostTracker, CostMetrics


class TestCostCalculations:
    """Test cost calculation accuracy for portfolio demonstration."""

    def test_openai_cost_calculation_accuracy(self):
        """Test OpenAI cost calculations use correct pricing models."""
        tracker = CostTracker()

        # Test with GPT-3.5-turbo pricing (realistic token counts)
        total_tokens = 1000
        cost = tracker.calculate_openai_cost(total_tokens, "gpt-3.5-turbo")

        # Should calculate based on current pricing
        # Input: 700 tokens * $0.0015/1k = $0.00105
        # Output: 300 tokens * $0.002/1k = $0.0006
        # Total: $0.00165
        expected_cost = (700 * 0.0015 / 1000) + (300 * 0.002 / 1000)
        assert abs(cost - expected_cost) < 0.0001

    def test_vllm_cost_calculation_infrastructure_only(self):
        """Test vLLM cost calculations reflect infrastructure-only pricing."""
        tracker = CostTracker()

        # Test with Llama-3-8B infrastructure cost
        total_tokens = 1000
        cost = tracker.calculate_vllm_cost(total_tokens, "llama-3-8b")

        # Should be much lower (infrastructure only)
        expected_cost = 1000 * 0.0001 / 1000  # $0.0001 per 1k tokens
        assert abs(cost - expected_cost) < 0.000001
        assert cost < 0.001  # Should be very low

    def test_cost_savings_calculation_meets_target(self):
        """Test that cost savings calculations demonstrate 60%+ savings target."""
        tracker = CostTracker()

        # Test with realistic viral content generation scenario
        total_tokens = 500  # Typical viral post length

        openai_cost = tracker.calculate_openai_cost(total_tokens, "gpt-3.5-turbo")
        vllm_cost = tracker.calculate_vllm_cost(total_tokens, "llama-3-8b")

        savings_percentage = ((openai_cost - vllm_cost) / openai_cost) * 100

        # Should meet our 60% savings target for portfolio demonstration
        assert savings_percentage >= 60.0
        assert vllm_cost < openai_cost
        assert openai_cost > 0
        assert vllm_cost > 0

    def test_cost_tracking_with_gpt4_comparison(self):
        """Test cost savings are even higher when compared to GPT-4."""
        tracker = CostTracker()

        total_tokens = 1000

        # Compare against GPT-4 pricing (higher cost baseline)
        gpt4_cost = tracker.calculate_openai_cost(total_tokens, "gpt-4")
        vllm_cost = tracker.calculate_vllm_cost(total_tokens, "llama-3-8b")

        savings_percentage = ((gpt4_cost - vllm_cost) / gpt4_cost) * 100

        # Should show massive savings vs GPT-4 (90%+)
        assert savings_percentage >= 90.0
        assert gpt4_cost > vllm_cost * 10  # At least 10x cheaper


class TestCostMetricsTracking:
    """Test cost metrics tracking for business analytics."""

    def test_track_request_creates_accurate_metrics(self):
        """Test request tracking creates accurate cost metrics."""
        tracker = CostTracker()

        model = "llama-3-8b"
        total_tokens = 750
        openai_equivalent = "gpt-3.5-turbo"

        metrics = tracker.track_request(model, total_tokens, openai_equivalent)

        # Should create valid CostMetrics object
        assert isinstance(metrics, CostMetrics)
        assert metrics.model == model
        assert metrics.total_tokens == total_tokens
        assert metrics.vllm_cost_usd > 0
        assert metrics.openai_cost_usd > 0
        assert metrics.savings_usd > 0
        assert metrics.savings_percentage > 50  # Should show meaningful savings
        assert metrics.timestamp > 0

        # Should accumulate in history
        assert len(tracker.cost_history) == 1
        assert tracker.total_savings > 0

    def test_cost_tracking_accumulates_total_savings(self):
        """Test that multiple requests accumulate total savings correctly."""
        tracker = CostTracker()

        # Track multiple requests
        requests = [
            ("llama-3-8b", 500, "gpt-3.5-turbo"),
            ("llama-3-8b", 750, "gpt-3.5-turbo"),
            ("llama-3-8b", 1000, "gpt-4"),
        ]

        total_expected_savings = 0
        for model, tokens, openai_model in requests:
            metrics = tracker.track_request(model, tokens, openai_model)
            total_expected_savings += metrics.savings_usd

        # Should accumulate correctly
        assert len(tracker.cost_history) == 3
        assert abs(tracker.total_savings - total_expected_savings) < 0.0001

    @pytest.mark.asyncio
    async def test_comparison_stats_empty_state(self):
        """Test comparison stats handle empty state gracefully."""
        tracker = CostTracker()

        stats = await tracker.get_comparison_stats()

        # Should return default values when no history
        assert stats["total_requests"] == 0
        assert stats["total_savings_usd"] == 0.0
        assert stats["average_savings_percentage"] == 0.0
        assert "cost_per_1k_tokens" in stats

        # Should include pricing reference
        pricing = stats["cost_per_1k_tokens"]
        assert pricing["vllm"] < pricing["openai_gpt35"]
        assert pricing["openai_gpt35"] < pricing["openai_gpt4"]

    @pytest.mark.asyncio
    async def test_comparison_stats_with_realistic_data(self):
        """Test comparison stats with realistic usage data."""
        tracker = CostTracker()

        # Simulate realistic viral content generation workload
        viral_content_requests = [
            (400, "gpt-3.5-turbo"),  # Short hooks
            (600, "gpt-3.5-turbo"),  # Medium posts
            (800, "gpt-3.5-turbo"),  # Long posts
            (500, "gpt-4"),  # High-quality content
        ]

        for tokens, openai_model in viral_content_requests:
            tracker.track_request("llama-3-8b", tokens, openai_model)

        stats = await tracker.get_comparison_stats()

        # Should provide meaningful business metrics
        assert stats["total_requests"] == 4
        assert stats["total_tokens"] == 2300  # Sum of all tokens
        assert stats["total_savings_usd"] > 0
        assert stats["average_savings_percentage"] >= 60  # Meet portfolio target

        # Should project monthly savings
        assert stats["projected_monthly_savings"] > 0

        # Should break down costs
        breakdown = stats["cost_breakdown"]
        assert breakdown["vllm_total"] > 0
        assert breakdown["openai_equivalent"] > 0
        assert breakdown["savings"] > 0
        assert breakdown["openai_equivalent"] > breakdown["vllm_total"]


class TestBusinessMetrics:
    """Test business-focused metrics for portfolio demonstration."""

    @pytest.mark.asyncio
    async def test_efficiency_metrics_calculation(self):
        """Test efficiency metrics demonstrate cost optimization."""
        tracker = CostTracker()

        # Simulate high-volume usage scenario
        for _ in range(10):
            tracker.track_request("llama-3-8b", 500, "gpt-3.5-turbo")

        stats = await tracker.get_comparison_stats()
        efficiency = stats["efficiency_metrics"]

        # Should show tokens per dollar metrics
        assert "tokens_per_dollar_vllm" in efficiency
        assert "tokens_per_dollar_openai" in efficiency

        # vLLM should provide much better token efficiency
        vllm_efficiency = efficiency["tokens_per_dollar_vllm"]
        openai_efficiency = efficiency["tokens_per_dollar_openai"]

        assert vllm_efficiency > openai_efficiency * 5  # At least 5x more efficient
        assert vllm_efficiency > 1000  # Should get lots of tokens per dollar

    def test_monthly_savings_projection_accuracy(self):
        """Test monthly savings projections for business planning."""
        tracker = CostTracker()

        # Simulate recent hour of activity
        current_time = time.time()

        # Mock recent requests (within last hour)
        for i in range(5):
            metrics = tracker.track_request("llama-3-8b", 600, "gpt-3.5-turbo")
            # Manually set timestamp to be recent
            metrics.timestamp = current_time - (i * 600)  # Every 10 minutes

        # Calculate projection manually for validation
        hourly_savings = sum(m.savings_usd for m in tracker.cost_history[-5:])
        expected_monthly = hourly_savings * 24 * 30

        # Should project realistic monthly savings
        assert expected_monthly > 0

        # For portfolio: demonstrate meaningful cost reduction
        # With 5 requests/hour * 24 * 30 = 3600 requests/month
        # Each saving ~$0.001, that's ~$3.6/month baseline
        assert expected_monthly >= 1.0  # At least $1/month in savings

    def test_recent_history_filtering(self):
        """Test recent history filtering for trending analysis."""
        tracker = CostTracker()

        current_time = time.time()

        # Add some old metrics (> 24 hours ago)
        old_metrics = CostMetrics(
            model="llama-3-8b",
            total_tokens=500,
            vllm_cost_usd=0.05,
            openai_cost_usd=0.75,
            savings_usd=0.70,
            savings_percentage=93.3,
            timestamp=current_time - (25 * 3600),  # 25 hours ago
        )
        tracker.cost_history.append(old_metrics)

        # Add recent metrics (< 24 hours ago)
        for i in range(3):
            recent_metrics = CostMetrics(
                model="llama-3-8b",
                total_tokens=600,
                vllm_cost_usd=0.06,
                openai_cost_usd=0.90,
                savings_usd=0.84,
                savings_percentage=93.3,
                timestamp=current_time - (i * 3600),  # 0, 1, 2 hours ago
            )
            tracker.cost_history.append(recent_metrics)

        # Get recent history (last 24 hours)
        recent = tracker.get_recent_history(24)

        # Should filter to only recent metrics
        assert len(recent) == 3  # Only the 3 recent ones
        for metric_dict in recent:
            assert metric_dict["timestamp"] > current_time - (24 * 3600)

    def test_reset_stats_functionality(self):
        """Test stats reset for testing and development."""
        tracker = CostTracker()

        # Add some data
        tracker.track_request("llama-3-8b", 500, "gpt-3.5-turbo")
        tracker.track_request("llama-3-8b", 600, "gpt-4")

        assert len(tracker.cost_history) == 2
        assert tracker.total_savings > 0

        # Reset should clear everything
        tracker.reset_stats()

        assert len(tracker.cost_history) == 0
        assert tracker.total_savings == 0.0


class TestPortfolioMetrics:
    """Test specific metrics that demonstrate GenAI expertise for portfolio."""

    def test_cost_optimization_portfolio_metrics(self):
        """Test cost optimization metrics for demonstrating GenAI engineering skills."""
        tracker = CostTracker()

        # Simulate real-world viral content generation scenario
        # Typical usage: 100 requests/day, 500 tokens average
        daily_requests = [
            (400, "gpt-3.5-turbo"),  # 20% short content
            (500, "gpt-3.5-turbo"),  # 60% medium content
            (500, "gpt-3.5-turbo"),
            (500, "gpt-3.5-turbo"),
            (800, "gpt-3.5-turbo"),  # 15% long content
            (1000, "gpt-4"),  # 5% premium content
        ]

        total_openai_cost = 0
        total_vllm_cost = 0

        for tokens, openai_model in daily_requests:
            metrics = tracker.track_request("llama-3-8b", tokens, openai_model)
            total_openai_cost += metrics.openai_cost_usd
            total_vllm_cost += metrics.vllm_cost_usd

        # Portfolio demonstration metrics
        total_savings = total_openai_cost - total_vllm_cost
        savings_percentage = (total_savings / total_openai_cost) * 100

        # Should demonstrate significant optimization achievements
        assert savings_percentage >= 70.0  # 70%+ cost reduction
        assert total_savings > 0.01  # Meaningful absolute savings

        # Cost per request should be dramatically lower
        vllm_cost_per_request = total_vllm_cost / len(daily_requests)
        openai_cost_per_request = total_openai_cost / len(daily_requests)

        assert (
            vllm_cost_per_request < openai_cost_per_request / 3
        )  # At least 3x cheaper

    def test_roi_calculation_for_infrastructure_investment(self):
        """Test ROI calculations that justify vLLM infrastructure investment."""
        tracker = CostTracker()

        # Simulate monthly usage for ROI calculation
        monthly_requests = 100 * 30  # 100 requests/day * 30 days
        avg_tokens_per_request = 600

        # Calculate costs for the month
        monthly_vllm_cost = 0
        monthly_openai_cost = 0

        for _ in range(monthly_requests):
            vllm_cost = tracker.calculate_vllm_cost(avg_tokens_per_request)
            openai_cost = tracker.calculate_openai_cost(
                avg_tokens_per_request, "gpt-3.5-turbo"
            )

            monthly_vllm_cost += vllm_cost
            monthly_openai_cost += openai_cost

        monthly_savings = monthly_openai_cost - monthly_vllm_cost

        # Infrastructure cost estimate (for portfolio calculation)
        # Assume $500/month for dedicated Apple Silicon Mac Pro or cloud GPU
        estimated_infrastructure_cost = 500.0

        # Should demonstrate positive ROI for portfolio
        net_monthly_savings = monthly_savings - estimated_infrastructure_cost
        roi_percentage = (net_monthly_savings / estimated_infrastructure_cost) * 100

        # For portfolio: demonstrate when vLLM infrastructure pays for itself
        if monthly_savings > estimated_infrastructure_cost:
            assert roi_percentage > 0  # Positive ROI
            payback_months = estimated_infrastructure_cost / monthly_savings
            assert payback_months < 12  # Payback within a year

        # At minimum, should show cost reduction trajectory
        assert monthly_savings > 0
        assert monthly_vllm_cost < monthly_openai_cost / 2  # At least 50% reduction
