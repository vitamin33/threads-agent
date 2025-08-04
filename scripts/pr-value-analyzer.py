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
        """Calculate business value based on performance metrics."""
        value = {}

        # Calculate cost savings based on performance improvements
        if "peak_rps" in performance_metrics:
            rps = performance_metrics["peak_rps"]
            # Estimate cost savings based on throughput improvement
            baseline_rps = 100  # Assumed baseline
            improvement_factor = rps / baseline_rps
            value["throughput_improvement_percent"] = round(
                (improvement_factor - 1) * 100, 1
            )

            # Infrastructure cost savings
            # Higher RPS means fewer servers needed
            value["infrastructure_savings_estimate"] = round(
                120000 * (improvement_factor - 1) / improvement_factor, 0
            )

        if "latency_ms" in performance_metrics:
            latency = performance_metrics["latency_ms"]
            # User experience improvement based on latency
            if latency < 100:
                value["user_experience_score"] = 10
            elif latency < 200:
                value["user_experience_score"] = 9
            elif latency < 500:
                value["user_experience_score"] = 8
            else:
                value["user_experience_score"] = 7

        # ROI calculation
        if "infrastructure_savings_estimate" in value:
            # Assume 150K development cost
            dev_cost = 150000
            annual_savings = value["infrastructure_savings_estimate"]
            value["roi_year_one_percent"] = round((annual_savings / dev_cost) * 100, 0)
            value["payback_period_months"] = round(12 * dev_cost / annual_savings, 1)

        return value

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
            # Get PR diff statistics
            result = subprocess.run(
                ["gh", "pr", "diff", self.pr_number, "--stat"],
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
            )

            if result.returncode != 0:
                print(f"❌ Failed to fetch PR details: {result.stderr}")
                return None

            pr_data = json.loads(result.stdout)
            pr_body = pr_data.get("body", "")

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

            # Generate KPIs
            self.metrics["kpis"] = {
                "performance_score": performance.get("peak_rps", 0) / 10,
                "quality_score": performance.get("test_coverage", 0) / 10,
                "business_value_score": business_value.get("roi_year_one_percent", 0)
                / 30,
                "innovation_score": innovation,
                "overall_score": round(
                    (
                        performance.get("peak_rps", 0) / 100
                        + performance.get("test_coverage", 0) / 10
                        + innovation
                    )
                    / 3,
                    1,
                ),
            }

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
        """Print analysis summary."""
        print("\n📊 PR Value Analysis Summary")
        print("=" * 50)

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

        print("\n📈 KPIs:")
        for key, value in self.metrics["kpis"].items():
            print(f"  • {key}: {value}")

        print("\n🔮 Future Impact:")
        for key, value in self.metrics["future_impact"].items():
            print(f"  • {key}: {value}")


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

        # Also save to achievement collector format
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
            "integration_ready": True,
            "schema_version": "2.0",
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
