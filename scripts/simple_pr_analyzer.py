#!/usr/bin/env python3
"""
Simplified Historical PR Analysis System (CRA-298)
Uses requests instead of aiohttp for easier setup
"""

import os
import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class PRMetrics:
    pr_number: int
    title: str
    state: str
    created_at: str
    merged_at: Optional[str]
    author: str
    lines_added: int
    lines_deleted: int
    files_changed: int
    labels: List[str]
    description: str


@dataclass
class BusinessValue:
    pr_number: int
    roi_percent: float
    cost_savings: float
    productivity_hours: float
    performance_improvement: float
    business_impact_score: float
    confidence_level: str
    value_category: str
    portfolio_value: float


class SimpleGitHubClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {self.token}" if self.token else "",
        }

    def get_all_prs(self, owner: str, repo: str, max_pages: int = 5) -> List[Dict]:
        """Fetch PRs with pagination (limited for demo)"""
        all_prs = []

        for page in range(1, max_pages + 1):
            url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
            params = {
                "state": "all",
                "per_page": 30,
                "page": page,
                "sort": "created",
                "direction": "desc",
            }

            print(f"Fetching PRs page {page}...")
            response = requests.get(url, headers=self.headers, params=params)

            if response.status_code == 200:
                prs = response.json()
                if not prs:
                    break
                all_prs.extend(prs)

                # Rate limiting
                remaining = int(response.headers.get("X-RateLimit-Remaining", 5000))
                if remaining < 100:
                    print(f"Rate limit low ({remaining}), waiting 60s...")
                    time.sleep(60)
                else:
                    time.sleep(1)  # Be nice to the API
            else:
                print(f"Error: {response.status_code} - {response.text}")
                break

        print(f"Fetched {len(all_prs)} total PRs")
        return all_prs


class SimplePRAnalyzer:
    def __init__(self):
        self.value_patterns = {
            "ai_ml": [
                "ai",
                "ml",
                "llm",
                "model",
                "neural",
                "rag",
                "embedding",
                "gpt",
                "claude",
            ],
            "performance": [
                "performance",
                "optimize",
                "speed",
                "latency",
                "throughput",
                "cache",
            ],
            "infrastructure": [
                "kubernetes",
                "docker",
                "ci/cd",
                "deployment",
                "monitoring",
                "k8s",
            ],
            "cost": ["cost", "savings", "reduce", "efficiency", "resource", "finops"],
            "feature": ["feature", "implement", "add", "new", "capability", "endpoint"],
            "bugfix": ["fix", "bug", "issue", "error", "resolve", "patch"],
        }

    def analyze_pr(self, pr_metrics: PRMetrics) -> BusinessValue:
        """Analyze PR for business value"""
        category = self._categorize_pr(pr_metrics)
        code_churn = pr_metrics.lines_added + pr_metrics.lines_deleted
        complexity_factor = min(code_churn / 500, 3)  # More conservative

        # Base calculations by category
        multipliers = {
            "ai_ml": {"roi": 250, "cost": 20000, "perf": 35},
            "performance": {"roi": 180, "cost": 12000, "perf": 25},
            "infrastructure": {"roi": 120, "cost": 15000, "perf": 20},
            "cost": {"roi": 200, "cost": 18000, "perf": 15},
            "feature": {"roi": 80, "cost": 8000, "perf": 10},
            "bugfix": {"roi": 40, "cost": 5000, "perf": 5},
        }

        mult = multipliers.get(category, multipliers["feature"])
        roi_percent = mult["roi"] * complexity_factor
        cost_savings = mult["cost"] * complexity_factor
        performance_improvement = mult["perf"] * complexity_factor

        # Additional metrics
        productivity_hours = code_churn * 0.05  # 0.05 hours per line
        business_impact_score = min(10, (roi_percent / 100) + (cost_savings / 15000))

        # Confidence based on PR quality indicators
        if pr_metrics.state == "closed" and pr_metrics.merged_at:
            confidence_level = "high"
        elif pr_metrics.state == "closed":
            confidence_level = "medium"
        else:
            confidence_level = "low"

        # Portfolio value (annual impact)
        portfolio_value = cost_savings + (productivity_hours * 120)  # $120/hour

        return BusinessValue(
            pr_number=pr_metrics.pr_number,
            roi_percent=round(roi_percent, 1),
            cost_savings=round(cost_savings, 2),
            productivity_hours=round(productivity_hours, 1),
            performance_improvement=round(performance_improvement, 1),
            business_impact_score=round(business_impact_score, 1),
            confidence_level=confidence_level,
            value_category=category,
            portfolio_value=round(portfolio_value, 2),
        )

    def _categorize_pr(self, pr_metrics: PRMetrics) -> str:
        """Categorize PR based on title and labels"""
        text = f"{pr_metrics.title} {pr_metrics.description}".lower()

        # Check labels first
        for label in pr_metrics.labels:
            if any(
                pattern in label.lower() for pattern in self.value_patterns["ai_ml"]
            ):
                return "ai_ml"
            elif "performance" in label.lower():
                return "performance"

        # Check text patterns
        category_scores = {}
        for category, patterns in self.value_patterns.items():
            score = sum(1 for pattern in patterns if pattern in text)
            if score > 0:
                category_scores[category] = score

        return (
            max(category_scores, key=category_scores.get)
            if category_scores
            else "feature"
        )


