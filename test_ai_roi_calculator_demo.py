#!/usr/bin/env python3
"""
AI ROI Calculator Demo

Demonstrates the AI ROI Calculator functionality with realistic scenarios.
Shows potential ROI for different AI use cases and industries.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.tech_doc_generator.app.services.ai_roi_calculator import (
    AIROICalculator,
    ROIInput,
    AIUseCase,
    IndustryType,
)


async def demo_content_generation_roi():
    """Demo: Content Generation for Tech Company"""
    print("🎯 Demo 1: AI Content Generation for Technology Company")
    print("=" * 60)

    calculator = AIROICalculator()

    # Scenario: Medium tech company automating blog content
    roi_input = ROIInput(
        use_case=AIUseCase.CONTENT_GENERATION,
        industry=IndustryType.TECHNOLOGY,
        company_size="medium",
        current_monthly_hours=120.0,  # 30 hours/week on content
        hourly_cost=85.0,  # Marketing manager + designer cost
        ai_monthly_cost=750.0,  # Enterprise AI tools
        implementation_cost=8000.0,  # Setup + training
        expected_efficiency_gain=0.55,  # 55% time savings
        revenue_impact=2500.0,  # SEO + lead gen value
        time_horizon_months=18,
    )

    result = await calculator.calculate_roi(roi_input)

    print("📊 ROI Analysis Results:")
    print(f"   💰 ROI: {result.metrics.roi_percentage:.1f}%")
    print(f"   ⏰ Payback Period: {result.metrics.payback_period_months:.1f} months")
    print(f"   💵 Annual Cost Savings: ${result.metrics.annual_cost_savings:,.0f}")
    print(
        f"   🕒 Monthly Time Savings: {result.metrics.monthly_time_savings_hours:.1f} hours"
    )
    print(f"   🎯 Success Probability: {result.success_probability:.1%}")

    print("\n🔍 Key Insights:")
    for insight in result.insights[:3]:
        print(f"   • {insight}")

    print("\n💡 Top Recommendations:")
    for rec in result.recommendations[:3]:
        print(f"   {rec}")

    print("\n" + "=" * 60 + "\n")


async def demo_customer_support_roi():
    """Demo: Customer Support Automation for Healthcare"""
    print("🏥 Demo 2: AI Customer Support for Healthcare Company")
    print("=" * 60)

    calculator = AIROICalculator()

    # Scenario: Healthcare company automating patient inquiries
    roi_input = ROIInput(
        use_case=AIUseCase.CUSTOMER_SUPPORT,
        industry=IndustryType.HEALTHCARE,
        company_size="large",
        current_monthly_hours=400.0,  # 2.5 FTE support staff
        hourly_cost=65.0,  # Healthcare support specialist cost
        ai_monthly_cost=1200.0,  # Healthcare-compliant AI platform
        implementation_cost=35000.0,  # HIPAA compliance + integration
        expected_efficiency_gain=0.7,  # 70% automation rate
        quality_improvement=0.25,  # Consistency improvement
        time_horizon_months=24,
    )

    result = await calculator.calculate_roi(roi_input)

    print("📊 ROI Analysis Results:")
    print(f"   💰 ROI: {result.metrics.roi_percentage:.1f}%")
    print(f"   ⏰ Payback Period: {result.metrics.payback_period_months:.1f} months")
    print(f"   💵 Annual Cost Savings: ${result.metrics.annual_cost_savings:,.0f}")
    print(
        f"   🕒 Monthly Time Savings: {result.metrics.monthly_time_savings_hours:.1f} hours"
    )
    print(f"   🎯 Success Probability: {result.success_probability:.1%}")

    print("\n🔍 Key Insights:")
    for insight in result.insights[:3]:
        print(f"   • {insight}")

    print("\n⚠️ Risk Factors:")
    for risk in result.risk_factors[:2]:
        print(f"   {risk}")

    print("\n" + "=" * 60 + "\n")


async def demo_data_analysis_roi():
    """Demo: Data Analysis Automation for Finance"""
    print("📈 Demo 3: AI Data Analysis for Financial Services")
    print("=" * 60)

    calculator = AIROICalculator()

    # Scenario: Finance company automating risk analysis reports
    roi_input = ROIInput(
        use_case=AIUseCase.DATA_ANALYSIS,
        industry=IndustryType.FINANCE,
        company_size="enterprise",
        current_monthly_hours=320.0,  # 2 FTE analysts
        hourly_cost=95.0,  # Senior financial analyst cost
        ai_monthly_cost=2000.0,  # Enterprise analytics platform
        implementation_cost=75000.0,  # Compliance + integration
        expected_efficiency_gain=0.8,  # 80% automation of routine analysis
        revenue_impact=8000.0,  # Better insights = better decisions
        time_horizon_months=36,
    )

    result = await calculator.calculate_roi(roi_input)

    print("📊 ROI Analysis Results:")
    print(f"   💰 ROI: {result.metrics.roi_percentage:.1f}%")
    print(f"   ⏰ Payback Period: {result.metrics.payback_period_months:.1f} months")
    print(f"   💵 Annual Cost Savings: ${result.metrics.annual_cost_savings:,.0f}")
    print(f"   📊 Revenue Impact: ${result.metrics.revenue_impact_annual:,.0f}")
    print(
        f"   🕒 Monthly Time Savings: {result.metrics.monthly_time_savings_hours:.1f} hours"
    )
    print(f"   🎯 Success Probability: {result.success_probability:.1%}")

    print("\n🔍 Key Insights:")
    for insight in result.insights[:3]:
        print(f"   • {insight}")

    print("\n📋 Implementation Timeline:")
    for phase in result.implementation_timeline[:3]:
        print(f"   • {phase}")

    print("\n" + "=" * 60 + "\n")


async def demo_code_generation_roi():
    """Demo: Code Generation for Startup"""
    print("💻 Demo 4: AI Code Generation for Tech Startup")
    print("=" * 60)

    calculator = AIROICalculator()

    # Scenario: Startup using AI to accelerate development
    roi_input = ROIInput(
        use_case=AIUseCase.CODE_GENERATION,
        industry=IndustryType.TECHNOLOGY,
        company_size="startup",
        current_monthly_hours=160.0,  # 1 FTE developer
        hourly_cost=110.0,  # Senior developer cost
        ai_monthly_cost=400.0,  # AI coding tools
        implementation_cost=2500.0,  # Training + setup
        expected_efficiency_gain=0.45,  # 45% productivity boost
        time_horizon_months=12,
    )

    result = await calculator.calculate_roi(roi_input)

    print("📊 ROI Analysis Results:")
    print(f"   💰 ROI: {result.metrics.roi_percentage:.1f}%")
    print(f"   ⏰ Payback Period: {result.metrics.payback_period_months:.1f} months")
    print(f"   💵 Annual Cost Savings: ${result.metrics.annual_cost_savings:,.0f}")
    print(
        f"   🕒 Monthly Time Savings: {result.metrics.monthly_time_savings_hours:.1f} hours"
    )
    print(f"   🎯 Success Probability: {result.success_probability:.1%}")

    print("\n🔍 Key Insights:")
    for insight in result.insights:
        print(f"   • {insight}")

    print("\n💡 Recommendations:")
    for rec in result.recommendations[:4]:
        print(f"   {rec}")

    print("\n" + "=" * 60 + "\n")


async def demo_industry_comparison():
    """Demo: Same Use Case Across Different Industries"""
    print("🏭 Demo 5: Content Generation ROI Across Industries")
    print("=" * 60)

    calculator = AIROICalculator()

    # Base scenario
    base_input = ROIInput(
        use_case=AIUseCase.CONTENT_GENERATION,
        industry=IndustryType.TECHNOLOGY,  # Will be overridden
        company_size="medium",
        current_monthly_hours=80.0,
        hourly_cost=75.0,
        ai_monthly_cost=600.0,
        implementation_cost=6000.0,
        expected_efficiency_gain=0.5,
        time_horizon_months=12,
    )

    industries = [
        IndustryType.TECHNOLOGY,
        IndustryType.HEALTHCARE,
        IndustryType.FINANCE,
        IndustryType.RETAIL,
    ]

    print("Industry Comparison Results:")
    print("-" * 40)

    for industry in industries:
        test_input = base_input
        test_input.industry = industry
        result = await calculator.calculate_roi(test_input)

        benchmark = calculator.industry_benchmarks[industry]

        print(f"\n{industry.value.title()}:")
        print(
            f"   ROI: {result.metrics.roi_percentage:.1f}% (avg: {benchmark.average_roi:.1f}%)"
        )
        print(
            f"   Payback: {result.metrics.payback_period_months:.1f}mo (avg: {benchmark.typical_payback_months:.1f}mo)"
        )
        print(
            f"   Success Rate: {result.success_probability:.1%} (avg: {benchmark.success_rate:.1%})"
        )

    print("\n" + "=" * 60 + "\n")


async def demo_edge_cases():
    """Demo: Edge Cases and Boundary Conditions"""
    print("⚡ Demo 6: Edge Cases and Scenarios")
    print("=" * 60)

    calculator = AIROICalculator()

    # Low-cost, high-efficiency scenario
    print("💡 Scenario A: Low Cost, High Efficiency (Best Case)")
    high_efficiency_input = ROIInput(
        use_case=AIUseCase.DOCUMENT_PROCESSING,
        industry=IndustryType.CONSULTING,
        company_size="small",
        current_monthly_hours=100.0,
        hourly_cost=80.0,
        ai_monthly_cost=200.0,  # Very affordable
        implementation_cost=1000.0,  # Minimal setup
        expected_efficiency_gain=0.85,  # 85% efficiency
        time_horizon_months=12,
    )

    result_a = await calculator.calculate_roi(high_efficiency_input)
    print(
        f"   ROI: {result_a.metrics.roi_percentage:.1f}% | Payback: {result_a.metrics.payback_period_months:.1f}mo"
    )

    # High-cost, low-efficiency scenario
    print("\n⚠️ Scenario B: High Cost, Low Efficiency (Challenging Case)")
    low_efficiency_input = ROIInput(
        use_case=AIUseCase.PREDICTIVE_ANALYTICS,
        industry=IndustryType.EDUCATION,
        company_size="large",
        current_monthly_hours=40.0,
        hourly_cost=50.0,
        ai_monthly_cost=3000.0,  # Expensive solution
        implementation_cost=80000.0,  # Major project
        expected_efficiency_gain=0.2,  # 20% efficiency
        time_horizon_months=12,
    )

    result_b = await calculator.calculate_roi(low_efficiency_input)
    print(
        f"   ROI: {result_b.metrics.roi_percentage:.1f}% | Payback: {result_b.metrics.payback_period_months:.1f}mo"
    )

    # Balanced scenario with revenue impact
    print("\n🎯 Scenario C: Balanced with Revenue Impact")
    balanced_input = ROIInput(
        use_case=AIUseCase.MARKETING_AUTOMATION,
        industry=IndustryType.RETAIL,
        company_size="medium",
        current_monthly_hours=60.0,
        hourly_cost=70.0,
        ai_monthly_cost=800.0,
        implementation_cost=12000.0,
        expected_efficiency_gain=0.4,
        revenue_impact=3000.0,  # Marketing ROI
        time_horizon_months=18,
    )

    result_c = await calculator.calculate_roi(balanced_input)
    print(
        f"   ROI: {result_c.metrics.roi_percentage:.1f}% | Payback: {result_c.metrics.payback_period_months:.1f}mo"
    )
    print(f"   Revenue Impact: ${result_c.metrics.revenue_impact_annual:,.0f}/year")

    print("\n" + "=" * 60 + "\n")


async def main():
    """Run all ROI Calculator demos"""
    print("🚀 AI ROI Calculator Comprehensive Demo")
    print("🔥 Showcasing Professional AI Implementation Analysis")
    print("=" * 70)
    print()

    try:
        # Run all demo scenarios
        await demo_content_generation_roi()
        await demo_customer_support_roi()
        await demo_data_analysis_roi()
        await demo_code_generation_roi()
        await demo_industry_comparison()
        await demo_edge_cases()

        print("🎉 AI ROI Calculator Demo Complete!")
        print("\n✅ Key Features Demonstrated:")
        print("   • Comprehensive ROI calculations with industry benchmarks")
        print("   • Multi-faceted analysis (cost savings, time, revenue)")
        print("   • Industry-specific insights and recommendations")
        print("   • Risk assessment and implementation guidance")
        print("   • Success probability with confidence intervals")
        print("   • Professional reporting and business case support")

        print("\n🎯 Perfect for:")
        print("   • Business case development and investment justification")
        print("   • Executive presentations and stakeholder buy-in")
        print("   • Implementation planning and risk management")
        print("   • Job interviews and consultant positioning")
        print("   • Lead generation and professional credibility")

        print("\n🚀 Next Steps:")
        print("   • Deploy as public tool at your domain")
        print("   • Add lead capture and consultation booking")
        print("   • Create content marketing around ROI insights")
        print("   • Use in job interviews to demonstrate expertise")

        return True

    except Exception as e:
        print(f"\n❌ DEMO FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
