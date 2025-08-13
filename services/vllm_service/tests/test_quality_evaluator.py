"""
Test Quality Evaluator - Validate viral content quality metrics and evaluation algorithms
"""

import pytest
import time
from unittest.mock import patch

from services.vllm_service.quality_evaluator import QualityEvaluator


class TestQualityMetricsCalculation:
    """Test quality metric calculation algorithms for viral content evaluation."""

    @pytest.mark.asyncio
    async def test_length_score_calculation_accuracy(self):
        """Test length score calculation for optimal viral content length."""
        evaluator = QualityEvaluator()

        prompt = "Write a viral hook about productivity"  # 6 words

        # Test optimal length (2-5x prompt length = 12-30 words)
        optimal_response = "🔥 Unpopular opinion: Most productivity advice makes you LESS productive. Here's why 90% of productivity gurus are actually harming your focus and what really works instead."  # ~25 words
        score = evaluator._evaluate_length(optimal_response, prompt)
        assert score == 1.0  # Perfect score for optimal length

        # Test acceptable length (1.5-2x or 5-7x prompt length)
        short_response = (
            "Productivity tips often backfire. Focus on fewer tools."  # ~9 words
        )
        score = evaluator._evaluate_length(short_response, prompt)
        assert score == 0.8  # Good but not perfect

        # Test too short
        very_short = "Productivity is overrated."  # ~3 words
        score = evaluator._evaluate_length(very_short, prompt)
        assert score <= 0.6  # Lower score for inadequate length

    def test_coherence_score_evaluation_factors(self):
        """Test coherence score evaluation considers multiple structural factors."""
        evaluator = QualityEvaluator()

        # High coherence response with proper structure
        coherent_response = """🔥 Unpopular opinion: Most productivity advice makes you LESS productive.

Here's why 90% of "productivity gurus" are actually harming your focus:

1. They sell complexity disguised as simplicity
2. More tools = more cognitive overhead  
3. Constant optimization prevents actual work

The truth? Pick 3 tools. Master them. Ignore everything else.

What's the simplest system that actually works for you?"""

        score = evaluator._evaluate_coherence(coherent_response)

        # Should score highly for multiple coherence factors
        assert score >= 0.8  # High coherence score

        # Test low coherence response
        incoherent_response = "productivity tools bad use less stuff"
        low_score = evaluator._evaluate_coherence(incoherent_response)
        assert low_score < score  # Should score lower
        assert low_score <= 0.5  # Below acceptable threshold

    def test_engagement_score_viral_elements_detection(self):
        """Test engagement score properly detects viral content elements."""
        evaluator = QualityEvaluator()

        # High engagement viral content
        viral_response = """🔥 Unpopular opinion: Your AI stack is broken if you're still doing this...

I see engineering teams burning $10k/month on OpenAI when they could run Llama-3.1-8B locally for 90% less.

The 3 signs your AI costs are out of control:
→ No token optimization strategy
→ No request caching layer  
→ No local model fallbacks

Built vLLM service that cuts AI costs 60% while improving latency.

What's your biggest AI cost pain point?"""

        score = evaluator._evaluate_engagement(viral_response)

        # Should detect multiple viral elements
        assert score >= 0.7  # High engagement score

        # Verify specific viral elements are detected
        response_lower = viral_response.lower()
        assert "unpopular opinion" in response_lower  # Opinion language
        assert "?" in viral_response  # Questions
        assert "🔥" in viral_response  # Engaging emojis
        assert "your" in response_lower  # Personal address

        # Test low engagement content
        boring_response = "AI models can be expensive. Consider alternatives."
        low_score = evaluator._evaluate_engagement(boring_response)
        assert low_score < score
        assert low_score <= 0.4

    def test_overall_quality_weighted_calculation(self):
        """Test overall quality score uses proper weighted average."""
        evaluator = QualityEvaluator()

        # Mock individual scores to test weighting
        with (
            patch.object(evaluator, "_evaluate_length", return_value=0.8),
            patch.object(evaluator, "_evaluate_coherence", return_value=0.9),
            patch.object(evaluator, "_evaluate_engagement", return_value=0.7),
        ):
            # Test the weighted calculation: 0.2 * length + 0.4 * coherence + 0.4 * engagement
            expected = (0.8 * 0.2) + (0.9 * 0.4) + (0.7 * 0.4)
            expected = 0.16 + 0.36 + 0.28  # = 0.8

            prompt = "Test prompt"
            response = "Test response"

            metrics = await evaluator.evaluate_response(prompt, response)

            assert abs(metrics.overall_quality - expected) < 0.001
            assert metrics.length_score == 0.8
            assert metrics.coherence_score == 0.9
            assert metrics.engagement_score == 0.7


