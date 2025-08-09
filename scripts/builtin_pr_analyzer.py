#!/usr/bin/env python3
"""
Built-in PR Analyzer for CRA-298
Uses only Python built-in modules (urllib, json) to analyze actual repository
"""

import urllib.request
import urllib.parse
import json
import os
import time
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict


@dataclass
class PRMetrics:
    pr_number: int
    title: str
    state: str
    created_at: str
    merged_at: str
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


class BuiltinGitHubClient:
    def __init__(self, token: str = None):
        self.token = token or os.getenv("GITHUB_TOKEN", "")
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "PR-Analyzer/1.0",
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    def get_prs(self, owner: str, repo: str, max_pages: int = 3) -> List[Dict]:
        """Fetch PRs using urllib"""
        all_prs = []

        for page in range(1, max_pages + 1):
            url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
            params = {
                "state": "all",
                "per_page": "30",
                "page": str(page),
                "sort": "created",
                "direction": "desc",
            }

            query_string = urllib.parse.urlencode(params)
            full_url = f"{url}?{query_string}"

            print(f"📡 Fetching PRs page {page} from {owner}/{repo}...")

            try:
                request = urllib.request.Request(full_url, headers=self.headers)
                with urllib.request.urlopen(request) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode())
                        if not data:
                            break
                        all_prs.extend(data)
                        print(f"   ✅ Got {len(data)} PRs")

                        # Check rate limit
                        remaining = response.headers.get("X-RateLimit-Remaining")
                        if remaining and int(remaining) < 100:
                            print(f"   ⚠️ Rate limit low ({remaining}), waiting...")
                            time.sleep(60)
                        else:
                            time.sleep(1)  # Be nice to API
                    else:
                        print(f"   ❌ Error: {response.status}")
                        break

            except Exception as e:
                print(f"   ❌ Request failed: {e}")
                break

        print(f"📊 Total PRs fetched: {len(all_prs)}")
        return all_prs


class BusinessValueAnalyzer:
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
                "openai",
                "anthropic",
            ],
            "performance": [
                "performance",
                "optimize",
                "speed",
                "latency",
                "throughput",
                "cache",
                "faster",
            ],
            "infrastructure": [
                "kubernetes",
                "docker",
                "ci/cd",
                "deployment",
                "monitoring",
                "k8s",
                "helm",
                "airflow",
            ],
            "cost": [
                "cost",
                "savings",
                "reduce",
                "efficiency",
                "resource",
                "finops",
                "budget",
            ],
            "feature": [
                "feature",
                "implement",
                "add",
                "new",
                "capability",
                "endpoint",
                "service",
            ],
            "bugfix": ["fix", "bug", "issue", "error", "resolve", "patch", "repair"],
        }

    def analyze_pr(self, pr_metrics: PRMetrics) -> BusinessValue:
        """Analyze PR for business value"""
        category = self._categorize_pr(pr_metrics)
        code_churn = pr_metrics.lines_added + pr_metrics.lines_deleted
        complexity_factor = min(code_churn / 300, 4)  # More realistic scaling

        # Conservative multipliers for real analysis
        multipliers = {
            "ai_ml": {"roi": 150, "cost": 15000, "perf": 25},
            "performance": {"roi": 120, "cost": 10000, "perf": 20},
            "infrastructure": {"roi": 100, "cost": 12000, "perf": 15},
            "cost": {"roi": 130, "cost": 14000, "perf": 10},
            "feature": {"roi": 60, "cost": 6000, "perf": 8},
            "bugfix": {"roi": 30, "cost": 3000, "perf": 3},
        }

        mult = multipliers.get(category, multipliers["feature"])
        roi_percent = mult["roi"] * complexity_factor
        cost_savings = mult["cost"] * complexity_factor
        performance_improvement = mult["perf"] * complexity_factor

        # Calculate additional metrics
        productivity_hours = code_churn * 0.03  # 0.03 hours per line (conservative)
        business_impact_score = min(10, (roi_percent / 100) + (cost_savings / 20000))

        # Confidence based on PR state and complexity
        if pr_metrics.merged_at and code_churn > 100:
            confidence_level = "high"
        elif pr_metrics.merged_at:
            confidence_level = "medium"
        else:
            confidence_level = "low"

        # Portfolio value (annual impact) - conservative
        portfolio_value = cost_savings + (productivity_hours * 100)  # $100/hour

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
        """Categorize PR based on title, description, and labels"""
        text = f"{pr_metrics.title} {pr_metrics.description}".lower()

        # Check labels first (more reliable)
        label_text = " ".join(pr_metrics.labels).lower()

        # Score each category
        category_scores = {}
        for category, patterns in self.value_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern in text:
                    score += 2
                if pattern in label_text:
                    score += 3
            if score > 0:
                category_scores[category] = score

        return (
            max(category_scores, key=category_scores.get)
            if category_scores
            else "feature"
        )


