#!/usr/bin/env python3
"""
Ultimate PR Value Analyzer - Comprehensive metrics with unified adaptive scoring

This analyzer combines:
1. ALL comprehensive metrics and calculations from the original analyzer
2. Detailed metric explanations and AI insights
3. Adaptive scoring that evaluates PRs based on what they actually deliver
4. Fair thresholds where PRs can succeed by excelling in relevant areas
"""

import json
import subprocess
import re
from datetime import datetime
from typing import Dict, List, Any
import os
import sys
import math


class UltimatePRValueAnalyzer:
    """The ultimate PR analyzer with comprehensive metrics and fair scoring."""

    def __init__(self, pr_number: str):
        self.pr_number = pr_number
        self.metrics = {
            "pr_number": pr_number,
            "timestamp": datetime.now().isoformat(),
            "value_categories": {},  # What types of value this PR provides
            "business_metrics": {},
            "technical_metrics": {},
            "achievement_tags": [],
            "kpis": {},
            "future_impact": {},
            "active_metrics": {},  # Which metrics are relevant
        }

    def detect_pr_value_categories(self, pr_data: Dict) -> Dict[str, float]:
        """
        Detect what types of value this PR provides.
        Returns confidence scores for each category.
        """
        title = pr_data.get("title", "").lower()
        body = pr_data.get("body", "").lower()
        files = pr_data.get("files", [])

        categories = {
            "performance": 0.0,
            "business": 0.0,
            "quality": 0.0,
            "documentation": 0.0,
            "infrastructure": 0.0,
            "security": 0.0,
            "user_experience": 0.0,
            "technical_debt": 0.0,
            "innovation": 0.0,
        }

        # Performance indicators
        perf_keywords = [
            "performance",
            "optimization",
            "speed",
            "latency",
            "rps",
            "throughput",
            "cache",
            "async",
        ]
        perf_score = sum(1 for kw in perf_keywords if kw in title + body) * 0.2
        if re.search(r"\d+\s*rps|\d+ms\s*latency", body, re.IGNORECASE):
            perf_score += 0.5
        categories["performance"] = min(perf_score, 1.0)

        # Business value indicators
        business_keywords = [
            "roi",
            "revenue",
            "cost",
            "savings",
            "customer",
            "user growth",
            "conversion",
        ]
        business_score = sum(1 for kw in business_keywords if kw in title + body) * 0.2
        if re.search(r"\$\d+|%\s*improvement|%\s*increase", body):
            business_score += 0.4
        categories["business"] = min(business_score, 1.0)

        # Quality indicators
        quality_keywords = [
            "test",
            "coverage",
            "bug",
            "fix",
            "error",
            "crash",
            "stability",
        ]
        quality_score = sum(1 for kw in quality_keywords if kw in title + body) * 0.15
        test_files = [f for f in files if "test" in f.get("path", "").lower()]
        if test_files:
            quality_score += 0.3 + (len(test_files) * 0.1)
        categories["quality"] = min(quality_score, 1.0)

        # Documentation indicators
        doc_keywords = [
            "documentation",
            "readme",
            "guide",
            "tutorial",
            "example",
            "api docs",
        ]
        doc_score = sum(1 for kw in doc_keywords if kw in title + body) * 0.2
        doc_files = [f for f in files if ".md" in f.get("path", "").lower()]
        if doc_files:
            doc_score += 0.4 + (len(doc_files) * 0.1)
        categories["documentation"] = min(doc_score, 1.0)

        # Infrastructure indicators
        infra_keywords = [
            "kubernetes",
            "k8s",
            "docker",
            "ci",
            "deployment",
            "helm",
            "airflow",
        ]
        infra_score = sum(1 for kw in infra_keywords if kw in title + body) * 0.2
        if any(
            path in str(files) for path in [".github/", "dockerfile", ".yaml", ".yml"]
        ):
            infra_score += 0.4
        categories["infrastructure"] = min(infra_score, 1.0)

        # Innovation indicators (AI/ML, novel approaches)
        innovation_keywords = [
            "novel",
            "new",
            "innovative",
            "ai",
            "ml",
            "rag",
            "llm",
            "airflow",
            "orchestration",
        ]
        innovation_score = (
            sum(1 for kw in innovation_keywords if kw in title + body) * 0.2
        )
        if pr_data.get("additions", 0) > 500:
            innovation_score += 0.2
        categories["innovation"] = min(innovation_score, 1.0)

        return categories

    def analyze_performance_metrics(self, pr_body: str) -> Dict[str, Any]:
        """Extract ALL performance metrics from PR body (keeping original logic)."""
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
        """Calculate business value (keeping ALL original calculations)."""
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
            baseline_servers = math.ceil(baseline_rps / 200)
            current_servers = math.ceil(rps / (200 * performance_factor))
            servers_saved = max(0, baseline_servers - current_servers)

            server_savings = servers_saved * 12000  # $12k per server/year

            # Additional savings
            bandwidth_savings = 0
            if latency_improvement > 1.2:  # 20% improvement
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
            team_size = 10
            search_time_saved_percent = min(50, throughput_improvement * 20)
            debug_time_saved_percent = min(40, latency_improvement * 15)

            hours_saved_per_week = (8 * search_time_saved_percent / 100) + (
                10 * debug_time_saved_percent / 100
            )
            annual_hours_saved = hours_saved_per_week * 48 * team_size

            value["developer_productivity_savings"] = round(
                annual_hours_saved * 150, 0
            )  # $150/hour
            value["productivity_hours_saved"] = round(annual_hours_saved, 0)

        # Quality impact
        if test_coverage > 0:
            bug_reduction_percent = min(50, test_coverage * 0.5)
            bugs_prevented_annually = round(20 * 12 * bug_reduction_percent / 100, 0)

            value["quality_improvement_savings"] = bugs_prevented_annually * 5000
            value["bugs_prevented_annually"] = bugs_prevented_annually

        # Total savings and ROI calculation
        total_savings = (
            value.get("infrastructure_savings_estimate", 0)
            + value.get("developer_productivity_savings", 0)
            + value.get("quality_improvement_savings", 0)
        )

        if total_savings > 0:
            # Development cost with overhead
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

    def calculate_unified_score(
        self,
        categories: Dict[str, float],
        performance: Dict[str, Any],
        business_value: Dict[str, Any],
        code_metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Calculate scores with unified approach - PRs succeed by excelling in ANY area.
        """
        scores = {}

        # Performance score
        perf_score = 0
        if performance.get("peak_rps", 0) > 0:
            rps = performance["peak_rps"]
            if rps >= 10000:
                perf_score = 10
            elif rps >= 5000:
                perf_score = 9
            elif rps >= 2000:
                perf_score = 8
            elif rps >= 1000:
                perf_score = 7
            elif rps >= 500:
                perf_score = 6
            else:
                perf_score = max(1, rps / 100)

        if performance.get("latency_ms", 0) > 0:
            latency = performance["latency_ms"]
            if latency <= 50:
                latency_score = 10
            elif latency <= 100:
                latency_score = 9
            elif latency <= 200:
                latency_score = 8
            elif latency <= 500:
                latency_score = 6
            else:
                latency_score = 4
            perf_score = max(perf_score, latency_score)

        scores["performance_score"] = perf_score

        # Quality score
        quality_score = performance.get("test_coverage", 0) / 10
        scores["quality_score"] = quality_score

        # Business value score
        roi = business_value.get("roi_year_one_percent", 0)
        business_score = min(10, roi / 30) if roi > 0 else 0
        scores["business_value_score"] = business_score

        # Innovation score
        innovation_score = self.calculate_innovation_score(
            self.metrics.get("pr_body", ""), code_metrics
        )
        scores["innovation_score"] = innovation_score

        # UNIFIED SCORING APPROACH
        # Take the best score from all categories
        category_scores = []

        # Add category-specific bonus based on PR focus
        if categories.get("performance", 0) > 0.5:
            category_scores.append(perf_score)
        if categories.get("quality", 0) > 0.5:
            category_scores.append(quality_score)
        if categories.get("business", 0) > 0.5:
            category_scores.append(business_score)
        if categories.get("innovation", 0) > 0.5:
            category_scores.append(innovation_score)

        # Documentation bonus
        if categories.get("documentation", 0) > 0.5:
            doc_score = 7 + (categories["documentation"] * 3)
            category_scores.append(doc_score)

        # Infrastructure bonus
        if categories.get("infrastructure", 0) > 0.5:
            infra_score = 6 + (categories["infrastructure"] * 4)
            category_scores.append(infra_score)

        # Calculate overall - best of approach with small multi-category bonus
        if category_scores:
            best_score = max(category_scores)
            multi_bonus = min(1, len([s for s in category_scores if s > 6]) * 0.3)
            overall = min(10, best_score + multi_bonus)
        else:
            # Fallback to average
            overall = (
                perf_score + quality_score + business_score + innovation_score
            ) / 4

        scores["overall_score"] = round(overall, 1)

        return scores

    def calculate_innovation_score(self, pr_body: str, code_metrics: Dict) -> float:
        """Calculate innovation score (keeping original logic)."""
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
            "airflow",
            "orchestration",
            "rag",
            "ai",
            "ml",
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

    def extract_achievement_tags(self, pr_body: str) -> List[str]:
        """Extract achievement tags (keeping ALL original tags)."""
        tags = []

        # Performance achievements
        if re.search(r"\d+\.?\d*\s*RPS", pr_body, re.IGNORECASE):
            tags.append("high_performance_implementation")

        # Cost optimization
        if re.search(r"cost.*reduction|savings", pr_body, re.IGNORECASE):
            tags.append("cost_optimization")

        # Kubernetes/DevOps
        if re.search(r"kubernetes|k8s|helm|airflow", pr_body, re.IGNORECASE):
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
        """Analyze code changes (keeping original implementation)."""
        try:
            # Get PR diff statistics
            base_result = subprocess.run(
                ["gh", "pr", "view", self.pr_number, "--json", "baseRefName"],
                capture_output=True,
                text=True,
            )

            if base_result.returncode == 0:
                base_data = json.loads(base_result.stdout)
                base_branch = base_data.get("baseRefName", "main")

                result = subprocess.run(
                    ["git", "diff", "--stat", f"origin/{base_branch}"],
                    capture_output=True,
                    text=True,
                )

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
                return {}
        except Exception as e:
            print(f"Error analyzing code changes: {e}")
            return {}

    def generate_future_impact(self, business_value: Dict, performance: Dict) -> Dict:
        """Project future impact (keeping original implementation)."""
        impact = {}

        # Revenue impact projection
        if "user_experience_score" in business_value:
            ux_score = business_value["user_experience_score"]
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
        """Run the complete analysis with all metrics."""
        print(f"🔍 Analyzing PR #{self.pr_number} with comprehensive metrics...")

        try:
            # Get PR details
            result = subprocess.run(
                [
                    "gh",
                    "pr",
                    "view",
                    self.pr_number,
                    "--json",
                    "body,title,author,files,additions,deletions",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                print(f"❌ Failed to fetch PR details: {result.stderr}")
                return None

            pr_data = json.loads(result.stdout)
            pr_body = pr_data.get("body", "")
            self.metrics["pr_body"] = pr_body

            # Detect value categories
            categories = self.detect_pr_value_categories(pr_data)
            self.metrics["value_categories"] = categories

            # Extract ALL performance metrics
            performance = self.analyze_performance_metrics(pr_body)
            self.metrics["technical_metrics"]["performance"] = performance

            # Calculate ALL business value metrics
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

            # Generate unified KPIs
            kpis = self.calculate_unified_score(
                categories, performance, business_value, code_metrics
            )
            self.metrics["kpis"] = kpis

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
        """Print comprehensive analysis summary."""
        print("\n📊 PR Value Analysis Summary")
        print("=" * 50)

        # Overall score with unified approach
        overall_score = self.metrics["kpis"]["overall_score"]
        print(
            f"\n🎯 Overall Score: {overall_score}/10 ({self._get_score_status(overall_score)})"
        )
        print("=" * 30)

        # Value categories detected
        print("\n📋 PR Value Categories (Adaptive Scoring):")
        categories = self.metrics["value_categories"]
        active_cats = [(cat, score) for cat, score in categories.items() if score > 0.3]
        if active_cats:
            for cat, confidence in sorted(
                active_cats, key=lambda x: x[1], reverse=True
            ):
                print(f"  • {cat}: {confidence:.0%} confidence")

        # Individual scores
        kpis = self.metrics["kpis"]
        print("\n📈 Score Components:")
        print(
            f"  {'✅' if kpis['innovation_score'] >= 6 else '❌'} Innovation: {kpis['innovation_score']}/10"
        )
        print(
            f"  {'✅' if kpis['performance_score'] >= 6 else '❌'} Performance: {kpis['performance_score']}/10"
        )
        print(
            f"  {'✅' if kpis['quality_score'] >= 6 else '❌'} Quality: {kpis['quality_score']}/10"
        )
        print(
            f"  {'✅' if kpis['business_value_score'] >= 6 else '❌'} Business Value: {kpis['business_value_score']}/10"
        )

        # Business metrics
        if self.metrics["business_metrics"]:
            print("\n💰 Business Metrics:")
            for key, value in self.metrics["business_metrics"].items():
                print(f"  • {key}: {value}")

        # Technical metrics
        perf = self.metrics["technical_metrics"].get("performance", {})
        if perf:
            print("\n🚀 Technical Metrics:")
            for key, value in perf.items():
                print(f"  • {key}: {value}")

        # Achievement tags
        if self.metrics["achievement_tags"]:
            print("\n🏷️  Achievement Tags:")
            for tag in self.metrics["achievement_tags"]:
                print(f"  • {tag}")

        # Future impact
        if self.metrics["future_impact"]:
            print("\n🔮 Future Impact:")
            for key, value in self.metrics["future_impact"].items():
                print(f"  • {key}: {value}")

        # Unified scoring explanation
        print("\n📌 Unified Scoring Approach:")
        print("  • PRs are evaluated based on the value they actually deliver")
        print("  • Excel in ANY category to achieve a high score")
        print("  • Different PR types have equal opportunity to succeed")

        # Thresholds
        print("\n🎯 Scoring Thresholds:")
        print("  • 7.0-10.0: Excellent (Any PR type can achieve this)")
        print("  • 5.0-6.9: Good (Solid contribution)")
        print("  • 0.0-4.9: Needs improvement")

    def _get_score_status(self, score: float) -> str:
        """Get score status description."""
        if score >= 7.0:
            return "Excellent ⭐"
        elif score >= 5.0:
            return "Good ✅"
        else:
            return "Needs Improvement ⚠️"

    def _generate_improvement_suggestions(self) -> List[str]:
        """Generate improvement suggestions based on detected categories."""
        suggestions = []
        kpis = self.metrics["kpis"]
        categories = self.metrics["value_categories"]

        # Performance suggestions
        if categories.get("performance", 0) > 0.3 and kpis["performance_score"] < 6:
            suggestions.append("Add specific performance metrics (RPS, latency)")

        # Quality suggestions
        if categories.get("quality", 0) > 0.3 and kpis["quality_score"] < 6:
            suggestions.append("Include test coverage percentage")

        # Business suggestions
        if categories.get("business", 0) > 0.3 and kpis["business_value_score"] < 6:
            suggestions.append("Quantify business impact (ROI, cost savings)")

        # Documentation suggestions
        if categories.get("documentation", 0) > 0.3:
            suggestions.append(
                "This is a documentation PR - metrics not required for high score"
            )

        return suggestions

    def _generate_metric_explanations_dict(self) -> Dict[str, Dict[str, Any]]:
        """Generate comprehensive metric explanations for all metrics."""
        return {
            "business_metrics": {
                "throughput_improvement_percent": {
                    "formula": "((current_rps / baseline_rps) - 1) × 100%",
                    "meaning": "How much faster the system processes requests vs baseline",
                    "baseline": "500 RPS (typical microservice performance)",
                },
                "infrastructure_savings_estimate": {
                    "formula": "servers_reduced × $12k/year + bandwidth_savings",
                    "meaning": "Annual cost reduction from needing fewer servers",
                    "calculation": "Based on reduced server needs from performance gains",
                },
                "servers_reduced": {
                    "formula": "max(0, baseline_servers - current_servers)",
                    "meaning": "Number of servers eliminated due to performance gains",
                    "baseline_servers": "ceil(baseline_rps / 200)",
                },
                "developer_productivity_savings": {
                    "formula": "hours_saved × team_size × $150/hour",
                    "meaning": "Cost savings from developers working more efficiently",
                    "hourly_rate": "$150/hour (industry standard)",
                },
                "productivity_hours_saved": {
                    "formula": "hours_saved_per_week × 48 weeks × team_size",
                    "meaning": "Total developer hours saved annually",
                },
                "quality_improvement_savings": {
                    "formula": "bugs_prevented × $5k/bug",
                    "meaning": "Cost avoided by catching bugs before production",
                    "bug_cost": "$5k average cost to fix bug in production",
                },
                "bugs_prevented_annually": {
                    "formula": "20 bugs/month × 12 months × bug_reduction_percent",
                    "meaning": "Number of bugs prevented through quality improvements",
                },
                "total_annual_savings": {
                    "formula": "infrastructure + productivity + quality savings",
                    "meaning": "Total projected annual cost reduction",
                },
                "risk_adjusted_savings": {
                    "formula": "total_savings × confidence_factor",
                    "meaning": "Conservative estimate accounting for uncertainty",
                    "confidence_factors": {"high": 0.9, "medium": 0.8, "low": 0.7},
                },
                "total_investment": {
                    "formula": "dev_cost + qa_cost + deployment_cost + maintenance",
                    "meaning": "Total cost to implement this PR",
                    "breakdown": "320 hours × $150/hour × 1.65 overhead factor",
                },
                "roi_year_one_percent": {
                    "formula": "((risk_adjusted_savings - investment) / investment) × 100%",
                    "meaning": "Return on investment in the first year",
                    "interpretation": ">100% means positive ROI within first year",
                },
                "roi_three_year_percent": {
                    "formula": "(risk_adjusted_savings × 3 / investment) × 100%",
                    "meaning": "Return on investment over three years",
                },
                "payback_period_months": {
                    "formula": "investment / (annual_savings / 12)",
                    "meaning": "Time to recover the initial investment",
                },
                "user_experience_score": {
                    "formula": "Based on response latency",
                    "scale": {
                        "10": "<100ms (Exceptional)",
                        "9": "<200ms (Excellent)",
                        "8": "<500ms (Good)",
                        "7": ">500ms (Needs improvement)",
                    },
                },
                "confidence_level": {
                    "meaning": "Reliability of estimates based on performance factor",
                    "levels": {
                        "high": "Performance factor < 1.5x (realistic)",
                        "medium": "Performance factor 1.5-3x (optimistic)",
                        "low": "Performance factor > 3x (very optimistic)",
                    },
                },
            },
            "performance_metrics": {
                "peak_rps": {
                    "meaning": "Maximum requests the system can handle per second",
                    "industry_standards": {
                        "low": "<100 RPS",
                        "medium": "100-500 RPS",
                        "high": "500-1000 RPS",
                        "very_high": ">1000 RPS",
                    },
                },
                "latency_ms": {
                    "meaning": "Average time to process a request",
                    "user_perception": {
                        "instant": "<100ms",
                        "fast": "100-300ms",
                        "acceptable": "300-1000ms",
                        "slow": ">1000ms",
                    },
                },
                "test_coverage": {
                    "meaning": "Percentage of code covered by tests",
                    "quality_standards": {
                        "excellent": ">80%",
                        "good": "60-80%",
                        "fair": "40-60%",
                        "poor": "<40%",
                    },
                },
                "success_rate": {
                    "meaning": "Percentage of successful requests",
                    "reliability_levels": {
                        "excellent": ">99.9%",
                        "good": "99-99.9%",
                        "acceptable": "95-99%",
                        "poor": "<95%",
                    },
                },
            },
            "kpi_scores": {
                "performance_score": {
                    "formula": "Logarithmic scale based on RPS and latency",
                    "scale": {
                        "10": ">10,000 RPS or <50ms latency",
                        "9": ">5,000 RPS or <100ms latency",
                        "8": ">2,000 RPS or <200ms latency",
                        "7": ">1,000 RPS or <500ms latency",
                        "6": ">500 RPS",
                        "5": ">200 RPS",
                    },
                },
                "quality_score": {
                    "formula": "test_coverage / 10",
                    "meaning": "Code quality based on test coverage",
                },
                "business_value_score": {
                    "formula": "min(10, roi_percent / 30)",
                    "meaning": "Financial impact relative to investment",
                    "scale": {
                        "10": "ROI >300%",
                        "8": "ROI >240%",
                        "6": "ROI >180%",
                        "4": "ROI >120%",
                        "2": "ROI >60%",
                    },
                },
                "innovation_score": {
                    "criteria": [
                        "New patterns/architectures introduced",
                        "AI/ML features implemented",
                        "Novel solutions to complex problems",
                        "Industry best practices adopted",
                        "Complex integrations completed",
                    ]
                },
                "overall_score": {
                    "formula": "Best category score + multi-category bonus",
                    "meaning": "Unified score based on strongest value contribution",
                    "approach": "PRs succeed by excelling in ANY relevant area",
                },
            },
        }


def main():
    """Main function to run ultimate PR value analysis."""
    if len(sys.argv) < 2:
        print("Usage: python pr-value-analyzer-ultimate.py <PR_NUMBER>")
        sys.exit(1)

    pr_number = sys.argv[1]

    # Create analyzer
    analyzer = UltimatePRValueAnalyzer(pr_number)

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
            "value_categories": results["value_categories"],
            "metric_explanations": analyzer._generate_metric_explanations_dict(),
            "future_impact": results.get("future_impact", {}),
            "warnings": results.get("warnings", []),
            "schema_version": "3.1",
        }

        achievement_file = f".achievements/pr_{pr_number}_achievement.json"
        os.makedirs(".achievements", exist_ok=True)

        with open(achievement_file, "w") as f:
            json.dump(achievement_data, f, indent=2)

        print(f"\n✅ Achievement data saved to {achievement_file}")

        # Return overall score for CI/CD integration
        overall_score = results["kpis"]["overall_score"]
        print(f"\n🎯 Overall PR Score: {overall_score}/10")

        # Unified exit strategy - 7+ is excellent for ANY PR type
        if overall_score >= 7:
            sys.exit(0)
        elif overall_score >= 5:
            sys.exit(1)
        else:
            sys.exit(2)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
