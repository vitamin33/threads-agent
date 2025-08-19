# M4: Release Path with Canary/Rollback

> **🎯 Goal**: Enable safe daily shipping with 1-3h/week savings through deployment confidence

## Quick Start

```bash
# Safe canary deployment (recommended)
just release canary 10              # 10% traffic canary

# Staging deployment  
just release-staging                # Deploy to staging first

# Release history
just release-history                # View recent deployments

# Advanced options
just release canary 25 prod         # 25% canary to production
just release-direct prod            # Direct deployment (risky)
```

## Release Strategies

### 1. Canary Deployment (Recommended)
- **Percentage-based traffic splitting** (default: 10%)
- **Automatic health monitoring** for 15 minutes
- **Auto-rollback** on error rate > 15% or high latency
- **Safety first**: Validates quality gates before deployment

```bash
just release canary 10              # 10% canary deployment
just release canary 25 staging      # 25% canary to staging  
```

### 2. Staging Deployment
- **Deploy to staging environment first**
- **Manual validation** before production promotion
- **Safe for testing**: Full feature validation

```bash
just release-staging                # Deploy to staging
```

### 3. Direct Deployment (Use with Caution)
- **No safety nets** - deploys directly
- **Fastest** but highest risk
- **Only for emergency fixes** or simple changes

```bash
just release-direct dev             # Direct to dev (lower risk)
just release-direct prod            # Direct to prod (high risk)
```

## Safety Validations

**Pre-deployment checks** (all must pass):
1. **M2 Quality Gates**: Evaluation score ≥ 0.85
2. **M1 Telemetry Health**: Success rate ≥ 90%  
3. **Git Status**: Working directory clean
4. **Dependency Check**: Required services available

**Health Monitoring** (during deployment):
- **Error Rate**: Must stay ≤ 15%
- **Latency**: P95 ≤ 2x baseline
- **Success Rate**: Must stay ≥ 80%
- **Request Volume**: Tracks traffic patterns

**Auto-Rollback Triggers**:
- Error rate spikes above 15%
- Latency increases beyond 2x baseline  
- Success rate drops below 80%
- Any critical alert threshold

## Example Workflows

### Daily Development Cycle
```bash
# Morning: Check system health
just brief                          # Get priorities
just metrics-today                  # Check overnight health

# Development work...

# Afternoon: Test and deploy
just eval-run core                  # Validate quality
just release canary 10              # Safe deployment
just release-history                # Verify success

# Evening: Review
just debrief                        # Log outcomes
```

### Emergency Hotfix
```bash
# Skip normal gates for critical fixes
just release-direct prod            # Direct deployment
just release-history                # Monitor outcome
```

### Feature Release
```bash
# Progressive rollout
just release-staging                # Test in staging first
just release canary 5               # Start with 5% traffic
just release canary 25              # Increase to 25%
just release canary 100             # Full deployment
```

## Monitoring & Rollback

### Automatic Rollback Example
```
🚀 Starting canary deployment (10% canary)
📋 Release ID: rel_1755595388
🎯 Environment: dev

🔍 Pre-deployment validation:
  ✅ quality_gates: Quality gates passing (score: 0.87)
  ✅ telemetry_health: Good success rate: 99.8%
  ✅ git_clean: Working directory clean

🐦 Deploying canary (10% traffic)...
📊 Monitoring deployment health...
⏱️  Monitoring for 900s...

📈 Health Check Results:
  • Error Rate: 18.2% (threshold: 15.0%)  ⚠️
  • Success Rate: 87.3%
  • P95 Latency: 2,450ms
  • Request Count: 387

🚨 Alerts: High error rate: 18.20%
🔄 Triggering automatic rollback...
✅ Rollback complete
📋 Reason: High error rate: 18.20%
```

### Release History Tracking
```
📋 Recent Release History:
  ✅ 08/19 12:15: canary -> deployed (45.2s)
  🔄 08/19 11:30: canary -> rolled_back (32.1s)  
  ❌ 08/19 10:45: staging -> failed (15.3s)
  🏗️ 08/19 09:20: staging -> staging (12.1s)

📊 7-day rollback rate: 12.5%
```

## Configuration

### Release Config (.dev-system/config/dev-system.yaml)
```yaml
release:
  enabled: true
  default_strategy: "canary"
  canary_percentage: 10
  rollback_threshold: 0.15  # 15% error rate
  health_check_timeout: 300  # 5 minutes
  staging_suffix: "-staging"
```

### Custom Thresholds
```python
from ops.release import ReleaseManager, ReleaseConfig

config = ReleaseConfig(
    canary_percentage=25,      # 25% canary
    rollback_threshold=0.10,   # 10% error threshold
    health_check_timeout=600   # 10 minute monitoring
)

manager = ReleaseManager(config)
```

## Integration with Existing Systems

**M1 Telemetry Integration:**
- Uses real performance metrics for health assessment
- Compares deployment metrics against historical baselines
- Automatic alerting based on telemetry thresholds

**M2 Quality Integration:**
- Blocks deployments if quality gates fail
- Integrates evaluation scores into deployment decisions
- Prevents deploying broken functionality

**M5 Planning Integration:**
- Release failures appear in morning brief priorities
- Evening debrief tracks deployment success patterns
- ICE scoring for deployment-related tasks

## Business Value

**Time Savings:**
- **1-3 hours/week** saved on deployment debugging
- **Faster iteration** through deployment confidence
- **Reduced "oh no" moments** through safety validation

**Risk Reduction:**
- **Automatic rollback** prevents extended outages
- **Quality gate integration** prevents bad deployments
- **Health monitoring** catches issues early

**Velocity Increase:**
- **Daily deployment confidence** enables faster shipping
- **Progressive rollout** allows safer feature releases  
- **Historical learning** improves deployment reliability

This system enables **fearless deployment** while maintaining production stability!