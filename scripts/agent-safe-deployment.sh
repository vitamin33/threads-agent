#!/bin/bash

# Agent Safe Deployment - Prevents merge conflicts
# Only syncs non-conflicting files to agent worktrees

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${BLUE}[SAFE-DEPLOY]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# Files that are safe to sync (won't cause merge conflicts)
SAFE_TO_SYNC=(
    "scripts/ai-dev-acceleration.sh"
    "scripts/auto-update-agent-focus.sh"
    "scripts/4-agent-turbo.sh"
    "scripts/ai-job-strategy-sync.sh"
    "scripts/cleanup.sh"
    "scripts/smart-tdd.sh"
    "docs/AI_DEVELOPMENT_ACCELERATION_GUIDE.md"
    "docs/AI_POWERED_DAILY_WORKFLOW.md"
    "docs/AGENT_MERGE_STRATEGY.md"
    "docs/QUICK_REFERENCE.md"
    ".vscode/settings.json"
    ".claude/custom-commands.json"
)

# Files that should be agent-specific (local only)
AGENT_LOCAL_FILES=(
    "AGENT_FOCUS.md"
    ".ai-context.json"
    ".dev-insights.json"
    ".agent.env"
    ".agent-config.local"
    "*.local"
)

# Files that should never sync (high conflict risk)
NEVER_SYNC=(
    "Justfile"          # Each agent may have customizations
    "CLAUDE.md"         # May have agent-specific notes
    ".pre-commit-config.yaml"  # May have different hooks
)

AGENT_WORKTREES=(
    "../wt-a1-mlops:a1:Infrastructure & Core Platform"
    "../wt-a2-genai:a2:AI/ML Services & Processing"
    "../wt-a3-analytics:a3:Data & Analytics Pipeline"
    "../wt-a4-platform:a4:Business & Revenue Systems"
)

# Service mapping for agent scope redesign
declare -A AGENT_SERVICES=(
    ["a1"]="orchestrator celery_worker common event_bus mlflow mlflow_service performance_monitor chaos_engineering"
    ["a2"]="persona_runtime rag_pipeline vllm_service prompt_engineering conversation_engine viral_engine viral_pattern_engine ml_autoscaling"
    ["a3"]="achievement_collector dashboard dashboard_api dashboard_frontend viral_metrics pattern_analyzer viral_learning_flywheel tech_doc_generator"
    ["a4"]="revenue finops_engine ab_testing_framework threads_adaptor fake_threads viral_scraper"
)