def analyze_repository(owner: str = "vitamin33", repo: str = "threads-agent"):
    """Main analysis function"""
    print(f"🚀 Analyzing {owner}/{repo} for AI Job Portfolio Metrics")
    print("-" * 60)

    # Initialize clients
    github_client = SimpleGitHubClient()
    analyzer = SimplePRAnalyzer()

    # Fetch PRs (limited to 150 for demo)
    prs = github_client.get_all_prs(owner, repo, max_pages=5)

    # Analyze each PR
    pr_metrics_list = []
    business_values = []

    for pr in prs:
        # Extract metrics
        pr_metrics = PRMetrics(
            pr_number=pr["number"],
            title=pr["title"],
            state=pr["state"],
            created_at=pr["created_at"],
            merged_at=pr.get("merged_at"),
            author=pr["user"]["login"],
            lines_added=pr.get("additions", 0),
            lines_deleted=pr.get("deletions", 0),
            files_changed=pr.get("changed_files", 0),
            labels=[label["name"] for label in pr.get("labels", [])],
            description=(pr.get("body") or "")[:300],
        )
        pr_metrics_list.append(pr_metrics)

        # Analyze business value
        business_value = analyzer.analyze_pr(pr_metrics)
        business_values.append(business_value)

    # Generate results
    total_value = sum(bv.portfolio_value for bv in business_values)
    avg_roi = (
        sum(bv.roi_percent for bv in business_values) / len(business_values)
        if business_values
        else 0
    )

    # Category breakdown
    categories = {}
    for bv in business_values:
        if bv.value_category not in categories:
            categories[bv.value_category] = {"count": 0, "value": 0}
        categories[bv.value_category]["count"] += 1
        categories[bv.value_category]["value"] += bv.portfolio_value

    # Results
    print("\n" + "=" * 60)
    print("📊 PORTFOLIO ANALYSIS RESULTS")
    print("=" * 60)
    print(f"Total Portfolio Value: ${total_value:,.2f}")
    print("Target Range: $200,000 - $350,000")
    print(
        f"Status: {'✅ VALIDATED' if 200000 <= total_value <= 350000 else '⚠️ NEEDS ADJUSTMENT'}"
    )
    print(f"Total PRs Analyzed: {len(pr_metrics_list)}")
    print(f"Average ROI: {avg_roi:.1f}%")

    print("\n📊 VALUE BY CATEGORY:")
    for category, stats in sorted(
        categories.items(), key=lambda x: x[1]["value"], reverse=True
    ):
        print(
            f"• {category.title()}: {stats['count']} PRs, ${stats['value']:,.0f} value"
        )

    # Top 5 achievements
    top_achievements = sorted(
        business_values, key=lambda x: x.portfolio_value, reverse=True
    )[:5]
    print("\n🏆 TOP 5 ACHIEVEMENTS FOR RESUME:")
    for i, bv in enumerate(top_achievements, 1):
        pr = next(pr for pr in pr_metrics_list if pr.pr_number == bv.pr_number)
        print(f"{i}. PR #{bv.pr_number}: {pr.title[:50]}...")
        print(
            f"   💰 ${bv.portfolio_value:,.0f} value | {bv.roi_percent:.0f}% ROI | {bv.value_category}"
        )

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = {
        "analysis_date": datetime.now().isoformat(),
        "repository": f"{owner}/{repo}",
        "total_portfolio_value": total_value,
        "total_prs": len(pr_metrics_list),
        "average_roi": avg_roi,
        "categories": categories,
        "top_achievements": [
            {
                "pr_number": bv.pr_number,
                "title": next(
                    pr.title for pr in pr_metrics_list if pr.pr_number == bv.pr_number
                ),
                "value": bv.portfolio_value,
                "roi": bv.roi_percent,
                "category": bv.value_category,
            }
            for bv in top_achievements
        ],
    }

    filename = f"pr_analysis_results_{timestamp}.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Results saved to: {filename}")
    print("\n🎯 Next Steps for AI Job Strategy:")
    print("1. Add top achievements to LinkedIn profile")
    print("2. Create portfolio website with these metrics")
    print("3. Write blog posts about technical implementations")
    print("4. Use in resume: 'Delivered $XXXk in business value'")

    return results


if __name__ == "__main__":
    analyze_repository()
