# CI Auto-Fix Setup Guide

This guide explains how to set up automatic CI failure detection and fixing using Claude Code.

## Overview

The CI Auto-Fix system consists of:
1. **GitHub Actions workflow** - Detects CI failures
2. **Monitor Service** - Continuously monitors and fixes failures
3. **Claude AI Integration** - Analyzes errors and suggests fixes
4. **Validation System** - Ensures fixes are safe before pushing

## Setup Options

### Option 1: Kubernetes Deployment (Recommended for Production)

1. **Create Secrets**
   ```bash
   kubectl create secret generic ci-monitor-secrets \
     --from-literal=github-token=$GITHUB_TOKEN \
     --from-literal=anthropic-api-key=$ANTHROPIC_API_KEY
   ```

2. **Enable in Helm Values**
   ```yaml
   # chart/values-prod.yaml
   ciMonitor:
     enabled: true
     image:
       repository: ghcr.io/threads-agent-stack/ci-monitor
       tag: latest
     githubToken: "" # Uses secret
     anthropicApiKey: "" # Uses secret
     monitorInterval: "300"
     autoApprove: "false"
   ```

3. **Deploy**
   ```bash
   helm upgrade --install threads ./chart -f chart/values-prod.yaml
   ```

### Option 2: Docker Compose (For Testing)

1. **Create .env File**
   ```bash
   cd services/ci-monitor
   cat > .env << EOF
   GITHUB_TOKEN=ghp_your_token_here
   ANTHROPIC_API_KEY=sk-ant-your_key_here
   REPO_OWNER=threads-agent-stack
   REPO_NAME=threads-agent
   MONITOR_INTERVAL=300
   AUTO_APPROVE=false
   EOF
   ```

2. **Run Service**
   ```bash
   docker-compose up -d
   ```

3. **Check Logs**
   ```bash
   docker-compose logs -f ci-monitor
   ```

### Option 3: GitHub Actions Only

1. **Add Repository Secrets**
   - `ANTHROPIC_API_KEY` - Your Anthropic API key
   - `AUTOFIX_WEBHOOK_URL` - Optional webhook for external service

2. **Enable Workflows**
   - The workflows are automatically active when pushed to the repository
   - They trigger on CI failures in pull requests

## How It Works

### 1. Detection Phase
- GitHub Actions workflow `ci-autofix-trigger.yml` detects when CI fails
- It checks if the failure is from a pull request
- Posts a comment on the PR indicating auto-fix will be attempted

### 2. Analysis Phase
- Monitor service downloads CI logs
- Extracts error messages and patterns
- Determines if errors are auto-fixable (mypy, imports, formatting, etc.)

### 3. Fix Generation Phase
- Uses Claude AI to analyze errors and suggest fixes
- Creates a fix plan based on error types
- Generates specific commands or code changes

### 4. Application Phase
- Clones the failing branch
- Applies fixes using appropriate tools (black, isort, ruff, etc.)
- Runs custom fix scripts for complex issues

### 5. Validation Phase
- Runs `just check` to ensure fixes don't break anything
- Only proceeds if all checks pass

### 6. Push Phase
- Creates atomic commits with detailed messages
- Pushes to the PR branch
- Comments on PR with results

## Security Considerations

### Required Permissions
- **GitHub Token**: `repo` scope for read/write access
- **Anthropic API Key**: Standard API access

### Best Practices
1. Use separate bot account for GitHub token
2. Limit token permissions to specific repositories
3. Set `AUTO_APPROVE=false` to review fixes before applying
4. Monitor service logs for suspicious activity
5. Rotate tokens regularly

## Supported Fix Types

### Automatically Fixable
- ✅ Import errors (missing imports, wrong order)
- ✅ Type annotation errors (mypy)
- ✅ Formatting issues (black, isort)
- ✅ Linting errors (ruff)
- ✅ Simple syntax errors
- ✅ Missing return type annotations

### Not Automatically Fixable
- ❌ Logic errors in tests
- ❌ Complex integration failures
- ❌ Infrastructure issues
- ❌ Security vulnerabilities
- ❌ Breaking API changes

## Monitoring & Debugging

### Check Service Status
```bash
# Kubernetes
kubectl logs -f deployment/ci-monitor
kubectl describe pod -l app=ci-monitor

# Docker
docker-compose logs -f ci-monitor
docker-compose ps
```

### Common Issues

1. **No fixes being applied**
   - Check GitHub token has correct permissions
   - Verify Anthropic API key is valid
   - Look for "not auto-fixable" messages in logs

2. **Fixes failing validation**
   - The fix might be incomplete
   - Dependencies might be missing
   - Manual intervention required

3. **Service not detecting failures**
   - Check workflow names in monitor config
   - Verify GitHub API rate limits
   - Ensure PR association is correct

## Cost Considerations

- **Claude API Usage**: ~$0.01-0.05 per fix attempt
- **GitHub Actions**: Free for public repos, minutes for private
- **Compute**: Minimal (can run on small instance)

## Advanced Configuration

### Custom Fix Patterns
Edit `monitor_v2.py` to add new fixable patterns:
```python
fixable_patterns = [
    'your_custom_error',
    'specific_framework_error'
]
```

### Webhook Integration
Set `AUTOFIX_WEBHOOK_URL` to integrate with external services:
```json
{
  "event": "ci_failure",
  "pr_number": 123,
  "branch": "feature-branch",
  "errors": ["error1", "error2"]
}
```

## Roadmap

### Future Enhancements
- 🚀 Direct Claude Code CLI integration
- 🚀 Learning from successful fixes
- 🚀 Parallel fix attempts
- 🚀 Fix success rate analytics
- 🚀 Integration with more LLMs
- 🚀 Custom fix strategies per project

## Support

For issues or questions:
1. Check service logs first
2. Review this guide
3. Open an issue with logs and error details
