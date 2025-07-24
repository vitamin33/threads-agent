#!/bin/bash

# scripts/plan-memory.sh - Universal development plan memory system
# Deep code-context awareness for intelligent, pattern-aware epic and task generation

set -euo pipefail

# Constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MEMORY_DIR="$PROJECT_ROOT/.plan-memory"
CODEBASE_DIR="$MEMORY_DIR/codebase"
PATTERNS_DIR="$MEMORY_DIR/patterns"
CONTEXT_DIR="$MEMORY_DIR/context"
PLANS_DIR="$MEMORY_DIR/plans"
KNOWLEDGE_DIR="$MEMORY_DIR/knowledge"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SESSION_ID="${SESSION_ID:-$(date +%s)_$$}"

# Integration with existing systems
LEARNING_SYSTEM="$SCRIPT_DIR/learning-system.sh"
WORKFLOW_SYSTEM="$SCRIPT_DIR/workflow-automation.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
MAGENTA='\033[0;95m'
BOLD='\033[1m'
NC='\033[0m'

# Logging
log_info() { echo -e "${BLUE}[MEMORY]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_analyze() { echo -e "${PURPLE}[ANALYZE]${NC} $*"; }
log_context() { echo -e "${CYAN}[CONTEXT]${NC} $*"; }
log_plan() { echo -e "${MAGENTA}[PLAN]${NC} $*"; }

# Initialize memory system
init_memory_system() {
    mkdir -p "$CODEBASE_DIR" "$PATTERNS_DIR" "$CONTEXT_DIR" "$PLANS_DIR" "$KNOWLEDGE_DIR"

    # Initialize memory databases
    touch "$MEMORY_DIR/codebase_map.json"
    touch "$MEMORY_DIR/pattern_registry.json"
    touch "$MEMORY_DIR/context_index.json"
    touch "$MEMORY_DIR/plan_history.json"
    touch "$MEMORY_DIR/knowledge_graph.json"

    # Create initial empty structures
    if [[ ! -s "$MEMORY_DIR/codebase_map.json" ]]; then
        echo '{"last_scan": "", "structure": {}, "dependencies": {}, "patterns": {}}' > "$MEMORY_DIR/codebase_map.json"
    fi

    if [[ ! -s "$MEMORY_DIR/pattern_registry.json" ]]; then
        echo '{"patterns": [], "templates": {}, "insights": []}' > "$MEMORY_DIR/pattern_registry.json"
    fi

    if [[ ! -s "$MEMORY_DIR/context_index.json" ]]; then
        echo '{"contexts": [], "relationships": {}, "semantic_map": {}}' > "$MEMORY_DIR/context_index.json"
    fi

    log_info "Universal memory system initialized"
}

# Deep codebase analysis and indexing
analyze_codebase() {
    local force_rescan="${1:-false}"

    log_analyze "Starting deep codebase analysis..."

    local last_scan=$(jq -r '.last_scan' "$MEMORY_DIR/codebase_map.json" 2>/dev/null || echo "")
    local current_time=$(date -Iseconds)

    # Check if we need to rescan
    if [[ "$force_rescan" != "true" ]] && [[ -n "$last_scan" ]]; then
        local scan_age=$(( $(date +%s) - $(date -d "$last_scan" +%s 2>/dev/null || echo 0) ))
        if [[ $scan_age -lt 3600 ]]; then # Less than 1 hour old
            log_info "Using cached codebase analysis ($(($scan_age / 60)) minutes old)"
            return 0
        fi
    fi

    log_analyze "Performing comprehensive codebase scan..."

    # 1. Architecture Analysis
    analyze_architecture

    # 2. Dependency Mapping
    analyze_dependencies

    # 3. Pattern Recognition
    analyze_code_patterns

    # 4. API and Interface Analysis
    analyze_apis_interfaces

    # 5. Test Coverage Analysis
    analyze_test_patterns

    # 6. Documentation Analysis
    analyze_documentation

    # 7. Git History Analysis
    analyze_git_history

    # Update scan timestamp
    local temp_file=$(mktemp)
    jq --arg timestamp "$current_time" '.last_scan = $timestamp' "$MEMORY_DIR/codebase_map.json" > "$temp_file"
    mv "$temp_file" "$MEMORY_DIR/codebase_map.json"

    log_success "Codebase analysis complete"
}

# Architecture Analysis
analyze_architecture() {
    log_analyze "Analyzing project architecture..."

    local arch_file="$CODEBASE_DIR/architecture_$TIMESTAMP.json"

    # Detect project structure and patterns
    cat > "$arch_file" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "project_type": "$(detect_project_type)",
  "architecture_style": "$(detect_architecture_style)",
  "services": $(analyze_services),
  "layers": $(analyze_layers),
  "modules": $(analyze_modules),
  "entry_points": $(find_entry_points),
  "configuration": $(analyze_configuration),
  "infrastructure": $(analyze_infrastructure)
}
EOF

    # Update main codebase map
    local temp_file=$(mktemp)
    jq --slurpfile arch <(cat "$arch_file") '.structure.architecture = $arch[0]' "$MEMORY_DIR/codebase_map.json" > "$temp_file"
    mv "$temp_file" "$MEMORY_DIR/codebase_map.json"

    log_success "Architecture analysis saved to $arch_file"
}

# Detect project type based on structure and files
detect_project_type() {
    if [[ -f "services/orchestrator/main.py" ]] && [[ -f "chart/Chart.yaml" ]]; then
        echo "microservices_k8s"
    elif [[ -f "package.json" ]] && [[ -d "src" ]]; then
        echo "javascript_app"
    elif [[ -f "requirements.txt" ]] || [[ -f "pyproject.toml" ]]; then
        echo "python_application"
    elif [[ -f "Cargo.toml" ]]; then
        echo "rust_application"
    elif [[ -f "go.mod" ]]; then
        echo "go_application"
    else
        echo "unknown"
    fi
}

# Detect architecture style
detect_architecture_style() {
    if [[ -d "services" ]] && [[ $(find services -maxdepth 1 -type d | wc -l) -gt 3 ]]; then
        echo "microservices"
    elif [[ -f "docker-compose.yml" ]] || [[ -f "chart/Chart.yaml" ]]; then
        echo "containerized"
    elif [[ -d "src" ]] && [[ -d "tests" ]] && [[ -d "docs" ]]; then
        echo "modular_monolith"
    else
        echo "standard"
    fi
}

