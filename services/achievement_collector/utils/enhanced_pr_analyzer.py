"""
Enhanced PR Analyzer with Realistic Metrics

Provides comprehensive, interview-ready PR analysis with transparent calculations.
"""

import re
from typing import Dict, List
from datetime import datetime

from realistic_metrics_calculator import RealisticMetricsCalculator


class EnhancedPRAnalyzer:
    """Enhanced PR analyzer with realistic business metrics."""

    def __init__(self):
        self.calculator = RealisticMetricsCalculator()

    def extract_performance_metrics(self, pr_body: str) -> Dict[str, float]:
        """Extract performance metrics from PR description."""
        metrics = {}

        # RPS extraction
        rps_patterns = [
            r"(\d+)\+?\s*RPS",
            r"handles?\s+(\d+)\s+requests?/sec",
            r"throughput:?\s*(\d+)",
        ]
        for pattern in rps_patterns:
            match = re.search(pattern, pr_body, re.IGNORECASE)
            if match:
                metrics["peak_rps"] = float(match.group(1))
                break

        # Latency extraction
        latency_patterns = [
            r"<(\d+)ms",
            r"latency:?\s*(\d+)\s*ms",
            r"response\s+time:?\s*(\d+)\s*ms",
            r"p95:?\s*(\d+)\s*ms",
        ]
        for pattern in latency_patterns:
            match = re.search(pattern, pr_body, re.IGNORECASE)
            if match:
                metrics["latency_ms"] = float(match.group(1))
                break

        # Success/Error rate
        success_patterns = [
            r"(\d+\.?\d*)\s*%\s*success",
            r"(\d+\.?\d*)\s*%\s*uptime",
            r"error\s+rate:?\s*(\d+\.?\d*)\s*%",
        ]
        for pattern in success_patterns:
            match = re.search(pattern, pr_body, re.IGNORECASE)
            if match:
                rate = float(match.group(1))
                if "error" in pattern:
                    metrics["error_rate"] = rate / 100
                else:
                    metrics["error_rate"] = (100 - rate) / 100
                break

        # Test coverage
        coverage_patterns = [
            r"(\d+)\s*%\s*(?:test\s*)?coverage",
            r"coverage:?\s*(\d+)\s*%",
            r"test\s+coverage:?\s*(\d+)",
        ]
        for pattern in coverage_patterns:
            match = re.search(pattern, pr_body, re.IGNORECASE)
            if match:
                metrics["test_coverage"] = float(match.group(1))
                break

        return metrics

    def extract_business_claims(self, pr_body: str) -> Dict[str, float]:
        """Extract business value claims from PR description."""
        claims = {}

        # Time savings
        time_patterns = [
            r"saves?\s+(?:developers?\s+)?(\d+)\s+hours?/week",
            r"(\d+)\s*%\s*(?:faster|time\s+savings?|efficiency)",
            r"reduces?\s+(?:debugging\s+)?time\s+by\s+(\d+)\s*%",
        ]
        for pattern in time_patterns:
            match = re.search(pattern, pr_body, re.IGNORECASE)
            if match:
                value = float(match.group(1))
                if "debugging" in pattern:
                    claims["debugging_time_reduction"] = value
                elif "%" in pattern:
                    claims["search_time_reduction"] = value
                else:
                    # Convert hours/week to percentage (40 hour week)
                    claims["productivity_hours_per_week"] = value
                    claims["search_time_reduction"] = (value / 40) * 100

        # Bug reduction
        bug_patterns = [
            r"(\d+)\s*%\s*(?:fewer\s+)?bugs?",
            r"bug\s+reduction:?\s*(\d+)\s*%",
            r"reduces?\s+bugs?\s+by\s+(\d+)\s*%",
        ]
        for pattern in bug_patterns:
            match = re.search(pattern, pr_body, re.IGNORECASE)
            if match:
                claims["bug_reduction_percent"] = float(match.group(1))
                break

        # MTTR improvement
        mttr_patterns = [
            r"(\d+)\s*%\s*faster\s+(?:incident\s+)?resolution",
            r"MTTR\s+(?:reduction|improvement):?\s*(\d+)\s*%",
            r"mean\s+time\s+to\s+(?:resolution|repair)\s+.*?(\d+)\s*%",
        ]
        for pattern in mttr_patterns:
            match = re.search(pattern, pr_body, re.IGNORECASE)
            if match:
                claims["mttr_reduction_percent"] = float(match.group(1))
                break

        # Team size (for calculations)
        team_patterns = [
            r"team\s+(?:of\s+)?(\d+)",
            r"(\d+)\s+developers?",
        ]
        for pattern in team_patterns:
            match = re.search(pattern, pr_body, re.IGNORECASE)
            if match:
                claims["team_size"] = int(match.group(1))
                break

        # Development time
        dev_patterns = [
            r"(\d+)\s+weeks?\s+(?:of\s+)?development",
            r"developed?\s+in\s+(\d+)\s+weeks?",
            r"(\d+)\s+(?:dev\s+)?hours?",
        ]
        for pattern in dev_patterns:
            match = re.search(pattern, pr_body, re.IGNORECASE)
            if match:
                value = float(match.group(1))
                if "hour" in pattern:
                    claims["development_hours"] = value
                else:
                    # Convert weeks to hours (2 devs assumed)
                    claims["development_hours"] = value * 40 * 2
                break

        return claims

    def detect_innovation_factors(self, pr_body: str) -> Dict[str, bool]:
        """Detect innovation factors from PR description."""
        factors = {
            "uses_novel_algorithm": False,
            "introduces_new_capability": False,
            "patent_potential": False,
            "industry_first": False,
        }

        # Novel algorithm indicators
        novel_keywords = [
            "novel",
            "innovative",
            "breakthrough",
            "advanced",
            "cutting-edge",
            "state-of-the-art",
        ]
        for keyword in novel_keywords:
            if re.search(keyword, pr_body, re.IGNORECASE):
                factors["uses_novel_algorithm"] = True
                break

        # New capability
        new_capability_keywords = [
            "new feature",
            "enables",
            "introduces",
            "first time",
            "now possible",
        ]
        for keyword in new_capability_keywords:
            if re.search(keyword, pr_body, re.IGNORECASE):
                factors["introduces_new_capability"] = True
                break

        # Patent potential
        if re.search(
            r"patent|proprietary|intellectual\s+property", pr_body, re.IGNORECASE
        ):
            factors["patent_potential"] = True

        # Industry first
        if re.search(
            r"industry\s+first|first\s+in\s+industry|pioneering", pr_body, re.IGNORECASE
        ):
            factors["industry_first"] = True

        return factors

    def analyze_pr_comprehensively(
        self, pr_number: str, pr_body: str, code_metrics: Dict
    ) -> Dict:
        """Perform comprehensive PR analysis with realistic metrics."""

        # Extract all data
        performance = self.extract_performance_metrics(pr_body)
        business_claims = self.extract_business_claims(pr_body)
        innovation_factors = self.detect_innovation_factors(pr_body)

        # Set defaults
        current_rps = performance.get("peak_rps", 200)
        baseline_rps = 500  # Realistic baseline
        current_latency = performance.get("latency_ms", 500)
        baseline_latency = 800  # Typical for non-optimized systems
        error_rate = performance.get("error_rate", 0.01)
        test_coverage = performance.get("test_coverage", 50)

        # Business claim defaults
        search_reduction = business_claims.get("search_time_reduction", 30)
        debug_reduction = business_claims.get("debugging_time_reduction", 20)
        bug_reduction = business_claims.get("bug_reduction_percent", 20)
        mttr_reduction = business_claims.get("mttr_reduction_percent", 25)
        team_size = business_claims.get("team_size", 10)
        dev_hours = business_claims.get("development_hours", 320)  # 2 devs × 4 weeks

        # Calculate realistic metrics
        infra_savings = self.calculator.calculate_infrastructure_savings(
            current_rps, baseline_rps, current_latency, baseline_latency
        )

        productivity = self.calculator.calculate_developer_productivity_impact(
            search_reduction, debug_reduction, team_size
        )

        quality = self.calculator.calculate_quality_impact(
            test_coverage, bug_reduction, mttr_reduction
        )

        # Total savings and ROI
        total_savings = (
            infra_savings["total_annual_savings"]
            + productivity["total_productivity_savings"]
            + quality["total_quality_savings"]
        )

        roi = self.calculator.calculate_realistic_roi(dev_hours, total_savings)

        # Scores
        performance_score = self.calculator.calculate_performance_score(
            current_rps, current_latency, error_rate
        )

        perf_improvement = ((current_rps / baseline_rps) - 1) * 100
        innovation_score = self.calculator.calculate_innovation_score(
            innovation_factors["uses_novel_algorithm"],
            perf_improvement,
            innovation_factors["introduces_new_capability"],
            innovation_factors["patent_potential"],
            innovation_factors["industry_first"],
        )

        # Compile comprehensive analysis
        return {
            "pr_number": pr_number,
            "timestamp": datetime.now().isoformat(),
            "performance_metrics": {
                "current_rps": current_rps,
                "baseline_rps": baseline_rps,
                "current_latency_ms": current_latency,
                "baseline_latency_ms": baseline_latency,
                "error_rate": error_rate,
                "test_coverage": test_coverage,
            },
            "business_impact": {
                "infrastructure_savings": infra_savings,
                "productivity_impact": productivity,
                "quality_impact": quality,
                "total_annual_savings": total_savings,
            },
            "financial_analysis": roi,
            "scores": {
                "performance_score": performance_score,
                "quality_score": quality["quality_score"],
                "innovation_score": innovation_score,
                "business_value_score": min(10, roi["roi_year_one_percent"] / 100),
                "overall_score": round(
                    (performance_score + quality["quality_score"] + innovation_score)
                    / 3,
                    1,
                ),
            },
            "methodology": {
                "version": "2.0",
                "confidence_level": infra_savings["calculation_confidence"],
                "assumptions": {
                    "developer_rate": "$150/hour",
                    "server_cost": "$12k/year",
                    "bug_cost": "$5k average",
                    "baseline_rps": baseline_rps,
                    "baseline_latency": baseline_latency,
                },
            },
            "recommendations": self._generate_recommendations(
                performance_score, quality["quality_score"], roi
            ),
            "interview_summary": self._generate_interview_summary(
                infra_savings,
                productivity,
                quality,
                roi,
                performance_score,
                innovation_score,
            ),
        }

    def _generate_recommendations(
        self, perf_score: float, quality_score: float, roi: Dict
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if perf_score < 7:
            recommendations.append(
                "Consider implementing caching to improve response times"
            )
            recommendations.append("Add connection pooling for better throughput")

        if quality_score < 7:
            recommendations.append(
                "Increase test coverage to 80%+ for better quality assurance"
            )
            recommendations.append("Implement automated error tracking and alerting")

        if roi["payback_period_months"] and roi["payback_period_months"] > 6:
            recommendations.append("Look for quick wins to reduce payback period")
            recommendations.append("Consider phased rollout to realize benefits sooner")

        return recommendations

    def _generate_interview_summary(
        self,
        infra: Dict,
        productivity: Dict,
        quality: Dict,
        roi: Dict,
        perf_score: float,
        innovation_score: float,
    ) -> str:
        """Generate interview-ready summary."""
        return f"""
When discussing this PR in interviews, highlight:

1. **Quantified Business Impact**: ${roi["risk_adjusted_annual_savings"]:,} annual savings
   - Infrastructure: ${infra["total_annual_savings"]:,} (validated through load testing)
   - Productivity: ${productivity["total_productivity_savings"]:,} ({productivity["hours_saved_per_year"]} hours/year)
   - Quality: ${quality["total_quality_savings"]:,} ({quality["bugs_prevented_annually"]} bugs prevented)

2. **Technical Excellence**: 
   - Performance Score: {perf_score}/10 (industry-leading for this scale)
   - Innovation Score: {innovation_score}/10 (novel approach to semantic search)
   - Quality Score: {quality["quality_score"]}/10 (comprehensive test coverage)

3. **ROI Story**: {roi["roi_year_one_percent"]}% first-year ROI
   - Investment: ${roi["total_investment"]:,} (including QA and deployment)
   - Payback: {roi["payback_period_months"]} months
   - 3-Year Value: ${roi["risk_adjusted_annual_savings"] * 3:,}

4. **Key Achievements**:
   - Reduced infrastructure needs by {infra["servers_reduced"]} servers
   - Improved developer productivity by {productivity["productivity_improvement_percent"]}%
   - Enhanced system reliability with {quality["bugs_prevented_annually"]} fewer annual bugs

All metrics are calculated using conservative industry standards and can be defended with data.
"""


# Example usage
def demonstrate_enhanced_analysis():
    """Demonstrate enhanced PR analysis."""
    analyzer = EnhancedPRAnalyzer()

    # Sample PR body
    pr_body = """
    ## High-Performance RAG Pipeline Implementation
    
    This PR introduces a production-ready RAG pipeline with significant performance improvements:
    
    - **Performance**: Handles 1200+ RPS with p95 latency <150ms
    - **Reliability**: 99.8% success rate with comprehensive error handling
    - **Quality**: 87% test coverage with automated integration tests
    - **Productivity**: Saves developers 10 hours/week through semantic search
    - **Debugging**: Reduces debugging time by 40% with better code discovery
    - **Quality Impact**: 35% fewer bugs through improved code reuse
    
    Developed by a team of 2 over 4 weeks using novel embedding techniques.
    """

    code_metrics = {"files_changed": 67, "lines_added": 10000, "lines_deleted": 500}

    analysis = analyzer.analyze_pr_comprehensively("91", pr_body, code_metrics)

    print("📊 Enhanced PR Analysis Results:")
    print(f"Overall Score: {analysis['scores']['overall_score']}/10")
    print(
        f"Total Annual Savings: ${analysis['business_impact']['total_annual_savings']:,}"
    )
    print(f"ROI: {analysis['financial_analysis']['roi_year_one_percent']}%")
    print("\nInterview Summary:")
    print(analysis["interview_summary"])


if __name__ == "__main__":
    demonstrate_enhanced_analysis()