# Safe deploy to specific agent
safe_deploy_to_agent() {
    local agent_path="$1"
    local agent_id="$2" 
    local agent_type="$3"
    
    if [[ ! -d "$agent_path" ]]; then
        warn "Agent worktree not found: $agent_path"
        return 1
    fi
    
    log "🔒 Safe deployment to $agent_type ($agent_id)..."
    
    # Create directories
    mkdir -p "$agent_path/scripts"
    mkdir -p "$agent_path/docs"
    mkdir -p "$agent_path/.vscode"
    mkdir -p "$agent_path/.claude"
    
    # Sync only safe files
    local synced=0
    for file in "${SAFE_TO_SYNC[@]}"; do
        if [[ -f "$file" ]]; then
            cp "$file" "$agent_path/$file"
            chmod +x "$agent_path/$file" 2>/dev/null || true
            ((synced++))
        fi
    done
    
    # Create agent-specific AGENT_FOCUS.md (local only)
    local services="${AGENT_SERVICES[$agent_id]}"
    cat > "$agent_path/AGENT_FOCUS.md.local" << EOF
# Agent $agent_type ($agent_id) - Service-Based Focus

## Service Ownership ($(echo $services | wc -w) services)
$(echo "$services" | tr ' ' '\n' | sed 's/^/- services\//' | sed 's/$\//')

## Responsibilities
**$agent_type**
- End-to-end ownership of assigned services
- Testing and quality for service group
- Documentation and monitoring
- Integration with other agent services

## Daily Workflow
\`\`\`bash
# Start focused session
export AGENT_ID="$agent_id"
just start

# Work on any service in your domain
just tdd "service enhancement"
just save

# Coordinate with other agents as needed
just agents  # Check other agent status
\`\`\`

## Job Strategy Alignment
**Target Roles**: Platform Engineer, ML Engineer, Data Engineer
**Skills Demonstrated**: Service ownership, testing, documentation, integration

---
*Agent-specific file - local only, not committed*
EOF

    # Create agent-specific .gitignore additions
    cat > "$agent_path/.gitignore.agent" << EOF
# Agent-specific files (never commit these)
AGENT_FOCUS.md.local
.ai-context.json
.dev-insights.json
.agent.env
.agent-config.local
*.local
.tdd-prompt.txt
.test-gen-prompt.txt
.daily-analysis.json
.job-strategy-analysis.json

# Temporary development files
.watch-dev.sh
.test-watch.sh
.learning-hooks.sh
*.tmp
temp_*
EOF
    
    success "🔒 Safe deployment complete: $synced files synced"
    success "📋 Agent-specific config: AGENT_FOCUS.md.local"
    warn "⚠️ Add .gitignore.agent contents to main .gitignore"
}

# Deploy to all agents safely
safe_deploy_all() {
    log "🔒 Safe deployment to all 4 agent worktrees (conflict-free)..."
    
    for agent_info in "${AGENT_WORKTREES[@]}"; do
        IFS=':' read -r agent_path agent_id agent_type <<< "$agent_info"
        safe_deploy_to_agent "$agent_path" "$agent_id" "$agent_type"
        echo
    done
    
    success "✅ Safe deployment complete - no merge conflict risk!"
    
    log "📋 Next steps:"
    log "1. Update main .gitignore with agent-specific patterns"
    log "2. Use AGENT_FOCUS.md.local in each agent (not committed)"
    log "3. Justfile customizations stay local to each agent"
    log "4. Merge agents without conflicts"
}

# Update main .gitignore with agent patterns
update_main_gitignore() {
    log "📝 Updating main .gitignore for conflict-free merges..."
    
    # Add agent-specific patterns to main .gitignore
    cat >> .gitignore << 'EOF'

# ═══════════════════════════════════════════════════════
# Agent-Specific Development Files (Never Commit)
# ═══════════════════════════════════════════════════════

# Agent configurations (local only)
AGENT_FOCUS.md.local
.agent-config.local
.agent.env.local

# AI development artifacts (temporary)
.ai-context.json
.dev-insights.json
.tdd-prompt.txt
.test-gen-prompt.txt
.daily-analysis.json
.job-strategy-analysis.json

# Development watchers (temporary)
.watch-dev.sh
.test-watch.sh
.learning-hooks.sh
.watch-pid
.test-watch-pid

# Agent deployment artifacts
.agent-coordination.json

# Temporary development files
*.local.tmp
temp_dev_*
.dev-temp.*

EOF
    
    success "📝 Main .gitignore updated with agent-specific patterns"
    log "💡 These files will never cause merge conflicts"
}

# Main execution
case "${1:-safe}" in
    "safe")
        safe_deploy_all
        ;;
    "gitignore")
        update_main_gitignore
        ;;
    "test")
        # Test if any conflicts would occur
        log "🧪 Testing for potential merge conflicts..."
        for agent_info in "${AGENT_WORKTREES[@]}"; do
            IFS=':' read -r agent_path agent_id agent_type <<< "$agent_info"
            if [[ -d "$agent_path" ]]; then
                local conflicts=$(cd "$agent_path" && git status --porcelain | grep -E "^(UU|AA|DD)" | wc -l || echo "0")
                if [[ $conflicts -gt 0 ]]; then
                    warn "$agent_type: $conflicts potential conflicts"
                else
                    success "$agent_type: No conflicts detected"
                fi
            fi
        done
        ;;
    *)
        cat << EOF
🔒 Agent Safe Deployment System

Usage: $0 [command]

Commands:
  safe       Deploy only safe files (no merge conflicts)
  gitignore  Update main .gitignore with agent patterns
  test       Check for potential merge conflicts

Benefits:
  - Prevents merge conflicts between agents
  - Allows safe file syncing without git issues
  - Maintains agent independence
  - Enables conflict-free merging

EOF
        ;;
esac