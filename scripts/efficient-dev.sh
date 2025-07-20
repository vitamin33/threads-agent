# scripts/efficient-dev.sh
#!/bin/bash

# Token-efficient development assistant with predictive capabilities

# Context integration
CONTEXT_DIR="$HOME/.threads-agent/context"
CURRENT_SESSION="$CONTEXT_DIR/current.ctx"

# Health check function for infrastructure status
health_check() {
    local status_file="/tmp/threads-agent-health-$(date +%s).tmp"
    local issues=()
    local warnings=()
    local good=()
    
    echo "🔍 Infrastructure Health Check"
    echo "==============================="
    
    # Check k3d cluster
    if k3d cluster list 2>/dev/null | grep -q "dev.*running"; then
        good+=("✅ k3d cluster 'dev' running")
    else
        issues+=("❌ k3d cluster 'dev' not running (run: just bootstrap)")
    fi
    
    # Check kubectl connectivity
    if kubectl get nodes >/dev/null 2>&1; then
        good+=("✅ kubectl connectivity")
        
        # Check pod status
        local failed_pods=$(kubectl get pods --no-headers 2>/dev/null | grep -v Running | grep -v Completed | wc -l | tr -d ' ')
        if [[ $failed_pods -eq 0 ]]; then
            good+=("✅ All pods running")
        else
            warnings+=("⚠️  $failed_pods pod(s) not running (check: kubectl get pods)")
        fi
        
        # Check critical services
        for svc in orchestrator celery-worker persona-runtime fake-threads; do
            if kubectl get svc $svc >/dev/null 2>&1; then
                good+=("✅ Service $svc deployed")
            else
                issues+=("❌ Service $svc missing (run: just deploy-dev)")
            fi
        done
        
    else
        issues+=("❌ kubectl not connected (check cluster status)")
    fi
    
    # Check port availability for testing
    for port in 8080 9009 6333 5432; do
        if lsof -i:$port >/dev/null 2>&1; then
            warnings+=("⚠️  Port $port in use (may conflict with port-forward)")
        fi
    done
    
    # Check Docker
    if docker info >/dev/null 2>&1; then
        good+=("✅ Docker running")
        
        # Check local images
        local missing_images=()
        for img in orchestrator celery-worker persona-runtime fake-threads; do
            if ! docker images | grep -q "$img.*local"; then
                missing_images+=("$img")
            fi
        done
        
        if [[ ${#missing_images[@]} -eq 0 ]]; then
            good+=("✅ All service images built")
        else
            warnings+=("⚠️  Missing images: ${missing_images[*]} (run: just images)")
        fi
    else
        issues+=("❌ Docker not running")
    fi
    
    # Check git state
    if git status >/dev/null 2>&1; then
        good+=("✅ Git repository")
        
        local uncommitted=$(git status --porcelain | wc -l | tr -d ' ')
        if [[ $uncommitted -gt 0 ]]; then
            warnings+=("⚠️  $uncommitted uncommitted changes")
        fi
        
        local branch=$(git branch --show-current)
        if [[ "$branch" == "main" ]]; then
            warnings+=("⚠️  On main branch (consider feature branch)")
        else
            good+=("✅ On feature branch: $branch")
        fi
    else
        issues+=("❌ Not in git repository")
    fi
    
    # Check test readiness
    if [[ -f pytest.ini ]]; then
        good+=("✅ Test configuration present")
    else
        warnings+=("⚠️  No pytest.ini found")
    fi
    
    # Display results
    if [[ ${#good[@]} -gt 0 ]]; then
        echo -e "\n🟢 HEALTHY:"
        printf '%s\n' "${good[@]}"
    fi
    
    if [[ ${#warnings[@]} -gt 0 ]]; then
        echo -e "\n🟡 WARNINGS:"
        printf '%s\n' "${warnings[@]}"
    fi
    
    if [[ ${#issues[@]} -gt 0 ]]; then
        echo -e "\n🔴 ISSUES:"
        printf '%s\n' "${issues[@]}"
        echo -e "\n💡 Quick fix: just e2e-prepare"
        return 1
    fi
    
    echo -e "\n🎉 System healthy for development!"
    return 0
}

# Predictive development assistant
predict() {
    local predictions=()
    local context_info=""
    
    echo "🔮 Development Predictions"
    echo "=========================="
    
    # Load context if available
    if [[ -f "$CURRENT_SESSION" ]]; then
        context_info=$(head -5 "$CURRENT_SESSION" | tail -4 | tr '\n' ' ')
        echo "📋 Context: $context_info"
        echo ""
    fi
    
    # Analyze git state
    if git status >/dev/null 2>&1; then
        local branch=$(git branch --show-current)
        local uncommitted=$(git status --porcelain | wc -l | tr -d ' ')
        local untracked=$(git ls-files --others --exclude-standard | wc -l | tr -d ' ')
        
        # Branch analysis
        if [[ "$branch" =~ ^cra-[0-9]+-.*$ ]]; then
            local ticket=$(echo "$branch" | grep -o 'cra-[0-9]\+')
            predictions+=("🎯 Working on $ticket - consider updating Linear status")
        fi
        
        # Change analysis
        if [[ $uncommitted -gt 0 ]]; then
            local modified=$(git status --porcelain | grep "^ M" | wc -l | tr -d ' ')
            local added=$(git status --porcelain | grep "^A" | wc -l | tr -d ' ')
            
            if [[ $modified -gt 3 ]]; then
                predictions+=("📝 $modified files modified - consider atomic commits")
            fi
            
            # Predict test needs
            if git status --porcelain | grep -q "\.py$"; then
                predictions+=("🧪 Python files changed - run: just test-watch")
            fi
            
            # Predict lint needs
            if git status --porcelain | grep -q -E "\.(py|js|ts)$"; then
                predictions+=("🧹 Code files changed - run: just lint before commit")
            fi
        fi
        
        if [[ $untracked -gt 0 ]]; then
            predictions+=("📁 $untracked untracked files - review and add or gitignore")
        fi
        
        # Recent commit analysis
        local last_commit=$(git log -1 --pretty=format:"%s" 2>/dev/null)
        if [[ "$last_commit" =~ ^(feat|fix|test|docs|refactor) ]]; then
            if [[ "$last_commit" =~ feat ]]; then
                predictions+=("🚀 Feature commit detected - consider adding tests")
            elif [[ "$last_commit" =~ fix ]]; then
                predictions+=("🔧 Bug fix committed - verify with: just e2e")
            fi
        fi
    fi
    
    # Analyze file patterns
    if [[ -d services ]]; then
        local service_changes=$(git status --porcelain 2>/dev/null | grep "services/" | cut -d'/' -f2 | sort | uniq | head -3)
        if [[ -n "$service_changes" ]]; then
            predictions+=("🔧 Service changes detected: $service_changes")
            predictions+=("🐳 Consider rebuilding images: just images")
        fi
    fi
    
    # Analyze test patterns
    if [[ -d tests ]]; then
        if git status --porcelain 2>/dev/null | grep -q "test.*\.py$"; then
            predictions+=("🔬 Test files modified - run specific tests first")
        fi
        
        # Check for missing test coverage
        if git status --porcelain 2>/dev/null | grep -q "services/.*\.py$" && ! git status --porcelain 2>/dev/null | grep -q "test"; then
            predictions+=("⚠️  Code changes without test updates - consider test coverage")
        fi
    fi
    
    # Infrastructure predictions
    if ! k3d cluster list 2>/dev/null | grep -q "dev.*running"; then
        predictions+=("🏗️  Infrastructure down - start with: just bootstrap")
    elif ! kubectl get pods >/dev/null 2>&1; then
        predictions+=("🚀 Cluster ready but no deployment - run: just deploy-dev")
    else
        local failing_pods=$(kubectl get pods --no-headers 2>/dev/null | grep -v Running | grep -v Completed | wc -l | tr -d ' ')
        if [[ $failing_pods -gt 0 ]]; then
            predictions+=("🚨 $failing_pods failing pods - check: kubectl get pods")
        fi
    fi
    
    # Configuration predictions
    if [[ -f chart/values-dev.yaml ]] && git status --porcelain 2>/dev/null | grep -q "chart/"; then
        predictions+=("⚙️  Helm config changed - redeploy: just deploy-dev")
    fi
    
    # Dependency predictions  
    if git status --porcelain 2>/dev/null | grep -q "requirements\.txt"; then
        predictions+=("📦 Dependencies changed - rebuild images: just images")
    fi
    
    # Development flow predictions
    local hour=$(date +%H)
    if [[ $hour -lt 10 ]]; then
        predictions+=("🌅 Morning session - consider: health-check → context review → focused work")
    elif [[ $hour -gt 17 ]]; then
        predictions+=("🌅 Evening session - consider: save context → review → ship work")
    fi
    
    # Display predictions
    if [[ ${#predictions[@]} -gt 0 ]]; then
        printf '%s\n' "${predictions[@]}"
        echo ""
        echo "💡 Next suggested action:"
        
        # Prioritize suggestions
        if [[ "${predictions[*]}" =~ "Infrastructure down" ]]; then
            echo "   just bootstrap"
        elif [[ "${predictions[*]}" =~ "no deployment" ]]; then
            echo "   just deploy-dev"
        elif [[ "${predictions[*]}" =~ "Test files modified" ]]; then
            echo "   just test-watch"
        elif [[ "${predictions[*]}" =~ "Code files changed" ]]; then
            echo "   just lint"
        elif [[ $uncommitted -gt 0 ]]; then
            echo "   Review changes and commit focused work"
        else
            echo "   just next"
        fi
    else
        echo "🎯 System stable - ready for focused development"
        echo "💡 Suggested: just next"
    fi
}

case "$1" in
    "health")
        # Infrastructure health check
        health_check
        ;;
    "predict")
        # Predictive development assistant
        predict
        ;;
    "next")
        # Enhanced next action with predictions
        predict | tail -2
        echo ""
        claude "Next specific task: check Linear progress, recommend immediate action (1-2 sentences)."
        ;;
    "code")
        if [ -z "$2" ]; then
            echo "Usage: $0 code 'specific requirement'"
            exit 1
        fi
        # Enhanced code generation with context
        local context_hint=""
        if [[ -f "$CURRENT_SESSION" ]]; then
            context_hint="Current context: $(head -3 "$CURRENT_SESSION" | tail -1) "
        fi
        claude "Generate code for: $2. $context_hint Use existing patterns from my codebase. Return only the code with minimal explanation."
        ;;
    "fix")
        if [ -z "$2" ]; then
            echo "Usage: $0 fix 'error description'"
            exit 1
        fi
        # Enhanced debugging with infrastructure context
        echo "🔧 Running health check first..."
        if ! health_check >/dev/null 2>&1; then
            echo "⚠️  Infrastructure issues detected - may be related to your problem"
        fi
        claude "Debug this specific issue: $2. Check relevant logs/database. Provide solution only."
        ;;
    "task")
        # Enhanced task planning with git context
        local branch_context=""
        if git status >/dev/null 2>&1; then
            branch_context="Current branch: $(git branch --show-current). "
        fi
        claude "Current Linear project: create 3-5 specific tasks for next sprint. $branch_context Format: Title | Description | Acceptance Criteria. No extra explanation."
        ;;
    "review")
        # Enhanced code review with predictive insights
        echo "🔍 Running predictions first..."
        predict | grep -E "(⚠️|🧪|🧹)" | head -3
        echo ""
        claude "Review my recent commits. Identify specific issues and actionable improvements only."
        ;;
    "smart")
        # Comprehensive development assistant
        echo "🧠 Smart Development Assistant"
        echo "=============================="
        echo ""
        health_check
        echo ""
        predict
        ;;
    *)
        echo "Efficient Development Commands:"
        echo "  health          - Infrastructure health check"
        echo "  predict         - Predictive development suggestions"
        echo "  smart           - Comprehensive health + predictions"
        echo "  next            - Get immediate next action (enhanced)"
        echo "  code 'req'      - Generate specific code (context-aware)"
        echo "  fix 'error'     - Debug specific issue (infrastructure-aware)"
        echo "  task            - Create sprint tasks (branch-aware)"
        echo "  review          - Review recent changes (prediction-enhanced)"
        ;;
esac
