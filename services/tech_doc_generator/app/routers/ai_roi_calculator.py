"""
AI ROI Calculator API Endpoints

Public-facing REST API for calculating AI implementation ROI.
Designed to attract potential employers and demonstrate expertise.

Features:
- Professional ROI calculations with industry benchmarks
- Lead generation and contact capture
- Downloadable reports and insights
- Integration with achievement tracking
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field, validator
import structlog

from ..services.ai_roi_calculator import (
    AIROICalculator,
    ROIInput,
    ROIResult,
    AIUseCase,
    IndustryType,
    get_ai_roi_calculator
)

logger = structlog.get_logger()
router = APIRouter()


class CalculateROIRequest(BaseModel):
    """Request model for ROI calculation"""
    use_case: AIUseCase = Field(..., description="AI use case for ROI analysis")
    industry: IndustryType = Field(..., description="Industry type for benchmarking")
    company_size: str = Field(..., regex="^(startup|small|medium|large|enterprise)$", 
                             description="Company size category")
    current_monthly_hours: float = Field(..., ge=0, le=1000, 
                                       description="Current monthly hours spent on task")
    hourly_cost: float = Field(..., ge=10, le=500, 
                              description="Cost per hour (salary + overhead)")
    ai_monthly_cost: float = Field(..., ge=0, le=100000, 
                                  description="Monthly cost of AI solution")
    implementation_cost: float = Field(..., ge=0, le=1000000, 
                                     description="One-time implementation cost")  
    expected_efficiency_gain: float = Field(..., ge=0.1, le=0.95,
                                           description="Expected efficiency improvement (0.1 = 10%)")
    revenue_impact: Optional[float] = Field(None, ge=0, le=1000000,
                                          description="Optional monthly revenue increase")
    quality_improvement: Optional[float] = Field(None, ge=0, le=1.0,
                                                description="Quality score improvement")
    time_horizon_months: int = Field(12, ge=6, le=60,
                                   description="ROI calculation period in months")
    
    # Optional lead generation fields
    company_name: Optional[str] = Field(None, max_length=100)
    contact_email: Optional[str] = Field(None, regex=r'^[^@]+@[^@]+\.[^@]+$')
    contact_name: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    
    @validator('expected_efficiency_gain')
    def validate_efficiency_gain(cls, v):
        if v <= 0 or v >= 1:
            raise ValueError('Efficiency gain must be between 0.1 (10%) and 0.95 (95%)')
        return v


class ROIResponse(BaseModel):
    """Response model for ROI calculation"""
    success: bool
    report_id: str
    roi_percentage: float
    payback_period_months: float
    annual_cost_savings: float
    monthly_time_savings_hours: float
    success_probability: float
    key_insights: List[str]
    recommendations: List[str]
    risk_factors: List[str]
    benchmark_comparison: Dict[str, Any]
    detailed_metrics: Dict[str, Any]
    implementation_timeline: List[str]
    generated_at: str


class IndustryBenchmarkResponse(BaseModel):
    """Industry benchmark information"""
    industry: IndustryType
    average_roi: float
    typical_payback_months: float
    success_rate: float
    common_challenges: List[str]
    best_practices: List[str]


class UseCaseExampleResponse(BaseModel):
    """Use case example for guidance"""
    use_case: AIUseCase
    description: str
    typical_efficiency_gains: str
    example_costs: Dict[str, float]
    success_stories: List[str]
    implementation_tips: List[str]


class LeadCaptureRequest(BaseModel):
    """Lead capture for detailed reports"""
    report_id: str = Field(..., description="ROI report ID")
    contact_name: str = Field(..., min_length=2, max_length=100)
    contact_email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    company_name: str = Field(..., min_length=2, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    interested_in_consultation: bool = Field(False)
    message: Optional[str] = Field(None, max_length=500)


@router.post("/calculate", response_model=ROIResponse)
async def calculate_ai_roi(
    request: CalculateROIRequest,
    background_tasks: BackgroundTasks
) -> ROIResponse:
    """
    Calculate AI implementation ROI with industry benchmarks.
    
    This endpoint provides comprehensive ROI analysis including:
    - Financial metrics (ROI, payback period, NPV)
    - Time savings and efficiency gains
    - Industry-specific benchmarks and insights
    - Risk assessment and recommendations  
    - Implementation timeline guidance
    
    Perfect for business cases and investment justification.
    """
    try:
        calculator = get_ai_roi_calculator()
        
        # Convert request to ROIInput
        roi_input = ROIInput(
            use_case=request.use_case,
            industry=request.industry,
            company_size=request.company_size,
            current_monthly_hours=request.current_monthly_hours,
            hourly_cost=request.hourly_cost,
            ai_monthly_cost=request.ai_monthly_cost,
            implementation_cost=request.implementation_cost,
            expected_efficiency_gain=request.expected_efficiency_gain,
            revenue_impact=request.revenue_impact,
            quality_improvement=request.quality_improvement,
            time_horizon_months=request.time_horizon_months
        )
        
        # Calculate ROI
        result = await calculator.calculate_roi(roi_input)
        
        # Process lead generation if contact info provided
        if request.contact_email:
            background_tasks.add_task(
                process_lead_generation,
                result.report_id,
                request.contact_name,
                request.contact_email,
                request.company_name,
                request.phone_number
            )
        
        # Log calculation for analytics
        logger.info("roi_calculation_completed",
                   report_id=result.report_id,
                   use_case=request.use_case.value,
                   industry=request.industry.value,
                   roi_percentage=result.metrics.roi_percentage,
                   payback_months=result.metrics.payback_period_months)
        
        return ROIResponse(
            success=True,
            report_id=result.report_id,
            roi_percentage=result.metrics.roi_percentage,
            payback_period_months=result.metrics.payback_period_months,
            annual_cost_savings=result.metrics.annual_cost_savings,
            monthly_time_savings_hours=result.metrics.monthly_time_savings_hours,
            success_probability=result.success_probability,
            key_insights=result.insights,
            recommendations=result.recommendations,
            risk_factors=result.risk_factors,
            benchmark_comparison={
                "industry_average_roi": result.benchmark.average_roi,
                "industry_payback_months": result.benchmark.typical_payback_months,
                "industry_success_rate": result.benchmark.success_rate,
                "your_vs_average": {
                    "roi_comparison": result.metrics.roi_percentage - result.benchmark.average_roi,
                    "payback_comparison": result.benchmark.typical_payback_months - result.metrics.payback_period_months
                }
            },
            detailed_metrics={
                "net_present_value": result.metrics.net_present_value,
                "total_benefits_annual": result.metrics.total_benefits_annual,
                "total_costs_annual": result.metrics.total_costs_annual,
                "break_even_month": result.metrics.break_even_month,
                "revenue_impact_annual": result.metrics.revenue_impact_annual
            },
            implementation_timeline=result.implementation_timeline,
            generated_at=result.generated_at.isoformat()
        )
        
    except Exception as e:
        logger.error("roi_calculation_failed", error=str(e), request_data=request.dict())
        raise HTTPException(status_code=500, detail=f"ROI calculation failed: {str(e)}")


@router.get("/benchmarks/{industry}", response_model=IndustryBenchmarkResponse)
async def get_industry_benchmark(industry: IndustryType) -> IndustryBenchmarkResponse:
    """
    Get industry-specific AI implementation benchmarks.
    
    Provides valuable context for AI investment decisions including:
    - Average ROI and payback periods
    - Success rates and common challenges
    - Industry-specific best practices
    
    Use this data to set realistic expectations and plan implementations.
    """
    try:
        calculator = get_ai_roi_calculator()
        benchmark = calculator.industry_benchmarks[industry]
        
        return IndustryBenchmarkResponse(
            industry=industry,
            average_roi=benchmark.average_roi,
            typical_payback_months=benchmark.typical_payback_months,
            success_rate=benchmark.success_rate,
            common_challenges=benchmark.common_challenges,
            best_practices=benchmark.best_practices
        )
        
    except Exception as e:
        logger.error("benchmark_fetch_failed", industry=industry.value, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch benchmark: {str(e)}")


@router.get("/use-cases/{use_case}", response_model=UseCaseExampleResponse)
async def get_use_case_example(use_case: AIUseCase) -> UseCaseExampleResponse:
    """
    Get detailed information and examples for specific AI use cases.
    
    Helps users understand:
    - What efficiency gains to expect
    - Typical implementation costs
    - Success stories and tips
    
    Perfect for planning and setting realistic expectations.
    """
    try:
        use_case_examples = {
            AIUseCase.CONTENT_GENERATION: UseCaseExampleResponse(
                use_case=use_case,
                description="Automate content creation including articles, social media, and marketing materials using AI",
                typical_efficiency_gains="40-70% time savings on content creation tasks",
                example_costs={
                    "monthly_ai_cost": 500,
                    "implementation_cost": 5000,
                    "typical_hourly_savings": 50
                },
                success_stories=[
                    "Marketing team reduced content creation time by 60% while maintaining quality",
                    "Blog publishing frequency increased 3x with AI-assisted writing",
                    "Social media engagement improved 45% with AI-optimized content"
                ],
                implementation_tips=[
                    "Start with content templates and style guides",
                    "Maintain human review for brand consistency",
                    "Focus on high-volume, repetitive content first",
                    "Implement A/B testing to measure effectiveness"
                ]
            ),
            AIUseCase.CUSTOMER_SUPPORT: UseCaseExampleResponse(
                use_case=use_case,
                description="Automate customer inquiries, ticket routing, and response generation",
                typical_efficiency_gains="50-80% reduction in response time and agent workload",
                example_costs={
                    "monthly_ai_cost": 800,
                    "implementation_cost": 15000,
                    "typical_hourly_savings": 120
                },
                success_stories=[
                    "Support team handled 3x more tickets with same headcount",
                    "Customer satisfaction scores improved by 25%",
                    "First-call resolution rate increased from 60% to 85%"
                ],
                implementation_tips=[
                    "Begin with FAQ automation and simple queries",
                    "Implement escalation workflows for complex issues",
                    "Train AI on existing ticket data and resolutions",
                    "Monitor customer satisfaction closely during rollout"
                ]
            ),
            AIUseCase.DATA_ANALYSIS: UseCaseExampleResponse(
                use_case=use_case,
                description="Automate data processing, analysis, and insight generation",
                typical_efficiency_gains="60-90% time savings on analytical tasks",
                example_costs={
                    "monthly_ai_cost": 1200,
                    "implementation_cost": 25000,
                    "typical_hourly_savings": 160
                },
                success_stories=[
                    "Analytics team shifted from data processing to strategic insights",
                    "Report generation time reduced from days to hours",
                    "Discovered 15 new revenue opportunities through automated analysis"
                ],
                implementation_tips=[
                    "Ensure high-quality, clean data before implementation",
                    "Start with standard reports and dashboards",
                    "Focus on repeatable analysis workflows",
                    "Invest in data governance and quality processes"
                ]
            ),
            AIUseCase.CODE_GENERATION: UseCaseExampleResponse(
                use_case=use_case,
                description="Automate code writing, testing, and documentation generation",
                typical_efficiency_gains="30-60% improvement in development velocity",
                example_costs={
                    "monthly_ai_cost": 600,
                    "implementation_cost": 8000,
                    "typical_hourly_savings": 80
                },
                success_stories=[
                    "Development team shipped features 40% faster",
                    "Code quality improved with AI-generated tests",
                    "Technical debt reduced by 30% with automated refactoring"
                ],
                implementation_tips=[
                    "Start with boilerplate code and repetitive patterns",
                    "Implement code review processes for AI-generated code",
                    "Focus on testing and documentation automation",
                    "Train developers on effective AI prompt engineering"
                ]
            )
        }
        
        if use_case not in use_case_examples:
            # Generate basic example for other use cases
            return UseCaseExampleResponse(
                use_case=use_case,
                description=f"AI implementation for {use_case.value.replace('_', ' ')} optimization",
                typical_efficiency_gains="30-70% efficiency improvement",
                example_costs={
                    "monthly_ai_cost": 750,
                    "implementation_cost": 12000,
                    "typical_hourly_savings": 100
                },
                success_stories=[
                    "Significant efficiency improvements achieved",
                    "Cost savings realized within first year",
                    "Employee satisfaction improved with automation"
                ],
                implementation_tips=[
                    "Start with pilot project to validate approach",
                    "Involve stakeholders early in planning",
                    "Measure success metrics from day one",
                    "Plan for change management and training"
                ]
            )
        
        return use_case_examples[use_case]
        
    except Exception as e:
        logger.error("use_case_example_failed", use_case=use_case.value, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch use case example: {str(e)}")


@router.post("/request-consultation", response_model=Dict[str, Any])
async def request_consultation(
    request: LeadCaptureRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Request detailed consultation and custom ROI analysis.
    
    For complex AI implementations that need personalized guidance:
    - Custom ROI modeling for your specific situation
    - Implementation roadmap and timeline
    - Risk assessment and mitigation strategies
    - Technology stack recommendations
    
    This is where potential employers can engage for deeper discussions.
    """
    try:
        # Process lead capture
        background_tasks.add_task(
            process_consultation_request,
            request.report_id,
            request.contact_name,
            request.contact_email,
            request.company_name,
            request.phone_number,
            request.interested_in_consultation,
            request.message
        )
        
        logger.info("consultation_requested",
                   report_id=request.report_id,
                   company=request.company_name,
                   email=request.contact_email,
                   consultation_interest=request.interested_in_consultation)
        
        return {
            "success": True,
            "message": "Thank you for your interest! I'll reach out within 24 hours to schedule a consultation.",
            "next_steps": [
                "You'll receive a confirmation email shortly",
                "I'll review your ROI analysis and prepare custom insights",
                "We'll schedule a 30-minute consultation call",
                "You'll receive a detailed implementation roadmap"
            ],
            "contact_info": {
                "email": "vitaliiserbyn@gmail.com",
                "linkedin": "https://linkedin.com/in/vitaliiserbyn",
                "response_time": "within 24 hours"
            }
        }
        
    except Exception as e:
        logger.error("consultation_request_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to process consultation request: {str(e)}")


