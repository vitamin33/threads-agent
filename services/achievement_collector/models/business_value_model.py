"""Comprehensive Business Value Model for Startup Interviews

This model structures business value data with additional KPIs that resonate
with startup founders, VCs, and technical leaders.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union
import json


class ValueType(Enum):
    """Types of business value for startup contexts."""

    TIME_SAVINGS = "time_savings"
    COST_REDUCTION = "cost_reduction"
    REVENUE_INCREASE = "revenue_increase"
    PRODUCTIVITY_GAIN = "productivity_gain"
    RISK_MITIGATION = "risk_mitigation"
    QUALITY_IMPROVEMENT = "quality_improvement"
    TECHNICAL_DEBT_REDUCTION = "technical_debt_reduction"
    AUTOMATION = "automation"
    SCALABILITY_IMPROVEMENT = "scalability_improvement"
    USER_EXPERIENCE_ENHANCEMENT = "user_experience_enhancement"


class ConfidenceLevel(Enum):
    """Confidence levels with startup-friendly descriptions."""

    HIGH = {"score": 0.9, "description": "Directly measurable, validated metrics"}
    MEDIUM = {
        "score": 0.7,
        "description": "Industry-standard estimates, defensible assumptions",
    }
    LOW = {"score": 0.4, "description": "Conservative projections, high uncertainty"}


class BusinessImpactTier(Enum):
    """Impact categorization for startup prioritization."""

    CRITICAL = {
        "threshold": 100000,
        "description": "Mission-critical, company-defining impact",
    }
    HIGH = {
        "threshold": 50000,
        "description": "Significant value creation, scaling enabler",
    }
    MEDIUM = {
        "threshold": 15000,
        "description": "Operational improvement, efficiency gain",
    }
    LOW = {"threshold": 5000, "description": "Incremental improvement, good practice"}


@dataclass
class StartupKPIs:
    """Key Performance Indicators relevant to startup growth."""

    # Growth Metrics
    user_impact_multiplier: float = 1.0  # How many users affected
    revenue_impact_monthly: float = 0.0  # Monthly recurring revenue impact
    customer_acquisition_cost_reduction: float = 0.0  # CAC improvement
    customer_lifetime_value_increase: float = 0.0  # CLV improvement

    # Operational Efficiency
    development_velocity_increase_pct: float = 0.0  # Sprint velocity improvement
    deployment_frequency_increase_pct: float = 0.0  # CD pipeline improvement
    incident_reduction_pct: float = 0.0  # Reliability improvement
    time_to_market_reduction_days: float = 0.0  # Feature delivery speed

    # Scale & Performance
    infrastructure_cost_reduction_pct: float = 0.0  # OpEx reduction
    system_throughput_increase_pct: float = 0.0  # Scalability improvement
    response_time_improvement_pct: float = 0.0  # User experience
    resource_utilization_improvement_pct: float = 0.0  # Efficiency

    # Team & Culture
    developer_satisfaction_score: float = 0.0  # Team happiness (1-10)
    onboarding_time_reduction_pct: float = 0.0  # New hire efficiency
    knowledge_sharing_score: float = 0.0  # Documentation/mentoring (1-10)
    technical_debt_reduction_score: float = 0.0  # Code health (1-10)


@dataclass
class CompetitiveAdvantage:
    """How this achievement provides competitive advantage."""

    differentiation_factor: str = ""  # What makes this unique
    market_timing_advantage: str = ""  # First-mover or timing benefits
    barrier_to_entry_created: str = ""  # Moats built
    patent_potential: bool = False  # IP creation opportunity
    talent_attraction_value: str = ""  # Recruiting advantage


@dataclass
class BusinessValueBreakdown:
    """Detailed breakdown of business value calculation."""

    # Core Calculation
    base_value: float = 0.0
    multipliers: Dict[str, float] = field(default_factory=dict)
    adjustments: Dict[str, float] = field(default_factory=dict)

    # Time-based components
    hourly_rates: Dict[str, float] = field(default_factory=dict)
    time_periods: Dict[str, int] = field(default_factory=dict)

    # Cost components
    infrastructure_costs: Dict[str, float] = field(default_factory=dict)
    operational_costs: Dict[str, float] = field(default_factory=dict)

    # Risk components
    incident_costs: Dict[str, float] = field(default_factory=dict)
    compliance_costs: Dict[str, float] = field(default_factory=dict)


@dataclass
class MarketContext:
    """Market and industry context for valuation."""

    industry_vertical: str = ""  # SaaS, FinTech, HealthTech, etc.
    company_stage: str = ""  # Seed, Series A, Series B, etc.
    team_size: int = 0  # Total company size
    engineering_team_size: int = 0  # Engineering team size
    geographic_market: str = ""  # SF, Austin, Remote, etc.

    # Benchmarks
    industry_average_salary: float = 0.0
    market_rate_multiplier: float = 1.0  # Geographic adjustment


@dataclass
class StrategicValue:
    """Strategic value beyond immediate financial impact."""

    platform_enablement: bool = False  # Enables future features
    data_collection_value: bool = False  # Creates valuable datasets
    partnership_opportunities: List[str] = field(default_factory=list)
    acquisition_attractiveness: str = ""  # M&A value proposition
    funding_story_impact: str = ""  # VC pitch enhancement


@dataclass
class ComprehensiveBusinessValue:
    """Complete business value model for startup contexts."""

    # Core Value (required fields first)
    total_value: float
    value_type: ValueType
    confidence: float  # 0.0 - 1.0
    confidence_level: ConfidenceLevel
    calculation_method: str
    impact_tier: BusinessImpactTier

    # Core Value (optional fields with defaults)
    currency: str = "USD"
    period: str = "yearly"  # yearly, monthly, one-time
    data_sources: List[str] = field(default_factory=list)

    # Impact Classification
    roi_multiple: float = 0.0  # Return on investment multiple
    payback_period_months: float = 0.0  # Time to break even

    # Detailed Breakdown
    breakdown: BusinessValueBreakdown = field(default_factory=BusinessValueBreakdown)
    startup_kpis: StartupKPIs = field(default_factory=StartupKPIs)

    # Strategic Context
    market_context: MarketContext = field(default_factory=MarketContext)
    competitive_advantage: CompetitiveAdvantage = field(
        default_factory=CompetitiveAdvantage
    )
    strategic_value: StrategicValue = field(default_factory=StrategicValue)

    # Validation & Evidence
    supporting_metrics: Dict[str, Union[float, str]] = field(default_factory=dict)
    testimonials: List[str] = field(default_factory=list)
    before_after_comparison: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_validated: Optional[datetime] = None
    achievement_id: Optional[str] = None

    def to_json(self) -> str:
        """Convert to JSON for database storage."""

        def serialize_value(obj):
            if isinstance(obj, Enum):
                return obj.value
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif hasattr(obj, "__dict__"):
                return {k: serialize_value(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, dict):
                return {k: serialize_value(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_value(item) for item in obj]
            return obj

        return json.dumps(serialize_value(self), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ComprehensiveBusinessValue":
        """Create instance from JSON string."""
        data = json.loads(json_str)
        # TODO: Implement proper deserialization
        return cls(**data)

    def get_elevator_pitch(self) -> str:
        """Generate a concise value proposition for presentations."""
        impact_desc = self.impact_tier.value["description"]
        confidence_desc = self.confidence_level.value["description"]

        return f"""
        💰 **${self.total_value:,.0f} {self.period}** business value
        🎯 **{impact_desc}** ({self.impact_tier.name} tier)
        📊 **{confidence_desc}** (confidence: {self.confidence:.1%})
        ⚡ **{self.value_type.value.replace("_", " ").title()}** via {self.calculation_method}
        """

    def get_startup_dashboard_summary(self) -> Dict[str, Union[str, float]]:
        """Generate startup-friendly dashboard metrics."""
        return {
            # Financial Impact
            "annual_value": self.total_value,
            "monthly_value": self.total_value / 12,
            "roi_multiple": self.roi_multiple,
            "payback_months": self.payback_period_months,
            # Growth Metrics
            "users_impacted": self.startup_kpis.user_impact_multiplier,
            "revenue_impact_monthly": self.startup_kpis.revenue_impact_monthly,
            "velocity_increase": f"{self.startup_kpis.development_velocity_increase_pct}%",
            "time_to_market_improvement": f"{self.startup_kpis.time_to_market_reduction_days} days",
            # Efficiency Metrics
            "cost_reduction": f"{self.startup_kpis.infrastructure_cost_reduction_pct}%",
            "performance_improvement": f"{self.startup_kpis.response_time_improvement_pct}%",
            "incident_reduction": f"{self.startup_kpis.incident_reduction_pct}%",
            # Strategic Value
            "competitive_advantage": self.competitive_advantage.differentiation_factor,
            "platform_enablement": self.strategic_value.platform_enablement,
            "funding_story_impact": self.strategic_value.funding_story_impact,
        }

    def get_interview_talking_points(self) -> List[str]:
        """Generate talking points for startup interviews."""
        points = []

        # Quantified Impact
        points.append(
            f"Delivered ${self.total_value:,.0f} in measurable business value through {self.value_type.value.replace('_', ' ')}"
        )

        # Scale & Growth
        if self.startup_kpis.user_impact_multiplier > 1:
            points.append(
                f"Impacted {self.startup_kpis.user_impact_multiplier:,.0f} users with improved experience"
            )

        if self.startup_kpis.development_velocity_increase_pct > 0:
            points.append(
                f"Increased team velocity by {self.startup_kpis.development_velocity_increase_pct}%, accelerating product delivery"
            )

        # Efficiency & Scale
        if self.startup_kpis.infrastructure_cost_reduction_pct > 0:
            points.append(
                f"Reduced infrastructure costs by {self.startup_kpis.infrastructure_cost_reduction_pct}%, improving unit economics"
            )

        # Risk & Reliability
        if self.startup_kpis.incident_reduction_pct > 0:
            points.append(
                f"Improved system reliability by {self.startup_kpis.incident_reduction_pct}%, reducing customer churn risk"
            )

        # Strategic Value
        if self.competitive_advantage.differentiation_factor:
            points.append(
                f"Created competitive advantage: {self.competitive_advantage.differentiation_factor}"
            )

        if self.strategic_value.platform_enablement:
            points.append(
                "Built platform capabilities enabling future product expansion"
            )

        return points


# Factory functions for common startup scenarios
def create_time_savings_value(
    hours_saved: float, team_size: int, role: str = "senior", period: str = "weekly"
) -> ComprehensiveBusinessValue:
    """Create business value for time savings scenarios."""

    rate_map = {"junior": 75, "mid": 100, "senior": 125, "lead": 150}
    hourly_rate = rate_map.get(role, 100)

    if period == "weekly":
        annual_hours = hours_saved * 52 * team_size
    elif period == "monthly":
        annual_hours = hours_saved * 12 * team_size
    else:
        annual_hours = hours_saved * team_size

    total_value = annual_hours * hourly_rate

    # Calculate startup KPIs
    startup_kpis = StartupKPIs(
        development_velocity_increase_pct=min(25.0, hours_saved * 2),  # Rough estimate
        time_to_market_reduction_days=annual_hours / 8,  # Convert hours to days
        developer_satisfaction_score=min(
            10.0, 7.0 + (hours_saved / 10)
        ),  # Happiness boost
    )

    return ComprehensiveBusinessValue(
        total_value=total_value,
        value_type=ValueType.TIME_SAVINGS,
        confidence=0.8,
        confidence_level=ConfidenceLevel.MEDIUM,
        calculation_method="time_calculation_with_role_adjustment",
        impact_tier=_determine_impact_tier(total_value),
        roi_multiple=total_value / (hourly_rate * 40),  # Assume 40 hours to implement
        payback_period_months=1.0,  # Time savings pay back immediately
        startup_kpis=startup_kpis,
        breakdown=BusinessValueBreakdown(
            base_value=annual_hours * hourly_rate,
            hourly_rates={role: hourly_rate},
            time_periods={"annual_hours": annual_hours, "team_size": team_size},
        ),
    )


def _determine_impact_tier(value: float) -> BusinessImpactTier:
    """Determine impact tier based on value."""
    if value >= BusinessImpactTier.CRITICAL.value["threshold"]:
        return BusinessImpactTier.CRITICAL
    elif value >= BusinessImpactTier.HIGH.value["threshold"]:
        return BusinessImpactTier.HIGH
    elif value >= BusinessImpactTier.MEDIUM.value["threshold"]:
        return BusinessImpactTier.MEDIUM
    else:
        return BusinessImpactTier.LOW


# Example usage and test cases
if __name__ == "__main__":
    # Example: Senior developer time savings for 4-person team
    value = create_time_savings_value(
        hours_saved=8, team_size=4, role="senior", period="weekly"
    )

    print("=== Startup Interview Business Value ===")
    print(value.get_elevator_pitch())
    print("\n=== Dashboard Metrics ===")
    for key, val in value.get_startup_dashboard_summary().items():
        print(f"{key}: {val}")

    print("\n=== Interview Talking Points ===")
    for point in value.get_interview_talking_points():
        print(f"• {point}")

    print(f"\n=== JSON Storage (length: {len(value.to_json())} chars) ===")
    print(
        value.to_json()[:500] + "..." if len(value.to_json()) > 500 else value.to_json()
    )
