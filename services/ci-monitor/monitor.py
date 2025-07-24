#!/usr/bin/env python3
"""
CI Monitor Service - Continuously monitors CI failures and attempts fixes
"""

import os
import subprocess
import time
from typing import Any, Dict, List

try:
    from github import Github

    HAS_GITHUB = True
except ImportError:
    Github = None  # type: ignore[misc,assignment]
    HAS_GITHUB = False


class CIMonitor:
    def __init__(self) -> None:
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.repo_name = "threads-agent-stack/threads-agent"
        if HAS_GITHUB:
            self.github = Github(self.github_token)
            self.repo = self.github.get_repo(self.repo_name)
        else:
            raise ImportError("github package not installed")

    def get_failed_prs(self) -> List[Dict[str, Any]]:
        """Get PRs with failed CI checks"""
        failed_prs: List[Dict[str, Any]] = []

        for pr in self.repo.get_pulls(state="open"):
            # Check if CI is failing
            for check in pr.get_commits()[0].get_check_runs():
                if check.conclusion == "failure":
                    failed_prs.append(
                        {
                            "pr_number": pr.number,
                            "branch": pr.head.ref,
                            "check_name": check.name,
                            "check_url": check.details_url,
                            "failure_time": check.completed_at,
                        }
                    )

        return failed_prs

    def analyze_failure(self, pr_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze CI failure logs"""
        # Download logs from GitHub Actions
        check_url = pr_info["check_url"]
        # Extract job ID from URL
        job_id = check_url.split("/")[-1]

        # Get logs via GitHub API
        logs = self.get_job_logs(job_id)

        # Extract error patterns
        errors = self.extract_errors(logs)

        return {
            "pr_number": pr_info["pr_number"],
            "branch": pr_info["branch"],
            "errors": errors,
            "fixable": self.is_fixable(errors),
        }

    def is_fixable(self, errors: List[str]) -> bool:
        """Determine if errors are auto-fixable"""
        fixable_patterns = [
            "mypy error",
            "import error",
            "test failure",
            "linting error",
            "type annotation",
            "missing import",
            "undefined variable",
        ]

        for error in errors:
            for pattern in fixable_patterns:
                if pattern.lower() in error.lower():
                    return True
        return False

    def attempt_fix(self, analysis: Dict[str, Any]) -> bool:
        """Attempt to fix the errors using Claude Code"""
        pr_number = analysis["pr_number"]
        branch = analysis["branch"]

        # Checkout the branch
        subprocess.run(["git", "fetch", "origin", f"{branch}:{branch}"])
        subprocess.run(["git", "checkout", branch])

        # Create fix prompt
        fix_prompt = self.create_fix_prompt(analysis["errors"])

        # Run Claude Code to fix
        result = subprocess.run(
            [
                "code",
                "claude",
                "--message",
                fix_prompt,
                "--auto-approve",  # Only if you trust the fixes
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            # Run tests locally
            test_result = subprocess.run(["just", "check"], capture_output=True)

            if test_result.returncode == 0:
                # Commit and push
                subprocess.run(["git", "add", "-A"])
                subprocess.run(
                    [
                        "git",
                        "commit",
                        "-m",
                        f"fix: Auto-fix CI failures for PR #{pr_number}",
                    ]
                )
                subprocess.run(["git", "push", "origin", branch])
                return True

        return False

    def create_fix_prompt(self, errors: List[str]) -> str:
        """Create a prompt for Claude Code to fix the errors"""
        return f"""
Fix the following CI errors:

{chr(10).join(errors)}

Requirements:
1. Only fix the specific errors mentioned
2. Do not modify any other code
3. Ensure all tests pass with 'just check'
4. Keep changes minimal and focused
"""

    def get_job_logs(self, job_id: str) -> str:
        """Get job logs from GitHub Actions."""
        # TODO: Implement via GitHub API
        return ""

    def extract_errors(self, logs: str) -> List[str]:
        """Extract error messages from logs."""
        # TODO: Implement error extraction logic
        return []

    def already_attempted(self, pr_info: Dict[str, Any]) -> bool:
        """Check if we already attempted to fix this PR."""
        # TODO: Implement tracking logic
        return False

    def mark_attempted(self, pr_info: Dict[str, Any]) -> None:
        """Mark PR as attempted."""
        # TODO: Implement tracking logic
        pass

    def comment_on_pr(self, pr_number: int, message: str) -> None:
        """Add comment to PR."""
        pr = self.repo.get_pull(pr_number)
        pr.create_issue_comment(message)

    def monitor_loop(self) -> None:
        """Main monitoring loop"""
        print(f"Starting CI Monitor for {self.repo_name}")

        while True:
            try:
                # Get failed PRs
                failed_prs = self.get_failed_prs()

                if failed_prs:
                    print(f"Found {len(failed_prs)} PRs with CI failures")

                    for pr_info in failed_prs:
                        # Check if we haven't already tried to fix this
                        if not self.already_attempted(pr_info):
                            print(f"Analyzing PR #{pr_info['pr_number']}")

                            analysis = self.analyze_failure(pr_info)

                            if analysis["fixable"]:
                                print(f"Attempting to fix PR #{pr_info['pr_number']}")

                                if self.attempt_fix(analysis):
                                    print(
                                        f"Successfully fixed PR #{pr_info['pr_number']}"
                                    )
                                    self.comment_on_pr(
                                        pr_info["pr_number"],
                                        "🤖 CI failures have been automatically fixed!",
                                    )
                                else:
                                    print(f"Failed to fix PR #{pr_info['pr_number']}")
                                    self.mark_attempted(pr_info)

                # Wait before next check
                time.sleep(300)  # Check every 5 minutes

            except Exception as e:
                print(f"Error in monitor loop: {e}")
                time.sleep(60)  # Wait 1 minute on error


if __name__ == "__main__":
    monitor = CIMonitor()
    monitor.monitor_loop()
