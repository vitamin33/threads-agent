"""
Realistic Metrics Calculator for PR Value Analysis

Provides industry-standard, interview-ready metric calculations
with transparent methodologies and realistic assumptions.
"""

from typing import Dict
from dataclasses import dataclass
import math


@dataclass
class CloudCostModel:
    """Realistic cloud infrastructure cost model."""

    # AWS/GCP typical costs
    server_cost_per_year: float = 12000  # t3.large equivalent
    load_balancer_cost: float = 3000  # Per year
    bandwidth_cost_per_gb: float = 0.09  # Egress costs
    storage_cost_per_tb_year: float = 276  # S3/GCS standard


@dataclass
class DevelopmentCostModel:
    """Realistic development cost model."""

    developer_rate_per_hour: float = 150  # Senior developer
    qa_overhead_factor: float = 0.3  # 30% QA time
    deployment_overhead_factor: float = 0.2  # 20% DevOps time
    maintenance_factor_year_one: float = 0.15  # 15% maintenance


class RealisticMetricsCalculator:
    """Calculate realistic, defensible business metrics."""

    def __init__(self):
        self.cloud_costs = CloudCostModel()
        self.dev_costs = DevelopmentCostModel()

    def calculate_infrastructure_savings(
        self,
        current_rps: float,
        baseline_rps: float,
        current_latency_ms: float,
        baseline_latency_ms: float,
    ) -> Dict[str, float]:
        """Calculate realistic infrastructure savings."""

        # Performance improvement factor
        throughput_improvement = current_rps / baseline_rps if baseline_rps > 0 else 1
        latency_improvement = (
            baseline_latency_ms / current_latency_ms if current_latency_ms > 0 else 1
        )

        # Combined improvement score (weighted)
        performance_factor = (throughput_improvement * 0.7) + (
            latency_improvement * 0.3
        )

        # Server capacity calculation
        # Assume 1 server handles 200 RPS at baseline
        baseline_servers_needed = math.ceil(baseline_rps / 200)
        current_servers_needed = math.ceil(current_rps / (200 * performance_factor))
        servers_saved = max(0, baseline_servers_needed - current_servers_needed)

        # Cost calculations
        server_savings = servers_saved * self.cloud_costs.server_cost_per_year

        # Additional savings from better performance
        # Less bandwidth usage due to faster responses
        bandwidth_savings = 0
        if latency_improvement > 1.2:  # 20% improvement threshold
            # Estimate 10TB/month baseline traffic
            monthly_bandwidth_gb = 10000
            bandwidth_reduction = (
                latency_improvement - 1
            ) * 0.1  # 10% per x improvement
            bandwidth_savings = (
                monthly_bandwidth_gb
                * bandwidth_reduction
                * self.cloud_costs.bandwidth_cost_per_gb
                * 12
            )

        # Load balancer efficiency (fewer needed with better performance)
        lb_savings = 0
        if servers_saved >= 2:
            lb_savings = self.cloud_costs.load_balancer_cost  # Save 1 LB

        total_savings = server_savings + bandwidth_savings + lb_savings

        return {
            "total_annual_savings": round(total_savings, 0),
            "server_cost_savings": round(server_savings, 0),
            "bandwidth_savings": round(bandwidth_savings, 0),
            "load_balancer_savings": round(lb_savings, 0),
            "servers_reduced": servers_saved,
            "calculation_confidence": self._calculate_confidence(performance_factor),
        }

    def calculate_developer_productivity_impact(
        self,
        search_time_reduction_percent: float,
        debugging_time_reduction_percent: float,
        team_size: int = 10,
    ) -> Dict[str, float]:
        """Calculate realistic developer productivity savings."""

        # Average developer spends:
        # - 20% time searching for code/docs
        # - 25% time debugging
        search_time_per_week = 40 * 0.20  # 8 hours
        debug_time_per_week = 40 * 0.25  # 10 hours

        # Time saved per developer per week
        search_time_saved = search_time_per_week * (search_time_reduction_percent / 100)
        debug_time_saved = debug_time_per_week * (
            debugging_time_reduction_percent / 100
        )
        total_hours_saved_per_week = search_time_saved + debug_time_saved

        # Annual savings
        weeks_per_year = 48  # Account for holidays/PTO
        hours_saved_per_year = total_hours_saved_per_week * weeks_per_year * team_size
        productivity_savings = (
            hours_saved_per_year * self.dev_costs.developer_rate_per_hour
        )

        # Additional benefits
        # Faster onboarding (new developers productive 30% faster)
        onboarding_savings = 0
        if search_time_reduction_percent > 50:
            # Assume 2 new hires per year, 1 month onboarding
            onboarding_hours_saved = 160 * 0.3 * 2  # 30% of 160 hours * 2 people
            onboarding_savings = (
                onboarding_hours_saved * self.dev_costs.developer_rate_per_hour
            )

        return {
            "total_productivity_savings": round(
                productivity_savings + onboarding_savings, 0
            ),
            "hours_saved_per_year": round(hours_saved_per_year, 0),
            "search_efficiency_savings": round(
                search_time_saved
                * weeks_per_year
                * team_size
                * self.dev_costs.developer_rate_per_hour,
                0,
            ),
            "debugging_efficiency_savings": round(
                debug_time_saved
                * weeks_per_year
                * team_size
                * self.dev_costs.developer_rate_per_hour,
                0,
            ),
            "onboarding_acceleration_savings": round(onboarding_savings, 0),
            "productivity_improvement_percent": round(
                (total_hours_saved_per_week / 40) * 100, 1
            ),
        }

    def calculate_quality_impact(
        self,
        test_coverage_percent: float,
        bug_reduction_percent: float,
        mean_time_to_resolution_reduction_percent: float,
    ) -> Dict[str, float]:
        """Calculate quality improvement financial impact."""

        # Industry averages
        avg_bug_cost = 5000  # Cost to fix a production bug
        bugs_per_month_baseline = 20  # For medium-sized system
        mttr_hours_baseline = 4  # Mean time to resolution

        # Bug reduction savings
        bugs_prevented_per_year = (
            bugs_per_month_baseline * 12 * (bug_reduction_percent / 100)
        )
        bug_prevention_savings = bugs_prevented_per_year * avg_bug_cost

        # MTTR improvement savings
        mttr_improvement_hours = mttr_hours_baseline * (
            mean_time_to_resolution_reduction_percent / 100
        )
        incidents_per_year = (
            bugs_per_month_baseline * 12 * (1 - bug_reduction_percent / 100)
        )
        mttr_savings = (
            incidents_per_year
            * mttr_improvement_hours
            * self.dev_costs.developer_rate_per_hour
            * 3
        )  # 3 people typically involved

        # Customer satisfaction impact (reduced churn)
        # High quality (>85% coverage) correlates with 10% less churn
        churn_reduction_savings = 0
        if test_coverage_percent > 85:
            # Assume $1M ARR, 20% baseline churn
            arr = 1000000
            baseline_churn = 0.20
            churn_improvement = 0.10  # 10% reduction in churn
            churn_reduction_savings = arr * baseline_churn * churn_improvement

        return {
            "total_quality_savings": round(
                bug_prevention_savings + mttr_savings + churn_reduction_savings, 0
            ),
            "bug_prevention_savings": round(bug_prevention_savings, 0),
            "mttr_improvement_savings": round(mttr_savings, 0),
            "customer_retention_savings": round(churn_reduction_savings, 0),
            "bugs_prevented_annually": round(bugs_prevented_per_year, 0),
            "quality_score": self._calculate_quality_score(
                test_coverage_percent, bug_reduction_percent
            ),
        }

    def calculate_realistic_roi(
        self,
        development_hours: float,
        total_annual_savings: float,
        implementation_risk_factor: float = 0.8,  # 80% success probability
    ) -> Dict[str, float]:
        """Calculate realistic ROI with risk adjustment."""

        # True development cost
        base_dev_cost = development_hours * self.dev_costs.developer_rate_per_hour
        qa_cost = base_dev_cost * self.dev_costs.qa_overhead_factor
        deployment_cost = base_dev_cost * self.dev_costs.deployment_overhead_factor
        year_one_maintenance = (
            base_dev_cost * self.dev_costs.maintenance_factor_year_one
        )

        total_year_one_cost = (
            base_dev_cost + qa_cost + deployment_cost + year_one_maintenance
        )

        # Risk-adjusted savings
        risk_adjusted_savings = total_annual_savings * implementation_risk_factor

        # ROI calculations
        roi_year_one = (
            (risk_adjusted_savings - total_year_one_cost) / total_year_one_cost
        ) * 100
        roi_three_year = (
            (risk_adjusted_savings * 3 - total_year_one_cost) / total_year_one_cost
        ) * 100

        # Payback period
        if risk_adjusted_savings > 0:
            payback_months = (total_year_one_cost / risk_adjusted_savings) * 12
        else:
            payback_months = float("inf")

        return {
            "total_investment": round(total_year_one_cost, 0),
            "development_cost": round(base_dev_cost, 0),
            "qa_cost": round(qa_cost, 0),
            "deployment_cost": round(deployment_cost, 0),
            "maintenance_cost_year_one": round(year_one_maintenance, 0),
            "roi_year_one_percent": round(roi_year_one, 1),
            "roi_three_year_percent": round(roi_three_year, 1),
            "payback_period_months": round(payback_months, 1)
            if payback_months != float("inf")
            else None,
            "risk_adjusted_annual_savings": round(risk_adjusted_savings, 0),
            "break_even_point": self._calculate_break_even(
                total_year_one_cost, risk_adjusted_savings
            ),
        }

    def calculate_performance_score(
        self, current_rps: float, latency_ms: float, error_rate: float
    ) -> float:
        """Calculate realistic performance score (0-10)."""
        # RPS scoring (logarithmic scale)
        if current_rps >= 10000:
            rps_score = 10
        elif current_rps >= 5000:
            rps_score = 9
        elif current_rps >= 2000:
            rps_score = 8
        elif current_rps >= 1000:
            rps_score = 7
        elif current_rps >= 500:
            rps_score = 6
        elif current_rps >= 200:
            rps_score = 5
        else:
            rps_score = max(1, current_rps / 40)

        # Latency scoring
        if latency_ms <= 50:
            latency_score = 10
        elif latency_ms <= 100:
            latency_score = 9
        elif latency_ms <= 200:
            latency_score = 8
        elif latency_ms <= 500:
            latency_score = 6
        elif latency_ms <= 1000:
            latency_score = 4
        else:
            latency_score = 2

        # Error rate scoring
        if error_rate <= 0.001:  # 0.1%
            error_score = 10
        elif error_rate <= 0.01:  # 1%
            error_score = 8
        elif error_rate <= 0.05:  # 5%
            error_score = 5
        else:
            error_score = 2

        # Weighted average
        return round((rps_score * 0.4 + latency_score * 0.4 + error_score * 0.2), 1)

    def calculate_innovation_score(
        self,
        uses_novel_algorithm: bool,
        performance_improvement_percent: float,
        introduces_new_capability: bool,
        patent_potential: bool,
        industry_first: bool,
    ) -> float:
        """Calculate realistic innovation score."""
        score = 5.0  # Base score

        if uses_novel_algorithm:
            score += 1.5
        if performance_improvement_percent > 100:
            score += 1.5
        elif performance_improvement_percent > 50:
            score += 1.0
        if introduces_new_capability:
            score += 1.0
        if patent_potential:
            score += 1.0
        if industry_first:
            score += 2.0

        return min(10.0, score)

    def _calculate_confidence(self, factor: float) -> str:
        """Calculate confidence level for estimates."""
        if factor < 1.5:
            return "high"
        elif factor < 3.0:
            return "medium"
        else:
            return "low"

    def _calculate_quality_score(self, coverage: float, bug_reduction: float) -> float:
        """Calculate quality score based on metrics."""
        coverage_score = min(10, coverage / 10)
        bug_score = min(10, bug_reduction / 10)
        return round((coverage_score * 0.6 + bug_score * 0.4), 1)

    def _calculate_break_even(self, investment: float, annual_return: float) -> str:
        """Calculate break-even point."""
        if annual_return <= 0:
            return "Never"
        months = (investment / annual_return) * 12
        if months <= 12:
            return f"{round(months, 1)} months"
        else:
            return f"{round(months / 12, 1)} years"

    def generate_interview_ready_summary(self, all_metrics: Dict) -> str:
        """Generate interview-ready explanation of metrics."""
        return f"""
## 📊 Metrics Calculation Methodology

### Infrastructure Savings: ${all_metrics.get("infrastructure_savings", 0):,}
- **Calculation**: Based on server reduction from performance improvements
- **Assumptions**: 
  - Baseline: 1 server per 200 RPS ($12k/year per server)
  - Current: {all_metrics.get("servers_reduced", 0)} fewer servers needed
  - Includes bandwidth and load balancer savings
- **Confidence**: {all_metrics.get("confidence", "medium")}

### Developer Productivity: ${all_metrics.get("productivity_savings", 0):,}
- **Calculation**: Time saved × hourly rate × team size
- **Assumptions**:
  - {all_metrics.get("hours_saved_per_year", 0)} hours saved annually
  - $150/hour senior developer rate
  - Team of {all_metrics.get("team_size", 10)} developers
- **Breakdown**:
  - Search efficiency: {all_metrics.get("search_time_reduction", 0)}% improvement
  - Debugging efficiency: {all_metrics.get("debug_time_reduction", 0)}% improvement

### Quality Impact: ${all_metrics.get("quality_savings", 0):,}
- **Calculation**: Prevented bugs × average bug cost
- **Assumptions**:
  - {all_metrics.get("bugs_prevented", 0)} bugs prevented annually
  - $5,000 average cost per production bug
  - {all_metrics.get("mttr_reduction", 0)}% faster incident resolution
  
### ROI: {all_metrics.get("roi_year_one", 0)}% (Year 1)
- **Investment**: ${all_metrics.get("total_investment", 0):,}
- **Risk-Adjusted Returns**: ${all_metrics.get("annual_returns", 0):,}
- **Payback Period**: {all_metrics.get("payback_period", "N/A")}
- **3-Year ROI**: {all_metrics.get("roi_three_year", 0)}%

### Key Success Factors:
1. **Performance**: {all_metrics.get("performance_score", 0)}/10
2. **Quality**: {all_metrics.get("quality_score", 0)}/10
3. **Innovation**: {all_metrics.get("innovation_score", 0)}/10

All calculations use industry-standard assumptions and conservative estimates.
"""


