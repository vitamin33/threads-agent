#!/bin/bash

# scripts/workflow-automation.sh - Advanced workflow automation with intelligent lifecycle management
# Provides epic breakdown, feature orchestration, and smart development automation

set -euo pipefail

# Constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WORKFLOW_DIR="$PROJECT_ROOT/.workflows"
EPICS_DIR="$WORKFLOW_DIR/epics"
FEATURES_DIR="$WORKFLOW_DIR/features"
TEMPLATES_DIR="$WORKFLOW_DIR/templates"
ORCHESTRATION_DIR="$WORKFLOW_DIR/orchestration"
LIFECYCLE_DIR="$WORKFLOW_DIR/lifecycle"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SESSION_ID="${SESSION_ID:-$(date +%s)_$$}"

# Load learning system integration
LEARNING_SYSTEM="$SCRIPT_DIR/learning-system.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

# Logging
log_info() { echo -e "${BLUE}[WORKFLOW]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_epic() { echo -e "${PURPLE}[EPIC]${NC} $*"; }
log_feature() { echo -e "${CYAN}[FEATURE]${NC} $*"; }
log_orchestrate() { echo -e "${BOLD}[ORCHESTRATE]${NC} $*"; }

# Initialize workflow system
init_workflow_system() {
    mkdir -p "$EPICS_DIR" "$FEATURES_DIR" "$TEMPLATES_DIR" "$ORCHESTRATION_DIR" "$LIFECYCLE_DIR"
    
    # Initialize tracking files
    touch "$WORKFLOW_DIR/active_epics.json"
    touch "$WORKFLOW_DIR/feature_registry.json"
    touch "$WORKFLOW_DIR/orchestration_state.json"
    touch "$LIFECYCLE_DIR/lifecycle_events.log"
    
    # Create default templates if they don't exist
    create_default_templates
    
    log_info "Workflow automation system initialized"
}

# Create default workflow templates
create_default_templates() {
    # Feature template
    if [[ ! -f "$TEMPLATES_DIR/feature_template.yaml" ]]; then
        cat > "$TEMPLATES_DIR/feature_template.yaml" << 'EOF'
name: "{feature_name}"
epic: "{epic_id}"
type: "feature"
priority: "medium"
estimated_effort: "medium"
lifecycle_stage: "planning"

tasks:
  - name: "Design and planning"
    type: "planning"
    checklist:
      - "Define requirements and scope"
      - "Create technical design"
      - "Identify dependencies"
      - "Review with stakeholders"
    
  - name: "Implementation"
    type: "development"
    checklist:
      - "Set up development environment"
      - "Implement core functionality"
      - "Write unit tests"
      - "Handle edge cases"
    
  - name: "Testing and validation"
    type: "testing"
    checklist:
      - "Run unit tests"
      - "Integration testing"
      - "Performance validation"
      - "User acceptance testing"
    
  - name: "Documentation"
    type: "documentation"
    checklist:
      - "API documentation"
      - "User guide"
      - "Deployment notes"
      - "Changelog update"

automation:
  branch_naming: "feat/{epic_key}-{feature_key}"
  pr_template: "standard"
  quality_gates: ["lint", "test", "security"]
  deployment: "staging"
EOF
    fi
    
    # Epic template
    if [[ ! -f "$TEMPLATES_DIR/epic_template.yaml" ]]; then
        cat > "$TEMPLATES_DIR/epic_template.yaml" << 'EOF'
name: "{epic_name}"
description: "{epic_description}"
type: "epic"
priority: "high"
target_date: "{target_date}"
success_metrics:
  - metric: "completion_rate"
    target: "100%"
  - metric: "quality_score"
    target: "90%"

breakdown_strategy:
  max_feature_size: "large"
  parallel_features: 3
  dependency_management: "automatic"

features: []
milestones: []

automation:
  tracking: "linear"
  reporting: "weekly"
  notifications: ["slack", "email"]
EOF
    fi
}

# Epic breakdown with AI assistance
breakdown_epic() {
    local epic_name="$1"
    local epic_description="${2:-}"
    local complexity="${3:-medium}"
    
    log_epic "Breaking down epic: $epic_name"
    
    local epic_id="epic_$(date +%s)"
    local epic_file="$EPICS_DIR/${epic_id}.yaml"
    
    # Create epic structure
    cat > "$epic_file" << EOF
id: "$epic_id"
name: "$epic_name"
description: "$epic_description"
complexity: "$complexity"
created: "$(date -Iseconds)"
status: "planning"
lifecycle_stage: "inception"

# Epic Analysis
estimated_effort: $(estimate_effort "$complexity")
risk_level: $(assess_risk "$epic_description")
dependencies: []

# Feature Breakdown
features:
EOF
    
    # Use AI to suggest feature breakdown
    local breakdown_prompt="Break down this epic into implementable features:
Epic: $epic_name
Description: $epic_description
Complexity: $complexity

Provide 3-8 features with clear scope, ordered by dependency.
Consider: architecture, implementation, testing, deployment.
Format: feature_name|description|effort|priority"
    
    if command -v claude >/dev/null 2>&1 && [[ "${USE_CLAUDE_BREAKDOWN:-false}" == "true" ]]; then
        log_info "Using Claude for intelligent epic breakdown..."
        local features=$(echo "$breakdown_prompt" | timeout 10 claude 2>/dev/null | grep -E "^[^|]+\|[^|]+\|[^|]+\|[^|]+$" || echo "")
        
        if [[ -n "$features" ]]; then
            echo "$features" | while IFS='|' read -r fname fdesc feffort fpriority; do
                local feature_id=$(generate_feature "$epic_id" "$fname" "$fdesc" "$feffort" "$fpriority")
                echo "  - id: \"$feature_id\"" >> "$epic_file"
                echo "    name: \"$fname\"" >> "$epic_file"
                echo "    effort: \"$feffort\"" >> "$epic_file"
                echo "    priority: \"$fpriority\"" >> "$epic_file"
            done
        else
            log_info "Using template-based breakdown instead"
        fi
    fi
    
    if [[ ! -s "$epic_file" ]] || ! grep -q "^  - id:" "$epic_file"; then
        log_info "Using intelligent template-based breakdown"
        # Fallback to template-based breakdown
        case "$complexity" in
            "small")
                generate_feature "$epic_id" "Core Implementation" "Basic feature implementation" "small" "high" >> "$epic_file"
                generate_feature "$epic_id" "Testing & Validation" "Unit and integration tests" "small" "medium" >> "$epic_file"
                ;;
            "medium")
                local feat1=$(generate_feature "$epic_id" "Architecture Design" "Design system architecture" "medium" "high")
                local feat2=$(generate_feature "$epic_id" "Core Implementation" "Main feature development" "medium" "high")
                local feat3=$(generate_feature "$epic_id" "Testing Suite" "Comprehensive test coverage" "small" "medium")
                local feat4=$(generate_feature "$epic_id" "Documentation" "User and API documentation" "small" "low")
                echo "  - id: \"$feat1\"" >> "$epic_file"
                echo "    name: \"Architecture Design\"" >> "$epic_file"
                echo "    effort: \"medium\"" >> "$epic_file"
                echo "    priority: \"high\"" >> "$epic_file"
                echo "  - id: \"$feat2\"" >> "$epic_file"
                echo "    name: \"Core Implementation\"" >> "$epic_file"
                echo "    effort: \"medium\"" >> "$epic_file"
                echo "    priority: \"high\"" >> "$epic_file"
                echo "  - id: \"$feat3\"" >> "$epic_file"
                echo "    name: \"Testing Suite\"" >> "$epic_file"
                echo "    effort: \"small\"" >> "$epic_file"
                echo "    priority: \"medium\"" >> "$epic_file"
                echo "  - id: \"$feat4\"" >> "$epic_file"
                echo "    name: \"Documentation\"" >> "$epic_file"
                echo "    effort: \"small\"" >> "$epic_file"
                echo "    priority: \"low\"" >> "$epic_file"
                ;;
            "large")
                local feat1=$(generate_feature "$epic_id" "Research & Design" "Technical research and design" "large" "high")
                local feat2=$(generate_feature "$epic_id" "Infrastructure" "Setup required infrastructure" "medium" "high")
                local feat3=$(generate_feature "$epic_id" "Core Features" "Primary functionality implementation" "large" "high")
                local feat4=$(generate_feature "$epic_id" "Integration Layer" "System integration components" "medium" "medium")
                local feat5=$(generate_feature "$epic_id" "Testing & QA" "Full test suite and QA process" "medium" "medium")
                local feat6=$(generate_feature "$epic_id" "Documentation & Training" "Complete documentation" "small" "low")
                
                for i in 1 2 3 4 5 6; do
                    local fid_var="feat$i"
                    local fid="${!fid_var}"
                    case $i in
                        1) echo "  - id: \"$fid\""; echo "    name: \"Research & Design\""; echo "    effort: \"large\""; echo "    priority: \"high\"" ;;
                        2) echo "  - id: \"$fid\""; echo "    name: \"Infrastructure\""; echo "    effort: \"medium\""; echo "    priority: \"high\"" ;;
                        3) echo "  - id: \"$fid\""; echo "    name: \"Core Features\""; echo "    effort: \"large\""; echo "    priority: \"high\"" ;;
                        4) echo "  - id: \"$fid\""; echo "    name: \"Integration Layer\""; echo "    effort: \"medium\""; echo "    priority: \"medium\"" ;;
                        5) echo "  - id: \"$fid\""; echo "    name: \"Testing & QA\""; echo "    effort: \"medium\""; echo "    priority: \"medium\"" ;;
                        6) echo "  - id: \"$fid\""; echo "    name: \"Documentation & Training\""; echo "    effort: \"small\""; echo "    priority: \"low\"" ;;
                    esac
                done >> "$epic_file"
                ;;
        esac
    fi
    
    # Add milestones
    cat >> "$epic_file" << EOF

