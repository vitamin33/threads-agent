#!/bin/bash

# scripts/ai-epic-planner.sh - AI-powered epic breakdown and planning
# Uses OpenAI to intelligently break down high-level requirements into epics, features, and tasks

set -euo pipefail

# Constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WORKFLOW_DIR="$PROJECT_ROOT/.workflows"
EPICS_DIR="$WORKFLOW_DIR/epics"
FEATURES_DIR="$WORKFLOW_DIR/features"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Source common utilities
source "$SCRIPT_DIR/workflow-automation.sh" 2>/dev/null || true

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
log_info() { echo -e "${BLUE}[AI-PLAN]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_ai() { echo -e "${PURPLE}[AI]${NC} $*"; }

# AI Planning prompt template
get_planning_prompt() {
    local requirement="$1"
    local context="${2:-}"

    cat << EOF
You are an expert software architect and project planner. Break down this requirement into a comprehensive implementation plan.

REQUIREMENT: $requirement

CONTEXT: $context

Please provide a detailed breakdown in the following EXACT YAML format:

\`\`\`yaml
epic:
  name: "Clear, actionable epic name"
  description: "2-3 sentence description of the epic's goal and value"
  complexity: "small|medium|large|xl"
  estimated_weeks: 2-6
  business_value: "Description of business impact"
  technical_approach: "High-level technical strategy"
  risks:
    - "Risk 1"
    - "Risk 2"

features:
  - name: "Feature 1 Name"
    description: "What this feature accomplishes"
    effort: "small|medium|large"
    priority: "high|medium|low"
    category: "backend|frontend|infrastructure|testing|docs"
    dependencies: []
    acceptance_criteria:
      - "User can..."
      - "System should..."
    tasks:
      - name: "Specific task 1"
        effort_hours: 2-4
        description: "Clear action item"
        technical_notes: "Implementation approach"
      - name: "Specific task 2"
        effort_hours: 1-2
        description: "Clear action item"
        technical_notes: "Implementation approach"

  - name: "Feature 2 Name"
    description: "What this feature accomplishes"
    effort: "medium"
    priority: "high"
    category: "backend"
    dependencies: ["Feature 1 Name"]
    acceptance_criteria:
      - "Criterion 1"
    tasks:
      - name: "Task name"
        effort_hours: 4-8
        description: "Task description"
        technical_notes: "Notes"

milestones:
  - name: "Milestone 1"
    week: 1
    deliverables:
      - "Working prototype of X"
      - "Documentation for Y"
  - name: "Milestone 2"
    week: 3
    deliverables:
      - "Feature X complete"
      - "Integration tests passing"

success_metrics:
  - metric: "Performance metric"
    target: "< 200ms response time"
    measurement: "How to measure"
  - metric: "Business metric"
    target: "20% increase in X"
    measurement: "How to measure"
\`\`\`

IMPORTANT GUIDELINES:
1. Be specific and actionable in task descriptions
2. Ensure realistic time estimates
3. Consider dependencies between features
4. Include testing and documentation tasks
5. Think about deployment and monitoring
6. Each feature should have 2-5 concrete tasks
7. Tasks should be 1-8 hours of work
8. Use the exact YAML structure provided
EOF
}

# Parse YAML response and create epic/features
process_ai_response() {
    local response="$1"
    local yaml_content=""

    # Extract YAML content between code blocks
    yaml_content=$(echo "$response" | sed -n '/^```yaml$/,/^```$/p' | sed '1d;$d')

    if [[ -z "$yaml_content" ]]; then
        log_error "No YAML content found in AI response"
        return 1
    fi

    # Save to temporary file for processing
    local temp_file="/tmp/ai_plan_${TIMESTAMP}.yaml"
    echo "$yaml_content" > "$temp_file"

    # Parse epic information
    local epic_name=$(yq eval '.epic.name' "$temp_file" 2>/dev/null || echo "")
    local epic_description=$(yq eval '.epic.description' "$temp_file" 2>/dev/null || echo "")
    local epic_complexity=$(yq eval '.epic.complexity' "$temp_file" 2>/dev/null || echo "medium")
    local estimated_weeks=$(yq eval '.epic.estimated_weeks' "$temp_file" 2>/dev/null || echo "4")

    if [[ -z "$epic_name" ]]; then
        log_error "Failed to parse epic name from AI response"
        return 1
    fi

    log_info "Creating epic: $epic_name"

    # Create epic
    local epic_id="epic_$(date +%s)"
    cat > "$EPICS_DIR/${epic_id}.yaml" << EOF
id: "$epic_id"
name: "$epic_name"
description: "$epic_description"
complexity: "$epic_complexity"
created: "$(date +%Y-%m-%dT%H:%M:%S%z)"
status: "planning"
lifecycle_stage: "inception"
ai_generated: true

# Epic Analysis
estimated_effort: "${estimated_weeks} weeks"
risk_level: "medium"
business_value: "$(yq eval '.epic.business_value' "$temp_file" 2>/dev/null || echo "")"
technical_approach: |
$(yq eval '.epic.technical_approach' "$temp_file" 2>/dev/null | sed 's/^/  /')

# Risks
risks:
$(yq eval '.epic.risks[]' "$temp_file" 2>/dev/null | sed 's/^/  - /')

# Features (generated below)
features: []

# Milestones
milestones:
$(yq eval '.milestones[]' "$temp_file" 2>/dev/null | while read -r milestone; do
    echo "  - name: \"$(echo "$milestone" | yq eval '.name' -)\""
    echo "    target_date: \"$(date -v+$(echo "$milestone" | yq eval '.week' -)w +%Y-%m-%d 2>/dev/null || date +%Y-%m-%d)\""
    echo "    criteria:"
    echo "$milestone" | yq eval '.deliverables[]' - | sed 's/^/      - /'
done)

# Success Metrics
metrics:
$(yq eval '.success_metrics[]' "$temp_file" 2>/dev/null | while read -r metric; do
    echo "  - name: \"$(echo "$metric" | yq eval '.metric' -)\""
    echo "    target: \"$(echo "$metric" | yq eval '.target' -)\""
    echo "    measurement: \"$(echo "$metric" | yq eval '.measurement' -)\""
done)

# Automation Configuration
automation:
  project_board: "local"
  branch_prefix: "$(echo "$epic_name" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | cut -c1-20)"
  ci_pipeline: "full"
  notifications:
    - channel: "development"
      events: ["milestone_reached", "blocker_detected"]
EOF

    # Update epic registry
    if [[ ! -f "$WORKFLOW_DIR/active_epics.json" ]]; then
        echo '{"epics": []}' > "$WORKFLOW_DIR/active_epics.json"
    fi

    jq --arg id "$epic_id" --arg name "$epic_name" --arg status "planning" --arg created "$(date +%Y-%m-%dT%H:%M:%S%z)" \
        '.epics += [{"id": $id, "name": $name, "status": $status, "created": $created}]' \
        "$WORKFLOW_DIR/active_epics.json" > "$WORKFLOW_DIR/active_epics.json.tmp" && \
        mv "$WORKFLOW_DIR/active_epics.json.tmp" "$WORKFLOW_DIR/active_epics.json"

    # Process features
    local feature_count=0
    yq eval '.features[]' "$temp_file" 2>/dev/null | while IFS= read -r feature_yaml; do
        ((feature_count++))
        process_feature "$epic_id" "$feature_yaml" "$feature_count"
    done

    # Clean up
    rm -f "$temp_file"

    log_success "Created epic: $epic_id with $(yq eval '.features | length' "$temp_file" 2>/dev/null || echo 0) features"
    echo "$epic_id"
}

# Process individual feature from AI response
process_feature() {
    local epic_id="$1"
    local feature_yaml="$2"
    local feature_num="$3"

    local feature_id="feat_${epic_id}_$(printf "%05d" $((RANDOM % 100000)))"
    local feature_name=$(echo "$feature_yaml" | yq eval '.name' -)
    local feature_description=$(echo "$feature_yaml" | yq eval '.description' -)
    local feature_effort=$(echo "$feature_yaml" | yq eval '.effort' -)
    local feature_priority=$(echo "$feature_yaml" | yq eval '.priority' -)
    local feature_category=$(echo "$feature_yaml" | yq eval '.category' -)

    log_info "Creating feature: $feature_name"

    # Create feature file
    cat > "$FEATURES_DIR/${feature_id}.yaml" << EOF
id: "$feature_id"
epic_id: "$epic_id"
name: "$feature_name"
description: "$feature_description"
effort: "$feature_effort"
priority: "$feature_priority"
status: "planning"
created: "$(date +%Y-%m-%dT%H:%M:%S%z)"
ai_generated: true

# Feature Analysis
category: "$feature_category"
estimated_hours: $(calculate_effort_hours "$feature_effort")
complexity_score: 5
risk_assessment: "medium"

# Dependencies
dependencies:
  internal:
$(echo "$feature_yaml" | yq eval '.dependencies[]' - 2>/dev/null | sed 's/^/    - /')
  external: []

# Acceptance Criteria
acceptance_criteria:
$(echo "$feature_yaml" | yq eval '.acceptance_criteria[]' - 2>/dev/null | sed 's/^/  - /')

# Tasks (AI Generated)
tasks:
$(echo "$feature_yaml" | yq eval '.tasks[]' - 2>/dev/null | while read -r task; do
    local task_name=$(echo "$task" | yq eval '.name' -)
    local task_hours=$(echo "$task" | yq eval '.effort_hours' -)
    local task_desc=$(echo "$task" | yq eval '.description' -)
    local task_notes=$(echo "$task" | yq eval '.technical_notes' -)
    echo "  - name: \"$task_name\""
    echo "    effort_hours: \"$task_hours\""
    echo "    description: \"$task_desc\""
    echo "    technical_notes: \"$task_notes\""
    echo "    status: \"pending\""
done)

# Implementation Plan
implementation_checklist:
$(echo "$feature_yaml" | yq eval '.tasks[].name' - 2>/dev/null | sed 's/^/  - /')

# Testing Strategy
testing:
  unit_tests:
    - "Test for core functionality"
  integration_tests:
    - "Test integration with existing system"
EOF

    # Update epic file to include feature reference
    local epic_file="$EPICS_DIR/${epic_id}.yaml"
    echo "  - id: \"$feature_id\"" >> "$epic_file"
    echo "    name: \"$feature_name\"" >> "$epic_file"
    echo "    effort: \"$feature_effort\"" >> "$epic_file"
    echo "    priority: \"$feature_priority\"" >> "$epic_file"

    # Update feature registry
    if [[ ! -f "$WORKFLOW_DIR/feature_registry.json" ]]; then
        echo '{"features": []}' > "$WORKFLOW_DIR/feature_registry.json"
    fi

    jq --arg id "$feature_id" --arg name "$feature_name" --arg epic "$epic_id" --arg status "planning" \
        '.features += [{"id": $id, "name": $name, "epic": $epic, "status": $status}]' \
        "$WORKFLOW_DIR/feature_registry.json" > "$WORKFLOW_DIR/feature_registry.json.tmp" && \
        mv "$WORKFLOW_DIR/feature_registry.json.tmp" "$WORKFLOW_DIR/feature_registry.json"
}

# Calculate effort hours from size
calculate_effort_hours() {
    case "$1" in
        small) echo "8" ;;
        medium) echo "24" ;;
        large) echo "40" ;;
        xl) echo "80" ;;
        *) echo "16" ;;
    esac
}

# Main AI planning function
ai_plan_epic() {
    local requirement="$1"
    local context="${2:-}"

    log_ai "Planning epic for: $requirement"

    # Check if OpenAI API key is available
    if [[ -z "${OPENAI_API_KEY:-}" ]]; then
        log_error "OPENAI_API_KEY not set. Please export OPENAI_API_KEY=your-key"
        return 1
    fi

    # Check for required tools
    if ! command -v yq >/dev/null 2>&1; then
        log_error "yq is required for YAML parsing. Install with: brew install yq"
        return 1
    fi

    # Initialize directories
    mkdir -p "$EPICS_DIR" "$FEATURES_DIR" "$WORKFLOW_DIR/tasks"

    # Get planning prompt
    local prompt=$(get_planning_prompt "$requirement" "$context")

    log_info "Consulting AI for epic breakdown..."

    # Call OpenAI API
    local response=$(curl -s https://api.openai.com/v1/chat/completions \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $OPENAI_API_KEY" \
        -d '{
            "model": "gpt-4",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert software architect who creates detailed, actionable project plans."
                },
                {
                    "role": "user",
                    "content": '"$(echo "$prompt" | jq -Rs .)"'
                }
            ],
            "temperature": 0.7,
            "max_tokens": 3000
        }' | jq -r '.choices[0].message.content')

    if [[ -z "$response" ]] || [[ "$response" == "null" ]]; then
        log_error "Failed to get response from OpenAI"
        return 1
    fi

    # Process the AI response
    local epic_id=$(process_ai_response "$response")

    if [[ -n "$epic_id" ]]; then
        log_success "AI planning complete! Epic created: $epic_id"
        echo
        echo "📋 View epic details:"
        echo "   cat $EPICS_DIR/${epic_id}.yaml"
        echo
        echo "📁 View features:"
        echo "   ls -la $FEATURES_DIR/feat_${epic_id}_*.yaml"
        echo
        echo "🚀 Start working:"
        echo "   ./scripts/workflow-automation.sh tasks list $epic_id"
    else
        log_error "Failed to create epic from AI response"
        return 1
    fi
}

# Show help
show_help() {
    cat << EOF
🤖 AI-Powered Epic Planning System

USAGE:
    $0 "requirement description" ["additional context"]

EXAMPLES:
    $0 "Build a user authentication system with OAuth2"

    $0 "Create a real-time chat application" "Must support 10k concurrent users"

    $0 "Implement payment processing with Stripe" "Need subscription management"

ENVIRONMENT:
    OPENAI_API_KEY    Your OpenAI API key (required)

FEATURES:
    - Breaks down requirements into epics, features, and tasks
    - Estimates effort and complexity
    - Creates dependencies and milestones
    - Generates acceptance criteria
    - Provides technical implementation notes
    - All output saved as YAML files in .workflows/

EOF
}

# Main execution
main() {
    if [[ $# -eq 0 ]] || [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
        show_help
        exit 0
    fi

    ai_plan_epic "$@"
}

main "$@"
