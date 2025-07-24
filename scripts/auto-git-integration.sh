#!/bin/bash

# scripts/auto-git-integration.sh - Seamless git integration for task management
# Automatically creates branches, commits, and PRs based on task workflow

set -euo pipefail

# Constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WORKFLOW_DIR="$PROJECT_ROOT/.workflows"
TASKS_DIR="$WORKFLOW_DIR/tasks"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

# Logging
log_info() { echo -e "${BLUE}[GIT-AUTO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_git() { echo -e "${CYAN}[GIT]${NC} $*"; }

# Get task details from YAML file
get_task_info() {
    local task_id="$1"
    local task_file="$TASKS_DIR/${task_id}.yaml"
    
    if [[ ! -f "$task_file" ]]; then
        log_error "Task file not found: $task_file"
        return 1
    fi
    
    # Extract key information
    local task_name=$(grep "^name:" "$task_file" | cut -d'"' -f2)
    local epic_id=$(grep "^epic_id:" "$task_file" | cut -d'"' -f2)
    local feature_id=$(grep "^feature_id:" "$task_file" | cut -d'"' -f2 2>/dev/null || echo "")
    local description=$(grep "^description:" "$task_file" | cut -d'"' -f2)
    local priority=$(grep "^priority:" "$task_file" | cut -d'"' -f2)
    local effort=$(grep "^effort:" "$task_file" | cut -d'"' -f2)
    
    # Export for use by other functions
    export TASK_NAME="$task_name"
    export EPIC_ID="$epic_id"
    export FEATURE_ID="$feature_id"
    export TASK_DESCRIPTION="$description"
    export TASK_PRIORITY="$priority"
    export TASK_EFFORT="$effort"
}

# Generate branch name from task info
generate_branch_name() {
    local task_id="$1"
    local epic_part=""
    local task_part=""
    
    # Get epic identifier (last part of epic ID)
    if [[ -n "$EPIC_ID" ]]; then
        epic_part=$(echo "$EPIC_ID" | sed 's/.*_//')
    fi
    
    # Clean task name for branch
    task_part=$(echo "$TASK_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-\|-$//g' | cut -c1-40)
    
    echo "task-${epic_part}-${task_part}"
}

# Start working on a task - create branch and update status
start_task() {
    local task_id="$1"
    
    log_info "Starting work on task: $task_id"
    
    # Get task information
    get_task_info "$task_id"
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        log_error "Not in a git repository"
        return 1
    fi
    
    # Ensure we're on main and up to date
    log_git "Ensuring main branch is up to date..."
    local current_branch=$(git branch --show-current)
    
    if [[ "$current_branch" != "main" ]]; then
        git checkout main
    fi
    
    git pull origin main
    
    # Generate branch name
    local branch_name=$(generate_branch_name "$task_id")
    
    # Check if branch already exists
    if git show-ref --verify --quiet "refs/heads/$branch_name"; then
        log_info "Branch $branch_name already exists, checking out..."
        git checkout "$branch_name"
    else
        log_git "Creating new branch: $branch_name"
        git checkout -b "$branch_name"
        git push -u origin "$branch_name"
    fi
    
    # Update task status
    update_task_status "$task_id" "in_progress"
    
    # Set up commit template
    setup_commit_template "$task_id"
    
    log_success "Ready to work on: $TASK_NAME"
    log_info "Branch: $branch_name"
    log_info "Task: $TASK_DESCRIPTION"
    
    # Show next steps
    echo
    echo "🚀 Next steps:"
    echo "   1. Make your changes"
    echo "   2. Commit: git-auto commit $task_id \"your message\""
    echo "   3. Ship: git-auto ship $task_id"
}

# Update task status in YAML file
update_task_status() {
    local task_id="$1"
    local new_status="$2"
    local task_file="$TASKS_DIR/${task_id}.yaml"
    
    if [[ ! -f "$task_file" ]]; then
        log_error "Task file not found: $task_file"
        return 1
    fi
    
    # Update status and timestamp
    sed -i.bak "s/^status: .*/status: \"$new_status\"/" "$task_file"
    sed -i.bak "s/^updated: .*/updated: \"$(date +%Y-%m-%dT%H:%M:%S%z)\"/" "$task_file"
    rm "${task_file}.bak"
    
    log_success "Updated task $task_id status: $new_status"
}

# Setup commit message template for the task
setup_commit_template() {
    local task_id="$1"
    
    cat > .gitmessage << EOF
# Task: $TASK_NAME ($task_id)
# Epic: $EPIC_ID
# Priority: $TASK_PRIORITY | Effort: $TASK_EFFORT
#
# Description: $TASK_DESCRIPTION
#
# Commit format: <type>: <description> (closes $task_id)
# Types: feat, fix, refactor, test, docs, style, chore
#
# Example: feat: implement JWT authentication middleware (closes $task_id)
EOF
    
    git config commit.template .gitmessage
    log_info "Commit template set up for task context"
}

# Smart commit with task context
commit_with_task() {
    local task_id="$1"
    local commit_message="$2"
    
    get_task_info "$task_id"
    
    # Enhance commit message with task context
    local enhanced_message="$commit_message

Task: $TASK_NAME ($task_id)
Epic: $EPIC_ID
Priority: $TASK_PRIORITY

Co-authored-by: AI Planning System <ai@threads-agent.dev>"
    
    # Stage all changes
    git add -A
    
    # Commit with enhanced message
    git commit -m "$enhanced_message"
    
    # Push to remote
    git push
    
    log_success "Committed and pushed changes for task: $task_id"
    
    # Update task progress (could be automated based on file changes)
    prompt_task_progress "$task_id"
}

# Prompt user to update task progress
prompt_task_progress() {
    local task_id="$1"
    
    echo
    echo "📊 Update task progress?"
    echo "1) 25% - Getting started"
    echo "2) 50% - Half done"
    echo "3) 75% - Almost complete"
    echo "4) 100% - Ready for review"
    echo "5) Skip"
    
    read -p "Choose (1-5): " choice
    
    case $choice in
        1) update_task_progress "$task_id" 25 ;;
        2) update_task_progress "$task_id" 50 ;;
        3) update_task_progress "$task_id" 75 ;;
        4) update_task_progress "$task_id" 100 && update_task_status "$task_id" "review" ;;
        5) log_info "Skipping progress update" ;;
        *) log_info "Invalid choice, skipping" ;;
    esac
}

