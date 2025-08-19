# M5: AI-Powered Planning System

> **🎯 Goal**: Eliminate decision fatigue and optimize daily productivity by 30-50%

## Quick Start

```bash
# Morning routine (2 minutes)
just work-day                    # Auto-runs: metrics-today + brief + dashboards

# Evening routine (1 minute)  
just end-day                     # Auto-runs: debrief + analysis + optimization

# Manual commands
just brief                       # Generate morning brief anytime
just debrief                     # Generate evening debrief anytime
just ice-demo                    # See ICE scoring examples
```

## System Overview

M5 creates an **intelligent daily loop** that learns from your patterns:

### Morning Brief (Data-Driven Planning)
- **Performance Summary**: Yesterday's telemetry from M1
- **Quality Status**: Latest M2 evaluation results  
- **Git Activity**: Recent commits and branch analysis
- **Top 3 Priorities**: ICE-scored with specific actions
- **Quick Commands**: Context-aware next steps

### Evening Debrief (Outcome Learning)
- **Productivity Score**: 0-100 based on metrics + activity
- **Achievement Analysis**: What got done vs planned
- **Pattern Insights**: Performance trends and blockers
- **Tomorrow's Focus**: Data-driven suggestions
- **Context Saving**: Learns for better future planning

### ICE Scoring (Intelligent Prioritization)
- **Impact**: Business/productivity impact (1-10)
- **Confidence**: Certainty of outcome (1-10)  
- **Effort**: Time/complexity required (1-10, lower = better)
- **Context-Aware**: Adjusts for category, urgency, dependencies
- **Category Intelligence**: Bug fixes vs features vs debt

## Data Sources

M5 integrates data from:
- **M1 Telemetry**: Success rates, latency, costs, alerts
- **M2 Quality Gates**: Test results, quality scores, failures
- **Git Activity**: Commits, changes, branch type analysis
- **Historical Context**: Previous briefs and outcomes

## Sample Morning Brief

```
🌅 Morning Brief - Tuesday, August 19, 2025
============================================================

📊 Yesterday's Performance:
  • Success Rate: 99.8%
  • P95 Latency: 13ms  
  • Cost: $0.00
  • Top Agent: perf_test

🎯 Quality Status:
  • Latest Score: 0.63
  • Gate Status: FAIL
  • Failed Tests: 0

🎯 Top 3 Priorities Today:
1. Fix Quality Gate Failures (ICE: 13.5)
   Resolve 0 failing quality tests
   📋 Action: Run: just eval-latest to see failures
   📊 Source: M2 Quality Gates

2. Enhance Development System (ICE: 7.71) 
   Continue building top 1% agent factory
   📋 Action: Continue with next milestone (M4/M3/M6)
   📊 Source: Milestone Roadmap

3. Complete Feature Implementation (ICE: 7.0)
   Finish current feature development and testing
   📋 Action: Continue feature implementation  
   📊 Source: Git Branch Analysis
```

## ICE Scoring Categories

| Category | Impact Multiplier | Use Case |
|----------|------------------|----------|
| **Urgent Bug** | 1.2x | Production issues, blockers |
| **Feature Development** | 1.0x | New functionality |  
| **Performance Optimization** | 1.1x | Speed/cost improvements |
| **Quality Improvement** | 0.8x | Code quality, testing |
| **Technical Debt** | 0.7x | Future maintainability |

## Context-Aware Adjustments

**Urgency**: +30% impact for urgent tasks
**Blocking Others**: +20% impact for dependencies  
**Learning Opportunity**: +10% impact for skill development
**Technical Risk**: Adjusts confidence and effort based on complexity

## Business Value

**Immediate Benefits:**
- **Eliminate decision paralysis** - always know what to work on next
- **Data-driven priorities** - based on real performance, not guesswork  
- **Pattern learning** - system gets smarter over time
- **Context preservation** - morning plans correlate with evening outcomes

**Weekly Time Savings:**
- **3-6 hours saved** on planning and decision-making
- **ROI payback** in 1.3-5.3 weeks
- **Productivity boost** through elimination of thrash

## Advanced Features

### Custom ICE Weights
```yaml
# In .dev-system/config/dev-system.yaml
planning:
  ice_weights:
    impact: 0.5      # 50% weight on business impact
    confidence: 0.3   # 30% weight on execution certainty
    effort: 0.2      # 20% weight on time/complexity
```

### Branch-Specific Planning
- **Feature branches**: Focus on implementation completion
- **Bug branches**: Prioritize verification and testing
- **Refactor branches**: Emphasize validation and cleanup

### Performance Correlation
- **High latency days**: Suggests optimization priorities
- **High cost days**: Recommends efficiency improvements  
- **Low success days**: Focuses on error investigation

## Integration with M1+M2

**M1 Telemetry Integration:**
- Morning brief shows yesterday's performance metrics
- Evening debrief correlates planned vs actual performance
- Productivity scoring uses real telemetry data

**M2 Quality Integration:**
- Surfaces quality gate failures as top priorities
- Tracks evaluation score trends over time
- Suggests quality improvements based on test results

## Files Structure

```
.dev-system/planner/
├── brief.py         # Morning brief generation
├── debrief.py       # Evening debrief with learning
├── ice.py           # ICE scoring system  
├── context/         # Saved planning context
│   ├── brief_*.json # Morning brief context
│   └── debrief_*.json # Evening debrief data
└── README.md        # This file
```

This planning system transforms your daily workflow from reactive to proactive, data-driven development that maximizes impact per hour invested.