class TestViralContentEvaluation:
    """Test quality evaluation specifically for viral content generation."""

    @pytest.mark.asyncio
    async def test_viral_hook_quality_evaluation(self):
        """Test quality evaluation of viral social media hooks."""
        evaluator = QualityEvaluator()

        prompt = "Write a viral hook about AI replacing jobs"
        viral_hook = """🔥 Plot twist: AI isn't taking your job... it's exposing how replaceable your skills became.

The harsh truth? While you were perfecting yesterday's tasks, AI learned to do them in seconds.

But here's what AI can't replace:
→ Strategic thinking that connects dots across industries
→ Emotional intelligence that builds genuine relationships  
→ Creative problem-solving that breaks conventional rules

The question isn't "Will AI replace me?" 

It's "What irreplaceable value am I creating?"

What's one skill you're developing that AI can't touch?"""

        metrics = await evaluator.evaluate_response(prompt, viral_hook)

        # Should score highly on all dimensions for viral content
        assert metrics.overall_quality >= 0.8  # High overall quality
        assert metrics.engagement_score >= 0.7  # Strong viral elements
        assert metrics.coherence_score >= 0.7  # Well-structured
        assert metrics.length_score >= 0.6  # Appropriate length

        # Verify viral content metadata
        assert len(metrics.vllm_response) > 100  # Substantial content
        assert "🔥" in metrics.vllm_response  # Engaging emoji
        assert "?" in metrics.vllm_response  # Engagement question

    @pytest.mark.asyncio
    async def test_low_quality_content_detection(self):
        """Test that low-quality content is properly detected and scored."""
        evaluator = QualityEvaluator()

        prompt = "Create engaging content about productivity"
        low_quality_response = (
            "productivity is good. use tools. be productive. work hard."
        )

        metrics = await evaluator.evaluate_response(prompt, low_quality_response)

        # Should score poorly across dimensions
        assert metrics.overall_quality <= 0.5  # Poor overall quality
        assert metrics.engagement_score <= 0.3  # No engaging elements
        assert metrics.coherence_score <= 0.6  # Poor structure

        # Should categorize as poor quality
        category = evaluator.get_quality_category(metrics.overall_quality)
        assert category in ["poor", "acceptable"]  # Below good quality

    @pytest.mark.asyncio
    async def test_promotional_content_penalty(self):
        """Test that overly promotional content receives engagement penalty."""
        evaluator = QualityEvaluator()

        prompt = "Write about productivity tools"
        promotional_response = """Buy our amazing productivity software now! Special discount offer today!
        
Purchase the best deal in productivity tools. Sale ends soon - buy now and save!
Discount available for limited time. Buy today!"""

        metrics = await evaluator.evaluate_response(prompt, promotional_response)

        # Should receive engagement penalty for excessive promotion
        assert metrics.engagement_score <= 0.4  # Low due to promotional language

        # Overall quality should suffer
        assert metrics.overall_quality <= 0.6


