# Claude Code Auto-Fix CI Guide

## Overview

The Claude Code Auto-Fix CI system automatically detects and fixes CI failures in pull requests using AI-powered code analysis and repair. When CI fails on a PR, Claude Code analyzes the failure logs and attempts to fix the issues automatically.

## Features

- 🤖 **Automatic CI Failure Detection**: Triggers when Dev CI workflow fails on a PR
- 🔍 **Intelligent Analysis**: Claude Code analyzes error logs and identifies root causes
- 🛠️ **Targeted Fixes**: Makes minimal, focused changes to fix only the failing issues
- ✅ **Validation**: Runs quick checks on fixes before committing
- 💬 **PR Updates**: Comments on the PR with fix details and results
- 📊 **Monitoring**: Track success rates and common fix patterns

## How It Works

1. **Trigger**: When the Dev CI workflow fails on a pull request
2. **Analysis**: Downloads and analyzes CI failure logs
3. **Fix Generation**: Claude Code generates targeted fixes for identified issues
4. **Validation**: Runs quick linting and tests on changed files
5. **Commit & Push**: Creates a fix commit and pushes to the PR branch
6. **Monitoring**: Tracks the new CI run to verify the fix worked

## Supported Fix Types

- ✅ **Test Failures**: Unit and integration test fixes
- ✅ **Linting Errors**: Ruff, Black, isort formatting issues
- ✅ **Type Checking**: MyPy type annotation fixes
- ✅ **Import Errors**: Missing or incorrect imports
- ✅ **Syntax Errors**: Python syntax issues
- ✅ **Configuration Issues**: Common config problems

## Setup

### 1. Add GitHub Secret

Add your Anthropic API key as a GitHub secret:

```bash
gh secret set ANTHROPIC_API_KEY --body "your-anthropic-api-key"
```

### 2. Enable the Workflow

The workflow is automatically active once merged to the repository. No additional setup required!

### 3. Configure Settings (Optional)

Edit `.github/claude-code-config.yml` to customize:

```yaml
auto_fix:
  enabled: true
  fix_types:
    test_failures: true
    linting_errors: true
    # ... customize which fixes to attempt

safety:
  max_files_changed: 10  # Limit scope of changes
  max_lines_changed: 500
  protected_files:       # Files that won't be auto-fixed
    - ".github/workflows/*"
```

## Usage

### Automatic Mode

Simply create a PR and push code. If CI fails, the auto-fix will trigger automatically:

1. Create a PR with your changes
2. If CI fails, wait ~2-3 minutes
3. Check the PR comments for fix details
4. Review the automated fix commit
5. Re-approve if the fixes look good

### Monitoring

Use the monitoring script to track auto-fix performance:

```bash
# Check last 7 days of auto-fix activity
./scripts/monitor-auto-fix.sh

# Check last 30 days
./scripts/monitor-auto-fix.sh 30
```

### Manual Trigger (Advanced)

You can manually trigger the auto-fix workflow:

```bash
gh workflow run auto-fix-ci.yml --ref your-branch
```

## Example PR Comment

When Claude Code fixes CI failures, it comments on the PR:

---

## 🤖 Claude Code CI Auto-Fix

✅ **CI failures detected and fixed automatically!**

### Changes Made:
```
services/orchestrator/tests/test_api.py
services/common/metrics.py
```

✅ Quick validation passed. The CI should now pass.

### Original Errors Fixed:
```
AssertionError: Expected 200 but got 404
ImportError: cannot import name 'record_metric' from 'services.common.metrics'
mypy: error: Missing return statement
```

Please review the automated fixes and re-run CI to confirm.

---

## Safety Features

The auto-fix system includes several safety mechanisms:

1. **Limited Scope**: Won't change more than 10 files or 500 lines
2. **Protected Files**: Critical configs and workflows are protected
3. **Validation**: Runs basic checks before committing
4. **Human Review**: Always requires PR approval before merging
5. **Audit Trail**: All changes are clearly marked in commits

## Troubleshooting

### Auto-Fix Not Triggering

1. Check if the workflow is enabled in Actions tab
2. Verify the PR is from a branch (not a fork)
3. Ensure ANTHROPIC_API_KEY secret is set

### Fix Failed

Check the PR comment for details. Common reasons:
- Complex failures requiring human intervention
- Protected files need changes
- Validation checks failed

### Monitoring Issues

```bash
# Check GitHub CLI authentication
gh auth status

# View workflow runs manually
gh run list --workflow auto-fix-ci.yml

# Check specific run logs
gh run view RUN_ID --log
```

## Best Practices

1. **Review All Fixes**: Always review automated changes before merging
2. **Add Test Coverage**: Prevent recurring issues with better tests
3. **Update Config**: Tune the configuration based on your needs
4. **Monitor Patterns**: Use monitoring to identify common issues
5. **Provide Context**: Clear commit messages help Claude Code understand the codebase

## Metrics and Success Tracking

The system tracks:
- Total auto-fix attempts
- Success/failure rates
- Common fix patterns
- Time saved on CI fixes
- Most problematic files/tests

View metrics:
```bash
cat .metrics/auto-fix-stats.json | jq '.'
```

## Security Considerations

- API keys are stored as encrypted GitHub secrets
- Claude Code only has access to the repository code
- All changes go through standard PR review process
- No direct commits to protected branches
- Audit log of all automated changes

## FAQ

**Q: Will it fix all CI failures?**
A: No, it focuses on common, straightforward fixes. Complex logic errors require human intervention.

**Q: Can it break my code?**
A: The system is designed to make minimal, safe changes. Validation checks and PR reviews add safety layers.

**Q: How much does it cost?**
A: Each fix uses Claude API tokens. Typical fixes cost $0.01-0.05.

**Q: Can I disable it for specific PRs?**
A: Yes, add `[skip-autofix]` to your PR title.

**Q: Does it work with forked PRs?**
A: No, for security reasons it only works on branches within the repository.

## Future Enhancements

- [ ] Support for more languages (currently Python-focused)
- [ ] Integration with more linters and tools
- [ ] Learning from successful fixes to improve accuracy
- [ ] Slack/Discord notifications
- [ ] Cost tracking and optimization
