# Complete Agent Factory User Guide

> **🏆 Your Daily Guide to Using the TOP 1% AI Agent Development System**
> 
> **Master your 13.5-31h/week efficiency gains through intelligent workflows**

## 🌅 **Daily Morning Routine (5-8 minutes)**

### **Step 1: System Health Check (2 minutes)**
```bash
# Get AI-powered priorities based on real data
just brief
# Output: Top 3 ICE-scored priorities with specific actions

# Check overnight system performance
just metrics-today
# Output: Success rate, latency, costs, alerts
```

### **Step 2: Quality Validation (2 minutes)**
```bash
# Check latest quality results
just eval-latest

# Run security scan
just safety-check
```

### **Step 3: Agent-Specific Planning (2-4 minutes)**
```bash
# If working in specific worktree (Agent A1-A4):
AGENT_ID=a2 just agent-brief        # AI/ML agent priorities
just my-services                    # Show your services
just agent-status                   # All agents dashboard

# Knowledge for your domain
just knowledge-search "machine learning"
just knowledge-stats
```

## 🔧 **Development Workflow**

### **Planning New Features**

#### **Strategic Feature Planning:**
```bash
# 1. Check current system priorities
just brief                          # What does data say to focus on?

# 2. ICE scoring for business value
# Impact (1-10): Business value?
# Confidence (1-10): Certainty of success?
# Effort (1-10): Time/complexity? (lower = better)

# 3. Check agent dependencies
just agent-impact a3                # Cross-agent effects
```

### **Feature Development Process**

#### **Phase 1: Setup (15 minutes)**
```bash
# 1. Create feature branch
git checkout -b feat/analytics/realtime-dashboard__a3

# 2. Plan with agent factory
just brief                          # Current priorities
just agent-impact a3                # Cross-agent impact

# 3. Set quality baseline
just eval-run achievement_collector
```

#### **Phase 2: Development**
```bash
# Continuous validation during development:
just eval-run achievement_collector  # Test changes
just safety-check                   # Security
just metrics-today                  # Performance impact
```

#### **Phase 3: Pre-Deployment (10 minutes)**
```bash
# 1. Comprehensive quality check
just eval-all
just eval-agents "achievement_collector dashboard_api"

# 2. Cross-agent validation
just agent-impact a3
just agent-status

# 3. Knowledge update
just knowledge-add "Feature Docs" "How new dashboard works"
```

#### **Phase 4: Safe Deployment (5 minutes)**
```bash
# 1. Check deployment sequence
just agent-deploy-sequence

# 2. Deploy with strategy
just release canary 15              # A3 deployment strategy

# 3. Monitor
just release-history
just agent-status
```

## 🌙 **Evening Routine (3-5 minutes)**

### **Productivity Analysis (2 minutes)**
```bash
just debrief
# Output: Productivity score, insights, tomorrow's focus
```

### **System Coordination (2-3 minutes)**
```bash
just quality-weekly                 # Cross-agent trends
just eval-all                       # System health
```

## 🎯 **Strategic Decision Making**

### **What to Develop Next**

#### **Let the System Guide You:**
```bash
just brief                          # AI analyzes all data
# Priority examples:
#   1. Fix Performance Alert (ICE: 18.0) - CRITICAL
#   2. Update Knowledge (ICE: 14.0) - HIGH  
#   3. Quality Issues (ICE: 13.5) - HIGH
```

#### **ICE Scoring Guidelines:**
- **CRITICAL (ICE > 15.0)**: Performance alerts, security issues
- **HIGH (ICE 10.0-15.0)**: Quality failures, user-facing features
- **MEDIUM (ICE 7.0-10.0)**: Technical improvements, optimizations
- **LOW (ICE < 7.0)**: Nice-to-have features, polish

### **Agent-Specific Strategy:**

**Agent A1 (Infrastructure)**: Deploy first, affects everyone
**Agent A2 (AI/ML)**: Focus on prompts and content quality
**Agent A3 (Analytics)**: Quality trends and data insights
**Agent A4 (Business)**: Conservative, security-focused

## 💡 **Tips & Tricks**

### **Daily Efficiency:**
```bash
# Morning routine alias
alias morning="just brief && just metrics-today && just eval-latest"

# Agent-specific shortcuts
alias a1-work="AGENT_ID=a1 just agent-brief && just eval-agents 'orchestrator celery_worker'"
```

### **Quality Management:**
```bash
# Before changes
just agent-impact a1                # Check dependencies

# After changes  
just eval-run <service>             # Validate immediately
just metrics-today                  # Performance check
```

### **Deployment Best Practices:**
```bash
# A1 Infrastructure: FIRST, staging required
just release staging

# A2+A3: PARALLEL, after A1
just release canary 10              # A2 standard
just release canary 15              # A3 aggressive

# A4 Business: LAST, conservative
just release canary 5
```

## 🔧 **Troubleshooting**

### **Performance Issues:**
```bash
just metrics-today                  # Identify issue
just eval-all                       # Find problematic agent
just knowledge-search "performance optimization"
```

### **Quality Failures:**
```bash
just eval-latest                    # See failures
just prompt-test <agent> <prompt>   # Check prompts
just prompt-rollback <agent> <prompt> <version>  # Rollback if needed
```

### **Agent Conflicts:**
```bash
just agent-impact <changed-agent>   # See affected agents
just eval-agents "<affected-services>"  # Test impacts
just agent-deploy-sequence          # Follow proper order
```

## 📈 **Weekly Planning**

### **Monday Planning (30 minutes):**
```bash
just quality-weekly                 # Last week performance
just brief                          # Strategic priorities
just agent-status                   # Coordination status
```

### **Friday Review (20 minutes):**
```bash
just debrief                        # Week achievements
just eval-all                       # System health
just knowledge-validate             # Knowledge freshness
```

## 🎓 **Mastery Path**

### **Week 1-2: Basics**
- Master `just brief` → work → `just debrief` routine
- Learn your services: `just my-services`
- Basic validation: `just eval-run <service>`

### **Week 3-4: Coordination**
- Multi-agent awareness: `just agent-status`
- Impact analysis: `just agent-impact`
- Quality trends: `just quality-weekly`

### **Month 2+: Advanced**
- ICE scoring for prioritization
- Cross-agent coordination mastery
- System optimization from telemetry

### **Month 3+: Expert**
- Predictive quality management
- Advanced prompt engineering
- Architecture decisions from data
- Team mentoring with agent factory

## 🏆 **Success Metrics**

### **Daily Success:**
- Morning brief < 5 minutes
- Zero deployment surprises
- Productivity score > 85
- Zero security alerts

### **Weekly Success:**
- All agents quality > 0.75
- Zero stale knowledge
- Smooth deployments
- Increasing productivity trends

**Your complete guide to mastering the TOP 1% agent development system!** 🎯