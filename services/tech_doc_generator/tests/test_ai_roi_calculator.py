"""
Tests for AI ROI Calculator

Comprehensive test suite covering:
- ROI calculations with various inputs
- Industry benchmarks and comparisons  
- API endpoints and error handling
- Lead generation workflows
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
import asyncio

from app.services.ai_roi_calculator import (
    AIROICalculator,
    ROIInput,
    AIUseCase,
    IndustryType,
    get_ai_roi_calculator
)


@pytest.fixture
def sample_roi_input():
    """Sample ROI input for testing"""
    return ROIInput(
        use_case=AIUseCase.CONTENT_GENERATION,
        industry=IndustryType.TECHNOLOGY,
        company_size="medium",
        current_monthly_hours=100.0,
        hourly_cost=75.0,
        ai_monthly_cost=500.0,
        implementation_cost=5000.0,
        expected_efficiency_gain=0.4,
        revenue_impact=1000.0,
        time_horizon_months=12
    )


@pytest.fixture
def ai_roi_calculator():
    """AI ROI Calculator instance for testing"""
    return AIROICalculator()


@pytest.mark.asyncio
class TestAIROICalculator:
    """Test suite for AI ROI Calculator core logic"""
    
    async def test_calculator_initialization(self, ai_roi_calculator):
        """Test calculator initializes with proper benchmarks"""
        assert len(ai_roi_calculator.industry_benchmarks) == 8
        assert len(ai_roi_calculator.use_case_multipliers) == 8
        
        # Test specific industry benchmark
        tech_benchmark = ai_roi_calculator.industry_benchmarks[IndustryType.TECHNOLOGY]
        assert tech_benchmark.average_roi == 245.0
        assert tech_benchmark.typical_payback_months == 8.5
        assert tech_benchmark.success_rate == 0.78
        assert len(tech_benchmark.best_practices) > 0
        assert len(tech_benchmark.common_challenges) > 0
    
    async def test_basic_roi_calculation(self, ai_roi_calculator, sample_roi_input):
        """Test basic ROI calculation with sample data"""
        result = await ai_roi_calculator.calculate_roi(sample_roi_input)
        
        # Verify result structure
        assert result.metrics is not None
        assert result.benchmark is not None
        assert len(result.insights) > 0
        assert len(result.recommendations) > 0
        assert result.success_probability > 0
        assert result.report_id is not None
        
        # Verify metrics calculations
        metrics = result.metrics
        assert metrics.monthly_time_savings_hours > 0
        assert metrics.monthly_cost_savings > 0
        assert metrics.annual_cost_savings == metrics.monthly_cost_savings * 12
        assert metrics.roi_percentage > 0
        assert metrics.payback_period_months > 0
    
    async def test_high_efficiency_gain_scenario(self, ai_roi_calculator):
        """Test scenario with high efficiency gains"""
        high_efficiency_input = ROIInput(
            use_case=AIUseCase.DOCUMENT_PROCESSING,  # High multiplier
            industry=IndustryType.HEALTHCARE,
            company_size="large",
            current_monthly_hours=200.0,
            hourly_cost=100.0,
            ai_monthly_cost=1000.0,
            implementation_cost=20000.0,
            expected_efficiency_gain=0.8,  # 80% efficiency gain
            time_horizon_months=24
        )
        
        result = await ai_roi_calculator.calculate_roi(high_efficiency_input)
        
        # Should have excellent ROI due to high efficiency gains
        assert result.metrics.roi_percentage > 200
        assert result.metrics.monthly_time_savings_hours > 100
        assert result.success_probability > 0.7
        
        # Should have insights about exceptional performance
        insights_text = " ".join(result.insights).lower()
        assert "exceptional" in insights_text or "high" in insights_text
    
    async def test_low_roi_scenario(self, ai_roi_calculator):
        """Test scenario with challenging ROI"""
        low_roi_input = ROIInput(
            use_case=AIUseCase.PREDICTIVE_ANALYTICS,
            industry=IndustryType.EDUCATION,  # Lower average ROI
            company_size="small",
            current_monthly_hours=20.0,  # Low hours
            hourly_cost=40.0,  # Low cost
            ai_monthly_cost=2000.0,  # High AI cost relative to savings
            implementation_cost=50000.0,  # High implementation cost
            expected_efficiency_gain=0.2,  # Low efficiency gain
            time_horizon_months=12
        )
        
        result = await ai_roi_calculator.calculate_roi(low_roi_input)
        
        # Should have challenging metrics
        assert result.metrics.payback_period_months > 12
        assert result.success_probability < 0.8
        
        # Should have recommendations for improvement
        recommendations_text = " ".join(result.recommendations).lower()
        assert "phased" in recommendations_text or "cost" in recommendations_text
    
    async def test_different_industries(self, ai_roi_calculator, sample_roi_input):
        """Test ROI calculation across different industries"""
        industries_to_test = [
            IndustryType.TECHNOLOGY,
            IndustryType.FINANCE,
            IndustryType.HEALTHCARE,
            IndustryType.RETAIL
        ]
        
        results = []
        for industry in industries_to_test:
            test_input = sample_roi_input
            test_input.industry = industry
            result = await ai_roi_calculator.calculate_roi(test_input)
            results.append((industry, result))
        
        # All should complete successfully
        assert len(results) == 4
        
        # Each should have industry-specific insights
        for industry, result in results:
            assert result.benchmark.average_roi > 0
            assert len(result.benchmark.best_practices) > 0
            assert len(result.insights) > 0
    
    async def test_different_use_cases(self, ai_roi_calculator):
        """Test different AI use cases"""
        base_input = ROIInput(
            use_case=AIUseCase.CONTENT_GENERATION,  # Will be overridden
            industry=IndustryType.TECHNOLOGY,
            company_size="medium",
            current_monthly_hours=80.0,
            hourly_cost=85.0,
            ai_monthly_cost=600.0,
            implementation_cost=8000.0,
            expected_efficiency_gain=0.5,
            time_horizon_months=12
        )
        
        use_cases_to_test = [
            AIUseCase.CONTENT_GENERATION,
            AIUseCase.CUSTOMER_SUPPORT,
            AIUseCase.DATA_ANALYSIS,
            AIUseCase.CODE_GENERATION
        ]
        
        results = []
        for use_case in use_cases_to_test:
            test_input = base_input
            test_input.use_case = use_case
            result = await ai_roi_calculator.calculate_roi(test_input)
            results.append((use_case, result))
        
        # All should complete successfully with different efficiency multipliers
        assert len(results) == 4
        
        # Results should vary based on use case multipliers
        roi_values = [result.metrics.roi_percentage for _, result in results]
        assert len(set(roi_values)) > 1  # Should have different ROI values
    
    async def test_company_size_impact(self, ai_roi_calculator, sample_roi_input):
        """Test impact of company size on calculations"""
        company_sizes = ["startup", "small", "medium", "large", "enterprise"]
        
        results = []
        for size in company_sizes:
            test_input = sample_roi_input
            test_input.company_size = size
            result = await ai_roi_calculator.calculate_roi(test_input)
            results.append((size, result))
        
        # All should complete successfully
        assert len(results) == 5
        
        # Different company sizes should have different timelines
        timeline_lengths = [len(result.implementation_timeline) for _, result in results]
        assert len(set(timeline_lengths)) > 1  # Should have different timeline lengths
    
    async def test_revenue_impact_inclusion(self, ai_roi_calculator, sample_roi_input):
        """Test ROI calculation with and without revenue impact"""
        # Test without revenue impact
        no_revenue_input = sample_roi_input
        no_revenue_input.revenue_impact = None
        result_no_revenue = await ai_roi_calculator.calculate_roi(no_revenue_input)
        
        # Test with revenue impact
        with_revenue_input = sample_roi_input
        with_revenue_input.revenue_impact = 2000.0  # $2000/month revenue increase
        result_with_revenue = await ai_roi_calculator.calculate_roi(with_revenue_input)
        
        # Revenue impact should increase total ROI
        assert result_with_revenue.metrics.roi_percentage > result_no_revenue.metrics.roi_percentage
        assert result_with_revenue.metrics.total_benefits_annual > result_no_revenue.metrics.total_benefits_annual
        assert result_with_revenue.metrics.revenue_impact_annual > 0
        assert result_no_revenue.metrics.revenue_impact_annual == 0
    
    async def test_success_probability_calculation(self, ai_roi_calculator):
        """Test success probability calculation logic"""
        # High success probability scenario
        high_success_input = ROIInput(
            use_case=AIUseCase.CONTENT_GENERATION,
            industry=IndustryType.CONSULTING,  # High success rate industry
            company_size="startup",  # Agile implementation
            current_monthly_hours=150.0,
            hourly_cost=90.0,
            ai_monthly_cost=400.0,
            implementation_cost=3000.0,
            expected_efficiency_gain=0.6,
            time_horizon_months=12
        )
        
        high_result = await ai_roi_calculator.calculate_roi(high_success_input)
        
        # Low success probability scenario
        low_success_input = ROIInput(
            use_case=AIUseCase.PREDICTIVE_ANALYTICS,
            industry=IndustryType.EDUCATION,  # Lower success rate
            company_size="enterprise",  # Less agile
            current_monthly_hours=30.0,
            hourly_cost=45.0,
            ai_monthly_cost=3000.0,
            implementation_cost=100000.0,
            expected_efficiency_gain=0.15,
            time_horizon_months=12
        )
        
        low_result = await ai_roi_calculator.calculate_roi(low_success_input)
        
        # High success scenario should have higher probability
        assert high_result.success_probability > low_result.success_probability
        assert high_result.success_probability <= 0.95  # Capped at 95%
        assert low_result.success_probability > 0.0  # Always positive
    
    async def test_edge_cases(self, ai_roi_calculator):
        """Test edge cases and boundary conditions"""
        # Minimum values
        min_input = ROIInput(
            use_case=AIUseCase.CONTENT_GENERATION,
            industry=IndustryType.TECHNOLOGY,
            company_size="startup",
            current_monthly_hours=1.0,  # Minimum hours
            hourly_cost=10.0,  # Minimum cost
            ai_monthly_cost=0.0,  # Free AI solution
            implementation_cost=0.0,  # No implementation cost
            expected_efficiency_gain=0.1,  # 10% gain
            time_horizon_months=6  # Minimum horizon
        )
        
        min_result = await ai_roi_calculator.calculate_roi(min_input)
        assert min_result.metrics.roi_percentage >= 0
        assert min_result.success_probability > 0
        
        # High values
        max_input = ROIInput(
            use_case=AIUseCase.INFRASTRUCTURE_OPTIMIZATION,
            industry=IndustryType.MANUFACTURING,
            company_size="enterprise",
            current_monthly_hours=1000.0,  # High hours
            hourly_cost=500.0,  # High cost
            ai_monthly_cost=50000.0,  # Expensive AI
            implementation_cost=500000.0,  # Large implementation
            expected_efficiency_gain=0.95,  # 95% gain
            time_horizon_months=60  # Long horizon
        )
        
        max_result = await ai_roi_calculator.calculate_roi(max_input)
        assert max_result.metrics.roi_percentage >= 0
        assert max_result.success_probability <= 0.95
    
    def test_singleton_pattern(self):
        """Test that get_ai_roi_calculator returns singleton"""
        calculator1 = get_ai_roi_calculator()
        calculator2 = get_ai_roi_calculator()
        
        assert calculator1 is calculator2


@pytest.mark.asyncio
class TestROIInsightsAndRecommendations:
    """Test suite for insights and recommendations generation"""
    
    async def test_insights_generation(self, ai_roi_calculator, sample_roi_input):
        """Test that insights are relevant and actionable"""
        result = await ai_roi_calculator.calculate_roi(sample_roi_input)
        
        insights = result.insights
        assert len(insights) > 0
        assert len(insights) <= 10  # Reasonable number
        
        # Should contain ROI comparison
        insights_text = " ".join(insights).lower()
        assert "roi" in insights_text or "return" in insights_text
        
        # Should contain actionable insights
        assert any("%" in insight for insight in insights)  # Percentage metrics
    
    async def test_recommendations_quality(self, ai_roi_calculator, sample_roi_input):
        """Test that recommendations are specific and actionable"""
        result = await ai_roi_calculator.calculate_roi(sample_roi_input)
        
        recommendations = result.recommendations
        assert len(recommendations) > 0
        assert len(recommendations) <= 6  # Limited to top recommendations
        
        # Should contain actionable language
        recommendations_text = " ".join(recommendations).lower()
        assert any(action_word in recommendations_text 
                  for action_word in ["start", "focus", "implement", "consider", "ensure"])
        
        # Should include industry best practices
        benchmark = ai_roi_calculator.industry_benchmarks[sample_roi_input.industry]
        first_best_practice = benchmark.best_practices[0].lower()
        recommendations_lower = [r.lower() for r in recommendations]
        assert any(first_best_practice in rec for rec in recommendations_lower)
    
    async def test_risk_factors_identification(self, ai_roi_calculator, sample_roi_input):
        """Test risk factor identification"""
        result = await ai_roi_calculator.calculate_roi(sample_roi_input)
        
        risk_factors = result.risk_factors
        assert len(risk_factors) > 0
        assert len(risk_factors) <= 5  # Limited to top risks
        
        # Should include industry-specific challenges
        benchmark = ai_roi_calculator.industry_benchmarks[sample_roi_input.industry]
        first_challenge = benchmark.common_challenges[0].lower()
        risks_text = " ".join(risk_factors).lower()
        assert first_challenge in risks_text
    
    async def test_implementation_timeline(self, ai_roi_calculator, sample_roi_input):
        """Test implementation timeline generation"""
        result = await ai_roi_calculator.calculate_roi(sample_roi_input)
        
        timeline = result.implementation_timeline
        assert len(timeline) > 0
        
        # Should contain time-based phases
        timeline_text = " ".join(timeline).lower()
        assert any(time_word in timeline_text 
                  for time_word in ["week", "month", "phase"])


@pytest.mark.asyncio
class TestROICalculatorPerformance:
    """Performance tests for ROI calculator"""
    
    async def test_calculation_performance(self, ai_roi_calculator, sample_roi_input):
        """Test that ROI calculations complete quickly"""
        import time
        
        start_time = time.time()
        result = await ai_roi_calculator.calculate_roi(sample_roi_input)
        end_time = time.time()
        
        calculation_time = end_time - start_time
        
        # Should complete within reasonable time
        assert calculation_time < 1.0  # Less than 1 second
        assert result is not None
    
    async def test_concurrent_calculations(self, ai_roi_calculator):
        """Test concurrent ROI calculations"""
        # Create multiple inputs
        inputs = []
        for i in range(5):
            input_data = ROIInput(
                use_case=list(AIUseCase)[i % len(AIUseCase)],
                industry=list(IndustryType)[i % len(IndustryType)],
                company_size=["startup", "small", "medium", "large", "enterprise"][i],
                current_monthly_hours=50.0 + i * 20,
                hourly_cost=60.0 + i * 10,
                ai_monthly_cost=400.0 + i * 100,
                implementation_cost=3000.0 + i * 1000,
                expected_efficiency_gain=0.3 + i * 0.1,
                time_horizon_months=12
            )
            inputs.append(input_data)
        
        # Run calculations concurrently
        tasks = [ai_roi_calculator.calculate_roi(input_data) for input_data in inputs]
        results = await asyncio.gather(*tasks)
        
        # All should complete successfully
        assert len(results) == 5
        assert all(result.metrics.roi_percentage >= 0 for result in results)
        assert all(len(result.insights) > 0 for result in results)


class TestROIInputValidation:
    """Test suite for ROI input validation"""
    
    def test_valid_roi_input_creation(self):
        """Test creating valid ROI input"""
        roi_input = ROIInput(
            use_case=AIUseCase.CONTENT_GENERATION,
            industry=IndustryType.TECHNOLOGY,
            company_size="medium",
            current_monthly_hours=100.0,
            hourly_cost=75.0,
            ai_monthly_cost=500.0,
            implementation_cost=5000.0,
            expected_efficiency_gain=0.4,
            time_horizon_months=12
        )
        
        assert roi_input.use_case == AIUseCase.CONTENT_GENERATION
        assert roi_input.industry == IndustryType.TECHNOLOGY
        assert roi_input.expected_efficiency_gain == 0.4
        assert roi_input.revenue_impact is None  # Optional field
    
    def test_roi_input_with_optional_fields(self):
        """Test ROI input with optional fields"""
        roi_input = ROIInput(
            use_case=AIUseCase.DATA_ANALYSIS,
            industry=IndustryType.FINANCE,
            company_size="large",
            current_monthly_hours=200.0,
            hourly_cost=120.0,
            ai_monthly_cost=1500.0,
            implementation_cost=25000.0,
            expected_efficiency_gain=0.6,
            revenue_impact=5000.0,  # Optional
            quality_improvement=0.3,  # Optional
            time_horizon_months=24
        )
        
        assert roi_input.revenue_impact == 5000.0
        assert roi_input.quality_improvement == 0.3
        assert roi_input.time_horizon_months == 24