class TestQualityMetricsAggregation:
    """Test quality metrics aggregation and trending analysis."""

    @pytest.mark.asyncio
    async def test_quality_distribution_calculation(self):
        """Test quality distribution categorization for business metrics."""
        evaluator = QualityEvaluator()

        # Add evaluations across quality spectrum
        test_cases = [
            (
                "excellent prompt",
                "🔥 Amazing viral content with perfect structure and engagement!",
                0.95,
            ),
            (
                "good prompt",
                "Solid content with good structure and some viral elements.",
                0.85,
            ),
            (
                "okay prompt",
                "Decent content but lacks engagement and viral potential.",
                0.75,
            ),
            ("poor prompt", "basic content no structure or engagement", 0.45),
        ]

        for prompt, response, expected_range in test_cases:
            await evaluator.evaluate_response(prompt, response)

        metrics = await evaluator.get_metrics()
        distribution = metrics["quality_distribution"]

        # Should categorize across quality levels
        assert distribution["excellent"] >= 1  # At least one excellent
        assert distribution["good"] >= 1  # At least one good
        assert distribution["acceptable"] >= 1  # At least one acceptable
        assert distribution["poor"] >= 1  # At least one poor

        # Total should match number of evaluations
        total_evals = sum(distribution.values())
        assert total_evals == 4

    @pytest.mark.asyncio
    async def test_trending_quality_analysis(self):
        """Test trending quality analysis for optimization insights."""
        evaluator = QualityEvaluator()

        # Simulate improving quality over time
        quality_progression = [0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.9, 0.85]

        for i, target_quality in enumerate(quality_progression):
            # Create response that will score around target quality
            if target_quality >= 0.9:
                response = (
                    "🔥 Excellent viral content with perfect engagement and structure!"
                )
            elif target_quality >= 0.8:
                response = "Great content with good viral elements and solid structure."
            elif target_quality >= 0.7:
                response = (
                    "Good content with some engaging elements and decent structure."
                )
            else:
                response = "Basic content with minimal engagement."

            await evaluator.evaluate_response(f"prompt {i}", response)

        metrics = await evaluator.get_metrics()

        # Should detect improving trend (recent 10 vs overall average)
        assert metrics["trending_quality"] > metrics["average_quality"]
        assert metrics["quality_trend"] == "improving"

    @pytest.mark.asyncio
    async def test_benchmark_comparison_metrics(self):
        """Test benchmark comparison for business performance tracking."""
        evaluator = QualityEvaluator()

        # Add several high-quality evaluations
        high_quality_responses = [
            "🔥 Viral content with excellent engagement and perfect structure!",
            "💡 Amazing insights with great viral potential and solid coherence.",
            "🚀 Outstanding content that hits all viral content requirements.",
        ]

        for i, response in enumerate(high_quality_responses):
            await evaluator.evaluate_response(f"viral prompt {i}", response)

        metrics = await evaluator.get_metrics()
        benchmarks = metrics["benchmarks"]

        # Should show performance against targets
        assert benchmarks["target_quality"] == 0.8  # Target threshold
        assert benchmarks["current_vs_target"] >= 80  # Should meet/exceed target
        assert benchmarks["passing_rate"] >= 80  # High passing rate

    @pytest.mark.asyncio
    async def test_empty_state_handling(self):
        """Test metrics calculation handles empty state gracefully."""
        evaluator = QualityEvaluator()

        metrics = await evaluator.get_metrics()

        # Should handle empty state without errors
        assert metrics["total_evaluations"] == 0
        assert metrics["average_quality"] == 0.0
        assert metrics["trending_quality"] == 0.0
        assert all(v == 0 for v in metrics["quality_distribution"].values())