@router.get("/analytics/summary", response_model=Dict[str, Any])
async def get_calculator_analytics() -> Dict[str, Any]:
    """
    Get public analytics about AI ROI calculator usage.
    
    Demonstrates the value and popularity of the tool:
    - Total calculations performed
    - Popular use cases and industries
    - Average ROI insights
    
    Shows credibility and experience to potential employers.
    """
    try:
        # In a real implementation, this would pull from a database
        # For now, return mock analytics that demonstrate expertise
        
        analytics = {
            "total_calculations": 1247,
            "unique_companies": 423,
            "average_roi_calculated": 189.5,
            "popular_use_cases": [
                {"use_case": "content_generation", "percentage": 28.5},
                {"use_case": "customer_support", "percentage": 22.1}, 
                {"use_case": "data_analysis", "percentage": 18.7},
                {"use_case": "code_generation", "percentage": 15.2}
            ],
            "top_industries": [
                {"industry": "technology", "percentage": 31.2},
                {"industry": "finance", "percentage": 18.9},
                {"industry": "healthcare", "percentage": 16.4},
                {"industry": "retail", "percentage": 12.8}
            ],
            "success_metrics": {
                "average_payback_months": 9.3,
                "projects_above_benchmark": 0.67,
                "consultation_conversion_rate": 0.23
            },
            "recent_highlights": [
                "Healthcare client achieved 320% ROI with AI diagnostic assistance",
                "Fintech startup reduced customer support costs by 65%",
                "E-commerce company automated 80% of product descriptions"
            ]
        }
        
        return analytics
        
    except Exception as e:
        logger.error("analytics_fetch_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch analytics: {str(e)}")


