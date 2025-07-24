# CI Monitor Service - Local Auto-Fix System

## Overview

The CI Monitor Service automatically fixes CI failures across all teammate repositories using Claude Code. It runs locally on your machine and monitors GitHub for CI failures, then uses Claude to analyze and fix them.

## Features

- ✅ **Multi-Repository Support**: Monitors all 3 teammate workspaces simultaneously
- ✅ **Local Execution**: Works directly with your local files (no cloning)
- ✅ **Claude Code Integration**: Uses your local Claude CLI for intelligent fixes
- ✅ **Validation**: Runs `just check` before committing any fixes
- ✅ **Auto CI Re-run**: Uses PAT to trigger new CI runs after fixes
- ✅ **PR Comments**: Adds informative comments about fix attempts

## Quick Start

```bash
# Start the monitor
./start_ci_monitor.sh

# Or run directly
python3 services/ci-monitor/run_monitor_host.py
```

## Configuration

The monitor is configured to watch:
1. **Main Repository**: `/Users/vitaliiserbyn/development/threads-agent`
2. **Jordan Kim's Repository**: `/Users/vitaliiserbyn/development/team/jordan-kim/threads-agent`
3. **Riley Morgan's Repository**: `/Users/vitaliiserbyn/development/team/riley-morgan/threads-agent`

## How It Works

1. **Detection**: Polls GitHub every 60 seconds for failed CI runs on PRs
2. **Analysis**: Downloads and analyzes CI logs to identify errors
3. **Fix**: Runs Claude Code with the errors to generate fixes
4. **Validation**: Executes `just check` to ensure fixes are correct
5. **Commit**: If validation passes, commits and pushes the fixes
6. **Re-run**: Triggers a new CI run using your PAT

## Environment Variables

- `GITHUB_TOKEN`: Your PAT with repo and workflow permissions (default: provided)
- `ANTHROPIC_API_KEY`: Your Anthropic API key (uses system environment)
- `MONITOR_INTERVAL`: Seconds between checks (default: 60)
- `AUTO_APPROVE`: Whether to auto-fix without confirmation (default: true)

## Monitoring Output

```
2025-07-24 14:27:27 - INFO - Initialized monitor for 3 repositories
2025-07-24 14:27:28 - INFO - Checking threads-agent-stack/threads-agent...
2025-07-24 14:27:35 - INFO - Found failed run: PR #44 in threads-agent
2025-07-24 14:27:51 - INFO - Analyzing failure for run 16493339765...
```

## Benefits vs GitHub Actions

| Aspect | Local Monitor | GitHub Actions |
|--------|--------------|----------------|
| Speed | ~30 seconds | 2-3 minutes |
| Cloning | Not needed | Every time |
| Environment | Shared local | Isolated |
| Resources | Your machine | GitHub runners |
| Multiple repos | Single service | Per-repo setup |

## Troubleshooting

### Monitor not detecting failures
- Check GitHub token has correct permissions
- Verify repositories are configured correctly
- Check network connectivity to GitHub

### Claude Code not fixing
- Ensure `claude` CLI is available in PATH
- Check Anthropic API key is set
- Review error logs for specific issues

### Fixes not validating
- Ensure `just` command is available
- Check all dependencies are installed
- Review the specific validation errors

## Security

- Uses PAT for GitHub operations (never commits secrets)
- Runs with your local user permissions
- Only modifies files to fix CI errors
- All changes are validated before committing