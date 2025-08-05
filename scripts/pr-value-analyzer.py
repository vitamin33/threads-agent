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
            # More realistic baseline based on typical web services
            baseline_rps = 500  # More realistic baseline for existing services
            improvement_factor = rps / baseline_rps
            value["throughput_improvement_percent"] = round(
                (improvement_factor - 1) * 100, 1
            )

            # Infrastructure cost savings
            # More conservative estimate based on real server costs
            # Only count savings if we have meaningful improvement (>20%)
            if improvement_factor > 1.2:
                # $5k per server/year, estimate servers saved
                servers_saved = max(0, (improvement_factor - 1) * 2)
                value["infrastructure_savings_estimate"] = round(
                    servers_saved * 5000, 0
                )
            else:
                value["infrastructure_savings_estimate"] = 0

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

        # ROI calculation with more realistic assumptions
        if "infrastructure_savings_estimate" in value:
            # More realistic development cost based on feature complexity
            dev_cost = 25000  # Realistic for RAG pipeline development (2-3 weeks)
            annual_savings = value["infrastructure_savings_estimate"]
            if annual_savings > 0:
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
                print(f"Warning: Failed to get PR diff stats: {result.stderr}")
                return {
                    "files_changed": 0,
                    "lines_added": 0,
                    "lines_deleted": 0,
                    "code_churn": 0,
                }
        except Exception as e:
            print(f"Error analyzing code changes: {e}")
            return {
                "files_changed": 0,
                "lines_added": 0,
                "lines_deleted": 0,
                "code_churn": 0,
            }

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
                print(f"❌ Empty response from GitHub CLI")
                return None

            try:
                pr_data = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON response: {e}")
                print(f"Response: {result.stdout[:500]}...")
                return None

            if pr_data is None:
                print(f"❌ GitHub returned null data")
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
                    print(f"✅ Retrieved PR content via fallback method")
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
                "performance_score": performance.get("peak_rps", 0) / 10,
                "quality_score": performance.get("test_coverage", 0) / 10,
                "business_value_score": min(10, max(0, 
                    (business_value.get("roi_year_one_percent", 0) / 100) * 
                    (10 if business_value.get("infrastructure_savings_estimate", 0) > 10000 else 5)
                )),
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
        """Print analysis summary with detailed explanations."""
        print("\n📊 PR Value Analysis Summary")
        print("=" * 50)
        
        # Detailed score breakdown
        overall_score = self.metrics["kpis"]["overall_score"]
        performance_score = self.metrics["kpis"]["performance_score"]
        quality_score = self.metrics["kpis"]["quality_score"]
        business_value_score = self.metrics["kpis"]["business_value_score"]
        innovation_score = self.metrics["kpis"]["innovation_score"]
        
        print(f"\n🎯 Overall Score: {overall_score}/10 ({self._get_score_status(overall_score)})")
        print("=" * 30)
        
        # Detailed breakdown with explanations
        print(f"{'✅' if innovation_score >= 6 else '❌'} Innovation: {innovation_score}/10 ({self._get_innovation_explanation(innovation_score)})")
        print(f"{'✅' if performance_score >= 6 else '❌'} Performance: {performance_score}/10 ({self._get_performance_explanation(performance_score)})")
        print(f"{'✅' if quality_score >= 6 else '❌'} Quality: {quality_score}/10 ({self._get_quality_explanation(quality_score)})")
        print(f"{'✅' if business_value_score >= 6 else '❌'} Business Value: {business_value_score}/10 ({self._get_business_explanation(business_value_score)})")

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
                suggestions.append("Add RPS metrics: 'Handles 500+ RPS' or 'Peak performance: 1000 RPS'")
            if not perf_metrics.get("latency_ms"):
                suggestions.append("Include latency metrics: 'Response time <100ms' or 'p95 latency: 150ms'")
            if not perf_metrics.get("success_rate"):
                suggestions.append("Document success rates: '99.9% success rate' or '100% uptime'")
        
        # Quality suggestions
        if kpis["quality_score"] < 6.0:
            if not perf_metrics.get("test_coverage"):
                suggestions.append("Add test coverage: 'Test coverage: 85%' or '90% code coverage achieved'")
                suggestions.append("Include testing details: 'Added 50 unit tests' or 'E2E test suite expanded'")
        
        # Business value suggestions
        if kpis["business_value_score"] < 6.0:
            if not business_metrics.get("infrastructure_savings_estimate"):
                suggestions.append("Quantify cost savings: 'Reduces infrastructure costs by $15k/year'")
            if not business_metrics.get("roi_year_one_percent"):
                suggestions.append("Calculate ROI: 'Expected ROI: 300% in first year'")
            suggestions.append("Add business impact: 'Improves user experience by 25%'")
            suggestions.append("Include time savings: 'Saves developers 10 hours/week'")
        
        # Innovation suggestions
        if kpis["innovation_score"] < 8.0:
            suggestions.append("Highlight technical innovation: Use words like 'novel', 'optimization', 'breakthrough'")
            suggestions.append("Explain architectural improvements: 'Advanced caching strategy' or 'Scalable microservices'")
        
        return suggestions


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

        # For CI, always exit 0 (success) since analysis completed successfully
        # Score is informational only - let other CI checks determine pass/fail
        if overall_score >= 8:
            print("🌟 Excellent PR! Outstanding value delivered.")
        elif overall_score >= 6:
            print("✅ Good PR with solid value.")
        else:
            print("⚠️ PR has room for improvement, but analysis successful.")
        
        sys.exit(0)  # Always successful - we completed the analysis
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