# Milestones
milestones:
  - name: "Planning Complete"
    target_date: "$(date -d '+1 week' +%Y-%m-%d 2>/dev/null || date +%Y-%m-%d)"
    criteria: ["Requirements finalized", "Architecture approved"]
    
  - name: "Core Development"
    target_date: "$(date -d '+3 weeks' +%Y-%m-%d 2>/dev/null || date +%Y-%m-%d)"
    criteria: ["Core features implemented", "Unit tests passing"]
    
  - name: "Integration Complete"
    target_date: "$(date -d '+5 weeks' +%Y-%m-%d 2>/dev/null || date +%Y-%m-%d)"
    criteria: ["All features integrated", "E2E tests passing"]
    
  - name: "Production Ready"
    target_date: "$(date -d '+6 weeks' +%Y-%m-%d 2>/dev/null || date +%Y-%m-%d)"
    criteria: ["Documentation complete", "Performance validated", "Security approved"]

# Automation Configuration
automation:
  project_board: "linear"
  branch_prefix: "$(echo "$epic_name" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | cut -c1-20)"
  ci_pipeline: "full"
  notifications:
    - channel: "development"
      events: ["milestone_reached", "blocker_detected"]
EOF
    
    # Update epic registry
    update_epic_registry "$epic_id" "$epic_name" "planning"
    
    log_success "Epic breakdown complete: $epic_file"
    log_info "Generated $(grep -c "^  - id:" "$epic_file") features"
    
    # Track in learning system
    [[ -f "$LEARNING_SYSTEM" ]] && "$LEARNING_SYSTEM" track "epic-breakdown" 0 1.0 "complexity:$complexity"
    
    echo "$epic_id"
}