# Example usage for interviews
def demonstrate_realistic_metrics():
    """Show how to calculate defensible metrics for interviews."""
    calculator = RealisticMetricsCalculator()

    # Performance improvements
    infra_savings = calculator.calculate_infrastructure_savings(
        current_rps=1200,
        baseline_rps=500,
        current_latency_ms=150,
        baseline_latency_ms=400,
    )

    # Developer productivity
    productivity = calculator.calculate_developer_productivity_impact(
        search_time_reduction_percent=60,  # RAG makes search 60% faster
        debugging_time_reduction_percent=40,  # Better code discovery
        team_size=10,
    )

    # Quality improvements
    quality = calculator.calculate_quality_impact(
        test_coverage_percent=87,
        bug_reduction_percent=35,
        mean_time_to_resolution_reduction_percent=45,
    )

    # Calculate ROI
    total_savings = (
        infra_savings["total_annual_savings"]
        + productivity["total_productivity_savings"]
        + quality["total_quality_savings"]
    )

    roi = calculator.calculate_realistic_roi(
        development_hours=320,  # 2 developers × 4 weeks × 40 hours
        total_annual_savings=total_savings,
        implementation_risk_factor=0.8,
    )

    # Performance score
    perf_score = calculator.calculate_performance_score(
        current_rps=1200,
        latency_ms=150,
        error_rate=0.002,  # 0.2% error rate
    )

    # Innovation score
    innovation_score = calculator.calculate_innovation_score(
        uses_novel_algorithm=True,  # RAG is novel
        performance_improvement_percent=140,
        introduces_new_capability=True,  # Semantic search
        patent_potential=False,
        industry_first=False,
    )

    # Compile all metrics
    all_metrics = {
        "infrastructure_savings": infra_savings["total_annual_savings"],
        "productivity_savings": productivity["total_productivity_savings"],
        "quality_savings": quality["total_quality_savings"],
        "total_annual_savings": total_savings,
        "roi_year_one": roi["roi_year_one_percent"],
        "roi_three_year": roi["roi_three_year_percent"],
        "payback_period": roi["payback_period_months"],
        "total_investment": roi["total_investment"],
        "performance_score": perf_score,
        "quality_score": quality["quality_score"],
        "innovation_score": innovation_score,
        "servers_reduced": infra_savings["servers_reduced"],
        "hours_saved_per_year": productivity["hours_saved_per_year"],
        "bugs_prevented": quality["bugs_prevented_annually"],
        "team_size": 10,
        "search_time_reduction": 60,
        "debug_time_reduction": 40,
        "mttr_reduction": 45,
        "annual_returns": roi["risk_adjusted_annual_savings"],
        "confidence": infra_savings["calculation_confidence"],
    }

    print("📊 Realistic Metrics for PR #91:")
    print(f"Infrastructure Savings: ${infra_savings['total_annual_savings']:,}")
    print(f"Productivity Savings: ${productivity['total_productivity_savings']:,}")
    print(f"Quality Savings: ${quality['total_quality_savings']:,}")
    print(f"Total Annual Savings: ${total_savings:,}")
    print(f"\nROI Year 1: {roi['roi_year_one_percent']}%")
    print(f"Payback Period: {roi['payback_period_months']} months")
    print(f"Performance Score: {perf_score}/10")
    print(f"Innovation Score: {innovation_score}/10")

    # Generate interview summary
    summary = calculator.generate_interview_ready_summary(all_metrics)
    print(summary)


if __name__ == "__main__":
    demonstrate_realistic_metrics()
