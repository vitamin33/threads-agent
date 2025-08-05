#!/usr/bin/env python3
"""
PR Value Analyzer V2 - Fair Scoring System for All PR Types

This script analyzes PRs with type-aware scoring that fairly evaluates
different kinds of contributions (features, bugs, docs, CI, etc).
"""

import json
import subprocess
import re
from datetime import datetime
from typing import Dict, List, Any, Tuple
import os
import sys


class PRValueAnalyzerV2:
    """Analyzes PR content with fair, type-aware scoring."""

    def __init__(self, pr_number: str):
        self.pr_number = pr_number
        self.metrics = {
            "pr_number": pr_number,
            "timestamp": datetime.now().isoformat(),
            "pr_type": "unknown",
            "business_metrics": {},
            "technical_metrics": {},
            "achievement_tags": [],
            "kpis": {},
            "future_impact": {},
        }

    def detect_pr_type(self, pr_data: Dict) -> str:
        """Detect PR type from title, body, and files changed."""
        title = pr_data.get("title", "").lower()
        body = pr_data.get("body", "").lower()
        files = pr_data.get("files", [])
        
        # Conventional commit patterns
        if title.startswith("feat:") or title.startswith("feature:"):
            return "feature"
        elif title.startswith("fix:") or title.startswith("bugfix:"):
            return "bugfix"
        elif title.startswith("docs:"):
            return "documentation"
        elif title.startswith("refactor:"):
            return "refactoring"
        elif title.startswith("test:"):
            return "testing"
        elif title.startswith("ci:") or title.startswith("build:"):
            return "ci"
        elif title.startswith("perf:"):
            return "performance"
        elif title.startswith("chore:"):
            return "chore"
        
        # Content-based detection
        if any(word in title + body for word in ["bug", "error", "crash", "broken", "fix"]):
            return "bugfix"
        
        # File-based detection
        file_paths = [f.get("path", "") for f in files]
        
        if all(".md" in path or "README" in path or "docs/" in path for path in file_paths if path):
            return "documentation"
        
        if all("test" in path or "spec" in path for path in file_paths if path):
            return "testing"
        
        if any(path.startswith(".github/") or "Dockerfile" in path or "ci/" in path for path in file_paths):
            return "ci"
        
        # Size-based heuristics
        additions = pr_data.get("additions", 0)
        deletions = pr_data.get("deletions", 0)
        
        if deletions > additions * 1.5:
            return "refactoring"
        
        return "feature"  # Default

    def get_scoring_weights(self, pr_type: str) -> Dict[str, float]:
        """Get scoring weights based on PR type."""
        weights = {
            "feature": {
                "complexity": 0.20,
                "test_coverage": 0.25,
                "documentation": 0.15,
                "innovation": 0.25,
                "risk_mitigation": 0.15
            },
            "bugfix": {
                "complexity": 0.10,
                "test_coverage": 0.30,
                "documentation": 0.10,
                "innovation": 0.10,
                "risk_mitigation": 0.40  # High value for fixing issues
            },
            "documentation": {
                "complexity": 0.15,
                "test_coverage": 0.05,
                "documentation": 0.50,  # Primary value
                "innovation": 0.10,
                "risk_mitigation": 0.20
            },
            "refactoring": {
                "complexity": 0.20,
                "test_coverage": 0.25,
                "documentation": 0.10,
                "innovation": 0.15,
                "risk_mitigation": 0.30  # Reduces tech debt
            },
            "testing": {
                "complexity": 0.15,
                "test_coverage": 0.40,  # Primary value
                "documentation": 0.10,
                "innovation": 0.10,
                "risk_mitigation": 0.25
            },
            "ci": {
                "complexity": 0.20,
                "test_coverage": 0.15,
                "documentation": 0.15,
                "innovation": 0.20,
                "risk_mitigation": 0.30  # Improves reliability
            },
            "performance": {
                "complexity": 0.25,
                "test_coverage": 0.20,
                "documentation": 0.10,
                "innovation": 0.30,
                "risk_mitigation": 0.15
            },
            "chore": {
                "complexity": 0.20,
                "test_coverage": 0.20,
                "documentation": 0.20,
                "innovation": 0.20,
                "risk_mitigation": 0.20  # Balanced
            }
        }
        return weights.get(pr_type, weights["feature"])

    def calculate_complexity_score(self, pr_data: Dict) -> float:
        """Calculate complexity score based on size and scope."""
        additions = pr_data.get("additions", 0)
        deletions = pr_data.get("deletions", 0)
        files_changed = len(pr_data.get("files", []))
        
        # Size score (0-10)
        total_lines = additions + deletions
        if total_lines < 50:
            size_score = 3
        elif total_lines < 200:
            size_score = 5
        elif total_lines < 500:
            size_score = 7
        elif total_lines < 1000:
            size_score = 8
        else:
            size_score = 9
        
        # Scope score (0-10)
        if files_changed < 5:
            scope_score = 3
        elif files_changed < 10:
            scope_score = 5
        elif files_changed < 20:
            scope_score = 7
        else:
            scope_score = 9
        
        return (size_score + scope_score) / 2

    def calculate_test_coverage_score(self, pr_data: Dict, pr_type: str) -> float:
        """Calculate test coverage score."""
        body = pr_data.get("body", "").lower()
        files = pr_data.get("files", [])
        
        # Check for test files
        test_files = [f for f in files if "test" in f.get("path", "").lower()]
        has_tests = len(test_files) > 0
        
        # Base score by PR type
        if pr_type == "testing":
            return 9.0  # Testing PRs inherently have high test value
        elif pr_type == "documentation":
            return 5.0  # Docs don't need tests
        elif pr_type == "bugfix" and has_tests:
            return 8.0  # Bug fixes with tests are valuable
        
        # Check for test mentions in body
        test_keywords = ["test", "coverage", "unit test", "integration test", "e2e"]
        test_mentions = sum(1 for keyword in test_keywords if keyword in body)
        
        if has_tests:
            return min(7.0 + test_mentions * 0.5, 10.0)
        elif test_mentions > 0:
            return min(4.0 + test_mentions * 0.5, 7.0)
        else:
            return 2.0

    def calculate_documentation_score(self, pr_data: Dict, pr_type: str) -> float:
        """Calculate documentation score."""
        files = pr_data.get("files", [])
        body = pr_data.get("body", "").lower()
        
        # Check for documentation files
        doc_files = [f for f in files if ".md" in f.get("path", "").lower() or "readme" in f.get("path", "").lower()]
        has_docs = len(doc_files) > 0
        
        # Base score by PR type
        if pr_type == "documentation":
            return 9.0  # Documentation PRs inherently have high doc value
        
        # Check for documentation mentions
        doc_keywords = ["documentation", "readme", "guide", "tutorial", "example"]
        doc_mentions = sum(1 for keyword in doc_keywords if keyword in body)
        
        if has_docs:
            return min(7.0 + doc_mentions * 0.3, 10.0)
        elif doc_mentions > 0:
            return min(4.0 + doc_mentions * 0.3, 6.0)
        else:
            return 2.0

    def calculate_innovation_score(self, pr_data: Dict, pr_type: str) -> float:
        """Calculate innovation score based on PR type and content."""
        title = pr_data.get("title", "").lower()
        body = pr_data.get("body", "").lower()
        
        # Innovation keywords
        innovation_keywords = [
            "new", "novel", "innovative", "breakthrough", "advanced",
            "optimization", "performance", "scale", "architecture",
            "framework", "system", "pipeline", "integration"
        ]
        
        keyword_count = sum(1 for keyword in innovation_keywords if keyword in title + body)
        
        # Base scores by type
        base_scores = {
            "feature": 6.0,
            "performance": 7.0,
            "ci": 5.0,
            "refactoring": 4.0,
            "bugfix": 3.0,
            "documentation": 3.0,
            "testing": 3.0,
            "chore": 2.0
        }
        
        base_score = base_scores.get(pr_type, 5.0)
        return min(base_score + keyword_count * 0.5, 10.0)

    def calculate_risk_mitigation_score(self, pr_data: Dict, pr_type: str) -> float:
        """Calculate risk mitigation score."""
        title = pr_data.get("title", "").lower()
        body = pr_data.get("body", "").lower()
        
        # Risk mitigation keywords
        risk_keywords = [
            "fix", "bug", "error", "crash", "security", "vulnerability",
            "stability", "reliability", "monitoring", "alert", "validation",
            "error handling", "fallback", "recovery", "resilience"
        ]
        
        keyword_count = sum(1 for keyword in risk_keywords if keyword in title + body)
        
        # Base scores by type
        base_scores = {
            "bugfix": 8.0,
            "security": 9.0,
            "ci": 6.0,
            "testing": 6.0,
            "refactoring": 5.0,
            "feature": 3.0,
            "documentation": 4.0,
            "chore": 3.0
        }
        
        base_score = base_scores.get(pr_type, 4.0)
        return min(base_score + keyword_count * 0.3, 10.0)

    def calculate_overall_score(self, pr_data: Dict) -> Tuple[float, Dict[str, float]]:
        """Calculate overall score with type-aware weighting."""
        pr_type = self.detect_pr_type(pr_data)
        weights = self.get_scoring_weights(pr_type)
        
        # Calculate individual scores
        scores = {
            "complexity": self.calculate_complexity_score(pr_data),
            "test_coverage": self.calculate_test_coverage_score(pr_data, pr_type),
            "documentation": self.calculate_documentation_score(pr_data, pr_type),
            "innovation": self.calculate_innovation_score(pr_data, pr_type),
            "risk_mitigation": self.calculate_risk_mitigation_score(pr_data, pr_type)
        }
        
        # Apply weights
        weighted_score = sum(scores[key] * weights[key] for key in scores)
        
        return round(weighted_score, 1), scores

    def get_pr_data(self) -> Dict[str, Any]:
        """Fetch PR data from GitHub."""
        try:
            # Get PR details
            result = subprocess.run(
                ["gh", "pr", "view", self.pr_number, "--json", 
                 "title,body,labels,files,additions,deletions,author,createdAt,updatedAt"],
                capture_output=True,
                text=True,
            )
            
            if result.returncode != 0:
                print(f"❌ Error fetching PR data: {result.stderr}")
                return None
            
            return json.loads(result.stdout)
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    def run_analysis(self) -> Dict[str, Any]:
        """Run the complete PR value analysis."""
        print(f"🔍 Analyzing PR #{self.pr_number}...")
        
        pr_data = self.get_pr_data()
        if not pr_data:
            return None
        
        # Detect PR type
        pr_type = self.detect_pr_type(pr_data)
        self.metrics["pr_type"] = pr_type
        
        # Calculate scores
        overall_score, individual_scores = self.calculate_overall_score(pr_data)
        
        # Store results
        self.metrics["kpis"] = {
            "overall_score": overall_score,
            "individual_scores": individual_scores,
            "pr_type": pr_type
        }
        
        self.metrics["scoring_weights"] = self.get_scoring_weights(pr_type)
        
        return self.metrics

    def print_summary(self):
        """Print analysis summary."""
        print("\n📊 PR Value Analysis Summary (Fair Scoring)")
        print("=" * 50)
        
        pr_type = self.metrics["pr_type"]
        overall_score = self.metrics["kpis"]["overall_score"]
        scores = self.metrics["kpis"]["individual_scores"]
        weights = self.metrics["scoring_weights"]
        
        print(f"\n📑 PR Type: {pr_type.upper()}")
        print(f"🎯 Overall Score: {overall_score}/10")
        print("\n📈 Score Breakdown:")
        
        for metric, score in scores.items():
            weight = weights[metric]
            weighted = score * weight
            print(f"  {metric.replace('_', ' ').title()}: {score:.1f}/10 (weight: {weight:.0%}) = {weighted:.1f}")
        
        # Interpretation
        print(f"\n📋 Interpretation:")
        if overall_score >= 8:
            print("  ✅ Excellent PR - High value contribution")
        elif overall_score >= 6:
            print("  ✅ Good PR - Solid contribution")
        elif overall_score >= 4:
            print("  ⚠️  Average PR - Meets basic standards")
        else:
            print("  ❌ Below Average - Consider improvements")
        
        print(f"\n💡 This scoring system is optimized for {pr_type} PRs")


def main():
    """Main execution."""
    if len(sys.argv) < 2:
        pr_number = os.environ.get("PR_NUMBER", "")
        if not pr_number:
            print("❌ Please provide PR number as argument or set PR_NUMBER env var")
            sys.exit(1)
    else:
        pr_number = sys.argv[1]
    
    analyzer = PRValueAnalyzerV2(pr_number)
    results = analyzer.run_analysis()
    
    if results:
        analyzer.print_summary()
        
        # Save results
        output_file = f"pr_{pr_number}_value_analysis_v2.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n✅ Results saved to {output_file}")
        
        # Use same exit code strategy but with fair scoring
        overall_score = results["kpis"]["overall_score"]
        if overall_score >= 7:
            sys.exit(0)  # Success
        elif overall_score >= 5:
            sys.exit(1)  # Warning
        else:
            sys.exit(2)  # Needs improvement
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()