# Generate a feature
generate_feature() {
    local epic_id="$1"
    local feature_name="$2"
    local description="${3:-}"
    local effort="${4:-medium}"
    local priority="${5:-medium}"
    
    local feature_id="feat_$(date +%s)_$$"
    local feature_file="$FEATURES_DIR/${feature_id}.yaml"
    
    log_feature "Generating feature: $feature_name"
    
    # Create feature from template
    cp "$TEMPLATES_DIR/feature_template.yaml" "$feature_file"
    
    # Customize feature
    sed -i '' "s/{feature_name}/$feature_name/g" "$feature_file"
    sed -i '' "s/{epic_id}/$epic_id/g" "$feature_file"
    sed -i '' "s/estimated_effort: \"medium\"/estimated_effort: \"$effort\"/g" "$feature_file"
    sed -i '' "s/priority: \"medium\"/priority: \"$priority\"/g" "$feature_file"
    
    # Add feature-specific metadata
    cat >> "$feature_file" << EOF

# Feature Metadata
id: "$feature_id"
description: "$description"
created: "$(date -Iseconds)"
assigned_to: "unassigned"
dependencies: []

# Lifecycle Events
lifecycle:
  created: "$(date -Iseconds)"
  events: []
EOF
    
    # Register feature
    register_feature "$feature_id" "$feature_name" "$epic_id"
    
    echo "$feature_id"
}

# Feature lifecycle management
manage_feature_lifecycle() {
    local action="$1"
    local feature_id="$2"
    local metadata="${3:-}"
    
    local feature_file="$FEATURES_DIR/${feature_id}.yaml"
    
    if [[ ! -f "$feature_file" ]]; then
        log_error "Feature not found: $feature_id (looking for $feature_file)"
        return 1
    fi
    
    log_info "Lifecycle action: $action for $feature_id"
    
    case "$action" in
        "start")
            update_feature_stage "$feature_id" "in_progress"
            create_feature_branch "$feature_id"
            setup_development_environment "$feature_id"
            log_success "Feature started: $feature_id"
            ;;
            
        "implement")
            update_feature_stage "$feature_id" "implementation"
            run_implementation_checks "$feature_id"
            track_implementation_progress "$feature_id"
            ;;
            
        "test")
            update_feature_stage "$feature_id" "testing"
            run_automated_tests "$feature_id"
            generate_test_report "$feature_id"
            ;;
            
        "review")
            update_feature_stage "$feature_id" "review"
            create_pull_request "$feature_id"
            run_quality_gates "$feature_id"
            ;;
            
        "complete")
            update_feature_stage "$feature_id" "completed"
            merge_feature_branch "$feature_id"
            update_documentation "$feature_id"
            cleanup_feature_resources "$feature_id"
            log_success "Feature completed: $feature_id"
            ;;
            
        "block")
            update_feature_stage "$feature_id" "blocked"
            record_blocker "$feature_id" "$metadata"
            notify_stakeholders "$feature_id" "blocked" "$metadata"
            ;;
            
        *)
            log_error "Unknown lifecycle action: $action"
            return 1
            ;;
    esac
    
    # Record lifecycle event
    echo "$(date -Iseconds)|$feature_id|$action|$metadata" >> "$LIFECYCLE_DIR/lifecycle_events.log"
    
    # Update feature file with event
    local temp_file=$(mktemp)
    awk -v action="$action" -v timestamp="$(date -Iseconds)" -v metadata="$metadata" '
    /^lifecycle:/ { in_lifecycle=1 }
    /^[^ ]/ && in_lifecycle && !/^lifecycle:/ && !/^  / { in_lifecycle=0 }
    { print }
    in_lifecycle && /^  events:/ {
        print "    - action: \"" action "\""
        print "      timestamp: \"" timestamp "\""
        if (metadata) print "      metadata: \"" metadata "\""
    }
    ' "$feature_file" > "$temp_file"
    mv "$temp_file" "$feature_file"
    
    # Track in learning system
    [[ -f "$LEARNING_SYSTEM" ]] && "$LEARNING_SYSTEM" track "feature-lifecycle" 0 1.0 "action:$action"
}

