# Achievement Collector Setup Guide

## Overview

The Achievement Collector is an automated system that tracks, analyzes, and showcases your professional accomplishments from the Threads-Agent Stack project. It captures metrics from Git commits, GitHub PRs, CI/CD runs, and production deployments to build a comprehensive portfolio.

## Quick Start

### 1. Local Development Setup

```bash
# Enable achievement collector in your local environment
just dev-start

# The service will be available at:
# http://localhost:8080/achievements
```

### 2. Configure GitHub Webhooks

1. Go to your GitHub repository settings
2. Navigate to Webhooks → Add webhook
3. Configure:
   - **Payload URL**: `https://your-domain.com/webhooks/github`
   - **Content type**: `application/json`
   - **Secret**: Generate with `openssl rand -hex 32`
   - **Events**: Select:
     - Pull requests
     - Pushes
     - Workflow runs
     - Issues

4. Update your Helm values:
```yaml
achievementCollector:
  enabled: true
  github:
    webhookSecret: "your-generated-secret"
    token: "ghp_your_github_personal_access_token"
```

### 3. Database Setup

The service automatically creates tables on startup. For production:

```bash
# Run migrations
cd services/achievement_collector
alembic upgrade head
```

## API Usage

### Create Achievement Manually

```bash
curl -X POST http://localhost:8000/achievements/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Optimized CI Pipeline",
    "description": "Reduced build time by 80%",
    "category": "optimization",
    "started_at": "2024-01-15T10:00:00",
    "completed_at": "2024-01-20T18:00:00",
    "source_type": "manual",
    "tags": ["ci/cd", "optimization"],
    "skills_demonstrated": ["GitHub Actions", "Docker"]
  }'
```

### Analyze Achievement

```bash
curl -X POST http://localhost:8000/analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "achievement_id": 1,
    "analyze_impact": true,
    "analyze_technical": true,
    "generate_summary": true
  }'
```

### Generate Portfolio

```bash
# Markdown format
curl -X POST http://localhost:8000/portfolio/generate \
  -H "Content-Type: application/json" \
  -d '{
    "format": "markdown",
    "portfolio_ready_only": true,
    "min_impact_score": 70
  }'

# Download generated portfolio
curl -O http://localhost:8000/portfolio/download/1
```

## Automated Tracking

### GitHub Integration

The service automatically creates achievements for:

1. **Merged Pull Requests**
   - Captures PR metrics, review time, code changes
   - Extracts skills from file types and PR content
   - Categories based on PR labels and title

2. **Successful Deployments**
   - Tracks deployment workflows
   - Records deployment duration and success rate
   - Links to production changes

3. **Closed Issues**
   - Bug fixes and feature implementations
   - Time to resolution metrics
   - Team collaboration tracking

### Example: PR Achievement

When you merge a PR, the system automatically:

1. Creates an achievement record
2. Analyzes the changes for impact
3. Extracts demonstrated skills
4. Calculates business value
5. Generates AI summaries

```json
{
  "title": "PR #45: Implement CI optimizations",
  "category": "optimization",
  "impact_score": 85.5,
  "business_value": 50000,
  "time_saved_hours": 40,
  "skills_demonstrated": ["GitHub Actions", "Docker", "Python"],
  "ai_summary": "Successfully optimized CI pipeline, reducing build times by 80% and saving 40 developer hours per month"
}
```

## Portfolio Templates

### Executive Summary
```bash
curl -X POST http://localhost:8000/portfolio/templates/executive_summary
```
- PDF format
- Top 10 achievements
- High impact only (70+ score)
- Business metrics focus

### Technical Portfolio
```bash
curl -X POST http://localhost:8000/portfolio/templates/technical_portfolio
```
- Markdown format
- Feature and architecture focus
- Detailed technical analysis
- Code examples included

### Full Archive
```bash
curl -X POST http://localhost:8000/portfolio/templates/full_archive
```
- JSON format
- All achievements
- Complete metrics data
- Machine-readable format

