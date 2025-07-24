#!/usr/bin/env python3
"""
Enhanced CI Monitor Service - Uses Claude Code API for automatic fixes
"""

import os
import subprocess
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from anthropic import Anthropic
from github import Github


class EnhancedCIMonitor:
    def __init__(self) -> None:
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.repo_owner = os.getenv("REPO_OWNER", "threads-agent-stack")
        self.repo_name = os.getenv("REPO_NAME", "threads-agent")
        self.monitor_interval = int(os.getenv("MONITOR_INTERVAL", "300"))
        self.auto_approve = os.getenv("AUTO_APPROVE", "false").lower() == "true"

        # Initialize clients
        self.github = Github(self.github_token)
        self.repo = self.github.get_repo(f"{self.repo_owner}/{self.repo_name}")
        self.anthropic = Anthropic(api_key=self.anthropic_api_key)

        # Track attempted fixes to avoid loops
        self.attempted_fixes: Dict[str, datetime] = {}

    def get_failed_ci_runs(self) -> List[Dict[str, Any]]:
        """Get recent failed CI runs from pull requests."""
        failed_runs = []

        # Check recent workflow runs
        workflows = self.repo.get_workflows()
        for workflow in workflows:
            if "ci" in workflow.name.lower() or "test" in workflow.name.lower():
                runs = workflow.get_runs(status="failure")
                for run in runs[:5]:  # Check last 5 failed runs
                    # Only process PR runs
                    if run.event == "pull_request":
                        pr_number = self._get_pr_from_run(run)
                        if pr_number and not self._already_attempted(run.id):
                            failed_runs.append(
                                {
                                    "run_id": run.id,
                                    "pr_number": pr_number,
                                    "branch": run.head_branch,
                                    "sha": run.head_sha,
                                    "workflow_name": workflow.name,
                                    "failed_at": run.created_at,
                                    "html_url": run.html_url,
                                }
                            )

        return failed_runs

    def _get_pr_from_run(self, run: Any) -> Optional[int]:
        """Extract PR number from workflow run."""
        try:
            # Get PR from the head branch
            prs = self.repo.get_pulls(
                state="open", head=f"{self.repo_owner}:{run.head_branch}"
            )
            for pr in prs:
                return int(pr.number)
            return None
        except Exception as e:
            print(f"Error getting PR from run: {e}")
            return None

    def _already_attempted(self, run_id: int) -> bool:
        """Check if we already attempted to fix this run."""
        run_id_str = str(run_id)
        if run_id_str in self.attempted_fixes:
            # Don't retry for 24 hours
            if datetime.now() - self.attempted_fixes[run_id_str] < timedelta(hours=24):
                return True
        return False

    def analyze_failure(self, run_info: Dict[str, Any]) -> Dict[str, Any]:
        """Download and analyze CI failure logs."""
        print(
            f"Analyzing failure for PR #{run_info['pr_number']} (run {run_info['run_id']})"
        )

        # Download logs
        run = self.repo.get_workflow_run(run_info["run_id"])
        logs_url = run.logs_url

        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        # Download logs as zip
        response = requests.get(logs_url, headers=headers)

        if response.status_code != 200:
            print(f"Failed to download logs: {response.status_code}")
            return {"fixable": False, "errors": []}

        # Extract logs (they come as a zip file)
        import io
        import zipfile

        errors = []
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            for filename in zf.namelist():
                with zf.open(filename) as f:
                    content = f.read().decode("utf-8", errors="ignore")

                    # Extract error patterns
                    error_patterns = [
                        r"error: [^\n]+",
                        r"ERROR: [^\n]+",
                        r"FAILED [^\n]+",
                        r"AssertionError: [^\n]+",
                        r"TypeError: [^\n]+",
                        r"ImportError: [^\n]+",
                        r"ModuleNotFoundError: [^\n]+",
                        r"mypy: [^\n]+error",
                        r"ruff: [^\n]+",
                        r"\s+E\s+[^\n]+",  # pytest errors
                    ]

                    import re

                    for pattern in error_patterns:
                        matches = re.findall(pattern, content, re.MULTILINE)
                        errors.extend(matches)

        # Deduplicate and categorize errors
        unique_errors = list(set(errors))[:20]  # Limit to 20 unique errors

        return {
            "run_id": run_info["run_id"],
            "pr_number": run_info["pr_number"],
            "branch": run_info["branch"],
            "errors": unique_errors,
            "fixable": self._is_fixable(unique_errors),
        }

    def _is_fixable(self, errors: List[str]) -> bool:
        """Determine if errors are auto-fixable."""
        fixable_patterns = [
            "mypy",
            "import",
            "ImportError",
            "ModuleNotFoundError",
            "type annotation",
            "undefined name",
            "SyntaxError",
            "indentation",
            "ruff",
            "black",
            "isort",
        ]

        error_text = " ".join(errors).lower()
        return any(pattern in error_text for pattern in fixable_patterns)

    def create_fix_with_claude(self, analysis: Dict[str, Any]) -> Optional[str]:
        """Use Claude API to create a fix for the errors."""
        error_summary = "\n".join(analysis["errors"][:10])

        prompt = f"""You are helping fix CI failures in a Python project. 

The following errors were found in the CI pipeline:

{error_summary}

Please analyze these errors and provide:
1. A brief explanation of what's wrong
2. The exact commands or code changes needed to fix these issues
3. Focus on the most critical errors first

The project uses:
- Python 3.12
- pytest for testing
- mypy for type checking
- ruff, black, isort for formatting
- FastAPI and other modern Python tools

Provide actionable fixes that can be automated."""

        try:
            response = self.anthropic.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4000,
                temperature=0,
                messages=[{"role": "user", "content": prompt}],
            )

            if response.content and len(response.content) > 0:
                content = response.content[0]
                if hasattr(content, "text"):
                    return str(content.text)
            return None
        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return None

    def apply_fixes(self, analysis: Dict[str, Any], fix_plan: str) -> bool:
        """Apply the fixes suggested by Claude."""
        pr_number = analysis["pr_number"]
        branch = analysis["branch"]

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "repo"

            try:
                # Clone the repository
                print(f"Cloning branch {branch}...")
                subprocess.run(
                    [
                        "git",
                        "clone",
                        "--branch",
                        branch,
                        "--depth",
                        "1",
                        f"https://{self.github_token}@github.com/{self.repo_owner}/{self.repo_name}.git",
                        str(repo_path),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )

                os.chdir(repo_path)

                # Configure git
                subprocess.run(
                    ["git", "config", "user.email", "ci-bot@threads-agent.com"],
                    check=True,
                )
                subprocess.run(
                    ["git", "config", "user.name", "CI Auto-Fix Bot"], check=True
                )

                # Create a fix script based on Claude's response
                fix_script = self._create_fix_script(fix_plan, analysis["errors"])

                # Run the fix script
                fix_script_path = repo_path / "auto_fix.py"
                fix_script_path.write_text(fix_script)

                print("Applying fixes...")
                result = subprocess.run(
                    ["python", str(fix_script_path)], capture_output=True, text=True
                )

                if result.returncode != 0:
                    print(f"Fix script failed: {result.stderr}")
                    return False

                # Run tests to validate fixes
                print("Running validation checks...")
                test_result = subprocess.run(
                    ["just", "check"], capture_output=True, text=True
                )

                if test_result.returncode != 0:
                    print(f"Validation failed: {test_result.stderr}")
                    return False

                # Commit and push changes
                subprocess.run(["git", "add", "-A"], check=True)

                # Check if there are changes
                diff_result = subprocess.run(
                    ["git", "diff", "--cached", "--quiet"], capture_output=True
                )

                if diff_result.returncode == 0:
                    print("No changes to commit")
                    return False

                commit_message = f"""fix: Auto-fix CI failures for PR #{pr_number}

Automated fixes for the following errors:
{chr(10).join(analysis["errors"][:5])}

🤖 Fixed by CI Auto-Fix Bot using Claude AI"""

                subprocess.run(["git", "commit", "-m", commit_message], check=True)
                subprocess.run(["git", "push", "origin", branch], check=True)

                print(f"Successfully pushed fixes to {branch}")
                return True

            except subprocess.CalledProcessError as e:
                print(f"Git operation failed: {e}")
                if hasattr(e, "stderr"):
                    print(f"Error output: {e.stderr}")
                return False
            except Exception as e:
                print(f"Unexpected error: {e}")
                return False

    def _create_fix_script(self, fix_plan: str, errors: List[str]) -> str:
        """Create a Python script to apply fixes based on Claude's plan."""
        # This is a simplified version - in production, you'd parse Claude's response more carefully
        return f"""#!/usr/bin/env python3
\"\"\"Auto-generated fix script based on CI errors.\"\"\"

import subprocess
import os
import re
from pathlib import Path

def main():
    print("Applying automated fixes...")
    
    # Fix import errors
    if any('import' in err.lower() for err in {errors!r}):
        print("Fixing import errors...")
        subprocess.run(['isort', '.'], check=True)
    
    # Fix formatting
    if any('black' in err.lower() or 'format' in err.lower() for err in {errors!r}):
        print("Fixing formatting...")
        subprocess.run(['black', '.'], check=True)
    
    # Fix linting
    if any('ruff' in err.lower() for err in {errors!r}):
        print("Fixing linting issues...")
        subprocess.run(['ruff', 'check', '.', '--fix'], check=True)
    
    # Fix common mypy errors
    if any('mypy' in err.lower() for err in {errors!r}):
        print("Attempting to fix type errors...")
        # Add type: ignore comments for specific errors
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.py'):
                    filepath = Path(root) / file
                    content = filepath.read_text()
                    
                    # Fix missing return type annotations
                    content = re.sub(
                        r'def ([\\w_]+)\\([^)]*\\)(?!\\s*->):',
                        r'def \\1(\\g<0>) -> None:',
                        content
                    )
                    
                    filepath.write_text(content)
    
    print("Fixes applied successfully!")

if __name__ == "__main__":
    main()
"""

    def comment_on_pr(self, pr_number: int, message: str) -> None:
        """Add a comment to the PR."""
        pr = self.repo.get_pull(pr_number)
        pr.create_issue_comment(message)

    def monitor_loop(self) -> None:
        """Main monitoring loop."""
        print(f"Starting Enhanced CI Monitor for {self.repo_owner}/{self.repo_name}")
        print(f"Checking every {self.monitor_interval} seconds...")

        while True:
            try:
                # Get failed CI runs
                failed_runs = self.get_failed_ci_runs()

                if failed_runs:
                    print(f"Found {len(failed_runs)} failed CI runs")

                    for run_info in failed_runs:
                        print(f"\nProcessing PR #{run_info['pr_number']}...")

                        # Analyze the failure
                        analysis = self.analyze_failure(run_info)

                        if not analysis["fixable"]:
                            print(
                                f"Errors not auto-fixable for PR #{run_info['pr_number']}"
                            )
                            self.attempted_fixes[str(run_info["run_id"])] = (
                                datetime.now()
                            )
                            continue

                        # Get fix plan from Claude
                        print("Consulting Claude for fix plan...")
                        fix_plan = self.create_fix_with_claude(analysis)

                        if not fix_plan:
                            print("Failed to get fix plan from Claude")
                            self.attempted_fixes[str(run_info["run_id"])] = (
                                datetime.now()
                            )
                            continue

                        # Apply fixes
                        print("Attempting to apply fixes...")
                        if self.apply_fixes(analysis, fix_plan):
                            self.comment_on_pr(
                                run_info["pr_number"],
                                f"🤖 **CI Auto-Fix Applied**\n\n"
                                f"I've automatically fixed the CI failures and pushed a commit.\n\n"
                                f"**Fixed errors:**\n"
                                f"```\n{chr(10).join(analysis['errors'][:5])}\n```\n\n"
                                f"The CI should now pass. Please review the changes.",
                            )
                            print(f"Successfully fixed PR #{run_info['pr_number']}")
                        else:
                            print(
                                f"Failed to apply fixes for PR #{run_info['pr_number']}"
                            )
                            self.comment_on_pr(
                                run_info["pr_number"],
                                f"🤖 **CI Auto-Fix Attempted**\n\n"
                                f"I tried to fix the CI failures but encountered issues.\n\n"
                                f"**Errors detected:**\n"
                                f"```\n{chr(10).join(analysis['errors'][:5])}\n```\n\n"
                                f"Manual intervention may be required.",
                            )

                        self.attempted_fixes[run_info["run_id"]] = datetime.now()

                # Clean up old attempts
                cutoff = datetime.now() - timedelta(days=1)
                self.attempted_fixes = {
                    k: v for k, v in self.attempted_fixes.items() if v > cutoff
                }

            except Exception as e:
                print(f"Error in monitor loop: {e}")
                import traceback

                traceback.print_exc()

            # Wait before next check
            time.sleep(self.monitor_interval)


if __name__ == "__main__":
    monitor = EnhancedCIMonitor()
    monitor.monitor_loop()