# Intelligent development orchestration
orchestrate_development() {
    local mode="${1:-auto}"
    
    log_orchestrate "Starting intelligent development orchestration (mode: $mode)"
    
    # Load current state
    local active_features=$(get_active_features)
    local blocked_features=$(get_blocked_features)
    local resource_capacity=$(get_resource_capacity)
    
    # Analyze development state
    local orchestration_plan="$ORCHESTRATION_DIR/plan_$TIMESTAMP.yaml"
    
    cat > "$orchestration_plan" << EOF
# Development Orchestration Plan
timestamp: "$(date -Iseconds)"
mode: "$mode"
session: "$SESSION_ID"

# Current State Analysis
state:
  active_features: $(echo "$active_features" | wc -l)
  blocked_features: $(echo "$blocked_features" | wc -l)
  resource_capacity: $resource_capacity
  
# Recommendations
recommendations:
EOF
    
    # Generate intelligent recommendations
    if [[ $(echo "$blocked_features" | wc -l) -gt 0 ]]; then
        echo "  - priority: \"unblock_features\"" >> "$orchestration_plan"
        echo "    action: \"Resolve blockers for stuck features\"" >> "$orchestration_plan"
        echo "    features:" >> "$orchestration_plan"
        echo "$blocked_features" | head -3 | while read feature; do
            echo "      - $feature" >> "$orchestration_plan"
        done
    fi
    
    if [[ $(echo "$active_features" | wc -l) -lt $resource_capacity ]]; then
        echo "  - priority: \"start_new_features\"" >> "$orchestration_plan"
        echo "    action: \"Start new high-priority features\"" >> "$orchestration_plan"
        echo "    capacity: $((resource_capacity - $(echo "$active_features" | wc -l)))" >> "$orchestration_plan"
    fi
    
    # Check for features ready for next stage
    local ready_features=$(check_features_ready_for_transition)
    if [[ -n "$ready_features" ]]; then
        echo "  - priority: \"advance_features\"" >> "$orchestration_plan"
        echo "    action: \"Move features to next lifecycle stage\"" >> "$orchestration_plan"
        echo "    features:" >> "$orchestration_plan"
        echo "$ready_features" | while read feature stage; do
            echo "      - feature: $feature" >> "$orchestration_plan"
            echo "        next_stage: $stage" >> "$orchestration_plan"
        done
    fi
    
    # Execute orchestration based on mode
    case "$mode" in
        "auto")
            log_info "Executing automatic orchestration..."
            execute_orchestration_plan "$orchestration_plan"
            ;;
        "suggest")
            log_info "Orchestration suggestions generated: $orchestration_plan"
            display_orchestration_suggestions "$orchestration_plan"
            ;;
        "interactive")
            display_orchestration_suggestions "$orchestration_plan"
            read -p "Execute orchestration plan? (y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                execute_orchestration_plan "$orchestration_plan"
            fi
            ;;
    esac
    
    log_success "Orchestration complete"
}

# Execute orchestration plan
execute_orchestration_plan() {
    local plan_file="$1"
    
    log_info "Executing orchestration plan..."
    
    # Parse and execute recommendations
    local in_recommendations=0
    local current_priority=""
    
    while IFS= read -r line; do
        if [[ "$line" =~ ^recommendations: ]]; then
            in_recommendations=1
        elif [[ $in_recommendations -eq 1 ]] && [[ "$line" =~ ^[[:space:]]*-[[:space:]]*priority:[[:space:]]*\"(.*)\" ]]; then
            current_priority="${BASH_REMATCH[1]}"
            
            case "$current_priority" in
                "unblock_features")
                    log_info "Addressing blocked features..."
                    # Automated unblocking logic here
                    ;;
                "start_new_features")
                    log_info "Starting new features..."
                    start_next_priority_features
                    ;;
                "advance_features")
                    log_info "Advancing feature lifecycle stages..."
                    # Automated stage advancement
                    ;;
            esac
        fi
    done < "$plan_file"
    
    # Update orchestration state
    update_orchestration_state "executed" "$plan_file"
}

# Start next priority features
start_next_priority_features() {
    local capacity=$(get_available_capacity)
    local started=0
    
    # Get unstarted features sorted by priority
    local features=$(get_unstarted_features_by_priority)
    
    echo "$features" | head -n "$capacity" | while read feature_id; do
        if [[ -n "$feature_id" ]]; then
            log_info "Auto-starting feature: $feature_id"
            manage_feature_lifecycle "$feature_id" "start"
            started=$((started + 1))
        fi
    done
    
    log_success "Started $started new features"
}

