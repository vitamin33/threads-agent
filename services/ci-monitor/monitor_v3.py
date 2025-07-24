#!/usr/bin/env python3
"""
Enhanced CI Monitor Service v3
- Monitors multiple repositories
- Uses local Claude Code CLI for fixes
- No cloning needed - works with local repos
- Automatically re-runs CI after fixes
"""

import json
import logging
import os
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from github import Github
from github.GithubException import GithubException

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MultiRepoMonitor:
    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")

        self.github = Github(self.github_token)

        # Configuration for multiple repositories
        self.repos_config = self._load_repos_config()
        self.monitor_interval = int(os.getenv("MONITOR_INTERVAL", "60"))
        self.auto_approve = os.getenv("AUTO_APPROVE", "true").lower() == "true"

        # Track attempted fixes to avoid loops
        self.attempted_fixes = {}

        logger.info(f"Initialized monitor for {len(self.repos_config)} repositories")
        logger.info(f"Monitoring interval: {self.monitor_interval}s")
        logger.info(f"Auto-approve fixes: {self.auto_approve}")

    def _load_repos_config(self) -> List[Dict]:
        """Load repository configuration from environment or config file."""
        # Default configuration - can be overridden by env vars or config file
        default_repos = [
            {
                "owner": "threads-agent-stack",
                "name": "threads-agent",
                "local_path": "/Users/vitaliiserbyn/development/threads-agent",
            },
            {
                "owner": "threads-agent-stack",
                "name": "threads-agent",
                "local_path": "/Users/vitaliiserbyn/development/team/jordan-kim/threads-agent",
            },
            {
                "owner": "threads-agent-stack",
                "name": "threads-agent",
                "local_path": "/Users/vitaliiserbyn/development/team/riley-morgan/threads-agent",
            },
        ]

        # Check for environment variable override
        repos_env = os.getenv("MONITORED_REPOS")
        if repos_env:
            try:
                return json.loads(repos_env)
            except json.JSONDecodeError:
                logger.warning("Invalid MONITORED_REPOS JSON, using defaults")

        return default_repos

    def get_failed_ci_runs(self) -> List[Dict]:
        """Get recent failed CI runs from all monitored repositories."""
        failed_runs = []

        for repo_config in self.repos_config:
            try:
                repo = self.github.get_repo(
                    f"{repo_config['owner']}/{repo_config['name']}"
                )
                logger.info(f"Checking {repo_config['owner']}/{repo_config['name']}...")

                # Get recent workflow runs
                workflows = repo.get_workflows()
                for workflow in workflows:
                    if "ci" in workflow.name.lower() or "test" in workflow.name.lower():
                        runs = workflow.get_runs(status="failure")
                        runs_list = (
                            list(runs)[:3] if runs else []
                        )  # Check last 3 failed runs

                        for run in runs_list:
                            # Only process PR runs
                            if run.event == "pull_request":
                                pr_number = self._get_pr_from_run(run)
                                if pr_number and not self._already_attempted(
                                    repo_config, run.id
                                ):
                                    failed_runs.append(
                                        {
                                            "repo_config": repo_config,
                                            "repo": repo,
                                            "run_id": run.id,
                                            "pr_number": pr_number,
                                            "branch": run.head_branch,
                                            "sha": run.head_sha,
                                            "workflow_name": workflow.name,
                                            "failed_at": run.created_at,
                                            "html_url": run.html_url,
                                        }
                                    )
                                    logger.info(
                                        f"Found failed run: PR #{pr_number} in {repo_config['name']}"
                                    )

            except GithubException as e:
                logger.error(f"Error checking {repo_config['name']}: {e}")
                continue

        return failed_runs

    def _get_pr_from_run(self, run) -> Optional[int]:
        """Extract PR number from workflow run."""
        if hasattr(run, "pull_requests") and run.pull_requests:
            return run.pull_requests[0].number
        return None

    def _already_attempted(self, repo_config: Dict, run_id: int) -> bool:
        """Check if we already attempted to fix this run."""
        key = f"{repo_config['owner']}/{repo_config['name']}:{run_id}"
        if key in self.attempted_fixes:
            # Don't retry within 30 minutes
            if datetime.now() - self.attempted_fixes[key] < timedelta(minutes=30):
                return True
        return False

    def _mark_attempted(self, repo_config: Dict, run_id: int):
        """Mark a run as attempted."""
        key = f"{repo_config['owner']}/{repo_config['name']}:{run_id}"
        self.attempted_fixes[key] = datetime.now()

    def analyze_failure(self, failed_run: Dict) -> Dict:
        """Download and analyze CI failure logs."""
        repo = failed_run["repo"]
        run_id = failed_run["run_id"]

        logger.info(f"Analyzing failure for run {run_id}...")

        try:
            # Get workflow run
            run = repo.get_workflow_run(run_id)

            # Download logs
            logs_url = run.logs_url
            response = self.github._Github__requester.requestBlob("GET", logs_url)

            # Extract error patterns
            errors = []
            error_patterns = [
                r"error: .*",
                r"ERROR: .*",
                r"FAILED .*",
                r"AssertionError: .*",
                r"TypeError: .*",
                r"ImportError: .*",
                r"ModuleNotFoundError: .*",
                r"IndentationError: .*",
                r"SyntaxError: .*",
                r"mypy: .* error",
                r"ruff: .* \[.*\]",
                r"black: .* error",
                r"E\d{3} .*",  # Flake8/ruff error codes
            ]

            import io
            import re
            import zipfile

            # Extract logs from zip
            with zipfile.ZipFile(io.BytesIO(response[1])) as zf:
                for filename in zf.namelist():
                    if filename.endswith(".txt"):
                        content = zf.read(filename).decode("utf-8", errors="ignore")
                        for pattern in error_patterns:
                            matches = re.findall(
                                pattern, content, re.MULTILINE | re.IGNORECASE
                            )
                            errors.extend(matches[:10])  # Limit matches per pattern

            # Deduplicate errors
            unique_errors = list(dict.fromkeys(errors))[:50]  # Limit total errors

            return {
                "run_id": run_id,
                "pr_number": failed_run["pr_number"],
                "branch": failed_run["branch"],
                "errors": unique_errors,
                "repo_config": failed_run["repo_config"],
                "workflow_name": failed_run["workflow_name"],
            }

        except Exception as e:
            logger.error(f"Failed to analyze logs: {e}")
            return None

    def fix_with_claude_code(self, analysis: Dict) -> bool:
        """Use Claude Code CLI to fix the errors."""
        repo_config = analysis["repo_config"]
        local_path = repo_config["local_path"]
        branch = analysis["branch"]
        pr_number = analysis["pr_number"]

        logger.info(f"Attempting to fix PR #{pr_number} in {local_path}")

        # Change to repository directory
        original_dir = os.getcwd()
        try:
            os.chdir(local_path)

            # Ensure we're on the right branch
            logger.info(f"Switching to branch {branch}")
            subprocess.run(["git", "fetch", "origin"], check=True, capture_output=True)
            subprocess.run(["git", "checkout", branch], check=True, capture_output=True)
            subprocess.run(
                ["git", "pull", "origin", branch], check=True, capture_output=True
            )

            # Create a focused prompt for Claude Code
            errors_text = "\n".join(analysis["errors"][:20])  # Top 20 errors
            prompt = f"""Fix the CI failures in this repository.

CI Workflow: {analysis['workflow_name']}
PR #{pr_number}

Errors to fix:
{errors_text}

Instructions:
1. Analyze the errors and fix them in the appropriate files
2. Focus on import errors, type errors, formatting issues, and syntax errors
3. Run 'just check' to validate all fixes
4. Only make changes that directly fix the CI errors
5. Do not modify unrelated code

Please fix these errors now."""

            # Run Claude Code CLI
            logger.info("Running Claude Code to fix errors...")

            # Use subprocess to run claude command
            result = subprocess.run(
                ["claude", prompt],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode != 0:
                logger.error(f"Claude Code failed: {result.stderr}")
                return False

            # Check if any files were modified
            git_status = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
            )

            if not git_status.stdout.strip():
                logger.info("No changes made by Claude Code")
                return False

            # Run validation
            logger.info("Running 'just check' to validate fixes...")
            check_result = subprocess.run(
                ["just", "check"], capture_output=True, text=True
            )

            if check_result.returncode != 0:
                logger.error("Validation failed, not committing")
                # Reset changes
                subprocess.run(["git", "checkout", "."], capture_output=True)
                return False

            logger.info("Validation passed! Committing fixes...")

            # Commit changes
            commit_message = f"""fix: Auto-fix CI failures for PR #{pr_number}

Automated fixes by Claude Code for:
- {analysis['workflow_name']} workflow failures
- {len(analysis['errors'])} errors detected and fixed

Validated with 'just check' ✅

Co-authored-by: CI Monitor <ci-monitor@threads-agent.com>"""

            subprocess.run(["git", "add", "-A"], check=True)
            subprocess.run(["git", "commit", "-m", commit_message], check=True)

            # Push with PAT for workflow triggering
            remote_url = f"https://x-access-token:{self.github_token}@github.com/{repo_config['owner']}/{repo_config['name']}.git"
            subprocess.run(
                ["git", "remote", "set-url", "origin", remote_url], check=True
            )
            subprocess.run(["git", "push", "origin", branch], check=True)

            logger.info(f"Successfully pushed fixes to {branch}")

            # Comment on PR
            self._comment_on_pr(repo_config, pr_number, analysis, success=True)

            return True

        except subprocess.TimeoutExpired:
            logger.error("Claude Code timed out")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e}")
            if hasattr(e, "stderr") and e.stderr:
                logger.error(f"Error output: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False
        finally:
            os.chdir(original_dir)

    def _comment_on_pr(
        self, repo_config: Dict, pr_number: int, analysis: Dict, success: bool
    ):
        """Comment on the PR about the fix attempt."""
        try:
            repo = self.github.get_repo(f"{repo_config['owner']}/{repo_config['name']}")
            pr = repo.get_pull(pr_number)

            if success:
                comment = f"""🤖 **CI Auto-Fix Applied**

✅ Successfully fixed CI failures using Claude Code

**Workflow**: {analysis['workflow_name']}
**Errors Fixed**: {len(analysis['errors'])}

The fixes have been validated with `just check` and pushed to the branch.
A new CI run should start automatically.

---
_Local CI Monitor Service with Claude Code_"""
            else:
                comment = f"""🤖 **CI Auto-Fix Attempted**

❌ Unable to automatically fix all CI failures

**Workflow**: {analysis['workflow_name']}
**Errors Detected**: {len(analysis['errors'])}

Manual intervention may be required.

---
_Local CI Monitor Service_"""

            pr.create_issue_comment(comment)

        except Exception as e:
            logger.error(f"Failed to comment on PR: {e}")

    def monitor_loop(self):
        """Main monitoring loop."""
        logger.info("Starting CI monitor loop...")

        while True:
            try:
                # Get failed CI runs
                failed_runs = self.get_failed_ci_runs()

                if not failed_runs:
                    logger.info("No failed CI runs found")
                else:
                    logger.info(f"Found {len(failed_runs)} failed CI runs")

                    for failed_run in failed_runs:
                        # Mark as attempted first to avoid retries
                        self._mark_attempted(
                            failed_run["repo_config"], failed_run["run_id"]
                        )

                        # Analyze failure
                        analysis = self.analyze_failure(failed_run)
                        if not analysis:
                            continue

                        # Fix with Claude Code
                        if self.auto_approve:
                            logger.info(f"Auto-fixing run {failed_run['run_id']}...")
                            self.fix_with_claude_code(analysis)
                        else:
                            logger.info("Skipping auto-fix (auto_approve=false)")

                # Wait before next check
                logger.info(f"Sleeping for {self.monitor_interval} seconds...")
                time.sleep(self.monitor_interval)

            except KeyboardInterrupt:
                logger.info("Received interrupt signal, exiting...")
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(self.monitor_interval)


if __name__ == "__main__":
    monitor = MultiRepoMonitor()
    monitor.monitor_loop()
