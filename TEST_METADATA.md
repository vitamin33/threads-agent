# Test Metadata Storage

This file tests that achievement metadata is properly stored when PRs are merged.

## Test Details
- Testing metadata storage fix
- Verifying GitHub run URL and PR URL are captured
- Checking that metadata_json field is populated

## Expected Metadata Fields
- `github_run_url`: Full URL to the GitHub Actions run
- `pr_url`: URL to the PR (if available)
- `collected_by`: Should be "github-actions"