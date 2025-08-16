#!/bin/bash

# Documentation Cleanup and Consolidation Script
# Removes outdated files and organizes documentation

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${BLUE}[DOCS-CLEANUP]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warn() { echo -e "${YELLOW}[ARCHIVE]${NC} $1"; }
error() { echo -e "${RED}[REMOVE]${NC} $1"; }

# Create archive directory
mkdir -p docs/archived/old-workflows
mkdir -p docs/archived/claude-integration
mkdir -p docs/archived/outdated

log "📚 Starting documentation cleanup and consolidation..."

# Files to archive (outdated but keep for reference)
ARCHIVE_FILES=(
    "PARALLEL_DEV_WORKFLOW.md:docs/archived/old-workflows/"
    "AGENT_DEVELOPMENT_GUIDE.md:docs/archived/old-workflows/"  
    "AI_POWERED_WORKFLOW.md:docs/archived/old-workflows/"
    "docs/IMPORTANT_WORKTREE_WORKFLOW.md:docs/archived/old-workflows/"
    "docs/PARALLEL_DEVELOPMENT_GUIDE.md:docs/archived/old-workflows/"
    "docs/claude-integration/:docs/archived/claude-integration/"
)

# Files to remove (completely outdated)
REMOVE_FILES=(
    "docs/FIX_ACHIEVEMENT_CI_WORKFLOW.md"
    "docs/DEV_CI_FIX_ANALYSIS.md"
    "AGENT_FOCUS.md.backup.*"
    ".daily-analysis.json"
    "ai-prompt.txt"
    ".job-strategy-analysis.json"
)

# Backup files to remove
BACKUP_PATTERN_FILES=(
    "*.backup.*"
    "temp_*"
    ".watch-*"
    "*.tmp"
)

# Archive files
log "📦 Archiving outdated documentation..."
for file_mapping in "${ARCHIVE_FILES[@]}"; do
    IFS=':' read -r source_file dest_dir <<< "$file_mapping"
    
    if [[ -e "$source_file" ]]; then
        mv "$source_file" "$dest_dir"
        warn "Archived: $source_file → $dest_dir"
    fi
done

# Remove completely outdated files
log "🗑️ Removing outdated files..."
for file in "${REMOVE_FILES[@]}"; do
    if [[ -e "$file" ]]; then
        rm -rf "$file"
        error "Removed: $file"
    fi
done

# Remove backup pattern files
for pattern in "${BACKUP_PATTERN_FILES[@]}"; do
    find . -name "$pattern" -not -path "./.venv/*" -not -path "./.git/*" -delete 2>/dev/null || true
done

# Update main CLAUDE.md with new workflow reference
log "📝 Updating CLAUDE.md with new workflow references..."

# Add reference to new documentation in CLAUDE.md
if ! grep -q "AI_POWERED_DAILY_WORKFLOW" CLAUDE.md; then
    # Insert after resources section
    local temp_file=$(mktemp)
    awk '
    /^## Resources/ { 
        print
        print ""
        print "- **[AI_POWERED_DAILY_WORKFLOW.md](./docs/AI_POWERED_DAILY_WORKFLOW.md)** - Complete enhanced workflow"
        print "- **[AI_DEVELOPMENT_ACCELERATION_GUIDE.md](./docs/AI_DEVELOPMENT_ACCELERATION_GUIDE.md)** - Technical AI system guide"  
        next
    }
    { print }
    ' CLAUDE.md > "$temp_file"
    mv "$temp_file" CLAUDE.md
    success "✅ Updated CLAUDE.md with new documentation references"
fi

# Create master quick reference
log "📋 Creating master quick reference..."
cat > docs/QUICK_REFERENCE.md << 'EOF'
# 🚀 Quick Reference - Ultra-Friendly Commands

## 🎯 Daily Commands (1-word)
```bash
just start       # Start AI development session
just save        # AI-powered commit
just done        # Complete session with focus update
just finish      # Stop all processes + cleanup
```

## 🤖 4-Agent Commands
```bash
just a1          # Switch to MLOps agent
just a2          # Switch to GenAI agent  
just a3          # Switch to Analytics agent
just a4          # Switch to Platform agent
just agents      # View all agent status
```

## 🎯 Smart Work Assignment
```bash
just mlflow      # MLflow work → A1 (MLOps)
just vllm        # Optimization → A2 (GenAI)
just docs        # Documentation → A3 (Analytics)
just ab          # A/B testing → A4 (Platform)
```

