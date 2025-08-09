#!/usr/bin/env python3
"""
Simple AI ROI Calculator Demo

Demonstrates core ROI calculation logic without dependencies.
Shows the value proposition of the AI ROI Calculator tool.
"""

import asyncio
from dataclasses import dataclass
from enum import Enum


class AIUseCase(Enum):
    """Common AI use cases for ROI calculation"""

    CONTENT_GENERATION = "content_generation"
    CUSTOMER_SUPPORT = "customer_support"
    DATA_ANALYSIS = "data_analysis"
    CODE_GENERATION = "code_generation"
    DOCUMENT_PROCESSING = "document_processing"
    PREDICTIVE_ANALYTICS = "predictive_analytics"
    MARKETING_AUTOMATION = "marketing_automation"
    INFRASTRUCTURE_OPTIMIZATION = "infrastructure_optimization"


class IndustryType(Enum):
    """Industry types for benchmarking"""

    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    RETAIL = "retail"
    MANUFACTURING = "manufacturing"
    EDUCATION = "education"
    MEDIA = "media"
    CONSULTING = "consulting"


@dataclass
class ROIMetrics:
    """Calculated ROI metrics"""

    monthly_time_savings_hours: float
    monthly_cost_savings: float
    annual_cost_savings: float
    payback_period_months: float
    roi_percentage: float
    net_present_value: float
    revenue_impact_annual: float
    total_benefits_annual: float
    total_costs_annual: float
    break_even_month: int


