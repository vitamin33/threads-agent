# Documentation Generation Sub-Agent Setup Guide

## Overview
Add a `documentation-specialist` sub-agent to Claude Code that automatically generates comprehensive documentation after successful task completion, tests passing, and PR creation.

## 1. Sub-Agent Definition

Add this agent definition to Claude Code's function descriptions:

```
- documentation-specialist: Use this agent after successful task completion, when all tests pass and PRs are created, to generate comprehensive documentation including component explanations, architectural flows, interactions, and interview-ready technical details. This agent should be invoked automatically at the end of the development workflow. Examples:

<example>
Context: User has just completed implementing a new feature and all tests are passing.
user: "I've finished implementing the viral content engine and all tests are green"
assistant: "Great! Now let me use the documentation-specialist agent to generate comprehensive documentation for this feature"
<commentary>
Since the feature is complete and tests are passing, automatically invoke the documentation-specialist to create thorough documentation.
</commentary>
</example>

<example>
Context: A PR has been successfully created and merged.
user: "The authentication system PR has been merged"
assistant: "Perfect! I'll use the documentation-specialist agent to document the authentication system architecture and flows"
<commentary>
After successful PR merge, use documentation-specialist to create detailed technical documentation.
</commentary>
</example>
```

## 2. Integration Points

### A. In CLAUDE.md Workflow Commands
Update your workflow automation to include docs generation:

```bash
# Enhanced workflow commands
just ship-with-docs "message"    # ship + auto-generate docs
just complete-task task_001      # complete + generate docs
```

### B. In Git Hooks (Recommended)
Add to `.git/hooks/post-merge`:

```bash
#!/bin/bash
# Auto-trigger docs generation after successful merge
if [[ "$1" == "1" ]]; then  # Only on actual merges, not fast-forwards
    echo "🔄 Triggering documentation generation..."
    claude-code --agent documentation-specialist "Generate documentation for the recently merged changes"
fi
```

## 3. Automation Setup

### A. GitHub Actions Integration
Create `.github/workflows/auto-docs.yml`:

```yaml
name: Auto Documentation Generation

on:
  pull_request:
    types: [closed]
    branches: [main]

jobs:
  generate-docs:
    if: github.event.pull_request.merged == true
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Generate Documentation
        run: |
          claude-code --agent documentation-specialist \
            "Generate comprehensive documentation for PR #${{ github.event.pull_request.number }}: ${{ github.event.pull_request.title }}"
```

### B. Local Workflow Integration
Update `scripts/workflow-automation.sh`:

```bash
# Add docs generation to existing commands
tasks_ship() {
    local task_id=$1
    
    # Existing ship logic...
    ./scripts/workflow-automation.sh tasks commit "$task_id" "final implementation"
    
    # Create PR
    gh pr create --title "..." --body "..."
    
    # Auto-generate docs after successful PR creation
    echo "🔄 Generating documentation..."
    claude-code --agent documentation-specialist \
        "Generate comprehensive documentation for task $task_id including component architecture, flows, and technical details"
}
```

## 4. Documentation Templates

The agent should generate documentation following these patterns:

### A. Component Documentation
```markdown
# [Component Name] Documentation

## Overview
Brief description and purpose

## Architecture
- Component structure
- Dependencies
- Data flow

## API/Interfaces
- Endpoints/methods
- Input/output schemas
- Error handling

## Integration Points
- How it connects to other components
- Event flows
- Database interactions

## Technical Interview Notes
- Key design decisions
- Scalability considerations
- Performance characteristics
- Trade-offs made
```

### B. Feature Documentation
```markdown
# [Feature Name] Implementation

## Business Context
- Problem solved
- Success metrics
- User impact

## Technical Implementation
- Core components
- Data models
- Processing flow

## System Integration
- Service interactions
- Database changes
- External dependencies

## Monitoring & Observability
- Metrics tracked
- Alerts configured
- Debugging approaches

## Interview Talking Points
- Technical challenges overcome
- Architecture decisions
- Future improvements
```

## 5. Trigger Conditions

The documentation-specialist should be automatically invoked when:

1. **All tests pass** (`just check` succeeds)
2. **PR is created** (via `just ship` or `tasks ship`)
3. **Feature is complete** (manual trigger via `tasks complete`)
4. **PR is merged** (post-merge hook)

## 6. Agent Prompt Template

```
Generate comprehensive technical documentation for the recently completed implementation. Include:

1. **Component Overview**: Purpose, responsibilities, and key features
2. **Architecture Diagram**: Component relationships and data flow (ASCII or mermaid)
3. **Technical Implementation**: Core classes, methods, and algorithms
4. **Integration Points**: How this connects to existing system components
5. **Database Schema**: Any new tables, indexes, or migrations
6. **API Documentation**: Endpoints, request/response formats, error codes
7. **Performance Characteristics**: Latency, throughput, resource usage
8. **Monitoring & Alerts**: Metrics, dashboards, and alerting rules
9. **Interview Preparation**: Key technical talking points and design decisions
10. **Future Enhancements**: Potential improvements and scalability considerations

Focus on creating documentation that would help explain this implementation in a technical interview setting.
```

## 7. File Organization

Generated docs should follow this structure:
```
docs/
├── components/
│   ├── orchestrator.md
│   ├── persona-runtime.md
│   └── viral-engine.md
├── features/
│   ├── authentication.md
│   ├── content-generation.md
│   └── trend-analysis.md
├── architecture/
│   ├── system-overview.md
│   ├── data-flow.md
│   └── service-interactions.md
└── interview-prep/
    ├── technical-highlights.md
    └── design-decisions.md
```

## 8. Usage Examples

### Manual Invocation
```bash
# After completing a feature
claude-code --agent documentation-specialist \
    "Document the new viral content generation system I just implemented"

# After PR merge
claude-code --agent documentation-specialist \
    "Generate technical documentation for the authentication refactor in PR #123"
```

### Automated Triggers
```bash
# In your workflow
./scripts/workflow-automation.sh tasks complete task_001
# → Automatically triggers docs generation

just ship-with-docs "implement user auth"
# → Ships PR and generates docs
```

## 9. Integration with Existing Agents

The documentation-specialist should work alongside:
- **tdd-master**: Documents test coverage and testing strategy
- **k8s-performance-optimizer**: Documents performance optimizations made
- **epic-planning-specialist**: Documents how implementation matches original plan

## 10. Success Metrics

Track documentation generation success:
- Docs generated per completed task
- Documentation completeness score
- Time saved in interview preparation
- Technical review efficiency improvement

---

This setup ensures every completed feature gets comprehensive documentation automatically, making your codebase interview-ready and technically well-documented.