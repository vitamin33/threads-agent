# Auto-Git Integration Guide

Complete git workflow automation that connects AI planning directly to code delivery.

## 🚀 **Complete Workflow: AI → Code → Ship**

```bash
# 1. AI creates the plan
./scripts/workflow-automation.sh ai-plan "Build user authentication system"

# 2. Start working on a task (auto-branching + setup)
./scripts/workflow-automation.sh tasks start task_auth_001

# 3. Make your changes...
# Edit files, implement features

# 4. Commit with enhanced context
./scripts/workflow-automation.sh tasks commit task_auth_001 "implement JWT middleware"

# 5. Ship for review (auto-PR creation)
./scripts/workflow-automation.sh tasks ship task_auth_001

# 6. Complete after merge
./scripts/workflow-automation.sh tasks complete task_auth_001
```

## 📋 **Commands Reference**

### **Start Working: `tasks start`**
```bash
./scripts/workflow-automation.sh tasks start task_12345
```

**What it does:**
- ✅ Ensures main branch is up-to-date
- ✅ Creates feature branch: `task-epic123-implement-auth-middleware`
- ✅ Sets up commit template with task context
- ✅ Updates task status to "in_progress"
- ✅ Shows task description and next steps

### **Enhanced Commits: `tasks commit`**
```bash
./scripts/workflow-automation.sh tasks commit task_12345 "add JWT validation"
```

**Enhanced commit message:**
```
add JWT validation

Task: Implement JWT Authentication Middleware (task_12345)
Epic: epic_auth_system_001
Priority: high

Co-authored-by: AI Planning System <ai@threads-agent.dev>
```

**Additional features:**
- ✅ Auto-stages all changes
- ✅ Pushes to remote branch
- ✅ Prompts for progress update (25%, 50%, 75%, 100%)
- ✅ Links commits to task tracking

### **Create PRs: `tasks ship`**
```bash
./scripts/workflow-automation.sh tasks ship task_12345 "feat: JWT authentication"
```

**Auto-generated PR includes:**
- 📋 Task name and description
- 🏷️ Auto-labels (priority, effort, feature type)
- ✅ Testing checklist template
- 🔗 Links to epic and feature
- 📊 Task metadata
- 🤖 AI-planned indicator

### **Complete Tasks: `tasks complete`**
```bash
./scripts/workflow-automation.sh tasks complete task_12345
```

**Cleanup process:**
- ✅ Updates task status to "completed"
- ✅ Sets progress to 100%
- ✅ Adds completion timestamp
- ✅ Switches back to main branch
- ✅ Optional branch cleanup
- ✅ Shows next available tasks from epic

## 🎯 **Smart Features**

### **Branch Naming**
Automatically generates semantic branch names:
- `task-123-implement-jwt-auth-middleware`
- `task-456-add-user-registration-form`
- `task-789-setup-password-reset-flow`

### **Commit Templates**
Sets up context-aware commit templates:
```
# Task: Implement JWT Authentication (task_12345)
# Epic: epic_auth_001
# Priority: high | Effort: medium
#
# Description: Create middleware for JWT token validation
#
# Commit format: <type>: <description> (closes task_12345)
```

### **PR Descriptions**
Rich PR descriptions with:
```markdown
## 📋 Task: Implement JWT Authentication

**Task ID:** `task_12345`
**Epic:** `epic_auth_001`
**Priority:** high | **Effort:** medium

### Description
Create JWT authentication middleware for API endpoints.
Should validate tokens, handle expiration, and provide user context.

### Changes Made
<!-- Auto-filled from commits -->

### Testing
- [ ] Unit tests added/updated
- [ ] Manual testing completed
- [ ] Integration tests pass

🤖 **AI-Planned** | 📋 **Task-Driven** | 🚀 **Ready for Review**
```

### **Progress Tracking**
Integrated progress updates:
- Prompts after each commit
- Visual progress indicators
- Status transitions: pending → in_progress → review → completed

