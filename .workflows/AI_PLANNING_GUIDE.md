# AI-Powered Epic Planning System

This system uses OpenAI's GPT-4 to intelligently break down high-level requirements into detailed epics, features, and tasks.

## Quick Start

### 1. Set up OpenAI API Key
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### 2. Run AI Planning
```bash
# Direct AI planner
./scripts/ai-epic-planner.sh "Build a real-time chat application"

# Via workflow script (when syntax is fixed)
./scripts/workflow-automation.sh ai-plan "Build a real-time chat application"
```

### 3. Demo Mode (No API Key Required)
```bash
./scripts/ai-epic-planner-demo.sh "Build a mobile app for food delivery"
```

## What Gets Generated

The AI creates:

### 📊 **Epic File** (`.workflows/epics/epic_*.yaml`)
- Epic name and description
- Business value proposition
- Technical approach overview
- Risk assessment
- Time estimates
- Success metrics

### 🔧 **Feature Files** (`.workflows/features/feat_*.yaml`)
- Detailed feature descriptions
- Acceptance criteria
- Implementation tasks with time estimates
- Dependencies between features
- Testing strategies

### 📋 **Task Breakdown**
- Specific, actionable tasks (1-8 hours each)
- Technical implementation notes
- Clear descriptions
- Effort estimates

### 🎯 **Milestones & Metrics**
- Week-by-week milestones
- Deliverable criteria
- Success metrics with targets
- Measurement strategies

## Example Output Structure

```yaml
epic:
  name: "Real-time Chat Application"
  description: "Build scalable WebSocket-based chat with authentication"
  complexity: "large"
  estimated_weeks: 6
  business_value: "Enable real-time communication, increase engagement 40%"

features:
  - name: "User Authentication & Sessions"
    effort: "medium"
    priority: "high"
    category: "backend"
    tasks:
      - name: "Setup authentication middleware"
        effort_hours: 4
        technical_notes: "Use express-jwt and bcrypt"
      - name: "Create user registration endpoint"
        effort_hours: 3
        technical_notes: "Validate email, hash passwords"

milestones:
  - name: "Authentication MVP"
    week: 2
    deliverables:
      - "User registration and login working"
      - "Basic session management"

success_metrics:
  - metric: "Message delivery latency"
    target: "< 100ms"
    measurement: "WebSocket ping-pong timing"
```

## AI Prompt Engineering

The system uses a sophisticated prompt that ensures:

1. **Structured Output**: YAML format for easy parsing
2. **Actionable Tasks**: Specific, time-bounded work items
3. **Dependencies**: Clear relationships between features
4. **Testing**: Built-in quality assurance tasks
5. **Metrics**: Measurable success criteria

## Integration Features

### Auto-Generated Files
- Epic YAML with full metadata
- Feature YAML with implementation details
- Updated epic registry (`active_epics.json`)
- Updated feature registry (`feature_registry.json`)

### Smart Defaults
- Branch naming patterns
- CI/CD pipeline configuration
- Notification channels
- Risk assessment

### Quality Controls
- Realistic time estimates
- Dependency validation
- Testing strategy inclusion
- Documentation requirements

## Advanced Usage

### Custom Context
```bash
./scripts/ai-epic-planner.sh "Build payment system" "Must support Stripe, handle subscriptions, PCI compliant"
```

### Integration with Workflow
```bash
# After AI planning, start working
epic_id="epic_1234567890"
./scripts/workflow-automation.sh tasks list $epic_id
./scripts/workflow-automation.sh tasks update task_001 in_progress
```

### Team Collaboration
```bash
# Assign tasks to team members
./scripts/workflow-automation.sh tasks assign task_001 alice
./scripts/workflow-automation.sh tasks assign task_002 bob
```

## Benefits

### 🚀 **Speed**
- Seconds to break down complex requirements
- Instant epic/feature/task structure
- Ready-to-work backlog

### 🎯 **Quality**
- Expert-level planning knowledge
- Industry best practices
- Realistic estimates

### 📈 **Consistency**
- Standardized epic structure
- Uniform task breakdown
- Predictable deliverables

### 🔄 **Integration**
- Git-based workflow
- Version controlled plans
- Team collaboration ready

## Next Steps

1. **Test with your requirements**
2. **Refine based on your team's needs**
3. **Integrate with your development workflow**
4. **Track actual vs estimated time for calibration**

---

*This AI planning system transforms high-level ideas into actionable development plans in seconds.*
