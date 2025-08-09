#!/usr/bin/env python3
"""
PR Analysis Deduplication Helper
Prevents multiple analyses on the same PR
"""

import json
import os
import sys
import subprocess
from datetime import datetime
from typing import Dict, Optional, List


def run_gh_command(args: List[str]) -> Optional[str]:
    """Run GitHub CLI command and return output"""
    try:
        result = subprocess.run(
            ["gh"] + args, capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running gh command: {e}")
        return None


def get_existing_analysis_comments(pr_number: int) -> List[Dict]:
    """Get existing PR value analysis comments"""
    result = run_gh_command(["pr", "view", str(pr_number), "--json", "comments"])

    if not result:
        return []

    try:
        data = json.loads(result)
        comments = data.get("comments", [])

        # Filter for bot comments containing our analysis
        analysis_comments = []
        for comment in comments:
            if comment.get("author", {}).get(
                "login"
            ) == "github-actions[bot]" and "Automated PR Value Analysis" in comment.get(
                "body", ""
            ):
                analysis_comments.append(comment)

        return analysis_comments
    except json.JSONDecodeError:
        return []


def get_pr_last_commit(pr_number: int) -> Optional[str]:
    """Get the last commit SHA for a PR"""
    result = run_gh_command(["pr", "view", str(pr_number), "--json", "commits"])

    if not result:
        return None

    try:
        data = json.loads(result)
        commits = data.get("commits", [])
        if commits:
            # Get the last commit
            return commits[-1].get("oid", "")[:7]
    except json.JSONDecodeError:
        pass

    return None


def extract_analysis_sha(comment_body: str) -> Optional[str]:
    """Extract SHA from analysis comment"""
    # Look for the SHA in the metadata line
    lines = comment_body.split("\n")
    for line in lines:
        if "SHA:" in line and "<sub>" in line:
            parts = line.split("SHA:")
            if len(parts) > 1:
                sha = parts[1].split("</sub>")[0].strip()
                return sha
    return None


def should_reanalyze(pr_number: int, force: bool = False) -> bool:
    """Determine if PR should be reanalyzed"""
    if force:
        print(f"Force flag set - will reanalyze PR #{pr_number}")
        return True

    # Get existing analysis comments
    existing_comments = get_existing_analysis_comments(pr_number)

    if not existing_comments:
        print(f"No existing analysis found for PR #{pr_number}")
        return True

    # Get current PR commit SHA
    current_sha = get_pr_last_commit(pr_number)
    if not current_sha:
        print(f"Could not determine current SHA for PR #{pr_number}")
        return True

    # Check if any existing analysis is for the current SHA
    for comment in existing_comments:
        comment_sha = extract_analysis_sha(comment.get("body", ""))
        if comment_sha == current_sha:
            print(f"Analysis already exists for PR #{pr_number} at SHA {current_sha}")
            print(f"Comment ID: {comment.get('id')}")
            return False

    print(f"Existing analyses found but none match current SHA {current_sha}")
    return True


def delete_old_analyses(pr_number: int, keep_latest: bool = False):
    """Delete old analysis comments"""
    existing_comments = get_existing_analysis_comments(pr_number)

    if not existing_comments:
        return

    # Sort by creation date
    existing_comments.sort(key=lambda x: x.get("createdAt", ""), reverse=True)

    # Determine which comments to delete
    comments_to_delete = existing_comments[1:] if keep_latest else existing_comments

    for comment in comments_to_delete:
        comment_id = comment.get("databaseId")
        if comment_id:
            print(f"Deleting old analysis comment {comment_id}")
            run_gh_command(
                [
                    "api",
                    "-X",
                    "DELETE",
                    f"/repos/{os.environ.get('GITHUB_REPOSITORY', '')}/issues/comments/{comment_id}",
                ]
            )


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: pr-analysis-dedupe.py <pr_number> [--force] [--delete-old]")
        sys.exit(1)

    pr_number = int(sys.argv[1])
    force = "--force" in sys.argv
    delete_old = "--delete-old" in sys.argv

    # Check if we need GitHub token
    if not os.environ.get("GH_TOKEN") and not os.environ.get("GITHUB_TOKEN"):
        print("Warning: No GitHub token found. Some operations may fail.")

    # Delete old analyses if requested
    if delete_old:
        delete_old_analyses(pr_number, keep_latest=False)

    # Check if we should analyze
    should_analyze = should_reanalyze(pr_number, force)

    # Output for GitHub Actions
    if os.environ.get("GITHUB_ACTIONS"):
        print(f"::set-output name=should_analyze::{str(should_analyze).lower()}")

    # Exit with appropriate code
    sys.exit(0 if should_analyze else 1)


if __name__ == "__main__":
    main()