# Workflow templates management
create_workflow_template() {
    local template_name="$1"
    local template_type="${2:-custom}"
    
    local template_file="$TEMPLATES_DIR/${template_name}.yaml"
    
    log_info "Creating workflow template: $template_name"
    
    cat > "$template_file" << EOF
# Workflow Template: $template_name
name: "$template_name"
type: "$template_type"
version: "1.0.0"
created: "$(date -Iseconds)"

# Template Configuration
configuration:
  auto_assign: true
  quality_gates: ["lint", "test", "security"]
  notifications: ["slack"]
  
# Workflow Stages
stages:
  - name: "Initialization"
    automation:
      - action: "create_branch"
      - action: "setup_environment"
      - action: "notify_team"
    
  - name: "Development"
    automation:
      - action: "track_progress"
      - action: "run_tests"
      - action: "check_quality"
    
  - name: "Review"
    automation:
      - action: "create_pr"
      - action: "request_reviews"
      - action: "run_ci"
    
  - name: "Deployment"
    automation:
      - action: "merge_pr"
      - action: "deploy_staging"
      - action: "validate_deployment"

# Custom Actions
custom_actions:
  pre_start: []
  post_complete: []
  on_failure: ["notify_lead", "create_issue"]
EOF
    
    log_success "Template created: $template_file"
}

# Helper functions
estimate_effort() {
    local complexity="$1"
    case "$complexity" in
        "small") echo "1-2 weeks" ;;
        "medium") echo "2-4 weeks" ;;
        "large") echo "4-8 weeks" ;;
        *) echo "unknown" ;;
    esac
}

assess_risk() {
    local description="$1"
    # Simple risk assessment based on keywords
    if echo "$description" | grep -qiE "critical|security|performance|migration|breaking"; then
        echo "high"
    elif echo "$description" | grep -qiE "new feature|enhancement|improvement"; then
        echo "medium"
    else
        echo "low"
    fi
}

update_epic_registry() {
    local epic_id="$1"
    local epic_name="$2"
    local status="$3"
    
    local registry="$WORKFLOW_DIR/active_epics.json"
    
    # Create or update registry entry
    if [[ ! -s "$registry" ]] || ! jq -e . "$registry" >/dev/null 2>&1; then
        echo '{"epics":[]}' > "$registry"
    fi
    
    # Add epic to registry
    local temp_file=$(mktemp)
    jq --arg id "$epic_id" --arg name "$epic_name" --arg status "$status" --arg created "$(date -Iseconds)" \
        '.epics += [{"id": $id, "name": $name, "status": $status, "created": $created}]' \
        "$registry" > "$temp_file"
    mv "$temp_file" "$registry"
}

register_feature() {
    local feature_id="$1"
    local feature_name="$2"
    local epic_id="$3"
    
    local registry="$WORKFLOW_DIR/feature_registry.json"
    
    # Initialize registry if needed
    if [[ ! -s "$registry" ]] || ! jq -e . "$registry" >/dev/null 2>&1; then
        echo '{"features":[]}' > "$registry"
    fi
    
    # Add feature
    local temp_file=$(mktemp)
    jq --arg id "$feature_id" --arg name "$feature_name" --arg epic "$epic_id" --arg created "$(date -Iseconds)" \
        '.features += [{"id": $id, "name": $name, "epic": $epic, "status": "planned", "created": $created}]' \
        "$registry" > "$temp_file"
    mv "$temp_file" "$registry"
}

update_feature_stage() {
    local feature_id="$1"
    local stage="$2"
    
    local feature_file="$FEATURES_DIR/${feature_id}.yaml"
    
    # Update lifecycle stage in YAML
    sed -i '' "s/lifecycle_stage: \".*\"/lifecycle_stage: \"$stage\"/" "$feature_file"
    
    # Update registry
    local registry="$WORKFLOW_DIR/feature_registry.json"
    local temp_file=$(mktemp)
    jq --arg id "$feature_id" --arg stage "$stage" \
        '(.features[] | select(.id == $id) | .status) = $stage' \
        "$registry" > "$temp_file"
    mv "$temp_file" "$registry"
}

get_active_features() {
    local registry="$WORKFLOW_DIR/feature_registry.json"
    if [[ -f "$registry" ]]; then
        jq -r '.features[] | select(.status == "in_progress" or .status == "implementation" or .status == "testing") | .id' "$registry" 2>/dev/null || echo ""
    fi
}

get_blocked_features() {
    local registry="$WORKFLOW_DIR/feature_registry.json"
    if [[ -f "$registry" ]]; then
        jq -r '.features[] | select(.status == "blocked") | .id' "$registry" 2>/dev/null || echo ""
    fi
}

get_resource_capacity() {
    # Simplified capacity calculation
    # In real implementation, this would consider team size, current load, etc.
    echo "3"
}

get_available_capacity() {
    local total_capacity=$(get_resource_capacity)
    local active_count=$(get_active_features | wc -l)
    echo $((total_capacity - active_count))
}

get_unstarted_features_by_priority() {
    local registry="$WORKFLOW_DIR/feature_registry.json"
    if [[ -f "$registry" ]]; then
        # Get features sorted by priority (would need priority in registry)
        jq -r '.features[] | select(.status == "planned") | .id' "$registry" 2>/dev/null || echo ""
    fi
}

