"""
AI ROI Calculator Service

Public-facing tool that calculates return on investment for AI implementations.
Positions user as thought leader and attracts potential employers.

Features:
- Multi-faceted ROI calculation (time savings, cost reduction, revenue increase)
- Industry benchmarks and best practices
- Professional reports with insights
- Lead generation for job opportunities
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import structlog

logger = structlog.get_logger()


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
class ROIInput:
    """Input parameters for ROI calculation"""

    use_case: AIUseCase
    industry: IndustryType
    company_size: str  # "startup", "small", "medium", "large", "enterprise"
    current_monthly_hours: float  # Hours spent on task monthly
    hourly_cost: float  # Cost per hour (salary + overhead)
    ai_monthly_cost: float  # Monthly cost of AI solution
    implementation_cost: float  # One-time setup cost
    expected_efficiency_gain: float  # Percentage improvement (e.g., 0.4 for 40%)
    revenue_impact: Optional[float] = None  # Optional revenue increase
    quality_improvement: Optional[float] = None  # Quality score improvement
    time_horizon_months: int = 12  # ROI calculation period


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


@dataclass
class IndustryBenchmark:
    """Industry benchmark data"""

    average_roi: float
    typical_payback_months: float
    success_rate: float
    common_challenges: List[str]
    best_practices: List[str]


@dataclass
class ROIResult:
    """Complete ROI analysis result"""

    metrics: ROIMetrics
    benchmark: IndustryBenchmark
    insights: List[str]
    recommendations: List[str]
    risk_factors: List[str]
    implementation_timeline: List[str]
    success_probability: float
    report_id: str
    generated_at: datetime


class AIROICalculator:
    """AI ROI Calculator with industry benchmarks and insights"""

    def __init__(self):
        self.industry_benchmarks = self._initialize_benchmarks()
        self.use_case_multipliers = self._initialize_use_case_multipliers()

    def _initialize_benchmarks(self) -> Dict[IndustryType, IndustryBenchmark]:
        """Initialize industry benchmark data"""
        return {
            IndustryType.TECHNOLOGY: IndustryBenchmark(
                average_roi=245.0,
                typical_payback_months=8.5,
                success_rate=0.78,
                common_challenges=[
                    "Technical integration complexity",
                    "Skills gap in AI implementation",
                    "Data quality and availability",
                ],
                best_practices=[
                    "Start with pilot projects and scale gradually",
                    "Invest in team training and upskilling",
                    "Establish clear metrics and monitoring",
                    "Focus on high-impact, low-risk use cases initially",
                ],
            ),
            IndustryType.FINANCE: IndustryBenchmark(
                average_roi=180.0,
                typical_payback_months=12.0,
                success_rate=0.65,
                common_challenges=[
                    "Regulatory compliance requirements",
                    "Risk management concerns",
                    "Legacy system integration",
                ],
                best_practices=[
                    "Ensure compliance from day one",
                    "Implement robust testing and validation",
                    "Start with back-office operations",
                    "Maintain human oversight for critical decisions",
                ],
            ),
            IndustryType.HEALTHCARE: IndustryBenchmark(
                average_roi=320.0,
                typical_payback_months=15.0,
                success_rate=0.70,
                common_challenges=[
                    "Patient data privacy and security",
                    "Clinical workflow integration",
                    "Regulatory approval processes",
                ],
                best_practices=[
                    "Prioritize patient safety and privacy",
                    "Involve clinical staff early in design",
                    "Focus on administrative tasks first",
                    "Establish clear audit trails",
                ],
            ),
            IndustryType.RETAIL: IndustryBenchmark(
                average_roi=165.0,
                typical_payback_months=9.0,
                success_rate=0.72,
                common_challenges=[
                    "Customer experience integration",
                    "Inventory management complexity",
                    "Seasonal demand variations",
                ],
                best_practices=[
                    "Focus on customer-facing improvements",
                    "Integrate with existing POS systems",
                    "Use predictive analytics for inventory",
                    "A/B test customer experience changes",
                ],
            ),
            IndustryType.MANUFACTURING: IndustryBenchmark(
                average_roi=290.0,
                typical_payback_months=11.0,
                success_rate=0.68,
                common_challenges=[
                    "Equipment integration and IoT connectivity",
                    "Production line disruption during implementation",
                    "Worker training and adoption",
                ],
                best_practices=[
                    "Start with predictive maintenance",
                    "Implement during planned downtime",
                    "Focus on quality control automation",
                    "Gradual rollout across production lines",
                ],
            ),
            IndustryType.EDUCATION: IndustryBenchmark(
                average_roi=140.0,
                typical_payback_months=18.0,
                success_rate=0.55,
                common_challenges=[
                    "Budget constraints and funding",
                    "Educator training and buy-in",
                    "Student privacy concerns",
                ],
                best_practices=[
                    "Start with administrative automation",
                    "Involve educators in solution design",
                    "Focus on student outcome improvements",
                    "Implement comprehensive training programs",
                ],
            ),
            IndustryType.MEDIA: IndustryBenchmark(
                average_roi=210.0,
                typical_payback_months=10.0,
                success_rate=0.75,
                common_challenges=[
                    "Content quality and brand consistency",
                    "Copyright and IP considerations",
                    "Audience engagement measurement",
                ],
                best_practices=[
                    "Maintain editorial oversight",
                    "Focus on content personalization",
                    "Implement robust fact-checking",
                    "Use AI for content distribution optimization",
                ],
            ),
            IndustryType.CONSULTING: IndustryBenchmark(
                average_roi=275.0,
                typical_payback_months=6.0,
                success_rate=0.80,
                common_challenges=[
                    "Client confidentiality and data security",
                    "Customization for different client needs",
                    "Demonstrating value to clients",
                ],
                best_practices=[
                    "Use AI for research and analysis",
                    "Automate report generation",
                    "Focus on insights and recommendations",
                    "Maintain client-specific customization",
                ],
            ),
        }

    def _initialize_use_case_multipliers(self) -> Dict[AIUseCase, float]:
        """Initialize use case complexity multipliers"""
        return {
            AIUseCase.CONTENT_GENERATION: 1.2,  # High efficiency gains
            AIUseCase.CUSTOMER_SUPPORT: 1.4,  # Very high time savings
            AIUseCase.DATA_ANALYSIS: 1.8,  # Massive efficiency improvements
            AIUseCase.CODE_GENERATION: 1.6,  # High productivity gains
            AIUseCase.DOCUMENT_PROCESSING: 2.0,  # Extreme automation potential
            AIUseCase.PREDICTIVE_ANALYTICS: 1.3,  # Business value multiplier
            AIUseCase.MARKETING_AUTOMATION: 1.5,  # Revenue and efficiency gains
            AIUseCase.INFRASTRUCTURE_OPTIMIZATION: 2.2,  # Cost savings + efficiency
        }

    async def calculate_roi(self, input_data: ROIInput) -> ROIResult:
        """Calculate comprehensive ROI analysis"""
        logger.info(
            "calculating_roi",
            use_case=input_data.use_case.value,
            industry=input_data.industry.value,
            company_size=input_data.company_size,
        )

        # Calculate core metrics
        metrics = await self._calculate_core_metrics(input_data)

        # Get industry benchmark
        benchmark = self.industry_benchmarks[input_data.industry]

        # Generate insights and recommendations
        insights = await self._generate_insights(input_data, metrics, benchmark)
        recommendations = await self._generate_recommendations(
            input_data, metrics, benchmark
        )
        risk_factors = await self._identify_risk_factors(input_data, metrics)
        implementation_timeline = await self._create_implementation_timeline(input_data)
        success_probability = await self._calculate_success_probability(
            input_data, metrics, benchmark
        )

        report_id = f"roi_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return ROIResult(
            metrics=metrics,
            benchmark=benchmark,
            insights=insights,
            recommendations=recommendations,
            risk_factors=risk_factors,
            implementation_timeline=implementation_timeline,
            success_probability=success_probability,
            report_id=report_id,
            generated_at=datetime.now(),
        )

    async def _calculate_core_metrics(self, input_data: ROIInput) -> ROIMetrics:
        """Calculate core ROI metrics"""
        # Apply use case multiplier to efficiency gain
        use_case_multiplier = self.use_case_multipliers[input_data.use_case]
        effective_efficiency_gain = min(
            0.95, input_data.expected_efficiency_gain * use_case_multiplier
        )

        # Calculate time and cost savings
        monthly_time_savings_hours = (
            input_data.current_monthly_hours * effective_efficiency_gain
        )
        monthly_cost_savings = monthly_time_savings_hours * input_data.hourly_cost
        annual_cost_savings = monthly_cost_savings * 12

        # Calculate net savings (subtract AI costs)
        net_monthly_savings = monthly_cost_savings - input_data.ai_monthly_cost
        net_annual_savings = net_monthly_savings * 12

        # Calculate revenue impact
        revenue_impact_annual = 0.0
        if input_data.revenue_impact:
            revenue_impact_annual = input_data.revenue_impact * 12

        # Total benefits and costs
        total_benefits_annual = net_annual_savings + revenue_impact_annual
        total_costs_annual = (
            input_data.ai_monthly_cost * 12
        ) + input_data.implementation_cost

        # Calculate ROI percentage
        if total_costs_annual > 0:
            roi_percentage = (total_benefits_annual / total_costs_annual) * 100
        else:
            roi_percentage = 0.0

        # Calculate payback period
        if net_monthly_savings > 0:
            payback_period_months = input_data.implementation_cost / net_monthly_savings
        else:
            payback_period_months = float("inf")

        # Calculate NPV (simplified with 10% discount rate)
        discount_rate = 0.10
        npv = 0.0
        for month in range(1, input_data.time_horizon_months + 1):
            monthly_benefit = net_monthly_savings + (
                revenue_impact_annual / 12 if input_data.revenue_impact else 0
            )
            discounted_benefit = monthly_benefit / ((1 + discount_rate / 12) ** month)
            npv += discounted_benefit
        npv -= input_data.implementation_cost

        # Break-even month
        break_even_month = (
            int(payback_period_months) + 1
            if payback_period_months != float("inf")
            else 0
        )

        return ROIMetrics(
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

    async def _generate_insights(
        self, input_data: ROIInput, metrics: ROIMetrics, benchmark: IndustryBenchmark
    ) -> List[str]:
        """Generate actionable insights based on ROI analysis"""
        insights = []

        # ROI comparison to industry benchmark
        if metrics.roi_percentage > benchmark.average_roi * 1.2:
            insights.append(
                f"🎯 Exceptional ROI potential: {metrics.roi_percentage:.1f}% vs industry average of {benchmark.average_roi:.1f}%"
            )
        elif metrics.roi_percentage > benchmark.average_roi:
            insights.append(
                f"📈 Above-average ROI: {metrics.roi_percentage:.1f}% vs industry average of {benchmark.average_roi:.1f}%"
            )
        else:
            insights.append(
                f"⚠️ Below-average ROI: {metrics.roi_percentage:.1f}% vs industry average of {benchmark.average_roi:.1f}%"
            )

        # Payback period analysis
        if metrics.payback_period_months < benchmark.typical_payback_months:
            insights.append(
                f"⚡ Fast payback: {metrics.payback_period_months:.1f} months vs typical {benchmark.typical_payback_months:.1f} months"
            )
        else:
            insights.append(
                f"⏰ Extended payback period: {metrics.payback_period_months:.1f} months vs typical {benchmark.typical_payback_months:.1f} months"
            )

        # Time savings impact
        if metrics.monthly_time_savings_hours > 40:
            insights.append(
                f"🚀 Significant time savings: {metrics.monthly_time_savings_hours:.1f} hours/month freed for strategic work"
            )
        elif metrics.monthly_time_savings_hours > 20:
            insights.append(
                f"⏱️ Moderate time savings: {metrics.monthly_time_savings_hours:.1f} hours/month for higher-value activities"
            )

        # Cost efficiency
        if metrics.annual_cost_savings > 100000:
            insights.append(
                f"💰 Major cost impact: ${metrics.annual_cost_savings:,.0f} annual savings"
            )
        elif metrics.annual_cost_savings > 25000:
            insights.append(
                f"💵 Solid cost savings: ${metrics.annual_cost_savings:,.0f} annually"
            )

        # Success probability
        if (
            metrics.roi_percentage > benchmark.average_roi
            and metrics.payback_period_months < benchmark.typical_payback_months
        ):
            insights.append(
                "✅ High success probability based on industry benchmarks and calculated metrics"
            )

        return insights

    async def _generate_recommendations(
        self, input_data: ROIInput, metrics: ROIMetrics, benchmark: IndustryBenchmark
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # Start with benchmark best practices
        recommendations.extend(
            [f"• {practice}" for practice in benchmark.best_practices[:2]]
        )

        # Add specific recommendations based on metrics
        if metrics.payback_period_months > 12:
            recommendations.append(
                "• Consider phased implementation to reduce upfront costs"
            )
            recommendations.append("• Focus on highest-impact use cases first")

        if metrics.roi_percentage < 100:
            recommendations.append("• Explore additional efficiency opportunities")
            recommendations.append(
                "• Consider combining multiple AI use cases for compound benefits"
            )

        # Use case specific recommendations
        if input_data.use_case == AIUseCase.CONTENT_GENERATION:
            recommendations.append(
                "• Start with content templates and gradually expand to full automation"
            )
            recommendations.append(
                "• Maintain quality control processes and brand guidelines"
            )
        elif input_data.use_case == AIUseCase.CUSTOMER_SUPPORT:
            recommendations.append("• Begin with FAQ automation before complex queries")
            recommendations.append("• Implement human handoff for escalated issues")
        elif input_data.use_case == AIUseCase.DATA_ANALYSIS:
            recommendations.append(
                "• Ensure data quality and governance before implementation"
            )
            recommendations.append(
                "• Focus on reporting automation and insight generation"
            )

        # Company size specific recommendations
        if input_data.company_size in ["startup", "small"]:
            recommendations.append("• Consider SaaS solutions over custom development")
            recommendations.append(
                "• Partner with AI vendors for implementation support"
            )
        elif input_data.company_size in ["large", "enterprise"]:
            recommendations.append("• Evaluate build vs. buy decisions carefully")
            recommendations.append(
                "• Establish center of excellence for AI initiatives"
            )

        return recommendations[:6]  # Limit to top 6 recommendations

    async def _identify_risk_factors(
        self, input_data: ROIInput, metrics: ROIMetrics
    ) -> List[str]:
        """Identify potential risk factors"""
        risks = []

        # Get industry-specific challenges
        benchmark = self.industry_benchmarks[input_data.industry]
        risks.extend([f"• {challenge}" for challenge in benchmark.common_challenges])

        # Add general risk factors based on metrics
        if metrics.payback_period_months > 18:
            risks.append("• Extended payback period increases project risk")

        if (
            input_data.implementation_cost
            > input_data.current_monthly_hours * input_data.hourly_cost * 6
        ):
            risks.append("• High implementation cost relative to monthly savings")

        # Use case specific risks
        if input_data.use_case == AIUseCase.CONTENT_GENERATION:
            risks.append("• Brand consistency and quality control challenges")
        elif input_data.use_case == AIUseCase.CUSTOMER_SUPPORT:
            risks.append("• Customer satisfaction impact if not implemented properly")

        return risks[:5]  # Limit to top 5 risks

    async def _create_implementation_timeline(self, input_data: ROIInput) -> List[str]:
        """Create implementation timeline"""
        timeline = []

        # Base timeline varies by company size
        if input_data.company_size in ["startup", "small"]:
            timeline = [
                "Week 1-2: Vendor selection and contract negotiation",
                "Week 3-4: Initial setup and configuration",
                "Week 5-6: Pilot testing and refinement",
                "Week 7-8: Full deployment and training",
                "Week 9-12: Monitoring and optimization",
            ]
        else:
            timeline = [
                "Month 1: Requirements gathering and vendor evaluation",
                "Month 2: Procurement and initial setup",
                "Month 3-4: Pilot implementation and testing",
                "Month 5-6: Full rollout and training",
                "Month 7-12: Optimization and scaling",
            ]

        return timeline

    async def _calculate_success_probability(
        self, input_data: ROIInput, metrics: ROIMetrics, benchmark: IndustryBenchmark
    ) -> float:
        """Calculate probability of successful implementation"""
        base_probability = benchmark.success_rate

        # Adjust based on ROI metrics
        roi_factor = 1.0
        if metrics.roi_percentage > benchmark.average_roi * 1.5:
            roi_factor = 1.2
        elif metrics.roi_percentage < benchmark.average_roi * 0.5:
            roi_factor = 0.8

        # Adjust based on payback period
        payback_factor = 1.0
        if metrics.payback_period_months < benchmark.typical_payback_months * 0.8:
            payback_factor = 1.1
        elif metrics.payback_period_months > benchmark.typical_payback_months * 1.5:
            payback_factor = 0.9

        # Adjust based on company size (smaller companies are more agile)
        size_factor = 1.0
        if input_data.company_size in ["startup", "small"]:
            size_factor = 1.1
        elif input_data.company_size == "enterprise":
            size_factor = 0.95

        # Calculate final probability
        final_probability = base_probability * roi_factor * payback_factor * size_factor
        return min(0.95, final_probability)  # Cap at 95%


def get_ai_roi_calculator() -> AIROICalculator:
    """Get singleton instance of AI ROI Calculator"""
    if not hasattr(get_ai_roi_calculator, "_instance"):
        get_ai_roi_calculator._instance = AIROICalculator()
    return get_ai_roi_calculator._instance
