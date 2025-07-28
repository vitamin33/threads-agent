"""CI/CD Metrics Collector for comprehensive achievement tracking."""

import os
import re
import json
import subprocess
from typing import Dict, Any
import xml.etree.ElementTree as ET

from services.achievement_collector.core.logging import setup_logging

logger = setup_logging(__name__)


class CIMetricsCollector:
    """Collects comprehensive metrics from CI/CD pipeline."""

    def __init__(self):
        """Initialize metrics collector."""
        self.metrics = {
            "performance": {},
            "quality": {},
            "business": {},
            "planning": {},
            "deployment": {},
            "monitoring": {},
        }

    async def collect_all_metrics(self, pr_number: int, sha: str) -> Dict[str, Any]:
        """Collect all available metrics from various sources."""
        logger.info(f"Collecting metrics for PR #{pr_number} (SHA: {sha})")

        # Collect different metric categories
        self.metrics["performance"] = await self._collect_performance_metrics(sha)
        self.metrics["quality"] = await self._collect_quality_metrics(sha)
        self.metrics["business"] = await self._collect_business_metrics(pr_number)
        self.metrics["planning"] = await self._collect_planning_metrics(pr_number)
        self.metrics["deployment"] = await self._collect_deployment_metrics(sha)
        self.metrics["monitoring"] = await self._collect_monitoring_metrics()

        return self.metrics

    async def _collect_performance_metrics(self, sha: str) -> Dict[str, Any]:
        """Collect performance-related metrics."""
        perf_metrics = {}

        # Test execution time from pytest
        if os.path.exists("test-results.xml"):
            try:
                tree = ET.parse("test-results.xml")
                root = tree.getroot()
                perf_metrics["test_execution_time"] = float(root.get("time", 0))
                perf_metrics["test_count"] = len(root.findall(".//testcase"))
                perf_metrics["test_failures"] = len(root.findall(".//failure"))
                perf_metrics["test_errors"] = len(root.findall(".//error"))
            except Exception as e:
                logger.error(f"Error parsing test results: {e}")

        # Code coverage
        if os.path.exists("coverage.xml"):
            try:
                tree = ET.parse("coverage.xml")
                root = tree.getroot()
                perf_metrics["line_coverage"] = float(root.get("line-rate", 0)) * 100
                perf_metrics["branch_coverage"] = (
                    float(root.get("branch-rate", 0)) * 100
                )

                # Calculate complexity metrics
                classes = root.findall(".//class")
                if classes:
                    complexities = [float(c.get("complexity", 0)) for c in classes]
                    perf_metrics["avg_complexity"] = sum(complexities) / len(
                        complexities
                    )
                    perf_metrics["max_complexity"] = max(complexities)
            except Exception as e:
                logger.error(f"Error parsing coverage: {e}")

        # Benchmark results if available
        if os.path.exists("benchmark-results.json"):
            try:
                with open("benchmark-results.json", "r") as f:
                    benchmarks = json.load(f)
                    perf_metrics["benchmarks"] = benchmarks
            except Exception as e:
                logger.error(f"Error reading benchmarks: {e}")

        # Load test results
        if os.path.exists("loadtest-results.json"):
            try:
                with open("loadtest-results.json", "r") as f:
                    load_test = json.load(f)
                    perf_metrics["avg_response_time"] = load_test.get(
                        "avg_response_time"
                    )
                    perf_metrics["p95_response_time"] = load_test.get(
                        "p95_response_time"
                    )
                    perf_metrics["requests_per_second"] = load_test.get("rps")
            except Exception as e:
                logger.error(f"Error reading load test results: {e}")

        return perf_metrics

    async def _collect_quality_metrics(self, sha: str) -> Dict[str, Any]:
        """Collect code quality metrics."""
        quality_metrics = {}

        # Linting results
        if os.path.exists("lint-results.json"):
            try:
                with open("lint-results.json", "r") as f:
                    lint_results = json.load(f)
                    quality_metrics["lint_errors"] = lint_results.get("error_count", 0)
                    quality_metrics["lint_warnings"] = lint_results.get(
                        "warning_count", 0
                    )
            except Exception as e:
                logger.error(f"Error reading lint results: {e}")

        # Security scan results
        if os.path.exists("security-scan.json"):
            try:
                with open("security-scan.json", "r") as f:
                    security = json.load(f)
                    quality_metrics["security_vulnerabilities"] = security.get(
                        "vulnerability_count", 0
                    )
                    quality_metrics["security_score"] = security.get("score", 100)
            except Exception as e:
                logger.error(f"Error reading security scan: {e}")

        # Type checking results
        if os.path.exists("mypy-results.json"):
            try:
                with open("mypy-results.json", "r") as f:
                    mypy = json.load(f)
                    quality_metrics["type_errors"] = mypy.get("error_count", 0)
                    quality_metrics["type_coverage"] = mypy.get("coverage_percent", 0)
            except Exception as e:
                logger.error(f"Error reading mypy results: {e}")

        # Documentation coverage
        try:
            result = subprocess.run(
                ["pydoc-coverage", "--json"], capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                doc_coverage = json.loads(result.stdout)
                quality_metrics["doc_coverage"] = doc_coverage.get("coverage", 0)
        except Exception as e:
            logger.debug(f"Could not get doc coverage: {e}")

        return quality_metrics

    async def _collect_business_metrics(self, pr_number: int) -> Dict[str, Any]:
        """Extract business metrics from PR and codebase."""
        business_metrics = {
            "kpis_affected": [],
            "features_added": [],
            "bugs_fixed": 0,
            "performance_improvements": [],
            "cost_impact": None,
            "revenue_impact": None,
        }

        # Analyze PR for business impact
        pr_data = os.getenv("PR_DATA", "{}")
        try:
            pr = json.loads(pr_data)
            pr_body = pr.get("body", "")
            pr_title = pr.get("title", "")

            # Extract KPIs mentioned
            kpi_patterns = {
                "engagement_rate": r"engagement.*?(\d+\.?\d*)\s*%",
                "cost_per_follow": r"cost.*?follow.*?\$(\d+\.?\d*)",
                "mrr": r"MRR.*?\$(\d+\.?\d*k?)",
                "conversion_rate": r"conversion.*?(\d+\.?\d*)\s*%",
                "retention_rate": r"retention.*?(\d+\.?\d*)\s*%",
                "churn_rate": r"churn.*?(\d+\.?\d*)\s*%",
            }

            for kpi, pattern in kpi_patterns.items():
                match = re.search(pattern, pr_body + pr_title, re.I)
                if match:
                    business_metrics["kpis_affected"].append(
                        {
                            "kpi": kpi,
                            "value": match.group(1),
                            "mentioned_in": "pr_description",
                        }
                    )

            # Extract features from conventional commits
            if "feat:" in pr_title.lower() or "feature:" in pr_title.lower():
                feature_match = re.search(
                    r"feat(?:ure)?[:\(](.+?)[\)\:]", pr_title, re.I
                )
                if feature_match:
                    business_metrics["features_added"].append(
                        feature_match.group(1).strip()
                    )

            # Count bug fixes
            if "fix:" in pr_title.lower() or "bug" in pr_title.lower():
                business_metrics["bugs_fixed"] += 1

            # Performance improvements
            if "perf:" in pr_title.lower() or "optimize" in pr_title.lower():
                perf_match = re.search(
                    r"(\d+\.?\d*)\s*(%|x|times?)\s*(faster|improvement|reduction)",
                    pr_body,
                    re.I,
                )
                if perf_match:
                    business_metrics["performance_improvements"].append(
                        {
                            "metric": "performance",
                            "improvement": perf_match.group(1),
                            "unit": perf_match.group(2),
                        }
                    )

            # Cost/Revenue impact
            cost_match = re.search(
                r"save.*?\$(\d+\.?\d*k?)|reduce.*?cost.*?\$(\d+\.?\d*k?)", pr_body, re.I
            )
            if cost_match:
                business_metrics["cost_impact"] = cost_match.group(
                    1
                ) or cost_match.group(2)

            revenue_match = re.search(
                r"revenue.*?\$(\d+\.?\d*k?)|increase.*?revenue.*?(\d+\.?\d*)\s*%",
                pr_body,
                re.I,
            )
            if revenue_match:
                business_metrics["revenue_impact"] = (
                    revenue_match.group(1) or f"{revenue_match.group(2)}%"
                )

        except Exception as e:
            logger.error(f"Error extracting business metrics: {e}")

        return business_metrics

    async def _collect_planning_metrics(self, pr_number: int) -> Dict[str, Any]:
        """Collect project planning metrics."""
        planning_metrics = {
            "linked_issues": [],
            "epic": None,
            "sprint": None,
            "story_points": None,
            "milestone": None,
            "project": None,
        }

        pr_data = os.getenv("PR_DATA", "{}")
        try:
            pr = json.loads(pr_data)
            pr_body = pr.get("body", "")
            pr_title = pr.get("title", "")
            full_text = f"{pr_title} {pr_body}"

            # Extract Linear issue IDs
            linear_pattern = r"([A-Z]{2,}-\d+)"
            linear_matches = re.findall(linear_pattern, full_text)
            planning_metrics["linked_issues"].extend(linear_matches)

            # Extract GitHub issue IDs
            github_pattern = r"#(\d+)"
            github_matches = re.findall(github_pattern, full_text)
            planning_metrics["linked_issues"].extend(
                [f"GH-{num}" for num in github_matches]
            )

            # Extract epic
            epic_pattern = r"[Ee]pic[:\s]+([^\n]+)"
            epic_match = re.search(epic_pattern, pr_body)
            if epic_match:
                planning_metrics["epic"] = epic_match.group(1).strip()

            # Extract sprint
            sprint_pattern = r"[Ss]print[:\s]+(\d+|[^\n]+)"
            sprint_match = re.search(sprint_pattern, pr_body)
            if sprint_match:
                planning_metrics["sprint"] = sprint_match.group(1).strip()

            # Extract story points
            points_pattern = r"(\d+)\s*(?:story\s*)?points?"
            points_match = re.search(points_pattern, pr_body, re.I)
            if points_match:
                planning_metrics["story_points"] = int(points_match.group(1))

            # Extract milestone from labels
            labels = pr.get("labels", [])
            for label in labels:
                label_name = label.get("name", "")
                if "milestone" in label_name.lower():
                    planning_metrics["milestone"] = label_name
                elif "project" in label_name.lower():
                    planning_metrics["project"] = label_name

        except Exception as e:
            logger.error(f"Error extracting planning metrics: {e}")

        return planning_metrics

    async def _collect_deployment_metrics(self, sha: str) -> Dict[str, Any]:
        """Collect deployment-related metrics."""
        deployment_metrics = {
            "deployment_time": None,
            "rollback_count": 0,
            "deployment_size": None,
            "affected_services": [],
            "deployment_type": None,
            "environment": None,
        }

        # Check deployment logs if available
        if os.path.exists("deployment-log.json"):
            try:
                with open("deployment-log.json", "r") as f:
                    deploy_log = json.load(f)
                    deployment_metrics.update(deploy_log)
            except Exception as e:
                logger.error(f"Error reading deployment log: {e}")

        # Analyze Kubernetes manifests changes
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", f"{sha}^", sha],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                changed_files = result.stdout.strip().split("\n")
                k8s_files = [
                    f
                    for f in changed_files
                    if "k8s" in f or "helm" in f or ".yaml" in f
                ]
                if k8s_files:
                    deployment_metrics["affected_services"] = list(
                        set([os.path.basename(f).split(".")[0] for f in k8s_files])
                    )
                    deployment_metrics["deployment_type"] = "kubernetes"
        except Exception as e:
            logger.debug(f"Could not analyze k8s changes: {e}")

        return deployment_metrics

    async def _collect_monitoring_metrics(self) -> Dict[str, Any]:
        """Collect monitoring and observability metrics."""
        monitoring_metrics = {
            "alerts_configured": 0,
            "dashboards_updated": 0,
            "metrics_added": [],
            "logs_structured": False,
            "tracing_enabled": False,
        }

        # Check for monitoring configuration changes
        try:
            # Check Prometheus rules
            if os.path.exists("monitoring/prometheus/rules"):
                alert_files = len(os.listdir("monitoring/prometheus/rules"))
                monitoring_metrics["alerts_configured"] = alert_files

            # Check Grafana dashboards
            if os.path.exists("monitoring/grafana/dashboards"):
                dashboard_files = len(os.listdir("monitoring/grafana/dashboards"))
                monitoring_metrics["dashboards_updated"] = dashboard_files

        except Exception as e:
            logger.debug(f"Could not check monitoring configs: {e}")

        return monitoring_metrics

    def calculate_comprehensive_impact_score(self) -> float:
        """Calculate impact score based on all collected metrics."""
        score = 50.0  # Base score

        # Performance impact (up to 20 points)
        perf = self.metrics.get("performance", {})
        if perf.get("test_coverage", 0) >= 80:
            score += 5
        if perf.get("avg_response_time") and perf["avg_response_time"] < 100:
            score += 5
        if perf.get("benchmarks") and any(
            b.get("improvement", 0) > 10 for b in perf["benchmarks"]
        ):
            score += 10

        # Quality impact (up to 15 points)
        quality = self.metrics.get("quality", {})
        if quality.get("lint_errors", 1) == 0:
            score += 5
        if quality.get("security_vulnerabilities", 1) == 0:
            score += 5
        if quality.get("type_coverage", 0) >= 90:
            score += 5

        # Business impact (up to 25 points)
        business = self.metrics.get("business", {})
        if business.get("revenue_impact"):
            score += 15
        elif business.get("cost_impact"):
            score += 10
        if business.get("kpis_affected"):
            score += 5
        if business.get("features_added"):
            score += 5

        # Planning alignment (up to 10 points)
        planning = self.metrics.get("planning", {})
        if planning.get("epic"):
            score += 5
        if planning.get("linked_issues"):
            score += 5

        return min(score, 100.0)


async def collect_metrics_for_ci(pr_number: int, sha: str) -> Dict[str, Any]:
    """Main entry point for CI metric collection."""
    collector = CIMetricsCollector()
    metrics = await collector.collect_all_metrics(pr_number, sha)
    metrics["impact_score"] = collector.calculate_comprehensive_impact_score()
    return metrics
