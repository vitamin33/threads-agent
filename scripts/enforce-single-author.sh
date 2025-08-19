#!/bin/bash

# Strict Single Author Enforcement
# Ensures only your git config author appears in all commits across all worktrees

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${BLUE}[AUTHOR-ENFORCE]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Your git config (only valid author)
VALID_AUTHOR_NAME="Vitalii Serbyn"
VALID_AUTHOR_EMAIL="serbyn.vitalii@gmail.com"

AGENT_WORKTREES=(
    "/Users/vitaliiserbyn/development/threads-agent:main"
    "/Users/vitaliiserbyn/development/wt-a1-mlops:a1"
    "/Users/vitaliiserbyn/development/wt-a2-genai:a2"
    "/Users/vitaliiserbyn/development/wt-a3-analytics:a3"
    "/Users/vitaliiserbyn/development/wt-a4-platform:a4"
)

# Configure git for single author in worktree
configure_single_author() {
    local worktree_path="$1"
    local agent_id="$2"
    
    if [[ ! -d "$worktree_path" ]]; then
        warn "Worktree not found: $worktree_path"
        return 1
    fi
    
    log "🔒 Configuring single author for $agent_id at $worktree_path"
    
    cd "$worktree_path"
    
    # Set strict git config
    git config user.name "$VALID_AUTHOR_NAME"
    git config user.email "$VALID_AUTHOR_EMAIL"
    
    # Disable any co-author templates
    git config commit.template ""
    git config commit.cleanup "strip"
    
    # Create pre-commit hook to block Claude co-author
    cat > .git/hooks/pre-commit-author-check << 'EOF'
#!/bin/bash

# Strict author enforcement - blocks commits with Claude co-author

# Check commit message for Claude co-author patterns
commit_msg_file=".git/COMMIT_EDITMSG"
if [[ -f "$commit_msg_file" ]]; then
    if grep -q "Co-Authored-By.*Claude\|Generated with.*Claude Code\|🤖 Generated" "$commit_msg_file"; then
        echo "❌ BLOCKED: Commit contains Claude co-author information"
        echo "   Only your authorship should appear in git history"
        echo "   Remove Co-Authored-By lines and regenerate commit"
        exit 1
    fi
fi

# Check git config
current_author=$(git config user.name)
current_email=$(git config user.email)

if [[ "$current_author" != "Vitalii Serbyn" ]]; then
    echo "❌ BLOCKED: Invalid git author: '$current_author'"
    echo "   Run: git config user.name 'Vitalii Serbyn'"
    exit 1
fi

if [[ "$current_email" != "serbyn.vitalii@gmail.com" ]]; then
    echo "❌ BLOCKED: Invalid git email: '$current_email'"  
    echo "   Run: git config user.email 'serbyn.vitalii@gmail.com'"
    exit 1
fi

echo "✅ Author verification passed: $current_author <$current_email>"
EOF

    chmod +x .git/hooks/pre-commit-author-check
    
    # Create commit-msg hook to strip Claude co-author info
    cat > .git/hooks/commit-msg << 'EOF'
#!/bin/bash

# Strip any Claude co-author information from commit messages

commit_msg_file="$1"

# Remove Claude co-author lines
sed -i.bak '/Co-Authored-By.*Claude/d' "$commit_msg_file"
sed -i.bak '/🤖 Generated with.*Claude Code/d' "$commit_msg_file"
sed -i.bak '/Generated with.*Claude/d' "$commit_msg_file"

# Remove trailing empty lines
sed -i.bak -e :a -e '/^\s*$/N;$!ba' -e 's/\n*$//' "$commit_msg_file"

# Clean up backup file
rm -f "${commit_msg_file}.bak"

echo "✅ Commit message cleaned - no Claude co-author information"
EOF

    chmod +x .git/hooks/commit-msg
    
    success "✅ Single author enforcement configured for $agent_id"
    success "   Author: $VALID_AUTHOR_NAME <$VALID_AUTHOR_EMAIL>"
}

# Audit existing commits for Claude co-author
audit_commits() {
    log "🔍 Auditing commit history for Claude co-author violations..."
    
    for worktree_info in "${AGENT_WORKTREES[@]}"; do
        IFS=':' read -r worktree_path agent_id <<< "$worktree_info"
        
        if [[ -d "$worktree_path" ]]; then
            cd "$worktree_path"
            
            # Check recent commits for Claude co-author
            local violations=$(git log --oneline -20 | grep -c "🤖\|Claude" || echo "0")
            local co_author_commits=$(git log --grep="Co-Authored-By.*Claude" --oneline -20 | wc -l || echo "0")
            
            if [[ $violations -gt 0 || $co_author_commits -gt 0 ]]; then
                warn "⚠️ $agent_id: Found $violations commits with Claude references"
                warn "   Co-author violations: $co_author_commits"
                
                # Show specific violations
                git log --oneline -10 | grep "🤖\|Claude" | head -3 | while read commit; do
                    warn "   - $commit"
                done
            else
                success "✅ $agent_id: Clean commit history (no Claude co-author)"
            fi
        fi
    done
}

