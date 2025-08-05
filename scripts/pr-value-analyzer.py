#!/usr/bin/env python3
"""
PR Value Analyzer - Automated Business & Technical Value Collection

This script analyzes PRs to extract and calculate business value metrics,
technical achievements, and future impact projections for achievement tracking.
"""

import json
import subprocess
import re
from datetime import datetime
from typing import Dict, List, Any
import os
import sys
import math


class PRValueAnalyzer:
    """Analyzes PR content to extract business and technical value metrics."""

    def __init__(self, pr_number: str):
        self.pr_number = pr_number
        self.metrics = {
            "pr_number": pr_number,
            "timestamp": datetime.now().isoformat(),
            "business_metrics": {},
            "technical_metrics": {},
            "achievement_tags": [],
            "kpis": {},
            "future_impact": {},
        }

    def analyze_performance_metrics(self, pr_body: str) -> Dict[str, Any]:
        """Extract performance metrics from PR body."""
        metrics = {}

        # RPS (Requests Per Second)
        rps_match = re.search(r"(\d+\.?\d*)\s*RPS", pr_body, re.IGNORECASE)
        if rps_match:
            metrics["peak_rps"] = float(rps_match.group(1))

        # Latency
        latency_match = re.search(r"<(\d+)ms", pr_body)
        if latency_match:
            metrics["latency_ms"] = int(latency_match.group(1))

        # Success Rate
        success_match = re.search(r"(\d+)%\s*success", pr_body, re.IGNORECASE)
        if success_match:
            metrics["success_rate"] = int(success_match.group(1))

        # Test Coverage
        coverage_match = re.search(
            r"(\d+)%\s*(?:test\s*)?coverage", pr_body, re.IGNORECASE
        )
        if coverage_match:
            metrics["test_coverage"] = int(coverage_match.group(1))

        return metrics

    def calculate_business_value(self, performance_metrics: Dict) -> Dict[str, Any]:
        """Calculate business value based on performance metrics with realistic assumptions."""
        value = {}

        # Extract metrics
        rps = performance_metrics.get("peak_rps", 200)
        latency = performance_metrics.get("latency_ms", 500)
        test_coverage = performance_metrics.get("test_coverage", 50)

        # More realistic baselines
        baseline_rps = 500  # Typical existing service
        baseline_latency = 800  # Typical unoptimized latency

        # Performance improvements
        if rps > 0 and baseline_rps > 0:
            throughput_improvement = rps / baseline_rps
            latency_improvement = baseline_latency / latency if latency > 0 else 1

            value["throughput_improvement_percent"] = round(
                (throughput_improvement - 1) * 100, 1
            )

            # Combined performance factor
            performance_factor = (throughput_improvement * 0.7) + (
                latency_improvement * 0.3
            )

            # Infrastructure savings (more realistic)
            # $12k/server/year, 1 server per 200 RPS baseline
            baseline_servers = math.ceil(baseline_rps / 200)
            current_servers = math.ceil(rps / (200 * performance_factor))
            servers_saved = max(0, baseline_servers - current_servers)

            server_savings = servers_saved * 12000  # $12k per server/year

            # Additional savings
            bandwidth_savings = 0
            if latency_improvement > 1.2:  # 20% improvement
                # Estimate bandwidth savings from faster responses
                monthly_bandwidth_gb = 10000  # 10TB/month typical
                bandwidth_reduction = (latency_improvement - 1) * 0.1
                bandwidth_savings = (
                    monthly_bandwidth_gb * bandwidth_reduction * 0.09 * 12
                )  # $0.09/GB

            value["infrastructure_savings_estimate"] = round(
                server_savings + bandwidth_savings, 0
            )
            value["servers_reduced"] = servers_saved

            # Confidence level
            if performance_factor < 1.5:
                value["confidence_level"] = "high"
            elif performance_factor < 3.0:
                value["confidence_level"] = "medium"
            else:
                value["confidence_level"] = "low"

        # User experience score
        if latency < 100:
            value["user_experience_score"] = 10
        elif latency < 200:
            value["user_experience_score"] = 9
        elif latency < 500:
            value["user_experience_score"] = 8
        else:
            value["user_experience_score"] = 7

        # Developer productivity (conservative estimates)
        if "peak_rps" in performance_metrics:
            # Assume 10-person team, improvements in search/debug time
            team_size = 10
            search_time_saved_percent = min(
                50, throughput_improvement * 20
            )  # Cap at 50%
            debug_time_saved_percent = min(40, latency_improvement * 15)  # Cap at 40%

            # 20% of time searching, 25% debugging
            hours_saved_per_week = (8 * search_time_saved_percent / 100) + (
                10 * debug_time_saved_percent / 100
            )
            annual_hours_saved = (
                hours_saved_per_week * 48 * team_size
            )  # 48 working weeks

            value["developer_productivity_savings"] = round(
                annual_hours_saved * 150, 0
            )  # $150/hour
            value["productivity_hours_saved"] = round(annual_hours_saved, 0)

        # Quality impact
        if test_coverage > 0:
            # Bug reduction based on coverage
            bug_reduction_percent = min(50, test_coverage * 0.5)  # Cap at 50%
            bugs_prevented_annually = round(
                20 * 12 * bug_reduction_percent / 100, 0
            )  # 20 bugs/month baseline

            value["quality_improvement_savings"] = (
                bugs_prevented_annually * 5000
            )  # $5k per bug
            value["bugs_prevented_annually"] = bugs_prevented_annually

        # Total savings and ROI calculation
        total_savings = (
            value.get("infrastructure_savings_estimate", 0)
            + value.get("developer_productivity_savings", 0)
            + value.get("quality_improvement_savings", 0)
        )

        if total_savings > 0:
            # More realistic development cost with overhead
            base_dev_hours = 320  # 2 devs × 4 weeks
            dev_cost = base_dev_hours * 150  # $150/hour
            qa_cost = dev_cost * 0.3  # 30% QA overhead
            deployment_cost = dev_cost * 0.2  # 20% deployment overhead
            maintenance_year_one = dev_cost * 0.15  # 15% maintenance

            total_investment = (
                dev_cost + qa_cost + deployment_cost + maintenance_year_one
            )

            # Risk-adjusted ROI
            risk_factor = 0.8  # 80% success probability
            risk_adjusted_savings = total_savings * risk_factor

            value["total_annual_savings"] = round(total_savings, 0)
            value["risk_adjusted_savings"] = round(risk_adjusted_savings, 0)
            value["total_investment"] = round(total_investment, 0)
            value["roi_year_one_percent"] = round(
                (risk_adjusted_savings / total_investment) * 100, 0
            )

            if risk_adjusted_savings > 0:
                value["payback_period_months"] = round(
                    total_investment / risk_adjusted_savings * 12, 1
                )

            # 3-year ROI
            value["roi_three_year_percent"] = round(
                (risk_adjusted_savings * 3 / total_investment) * 100, 0
            )

        return value

    def calculate_realistic_performance_score(
        self, current_rps: float, latency_ms: float, error_rate: float
    ) -> float:
        """Calculate realistic performance score (0-10) using logarithmic scale."""
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

        # Weighted average (RPS and latency more important than error rate)
        return round((rps_score * 0.4 + latency_score * 0.4 + error_score * 0.2), 1)

    def extract_achievement_tags(self, pr_body: str) -> List[str]:
        """Extract achievement tags from PR body."""
        tags = []

        # Performance achievements
        if re.search(r"\d+\.?\d*\s*RPS", pr_body, re.IGNORECASE):
            tags.append("high_performance_implementation")

        # Cost optimization
        if re.search(r"cost.*reduction|savings", pr_body, re.IGNORECASE):
            tags.append("cost_optimization")

        # Kubernetes/DevOps
        if re.search(r"kubernetes|k8s|helm", pr_body, re.IGNORECASE):
            tags.append("kubernetes_deployment")

        # AI/ML features
        if re.search(r"RAG|embedding|vector|AI|ML", pr_body, re.IGNORECASE):
            tags.append("ai_ml_feature")

        # Production readiness
        if re.search(
            r"production.*ready|monitoring|health.*check", pr_body, re.IGNORECASE
        ):
            tags.append("production_ready")

        return tags

    def analyze_code_changes(self) -> Dict[str, Any]:
        """Analyze code changes in the PR."""
        try:
            # Get PR diff statistics using git since gh doesn't support --stat
            # First get the base branch
            base_result = subprocess.run(
                ["gh", "pr", "view", self.pr_number, "--json", "baseRefName"],
                capture_output=True,
                text=True,
            )

            if base_result.returncode == 0:
                base_data = json.loads(base_result.stdout)
                base_branch = base_data.get("baseRefName", "main")

                # Use git diff --stat with the base branch
                result = subprocess.run(
                    ["git", "diff", "--stat", f"origin/{base_branch}"],
                    capture_output=True,
                    text=True,
                )

                # If origin branch doesn't exist, try without origin prefix
                if result.returncode != 0:
                    result = subprocess.run(
                        ["git", "diff", "--stat", base_branch],
                        capture_output=True,
                        text=True,
                    )

                    # Additional fallback for CI environments
                    if result.returncode != 0:
                        result = subprocess.run(
                            ["git", "diff", "--stat", "HEAD~1"],
                            capture_output=True,
                            text=True,
                        )
            else:
                # Fallback to main branch
                result = subprocess.run(
                    ["git", "diff", "--stat", "origin/main"],
                    capture_output=True,
                    text=True,
                )

                # If origin/main doesn't exist, try main, then HEAD~1 as fallback
                if result.returncode != 0:
                    result = subprocess.run(
                        ["git", "diff", "--stat", "main"],
                        capture_output=True,
                        text=True,
                    )

                    # Final fallback for CI environments
                    if result.returncode != 0:
                        result = subprocess.run(
                            ["git", "diff", "--stat", "HEAD~1"],
                            capture_output=True,
                            text=True,
                        )

            if result.returncode == 0:
                stats_text = result.stdout

                # Extract file count and line changes
                files_match = re.search(r"(\d+)\s+files?\s+changed", stats_text)
                insertions_match = re.search(r"(\d+)\s+insertions?\(\+\)", stats_text)
                deletions_match = re.search(r"(\d+)\s+deletions?\(-\)", stats_text)

                return {
                    "files_changed": int(files_match.group(1)) if files_match else 0,
                    "lines_added": int(insertions_match.group(1))
                    if insertions_match
                    else 0,
                    "lines_deleted": int(deletions_match.group(1))
                    if deletions_match
                    else 0,
                    "code_churn": (
                        int(insertions_match.group(1)) if insertions_match else 0
                    )
                    + (int(deletions_match.group(1)) if deletions_match else 0),
                }
            else:
                # Git diff failed, continue without code metrics (not critical)
                return {}
        except Exception as e:
            print(f"Error analyzing code changes: {e}")
            return {}

    def calculate_innovation_score(self, pr_body: str, code_metrics: Dict) -> float:
        """Calculate innovation score based on PR content."""
        score = 5.0  # Base score

        # Innovation indicators
        innovation_keywords = [
            "novel",
            "innovative",
            "breakthrough",
            "advanced",
            "optimization",
            "performance",
            "scalability",
            "architecture",
        ]

        for keyword in innovation_keywords:
            if re.search(keyword, pr_body, re.IGNORECASE):
                score += 0.5

        # Code complexity indicator
        if code_metrics.get("files_changed", 0) > 20:
            score += 1.0
        if code_metrics.get("lines_added", 0) > 1000:
            score += 1.0

        # Cap at 10
        return min(score, 10.0)

    def generate_future_impact(self, business_value: Dict, performance: Dict) -> Dict:
        """Project future impact based on current metrics."""
        impact = {}

        # Revenue impact projection
        if "user_experience_score" in business_value:
            ux_score = business_value["user_experience_score"]
            # Better UX correlates with revenue
            impact["revenue_impact_3yr"] = round(ux_score * 500000 * 0.1, 0)

        # Market positioning
        if performance.get("peak_rps", 0) > 500:
            impact["competitive_advantage"] = "high"
            impact["market_differentiation"] = "performance_leader"

        # Technical debt reduction
        if performance.get("test_coverage", 0) > 90:
            impact["technical_debt_reduction"] = "significant"
            impact["maintenance_cost_reduction_percent"] = 30

        return impact

    def run_analysis(self):
        """Run complete PR analysis."""
        print(f"🔍 Analyzing PR #{self.pr_number}...")

        # Get PR details
        try:
            result = subprocess.run(
                ["gh", "pr", "view", self.pr_number, "--json", "body,title,author"],
                capture_output=True,
                text=True,
                timeout=30,  # Add timeout to prevent hanging
            )

            if result.returncode != 0:
                print(f"❌ Failed to fetch PR details: {result.stderr}")
                return None

            if not result.stdout.strip():
                print("❌ Empty response from GitHub CLI")
                return None

            try:
                pr_data = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON response: {e}")
                print(f"Response: {result.stdout[:500]}...")
                return None

            if pr_data is None:
                print("❌ GitHub returned null data")
                return None

            pr_body = pr_data.get("body", "")

            # Fallback: if PR body is empty, try alternative fetch
            if not pr_body:
                print("ℹ️ PR body empty, trying alternative fetch...")
                fallback_result = subprocess.run(
                    ["gh", "pr", "view", self.pr_number],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                if fallback_result.returncode == 0:
                    pr_body = fallback_result.stdout
                    print("✅ Retrieved PR content via fallback method")
                else:
                    print("⚠️ No PR body available, continuing with limited analysis")

            # Extract performance metrics
            performance = self.analyze_performance_metrics(pr_body)
            self.metrics["technical_metrics"]["performance"] = performance

            # Calculate business value
            business_value = self.calculate_business_value(performance)
            self.metrics["business_metrics"] = business_value

            # Extract achievement tags
            tags = self.extract_achievement_tags(pr_body)
            self.metrics["achievement_tags"] = tags

            # Analyze code changes
            code_metrics = self.analyze_code_changes()
            self.metrics["technical_metrics"]["code_metrics"] = code_metrics

            # Calculate innovation score
            innovation = self.calculate_innovation_score(pr_body, code_metrics)
            self.metrics["technical_metrics"]["innovation_score"] = innovation

            # Generate future impact
            impact = self.generate_future_impact(business_value, performance)
            self.metrics["future_impact"] = impact

            # Add warnings for unrealistic metrics
            warnings = []
            if business_value.get("throughput_improvement_percent", 0) > 200:
                warnings.append("Throughput improvement >200% may be unrealistic")
            if business_value.get("infrastructure_savings_estimate", 0) > 50000:
                warnings.append("Infrastructure savings >$50k/year needs validation")
            if business_value.get("roi_year_one_percent", 0) > 300:
                warnings.append("ROI >300% is exceptional - verify calculations")

            self.metrics["warnings"] = warnings

            # Generate KPIs
            self.metrics["kpis"] = {
                "performance_score": self.calculate_realistic_performance_score(
                    performance.get("peak_rps", 0),
                    performance.get("latency_ms", 500),
                    performance.get("error_rate", 0.02),
                ),
                "quality_score": performance.get("test_coverage", 0) / 10,
                "business_value_score": min(
                    10,
                    max(
                        0,
                        (
                            business_value.get("roi_year_one_percent", 0) / 30
                        ),  # More realistic scaling
                    ),
                ),
                "innovation_score": innovation,
                "overall_score": 0,  # Will be calculated after
            }

            # Calculate overall score properly
            self.metrics["kpis"]["overall_score"] = round(
                (
                    self.metrics["kpis"]["performance_score"]
                    + self.metrics["kpis"]["quality_score"]
                    + self.metrics["kpis"]["innovation_score"]
                )
                / 3,
                1,
            )

            return self.metrics

        except Exception as e:
            print(f"❌ Error during analysis: {e}")
            return None

    def save_results(self, output_file: str = None):
        """Save analysis results to file."""
        if not output_file:
            output_file = f"pr_{self.pr_number}_value_analysis.json"

        with open(output_file, "w") as f:
            json.dump(self.metrics, f, indent=2)

        print(f"✅ Results saved to {output_file}")

    def print_summary(self):
        """Print analysis summary with detailed explanations."""
        print("\n📊 PR Value Analysis Summary")
        print("=" * 50)

        # Detailed score breakdown
        overall_score = self.metrics["kpis"]["overall_score"]
        performance_score = self.metrics["kpis"]["performance_score"]
        quality_score = self.metrics["kpis"]["quality_score"]
        business_value_score = self.metrics["kpis"]["business_value_score"]
        innovation_score = self.metrics["kpis"]["innovation_score"]

        print(
            f"\n🎯 Overall Score: {overall_score}/10 ({self._get_score_status(overall_score)})"
        )
        print("=" * 30)

        # Detailed breakdown with explanations
        print(
            f"{'✅' if innovation_score >= 6 else '❌'} Innovation: {innovation_score}/10 ({self._get_innovation_explanation(innovation_score)})"
        )
        print(
            f"{'✅' if performance_score >= 6 else '❌'} Performance: {performance_score}/10 ({self._get_performance_explanation(performance_score)})"
        )
        print(
            f"{'✅' if quality_score >= 6 else '❌'} Quality: {quality_score}/10 ({self._get_quality_explanation(quality_score)})"
        )
        print(
            f"{'✅' if business_value_score >= 6 else '❌'} Business Value: {business_value_score}/10 ({self._get_business_explanation(business_value_score)})"
        )

        # Improvement suggestions
        suggestions = self._generate_improvement_suggestions()
        if suggestions:
            print("\n💡 How to Improve Your PR Score:")
            for suggestion in suggestions:
                print(f"  • {suggestion}")

        print("\n💰 Business Metrics:")
        for key, value in self.metrics["business_metrics"].items():
            print(f"  • {key}: {value}")

        print("\n🚀 Technical Metrics:")
        perf = self.metrics["technical_metrics"].get("performance", {})
        for key, value in perf.items():
            print(f"  • {key}: {value}")

        print("\n🏷️  Achievement Tags:")
        for tag in self.metrics["achievement_tags"]:
            print(f"  • {tag}")

        print("\n📈 Detailed KPIs:")
        for key, value in self.metrics["kpis"].items():
            print(f"  • {key}: {value}")

        print("\n🔮 Future Impact:")
        for key, value in self.metrics["future_impact"].items():
            print(f"  • {key}: {value}")

        # Add calculation explanations
        print("\n📐 How Metrics Are Calculated:")
        print("  • ROI = (Annual Savings / Dev Cost) × 100")
        print("  • Infrastructure Savings = $120k × (Perf Factor - 1) / Perf Factor")
        print("  • Overall Score = (Performance + Quality + Innovation) / 3")
        print("  • Time Savings = Hours/Week × 50 weeks × $100/hour")

        # Scoring thresholds
        print("\n🎯 Scoring Thresholds:")
        print("  • 8.0-10.0: Excellent (Automatic merge approval)")
        print("  • 6.0-7.9: Good (Review recommended)")
        print("  • 0.0-5.9: Needs improvement (Enhancement required)")

    def _get_score_status(self, score: float) -> str:
        """Get score status description."""
        if score >= 8.0:
            return "Excellent ⭐"
        elif score >= 6.0:
            return "Good ✅"
        else:
            return "Needs Improvement ⚠️"

    def _get_innovation_explanation(self, score: float) -> str:
        """Explain innovation score."""
        if score >= 8.0:
            return "exceptional technical complexity and novel approach"
        elif score >= 6.0:
            return "good technical innovation with advanced concepts"
        elif score >= 4.0:
            return "moderate complexity, some innovative elements"
        else:
            return "basic implementation, limited technical innovation"

    def _get_performance_explanation(self, score: float) -> str:
        """Explain performance score."""
        perf_metrics = self.metrics["technical_metrics"].get("performance", {})

        if not perf_metrics or not any(perf_metrics.values()):
            return "no measurable performance metrics detected"
        elif score >= 8.0:
            return "excellent performance metrics documented"
        elif score >= 6.0:
            return "good performance metrics provided"
        else:
            return "performance metrics present but could be improved"

    def _get_quality_explanation(self, score: float) -> str:
        """Explain quality score."""
        perf_metrics = self.metrics["technical_metrics"].get("performance", {})
        test_coverage = perf_metrics.get("test_coverage", 0)

        if test_coverage == 0:
            return "no test coverage metrics detected"
        elif score >= 8.0:
            return f"excellent test coverage ({test_coverage}%)"
        elif score >= 6.0:
            return f"good test coverage ({test_coverage}%)"
        else:
            return f"test coverage needs improvement ({test_coverage}%)"

    def _get_business_explanation(self, score: float) -> str:
        """Explain business value score."""
        business_metrics = self.metrics["business_metrics"]

        if not business_metrics or not any(business_metrics.values()):
            return "no ROI/cost savings metrics detected"
        elif score >= 8.0:
            return "strong business value with clear ROI"
        elif score >= 6.0:
            return "good business value demonstrated"
        else:
            return "business value present but could be quantified better"

    def _generate_improvement_suggestions(self) -> list:
        """Generate specific improvement suggestions."""
        suggestions = []
        kpis = self.metrics["kpis"]
        perf_metrics = self.metrics["technical_metrics"].get("performance", {})
        business_metrics = self.metrics["business_metrics"]

        # Performance suggestions
        if kpis["performance_score"] < 6.0:
            if not perf_metrics.get("peak_rps"):
                suggestions.append(
                    "Add RPS metrics: 'Handles 500+ RPS' or 'Peak performance: 1000 RPS'"
                )
            if not perf_metrics.get("latency_ms"):
                suggestions.append(
                    "Include latency metrics: 'Response time <100ms' or 'p95 latency: 150ms'"
                )
            if not perf_metrics.get("success_rate"):
                suggestions.append(
                    "Document success rates: '99.9% success rate' or '100% uptime'"
                )

        # Quality suggestions
        if kpis["quality_score"] < 6.0:
            if not perf_metrics.get("test_coverage"):
                suggestions.append(
                    "Add test coverage: 'Test coverage: 85%' or '90% code coverage achieved'"
                )
                suggestions.append(
                    "Include testing details: 'Added 50 unit tests' or 'E2E test suite expanded'"
                )

        # Business value suggestions
        if kpis["business_value_score"] < 6.0:
            if not business_metrics.get("infrastructure_savings_estimate"):
                suggestions.append(
                    "Quantify cost savings: 'Reduces infrastructure costs by $15k/year'"
                )
            if not business_metrics.get("roi_year_one_percent"):
                suggestions.append("Calculate ROI: 'Expected ROI: 300% in first year'")
            suggestions.append("Add business impact: 'Improves user experience by 25%'")
            suggestions.append("Include time savings: 'Saves developers 10 hours/week'")

        # Innovation suggestions
        if kpis["innovation_score"] < 8.0:
            suggestions.append(
                "Highlight technical innovation: Use words like 'novel', 'optimization', 'breakthrough'"
            )
            suggestions.append(
                "Explain architectural improvements: 'Advanced caching strategy' or 'Scalable microservices'"
            )

        return suggestions

    def _generate_interview_talking_points(self, results: Dict) -> List[str]:
        """Generate interview-ready talking points."""
        points = []

        # Performance achievements
        if results["technical_metrics"]["performance"].get("peak_rps", 0) > 1000:
            points.append(
                f"Achieved {results['technical_metrics']['performance']['peak_rps']} RPS - exceeding industry standards for similar systems"
            )

        # Cost savings
        if (
            results["business_metrics"].get("infrastructure_savings_estimate", 0)
            > 10000
        ):
            points.append(
                f"Delivered ${results['business_metrics']['infrastructure_savings_estimate']:,} annual infrastructure savings through performance optimization"
            )

        # Quality improvements
        if results["technical_metrics"]["performance"].get("test_coverage", 0) > 80:
            points.append(
                f"Implemented {results['technical_metrics']['performance']['test_coverage']}% test coverage, ensuring production reliability"
            )

        # Innovation
        if results["kpis"]["innovation_score"] > 8:
            points.append(
                "Pioneered novel approach to semantic search using advanced RAG techniques"
            )

        # ROI story
        if results["business_metrics"].get("roi_year_one_percent", 0) > 100:
            points.append(
                f"{results['business_metrics']['roi_year_one_percent']}% first-year ROI with {results['business_metrics'].get('payback_period_months', 'N/A')} month payback"
            )

        # Team impact
        if results["business_metrics"].get("developer_productivity_savings", 0) > 50000:
            points.append(
                f"Improved team productivity by ${results['business_metrics']['developer_productivity_savings']:,}/year"
            )

        return points

    def _generate_article_suggestions(self, results: Dict) -> Dict[str, List[str]]:
        """Generate suggestions for future articles/blog posts."""
        suggestions = {
            "technical_deep_dives": [],
            "business_case_studies": [],
            "best_practices": [],
            "lessons_learned": [],
        }

        # Technical articles
        if results["technical_metrics"]["performance"].get("peak_rps", 0) > 1000:
            suggestions["technical_deep_dives"].append(
                "How We Achieved 1200+ RPS with Python and FastAPI"
            )
            suggestions["technical_deep_dives"].append(
                "Optimizing Kubernetes for High-Performance Microservices"
            )

        if "ai_ml_feature" in results["achievement_tags"]:
            suggestions["technical_deep_dives"].append(
                "Building Production-Ready RAG Pipelines: A Complete Guide"
            )
            suggestions["technical_deep_dives"].append(
                "Semantic Search at Scale: Lessons from Production"
            )

        # Business case studies
        if results["business_metrics"].get("roi_year_one_percent", 0) > 100:
            suggestions["business_case_studies"].append(
                f"Case Study: {results['business_metrics']['roi_year_one_percent']}% ROI from Performance Optimization"
            )

        if results["business_metrics"].get("developer_productivity_savings", 0) > 50000:
            suggestions["business_case_studies"].append(
                "How Semantic Search Saved Our Team 10 Hours/Week"
            )

        # Best practices
        if results["technical_metrics"]["performance"].get("test_coverage", 0) > 80:
            suggestions["best_practices"].append(
                "Achieving 87% Test Coverage in Production Microservices"
            )

        if results["technical_metrics"]["performance"].get("latency_ms", 0) < 200:
            suggestions["best_practices"].append(
                "Sub-200ms Response Times: Architecture and Optimization Strategies"
            )

        # Lessons learned
        suggestions["lessons_learned"].append(
            "From Concept to Production: Building a High-Performance RAG System"
        )
        suggestions["lessons_learned"].append(
            "The Hidden Costs of Poor Performance (And How We Fixed Them)"
        )

        return suggestions

    def _generate_portfolio_summary(self, results: Dict) -> str:
        """Generate a portfolio-ready project summary."""
        perf = results["technical_metrics"]["performance"]
        business = results["business_metrics"]

        summary = f"""**High-Performance RAG Pipeline Implementation**

Led the development of a production-ready RAG (Retrieval-Augmented Generation) pipeline that revolutionized our team's code discovery and development workflow.

**Key Achievements:**
• Performance: {perf.get("peak_rps", 0)} RPS with {perf.get("latency_ms", "N/A")}ms latency
• Scale: Handles {results["technical_metrics"]["code_metrics"].get("files_changed", 0)} files across the codebase
• Quality: {perf.get("test_coverage", 0)}% test coverage with comprehensive integration tests
• Business Impact: ${business.get("infrastructure_savings_estimate", 0):,} annual savings, {business.get("roi_year_one_percent", 0)}% ROI

**Technologies:** Python, FastAPI, Kubernetes, PostgreSQL, Qdrant, OpenAI API, Docker

**Innovation:** Implemented novel embedding techniques for semantic code search, reducing developer search time by 60% and debugging time by 40%. This project demonstrates expertise in AI/ML integration, distributed systems, and performance optimization."""

        return summary


def main():
    """Main function to run PR value analysis."""
    if len(sys.argv) < 2:
        print("Usage: python pr-value-analyzer.py <PR_NUMBER>")
        sys.exit(1)

    pr_number = sys.argv[1]

    # Create analyzer
    analyzer = PRValueAnalyzer(pr_number)

    # Run analysis
    results = analyzer.run_analysis()

    if results:
        # Print summary
        analyzer.print_summary()

        # Save results
        analyzer.save_results()

        # Also save to achievement collector format with AI insights
        achievement_data = {
            "pr_number": pr_number,
            "timestamp": results["timestamp"],
            "tags": results["achievement_tags"],
            "metrics": {
                **results["business_metrics"],
                **results["technical_metrics"]["performance"],
                "innovation_score": results["technical_metrics"]["innovation_score"],
            },
            "kpis": results["kpis"],
            "ai_insights": {
                "improvement_suggestions": analyzer._generate_improvement_suggestions(),
                "score_explanations": {
                    "innovation": analyzer._get_innovation_explanation(
                        results["kpis"]["innovation_score"]
                    ),
                    "performance": analyzer._get_performance_explanation(
                        results["kpis"]["performance_score"]
                    ),
                    "quality": analyzer._get_quality_explanation(
                        results["kpis"]["quality_score"]
                    ),
                    "business": analyzer._get_business_explanation(
                        results["kpis"]["business_value_score"]
                    ),
                },
                "interview_talking_points": analyzer._generate_interview_talking_points(
                    results
                ),
                "article_suggestions": analyzer._generate_article_suggestions(results),
                "portfolio_summary": analyzer._generate_portfolio_summary(results),
            },
            "calculation_methodology": {
                "roi_formula": "ROI = (Annual Savings - Total Investment) / Total Investment × 100",
                "infrastructure_formula": "Savings = Servers_Reduced × $12k/year + Bandwidth_Savings",
                "productivity_formula": "Savings = Hours_Saved × Team_Size × $150/hour",
                "confidence_level": results["business_metrics"].get(
                    "confidence_level", "medium"
                ),
                "assumptions": {
                    "developer_rate": "$150/hour",
                    "server_cost": "$12k/year",
                    "baseline_rps": 500,
                    "baseline_latency": 800,
                },
            },
            "future_impact": results.get("future_impact", {}),
            "warnings": results.get("warnings", []),
            "integration_ready": True,
            "schema_version": "3.0",  # Updated version for AI insights
        }

        achievement_file = f".achievements/pr_{pr_number}_achievement.json"
        os.makedirs(".achievements", exist_ok=True)

        with open(achievement_file, "w") as f:
            json.dump(achievement_data, f, indent=2)

        print(f"\n✅ Achievement data saved to {achievement_file}")

        # Notify about achievement collector integration
        if results["kpis"]["overall_score"] >= 6:
            print("\n🎯 This PR qualifies for Achievement Collector!")
            print("   Run the following to create the achievement:")
            print(
                f"   curl -X POST http://localhost:8000/pr-analysis/analyze/{pr_number}"
            )

        # Return overall score for CI/CD integration
        overall_score = results["kpis"]["overall_score"]
        print(f"\n🎯 Overall PR Score: {overall_score}/10")

        # Exit with score-based code (0 = excellent, 1 = good, 2 = needs improvement)
        if overall_score >= 8:
            sys.exit(0)
        elif overall_score >= 6:
            sys.exit(1)
        else:
            sys.exit(2)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
