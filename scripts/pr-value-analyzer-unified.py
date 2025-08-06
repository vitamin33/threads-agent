#!/usr/bin/env python3
"""
Unified PR Value Analyzer - Adaptive scoring based on actual PR contributions

This analyzer detects what type of value a PR provides and scores it accordingly.
All PRs can achieve high scores by excelling in their area of contribution.
"""

import json
import subprocess
import re
from datetime import datetime
from typing import Dict, List, Any, Tuple, Set
import os
import sys
import math


class UnifiedPRValueAnalyzer:
    """Unified PR analyzer that adapts to different types of contributions."""

    def __init__(self, pr_number: str):
        self.pr_number = pr_number
        self.metrics = {
            "pr_number": pr_number,
            "timestamp": datetime.now().isoformat(),
            "pr_types": [],  # Can have multiple types
            "value_categories": {},  # Categories where this PR provides value
            "business_metrics": {},
            "technical_metrics": {},
            "quality_metrics": {},
            "documentation_metrics": {},
            "achievement_tags": [],
            "kpis": {},
            "future_impact": {},
            "active_metrics": {},  # Which metrics are relevant for this PR
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
            "retention",
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
            "reliability",
        ]
        quality_score = sum(1 for kw in quality_keywords if kw in title + body) * 0.15
        test_files = [f for f in files if "test" in f.get("path", "").lower()]
        if test_files:
            quality_score += 0.3 + (len(test_files) * 0.1)
        if re.search(r"\d+%\s*coverage|test\s*coverage", body, re.IGNORECASE):
            quality_score += 0.4
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
        doc_files = [
            f
            for f in files
            if any(
                ext in f.get("path", "").lower() for ext in [".md", "readme", "docs/"]
            )
        ]
        if doc_files:
            doc_score += 0.4 + (len(doc_files) * 0.1)
        categories["documentation"] = min(doc_score, 1.0)

        # Infrastructure indicators
        infra_keywords = [
            "kubernetes",
            "k8s",
            "docker",
            "ci",
            "cd",
            "deployment",
            "infrastructure",
            "helm",
            "terraform",
        ]
        infra_score = sum(1 for kw in infra_keywords if kw in title + body) * 0.2
        infra_files = [
            f
            for f in files
            if any(
                path in f.get("path", "").lower()
                for path in [".github/", "dockerfile", ".yaml", ".yml", "helm/", "k8s/"]
            )
        ]
        if infra_files:
            infra_score += 0.4
        categories["infrastructure"] = min(infra_score, 1.0)

        # Security indicators
        security_keywords = [
            "security",
            "vulnerability",
            "authentication",
            "authorization",
            "encryption",
            "cve",
            "patch",
        ]
        security_score = sum(1 for kw in security_keywords if kw in title + body) * 0.25
        categories["security"] = min(security_score, 1.0)

        # User experience indicators
        ux_keywords = [
            "ui",
            "ux",
            "user experience",
            "usability",
            "accessibility",
            "frontend",
            "design",
        ]
        ux_score = sum(1 for kw in ux_keywords if kw in title + body) * 0.2
        categories["user_experience"] = min(ux_score, 1.0)

        # Technical debt indicators
        debt_keywords = [
            "refactor",
            "cleanup",
            "technical debt",
            "legacy",
            "deprecate",
            "modernize",
        ]
        debt_score = sum(1 for kw in debt_keywords if kw in title + body) * 0.25
        if pr_data.get("deletions", 0) > pr_data.get("additions", 0):
            debt_score += 0.3
        categories["technical_debt"] = min(debt_score, 1.0)

        # Innovation indicators
        innovation_keywords = [
            "novel",
            "new approach",
            "innovative",
            "breakthrough",
            "ai",
            "ml",
            "rag",
            "llm",
        ]
        innovation_score = (
            sum(1 for kw in innovation_keywords if kw in title + body) * 0.2
        )
        if pr_data.get("additions", 0) > 500:
            innovation_score += 0.2
        categories["innovation"] = min(innovation_score, 1.0)

        return categories

    def extract_relevant_metrics(
        self, pr_body: str, categories: Dict[str, float]
    ) -> Dict[str, Any]:
        """Extract only metrics relevant to the PR's value categories."""
        metrics = {
            "performance": {},
            "business": {},
            "quality": {},
            "documentation": {},
            "infrastructure": {},
        }

        # Performance metrics (only if performance-related)
        if categories.get("performance", 0) > 0.3:
            # RPS
            rps_match = re.search(r"(\d+\.?\d*)\s*RPS", pr_body, re.IGNORECASE)
            if rps_match:
                metrics["performance"]["peak_rps"] = float(rps_match.group(1))

            # Latency
            latency_match = re.search(
                r"<(\d+)ms|(\d+)ms\s*latency", pr_body, re.IGNORECASE
            )
            if latency_match:
                metrics["performance"]["latency_ms"] = int(
                    latency_match.group(1) or latency_match.group(2)
                )

            # Throughput improvement
            throughput_match = re.search(
                r"(\d+)x\s*(?:faster|throughput|improvement)", pr_body, re.IGNORECASE
            )
            if throughput_match:
                metrics["performance"]["throughput_multiplier"] = int(
                    throughput_match.group(1)
                )

        # Business metrics (only if business-related)
        if categories.get("business", 0) > 0.3:
            # Cost savings
            cost_match = re.search(
                r"\$(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:k|K)?\s*(?:savings|saved|reduction)",
                pr_body,
            )
            if cost_match:
                amount = float(cost_match.group(1).replace(",", ""))
                if "k" in cost_match.group(0).lower():
                    amount *= 1000
                metrics["business"]["cost_savings"] = amount

            # ROI
            roi_match = re.search(r"(\d+)%\s*ROI", pr_body, re.IGNORECASE)
            if roi_match:
                metrics["business"]["roi_percent"] = int(roi_match.group(1))

            # Revenue impact
            revenue_match = re.search(
                r"(\d+)%\s*(?:revenue|conversion)\s*(?:increase|improvement)",
                pr_body,
                re.IGNORECASE,
            )
            if revenue_match:
                metrics["business"]["revenue_increase_percent"] = int(
                    revenue_match.group(1)
                )

        # Quality metrics (only if quality-related)
        if categories.get("quality", 0) > 0.3:
            # Test coverage
            coverage_match = re.search(
                r"(\d+)%\s*(?:test\s*)?coverage", pr_body, re.IGNORECASE
            )
            if coverage_match:
                metrics["quality"]["test_coverage"] = int(coverage_match.group(1))

            # Bug fixes
            bugs_match = re.search(
                r"(?:fixes?|resolved?)\s*(\d+)\s*bugs?", pr_body, re.IGNORECASE
            )
            if bugs_match:
                metrics["quality"]["bugs_fixed"] = int(bugs_match.group(1))

            # Test count
            tests_match = re.search(
                r"(?:added|created)\s*(\d+)\s*(?:unit\s*)?tests?",
                pr_body,
                re.IGNORECASE,
            )
            if tests_match:
                metrics["quality"]["tests_added"] = int(tests_match.group(1))

        # Documentation metrics (only if documentation-related)
        if categories.get("documentation", 0) > 0.3:
            # Pages/sections added
            docs_match = re.search(
                r"(\d+)\s*(?:pages?|sections?|guides?)\s*(?:added|created|written)",
                pr_body,
                re.IGNORECASE,
            )
            if docs_match:
                metrics["documentation"]["pages_added"] = int(docs_match.group(1))

            # API endpoints documented
            api_match = re.search(
                r"(\d+)\s*(?:api\s*)?endpoints?\s*documented", pr_body, re.IGNORECASE
            )
            if api_match:
                metrics["documentation"]["endpoints_documented"] = int(
                    api_match.group(1)
                )

        # Infrastructure metrics (only if infrastructure-related)
        if categories.get("infrastructure", 0) > 0.3:
            # Deployment time reduction
            deploy_match = re.search(
                r"(\d+)%\s*(?:faster|reduced)\s*deployment", pr_body, re.IGNORECASE
            )
            if deploy_match:
                metrics["infrastructure"]["deployment_time_reduction"] = int(
                    deploy_match.group(1)
                )

            # Availability improvement
            avail_match = re.search(
                r"(\d+\.?\d*)%\s*(?:availability|uptime)", pr_body, re.IGNORECASE
            )
            if avail_match:
                metrics["infrastructure"]["availability_percent"] = float(
                    avail_match.group(1)
                )

        return metrics

    def calculate_business_value(
        self, metrics: Dict[str, Any], categories: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate business value based on extracted metrics and PR categories."""
        value = {}

        # Only calculate relevant business metrics
        if categories.get("performance", 0) > 0.3 and metrics.get("performance"):
            perf = metrics["performance"]
            if "peak_rps" in perf:
                # Performance-based savings
                baseline_rps = 500
                if perf["peak_rps"] > baseline_rps:
                    servers_saved = math.floor((perf["peak_rps"] - baseline_rps) / 200)
                    value["infrastructure_savings"] = servers_saved * 12000
                    value["servers_reduced"] = servers_saved

        if categories.get("business", 0) > 0.3 and metrics.get("business"):
            biz = metrics["business"]
            # Direct business metrics
            if "cost_savings" in biz:
                value["direct_cost_savings"] = biz["cost_savings"]
            if "roi_percent" in biz:
                value["roi_year_one"] = biz["roi_percent"]
            if "revenue_increase_percent" in biz:
                # Assume $1M baseline revenue for calculation
                value["revenue_impact"] = 1000000 * (
                    biz["revenue_increase_percent"] / 100
                )

        if categories.get("quality", 0) > 0.3 and metrics.get("quality"):
            qual = metrics["quality"]
            if "bugs_fixed" in qual:
                # $5k per bug in production
                value["quality_savings"] = qual["bugs_fixed"] * 5000
            if "test_coverage" in qual and qual["test_coverage"] > 60:
                # Reduced maintenance costs
                value["maintenance_reduction"] = (qual["test_coverage"] - 60) * 500

        if categories.get("technical_debt", 0) > 0.3:
            # Technical debt reduction value
            value["tech_debt_savings"] = 25000 * categories["technical_debt"]

        if categories.get("documentation", 0) > 0.3:
            # Developer productivity from better docs
            value["developer_time_savings"] = 10000 * categories["documentation"]

        # Calculate total value
        total_value = sum(
            v
            for k, v in value.items()
            if isinstance(v, (int, float)) and "percent" not in k
        )
        if total_value > 0:
            value["total_business_value"] = total_value

        return value

    def calculate_unified_score(
        self,
        categories: Dict[str, float],
        metrics: Dict[str, Any],
        business_value: Dict[str, Any],
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate unified score using "best of" approach.
        PR succeeds if it excels in ANY relevant category.
        """
        scores = {}

        # Performance score (if applicable)
        if categories.get("performance", 0) > 0.3:
            perf_metrics = metrics.get("performance", {})
            rps = perf_metrics.get("peak_rps", 0)
            latency = perf_metrics.get("latency_ms", 999)

            rps_score = min(10, rps / 100) if rps > 0 else 0
            latency_score = max(0, 10 - (latency / 100)) if latency < 1000 else 0

            scores["performance"] = (
                (rps_score + latency_score) / 2 if rps_score or latency_score else 0
            )

        # Business score (if applicable)
        if categories.get("business", 0) > 0.3:
            total_value = business_value.get("total_business_value", 0)
            roi = business_value.get("roi_year_one", 0)

            value_score = min(10, total_value / 10000) if total_value > 0 else 0
            roi_score = min(10, roi / 30) if roi > 0 else 0

            scores["business"] = max(value_score, roi_score)

        # Quality score (if applicable)
        if categories.get("quality", 0) > 0.3:
            qual_metrics = metrics.get("quality", {})
            coverage = qual_metrics.get("test_coverage", 0)
            bugs_fixed = qual_metrics.get("bugs_fixed", 0)
            tests_added = qual_metrics.get("tests_added", 0)

            coverage_score = coverage / 10 if coverage > 0 else 0
            bugs_score = min(10, bugs_fixed * 2) if bugs_fixed > 0 else 0
            tests_score = min(10, tests_added / 5) if tests_added > 0 else 0

            scores["quality"] = max(coverage_score, bugs_score, tests_score)

        # Documentation score (if applicable)
        if categories.get("documentation", 0) > 0.3:
            doc_metrics = metrics.get("documentation", {})
            pages = doc_metrics.get("pages_added", 0)
            endpoints = doc_metrics.get("endpoints_documented", 0)

            pages_score = min(10, pages * 2) if pages > 0 else 0
            endpoints_score = min(10, endpoints / 2) if endpoints > 0 else 0

            scores["documentation"] = max(
                pages_score, endpoints_score, categories["documentation"] * 8
            )

        # Infrastructure score (if applicable)
        if categories.get("infrastructure", 0) > 0.3:
            infra_metrics = metrics.get("infrastructure", {})
            deploy_reduction = infra_metrics.get("deployment_time_reduction", 0)
            availability = infra_metrics.get("availability_percent", 0)

            deploy_score = min(10, deploy_reduction / 10) if deploy_reduction > 0 else 0
            avail_score = (availability - 90) if availability > 90 else 0

            scores["infrastructure"] = max(
                deploy_score, avail_score, categories["infrastructure"] * 7
            )

        # Innovation score (always applicable)
        innovation_score = categories.get("innovation", 0) * 10
        scores["innovation"] = innovation_score

        # Technical debt score (if applicable)
        if categories.get("technical_debt", 0) > 0.3:
            scores["technical_debt"] = categories["technical_debt"] * 8

        # Security score (if applicable)
        if categories.get("security", 0) > 0.3:
            scores["security"] = (
                categories["security"] * 9
            )  # High value for security fixes

        # UNIFIED SCORING: Best of approach
        # Take the highest score from all applicable categories
        if scores:
            best_score = max(scores.values())
            # Add small bonus for excelling in multiple categories
            multi_category_bonus = min(
                2, len([s for s in scores.values() if s > 5]) * 0.5
            )
            overall_score = min(10, best_score + multi_category_bonus)
        else:
            # No clear category, use basic heuristics
            file_count = len(metrics.get("code_changes", {}).get("files", []))
            overall_score = min(5, 2 + (file_count / 10))

        return overall_score, scores

    def generate_achievement_tags(
        self, categories: Dict[str, float], metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate achievement tags based on PR characteristics."""
        tags = []

        # Category-based tags
        if categories.get("performance", 0) > 0.5:
            tags.append("performance_optimization")
        if categories.get("business", 0) > 0.5:
            tags.append("business_value_driver")
        if categories.get("quality", 0) > 0.5:
            tags.append("quality_improvement")
        if categories.get("documentation", 0) > 0.5:
            tags.append("documentation_hero")
        if categories.get("infrastructure", 0) > 0.5:
            tags.append("infrastructure_enhancement")
        if categories.get("security", 0) > 0.5:
            tags.append("security_champion")
        if categories.get("innovation", 0) > 0.5:
            tags.append("innovation_leader")

        # Metric-based tags
        perf = metrics.get("performance", {})
        if perf.get("peak_rps", 0) > 1000:
            tags.append("high_performance_implementation")
        if perf.get("latency_ms", 999) < 100:
            tags.append("lightning_fast")

        qual = metrics.get("quality", {})
        if qual.get("test_coverage", 0) > 80:
            tags.append("well_tested")
        if qual.get("bugs_fixed", 0) > 5:
            tags.append("bug_crusher")

        return list(set(tags))

    def analyze_code_changes(self) -> Dict[str, Any]:
        """Analyze code changes in the PR."""
        try:
            # Get PR diff statistics
            result = subprocess.run(
                [
                    "gh",
                    "pr",
                    "view",
                    self.pr_number,
                    "--json",
                    "files,additions,deletions",
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                return {
                    "files": data.get("files", []),
                    "additions": data.get("additions", 0),
                    "deletions": data.get("deletions", 0),
                    "total_changes": data.get("additions", 0)
                    + data.get("deletions", 0),
                }
            return {}
        except Exception as e:
            print(f"Error analyzing code changes: {e}")
            return {}

    def run_analysis(self):
        """Run the unified PR analysis."""
        print(f"🔍 Analyzing PR #{self.pr_number} with unified scoring...")

        # Get PR data
        try:
            result = subprocess.run(
                [
                    "gh",
                    "pr",
                    "view",
                    self.pr_number,
                    "--json",
                    "title,body,labels,files,additions,deletions,author",
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                print(f"❌ Failed to fetch PR details: {result.stderr}")
                return None

            pr_data = json.loads(result.stdout)
            pr_body = pr_data.get("body", "")

            # Detect value categories
            categories = self.detect_pr_value_categories(pr_data)
            self.metrics["value_categories"] = categories

            # Identify active categories (confidence > 0.3)
            active_categories = [
                cat for cat, score in categories.items() if score > 0.3
            ]
            self.metrics["active_categories"] = active_categories

            # Extract relevant metrics based on categories
            extracted_metrics = self.extract_relevant_metrics(pr_body, categories)

            # Store metrics by category
            self.metrics["technical_metrics"] = extracted_metrics.get("performance", {})
            self.metrics["quality_metrics"] = extracted_metrics.get("quality", {})
            self.metrics["documentation_metrics"] = extracted_metrics.get(
                "documentation", {}
            )
            self.metrics["infrastructure_metrics"] = extracted_metrics.get(
                "infrastructure", {}
            )

            # Calculate business value
            business_value = self.calculate_business_value(
                extracted_metrics, categories
            )
            self.metrics["business_metrics"] = business_value

            # Analyze code changes
            code_changes = self.analyze_code_changes()
            self.metrics["code_changes"] = code_changes

            # Calculate unified score
            overall_score, category_scores = self.calculate_unified_score(
                categories, extracted_metrics, business_value
            )

            # Generate achievement tags
            tags = self.generate_achievement_tags(categories, extracted_metrics)
            self.metrics["achievement_tags"] = tags

            # Store KPIs
            self.metrics["kpis"] = {
                "overall_score": round(overall_score, 1),
                "category_scores": {k: round(v, 1) for k, v in category_scores.items()},
                "best_category": max(category_scores.items(), key=lambda x: x[1])[0]
                if category_scores
                else "none",
                "active_categories_count": len(active_categories),
            }

            # Mark which metrics were actually found/used
            self.metrics["active_metrics"] = {
                "performance": bool(extracted_metrics.get("performance")),
                "business": bool(extracted_metrics.get("business")),
                "quality": bool(extracted_metrics.get("quality")),
                "documentation": bool(extracted_metrics.get("documentation")),
                "infrastructure": bool(extracted_metrics.get("infrastructure")),
            }

            return self.metrics

        except Exception as e:
            print(f"❌ Error during analysis: {e}")
            return None

    def print_summary(self):
        """Print unified analysis summary."""
        print("\n📊 Unified PR Value Analysis")
        print("=" * 50)

        # Overall score
        overall = self.metrics["kpis"]["overall_score"]
        print(f"\n🎯 Overall Score: {overall}/10 ", end="")
        if overall >= 7:
            print("🌟 Excellent!")
        elif overall >= 5:
            print("✅ Good")
        else:
            print("⚠️ Needs Improvement")

        # Value categories detected
        print("\n📋 Value Categories Detected:")
        categories = self.metrics["value_categories"]
        for cat, confidence in sorted(
            categories.items(), key=lambda x: x[1], reverse=True
        ):
            if confidence > 0.3:
                print(f"  • {cat}: {confidence:.0%} confidence ✓")

        # Active metrics
        print("\n📈 Metrics Found:")
        if self.metrics.get("technical_metrics"):
            print(
                "  • Performance metrics:",
                ", ".join(self.metrics["technical_metrics"].keys()),
            )
        if self.metrics.get("business_metrics"):
            print(
                "  • Business metrics:",
                ", ".join(self.metrics["business_metrics"].keys()),
            )
        if self.metrics.get("quality_metrics"):
            print(
                "  • Quality metrics:",
                ", ".join(self.metrics["quality_metrics"].keys()),
            )

        # Category scores
        print("\n🏆 Category Scores (only relevant categories shown):")
        for cat, score in self.metrics["kpis"]["category_scores"].items():
            print(f"  • {cat}: {score}/10")

        # Best category
        best_cat = self.metrics["kpis"]["best_category"]
        print(f"\n⭐ Strongest Category: {best_cat}")

        # Business value (if any)
        if self.metrics.get("business_metrics"):
            print("\n💰 Business Value:")
            for key, value in self.metrics["business_metrics"].items():
                if isinstance(value, (int, float)):
                    if "percent" in key:
                        print(f"  • {key}: {value}%")
                    elif "savings" in key or "value" in key or "impact" in key:
                        print(f"  • {key}: ${value:,.0f}")
                    else:
                        print(f"  • {key}: {value}")

        # Achievement tags
        if self.metrics.get("achievement_tags"):
            print("\n🏷️ Achievement Tags:")
            for tag in self.metrics["achievement_tags"]:
                print(f"  • {tag}")

        print("\n📌 Scoring Philosophy:")
        print("  This PR is scored based on the value it actually delivers.")
        print("  Different types of PRs are evaluated on their own merits.")
        print(f"  Your PR excels in: {best_cat}")


def main():
    """Main execution."""
    if len(sys.argv) < 2:
        pr_number = os.environ.get("PR_NUMBER", "")
        if not pr_number:
            print("❌ Please provide PR number as argument or set PR_NUMBER env var")
            sys.exit(1)
    else:
        pr_number = sys.argv[1]

    analyzer = UnifiedPRValueAnalyzer(pr_number)
    results = analyzer.run_analysis()

    if results:
        analyzer.print_summary()

        # Save results
        output_file = f"pr_{pr_number}_value_analysis_unified.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n✅ Results saved to {output_file}")

        # Unified exit strategy: 7+ is good for ANY type of PR
        overall_score = results["kpis"]["overall_score"]
        if overall_score >= 7:
            sys.exit(0)  # Excellent
        elif overall_score >= 5:
            sys.exit(1)  # Good
        else:
            sys.exit(2)  # Needs improvement
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