### **Smart Suggestions**
- Shows next available tasks after completion
- Suggests related tasks from the same epic
- Recommends team assignments

## 🔧 **Setup & Configuration**

### **Prerequisites**
```bash
# GitHub CLI (for auto-PR creation)
brew install gh
gh auth login

# Standard git setup
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### **Repository Setup**
Works with any git repository. No special setup required.

### **Team Integration**
```bash
# Assign tasks to team members
./scripts/workflow-automation.sh tasks assign task_12345 alice

# Alice starts working
./scripts/workflow-automation.sh tasks start task_12345
```

## 📊 **Integration Examples**

### **From AI Planning**
```bash
# Complete flow from idea to code
./scripts/workflow-automation.sh ai-plan "Build payment processing"
# → Creates epic with 5 features, 15 tasks

./scripts/workflow-automation.sh tasks list epic_payment_001
# → Shows all available tasks

./scripts/workflow-automation.sh tasks start task_payment_stripe_001
# → Ready to code!
```

### **Team Workflow**
```bash
# Project manager assigns tasks
./scripts/workflow-automation.sh tasks assign task_001 alice
./scripts/workflow-automation.sh tasks assign task_002 bob

# Developers start working
./scripts/workflow-automation.sh tasks start task_001  # Alice
./scripts/workflow-automation.sh tasks start task_002  # Bob

# Progress tracking
./scripts/workflow-automation.sh tasks list epic_001
```

### **Sprint Planning**
```bash
# See what's available for this sprint
./scripts/workflow-automation.sh tasks list epic_001 pending

# Estimate total effort
./scripts/workflow-automation.sh tasks show task_001  # 4 hours
./scripts/workflow-automation.sh tasks show task_002  # 6 hours
# Total: 10 hours for this epic
```

## 🎉 **Benefits**

### **Developer Experience**
- 🚀 **Zero Setup Time**: One command starts everything
- 📝 **Rich Context**: Commits and PRs have full task context
- 🧹 **Auto Cleanup**: Branch management handled automatically
- 📊 **Progress Tracking**: Always know where you are

### **Team Collaboration**
- 👥 **Clear Ownership**: Tasks assigned and tracked
- 🔗 **Linked Work**: PRs connected to planning
- 📈 **Visibility**: Real-time progress across team
- 🎯 **Focus**: Next tasks automatically suggested

### **Project Management**
- 📊 **Traceability**: Code changes linked to business requirements
- 📈 **Metrics**: Track velocity and completion rates
- 🎯 **Prioritization**: Priority and effort visible in all commits/PRs
- 🤖 **AI-Driven**: Planning and execution connected seamlessly

### **Quality Assurance**
- ✅ **Consistent PRs**: Every PR has proper description and checklist
- 🔗 **Requirements Traceability**: Code changes linked to original tasks
- 📝 **Documentation**: Auto-generated from planning context
- 🧪 **Testing Reminders**: Built-in testing checklist

## 🚨 **Error Handling**

### **Common Issues**

**No task file found:**
```bash
# Ensure task exists
./scripts/workflow-automation.sh tasks show task_12345
```

**Branch already exists:**
```bash
# Auto-checkout existing branch
# No action needed - system handles this
```

**GitHub CLI not found:**
```bash
# Install gh CLI
brew install gh
gh auth login
```

**Merge conflicts:**
```bash
# Standard git workflow
git status
git add .
git commit
./scripts/workflow-automation.sh tasks ship task_12345
```

---

## 🎯 **This Transforms Your Workflow**

**Before:**
1. Read requirement
2. Think about structure
3. Manually create branch
4. Code
5. Remember to commit
6. Write PR description
7. Manual cleanup

**After:**
1. `ai-plan "requirement"`
2. `tasks start task_001`
3. Code
4. `tasks commit task_001 "message"`
5. `tasks ship task_001`
6. `tasks complete task_001`

**Result: 10x faster from idea to shipped code! 🚀**
