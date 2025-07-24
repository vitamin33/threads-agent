# CI Auto-Fix Setup Guide

This guide explains how to set up and use the improved CI auto-fix workflow that validates fixes and triggers new CI runs.

## Overview

The improved CI auto-fix workflow (`auto-fix-ci-improved.yml`) provides:
- Automatic detection and fixing of CI failures
- Validation with `just check` before committing
- Automatic triggering of new CI runs after fixes
- Clean commits without temporary files

## Setup Instructions

### 1. Create a Personal Access Token (PAT)

The workflow needs a PAT to trigger new CI runs (GitHub prevents the default GITHUB_TOKEN from creating infinite loops).

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a descriptive name: `CI Auto-Fix Token`
4. Set expiration (recommend 90 days for security)
5. Select these scopes:
   - `repo` (all permissions under repo)
   - `workflow` (to trigger workflows)
6. Click "Generate token" and copy the token

### 2. Add the PAT to Repository Secrets

1. Go to your repository: https://github.com/threads-agent-stack/threads-agent
2. Navigate to Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `AUTO_FIX_PAT`
5. Value: Paste your PAT
6. Click "Add secret"

### 3. (Optional) Add Anthropic API Key

For AI-powered fixes (beyond simple formatting):

1. Same location: Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `ANTHROPIC_API_KEY`
4. Value: Your Anthropic API key
5. Click "Add secret"

## How It Works

### Trigger Conditions
The workflow runs when:
- The main CI workflow (`dev-ci`) fails
- The failure is on a pull request (not main branch)

### Fix Process
1. **Analyze Failure**: Downloads and analyzes CI logs
2. **Apply Fixes**: 
   - First tries automatic formatting fixes (ruff, black, isort)
   - If enabled, uses AI for more complex fixes
3. **Validate**: Runs `just check` to ensure fixes are correct
4. **Commit**: Only commits if validation passes
5. **Trigger CI**: Uses PAT to trigger a new CI run
6. **Comment**: Adds a summary comment to the PR

### What Gets Fixed
- Import errors
- Formatting issues (indentation, line length)
- Type annotation problems
- Linting violations
- Import sorting issues

### What Doesn't Get Fixed
- Logic errors
- Test failures due to incorrect assertions
- Missing dependencies in requirements files
- Infrastructure issues

## Comparison with Existing Workflow

| Feature | Existing (`auto-fix-ci.yml`) | Improved (`auto-fix-ci-improved.yml`) |
|---------|------------------------------|---------------------------------------|
| Validation before commit | ❌ No | ✅ Yes (`just check`) |
| Triggers new CI run | ❌ No | ✅ Yes (with PAT) |
| Excludes temp files | ❌ No | ✅ Yes |
| Error analysis | Basic | Advanced patterns |
| Fix validation | Quick checks only | Full validation suite |

## Testing the Workflow

1. Create a test file with intentional errors:
```python
# test_errors.py
import json  # Missing from code
def bad_function(x: int) -> str:
    return x  # Type error
```

2. Commit and push to a PR
3. Watch the CI fail
4. The auto-fix workflow will:
   - Detect the failures
   - Apply fixes
   - Validate with `just check`
   - Commit and push if valid
   - Trigger a new CI run

## Monitoring

Check the Actions tab to see:
- When auto-fix runs
- What fixes were applied
- Whether validation passed
- PR comments with summaries

## Troubleshooting

### Workflow Not Triggering
- Ensure it's a PR, not a direct push to main
- Check that the main CI actually failed (not cancelled)

### No New CI Run After Fix
- Verify AUTO_FIX_PAT secret is set
- Check PAT has `workflow` permission
- Look at workflow logs for errors

### Fixes Not Working
- Some errors require manual intervention
- Check the PR comment for what was attempted
- Review the workflow logs for details

## Security Notes

- PATs expire - set a reminder to renew
- Limit PAT scope to minimum required permissions
- The workflow only runs on PR branches, not main
- All fixes are validated before committing