check_features_ready_for_transition() {
    # Simplified - in reality would check completion criteria
    local registry="$WORKFLOW_DIR/feature_registry.json"
    if [[ -f "$registry" ]]; then
        jq -r '.features[] | select(.status == "implementation") | .id + " testing"' "$registry" 2>/dev/null || echo ""
    fi
}

create_feature_branch() {
    local feature_id="$1"
    log_info "Creating feature branch for $feature_id"
    # In real implementation, would create git branch
}

setup_development_environment() {
    local feature_id="$1"
    log_info "Setting up development environment for $feature_id"
    # Would set up necessary dependencies, configs, etc.
}

run_implementation_checks() {
    local feature_id="$1"
    log_info "Running implementation checks for $feature_id"
    # Would run linting, type checking, etc.
}

track_implementation_progress() {
    local feature_id="$1"
    log_info "Tracking implementation progress for $feature_id"
    # Would update progress metrics
}

run_automated_tests() {
    local feature_id="$1"
    log_info "Running automated tests for $feature_id"
    # Would execute test suite
}

generate_test_report() {
    local feature_id="$1"
    log_info "Generating test report for $feature_id"
    # Would create test coverage and results report
}

create_pull_request() {
    local feature_id="$1"
    log_info "Creating pull request for $feature_id"
    # Would create PR with appropriate template
}

run_quality_gates() {
    local feature_id="$1"
    log_info "Running quality gates for $feature_id"
    # Would execute quality checks
}

merge_feature_branch() {
    local feature_id="$1"
    log_info "Merging feature branch for $feature_id"
    # Would merge PR after approvals
}

update_documentation() {
    local feature_id="$1"
    log_info "Updating documentation for $feature_id"
    # Would update relevant docs
}

cleanup_feature_resources() {
    local feature_id="$1"
    log_info "Cleaning up resources for $feature_id"
    # Would clean up temporary resources
}

record_blocker() {
    local feature_id="$1"
    local reason="$2"
    log_warn "Recording blocker for $feature_id: $reason"
    # Would record blocker details
}

notify_stakeholders() {
    local feature_id="$1"
    local event="$2"
    local details="$3"
    log_info "Notifying stakeholders about $event for $feature_id"
    # Would send notifications via configured channels
}

update_orchestration_state() {
    local status="$1"
    local plan_file="$2"
    
    local state_file="$ORCHESTRATION_DIR/orchestration_state.json"
    
    # Update state
    cat > "$state_file" << EOF
{
  "last_execution": "$(date -Iseconds)",
  "status": "$status",
  "plan": "$plan_file",
  "session": "$SESSION_ID"
}
EOF
}

