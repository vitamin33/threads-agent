#!/usr/bin/env python3
"""Script to track git commit as achievement - called by git hook."""

import os
import subprocess
import sys
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def main():
    try:
        from services.achievement_collector.services.git_tracker import GitCommitTracker

        # Get commit information
        commit_hash = (
            subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
        )
        commit_message = (
            subprocess.check_output(["git", "log", "-1", "--pretty=%B"])
            .decode()
            .strip()
        )
        author_name = (
            subprocess.check_output(["git", "log", "-1", "--pretty=%an"])
            .decode()
            .strip()
        )
        author_email = (
            subprocess.check_output(["git", "log", "-1", "--pretty=%ae"])
            .decode()
            .strip()
        )

        # Get file statistics
        try:
            diff_output = subprocess.check_output(
                ["git", "diff", "HEAD~1", "HEAD", "--numstat"]
            ).decode()
        except subprocess.CalledProcessError:
            # First commit in repo
            diff_output = subprocess.check_output(
                ["git", "diff-tree", "--root", "HEAD", "--numstat"]
            ).decode()

        files_changed = 0
        lines_added = 0
        lines_deleted = 0
        files = []

        for line in diff_output.strip().split("\n"):
            if line and "\t" in line:
                parts = line.split("\t")
                if len(parts) == 3:
                    added = int(parts[0]) if parts[0] != "-" else 0
                    deleted = int(parts[1]) if parts[1] != "-" else 0
                    filename = parts[2]

                    files_changed += 1
                    lines_added += added
                    lines_deleted += deleted
                    files.append({"name": filename, "added": added, "deleted": deleted})

        # Create commit data
        commit_data = {
            "hash": commit_hash,
            "author": author_name,
            "email": author_email,
            "timestamp": int(datetime.now().timestamp()),
            "message": commit_message,
            "files_changed": files_changed,
            "lines_added": lines_added,
            "lines_deleted": lines_deleted,
            "files": files,
        }

        # Check if significant
        tracker = GitCommitTracker()
        if tracker._is_significant_commit(commit_data):
            # Create achievement synchronously
            import asyncio

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(tracker._create_commit_achievement(commit_data))
            print(f"✅ Achievement created for commit {commit_hash[:8]}")
        else:
            print(f"ℹ️  Commit {commit_hash[:8]} not significant enough for achievement")

    except Exception as e:
        # Don't break git workflow if achievement tracking fails
        print(f"⚠️  Achievement tracking failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