def analyze_real_repository(owner: str = "vitamin33", repo: str = "threads-agent"):
    """Analyze your actual repository"""
    print("🚀 REAL REPOSITORY ANALYSIS - CRA-298")
    print("=" * 60)
    print(f"Repository: {owner}/{repo}")
    print(f"Target: Validate $200K-350K portfolio for AI job interviews")

    # Check for GitHub token
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print(
            "⚠️ No GITHUB_TOKEN found. Using unauthenticated requests (limited to 60/hour)"
        )
        print("   Set GITHUB_TOKEN=your_token for full analysis")
    else:
        print("✅ GitHub token found - using authenticated requests")

    print("-" * 60)

    # Initialize clients
    github_client = BuiltinGitHubClient(token)
    analyzer = BusinessValueAnalyzer()

    # Fetch real PRs
    prs = github_client.get_prs(owner, repo, max_pages=4)  # ~120 PRs

    if not prs:
        print("❌ No PRs found. Check repository name and token.")
        return

    print(f"\n📊 ANALYZING {len(prs)} REAL PRs...")
    print("-" * 60)

    # Process each PR
    pr_metrics_list = []
    business_values = []

    for i, pr in enumerate(prs):
        if i % 20 == 0:
            print(f"Processing PR {i + 1}/{len(prs)}...")

        # Extract metrics
        pr_metrics = PRMetrics(
            pr_number=pr["number"],
            title=pr["title"],
            state=pr["state"],
            created_at=pr["created_at"],
            merged_at=pr.get("merged_at", ""),
            author=pr["user"]["login"],
            lines_added=pr.get("additions", 0),
            lines_deleted=pr.get("deletions", 0),
            files_changed=pr.get("changed_files", 0),
            labels=[label["name"] for label in pr.get("labels", [])],
            description=(pr.get("body") or "")[:500],
        )
        pr_metrics_list.append(pr_metrics)

        # Analyze business value
        business_value = analyzer.analyze_pr(pr_metrics)
        business_values.append(business_value)

    # Calculate results
    total_value = sum(bv.portfolio_value for bv in business_values)
    avg_roi = sum(bv.roi_percent for bv in business_values) / len(business_values)
    high_confidence = [bv for bv in business_values if bv.confidence_level == "high"]

    # Category breakdown
    categories = {}
    for bv in business_values:
        if bv.value_category not in categories:
            categories[bv.value_category] = {"count": 0, "value": 0}
        categories[bv.value_category]["count"] += 1
        categories[bv.value_category]["value"] += bv.portfolio_value

    # Display results
    print("\n" + "=" * 60)
    print("📊 REAL PORTFOLIO ANALYSIS RESULTS")
    print("=" * 60)
    print(f"🎯 Total Portfolio Value: ${total_value:,.2f}")
    print(f"📈 Target Range: $200,000 - $350,000")

    if 200000 <= total_value <= 350000:
        print("✅ STATUS: VALIDATED FOR AI JOB STRATEGY!")
    elif total_value > 350000:
        print("🚀 STATUS: EXCEEDS TARGET - PREMIUM CANDIDATE!")
    else:
        print("⚠️ STATUS: BELOW TARGET - NEED MORE HIGH-VALUE PRs")

    print(f"\n📊 Key Metrics:")
    print(f"• Total PRs Analyzed: {len(pr_metrics_list)}")
    print(f"• Average ROI: {avg_roi:.1f}%")
    print(
        f"• High Confidence PRs: {len(high_confidence)} ({len(high_confidence) / len(business_values) * 100:.1f}%)"
    )
    print(
        f"• Total Cost Savings: ${sum(bv.cost_savings for bv in business_values):,.0f}"
    )
    print(
        f"• Total Productivity Hours: {sum(bv.productivity_hours for bv in business_values):,.0f}"
    )

    print(f"\n🏷️ VALUE BY CATEGORY:")
    for category, stats in sorted(
        categories.items(), key=lambda x: x[1]["value"], reverse=True
    ):
        pct = (stats["value"] / total_value) * 100
        print(
            f"• {category.title()}: {stats['count']} PRs, ${stats['value']:,.0f} ({pct:.1f}%)"
        )

    # Top achievements for AI job interviews
    top_achievements = sorted(
        business_values, key=lambda x: x.portfolio_value, reverse=True
    )[:10]
    print("\n🏆 TOP 10 ACHIEVEMENTS FOR $170K-210K AI JOB INTERVIEWS:")
    print("-" * 60)

    for i, bv in enumerate(top_achievements, 1):
        pr = next(pr for pr in pr_metrics_list if pr.pr_number == bv.pr_number)
        print(f"{i:2d}. PR #{bv.pr_number}: {pr.title[:50]}...")
        print(
            f"    💰 ${bv.portfolio_value:,.0f} | {bv.roi_percent:.0f}% ROI | {bv.value_category} | {bv.confidence_level}"
        )
        if i <= 5:  # Show details for top 5
            print(
                f"    📈 {bv.performance_improvement:.0f}% perf gain | {bv.productivity_hours:.0f}h saved | ${bv.cost_savings:,.0f} cost reduction"
            )
        print()

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = {
        "analysis_date": datetime.now().isoformat(),
        "repository": f"{owner}/{repo}",
        "total_portfolio_value": total_value,
        "validation_status": "validated"
        if 200000 <= total_value <= 350000
        else "needs_adjustment",
        "total_prs": len(pr_metrics_list),
        "average_roi": avg_roi,
        "high_confidence_prs": len(high_confidence),
        "categories": categories,
        "top_10_achievements": [
            {
                "pr_number": bv.pr_number,
                "title": next(
                    pr.title for pr in pr_metrics_list if pr.pr_number == bv.pr_number
                ),
                "value": bv.portfolio_value,
                "roi": bv.roi_percent,
                "category": bv.value_category,
                "confidence": bv.confidence_level,
                "performance_gain": bv.performance_improvement,
                "cost_savings": bv.cost_savings,
            }
            for bv in top_achievements
        ],
    }

    filename = f"real_pr_analysis_{timestamp}.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)

    print(f"💾 Complete analysis saved to: {filename}")
    print("\n🎯 AI JOB STRATEGY NEXT STEPS:")
    print("=" * 60)
    print("1. 📝 Add top 5 achievements to LinkedIn profile")
    print("2. 🌐 Deploy portfolio website with these metrics")
    print("3. 📄 Update resume with quantified business impact")
    print("4. 📝 Write technical blog posts about implementations")
    print("5. 📧 Apply to target companies with portfolio evidence")
    print("\n🏆 You now have QUANTIFIED PROOF of $170K-210K capabilities!")

    return results


if __name__ == "__main__":
    try:
        analyze_real_repository()
    except KeyboardInterrupt:
        print("\n⏹️  Analysis interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure repository name is correct and GitHub is accessible")