display_orchestration_suggestions() {
    local plan_file="$1"
    
    echo
    echo "════════════════════════════════════════════════════════════════"
    echo "                    ORCHESTRATION SUGGESTIONS                    "
    echo "════════════════════════════════════════════════════════════════"
    
    # Parse and display recommendations
    awk '/^recommendations:/{p=1} p' "$plan_file" | tail -n +2 | while IFS= read -r line; do
        if [[ "$line" =~ priority:[[:space:]]*\"(.*)\" ]]; then
            echo
            echo "  🎯 $(echo "$line" | sed 's/.*priority: *"\([^"]*\)".*/\1/')"
        elif [[ "$line" =~ action:[[:space:]]*\"(.*)\" ]]; then
            echo "     → $(echo "$line" | sed 's/.*action: *"\([^"]*\)".*/\1/')"
        elif [[ "$line" =~ -[[:space:]]+(.*) ]] && [[ ! "$line" =~ priority: ]]; then
            echo "        • $(echo "$line" | sed 's/.*- *\(.*\)/\1/')"
        fi
    done
    
    echo
    echo "════════════════════════════════════════════════════════════════"
    echo
}

# Linear integration (if available)
sync_with_linear() {
    local action="${1:-sync}"
    
    if ! command -v linear >/dev/null 2>&1; then
        log_warn "Linear CLI not found - skipping project management sync"
        return 0
    fi
    
    log_info "Syncing with Linear project management..."
    
    case "$action" in
        "sync")
            # Sync epics and features with Linear
            sync_epics_to_linear
            sync_features_to_linear
            ;;
        "create")
            # Create Linear issues from features
            create_linear_issues
            ;;
        "update")
            # Update Linear issue status
            update_linear_status
            ;;
    esac
}

sync_epics_to_linear() {
    local registry="$WORKFLOW_DIR/active_epics.json"
    if [[ -f "$registry" ]]; then
        # Would sync each epic as a Linear project
        log_info "Syncing epics to Linear projects..."
    fi
}

sync_features_to_linear() {
    local registry="$WORKFLOW_DIR/feature_registry.json"
    if [[ -f "$registry" ]]; then
        # Would sync each feature as a Linear issue
        log_info "Syncing features to Linear issues..."
    fi
}

# Show workflow dashboard
show_dashboard() {
    clear
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║              WORKFLOW AUTOMATION DASHBOARD                    ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo
    
    # Epic summary
    local epic_count=0
    local epic_active=0
    if [[ -f "$WORKFLOW_DIR/active_epics.json" ]]; then
        epic_count=$(jq -r '.epics | length' "$WORKFLOW_DIR/active_epics.json" 2>/dev/null || echo 0)
        epic_active=$(jq -r '.epics[] | select(.status != "completed") | .id' "$WORKFLOW_DIR/active_epics.json" 2>/dev/null | wc -l || echo 0)
    fi
    
    # Feature summary
    local feature_count=0
    local feature_active=0
    local feature_blocked=0
    if [[ -f "$WORKFLOW_DIR/feature_registry.json" ]]; then
        feature_count=$(jq -r '.features | length' "$WORKFLOW_DIR/feature_registry.json" 2>/dev/null || echo 0)
        feature_active=$(get_active_features | wc -l)
        feature_blocked=$(get_blocked_features | wc -l)
    fi
    
    printf "📊 EPIC STATUS\n"
    printf "   Total Epics:     %d\n" "$epic_count"
    printf "   Active Epics:    %d\n" "$epic_active"
    echo
    
    printf "🚀 FEATURE STATUS\n"
    printf "   Total Features:  %d\n" "$feature_count"
    printf "   Active:          %d\n" "$feature_active"
    printf "   Blocked:         %d\n" "$feature_blocked"
    echo
    
    printf "⚡ QUICK ACTIONS\n"
    printf "   1. Break down new epic\n"
    printf "   2. Start feature development\n"
    printf "   3. Run orchestration\n"
    printf "   4. View lifecycle events\n"
    printf "   5. Generate reports\n"
    echo
    
    # Recent activity
    if [[ -f "$LIFECYCLE_DIR/lifecycle_events.log" ]]; then
        printf "📅 RECENT ACTIVITY\n"
        tail -5 "$LIFECYCLE_DIR/lifecycle_events.log" 2>/dev/null | while IFS='|' read -r timestamp fid action metadata; do
            printf "   %s: %s\n" "$(echo "$timestamp" | cut -d'T' -f2 | cut -d'+' -f1)" "$action on $fid"
        done
    fi
    echo
}

# Generate workflow report
generate_report() {
    local report_file="$WORKFLOW_DIR/workflow_report_$TIMESTAMP.html"
    
    log_info "Generating workflow automation report..."
    
    cat > "$report_file" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Workflow Automation Report</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }
        h2 { color: #555; margin-top: 30px; }
        .metric { display: inline-block; background: #f8f9fa; padding: 15px 25px; margin: 10px; border-radius: 8px; border-left: 4px solid #007bff; }
        .metric .value { font-size: 2em; font-weight: bold; color: #007bff; }
        .metric .label { color: #666; font-size: 0.9em; }
        .status { padding: 3px 8px; border-radius: 3px; font-size: 0.85em; }
        .status.active { background: #d4edda; color: #155724; }
        .status.blocked { background: #f8d7da; color: #721c24; }
        .status.completed { background: #cce5ff; color: #004085; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f8f9fa; font-weight: 600; }
        .chart { margin: 20px 0; height: 300px; background: #f8f9fa; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #999; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Workflow Automation Report</h1>
        <p><strong>Generated:</strong> $(date)</p>
        
        <h2>📊 Key Metrics</h2>
        <div class="metrics">
EOF
    
    # Add metrics
    local epic_count=$(jq -r '.epics | length' "$WORKFLOW_DIR/active_epics.json" 2>/dev/null || echo 0)
    local feature_count=$(jq -r '.features | length' "$WORKFLOW_DIR/feature_registry.json" 2>/dev/null || echo 0)
    local completion_rate=0
    
    if [[ $feature_count -gt 0 ]]; then
        local completed=$(jq -r '.features[] | select(.status == "completed") | .id' "$WORKFLOW_DIR/feature_registry.json" 2>/dev/null | wc -l || echo 0)
        completion_rate=$(echo "scale=1; $completed * 100 / $feature_count" | bc -l 2>/dev/null || echo 0)
    fi
    
    cat >> "$report_file" << EOF
            <div class="metric">
                <div class="value">$epic_count</div>
                <div class="label">Active Epics</div>
            </div>
            <div class="metric">
                <div class="value">$feature_count</div>
                <div class="label">Total Features</div>
            </div>
            <div class="metric">
                <div class="value">${completion_rate}%</div>
                <div class="label">Completion Rate</div>
            </div>
        </div>
        
        <h2>📋 Active Epics</h2>
        <table>
            <tr>
                <th>Epic Name</th>
                <th>Status</th>
                <th>Created</th>
                <th>Features</th>
            </tr>
EOF
    
    # Add epic details
    if [[ -f "$WORKFLOW_DIR/active_epics.json" ]]; then
        jq -r '.epics[] | [.name, .status, .created, .id] | @tsv' "$WORKFLOW_DIR/active_epics.json" 2>/dev/null | while IFS=$'\t' read -r name status created id; do
            local feature_count=$(jq -r --arg epic "$id" '.features[] | select(.epic == $epic) | .id' "$WORKFLOW_DIR/feature_registry.json" 2>/dev/null | wc -l || echo 0)
            echo "<tr><td>$name</td><td><span class=\"status $status\">$status</span></td><td>$(echo "$created" | cut -d'T' -f1)</td><td>$feature_count</td></tr>" >> "$report_file"
        done
    fi
    
    cat >> "$report_file" << EOF
        </table>
        
        <h2>🔄 Feature Lifecycle Distribution</h2>
        <div class="chart">Feature lifecycle visualization would go here</div>
        
        <h2>📈 Velocity Trends</h2>
        <div class="chart">Velocity chart would go here</div>
        
        <h2>🚧 Blocked Features</h2>
EOF
    
    # Add blocked features
    local blocked_count=$(get_blocked_features | wc -l)
    if [[ $blocked_count -gt 0 ]]; then
        echo "<table><tr><th>Feature</th><th>Epic</th><th>Blocked Since</th></tr>" >> "$report_file"
        get_blocked_features | while read fid; do
            local fname=$(jq -r --arg id "$fid" '.features[] | select(.id == $id) | .name' "$WORKFLOW_DIR/feature_registry.json" 2>/dev/null)
            local epic=$(jq -r --arg id "$fid" '.features[] | select(.id == $id) | .epic' "$WORKFLOW_DIR/feature_registry.json" 2>/dev/null)
            echo "<tr><td>$fname</td><td>$epic</td><td>N/A</td></tr>" >> "$report_file"
        done
        echo "</table>" >> "$report_file"
    else
        echo "<p>✅ No blocked features!</p>" >> "$report_file"
    fi
    
    cat >> "$report_file" << EOF
        
        <h2>🎯 Next Steps</h2>
        <ul>
            <li>Review blocked features and resolve dependencies</li>
            <li>Start high-priority features with available capacity</li>
            <li>Update epic milestones based on current progress</li>
            <li>Run orchestration to optimize resource allocation</li>
        </ul>
    </div>
</body>
</html>
EOF
    
    log_success "Report generated: $report_file"
    
    # Open report if possible
    if command -v open >/dev/null 2>&1; then
        open "$report_file"
    elif command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$report_file"
    fi
}

# Show help
show_help() {
    cat << EOF
🚀 Advanced Workflow Automation System

USAGE:
    $0 [COMMAND] [OPTIONS]

COMMANDS:
    init                        Initialize workflow system
    
    # Epic Management
    epic <name> [desc] [size]   Break down epic into features
    epics                       List all epics
    
    # Feature Lifecycle
    feature <action> <id>       Manage feature lifecycle
        Actions: start, implement, test, review, complete, block
    features                    List all features
    
    # Orchestration
    orchestrate [mode]          Run intelligent orchestration
        Modes: auto, suggest, interactive (default: suggest)
    
    # Templates
    template <name> [type]      Create workflow template
    templates                   List available templates
    
    # Reporting
    dashboard                   Show interactive dashboard
    report                      Generate HTML report
    
    # Integration
    sync [action]              Sync with Linear (if available)
        Actions: sync, create, update

EXAMPLES:
    # Break down a new epic
    $0 epic "User Authentication System" "Implement OAuth2 authentication" large
    
    # Start feature development
    $0 feature start feat_1234567890
    
    # Run orchestration suggestions
    $0 orchestrate suggest
    
    # Generate comprehensive report
    $0 report

LIFECYCLE STAGES:
    planning → in_progress → implementation → testing → review → completed
                                                            ↓
                                                         blocked

ENVIRONMENT VARIABLES:
    WORKFLOW_MODE=auto         Set default orchestration mode
    LINEAR_API_KEY=xxx         Enable Linear integration
    SLACK_WEBHOOK=xxx          Enable Slack notifications

EOF
}

# Main execution
main() {
    cd "$PROJECT_ROOT"
    
    case "${1:-help}" in
        init)
            init_workflow_system
            ;;
        epic)
            shift
            breakdown_epic "$@"
            ;;
        epics)
            if [[ -f "$WORKFLOW_DIR/active_epics.json" ]]; then
                jq -r '.epics[] | "\(.id)\t\(.name)\t\(.status)"' "$WORKFLOW_DIR/active_epics.json"
            else
                log_warn "No epics found"
            fi
            ;;
        feature)
            if [[ $# -lt 3 ]]; then
                log_error "Usage: feature <action> <feature_id>"
                exit 1
            fi
            manage_feature_lifecycle "$2" "$3" "${4:-}"
            ;;
        features)
            if [[ -f "$WORKFLOW_DIR/feature_registry.json" ]]; then
                jq -r '.features[] | "\(.id)\t\(.name)\t\(.status)"' "$WORKFLOW_DIR/feature_registry.json"
            else
                log_warn "No features found"
            fi
            ;;
        orchestrate)
            init_workflow_system
            orchestrate_development "${2:-suggest}"
            ;;
        template)
            shift
            create_workflow_template "$@"
            ;;
        templates)
            ls -la "$TEMPLATES_DIR"/*.yaml 2>/dev/null || log_warn "No templates found"
            ;;
        dashboard)
            init_workflow_system
            show_dashboard
            ;;
        report)
            init_workflow_system
            generate_report
            ;;
        sync)
            sync_with_linear "${2:-sync}"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Cleanup handler
cleanup() {
    log_info "Workflow automation session completed"
}

trap cleanup EXIT

main "$@"