class SimpleAIROICalculator:
    """Simplified AI ROI Calculator for demo purposes"""

    def __init__(self):
        self.industry_benchmarks = {
            IndustryType.TECHNOLOGY: {
                "average_roi": 245.0,
                "typical_payback_months": 8.5,
                "success_rate": 0.78,
                "description": "High innovation adoption, strong technical teams",
            },
            IndustryType.HEALTHCARE: {
                "average_roi": 320.0,
                "typical_payback_months": 15.0,
                "success_rate": 0.70,
                "description": "High impact potential, regulatory complexity",
            },
            IndustryType.FINANCE: {
                "average_roi": 180.0,
                "typical_payback_months": 12.0,
                "success_rate": 0.65,
                "description": "Compliance focus, risk management priority",
            },
            IndustryType.RETAIL: {
                "average_roi": 165.0,
                "typical_payback_months": 9.0,
                "success_rate": 0.72,
                "description": "Customer experience focus, seasonal variations",
            },
            IndustryType.CONSULTING: {
                "average_roi": 275.0,
                "typical_payback_months": 6.0,
                "success_rate": 0.80,
                "description": "High leverage, client value multiplication",
            },
        }

        self.use_case_multipliers = {
            AIUseCase.CONTENT_GENERATION: 1.2,
            AIUseCase.CUSTOMER_SUPPORT: 1.4,
            AIUseCase.DATA_ANALYSIS: 1.8,
            AIUseCase.CODE_GENERATION: 1.6,
            AIUseCase.DOCUMENT_PROCESSING: 2.0,
            AIUseCase.PREDICTIVE_ANALYTICS: 1.3,
            AIUseCase.MARKETING_AUTOMATION: 1.5,
            AIUseCase.INFRASTRUCTURE_OPTIMIZATION: 2.2,
        }

    async def calculate_roi(
        self,
        use_case,
        industry,
        company_size,
        current_monthly_hours,
        hourly_cost,
        ai_monthly_cost,
        implementation_cost,
        expected_efficiency_gain,
        revenue_impact=None,
        time_horizon_months=12,
    ):
        """Calculate comprehensive ROI analysis"""

        # Apply use case multiplier to efficiency gain
        use_case_multiplier = self.use_case_multipliers[use_case]
        effective_efficiency_gain = min(
            0.95, expected_efficiency_gain * use_case_multiplier
        )

        # Calculate time and cost savings
        monthly_time_savings_hours = current_monthly_hours * effective_efficiency_gain
        monthly_cost_savings = monthly_time_savings_hours * hourly_cost
        annual_cost_savings = monthly_cost_savings * 12

        # Calculate net savings (subtract AI costs)
        net_monthly_savings = monthly_cost_savings - ai_monthly_cost
        net_annual_savings = net_monthly_savings * 12

        # Calculate revenue impact
        revenue_impact_annual = 0.0
        if revenue_impact:
            revenue_impact_annual = revenue_impact * 12

        # Total benefits and costs
        total_benefits_annual = net_annual_savings + revenue_impact_annual
        total_costs_annual = (ai_monthly_cost * 12) + implementation_cost

        # Calculate ROI percentage
        if total_costs_annual > 0:
            roi_percentage = (total_benefits_annual / total_costs_annual) * 100
        else:
            roi_percentage = 0.0

        # Calculate payback period
        if net_monthly_savings > 0:
            payback_period_months = implementation_cost / net_monthly_savings
        else:
            payback_period_months = float("inf")

        # Calculate NPV (simplified with 10% discount rate)
        discount_rate = 0.10
        npv = 0.0
        for month in range(1, time_horizon_months + 1):
            monthly_benefit = net_monthly_savings + (
                revenue_impact_annual / 12 if revenue_impact else 0
            )
            discounted_benefit = monthly_benefit / ((1 + discount_rate / 12) ** month)
            npv += discounted_benefit
        npv -= implementation_cost

        # Break-even month
        break_even_month = (
            int(payback_period_months) + 1
            if payback_period_months != float("inf")
            else 0
        )

        metrics = ROIMetrics(
            monthly_time_savings_hours=monthly_time_savings_hours,
            monthly_cost_savings=monthly_cost_savings,
            annual_cost_savings=annual_cost_savings,
            payback_period_months=payback_period_months,
            roi_percentage=roi_percentage,
            net_present_value=npv,
            revenue_impact_annual=revenue_impact_annual,
            total_benefits_annual=total_benefits_annual,
            total_costs_annual=total_costs_annual,
            break_even_month=break_even_month,
        )

        # Generate insights
        benchmark = self.industry_benchmarks[industry]
        insights = self.generate_insights(metrics, benchmark)
        success_probability = self.calculate_success_probability(
            metrics, benchmark, company_size
        )

        return {
            "metrics": metrics,
            "benchmark": benchmark,
            "insights": insights,
            "success_probability": success_probability,
        }

    def generate_insights(self, metrics, benchmark):
        """Generate actionable insights"""
        insights = []

        # ROI comparison
        if metrics.roi_percentage > benchmark["average_roi"] * 1.2:
            insights.append(
                f"🎯 Exceptional ROI potential: {metrics.roi_percentage:.1f}% vs industry average of {benchmark['average_roi']:.1f}%"
            )
        elif metrics.roi_percentage > benchmark["average_roi"]:
            insights.append(
                f"📈 Above-average ROI: {metrics.roi_percentage:.1f}% vs industry average of {benchmark['average_roi']:.1f}%"
            )
        else:
            insights.append(
                f"⚠️ Below-average ROI: {metrics.roi_percentage:.1f}% vs industry average of {benchmark['average_roi']:.1f}%"
            )

        # Payback analysis
        if metrics.payback_period_months < benchmark["typical_payback_months"]:
            insights.append(
                f"⚡ Fast payback: {metrics.payback_period_months:.1f} months vs typical {benchmark['typical_payback_months']:.1f} months"
            )
        else:
            insights.append(
                f"⏰ Extended payback: {metrics.payback_period_months:.1f} months vs typical {benchmark['typical_payback_months']:.1f} months"
            )

        # Time savings
        if metrics.monthly_time_savings_hours > 40:
            insights.append(
                f"🚀 Major time liberation: {metrics.monthly_time_savings_hours:.1f} hours/month for strategic work"
            )
        elif metrics.monthly_time_savings_hours > 20:
            insights.append(
                f"⏱️ Solid time savings: {metrics.monthly_time_savings_hours:.1f} hours/month for higher-value activities"
            )

        # Cost impact
        if metrics.annual_cost_savings > 100000:
            insights.append(
                f"💰 Major cost impact: ${metrics.annual_cost_savings:,.0f} annual savings"
            )
        elif metrics.annual_cost_savings > 25000:
            insights.append(
                f"💵 Solid cost savings: ${metrics.annual_cost_savings:,.0f} annually"
            )

        return insights

    def calculate_success_probability(self, metrics, benchmark, company_size):
        """Calculate implementation success probability"""
        base_probability = benchmark["success_rate"]

        # Adjust based on ROI
        roi_factor = 1.0
        if metrics.roi_percentage > benchmark["average_roi"] * 1.5:
            roi_factor = 1.2
        elif metrics.roi_percentage < benchmark["average_roi"] * 0.5:
            roi_factor = 0.8

        # Adjust based on company size
        size_factor = 1.0
        if company_size in ["startup", "small"]:
            size_factor = 1.1  # More agile
        elif company_size == "enterprise":
            size_factor = 0.95  # More complex

        return min(0.95, base_probability * roi_factor * size_factor)


