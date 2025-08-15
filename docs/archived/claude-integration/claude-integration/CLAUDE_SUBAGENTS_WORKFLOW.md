# Claude Code Subagents Workflow Guide

## 🚀 Integrated Development Workflow with Subagents

### Quick Reference: Subagent Specialties
| Subagent | Trigger Phrase | Best For |
|----------|----------------|----------|
| **epic-planner** | "plan epic" | Breaking down features into tasks |
| **tdd-master** | "write tests" | Enforcing test-first development |
| **test-generator** | "generate tests" | Creating comprehensive test suites |
| **performance-hunter** | "optimize performance" | Finding bottlenecks |
| **devops-automator** | "setup k8s" | Infrastructure & deployment |

## 📋 Standard Development Workflow

### Phase 1: Planning (epic-planner)
```bash
# AI plans your feature
./scripts/workflow-automation.sh ai-plan "your feature idea"

# Epic gets created with:
# - Unique ID (epic_timestamp)
# - Feature breakdown
# - Effort estimates
# - Success metrics
```

### Phase 2: TDD Development (tdd-master + test-generator)
```bash
# Start task (auto-creates branch)
./scripts/workflow-automation.sh tasks start task_001

# TDD workflow:
# 1. tdd-master forces you to write tests first
# 2. test-generator creates comprehensive test suite
# 3. Write minimal code to pass
# 4. Refactor with green tests
```

### Phase 3: Performance (performance-hunter)
```bash
# Performance analysis finds:
# - N+1 queries
# - Missing indexes  
# - Sync operations that should be async
# - Memory leaks
# - Cache opportunities
```

### Phase 4: Deployment (devops-automator)
```bash
# Smart deployment
just ship-it  # Tests + Deploy + PR

# Or step by step:
just unit
just e2e
./scripts/smart-deploy.sh canary
```

## 🎯 Epic-Specific Workflows

### E4: User Authentication Epic
```bash
# 1. Plan with AI
./scripts/workflow-automation.sh ai-plan "OAuth integration with Google/GitHub"

# 2. Subagents will:
# - epic-planner: Create auth epic with security milestones
# - tdd-master: Force auth tests first (security critical!)
# - test-generator: Create auth edge cases
# - performance-hunter: Check token validation performance
# - devops-automator: Setup OAuth secrets in K8s
```

### E5: Content Generation Pipeline
```bash
# 1. Use trend detection
just trend-check "viral topics"
./scripts/trend-detection-workflow.sh

# 2. Subagents optimize:
# - performance-hunter: Optimize LLM calls (batching, caching)
# - test-generator: Mock OpenAI responses for tests
```

### E6: Analytics Dashboard
```bash
# 1. Customer intelligence first
./scripts/customer-intelligence.sh

# 2. Subagents handle:
# - epic-planner: Break down by metric types
# - performance-hunter: Optimize Grafana queries
# - devops-automator: Setup Prometheus alerts
```

### E7: Monetization Features
```bash
# 1. Revenue planning
./scripts/grow-to-20k.sh

# 2. Specialized handling:
# - tdd-master: Critical for payment flows
# - test-generator: Stripe webhook tests
# - devops-automator: PCI compliance setup
```

### E8: API Development
```bash
# 1. API design first
# epic-planner creates OpenAPI spec

# 2. Development:
# - tdd-master: Contract testing
# - test-generator: Integration tests
# - performance-hunter: API latency optimization
```

### E9: Mobile/Web UI
```bash
# 1. UI/UX planning
# epic-planner: Component breakdown

# 2. Frontend specific:
# - test-generator: React component tests
# - performance-hunter: Bundle size optimization
```

### E10: Infrastructure Scaling
```bash
# 1. Full devops-automator control
./scripts/cluster-manager.sh

# 2. Automated:
# - K8s resource optimization
# - Autoscaling setup
# - Cost analysis
```

### E11: Security Hardening
```bash
# 1. Security audit
# tdd-master: Security test suite

# 2. Implementation:
# - test-generator: Penetration tests
# - devops-automator: Security policies
```

### E12: Performance Optimization
```bash
# 1. Full performance-hunter analysis
# - Database optimization
# - Caching strategy
# - Async processing

# 2. Measure:
just grafana  # View improvements
```

## 🔄 Daily Workflow Integration

### Morning Routine
```bash
just work-day  # Starts environment + dashboards

# Check overnight achievements
./scripts/test-achievement-collector.sh

# Review AI suggestions
./scripts/ai-business-intelligence.sh
```

### During Development
```bash
# Always use task management
./scripts/workflow-automation.sh tasks start task_XXX

# Commit frequently
./scripts/workflow-automation.sh tasks commit task_XXX "changes"

# Let subagents guide you:
# - "I need to add auth" → epic-planner creates plan
# - "Write login endpoint" → tdd-master forces tests
# - "It's slow" → performance-hunter analyzes
```

### End of Day
```bash
# Ship completed work
./scripts/workflow-automation.sh tasks ship task_XXX

# Analyze metrics
just end-day

# Let AI optimize tomorrow
./scripts/learning-system.sh
```

## 💡 Pro Tips

### 1. Parallel Subagent Execution
```yaml
# In .claude/agents/, agents can work simultaneously:
# - epic-planner: Planning next epic
# - test-generator: Writing tests for current task
# - performance-hunter: Analyzing production metrics
```

### 2. Context Switching
```bash
# Save context before switching
./scripts/claude-session-tracker.sh save

# Switch tasks
./scripts/workflow-automation.sh tasks start new_task

# Restore context
./scripts/claude-session-tracker.sh restore
```

### 3. Automated Workflows
```bash
# Autopilot mode (AI drives development)
./scripts/autopilot.sh

# Make money mode (focuses on monetization)
just make-money
```

### 4. Smart Caching
```bash
# Cache expensive operations
just cache-set "trends-$(date +%Y%m%d)" "$(just trend-check 'AI')"
just cached-analyze  # 0 tokens used!
```

## 📊 Metrics to Track

### With Subagents Active
- **Code Coverage**: >90% (enforced by tdd-master)
- **Performance**: <100ms API latency (performance-hunter)
- **Deployment Success**: >99% (smart-deploy + devops-automator)
- **Development Speed**: 3-5x faster with AI planning

### ROI Metrics
```bash
# Weekly time saved:
# - AI Planning: 8-10 hours
# - TDD Enforcement: 6-8 hours  
# - Performance Optimization: 4-5 hours
# - DevOps Automation: 5-6 hours
# Total: 23-29 hours/week
```

## 🚨 Common Patterns

### Pattern 1: Feature Development
```
ai-plan → epic-planner → tasks start → tdd-master → 
test-generator → implement → performance-hunter → 
ship → devops-automator
```

### Pattern 2: Bug Fix
```
grep/search → tdd-master (reproduce bug) → 
fix → test-generator (regression test) → ship
```

### Pattern 3: Performance Issue
```
performance-hunter (identify) → implement fix → 
measure → smart-deploy (canary) → monitor
```

## 🔗 Integration Points

### With Claude Hooks
- epic-planner completion → voice notification
- tdd-master test failure → error alert
- performance-hunter finding → Slack notification
- devops-automator deployment → success sound

### With MCP Servers
- Redis: Cache AI responses
- K8s: Deploy with devops-automator
- PostgreSQL: Performance analysis queries
- Slack: Team notifications

Remember: Let the subagents guide you - they enforce best practices automatically!