# Configure all worktrees
configure_all() {
    log "🔒 Configuring strict single author enforcement across all worktrees..."
    
    local configured=0
    local failed=0
    
    for worktree_info in "${AGENT_WORKTREES[@]}"; do
        IFS=':' read -r worktree_path agent_id <<< "$worktree_info"
        
        if configure_single_author "$worktree_path" "$agent_id"; then
            ((configured++))
        else
            ((failed++))
        fi
    done
    
    success "✅ Single author enforcement: $configured configured, $failed failed"
    
    # Update AI commit scripts to never add co-author
    log "🔧 Updating AI commit scripts to enforce single author..."
    update_commit_scripts
}

# Update commit scripts to never add Claude co-author
update_commit_scripts() {
    local scripts=(
        "scripts/ai-smart-commit.sh"
        "scripts/auto-update-agent-focus.sh"
        "scripts/ai-dev-acceleration.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [[ -f "$script" ]]; then
            # Remove any Claude co-author additions
            sed -i.bak 's/Co-Authored-By.*Claude.*//g' "$script"
            sed -i.bak 's/🤖 Generated with.*Claude Code.*//g' "$script"
            sed -i.bak '/Generated with.*Claude/d' "$script"
            rm -f "${script}.bak"
            
            success "✅ Cleaned $script - no Claude co-author additions"
        fi
    done
}

# Create commit template that prevents Claude co-author
create_commit_template() {
    log "📝 Creating commit templates that enforce single authorship..."
    
    for worktree_info in "${AGENT_WORKTREES[@]}"; do
        IFS=':' read -r worktree_path agent_id <<< "$worktree_info"
        
        if [[ -d "$worktree_path" ]]; then
            cd "$worktree_path"
            
            # Create commit template
            cat > .gitmessage << 'EOF'
# Commit message template - SINGLE AUTHOR ONLY
# 
# Format: <type>: <description>
#
# Types: feat, fix, docs, style, refactor, test, chore
#
# STRICT RULE: NO Claude co-author information allowed
# - No "Co-Authored-By: Claude" lines
# - No "Generated with Claude Code" lines  
# - Only your authorship should appear
#
# Your commits should reflect YOUR work and expertise
# for professional portfolio and career advancement
EOF

            git config commit.template ".gitmessage"
            success "✅ Commit template configured for $agent_id"
        fi
    done
}

# Validate current git configuration
validate_config() {
    log "🔍 Validating git configuration across all worktrees..."
    
    for worktree_info in "${AGENT_WORKTREES[@]}"; do
        IFS=':' read -r worktree_path agent_id <<< "$worktree_info"
        
        if [[ -d "$worktree_path" ]]; then
            cd "$worktree_path"
            
            local current_name=$(git config user.name)
            local current_email=$(git config user.email)
            
            if [[ "$current_name" == "$VALID_AUTHOR_NAME" && "$current_email" == "$VALID_AUTHOR_EMAIL" ]]; then
                success "✅ $agent_id: Correct author configured"
            else
                error "❌ $agent_id: Invalid author - '$current_name' <$current_email>"
                error "   Should be: '$VALID_AUTHOR_NAME' <$VALID_AUTHOR_EMAIL>"
            fi
        fi
    done
}

# Main execution
case "${1:-configure}" in
    "configure")
        configure_all
        create_commit_template
        ;;
    "audit")
        audit_commits
        ;;
    "validate")
        validate_config
        ;;
    "all")
        configure_all
        create_commit_template
        audit_commits
        validate_config
        ;;
    *)
        cat << EOF
🔒 Strict Single Author Enforcement System

Usage: $0 [command]

Commands:
  configure   Configure all worktrees for single author only
  audit       Audit commit history for Claude co-author violations
  validate    Validate git configuration across worktrees
  all         Run complete enforcement setup

Features:
  ✅ Blocks commits with Claude co-author information
  ✅ Enforces your git config across all worktrees
  ✅ Creates commit templates preventing co-author additions
  ✅ Audits existing commits for violations
  ✅ Updates AI scripts to never add Claude co-author

Professional Standard:
  Only YOUR authorship appears in git history for:
  - Portfolio credibility
  - Career advancement  
  - Professional representation
  - Interview discussions

EOF
        ;;
esac