# Update task progress percentage
update_task_progress() {
    local task_id="$1"
    local progress="$2"
    local task_file="$TASKS_DIR/${task_id}.yaml"
    
    sed -i.bak "s/^progress: .*/progress: $progress/" "$task_file"
    rm "${task_file}.bak"
    
    log_success "Updated task progress: $progress%"
}

# Ship the task - create PR and update status
ship_task() {
    local task_id="$1"
    local pr_title="${2:-}"
    
    get_task_info "$task_id"
    
    # Default PR title if not provided
    if [[ -z "$pr_title" ]]; then
        pr_title="$TASK_NAME"
    fi
    
    # Generate PR description from task info
    local pr_description=$(generate_pr_description "$task_id")
    
    # Check if gh CLI is available
    if command -v gh >/dev/null 2>&1; then
        log_git "Creating PR with GitHub CLI..."
        
        # Create PR
        local pr_url=$(gh pr create \
            --title "$pr_title" \
            --body "$pr_description" \
            --label "task" \
            --label "$TASK_PRIORITY" \
            --label "$TASK_EFFORT" 2>/dev/null || echo "")
        
        if [[ -n "$pr_url" ]]; then
            log_success "PR created: $pr_url"
            
            # Update task with PR info
            echo "pr_url: \"$pr_url\"" >> "$TASKS_DIR/${task_id}.yaml"
            update_task_status "$task_id" "review"
            
            # Open PR in browser if possible
            if command -v open >/dev/null 2>&1; then
                open "$pr_url"
            fi
        else
            log_error "Failed to create PR with gh CLI"
            manual_pr_instructions "$task_id"
        fi
    else
        log_error "GitHub CLI (gh) not found"
        manual_pr_instructions "$task_id"
    fi
}