## Metrics and Impact Scoring

### Impact Score Calculation (0-100)
- **Business Value** (40 points max)
  - $100k+ = 40 points
  - $50k+ = 30 points
  - $10k+ = 20 points
  - $1k+ = 10 points

- **Time Saved** (30 points max)
  - 100+ hours/month = 30 points
  - 50+ hours/month = 20 points
  - 10+ hours/month = 10 points

- **Category Bonus** (20 points max)
  - Architecture = 20 points
  - Optimization = 18 points
  - Security = 15 points
  - Feature = 15 points

- **Evidence** (10 points max)
  - Before/after metrics = 5 points
  - Screenshots/logs = 5 points

### Complexity Score Calculation (0-100)
- Duration (30 points max)
- Skills demonstrated (30 points max)
- Category complexity (20 points max)
- Technical analysis depth (20 points max)

## Production Deployment

### Kubernetes Setup

1. Create secrets:
```bash
kubectl create secret generic achievement-collector-secrets \
  --from-literal=github-webhook-secret="your-secret" \
  --from-literal=github-token="ghp_your_token" \
  --from-literal=openai-api-key="sk-your-key"
```

2. Enable in production values:
```yaml
achievementCollector:
  enabled: true
  replicas: 2
  ingress:
    enabled: true
    host: achievements.your-domain.com
    annotations:
      cert-manager.io/cluster-issuer: letsencrypt-prod
    tls:
      - secretName: achievements-tls
        hosts:
          - achievements.your-domain.com
```

3. Deploy:
```bash
helm upgrade --install threads-agent ./chart \
  -f chart/values-prod.yaml
```

### Monitoring

The service exposes Prometheus metrics at `/metrics`:

- `achievements_created_total` - Total achievements created
- `achievements_analyzed_total` - Total achievements analyzed
- `portfolio_generations_total` - Total portfolios generated
- `webhook_events_processed_total` - Webhook events by type
- `analysis_duration_seconds` - AI analysis timing

### Backup and Recovery

1. Database backups:
```bash
# Backup achievements
pg_dump -h localhost -U postgres -d achievement_collector \
  -t achievements -t git_commits -t github_prs \
  > achievements_backup.sql

# Restore
psql -h localhost -U postgres -d achievement_collector < achievements_backup.sql
```

2. Portfolio backups:
- Generated portfolios are stored in persistent volume
- Configure S3/GCS backup for long-term storage

## Troubleshooting

### Common Issues

1. **Webhooks not processing**
   - Check webhook secret configuration
   - Verify GitHub webhook delivery logs
   - Check service logs: `kubectl logs deploy/achievement-collector`

2. **AI analysis failing**
   - Verify OpenAI API key is set
   - Check API rate limits
   - Review error logs for specific failures

3. **Portfolio generation errors**
   - Ensure sufficient achievements exist
   - Check persistent volume has space
   - Verify template rendering

### Debug Commands

```bash
# Check service health
curl http://localhost:8000/health

# View webhook status
curl http://localhost:8000/webhooks/health

# Test GitHub signature verification
curl -X POST http://localhost:8000/webhooks/github \
  -H "X-GitHub-Event: ping" \
  -H "X-Hub-Signature-256: sha256=test" \
  -d '{"zen": "Design for failure."}'

# View recent achievements
curl "http://localhost:8000/achievements/?per_page=10&sort_by=completed_at"
```

## Best Practices

1. **Regular Analysis**
   - Run batch analysis weekly
   - Review AI-generated summaries
   - Update portfolio readiness flags

2. **Portfolio Maintenance**
   - Generate monthly snapshots
   - Archive old achievements
   - Update impact scores with real data

3. **Security**
   - Rotate webhook secrets quarterly
   - Use read-only GitHub tokens
   - Restrict API access in production

4. **Performance**
   - Limit webhook processing concurrency
   - Cache AI analysis results
   - Use pagination for large queries