class TestQualityEvaluationPortfolioMetrics:
    """Test quality evaluation metrics for GenAI portfolio demonstration."""

    @pytest.mark.asyncio
    async def test_viral_content_quality_standards(self):
        """Test that quality evaluation meets viral content standards for portfolio."""
        evaluator = QualityEvaluator()

        # Test with portfolio-quality viral content
        portfolio_content = """🔥 Unpopular opinion: Your AI stack is broken if you're still doing this...

I see engineering teams burning $10k/month on OpenAI when they could run Llama-3.1-8B locally for 90% less.

The 3 signs your AI costs are out of control:
→ No token optimization strategy
→ No request caching layer  
→ No local model fallbacks

Built vLLM service that cuts AI costs 60% while improving latency.

Result: Same quality, fraction of the cost.

What's your biggest AI cost pain point?"""

        metrics = await evaluator.evaluate_response(
            "Create viral content about AI cost optimization", portfolio_content
        )

        # Should meet portfolio quality standards
        assert metrics.overall_quality >= 0.85  # Excellent quality for portfolio
        assert metrics.engagement_score >= 0.8  # High viral potential
        assert metrics.coherence_score >= 0.8  # Professional structure

        # Should categorize as excellent for portfolio demonstration
        category = evaluator.get_quality_category(metrics.overall_quality)
        assert category in ["excellent", "good"]

    @pytest.mark.asyncio
    async def test_quality_consistency_across_topics(self):
        """Test quality evaluation consistency across different viral content topics."""
        evaluator = QualityEvaluator()

        # Test different viral content categories
        content_topics = [
            (
                "productivity",
                "🔥 The productivity hack that changed everything: Do less, achieve more.",
            ),
            (
                "AI/tech",
                "💡 Plot twist: AI isn't replacing developers, it's exposing bad ones.",
            ),
            (
                "career",
                "🚀 Career advice that actually works: Choose boring problems over sexy startups.",
            ),
            (
                "business",
                "💰 The $10M mistake every startup makes: Building features customers don't want.",
            ),
        ]

        quality_scores = []

        for topic, content in content_topics:
            metrics = await evaluator.evaluate_response(
                f"Create viral {topic} content", content
            )
            quality_scores.append(metrics.overall_quality)

        # Should maintain consistent quality across topics
        avg_quality = sum(quality_scores) / len(quality_scores)
        assert avg_quality >= 0.7  # Consistent good quality

        # Variation should be reasonable (not too much variance)
        max_quality = max(quality_scores)
        min_quality = min(quality_scores)
        assert (max_quality - min_quality) <= 0.3  # Consistent evaluation

    @pytest.mark.asyncio
    async def test_quality_evaluation_performance_tracking(self):
        """Test quality evaluation performance for production monitoring."""
        evaluator = QualityEvaluator()

        # Simulate production workload
        start_time = time.time()

        # Process multiple evaluations quickly
        for i in range(10):
            content = f"🔥 Viral content example {i} with engaging elements and proper structure."
            await evaluator.evaluate_response(f"prompt {i}", content)

        evaluation_time = time.time() - start_time

        # Should be fast enough for production use
        assert evaluation_time < 1.0  # Under 1 second for 10 evaluations
        assert len(evaluator.evaluations) == 10

        # Get metrics efficiently
        metrics_start = time.time()
        metrics = await evaluator.get_metrics()
        metrics_time = time.time() - metrics_start

        assert metrics_time < 0.1  # Metrics calculation should be very fast
        assert metrics["total_evaluations"] == 10

    def test_quality_category_thresholds(self):
        """Test quality category thresholds for business reporting."""
        evaluator = QualityEvaluator()

        # Test threshold boundaries
        test_scores = [0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.5, 0.4]
        expected_categories = [
            "excellent",
            "excellent",
            "good",
            "good",
            "acceptable",
            "acceptable",
            "acceptable",
            "poor",
            "poor",
        ]

        for score, expected in zip(test_scores, expected_categories):
            category = evaluator.get_quality_category(score)
            assert category == expected, (
                f"Score {score} should be {expected}, got {category}"
            )

    @pytest.mark.asyncio
    async def test_business_quality_kpis(self):
        """Test business KPIs for quality evaluation portfolio metrics."""
        evaluator = QualityEvaluator()

        # Simulate realistic business scenario
        # Goal: 80% of content should be "good" or "excellent" quality
        content_samples = [
            # 70% high quality content
            "🔥 Excellent viral content with perfect engagement!",
            "💡 Great insights with strong viral potential.",
            "🚀 Amazing content that drives engagement.",
            "⚡ Perfect viral hook with ideal structure.",
            "✨ Outstanding quality with excellent engagement.",
            "🎯 High-quality content with viral elements.",
            "💭 Excellent structure and engagement factors.",
            # 20% good quality content
            "Good content with decent engagement.",
            "Solid structure with some viral elements.",
            # 10% acceptable/poor content
            "Basic content with minimal engagement.",
        ]

        for i, content in enumerate(content_samples):
            await evaluator.evaluate_response(f"prompt {i}", content)

        metrics = await evaluator.get_metrics()

        # Business KPI: 80% should be good or excellent
        total_good_plus = (
            metrics["quality_distribution"]["excellent"]
            + metrics["quality_distribution"]["good"]
        )
        success_rate = (total_good_plus / metrics["total_evaluations"]) * 100

        assert success_rate >= 80.0  # Meet business quality target
        assert metrics["benchmarks"]["passing_rate"] >= 80.0