# Generate PR description from task
generate_pr_description() {
    local task_id="$1"
    
    cat << EOF
## 📋 Task: $TASK_NAME

**Task ID:** \`$task_id\`  
**Epic:** \`$EPIC_ID\`  
**Priority:** $TASK_PRIORITY | **Effort:** $TASK_EFFORT

### Description
$TASK_DESCRIPTION

### Changes Made
<!-- Describe what you implemented -->

### Testing
<!-- How was this tested? -->
- [ ] Unit tests added/updated
- [ ] Manual testing completed
- [ ] Integration tests pass

### Checklist
- [ ] Code follows project conventions
- [ ] Documentation updated if needed
- [ ] No breaking changes
- [ ] Task requirements met

---
*Auto-generated from task management system*
🤖 **AI-Planned** | 📋 **Task-Driven** | 🚀 **Ready for Review**
EOF
}

# Show manual PR creation instructions
manual_pr_instructions() {
    local task_id="$1"
    local branch_name=$(git branch --show-current)
    
    echo
    echo "📝 Manual PR Creation:"
    echo "1. Go to: https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]\([^.]*\).*/\1/')/compare/$branch_name?expand=1"
    echo "2. Title: $TASK_NAME"
    echo "3. Use description from: generate_pr_description $task_id"
    echo
    
    update_task_status "$task_id" "review"
}

# Complete a task - merge and cleanup
complete_task() {
    local task_id="$1"
    
    get_task_info "$task_id"
    
    # Update task status
    update_task_status "$task_id" "completed"
    update_task_progress "$task_id" 100
    
    # Add completion timestamp
    echo "completed_date: \"$(date +%Y-%m-%dT%H:%M:%S%z)\"" >> "$TASKS_DIR/${task_id}.yaml"
    
    # Switch back to main
    git checkout main
    git pull origin main
    
    # Optional: Delete the feature branch (user choice)
    local branch_name=$(generate_branch_name "$task_id")
    echo
    echo "🧹 Clean up feature branch?"
    read -p "Delete branch '$branch_name'? (y/N): " delete_branch
    
    if [[ "$delete_branch" =~ ^[Yy]$ ]]; then
        git branch -d "$branch_name" 2>/dev/null || true
        git push origin --delete "$branch_name" 2>/dev/null || true
        log_success "Cleaned up branch: $branch_name"
    fi
    
    log_success "Task completed: $TASK_NAME"
    
    # Show next available tasks
    show_next_tasks "$EPIC_ID"
}

# Show next available tasks from the same epic
show_next_tasks() {
    local epic_id="$1"
    
    echo
    echo "🎯 Next available tasks from this epic:"
    
    local count=0
    for task_file in "$TASKS_DIR"/task_*.yaml; do
        [[ -f "$task_file" ]] || continue
        
        local file_epic=$(grep "^epic_id:" "$task_file" | cut -d'"' -f2)
        local file_status=$(grep "^status:" "$task_file" | cut -d'"' -f2)
        
        if [[ "$file_epic" == "$epic_id" ]] && [[ "$file_status" == "pending" ]]; then
            local file_task_id=$(basename "$task_file" .yaml)
            local file_name=$(grep "^name:" "$task_file" | cut -d'"' -f2)
            local file_priority=$(grep "^priority:" "$task_file" | cut -d'"' -f2)
            
            echo "   $file_task_id: $file_name [$file_priority]"
            ((count++))
            
            if [[ $count -ge 3 ]]; then
                echo "   ... (use 'tasks list $epic_id' for full list)"
                break
            fi
        fi
    done
    
    if [[ $count -eq 0 ]]; then
        echo "   🎉 No pending tasks! Epic might be complete."
    fi
}

# Show help
show_help() {
    cat << EOF
🔄 Auto-Git Integration for Task Management

USAGE:
    $0 <command> <task_id> [options]

COMMANDS:
    start <task_id>              Start working on task (create branch, update status)
    commit <task_id> "message"   Commit with task context and enhanced message
    ship <task_id> ["pr_title"]  Create PR from task description
    complete <task_id>           Mark task complete and cleanup

WORKFLOW:
    1. git-auto start task_12345        # Creates branch, sets up workspace
    2. # ... make your changes ...
    3. git-auto commit task_12345 "implement auth middleware"
    4. git-auto ship task_12345          # Creates PR with task context
    5. # ... after PR review/merge ...
    6. git-auto complete task_12345      # Mark done, cleanup

FEATURES:
    🌟 Auto-branch creation with smart naming
    📝 Enhanced commit messages with task context
    🚀 PR generation with task descriptions
    📊 Progress tracking integration
    🧹 Automatic cleanup and next task suggestions

EXAMPLES:
    # Start working on authentication task
    $0 start task_feat_epic123_45678
    
    # Commit progress with context
    $0 commit task_feat_epic123_45678 "add JWT middleware and validation"
    
    # Ship for review
    $0 ship task_feat_epic123_45678 "feat: implement JWT authentication"

EOF
}

# Main execution
main() {
    cd "$PROJECT_ROOT"
    
    case "${1:-help}" in
        start)
            if [[ $# -lt 2 ]]; then
                log_error "Usage: start <task_id>"
                exit 1
            fi
            start_task "$2"
            ;;
        commit)
            if [[ $# -lt 3 ]]; then
                log_error "Usage: commit <task_id> \"message\""
                exit 1
            fi
            commit_with_task "$2" "$3"
            ;;
        ship)
            if [[ $# -lt 2 ]]; then
                log_error "Usage: ship <task_id> [\"pr_title\"]"
                exit 1
            fi
            ship_task "$2" "${3:-}"
            ;;
        complete)
            if [[ $# -lt 2 ]]; then
                log_error "Usage: complete <task_id>"
                exit 1
            fi
            complete_task "$2"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: ${1:-}"
            show_help
            exit 1
            ;;
    esac
}

main "$@"