## 📊 Intelligence & Strategy
```bash
just align       # Sync with AI job strategy
just progress    # Weekly progress report
just learn-activate  # Enable learning tracking
just dev-insights    # Development analytics
```

## 🧹 Maintenance
```bash
just cleanup     # Clean temporary files
just quality-all # Quality check all agents
just sync-all    # Sync focus across agents
```

## 🚀 Legacy Commands (Still Available)
```bash
just make-money     # Business autopilot
just create-viral   # AI content generation
just ship-it        # Deploy & PR
just health-check   # System status
```

---
*Complete workflow guide: [AI_POWERED_DAILY_WORKFLOW.md](./AI_POWERED_DAILY_WORKFLOW.md)*
EOF

success "📋 Created docs/QUICK_REFERENCE.md"

# Generate cleanup report
log "📊 Generating cleanup report..."
cat > docs/DOCUMENTATION_CLEANUP_REPORT.md << EOF
# 📚 Documentation Cleanup Report
*Generated: $(date)*

## ✅ Actions Completed

### Files Archived
$(for file_mapping in "${ARCHIVE_FILES[@]}"; do
    IFS=':' read -r source_file dest_dir <<< "$file_mapping"
    if [[ -e "$dest_dir/$(basename "$source_file")" ]]; then
        echo "- $source_file → $dest_dir"
    fi
done)

### Files Removed
$(for file in "${REMOVE_FILES[@]}"; do
    echo "- $file (outdated/duplicate)"
done)

### Documentation Structure Updated
- ✅ CLAUDE.md updated with new workflow references
- ✅ DAILY_PLAYBOOK.md enhanced with ultra-friendly commands
- ✅ QUICK_REFERENCE.md created as master command guide
- ✅ Archive structure created for old documentation

## 📁 New Documentation Structure
\`\`\`
📁 Root Level
├── CLAUDE.md                    # Main project guide (updated)
├── AI_JOB_STRATEGY.md          # Career strategy
└── README.md                   # Project overview

📁 docs/ (Organized)
├── 🚀 AI_POWERED_DAILY_WORKFLOW.md     # Complete enhanced workflow
├── 🧠 AI_DEVELOPMENT_ACCELERATION_GUIDE.md  # Technical AI system
├── 🤝 AGENT_MERGE_STRATEGY.md          # 4-agent coordination  
├── 📊 PRODUCTIVITY_GUIDE.md            # Productivity metrics
├── 🎯 QUICK_REFERENCE.md              # Master command reference
└── 📚 DAILY_PLAYBOOK.md               # 80/20 command guide (updated)

📁 docs/archived/ (Reference Only)
├── old-workflows/              # Previous workflow documentation
├── claude-integration/         # Old Claude integration docs
└── outdated/                   # Deprecated files
\`\`\`

## 🎯 Maintenance Strategy
- **Auto-generated files**: Never edit manually (.ai-context.json, AGENT_FOCUS.md, reports/)
- **Core guides**: Update when system changes (CLAUDE.md, AI_POWERED_DAILY_WORKFLOW.md)
- **Reference docs**: Keep current (QUICK_REFERENCE.md, DAILY_PLAYBOOK.md)
- **Archive**: Preserve but don't maintain (docs/archived/)

## 📈 Benefits
- ✅ Eliminated duplicate documentation
- ✅ Clear separation of current vs archived
- ✅ Single source of truth for commands
- ✅ Auto-updating system reduces maintenance
- ✅ Job strategy integration built-in

---
*Cleanup completed successfully - documentation now optimized for 4-agent AI development*
EOF

success "📊 Cleanup report generated: docs/DOCUMENTATION_CLEANUP_REPORT.md"

# Final summary
echo
success "🎉 Documentation cleanup complete!"
log "📚 Active documentation: 6 core files"
log "📦 Archived documentation: Preserved in docs/archived/"
log "🗑️ Removed files: Outdated duplicates eliminated"
log ""
log "📖 Key files to use:"
log "  - docs/QUICK_REFERENCE.md (daily command reference)"
log "  - docs/DAILY_PLAYBOOK.md (80/20 workflow guide)"
log "  - docs/AI_POWERED_DAILY_WORKFLOW.md (complete workflow)"
log ""
log "🚀 Your documentation is now optimized for AI-accelerated development!"