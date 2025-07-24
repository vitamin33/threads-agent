# CI Monitor Service

This service continuously monitors CI failures and automatically attempts to fix them using Claude Code.

## Features

- Monitors GitHub Actions for CI failures
- Automatically checks out failing branches
- Analyzes error logs to identify fixable issues
- Uses Claude Code to generate and apply fixes
- Runs tests locally before pushing
- Creates fix commits with detailed messages
- Comments on PRs with fix status

## Setup

### 1. Environment Variables

Create a `.env` file:

```bash
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx  # GitHub PAT with repo access
ANTHROPIC_API_KEY=sk-ant-xxxxx   # Your Anthropic API key
REPO_OWNER=threads-agent-stack
REPO_NAME=threads-agent
MONITOR_INTERVAL=300             # Check every 5 minutes
AUTO_APPROVE=false               # Require manual approval for fixes
```

### 2. Run with Docker Compose

```bash
docker-compose up -d
```

### 3. Run with Kubernetes

```bash
# Create secrets
kubectl create secret generic ci-monitor-secrets \
  --from-literal=github-token=$GITHUB_TOKEN \
  --from-literal=anthropic-api-key=$ANTHROPIC_API_KEY

# Deploy (enable in values)
helm upgrade --install threads ./chart \
  --set ciMonitor.enabled=true \
  --set ciMonitor.githubToken=$GITHUB_TOKEN \
  --set ciMonitor.anthropicApiKey=$ANTHROPIC_API_KEY
```

## How It Works

1. **Polling**: Checks for failed CI runs every 5 minutes
2. **Analysis**: Downloads logs and extracts error patterns
3. **Filtering**: Only attempts to fix known fixable errors (mypy, imports, tests)
4. **Fixing**: Uses Claude Code API to analyze and fix issues
5. **Validation**: Runs `just check` locally before pushing
6. **Pushing**: Creates atomic fix commits
7. **Tracking**: Maintains state to avoid re-attempting failed fixes

## Supported Fix Types

- Type annotation errors (mypy)
- Import errors
- Simple test failures
- Linting issues
- Missing dependencies
- Syntax errors

## Security Considerations

- Never stores credentials in code
- Uses GitHub token with minimal required permissions
- All fixes are validated locally before pushing
- Can require manual approval (AUTO_APPROVE=false)

## Monitoring

Check logs:
```bash
docker-compose logs -f ci-monitor
```

Or in Kubernetes:
```bash
kubectl logs -f deployment/ci-monitor
```
