#!/bin/bash

# Demo version of AI epic planner that uses pre-defined examples
# For testing without OpenAI API key

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[AI-DEMO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_ai() { echo -e "${PURPLE}[AI-DEMO]${NC} $*"; }

demo_ai_planning() {
    local requirement="$1"

    log_ai "Demo: Planning epic for '$requirement'"
    log_info "In real mode, this would call OpenAI API..."

    # Simulate AI thinking
    echo -n "🤖 AI is analyzing your requirement"
    for i in {1..3}; do
        sleep 0.5
        echo -n "."
    done
    echo " Done!"

    # Create a demo epic based on the requirement
    local epic_id="epic_demo_$(date +%s)"
    local epic_name="Demo: $(echo "$requirement" | cut -c1-50)"

    mkdir -p "$PROJECT_ROOT/.workflows/epics"

    cat > "$PROJECT_ROOT/.workflows/epics/${epic_id}.yaml" << EOF
id: "$epic_id"
name: "$epic_name"
description: "AI-generated demo epic based on: $requirement"
complexity: "medium"
created: "$(date +%Y-%m-%dT%H:%M:%S%z)"
status: "planning"
ai_generated: true
demo_mode: true

# Epic Analysis
estimated_effort: "4 weeks"
risk_level: "medium"
business_value: "Demonstrates AI planning capabilities"

# Demo Features
features:
  - id: "feat_${epic_id}_001"
    name: "Core Implementation"
    effort: "large"
    priority: "high"
  - id: "feat_${epic_id}_002"
    name: "Testing & Quality"
    effort: "medium"
    priority: "high"
  - id: "feat_${epic_id}_003"
    name: "Documentation"
    effort: "small"
    priority: "medium"

# Milestones
milestones:
  - name: "Planning Complete"
    target_date: "$(date -v+1w +%Y-%m-%d)"
    criteria: ["Requirements clarified", "Architecture approved"]
  - name: "MVP Ready"
    target_date: "$(date -v+3w +%Y-%m-%d)"
    criteria: ["Core functionality working", "Basic tests passing"]

# Automation Configuration
automation:
  project_board: "local"
  branch_prefix: "demo-epic"
  ci_pipeline: "full"
EOF

    # Update registry
    if [[ ! -f "$PROJECT_ROOT/.workflows/active_epics.json" ]]; then
        echo '{"epics": []}' > "$PROJECT_ROOT/.workflows/active_epics.json"
    fi

    jq --arg id "$epic_id" --arg name "$epic_name" --arg status "planning" --arg created "$(date +%Y-%m-%dT%H:%M:%S%z)" \
        '.epics += [{"id": $id, "name": $name, "status": $status, "created": $created}]' \
        "$PROJECT_ROOT/.workflows/active_epics.json" > "$PROJECT_ROOT/.workflows/active_epics.json.tmp" && \
        mv "$PROJECT_ROOT/.workflows/active_epics.json.tmp" "$PROJECT_ROOT/.workflows/active_epics.json"

    log_success "Demo epic created: $epic_id"
    echo
    echo "📋 This is a demo epic. For real AI planning:"
    echo "   1. Set OPENAI_API_KEY environment variable"
    echo "   2. Use: ./scripts/ai-epic-planner.sh \"your requirement\""
    echo
    echo "📁 View demo epic:"
    echo "   cat .workflows/epics/${epic_id}.yaml"
}

if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    echo "🤖 AI Epic Planner - Demo Mode"
    echo "Usage: $0 \"your requirement\""
    echo "This creates a demo epic without calling OpenAI API"
    exit 0
fi

if [[ $# -eq 0 ]]; then
    echo "Usage: $0 \"your requirement\""
    exit 1
fi

demo_ai_planning "$1"