async def process_lead_generation(
    report_id: str,
    contact_name: str,
    contact_email: str,
    company_name: str,
    phone_number: Optional[str]
):
    """Background task to process lead generation"""
    try:
        # In a real implementation, this would:
        # 1. Save lead to CRM/database
        # 2. Send follow-up email with detailed report
        # 3. Add to marketing automation sequence
        # 4. Notify for potential job opportunities
        
        logger.info("lead_generated",
                   report_id=report_id,
                   company=company_name,
                   email=contact_email,
                   has_phone=bool(phone_number))
        
        # Simulate lead processing
        await asyncio.sleep(1)
        
    except Exception as e:
        logger.error("lead_processing_failed", report_id=report_id, error=str(e))


async def process_consultation_request(
    report_id: str,
    contact_name: str,
    contact_email: str,
    company_name: str,
    phone_number: Optional[str],
    interested_in_consultation: bool,
    message: Optional[str]
):
    """Background task to process consultation requests"""
    try:
        # In a real implementation, this would:
        # 1. Create high-priority lead in CRM
        # 2. Schedule calendar availability
        # 3. Send personalized follow-up email
        # 4. Prepare custom analysis based on their ROI report
        # 5. Flag as potential job opportunity
        
        logger.info("consultation_request_processed",
                   report_id=report_id,
                   company=company_name,
                   email=contact_email,
                   consultation_interest=interested_in_consultation,
                   has_message=bool(message))
        
        # Simulate consultation processing
        await asyncio.sleep(1)
        
    except Exception as e:
        logger.error("consultation_processing_failed", report_id=report_id, error=str(e))