# Analyze services
analyze_services() {
    if [[ -d "services" ]]; then
        local services_json="["
        local first=true

        for service_dir in services/*/; do
            if [[ -d "$service_dir" ]]; then
                local service_name=$(basename "$service_dir")

                if [[ "$first" == "true" ]]; then
                    first=false
                else
                    services_json+=","
                fi

                services_json+="{\"name\":\"$service_name\",\"type\":\"$(detect_service_type "$service_dir")\",\"endpoints\":$(find_service_endpoints "$service_dir"),\"dependencies\":$(find_service_dependencies "$service_dir")}"
            fi
        done

        services_json+="]"
        echo "$services_json"
    else
        echo "[]"
    fi
}

# Detect service type
detect_service_type() {
    local service_dir="$1"

    if [[ -f "$service_dir/main.py" ]] && grep -q "FastAPI\|app = " "$service_dir"/*.py 2>/dev/null; then
        echo "fastapi_service"
    elif [[ -f "$service_dir/tasks.py" ]] && grep -q "celery\|@task" "$service_dir"/*.py 2>/dev/null; then
        echo "celery_worker"
    elif [[ -f "$service_dir/app.py" ]] && grep -q "Flask" "$service_dir"/*.py 2>/dev/null; then
        echo "flask_service"
    elif find "$service_dir" -name "*.py" -exec grep -l "def.*handler\|lambda_handler" {} \; 2>/dev/null | head -1; then
        echo "lambda_function"
    else
        echo "generic_service"
    fi
}

# Find service endpoints
find_service_endpoints() {
    local service_dir="$1"

    # Simplified endpoint detection to avoid JSON syntax issues
    if find "$service_dir" -name "*.py" -exec grep -l "FastAPI\|@app\.\|@router\." {} \; 2>/dev/null | head -1 >/dev/null; then
        echo '["API"]'
    else
        echo '[]'
    fi
}

# Find service dependencies
find_service_dependencies() {
    local service_dir="$1"

    # Simplified dependency detection to avoid JSON issues
    if [[ -f "$service_dir/requirements.txt" ]]; then
        echo '["requirements"]'
    else
        echo '[]'
    fi
}

# Analyze layers
analyze_layers() {
    local layers="{"

    # Common layer patterns
    if [[ -d "services" ]]; then
        layers+="\"services\": $(find services -name "*.py" | wc -l),"
    fi

    if [[ -d "tests" ]]; then
        layers+="\"tests\": $(find tests -name "*.py" | wc -l),"
    fi

    if [[ -d "scripts" ]]; then
        layers+="\"scripts\": $(find scripts -name "*.sh" -o -name "*.py" | wc -l),"
    fi

    if [[ -d "docs" ]]; then
        layers+="\"documentation\": $(find docs -name "*.md" -o -name "*.rst" | wc -l),"
    fi

    if [[ -d "chart" ]] || [[ -d "k8s" ]] || [[ -d "helm" ]]; then
        layers+="\"infrastructure\": $(find chart k8s helm -name "*.yaml" -o -name "*.yml" 2>/dev/null | wc -l),"
    fi

    # Remove trailing comma and close
    layers=$(echo "$layers" | sed 's/,$//')
    layers+="}"

    echo "$layers"
}

# Analyze modules and components
analyze_modules() {
    local modules="["
    local first=true

    # Find Python modules
    find . -name "*.py" -path "*/services/*" -exec dirname {} \; | sort -u | while read module_dir; do
        if [[ "$module_dir" != "." ]]; then
            local module_name=$(basename "$module_dir")
            local file_count=$(find "$module_dir" -maxdepth 1 -name "*.py" | wc -l)

            if [[ "$first" == "true" ]]; then
                first=false
            else
                modules+=","
            fi

            modules+="{\"name\":\"$module_name\",\"path\":\"$module_dir\",\"files\":$file_count,\"type\":\"python_module\"}"
        fi
    done

    modules+="]"
    echo "$modules"
}

# Find entry points
find_entry_points() {
    local entry_points="["
    local first=true

    # Find main entry points
    find . -name "main.py" -o -name "app.py" -o -name "__main__.py" -o -name "run.py" | while read entry; do
        if [[ "$first" == "true" ]]; then
            first=false
        else
            entry_points+=","
        fi

        entry_points+="{\"file\":\"$entry\",\"type\":\"python_entry\"}"
    done

    # Find Dockerfiles
    find . -name "Dockerfile*" | while read dockerfile; do
        if [[ "$first" == "true" ]]; then
            first=false
        else
            entry_points+=","
        fi

        entry_points+="{\"file\":\"$dockerfile\",\"type\":\"container_entry\"}"
    done

    entry_points+="]"
    echo "$entry_points"
}

# Analyze configuration
analyze_configuration() {
    local config="{"

    # Environment files
    local env_count=$(find . -name ".env*" -o -name "*.env" | wc -l)
    config+="\"env_files\": $env_count,"

    # Config files
    local yaml_count=$(find . -name "*.yaml" -o -name "*.yml" | wc -l)
    config+="\"yaml_configs\": $yaml_count,"

    local json_count=$(find . -name "*.json" -path "*/config/*" -o -name "config.json" | wc -l)
    config+="\"json_configs\": $json_count,"

    # Python config
    local ini_count=$(find . -name "*.ini" -o -name "*.cfg" | wc -l)
    config+="\"ini_configs\": $ini_count"

    config+="}"
    echo "$config"
}

# Analyze infrastructure
analyze_infrastructure() {
    local infra="{"

    # Docker
    if [[ -f "docker-compose.yml" ]] || [[ -f "docker-compose.yaml" ]]; then
        infra+="\"docker_compose\": true,"
    else
        infra+="\"docker_compose\": false,"
    fi

    # Kubernetes
    if [[ -d "chart" ]] || [[ -d "k8s" ]]; then
        infra+="\"kubernetes\": true,"
    else
        infra+="\"kubernetes\": false,"
    fi

    # CI/CD
    if [[ -d ".github/workflows" ]]; then
        infra+="\"github_actions\": true,"
    else
        infra+="\"github_actions\": false,"
    fi

    # Remove trailing comma
    infra=$(echo "$infra" | sed 's/,$//')
    infra+="}"

    echo "$infra"
}

# Dependency analysis
analyze_dependencies() {
    log_analyze "Mapping dependencies..."

    local deps_file="$CODEBASE_DIR/dependencies_$TIMESTAMP.json"

    cat > "$deps_file" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "internal_deps": $(analyze_internal_dependencies),
  "external_deps": $(analyze_external_dependencies),
  "dependency_graph": $(build_dependency_graph),
  "circular_deps": $(detect_circular_dependencies)
}
EOF

    # Update main map
    local temp_file=$(mktemp)
    jq --slurpfile deps <(cat "$deps_file") '.dependencies = $deps[0]' "$MEMORY_DIR/codebase_map.json" > "$temp_file"
    mv "$temp_file" "$MEMORY_DIR/codebase_map.json"
}

# Analyze internal dependencies
analyze_internal_dependencies() {
    local internal_deps="{"

    # Find internal imports
    find services -name "*.py" 2>/dev/null | while read pyfile; do
        local service=$(echo "$pyfile" | cut -d'/' -f2)
        local imports=$(grep -E "^from services\.|^import services\." "$pyfile" 2>/dev/null | wc -l)

        if [[ $imports -gt 0 ]]; then
            internal_deps+="\"$service\": $imports,"
        fi
    done

    # Remove trailing comma
    internal_deps=$(echo "$internal_deps" | sed 's/,$//')
    internal_deps+="}"

    echo "$internal_deps"
}

# Analyze external dependencies
analyze_external_dependencies() {
    local external_deps="["
    local first=true

    # Collect all requirements
    find . -name "requirements*.txt" -o -name "pyproject.toml" | while read req_file; do
        if [[ "$req_file" == *"requirements"* ]]; then
            while IFS= read -r dep; do
                if [[ -n "$dep" ]] && [[ "$dep" != \#* ]]; then
                    local pkg_name=$(echo "$dep" | cut -d'=' -f1 | cut -d'>' -f1 | cut -d'<' -f1 | cut -d'[' -f1)

                    if [[ "$first" == "true" ]]; then
                        first=false
                    else
                        external_deps+=","
                    fi

                    external_deps+="{\"name\":\"$pkg_name\",\"version\":\"$(echo "$dep" | grep -o '[=><][^,]*' | head -1 || echo 'any')\",\"file\":\"$req_file\"}"
                fi
            done < "$req_file"
        fi
    done

    external_deps+="]"
    echo "$external_deps"
}

# Build dependency graph
build_dependency_graph() {
    echo '{"nodes": [], "edges": []}'  # Simplified for now
}

# Detect circular dependencies
detect_circular_dependencies() {
    echo '[]'  # Simplified for now
}

# Code pattern analysis
analyze_code_patterns() {
    log_analyze "Analyzing code patterns..."

    local patterns_file="$PATTERNS_DIR/code_patterns_$TIMESTAMP.json"

    cat > "$patterns_file" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "design_patterns": $(detect_design_patterns),
  "architectural_patterns": $(detect_architectural_patterns),
  "coding_patterns": $(detect_coding_patterns),
  "anti_patterns": $(detect_anti_patterns),
  "best_practices": $(assess_best_practices)
}
EOF

    # Update pattern registry
    local temp_file=$(mktemp)
    jq --slurpfile patterns <(cat "$patterns_file") '.patterns += [$patterns[0]]' "$MEMORY_DIR/pattern_registry.json" > "$temp_file"
    mv "$temp_file" "$MEMORY_DIR/pattern_registry.json"
}

# Detect design patterns
detect_design_patterns() {
    local patterns="["
    local first=true

    # Factory pattern
    if grep -r "class.*Factory\|def create_" services/ 2>/dev/null | head -1 >/dev/null; then
        patterns+='"factory"'
        first=false
    fi

    # Singleton pattern
    if grep -r "__new__\|_instance.*None" services/ 2>/dev/null | head -1 >/dev/null; then
        if [[ "$first" == "false" ]]; then patterns+=","; fi
        patterns+='"singleton"'
        first=false
    fi

    # Observer pattern
    if grep -r "subscribe\|notify\|observer" services/ 2>/dev/null | head -1 >/dev/null; then
        if [[ "$first" == "false" ]]; then patterns+=","; fi
        patterns+='"observer"'
        first=false
    fi

    # Strategy pattern
    if grep -r "strategy\|algorithm" services/ 2>/dev/null | head -1 >/dev/null; then
        if [[ "$first" == "false" ]]; then patterns+=","; fi
        patterns+='"strategy"'
        first=false
    fi

    patterns+="]"
    echo "$patterns"
}

# Detect architectural patterns
detect_architectural_patterns() {
    local patterns="["
    local first=true

    # Microservices
    if [[ -d "services" ]] && [[ $(find services -maxdepth 1 -type d | wc -l) -gt 3 ]]; then
        patterns+='"microservices"'
        first=false
    fi

    # API Gateway
    if grep -r "gateway\|proxy" services/ 2>/dev/null | head -1 >/dev/null; then
        if [[ "$first" == "false" ]]; then patterns+=","; fi
        patterns+='"api_gateway"'
        first=false
    fi

    # Event Driven
    if grep -r "event\|message\|queue" services/ 2>/dev/null | head -1 >/dev/null; then
        if [[ "$first" == "false" ]]; then patterns+=","; fi
        patterns+='"event_driven"'
        first=false
    fi

    # CQRS
    if grep -r "command\|query.*handler" services/ 2>/dev/null | head -1 >/dev/null; then
        if [[ "$first" == "false" ]]; then patterns+=","; fi
        patterns+='"cqrs"'
        first=false
    fi

    patterns+="]"
    echo "$patterns"
}

# Detect coding patterns
detect_coding_patterns() {
    local patterns="["
    local first=true

    # Dependency Injection
    if grep -r "inject\|dependency" services/ 2>/dev/null | head -1 >/dev/null; then
        patterns+='"dependency_injection"'
        first=false
    fi

    # Repository Pattern
    if grep -r "repository\|repo" services/ 2>/dev/null | head -1 >/dev/null; then
        if [[ "$first" == "false" ]]; then patterns+=","; fi
        patterns+='"repository"'
        first=false
    fi

    # MVC/MVP
    if find services -name "*controller*" -o -name "*view*" -o -name "*model*" | head -1 >/dev/null; then
        if [[ "$first" == "false" ]]; then patterns+=","; fi
        patterns+='"mvc"'
        first=false
    fi

    patterns+="]"
    echo "$patterns"
}

# Detect anti-patterns
detect_anti_patterns() {
    local anti_patterns="["
    local first=true

    # God object (large files)
    local large_files=$(find services -name "*.py" -exec wc -l {} + 2>/dev/null | awk '$1 > 500 {print $2}' | wc -l)
    if [[ $large_files -gt 0 ]]; then
        anti_patterns+='"god_object"'
        first=false
    fi

    # Long parameter lists
    if grep -r "def.*(" services/ 2>/dev/null | grep -E "\([^)]*,[^)]*,[^)]*,[^)]*,[^)]*," | head -1 >/dev/null; then
        if [[ "$first" == "false" ]]; then anti_patterns+=","; fi
        anti_patterns+='"long_parameter_list"'
        first=false
    fi

    # Hardcoded values
    if grep -r "localhost\|127\.0\.0\.1\|3306\|5432" services/ 2>/dev/null | grep -v "test\|example" | head -1 >/dev/null; then
        if [[ "$first" == "false" ]]; then anti_patterns+=","; fi
        anti_patterns+='"hardcoded_values"'
        first=false
    fi

    anti_patterns+="]"
    echo "$anti_patterns"
}

# Assess best practices
assess_best_practices() {
    local practices="{"
    local score=0
    local total=0

    # Type hints
    local type_hint_files=$(find services -name "*.py" -exec grep -l ":" {} + 2>/dev/null | wc -l)
    local total_py_files=$(find services -name "*.py" 2>/dev/null | wc -l)
    if [[ $total_py_files -gt 0 ]]; then
        local type_hint_ratio=$(echo "scale=2; $type_hint_files * 100 / $total_py_files" | bc -l 2>/dev/null || echo 0)
        practices+="\"type_hints_percentage\": $type_hint_ratio,"
        if (( $(echo "$type_hint_ratio > 50" | bc -l 2>/dev/null || echo 0) )); then
            score=$((score + 1))
        fi
        total=$((total + 1))
    fi

    # Documentation
    local doc_files=$(find . -name "*.md" -o -name "*.rst" | wc -l)
    practices+="\"documentation_files\": $doc_files,"
    if [[ $doc_files -gt 3 ]]; then
        score=$((score + 1))
    fi
    total=$((total + 1))

    # Tests
    local test_files=$(find tests -name "*.py" 2>/dev/null | wc -l)
    practices+="\"test_files\": $test_files,"
    if [[ $test_files -gt 5 ]]; then
        score=$((score + 1))
    fi
    total=$((total + 1))

    # Configuration management
    if [[ -f ".env.example" ]] || [[ -f "config.yaml" ]]; then
        practices+="\"config_management\": true,"
        score=$((score + 1))
    else
        practices+="\"config_management\": false,"
    fi
    total=$((total + 1))

    # Calculate overall score
    local overall_score=0
    if [[ $total -gt 0 ]]; then
        overall_score=$(echo "scale=2; $score * 100 / $total" | bc -l 2>/dev/null || echo 0)
    fi
    practices+="\"overall_score\": $overall_score"

    practices+="}"
    echo "$practices"
}

# API and interface analysis
analyze_apis_interfaces() {
    log_analyze "Analyzing APIs and interfaces..."

    local apis_file="$CODEBASE_DIR/apis_$TIMESTAMP.json"

    cat > "$apis_file" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "rest_apis": $(find_rest_apis),
  "graphql_apis": $(find_graphql_apis),
  "internal_apis": $(find_internal_apis),
  "external_apis": $(find_external_apis),
  "interfaces": $(find_interfaces)
}
EOF
}

# Find REST APIs
find_rest_apis() {
    local apis="["
    local first=true

    # Find FastAPI/Flask routes
    find services -name "*.py" -exec grep -l "@app\.\|@router\." {} + 2>/dev/null | while read api_file; do
        local service=$(echo "$api_file" | cut -d'/' -f2)

        if [[ "$first" == "true" ]]; then
            first=false
        else
            apis+=","
        fi

        apis+="{\"service\":\"$service\",\"file\":\"$api_file\",\"type\":\"fastapi\"}"
    done

    apis+="]"
    echo "$apis"
}

# Find GraphQL APIs
find_graphql_apis() {
    local apis="["

    # Look for GraphQL patterns
    if find services -name "*.py" -exec grep -l "graphql\|GraphQL\|schema" {} + 2>/dev/null | head -1 >/dev/null; then
        apis+="{\"type\":\"graphql\",\"found\":true}"
    fi

    apis+="]"
    echo "$apis"
}

# Find internal APIs
find_internal_apis() {
    echo '[]'  # Simplified for now
}

# Find external APIs
find_external_apis() {
    local apis="["
    local first=true

    # Look for HTTP clients and API calls
    find services -name "*.py" -exec grep -l "requests\.\|httpx\.\|aiohttp" {} + 2>/dev/null | while read client_file; do
        if [[ "$first" == "true" ]]; then
            first=false
        else
            apis+=","
        fi

        apis+="{\"file\":\"$client_file\",\"type\":\"http_client\"}"
    done

    apis+="]"
    echo "$apis"
}

# Find interfaces
find_interfaces() {
    local interfaces="["
    local first=true

    # Find abstract base classes and protocols
    find services -name "*.py" -exec grep -l "ABC\|Protocol\|abstract" {} + 2>/dev/null | while read interface_file; do
        if [[ "$first" == "true" ]]; then
            first=false
        else
            interfaces+=","
        fi

        interfaces+="{\"file\":\"$interface_file\",\"type\":\"abc_protocol\"}"
    done

    interfaces+="]"
    echo "$interfaces"
}

# Test pattern analysis
analyze_test_patterns() {
    log_analyze "Analyzing test patterns..."

    local tests_file="$CODEBASE_DIR/tests_$TIMESTAMP.json"

    cat > "$tests_file" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "test_structure": $(analyze_test_structure),
  "test_types": $(analyze_test_types),
  "coverage_estimation": $(estimate_test_coverage),
  "test_patterns": $(detect_test_patterns)
}
EOF
}

# Analyze test structure
analyze_test_structure() {
    local structure="{"

    # Count different test types
    local unit_tests=$(find tests -path "*/unit/*" -name "*.py" 2>/dev/null | wc -l)
    local integration_tests=$(find tests -path "*/integration/*" -name "*.py" 2>/dev/null | wc -l)
    local e2e_tests=$(find tests -path "*/e2e/*" -name "*.py" 2>/dev/null | wc -l)
    local service_tests=$(find services -path "*/tests/*" -name "*.py" 2>/dev/null | wc -l)

    structure+="\"unit_tests\": $unit_tests,"
    structure+="\"integration_tests\": $integration_tests,"
    structure+="\"e2e_tests\": $e2e_tests,"
    structure+="\"service_tests\": $service_tests"

    structure+="}"
    echo "$structure"
}

# Analyze test types
analyze_test_types() {
    local types="["
    local first=true

    # Check for different testing frameworks and patterns
    if find tests services -name "*.py" -exec grep -l "pytest" {} + 2>/dev/null | head -1 >/dev/null; then
        types+='"pytest"'
        first=false
    fi

    if find tests services -name "*.py" -exec grep -l "unittest" {} + 2>/dev/null | head -1 >/dev/null; then
        if [[ "$first" == "false" ]]; then types+=","; fi
        types+='"unittest"'
        first=false
    fi

    if find tests services -name "*.py" -exec grep -l "@mock\|Mock" {} + 2>/dev/null | head -1 >/dev/null; then
        if [[ "$first" == "false" ]]; then types+=","; fi
        types+='"mocking"'
        first=false
    fi

    if find tests services -name "*.py" -exec grep -l "fixture" {} + 2>/dev/null | head -1 >/dev/null; then
        if [[ "$first" == "false" ]]; then types+=","; fi
        types+='"fixtures"'
        first=false
    fi

    types+="]"
    echo "$types"
}

# Estimate test coverage
estimate_test_coverage() {
    local total_py_files=$(find services -name "*.py" 2>/dev/null | wc -l)
    local total_test_files=$(find tests services -path "*/tests/*" -name "*.py" 2>/dev/null | wc -l)

    local coverage=0
    if [[ $total_py_files -gt 0 ]]; then
        coverage=$(echo "scale=2; $total_test_files * 100 / $total_py_files" | bc -l 2>/dev/null || echo 0)
    fi

    echo "{\"estimated_coverage\": $coverage, \"source_files\": $total_py_files, \"test_files\": $total_test_files}"
}

# Detect test patterns
detect_test_patterns() {
    local patterns="["
    local first=true

    # AAA pattern (Arrange, Act, Assert)
    if find tests services -name "*.py" -exec grep -l "# Arrange\|# Act\|# Assert" {} + 2>/dev/null | head -1 >/dev/null; then
        patterns+='"aaa_pattern"'
        first=false
    fi

    # Given-When-Then
    if find tests services -name "*.py" -exec grep -l "given\|when\|then" {} + 2>/dev/null | head -1 >/dev/null; then
        if [[ "$first" == "false" ]]; then patterns+=","; fi
        patterns+='"given_when_then"'
        first=false
    fi

    # Parameterized tests
    if find tests services -name "*.py" -exec grep -l "@pytest.mark.parametrize\|@parameterized" {} + 2>/dev/null | head -1 >/dev/null; then
        if [[ "$first" == "false" ]]; then patterns+=","; fi
        patterns+='"parameterized"'
        first=false
    fi

    patterns+="]"
    echo "$patterns"
}

# Documentation analysis
analyze_documentation() {
    log_analyze "Analyzing documentation..."

    local docs_file="$CODEBASE_DIR/documentation_$TIMESTAMP.json"

    cat > "$docs_file" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "readme_analysis": $(analyze_readme),
  "api_docs": $(analyze_api_docs),
  "code_comments": $(analyze_code_comments),
  "inline_docs": $(analyze_inline_docs)
}
EOF
}

# Analyze README and main documentation
analyze_readme() {
    local readme_analysis="{"

    if [[ -f "README.md" ]]; then
        local word_count=$(wc -w < "README.md")
        local line_count=$(wc -l < "README.md")

        readme_analysis+="\"exists\": true,"
        readme_analysis+="\"word_count\": $word_count,"
        readme_analysis+="\"line_count\": $line_count,"

        # Check for common sections
        if grep -q -i "installation\|setup" "README.md"; then
            readme_analysis+="\"has_installation\": true,"
        else
            readme_analysis+="\"has_installation\": false,"
        fi

        if grep -q -i "usage\|example" "README.md"; then
            readme_analysis+="\"has_usage\": true,"
        else
            readme_analysis+="\"has_usage\": false,"
        fi

        if grep -q -i "api\|endpoint" "README.md"; then
            readme_analysis+="\"has_api_docs\": true"
        else
            readme_analysis+="\"has_api_docs\": false"
        fi
    else
        readme_analysis+="\"exists\": false"
    fi

    readme_analysis+="}"
    echo "$readme_analysis"
}

# Analyze API documentation
analyze_api_docs() {
    local api_docs="{"

    # Check for OpenAPI/Swagger docs
    if find . -name "*.yaml" -o -name "*.yml" -exec grep -l "openapi\|swagger" {} + 2>/dev/null | head -1 >/dev/null; then
        api_docs+="\"openapi\": true,"
    else
        api_docs+="\"openapi\": false,"
    fi

    # Check for docstrings in API endpoints
    local documented_endpoints=0
    local total_endpoints=0

    if find services -name "*.py" -exec grep -l "@app\.\|@router\." {} + 2>/dev/null; then
        find services -name "*.py" -exec grep -A 5 "@app\.\|@router\." {} + 2>/dev/null | grep -c '"""' || echo 0
        documented_endpoints=$?
        find services -name "*.py" -exec grep -c "@app\.\|@router\." {} + 2>/dev/null | awk '{sum += $1} END {print sum}' || echo 0
        total_endpoints=$?
    fi

    api_docs+="\"documented_endpoints\": $documented_endpoints,"
    api_docs+="\"total_endpoints\": $total_endpoints"

    api_docs+="}"
    echo "$api_docs"
}

# Analyze code comments
analyze_code_comments() {
    local comments="{"

    # Count comments in Python files
    local total_lines=$(find services -name "*.py" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}' || echo 0)
    local comment_lines=$(find services -name "*.py" -exec grep -c "^[[:space:]]*#" {} + 2>/dev/null | awk '{sum += $1} END {print sum}' || echo 0)

    local comment_ratio=0
    if [[ $total_lines -gt 0 ]]; then
        comment_ratio=$(echo "scale=2; $comment_lines * 100 / $total_lines" | bc -l 2>/dev/null || echo 0)
    fi

    comments+="\"comment_lines\": $comment_lines,"
    comments+="\"total_lines\": $total_lines,"
    comments+="\"comment_ratio\": $comment_ratio"

    comments+="}"
    echo "$comments"
}

# Analyze inline documentation
analyze_inline_docs() {
    local inline_docs="{"

    # Count docstrings
    local docstring_count=$(find services -name "*.py" -exec grep -c '"""' {} + 2>/dev/null | awk '{sum += $1} END {print sum}' || echo 0)
    local function_count=$(find services -name "*.py" -exec grep -c "^def \|^    def " {} + 2>/dev/null | awk '{sum += $1} END {print sum}' || echo 0)

    local docstring_ratio=0
    if [[ $function_count -gt 0 ]]; then
        docstring_ratio=$(echo "scale=2; $docstring_count * 100 / $function_count" | bc -l 2>/dev/null || echo 0)
    fi

    inline_docs+="\"docstring_count\": $docstring_count,"
    inline_docs+="\"function_count\": $function_count,"
    inline_docs+="\"docstring_ratio\": $docstring_ratio"

    inline_docs+="}"
    echo "$inline_docs"
}

# Git history analysis
analyze_git_history() {
    log_analyze "Analyzing git history..."

    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        log_warn "Not a git repository - skipping git analysis"
        return
    fi

    local git_file="$CODEBASE_DIR/git_history_$TIMESTAMP.json"

    cat > "$git_file" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "commit_patterns": $(analyze_commit_patterns),
  "branch_patterns": $(analyze_branch_patterns),
  "contributor_patterns": $(analyze_contributor_patterns),
  "file_change_patterns": $(analyze_file_changes)
}
EOF
}

# Analyze commit patterns
analyze_commit_patterns() {
    local patterns="{"

    # Recent commit frequency
    local recent_commits=$(git log --since="1 month ago" --oneline 2>/dev/null | wc -l || echo 0)
    patterns+="\"monthly_commits\": $recent_commits,"

    # Commit message patterns
    local feature_commits=$(git log --since="3 months ago" --oneline 2>/dev/null | grep -c "feat\|feature" || echo 0)
    local fix_commits=$(git log --since="3 months ago" --oneline 2>/dev/null | grep -c "fix\|bug" || echo 0)
    local refactor_commits=$(git log --since="3 months ago" --oneline 2>/dev/null | grep -c "refactor\|clean" || echo 0)

    patterns+="\"feature_commits\": $feature_commits,"
    patterns+="\"fix_commits\": $fix_commits,"
    patterns+="\"refactor_commits\": $refactor_commits"

    patterns+="}"
    echo "$patterns"
}

# Analyze branch patterns
analyze_branch_patterns() {
    local patterns="{"

    # Branch count and naming
    local total_branches=$(git branch -a 2>/dev/null | wc -l || echo 0)
    local feature_branches=$(git branch -a 2>/dev/null | grep -c "feature\|feat" || echo 0)
    local release_branches=$(git branch -a 2>/dev/null | grep -c "release\|rel" || echo 0)

    patterns+="\"total_branches\": $total_branches,"
    patterns+="\"feature_branches\": $feature_branches,"
    patterns+="\"release_branches\": $release_branches"

    patterns+="}"
    echo "$patterns"
}

# Analyze contributor patterns
analyze_contributor_patterns() {
    local patterns="{"

    # Contributor count
    local contributors=$(git log --format='%ae' 2>/dev/null | sort -u | wc -l || echo 0)
    local recent_contributors=$(git log --since="1 month ago" --format='%ae' 2>/dev/null | sort -u | wc -l || echo 0)

    patterns+="\"total_contributors\": $contributors,"
    patterns+="\"recent_contributors\": $recent_contributors"

    patterns+="}"
    echo "$patterns"
}

# Analyze file change patterns
analyze_file_changes() {
    local patterns="{"

    # Most changed files
    local most_changed=$(git log --name-only --pretty=format: 2>/dev/null | sort | uniq -c | sort -nr | head -5 | wc -l || echo 0)

    patterns+="\"frequently_changed_files\": $most_changed"

    patterns+="}"
    echo "$patterns"
}

# Build contextual understanding
build_context_map() {
    local focus_area="${1:-}"

    log_context "Building contextual understanding..."

    # Ensure we have recent analysis
    analyze_codebase false

    local context_file="$CONTEXT_DIR/context_map_$TIMESTAMP.json"

    cat > "$context_file" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "focus_area": "$focus_area",
  "codebase_summary": $(summarize_codebase),
  "key_patterns": $(extract_key_patterns),
  "development_context": $(build_development_context),
  "technical_debt": $(assess_technical_debt),
  "opportunities": $(identify_opportunities)
}
EOF

    # Update context index
    local temp_file=$(mktemp)
    jq --slurpfile ctx <(cat "$context_file") '.contexts += [$ctx[0]]' "$MEMORY_DIR/context_index.json" > "$temp_file"
    mv "$temp_file" "$MEMORY_DIR/context_index.json"

    log_success "Context map built: $context_file"
}

# Summarize codebase
summarize_codebase() {
    local summary="{"

    # Load architecture data
    local arch_data=$(jq '.structure.architecture // {}' "$MEMORY_DIR/codebase_map.json" 2>/dev/null)
    local project_type=$(echo "$arch_data" | jq -r '.project_type // "unknown"')
    local architecture_style=$(echo "$arch_data" | jq -r '.architecture_style // "unknown"')

    summary+="\"project_type\": \"$project_type\","
    summary+="\"architecture_style\": \"$architecture_style\","

    # Service count
    local service_count=$(echo "$arch_data" | jq '.services | length' 2>/dev/null || echo 0)
    summary+="\"service_count\": $service_count,"

    # Complexity assessment
    local total_files=$(find services -name "*.py" 2>/dev/null | wc -l)
    local avg_file_size=$(find services -name "*.py" -exec wc -l {} + 2>/dev/null | awk '{sum += $1; count++} END {if(count > 0) print int(sum/count); else print 0}')

    summary+="\"total_files\": $total_files,"
    summary+="\"avg_file_size\": $avg_file_size,"

    # Determine complexity level
    local complexity="simple"
    if [[ $service_count -gt 5 ]] || [[ $total_files -gt 50 ]]; then
        complexity="complex"
    elif [[ $service_count -gt 2 ]] || [[ $total_files -gt 20 ]]; then
        complexity="moderate"
    fi

    summary+="\"complexity\": \"$complexity\""

    summary+="}"
    echo "$summary"
}

# Extract key patterns
extract_key_patterns() {
    local patterns="["
    local first=true

    # Load pattern data
    local pattern_data=$(jq '.patterns[-1] // {}' "$MEMORY_DIR/pattern_registry.json" 2>/dev/null)

    # Extract design patterns
    local design_patterns=$(echo "$pattern_data" | jq -r '.design_patterns[]? // empty' 2>/dev/null)
    if [[ -n "$design_patterns" ]]; then
        echo "$design_patterns" | while read pattern; do
            if [[ "$first" == "true" ]]; then
                first=false
            else
                patterns+=","
            fi
            patterns+="{\"type\":\"design\",\"pattern\":\"$pattern\"}"
        done
    fi

    # Extract architectural patterns
    local arch_patterns=$(echo "$pattern_data" | jq -r '.architectural_patterns[]? // empty' 2>/dev/null)
    if [[ -n "$arch_patterns" ]]; then
        echo "$arch_patterns" | while read pattern; do
            if [[ "$first" == "true" ]]; then
                first=false
            else
                patterns+=","
            fi
            patterns+="{\"type\":\"architectural\",\"pattern\":\"$pattern\"}"
        done
    fi

    patterns+="]"
    echo "$patterns"
}

# Build development context
build_development_context() {
    local context="{"

    # Integration with learning system
    if [[ -f "$LEARNING_SYSTEM" ]]; then
        # Get recent development patterns
        local recent_commands=$(tail -10 "$PROJECT_ROOT/.learning/analytics/commands.log" 2>/dev/null | wc -l || echo 0)
        local recent_failures=$(tail -10 "$PROJECT_ROOT/.learning/analytics/failures.log" 2>/dev/null | wc -l || echo 0)

        context+="\"recent_activity\": $recent_commands,"
        context+="\"recent_issues\": $recent_failures,"

        # Most used commands
        local top_command=$(tail -100 "$PROJECT_ROOT/.learning/analytics/commands.log" 2>/dev/null | cut -d'|' -f3 | sort | uniq -c | sort -nr | head -1 | awk '{print $2}' || echo "unknown")
        context+="\"primary_workflow\": \"$top_command\","
    fi

    # Git context
    if git rev-parse --git-dir >/dev/null 2>&1; then
        local current_branch=$(git branch --show-current 2>/dev/null || echo "unknown")
        local uncommitted_changes=$(git status --porcelain 2>/dev/null | wc -l || echo 0)

        context+="\"current_branch\": \"$current_branch\","
        context+="\"uncommitted_changes\": $uncommitted_changes,"
    fi

    # Remove trailing comma
    context=$(echo "$context" | sed 's/,$//')
    context+="}"

    echo "$context"
}

# Assess technical debt
assess_technical_debt() {
    local debt="{"
    local debt_score=0

    # Code complexity indicators
    local large_files=$(find services -name "*.py" -exec wc -l {} + 2>/dev/null | awk '$1 > 300 {count++} END {print count+0}')
    if [[ $large_files -gt 0 ]]; then
        debt_score=$((debt_score + large_files))
    fi
    debt+="\"large_files\": $large_files,"

    # TODO/FIXME comments
    local todo_count=$(find services -name "*.py" -exec grep -c "TODO\|FIXME\|XXX" {} + 2>/dev/null | awk '{sum += $1} END {print sum+0}')
    debt_score=$((debt_score + todo_count / 2))
    debt+="\"todo_comments\": $todo_count,"

    # Duplicate code indicators
    local duplicate_functions=$(find services -name "*.py" -exec grep -h "^def " {} + 2>/dev/null | sort | uniq -d | wc -l || echo 0)
    debt_score=$((debt_score + duplicate_functions))
    debt+="\"potential_duplicates\": $duplicate_functions,"

    # Overall debt assessment
    local debt_level="low"
    if [[ $debt_score -gt 20 ]]; then
        debt_level="high"
    elif [[ $debt_score -gt 10 ]]; then
        debt_level="medium"
    fi

    debt+="\"debt_score\": $debt_score,"
    debt+="\"debt_level\": \"$debt_level\""

    debt+="}"
    echo "$debt"
}

# Identify opportunities
identify_opportunities() {
    local opportunities="["
    local first=true

    # Test coverage opportunities
    local test_coverage=$(jq '.structure.architecture.layers.tests // 0' "$MEMORY_DIR/codebase_map.json" 2>/dev/null)
    local source_files=$(jq '.structure.architecture.layers.services // 0' "$MEMORY_DIR/codebase_map.json" 2>/dev/null)

    if [[ $source_files -gt 0 ]] && [[ $test_coverage -lt $((source_files / 2)) ]]; then
        opportunities+="{\"type\":\"testing\",\"description\":\"Improve test coverage\",\"priority\":\"medium\"}"
        first=false
    fi

    # Documentation opportunities
    local doc_files=$(find . -name "*.md" | wc -l)
    if [[ $doc_files -lt 3 ]]; then
        if [[ "$first" == "false" ]]; then opportunities+=","; fi
        opportunities+="{\"type\":\"documentation\",\"description\":\"Enhance documentation\",\"priority\":\"low\"}"
        first=false
    fi

    # Performance opportunities
    if grep -r "time\.sleep\|Thread" services/ 2>/dev/null | head -1 >/dev/null; then
        if [[ "$first" == "false" ]]; then opportunities+=","; fi
        opportunities+="{\"type\":\"performance\",\"description\":\"Async optimization potential\",\"priority\":\"medium\"}"
        first=false
    fi

    # Security opportunities
    if grep -r "password\|secret\|key" services/ 2>/dev/null | grep -v "test\|example" | head -1 >/dev/null; then
        if [[ "$first" == "false" ]]; then opportunities+=","; fi
        opportunities+="{\"type\":\"security\",\"description\":\"Review secret management\",\"priority\":\"high\"}"
        first=false
    fi

    opportunities+="]"
    echo "$opportunities"
}

# Generate intelligent epic based on context
generate_intelligent_epic() {
    local epic_description="$1"
    local focus_area="${2:-general}"

    log_plan "Generating intelligent epic based on code context..."

    # Build context first
    build_context_map "$focus_area"

    # Load context data
    local context_data=$(jq '.contexts[-1] // {}' "$MEMORY_DIR/context_index.json" 2>/dev/null)
    local codebase_summary=$(echo "$context_data" | jq '.codebase_summary // {}')
    local project_type=$(echo "$codebase_summary" | jq -r '.project_type // "unknown"')
    local complexity=$(echo "$codebase_summary" | jq -r '.complexity // "simple"')
    local architecture_style=$(echo "$codebase_summary" | jq -r '.architecture_style // "standard"')

    # Generate context-aware epic
    local epic_file="$PLANS_DIR/intelligent_epic_$TIMESTAMP.yaml"

    cat > "$epic_file" << EOF
# Intelligent Epic: $epic_description
name: "$epic_description"
description: "$epic_description"
generated: "$(date -Iseconds)"
context_aware: true

# Codebase Context
codebase_context:
  project_type: "$project_type"
  architecture_style: "$architecture_style"
  complexity: "$complexity"
  focus_area: "$focus_area"

# Context-Aware Feature Breakdown
features:
EOF

    # Generate features based on project type and context
    case "$project_type" in
        "microservices_k8s")
            generate_microservices_features "$epic_description" "$complexity" >> "$epic_file"
            ;;
        "python_application")
            generate_python_app_features "$epic_description" "$complexity" >> "$epic_file"
            ;;
        *)
            generate_generic_features "$epic_description" "$complexity" >> "$epic_file"
            ;;
    esac

    # Add context-aware implementation strategy
    cat >> "$epic_file" << EOF

# Implementation Strategy (Context-Aware)
implementation_strategy:
  approach: "$(determine_implementation_approach "$project_type" "$complexity")"
  phases: $(generate_implementation_phases "$complexity")
  dependencies: $(analyze_implementation_dependencies)
  risks: $(identify_implementation_risks "$project_type")

# Integration Points
integration_points:
  existing_services: $(identify_service_integration_points)
  apis: $(identify_api_integration_points)
  databases: $(identify_database_integration_points)
  infrastructure: $(identify_infrastructure_integration_points)

# Quality Considerations
quality_gates:
  testing_strategy: "$(determine_testing_strategy "$project_type")"
  code_review_requirements: $(determine_review_requirements "$complexity")
  deployment_strategy: "$(determine_deployment_strategy "$architecture_style")"
  monitoring_requirements: $(determine_monitoring_requirements)

# Success Metrics
success_metrics:
  technical: $(define_technical_metrics "$focus_area")
  business: $(define_business_metrics "$focus_area")
  operational: $(define_operational_metrics)
EOF

    log_success "Intelligent epic generated: $epic_file"

    # Integrate with workflow system if available
    if [[ -f "$WORKFLOW_SYSTEM" ]]; then
        log_info "Integrating with workflow automation system..."
        # Create epic in workflow system with enhanced context
        "$WORKFLOW_SYSTEM" epic "$epic_description" "Context-aware epic generated from codebase analysis" "$complexity"
    fi

    echo "$epic_file"
}

# Generate features for microservices architecture
generate_microservices_features() {
    local epic_desc="$1"
    local complexity="$2"

    cat << EOF
  - name: "Service Architecture Design"
    description: "Design service boundaries and communication patterns"
    type: "architecture"
    priority: "high"
    effort: "medium"
    context_considerations:
      - "Existing service topology"
      - "Inter-service communication patterns"
      - "Data consistency requirements"

  - name: "API Contract Definition"
    description: "Define service APIs and contracts"
    type: "api_design"
    priority: "high"
    effort: "small"
    context_considerations:
      - "Existing API patterns"
      - "Versioning strategy"
      - "OpenAPI/Swagger documentation"

  - name: "Core Service Implementation"
    description: "Implement main service functionality"
    type: "development"
    priority: "high"
    effort: "$(determine_effort_for_complexity "$complexity")"
    context_considerations:
      - "Existing service patterns"
      - "Shared libraries and utilities"
      - "Error handling conventions"

  - name: "Service Integration"
    description: "Integrate with existing services and infrastructure"
    type: "integration"
    priority: "medium"
    effort: "medium"
    context_considerations:
      - "Service mesh configuration"
      - "Database connections"
      - "Message queue integration"

  - name: "Testing and Validation"
    description: "Comprehensive testing across service boundaries"
    type: "testing"
    priority: "medium"
    effort: "medium"
    context_considerations:
      - "Existing test infrastructure"
      - "Contract testing"
      - "End-to-end test scenarios"

  - name: "Deployment and Monitoring"
    description: "Deploy service and implement monitoring"
    type: "deployment"
    priority: "low"
    effort: "small"
    context_considerations:
      - "Kubernetes deployment patterns"
      - "Helm chart templates"
      - "Observability stack integration"
EOF
}

# Generate features for Python applications
generate_python_app_features() {
    local epic_desc="$1"
    local complexity="$2"

    cat << EOF
  - name: "Module Architecture"
    description: "Design module structure and dependencies"
    type: "architecture"
    priority: "high"
    effort: "small"
    context_considerations:
      - "Existing module patterns"
      - "Import conventions"
      - "Package structure"

  - name: "Core Implementation"
    description: "Implement main functionality"
    type: "development"
    priority: "high"
    effort: "$(determine_effort_for_complexity "$complexity")"
    context_considerations:
      - "Code style conventions"
      - "Type hint usage"
      - "Error handling patterns"

  - name: "Testing Suite"
    description: "Unit and integration tests"
    type: "testing"
    priority: "medium"
    effort: "medium"
    context_considerations:
      - "Existing test framework"
      - "Test organization patterns"
      - "Coverage requirements"

  - name: "Documentation"
    description: "API and usage documentation"
    type: "documentation"
    priority: "low"
    effort: "small"
    context_considerations:
      - "Documentation standards"
      - "Docstring conventions"
      - "Example patterns"
EOF
}

# Generate generic features
generate_generic_features() {
    local epic_desc="$1"
    local complexity="$2"

    cat << EOF
  - name: "Requirements Analysis"
    description: "Analyze and define requirements"
    type: "analysis"
    priority: "high"
    effort: "small"

  - name: "Design and Planning"
    description: "Technical design and implementation planning"
    type: "design"
    priority: "high"
    effort: "medium"

  - name: "Core Implementation"
    description: "Primary feature implementation"
    type: "development"
    priority: "high"
    effort: "$(determine_effort_for_complexity "$complexity")"

  - name: "Testing and Validation"
    description: "Testing and quality assurance"
    type: "testing"
    priority: "medium"
    effort: "medium"

  - name: "Documentation and Deployment"
    description: "Documentation and deployment preparation"
    type: "deployment"
    priority: "low"
    effort: "small"
EOF
}

# Helper functions for context-aware generation
determine_effort_for_complexity() {
    case "$1" in
        "simple") echo "small" ;;
        "moderate") echo "medium" ;;
        "complex") echo "large" ;;
        *) echo "medium" ;;
    esac
}

determine_implementation_approach() {
    local project_type="$1"
    local complexity="$2"

    case "$project_type" in
        "microservices_k8s") echo "incremental_service_deployment" ;;
        "python_application") echo "modular_development" ;;
        *) echo "iterative_development" ;;
    esac
}

generate_implementation_phases() {
    local complexity="$1"

    case "$complexity" in
        "simple")
            echo '["planning", "implementation", "testing"]'
            ;;
        "moderate")
            echo '["planning", "design", "implementation", "integration", "testing"]'
            ;;
        "complex")
            echo '["research", "planning", "design", "proof_of_concept", "implementation", "integration", "testing", "deployment"]'
            ;;
        *)
            echo '["planning", "implementation", "testing"]'
            ;;
    esac
}

analyze_implementation_dependencies() {
    # Load existing service dependencies
    local deps=$(jq '.dependencies.internal_deps // {}' "$MEMORY_DIR/codebase_map.json" 2>/dev/null)
    echo "$deps"
}

identify_implementation_risks() {
    local project_type="$1"

    local risks="["

    case "$project_type" in
        "microservices_k8s")
            risks+='"service_coordination",'
            risks+='"network_latency",'
            risks+='"data_consistency"'
            ;;
        "python_application")
            risks+='"dependency_conflicts",'
            risks+='"performance_impact"'
            ;;
        *)
            risks+='"integration_complexity",'
            risks+='"technical_debt"'
            ;;
    esac

    risks+="]"
    echo "$risks"
}

identify_service_integration_points() {
    local services=$(jq '.structure.architecture.services // []' "$MEMORY_DIR/codebase_map.json" 2>/dev/null)
    echo "$services"
}

identify_api_integration_points() {
    echo '[]'  # Simplified for now
}

identify_database_integration_points() {
    echo '[]'  # Simplified for now
}

identify_infrastructure_integration_points() {
    local infra=$(jq '.structure.architecture.infrastructure // {}' "$MEMORY_DIR/codebase_map.json" 2>/dev/null)
    echo "$infra"
}

determine_testing_strategy() {
    local project_type="$1"

    case "$project_type" in
        "microservices_k8s") echo "contract_testing_and_e2e" ;;
        "python_application") echo "unit_and_integration" ;;
        *) echo "standard_pyramid" ;;
    esac
}

determine_review_requirements() {
    local complexity="$1"

    case "$complexity" in
        "simple") echo '["peer_review"]' ;;
        "moderate") echo '["peer_review", "architecture_review"]' ;;
        "complex") echo '["peer_review", "architecture_review", "security_review"]' ;;
        *) echo '["peer_review"]' ;;
    esac
}

determine_deployment_strategy() {
    local architecture="$1"

    case "$architecture" in
        "microservices") echo "rolling_deployment" ;;
        "containerized") echo "blue_green_deployment" ;;
        *) echo "standard_deployment" ;;
    esac
}

determine_monitoring_requirements() {
    echo '["metrics", "logging", "health_checks"]'
}

define_technical_metrics() {
    local focus_area="$1"

    case "$focus_area" in
        "performance") echo '["response_time", "throughput", "error_rate"]' ;;
        "security") echo '["vulnerability_scan", "auth_success_rate", "access_control"]' ;;
        *) echo '["code_coverage", "build_success", "deployment_frequency"]' ;;
    esac
}

define_business_metrics() {
    local focus_area="$1"

    case "$focus_area" in
        "user_experience") echo '["user_satisfaction", "feature_adoption", "user_retention"]' ;;
        *) echo '["feature_usage", "time_to_value", "business_impact"]' ;;
    esac
}

define_operational_metrics() {
    echo '["uptime", "deployment_frequency", "mean_time_to_recovery"]'
}

# Generate contextual task recommendations
generate_contextual_tasks() {
    local epic_id="$1"
    local feature_context="$2"

    log_plan "Generating contextual tasks for epic: $epic_id"

    # Load epic context
    local epic_file="$PLANS_DIR/intelligent_epic_$epic_id.yaml"
    if [[ ! -f "$epic_file" ]]; then
        log_error "Epic file not found: $epic_file"
        return 1
    fi

    # Generate tasks based on current development context
    local tasks_file="$PLANS_DIR/contextual_tasks_${epic_id}_$TIMESTAMP.yaml"

    cat > "$tasks_file" << EOF
# Contextual Tasks for Epic: $epic_id
epic_id: "$epic_id"
generated: "$(date -Iseconds)"
context: "$feature_context"

tasks:
EOF

    # Generate context-aware tasks
    generate_development_tasks "$feature_context" >> "$tasks_file"

    log_success "Contextual tasks generated: $tasks_file"
}

# Generate development tasks based on context
generate_development_tasks() {
    local context="$1"

    # Load current development patterns from learning system
    local recent_commands=""
    if [[ -f "$PROJECT_ROOT/.learning/analytics/commands.log" ]]; then
        recent_commands=$(tail -20 "$PROJECT_ROOT/.learning/analytics/commands.log" | cut -d'|' -f3 | sort | uniq -c | sort -nr | head -3)
    fi

    cat << EOF
  - name: "Environment Setup"
    description: "Set up development environment with proper dependencies"
    type: "setup"
    priority: "high"
    estimated_time: "30 minutes"
    context_aware_steps:
      - "Activate virtual environment"
      - "Install dependencies from requirements.txt"
      - "Verify existing service integrations"
      - "Run initial health checks"

  - name: "Code Structure Planning"
    description: "Plan code organization following existing patterns"
    type: "planning"
    priority: "high"
    estimated_time: "1 hour"
    context_aware_steps:
      - "Review existing service structure"
      - "Identify reusable patterns and utilities"
      - "Plan module organization"
      - "Define interface contracts"

  - name: "Implementation with Pattern Adherence"
    description: "Implement following established code patterns"
    type: "development"
    priority: "high"
    estimated_time: "4-8 hours"
    context_aware_steps:
      - "Follow existing error handling patterns"
      - "Use established logging conventions"
      - "Implement with type hints (following codebase style)"
      - "Apply existing validation patterns"

  - name: "Testing Integration"
    description: "Implement tests using existing test infrastructure"
    type: "testing"
    priority: "medium"
    estimated_time: "2-4 hours"
    context_aware_steps:
      - "Use existing test fixtures and utilities"
      - "Follow established test organization"
      - "Integrate with existing CI/CD pipeline"
      - "Ensure coverage meets project standards"

  - name: "Quality Gates Compliance"
    description: "Ensure compliance with project quality standards"
    type: "quality"
    priority: "medium"
    estimated_time: "1 hour"
    context_aware_steps:
      - "Run 'just pre-commit-fix' for automated checks"
      - "Ensure all quality gates pass"
      - "Review with existing code review process"
      - "Validate against project standards"
EOF
}

# Memory-driven development suggestions
suggest_development_plan() {
    local goal="$1"
    local timeframe="${2:-medium}"

    log_plan "Generating memory-driven development plan for: $goal"

    # Ensure fresh context
    build_context_map

    # Load all available context
    local context_data=$(jq '.contexts[-1] // {}' "$MEMORY_DIR/context_index.json" 2>/dev/null)
    local codebase_summary=$(echo "$context_data" | jq '.codebase_summary // {}')
    local opportunities=$(echo "$context_data" | jq '.opportunities // []')
    local technical_debt=$(echo "$context_data" | jq '.technical_debt // {}')

    local plan_file="$PLANS_DIR/development_plan_$TIMESTAMP.md"

    cat > "$plan_file" << EOF
# Memory-Driven Development Plan: $goal

**Generated:** $(date)
**Timeframe:** $timeframe
**Context-Aware:** Yes

## 📊 Current Codebase Context

$(echo "$codebase_summary" | jq -r 'to_entries | map("- **\(.key | gsub("_"; " ") | . as $x | ($x[:1] | ascii_upcase) + $x[1:]):** \(.value)") | join("\n")')

## 🎯 Goal-Specific Recommendations

$(generate_goal_specific_recommendations "$goal" "$timeframe")

## 🚧 Technical Debt Considerations

**Debt Level:** $(echo "$technical_debt" | jq -r '.debt_level // "unknown"')

$(if [[ "$(echo "$technical_debt" | jq -r '.debt_level')" != "low" ]]; then
cat << EOD
### Debt Remediation Tasks:
- Address $(echo "$technical_debt" | jq -r '.large_files // 0') large files that may need refactoring
- Resolve $(echo "$technical_debt" | jq -r '.todo_comments // 0') TODO/FIXME comments
- Review $(echo "$technical_debt" | jq -r '.potential_duplicates // 0') potential code duplications

**Recommendation:** Address high-priority technical debt before implementing major new features.
EOD
fi)

## 💡 Identified Opportunities

$(echo "$opportunities" | jq -r '.[] | "- **\(.type | ascii_upcase):** \(.description) (Priority: \(.priority))"')

## 📋 Suggested Implementation Phases

$(generate_implementation_phases_for_goal "$goal" "$timeframe")

## 🔄 Integration with Existing Workflows

- **Quality Gates:** Use \`just pre-commit-fix\` before each commit
- **Testing:** Follow existing test patterns and coverage requirements
- **Deployment:** Leverage current Kubernetes/Helm infrastructure
- **Monitoring:** Integrate with existing observability stack

## 📈 Success Metrics

- **Technical:** Code coverage maintenance, build success rate, performance benchmarks
- **Process:** Reduced development cycle time, improved code review efficiency
- **Business:** Feature adoption, user satisfaction, system reliability

## 🎯 Next Actions

1. **Immediate (Today):**
   - Review this plan with stakeholders
   - Set up development environment
   - Create initial epic and features

2. **Short-term (This Week):**
   - Begin implementation of highest priority features
   - Set up monitoring and quality gates
   - Establish feedback loops

3. **Medium-term (This Month):**
   - Complete core functionality
   - Conduct thorough testing
   - Prepare for deployment

---
*This plan was generated using deep codebase analysis and learning system insights.*
EOF

    log_success "Development plan generated: $plan_file"

    # Auto-open if possible
    if command -v open >/dev/null 2>&1; then
        open "$plan_file"
    fi

    echo "$plan_file"
}

generate_goal_specific_recommendations() {
    local goal="$1"
    local timeframe="$2"

    # Analyze goal type and provide specific recommendations
    if echo "$goal" | grep -qi "performance\|speed\|optimization"; then
        cat << EOF
### Performance Focus Recommendations:
- **Database Optimization:** Review query patterns and add appropriate indexes
- **Caching Strategy:** Implement Redis/memory caching for frequent operations
- **Async Processing:** Convert blocking operations to async where beneficial
- **Profiling:** Add performance monitoring and profiling tools
- **Load Testing:** Implement comprehensive load testing scenarios
EOF
    elif echo "$goal" | grep -qi "security\|auth\|protection"; then
        cat << EOF
### Security Focus Recommendations:
- **Authentication:** Strengthen auth mechanisms and session management
- **Input Validation:** Review and harden all input validation
- **Secret Management:** Audit and improve secret storage/rotation
- **Security Scanning:** Integrate SAST/DAST tools into CI/CD
- **Access Control:** Review and enhance authorization mechanisms
EOF
    elif echo "$goal" | grep -qi "scale\|scaling\|growth"; then
        cat << EOF
### Scalability Focus Recommendations:
- **Service Architecture:** Design for horizontal scaling
- **Database Sharding:** Plan for data partitioning strategies
- **Load Balancing:** Implement proper load distribution
- **Monitoring:** Set up comprehensive metrics and alerting
- **Infrastructure:** Design auto-scaling policies
EOF
    else
        cat << EOF
### General Development Recommendations:
- **Incremental Approach:** Break down into manageable iterations
- **Quality First:** Maintain high code quality and test coverage
- **Documentation:** Keep documentation current and comprehensive
- **Feedback Loops:** Establish rapid feedback and validation cycles
- **Risk Mitigation:** Identify and plan for potential roadblocks
EOF
    fi
}

generate_implementation_phases_for_goal() {
    local goal="$1"
    local timeframe="$2"

    case "$timeframe" in
        "short"|"immediate")
            cat << EOF
### Phase 1: Immediate Implementation (1-2 weeks)
- **Week 1:** Requirements analysis, design, and planning
- **Week 2:** Core implementation and basic testing

**Key Deliverables:**
- Working prototype
- Basic test coverage
- Initial documentation
EOF
            ;;
        "medium"|"standard")
            cat << EOF
### Phase 1: Foundation (Weeks 1-2)
- Requirements analysis and technical design
- Environment setup and tooling
- Core architecture implementation

### Phase 2: Implementation (Weeks 3-4)
- Feature development
- Testing and validation
- Integration with existing systems

### Phase 3: Refinement (Weeks 5-6)
- Performance optimization
- Security hardening
- Documentation completion
- Deployment preparation

**Key Deliverables:**
- Production-ready implementation
- Comprehensive test suite
- Full documentation
- Deployment scripts
EOF
            ;;
        "long"|"extended")
            cat << EOF
### Phase 1: Research & Planning (Month 1)
- Comprehensive requirements analysis
- Technical research and proof of concept
- Architecture design and review
- Risk assessment and mitigation planning

### Phase 2: Foundation Development (Month 2)
- Core infrastructure setup
- Basic functionality implementation
- Initial testing framework
- CI/CD pipeline integration

### Phase 3: Feature Development (Month 3)
- Advanced feature implementation
- Comprehensive testing
- Performance optimization
- Security implementation

### Phase 4: Integration & Deployment (Month 4)
- System integration testing
- User acceptance testing
- Production deployment
- Monitoring and observability setup

**Key Deliverables:**
- Enterprise-grade implementation
- Full test automation
- Complete documentation suite
- Production monitoring
- Training materials
EOF
            ;;
    esac
}

# Show memory dashboard
show_memory_dashboard() {
    clear
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                 PLAN MEMORY DASHBOARD                         ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo

    # Memory system status
    local last_scan=$(jq -r '.last_scan // "never"' "$MEMORY_DIR/codebase_map.json" 2>/dev/null)
    local context_count=$(jq '.contexts | length' "$MEMORY_DIR/context_index.json" 2>/dev/null || echo 0)
    local pattern_count=$(jq '.patterns | length' "$MEMORY_DIR/pattern_registry.json" 2>/dev/null || echo 0)

    printf "🧠 MEMORY STATUS\n"
    printf "   Last Scan:       %s\n" "$last_scan"
    printf "   Context Maps:    %d\n" "$context_count"
    printf "   Pattern Library: %d\n" "$pattern_count"
    echo

    # Codebase summary
    local project_type=$(jq -r '.structure.architecture.project_type // "unknown"' "$MEMORY_DIR/codebase_map.json" 2>/dev/null)
    local architecture=$(jq -r '.structure.architecture.architecture_style // "unknown"' "$MEMORY_DIR/codebase_map.json" 2>/dev/null)
    local service_count=$(jq '.structure.architecture.services | length' "$MEMORY_DIR/codebase_map.json" 2>/dev/null || echo 0)

    printf "🏗️  CODEBASE ANALYSIS\n"
    printf "   Project Type:    %s\n" "$project_type"
    printf "   Architecture:    %s\n" "$architecture"
    printf "   Services:        %d\n" "$service_count"
    echo

    # Recent intelligence
    if [[ -f "$CONTEXT_DIR/context_map_$TIMESTAMP.json" ]] || [[ $(find "$CONTEXT_DIR" -name "context_map_*.json" | wc -l) -gt 0 ]]; then
        printf "🎯 RECENT INTELLIGENCE\n"

        # Load latest context
        local latest_context=$(find "$CONTEXT_DIR" -name "context_map_*.json" | sort | tail -1)
        if [[ -n "$latest_context" ]]; then
            local complexity=$(jq -r '.codebase_summary.complexity // "unknown"' "$latest_context" 2>/dev/null)
            local debt_level=$(jq -r '.technical_debt.debt_level // "unknown"' "$latest_context" 2>/dev/null)
            local opportunity_count=$(jq '.opportunities | length' "$latest_context" 2>/dev/null || echo 0)

            printf "   Complexity:      %s\n" "$complexity"
            printf "   Tech Debt:       %s\n" "$debt_level"
            printf "   Opportunities:   %d\n" "$opportunity_count"
        fi
    fi
    echo

    printf "⚡ QUICK ACTIONS\n"
    printf "   1. Analyze codebase (plan-memory.sh analyze)\n"
    printf "   2. Generate intelligent epic\n"
    printf "   3. Create development plan\n"
    printf "   4. Review patterns and opportunities\n"
    echo

    # Available plans
    local plan_count=$(find "$PLANS_DIR" -name "*.yaml" -o -name "*.md" 2>/dev/null | wc -l || echo 0)
    if [[ $plan_count -gt 0 ]]; then
        printf "📋 AVAILABLE PLANS (%d)\n" "$plan_count"
        find "$PLANS_DIR" -name "*.yaml" -o -name "*.md" | sort | tail -5 | while read plan_file; do
            local plan_name=$(basename "$plan_file" | sed 's/\.[^.]*$//')
            printf "   - %s\n" "$plan_name"
        done
    fi
    echo
}

# Show help
show_help() {
    cat << EOF
🧠 Universal Development Plan Memory System

USAGE:
    $0 [COMMAND] [OPTIONS]

COMMANDS:
    init                        Initialize memory system
    analyze [force]             Deep codebase analysis and indexing
    context [focus_area]        Build contextual understanding

    # Intelligent Planning
    epic <description> [area]   Generate context-aware epic
    plan <goal> [timeframe]     Generate development plan
    tasks <epic_id> [context]   Generate contextual tasks

    # Memory Operations
    patterns                    Show discovered patterns
    opportunities              Show identified opportunities
    dashboard                  Interactive memory dashboard

    # Maintenance
    cleanup [days]             Clean old memory data
    export [format]            Export memory data

EXAMPLES:
    # Initialize and analyze codebase
    $0 init && $0 analyze

    # Generate intelligent epic
    $0 epic "API Rate Limiting System" performance

    # Create development plan
    $0 plan "Improve system performance" medium

    # Build context and generate suggestions
    $0 context security && $0 opportunities

MEMORY STRUCTURE:
    .plan-memory/
    ├── codebase/          # Deep codebase analysis
    ├── patterns/          # Discovered patterns and anti-patterns
    ├── context/           # Contextual understanding maps
    ├── plans/             # Generated plans and epics
    └── knowledge/         # Accumulated development knowledge

INTEGRATION:
    - Workflow System: Auto-creates epics with enhanced context
    - Learning System: Uses development patterns and history
    - Quality Gates: Considers existing quality standards
    - Git History: Analyzes development patterns and trends

ENVIRONMENT VARIABLES:
    PLAN_MEMORY_LEVEL=deep     Set analysis depth (basic|standard|deep)
    CONTEXT_FOCUS=performance  Default context focus area

EOF
}

# Main execution
main() {
    cd "$PROJECT_ROOT"

    case "${1:-help}" in
        init)
            init_memory_system
            ;;
        analyze)
            init_memory_system
            analyze_codebase "${2:-false}"
            ;;
        context)
            init_memory_system
            build_context_map "${2:-}"
            ;;
        epic)
            if [[ $# -lt 2 ]]; then
                log_error "Usage: epic <description> [focus_area]"
                exit 1
            fi
            init_memory_system
            generate_intelligent_epic "$2" "${3:-general}"
            ;;
        plan)
            if [[ $# -lt 2 ]]; then
                log_error "Usage: plan <goal> [timeframe]"
                exit 1
            fi
            init_memory_system
            suggest_development_plan "$2" "${3:-medium}"
            ;;
        tasks)
            if [[ $# -lt 2 ]]; then
                log_error "Usage: tasks <epic_id> [context]"
                exit 1
            fi
            init_memory_system
            generate_contextual_tasks "$2" "${3:-general}"
            ;;
        patterns)
            if [[ -f "$MEMORY_DIR/pattern_registry.json" ]]; then
                jq '.patterns[-1] // {}' "$MEMORY_DIR/pattern_registry.json"
            else
                log_warn "No patterns found - run 'analyze' first"
            fi
            ;;
        opportunities)
            init_memory_system
            build_context_map
            local latest_context=$(find "$CONTEXT_DIR" -name "context_map_*.json" | sort | tail -1)
            if [[ -n "$latest_context" ]]; then
                jq '.opportunities // []' "$latest_context"
            else
                log_warn "No opportunities identified - run 'context' first"
            fi
            ;;
        dashboard)
            init_memory_system
            show_memory_dashboard
            ;;
        cleanup)
            cleanup_memory_data "${2:-30}"
            ;;
        export)
            export_memory_data "${2:-json}"
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

# Cleanup memory data
cleanup_memory_data() {
    local days="${1:-30}"
    log_info "Cleaning memory data older than $days days..."

    local cutoff_date=$(date -d "$days days ago" '+%Y%m%d' 2>/dev/null || date -v-${days}d '+%Y%m%d' 2>/dev/null || echo "")

    if [[ -n "$cutoff_date" ]]; then
        find "$MEMORY_DIR" -name "*_[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_*" | while read file; do
            local file_date=$(echo "$file" | grep -o '[0-9]\{8\}' | head -1)
            if [[ -n "$file_date" ]] && [[ "$file_date" < "$cutoff_date" ]]; then
                rm -f "$file"
            fi
        done
        log_success "Memory cleanup complete"
    else
        log_warn "Could not determine cutoff date"
    fi
}

# Export memory data
export_memory_data() {
    local format="${1:-json}"
    local export_file="$MEMORY_DIR/memory_export_$TIMESTAMP.$format"

    log_info "Exporting memory data to $format format..."

    case "$format" in
        json)
            cat > "$export_file" << EOF
{
  "export_timestamp": "$(date -Iseconds)",
  "codebase_map": $(cat "$MEMORY_DIR/codebase_map.json" 2>/dev/null || echo '{}'),
  "pattern_registry": $(cat "$MEMORY_DIR/pattern_registry.json" 2>/dev/null || echo '{}'),
  "context_index": $(cat "$MEMORY_DIR/context_index.json" 2>/dev/null || echo '{}'),
  "knowledge_graph": $(cat "$MEMORY_DIR/knowledge_graph.json" 2>/dev/null || echo '{}')
}
EOF
            ;;
        *)
            log_error "Unsupported export format: $format"
            return 1
            ;;
    esac

    log_success "Memory data exported to: $export_file"
}

# Cleanup handler
cleanup() {
    log_info "Memory system session completed"
}

trap cleanup EXIT

main "$@"