async def demo_scenarios():
    """Run demo scenarios"""
    calculator = SimpleAIROICalculator()

    print("🚀 AI ROI Calculator Demo")
    print("=" * 50)

    scenarios = [
        {
            "name": "Content Generation - Tech Company",
            "use_case": AIUseCase.CONTENT_GENERATION,
            "industry": IndustryType.TECHNOLOGY,
            "company_size": "medium",
            "current_monthly_hours": 120.0,
            "hourly_cost": 85.0,
            "ai_monthly_cost": 750.0,
            "implementation_cost": 8000.0,
            "expected_efficiency_gain": 0.55,
            "revenue_impact": 2500.0,
        },
        {
            "name": "Customer Support - Healthcare",
            "use_case": AIUseCase.CUSTOMER_SUPPORT,
            "industry": IndustryType.HEALTHCARE,
            "company_size": "large",
            "current_monthly_hours": 400.0,
            "hourly_cost": 65.0,
            "ai_monthly_cost": 1200.0,
            "implementation_cost": 35000.0,
            "expected_efficiency_gain": 0.7,
            "revenue_impact": None,
        },
        {
            "name": "Data Analysis - Finance",
            "use_case": AIUseCase.DATA_ANALYSIS,
            "industry": IndustryType.FINANCE,
            "company_size": "enterprise",
            "current_monthly_hours": 320.0,
            "hourly_cost": 95.0,
            "ai_monthly_cost": 2000.0,
            "implementation_cost": 75000.0,
            "expected_efficiency_gain": 0.8,
            "revenue_impact": 8000.0,
        },
        {
            "name": "Code Generation - Startup",
            "use_case": AIUseCase.CODE_GENERATION,
            "industry": IndustryType.TECHNOLOGY,
            "company_size": "startup",
            "current_monthly_hours": 160.0,
            "hourly_cost": 110.0,
            "ai_monthly_cost": 400.0,
            "implementation_cost": 2500.0,
            "expected_efficiency_gain": 0.45,
            "revenue_impact": None,
        },
    ]

    for scenario in scenarios:
        print(f"\n📊 {scenario['name']}")
        print("-" * 40)

        result = await calculator.calculate_roi(
            use_case=scenario["use_case"],
            industry=scenario["industry"],
            company_size=scenario["company_size"],
            current_monthly_hours=scenario["current_monthly_hours"],
            hourly_cost=scenario["hourly_cost"],
            ai_monthly_cost=scenario["ai_monthly_cost"],
            implementation_cost=scenario["implementation_cost"],
            expected_efficiency_gain=scenario["expected_efficiency_gain"],
            revenue_impact=scenario["revenue_impact"],
        )

        metrics = result["metrics"]

        print(f"💰 ROI: {metrics.roi_percentage:.1f}%")
        print(f"⏰ Payback: {metrics.payback_period_months:.1f} months")
        print(f"💵 Annual Savings: ${metrics.annual_cost_savings:,.0f}")
        print(f"🕒 Time Savings: {metrics.monthly_time_savings_hours:.1f} hours/month")
        print(f"🎯 Success Probability: {result['success_probability']:.1%}")

        if metrics.revenue_impact_annual > 0:
            print(f"📈 Revenue Impact: ${metrics.revenue_impact_annual:,.0f}/year")

        print("\nKey Insights:")
        for insight in result["insights"][:2]:
            print(f"  • {insight}")

    print("\n" + "=" * 50)
    print("🎉 Demo Complete!")
    print("\n✅ AI ROI Calculator demonstrates:")
    print("  • Professional financial analysis capabilities")
    print("  • Industry expertise and benchmarking knowledge")
    print("  • Business case development skills")
    print("  • Executive-level communication ability")
    print("  • Practical AI implementation experience")

    print("\n🎯 Perfect for job interviews and client discussions!")


if __name__ == "__main__":
    asyncio.run(demo_scenarios())
