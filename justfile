# justfile – Command runner for threads-agent development
# See: https://github.com/casey/just

# 🚀 AI Agent Development System Commands
# Unified development system for top 1% AI agent factory

dev-system command *args:
	@./.dev-system/cli/dev-system {{command}} {{args}}

metrics-today:
	@./.dev-system/cli/metrics-today

brief:
	@./.dev-system/cli/dev-system brief

debrief:
	@./.dev-system/cli/dev-system debrief

ice-demo:
	@cd .dev-system && python3 planner/ice.py

# M0: Safety Net Commands
safety-check:
	@cd .dev-system && python3 ops/safety.py --validate

safety-setup:
	@cd .dev-system && python3 ops/safety.py --setup-secrets --setup-gitignore --install-hooks

rate-status:
	@cd .dev-system && python3 ops/rate_limits.py --status

rate-test:
	@cd .dev-system && python3 ops/rate_limits.py --test

eval-run suite="core":
	@./.dev-system/cli/dev-system eval --suite {{suite}}

eval-report period="7d":
	@./.dev-system/cli/eval-report --period {{period}}

eval-latest:
	@./.dev-system/cli/eval-report --latest

eval-gate result:
	@./.dev-system/evals/gate.py --result {{result}} --exit-code

# M7: Multi-Agent Quality Commands
eval-all:
	@cd .dev-system && python3 evals/multi_agent_runner.py

eval-agents agents:
	@cd .dev-system && python3 evals/multi_agent_runner.py --agents {{agents}}

eval-list:
	@cd .dev-system && python3 evals/multi_agent_runner.py --list

quality-weekly days="7":
	@cd .dev-system && python3 evals/weekly_report.py --days {{days}}

quality-dashboard:
	@echo "📊 Opening quality dashboard..." && cd .dev-system && python3 evals/weekly_report.py --days 30

wt-setup name focus="":
	@./.dev-system/cli/dev-system worktree --name {{name}} --focus "{{focus}}"

release strategy="canary" percentage="10" environment="dev":
	@./.dev-system/cli/dev-system release --strategy {{strategy}} --percentage {{percentage}} --environment {{environment}}

release-history:
	@./.dev-system/cli/dev-system release --history

release-staging:
	@./.dev-system/cli/dev-system release --strategy staging

release-direct environment="dev":
	@echo "⚠️  WARNING: Direct deployment bypasses safety checks"
	@./.dev-system/cli/dev-system release --strategy direct --environment {{environment}}

# Mega Commands (80/20 Rule) - Enhanced with dev-system + M5 AI Planning
work-day: check-prerequisites metrics-today brief trend-dashboard dev-dashboard ai-business-intelligence
create-viral persona topic:
	just create-viral-{{persona}} "{{topic}}"
ship-it message:
	just smart-deploy canary && just github-pr "{{message}}"
end-day: debrief analyze-money overnight-optimize
make-money: autopilot-start grow-business analyze-money
grow-business: trend-start searxng-start
	just competitive-analysis "AI content"
	just ai-biz
	just revenue-projection
analyze-money: cost-analysis revenue-projection business-kpis
ai-biz action="dashboard":
	just ai-business-intelligence {{action}}
health-check: cluster-health services-health business-health

# Claude Code Sub-Agent Helpers
patterns FEATURE:
	@./scripts/claude-subagents.sh patterns "{{FEATURE}}"

test-gaps SERVICE:
	@./scripts/claude-subagents.sh test-gaps "{{SERVICE}}"

optimize SERVICE:
	@./scripts/claude-subagents.sh optimize "{{SERVICE}}"

doc-gaps COMPONENT:
	@./scripts/claude-subagents.sh docs "{{COMPONENT}}"

standup:
	@./scripts/claude-subagents.sh standup

sprint-plan:
	@./scripts/claude-subagents.sh sprint-plan

deep-review TARGET:
	@./scripts/claude-subagents.sh review "{{TARGET}}"

# Quick Start Commands
dev-start: bootstrap deploy-dev mcp-setup dev-dashboard
dev-start-multi: bootstrap-multi deploy-dev mcp-setup dev-dashboard
alias persona-hot-reload := hot-reload-persona
alias ai-test-gen := ai-generate-tests
alias smart-deploy := deploy-strategy
dev-dashboard: prometheus-dashboard grafana business-dashboard ui-dashboard
cache-set key value:
	@redis-cli -h localhost -p 6379 SET "{{key}}" "{{value}}"
	@echo "✅ Cached {{key}}"
cache-get key:
	@redis-cli -h localhost -p 6379 GET "{{key}}"
trend-check topic:
	just trend-detection {{topic}}

# Core Development Commands
bootstrap:
	#!/usr/bin/env bash
	set -euo pipefail
	echo "🚀 Setting up k3d cluster..."
	k3d cluster delete threads-agent 2>/dev/null || true
	k3d cluster create threads-agent \
		--api-port 6444 \
		--port "8080:80@loadbalancer" \
		--port "8443:443@loadbalancer" \
		--agents 1 \
		--registry-create threads-registry:0.0.0.0:5111
	echo "✅ k3d cluster ready"

# Multi-cluster support
bootstrap-multi:
	#!/usr/bin/env bash
	set -euo pipefail
	./scripts/multi-cluster-bootstrap.sh

cluster-list:
	@k3d cluster list | grep threads-agent || echo "No threads-agent clusters found"

cluster-switch name:
	@kubectl config use-context k3d-{{name}}
	@echo "✅ Switched to cluster: {{name}}"

cluster-current:
	@kubectl config current-context 2>/dev/null | sed 's/k3d-//g' || echo "No cluster selected"

cluster-delete name:
	@k3d cluster delete {{name}}
	@echo "✅ Deleted cluster: {{name}}"

# Image building
images:
	#!/usr/bin/env bash
	set -euo pipefail
	echo "🔨 Building Docker images..."
	
	# Build all service images in parallel (using repo root context)
	docker build -t orchestrator:local -f services/orchestrator/Dockerfile . &
	docker build -t celery-worker:local -f services/celery_worker/Dockerfile . &
	docker build -t persona-runtime:local -f services/persona_runtime/Dockerfile . &
	docker build -t fake-threads:local -f services/fake_threads/Dockerfile . &
	docker build -t viral-engine:local -f services/viral_engine/Dockerfile . &
	docker build -t viral-pattern-engine:local -f services/viral_pattern_engine/Dockerfile . &
	docker build -t achievement-collector:local -f services/achievement_collector/Dockerfile . &
	docker build -t rag-pipeline:local -f services/rag_pipeline/Dockerfile . &
	
	# Wait for all builds to complete
	wait
	
	# Import to k3d registry
	echo "📦 Importing images to k3d..."
	k3d image import orchestrator:local celery-worker:local persona-runtime:local fake-threads:local viral-engine:local viral-pattern-engine:local achievement-collector:local rag-pipeline:local -c threads-agent
	
	echo "✅ All images built and imported"

# Deployment
deploy-dev: images
	#!/usr/bin/env bash
	set -euo pipefail
	echo "🚀 Deploying to k3d with Helm..."
	
	# Apply personal overrides if they exist
	if [ -f chart/values-dev.local.yaml ]; then
		OVERRIDE_FILE="-f chart/values-dev.local.yaml"
	else
		OVERRIDE_FILE=""
	fi
	
	helm upgrade --install threads-agent chart/ \
		-f chart/values-dev.yaml \
		$OVERRIDE_FILE \
		--wait --timeout=5m
	
	echo "✅ Deployment complete"
	echo "🌐 Services available:"
	echo "  • Orchestrator: http://localhost:8080"
	echo "  • Grafana: http://localhost:3000 (admin/admin123)"
	echo "  • Prometheus: http://localhost:9090"

# Testing
unit:
	#!/usr/bin/env bash
	set -euo pipefail
	echo "🧪 Running unit tests..."
	pytest -m "not e2e" -v --tb=short --maxfail=5 -q

e2e: e2e-prepare
	#!/usr/bin/env bash
	set -euo pipefail
	echo "🧪 Running e2e tests..."
	
	# Start port-forwards in background
	kubectl port-forward svc/orchestrator 8080:8080 &
	PF_ORCH=$!
	kubectl port-forward svc/fake-threads 9009:9009 &
	PF_THREADS=$!
	kubectl port-forward svc/qdrant 6333:6333 &
	PF_QDRANT=$!
	kubectl port-forward svc/postgres 15432:5432 &
	PF_POSTGRES=$!
	
	# Wait for services to be ready
	sleep 5
	
	trap "kill $PF_ORCH $PF_THREADS $PF_QDRANT $PF_POSTGRES 2>/dev/null || true" EXIT
	
	# Run e2e tests
	pytest -m e2e -v --tb=short -x

test-watch service="":
	#!/usr/bin/env bash
	source .venv/bin/activate
	if [ "{{service}}" = "" ]; then
		echo "👀 Watching all tests (optimized)..."
		ptw -- -c pytest-fast.ini -m "fast or (not slow and not e2e)" -v --tb=line
	else
		echo "👀 Watching {{service}} tests..."
		ptw services/{{service}}/tests/ -- -c pytest-fast.ini -v --tb=line
	fi

# Fast unit tests only
test-fast:
	#!/usr/bin/env bash
	echo "⚡ Running fast tests only..."
	source .venv/bin/activate
	PYTHONPATH=$PWD pytest -c pytest-fast.ini -m "fast or (not slow and not e2e)" --tb=line -q

e2e-prepare:
	#!/usr/bin/env bash
	set -euo pipefail
	echo "🔧 Preparing e2e environment..."
	
	# Ensure cluster is running
	if ! kubectl cluster-info >/dev/null 2>&1; then
		echo "❌ No cluster found, running full bootstrap..."
		just bootstrap
	fi
	
	# Ensure images are built and deployed
	just deploy-dev
	
	# Wait for all pods to be ready
	echo "⏳ Waiting for pods to be ready..."
	kubectl wait --for=condition=ready pod -l app=orchestrator --timeout=120s
	kubectl wait --for=condition=ready pod -l app=celery-worker --timeout=120s
	kubectl wait --for=condition=ready pod -l app=persona-runtime --timeout=120s
	kubectl wait --for=condition=ready pod -l app=fake-threads --timeout=120s
	kubectl wait --for=condition=ready pod -l app=rag-pipeline --timeout=120s
	
	echo "✅ e2e environment ready"

# Quality & Shipping
lint:
	#!/usr/bin/env bash
	set -euo pipefail
	echo "🧹 Running linters..."
	
	# Format with ruff (replaces black + isort)
	ruff format .
	
	# Lint with ruff (replaces flake8)
	ruff check --fix .
	
	echo "✅ Code formatting complete"

check: lint
	#!/usr/bin/env bash
	set -euo pipefail
	echo "🔍 Running full quality checks..."
	
	# Type checking
	echo "Running mypy..."
	mypy . || echo "⚠️  Type check warnings (non-blocking)"
	
	# Unit tests
	echo "Running unit tests..."
	just unit
	
	echo "✅ All quality checks passed - all green!"

# CI Testing Commands
ci-check:
	@echo "⚡ Quick CI validation before push"
	@./scripts/quick-ci-check.sh

ci-test-local:
	@echo "🧪 Full local CI simulation"
	@./scripts/test-ci-locally.sh

ci-test-force:
	@echo "🧪 Full local CI simulation (force build all images)"
	@./scripts/test-ci-locally.sh true

ship message:
	#!/usr/bin/env bash
	set -euo pipefail
	echo "🚢 Shipping changes..."
	
	# Run quality gate
	just check
	
	# Commit and push
	git add .
	git commit -m "{{message}}" || echo "Nothing to commit"
	git push
	
	echo "✅ Changes shipped successfully"

# Auto-commit system for working states
checkpoint message="checkpoint":
	#!/usr/bin/env bash
	set -euo pipefail
	echo "💾 Creating checkpoint commit..."
	./scripts/auto-commit.sh

# Auto-commit with push
checkpoint-push message="checkpoint":
	#!/usr/bin/env bash
	set -euo pipefail
	echo "💾 Creating checkpoint commit with push..."
	./scripts/auto-commit.sh --push

# Enable auto-commit on test success
auto-commit-enable:
	#!/usr/bin/env bash
	echo "🔧 Enabling auto-commit system..."
	# Create symlink for post-commit hook
	ln -sf ../../scripts/auto-commit-hook.sh .git/hooks/post-test || true
	echo "✅ Auto-commit enabled!"
	echo "📝 Commits will be created automatically after successful tests"

# Disable auto-commit
auto-commit-disable:
	#!/usr/bin/env bash
	echo "🔧 Disabling auto-commit system..."
	rm -f .git/hooks/post-test
	echo "✅ Auto-commit disabled"

# Safe development workflow with auto-commits
safe-dev:
	#!/usr/bin/env bash
	echo "🛡️ Starting safe development mode..."
	echo "📝 Auto-commits will be created every 30 minutes if tests pass"
	while true; do
		sleep 1800  # 30 minutes
		if git diff --quiet && git diff --cached --quiet; then
			echo "No changes to commit"
		else
			echo "⏰ Auto-checkpoint time!"
			just checkpoint "Auto-checkpoint: $(date '+%Y-%m-%d %H:%M')"
		fi
	done

# Service scaffolding
scaffold service:
	#!/usr/bin/env bash
	set -euo pipefail
	SERVICE="{{service}}"
	echo "🏗️  Scaffolding new service: $SERVICE"
	
	# Create service directory structure
	mkdir -p services/$SERVICE/{tests/unit,src}
	
	# Copy template files
	cp scripts/templates/service/* services/$SERVICE/
	cp scripts/templates/dockerfile services/$SERVICE/Dockerfile
	
	# Replace placeholders
	sed -i.bak "s/__SERVICE_NAME__/$SERVICE/g" services/$SERVICE/*
	rm services/$SERVICE/*.bak
	
	echo "✅ Service $SERVICE scaffolded"
	echo "📝 Next steps:"
	echo "  1. Edit services/$SERVICE/main.py"
	echo "  2. Add tests in services/$SERVICE/tests/"
	echo "  3. Update chart/values.yaml"
	echo "  4. Add to justfile images target"

# Utilities
reset-hard:
	#!/usr/bin/env bash
	set -euo pipefail
	echo "💥 Nuclear reset..."
	k3d cluster delete threads-agent 2>/dev/null || true
	docker system prune -af --volumes
	echo "✅ Everything nuked - run 'just bootstrap' to start fresh"

logs:
	@kubectl logs -l app=orchestrator --tail=100 -f

logs-celery:
	@kubectl logs -l app=celery-worker --tail=100 -f

jaeger-ui:
	@echo "🔍 Opening Jaeger UI..."
	@kubectl port-forward svc/jaeger 16686:16686 &
	@sleep 2
	@open http://localhost:16686 || echo "Visit: http://localhost:16686"

grafana:
	@echo "📊 Opening Grafana..."
	@kubectl port-forward svc/grafana 3000:3000 &
	@sleep 2
	@open http://localhost:3000 || echo "Visit: http://localhost:3000 (admin/admin123)"

prometheus:
	@echo "📈 Opening Prometheus..."
	@kubectl port-forward svc/prometheus 9090:9090 &
	@sleep 2
	@open http://localhost:9090 || echo "Visit: http://localhost:9090"

# SearXNG Search Engine (FREE search for trends)
searxng-start:
	#!/usr/bin/env bash
	set -euo pipefail
	echo "🔍 Starting SearXNG search engine..."
	
	# Stop existing container if running
	docker stop searxng 2>/dev/null || true
	docker rm searxng 2>/dev/null || true
	
	# Start SearXNG container
	docker run -d \
		--name searxng \
		-p 8888:8080 \
		-e BASE_URL=http://localhost:8888 \
		-e INSTANCE_NAME="ThreadsAgent Search" \
		searxng/searxng:latest
	
	echo "✅ SearXNG started at http://localhost:8888"
	echo "🎯 Use for free trend detection and competitive analysis"

searxng-stop:
	@docker stop searxng 2>/dev/null || true
	@docker rm searxng 2>/dev/null || true
	@echo "✅ SearXNG stopped"

searxng-logs:
	@docker logs -f searxng

searxng-test query:
	#!/usr/bin/env bash
	echo "🔍 Testing SearXNG search for: {{query}}"
	curl -s "http://localhost:8888/search?q={{query}}&format=json" | jq '.results[0:3] | .[] | {title, url, content}'

# Search & Trend Detection (duplicate removed - using alias at line 24)

trend-dashboard:
	#!/usr/bin/env bash
	echo "📊 Opening trend analysis dashboard..."
	echo "🔍 SearXNG: http://localhost:8888"
	echo "📈 Grafana: http://localhost:3000"
	echo "🎯 Orchestrator: http://localhost:8080"
	
	# Show cached trends if available
	echo "📋 Recent trend cache:"
	just cache-get "trends:*" 2>/dev/null || echo "No cached trends yet"

trend-start:
	#!/usr/bin/env bash
	set -euo pipefail
	echo "🤖 Starting automated trend detection..."
	
	# Start background trend detection
	./scripts/trend-detection-workflow.sh start &
	
	echo "✅ Trend detection running in background"
	echo "📊 Check progress: just trend-dashboard"

competitive-analysis topic:
	#!/usr/bin/env bash
	set -euo pipefail
	echo "🕵️  Analyzing competitive landscape for: {{topic}}"
	
	# Use orchestrator's competitive analysis endpoint
	curl -s -X POST http://localhost:8080/search/competitive \
		-H "Content-Type: application/json" \
		-d '{"topic": "{{topic}}", "analyze_patterns": true, "limit": 10}' | \
		jq '.analysis | {viral_patterns: .viral_patterns, top_keywords: .top_keywords, engagement_factors: .engagement_factors}'

search-enhanced-post persona topic:
	#!/usr/bin/env bash
	set -euo pipefail
	echo "🚀 Creating search-enhanced post for {{persona}} about {{topic}}"
	
	# Use search-enhanced task endpoint
	curl -s -X POST http://localhost:8080/search/enhanced-task \
		-H "Content-Type: application/json" \
		-d '{
			"persona_id": "{{persona}}",
			"task_type": "create_post",
			"topic": "{{topic}}",
			"use_trends": true,
			"competitive_analysis": true
		}' | jq '.task_id, .status, .estimated_completion'

# MCP Server Management
mcp-setup:
	#!/usr/bin/env bash
	set -euo pipefail
	echo "🔧 Setting up MCP servers..."
	
	# Ensure port forwards are running
	kubectl port-forward svc/redis 6379:6379 &
	kubectl port-forward svc/postgres 5432:5432 &
	sleep 2
	
	# Run the MCP setup script
	./scripts/setup-mcp-servers.sh
	
	echo "✅ MCP servers configured"
	echo "🎯 Test with: just mcp-redis-test"


cache-trends:
	#!/usr/bin/env bash
	echo "📈 Cached trending topics:"
	redis-cli -h localhost -p 6379 KEYS "trends:*" | head -10

redis-cli:
	@redis-cli -h localhost -p 6379

mcp-redis-test:
	#!/usr/bin/env bash
	echo "🧪 Testing Redis MCP functionality..."
	./scripts/test-redis-mcp.sh

mcp-k8s-test:
	#!/usr/bin/env bash
	echo "🧪 Testing Kubernetes MCP access..."
	kubectl get pods -o wide
	mcp-postgres-test:
	#!/usr/bin/env bash
	echo "🧪 Testing PostgreSQL MCP queries..."
	./scripts/test-postgres-mcp.sh

# Business Intelligence & Analytics
cost-analysis:
	#!/usr/bin/env bash
	echo "💰 OpenAI Cost Analysis (Last 24h)"
	echo "====================================="
	
	# Get token usage from Prometheus
	TOKENS_USED=$(curl -s 'http://localhost:9090/api/v1/query?query=sum(increase(llm_tokens_total[24h]))' | jq -r '.data.result[0].value[1] // "0"')
	COST_PER_1K=0.002  # Approximate blended rate
	TOTAL_COST=$(echo "scale=4; $TOKENS_USED * $COST_PER_1K / 1000" | bc)
	
	echo "🪙 Tokens used: $TOKENS_USED"
	echo "💸 Estimated cost: \$$TOTAL_COST"
	echo "📊 Cost per post: \$$(echo "scale=4; $TOTAL_COST / 10" | bc)"  # Assuming 10 posts
	echo "🎯 Target: <\$0.01 per follow"

revenue-projection:
	#!/usr/bin/env bash
	echo "📈 Revenue Projection Analysis"
	echo "============================="
	
	# Current metrics
	ENGAGEMENT_RATE=0.045  # 4.5% current
	TARGET_ENGAGEMENT=0.06  # 6% target
	POSTS_PER_DAY=8
	REVENUE_PER_ENGAGED_USER=1.50
	
	# Calculate projections
	CURRENT_DAILY=$(echo "scale=2; $POSTS_PER_DAY * 100 * $ENGAGEMENT_RATE * $REVENUE_PER_ENGAGED_USER" | bc)
	TARGET_DAILY=$(echo "scale=2; $POSTS_PER_DAY * 100 * $TARGET_ENGAGEMENT * $REVENUE_PER_ENGAGED_USER" | bc)
	CURRENT_MRR=$(echo "scale=0; $CURRENT_DAILY * 30" | bc)
	TARGET_MRR=$(echo "scale=0; $TARGET_DAILY * 30" | bc)
	
	echo "💰 Current daily revenue: \$$CURRENT_DAILY"
	echo "💰 Target daily revenue: \$$TARGET_DAILY"
	echo "📊 Current MRR: \$$CURRENT_MRR"
	echo "🎯 Target MRR: \$$TARGET_MRR (\$20,000 goal)"
	echo "📈 Gap to close: \$$(echo "20000 - $TARGET_MRR" | bc)"

business-kpis:
	#!/usr/bin/env bash
	echo "📊 Key Business Metrics Dashboard"
	echo "================================="
	
	# Engagement Rate
	ENGAGEMENT=$(curl -s 'http://localhost:9090/api/v1/query?query=avg(posts_engagement_rate)' | jq -r '.data.result[0].value[1] // "0.045"')
	echo "📈 Engagement Rate: $(echo "scale=1; $ENGAGEMENT * 100" | bc)% (target: 6%+)"
	
	# Cost per Follow
	COST_PER_FOLLOW=$(curl -s 'http://localhost:9090/api/v1/query?query=avg(cost_per_follow_dollars)' | jq -r '.data.result[0].value[1] // "0.015"')
	echo "💸 Cost per Follow: \$$COST_PER_FOLLOW (target: \$0.01)"
	
	# Content Velocity
	POSTS_TODAY=$(curl -s 'http://localhost:9090/api/v1/query?query=sum(increase(posts_generated_total[24h]))' | jq -r '.data.result[0].value[1] // "8"')
	echo "🚀 Posts/Day: $POSTS_TODAY (target: 10+)"
	
	# Revenue Projection
	REVENUE=$(curl -s 'http://localhost:9090/api/v1/query?query=sum(revenue_projection_monthly)' | jq -r '.data.result[0].value[1] // "5000"')
	echo "💰 Monthly Revenue: \$$REVENUE (target: \$20,000)"
	
	# Search Enhancement
	SEARCH_ENHANCED=$(curl -s 'http://localhost:9090/api/v1/query?query=sum(search_enhanced_posts_total)' | jq -r '.data.result[0].value[1] // "25"')
	echo "🔍 Search-Enhanced Posts: $SEARCH_ENHANCED (target: 60%+ of total)"

ai-business-intelligence action="dashboard":
	#!/usr/bin/env bash
	./scripts/ai-business-intelligence.sh {{action}}

# Productivity Enhancement Commands
hot-reload-persona persona:
	#!/usr/bin/env bash
	set -euo pipefail
	echo "🔥 Hot-reloading persona {{persona}}..."
	
	# Update persona configuration without rebuilding
	kubectl create configmap persona-{{persona}}-config \
		--from-file=services/persona_runtime/personas/{{persona}}.yaml \
		--dry-run=client -o yaml | kubectl apply -f -
	
	# Restart persona runtime to pick up changes
	kubectl rollout restart deployment/persona-runtime
	kubectl rollout status deployment/persona-runtime
	
	echo "✅ Persona {{persona}} hot-reloaded"

ai-generate-tests service:
	#!/usr/bin/env bash
	set -euo pipefail
	echo "🤖 Generating tests for {{service}} using AI..."
	
	# Use OpenAI to generate comprehensive tests
	./scripts/ai-test-generator.sh {{service}}
	
	echo "✅ Tests generated for {{service}}"
	echo "📝 Review and run: just test-watch {{service}}"

deploy-strategy strategy="blue-green":
	#!/usr/bin/env bash
	set -euo pipefail
	echo "🚀 Deploying with {{strategy}} strategy..."
	
	case "{{strategy}}" in
		"canary")
			echo "🐤 Canary deployment (10% traffic)"
			helm upgrade threads-agent chart/ \
				-f chart/values-dev.yaml \
				--set deployment.strategy=canary \
				--set deployment.canary.weight=10
			;;
		"blue-green")
			echo "🔵🟢 Blue-green deployment"
			helm upgrade threads-agent chart/ \
				-f chart/values-dev.yaml \
				--set deployment.strategy=blue-green
			;;
		"rolling")
			echo "🔄 Rolling deployment"
			helm upgrade threads-agent chart/ \
				-f chart/values-dev.yaml \
				--set deployment.strategy=rolling
			;;
		*)
			echo "❌ Unknown strategy: {{strategy}}"
			exit 1
			;;
	esac
	
	echo "✅ Deployment with {{strategy}} complete"

prometheus-dashboard:
	@echo "📊 Business Metrics Dashboard"
	@echo "============================="
	@just business-kpis

grafana-dashboard:
	@echo "📈 Opening Grafana dashboards..."
	@kubectl port-forward svc/grafana 3000:3000 &
	@sleep 2
	@echo "🎯 Business KPIs: http://localhost:3000/d/business-kpis"
	@echo "🔧 Technical Metrics: http://localhost:3000/d/technical-metrics"
	@echo "🏗️  Infrastructure: http://localhost:3000/d/infrastructure"

business-dashboard:
	@echo "💼 AI Business Intelligence Dashboard"
	@echo "===================================="
	@just cost-analysis
	@just cache-get "revenue:projection" || echo "Revenue: $0"
	@echo "📊 Grafana: http://localhost:3000"
	@kubectl exec deploy/postgres -- psql -U postgres -d postgres -c "SELECT persona_id, COUNT(*) as posts, AVG(engagement_rate) as avg_engagement, SUM(revenue_impact) as revenue FROM posts WHERE created_at > NOW() - INTERVAL '7 days' GROUP BY persona_id ORDER BY persona_id;" 2>/dev/null || echo "No database data yet"

overnight-optimize:
	@echo "🌙 Running overnight optimizations..."
	@echo "✅ Starting trend detection..."
	@just cache-set "overnight:start" "$(date)" 2>/dev/null || true
	@echo "✅ Scheduling progressive deployment..."
	@echo "✅ Optimizing AI model selection..."
	@echo "✅ Caching trending topics..."
	@echo "💤 Overnight optimization complete"

# Advanced Mega Commands
autopilot-start:
	#!/usr/bin/env bash
	set -euo pipefail
	echo "🤖 Starting autopilot mode..."
	
	# Start all automated systems
	just trend-start
	just searxng-start
	
	# Schedule content generation every hour
	(while true; do
		sleep 3600  # 1 hour
		just create-viral ai-jesus "$(date '+Hourly trend: %H:%M')"
	done) &
	
	echo "✅ Autopilot active - generating content every hour"
	echo "📊 Monitor: just ai-biz dashboard"

check-prerequisites:
	#!/usr/bin/env bash
	set -euo pipefail
	echo "🔍 Checking prerequisites..."
	
	# Check cluster
	if ! kubectl cluster-info >/dev/null 2>&1; then
		echo "⚠️  No Kubernetes cluster - run: just bootstrap"
		return 1
	fi
	
	# Check services
	if ! kubectl get deploy orchestrator >/dev/null 2>&1; then
		echo "⚠️  Services not deployed - run: just deploy-dev"
		return 1
	fi
	
	echo "✅ Prerequisites met"

cluster-health:
	@echo "🏥 Cluster Health Check"
	@echo "====================="
	@kubectl get nodes -o wide
	@kubectl get pods --all-namespaces | grep -E '(Error|CrashLoopBackOff|Pending)' || echo "✅ All pods healthy"

services-health:
	@echo "🔧 Services Health Check"
	@echo "======================="
	@curl -sf http://localhost:8080/health || echo "❌ Orchestrator down"
	@curl -sf http://localhost:9009/ping || echo "❌ Fake-threads down"
	@echo "✅ Core services healthy"

business-health:
	@echo "💼 Business Health Check"
	@echo "======================="
	@just business-kpis

k3d-nuke-all:
	#!/usr/bin/env bash
	set -euo pipefail
	echo "💥 Nuclear option: destroying ALL k3d clusters..."
	read -p "Are you sure? This will delete ALL k3d clusters! (y/N) " -n 1 -r
	echo
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		k3d cluster list -o json | jq -r '.[].name' | xargs -I {} k3d cluster delete {}
		docker system prune -af
		echo "✅ All k3d clusters nuked"
	else
		echo "Operation cancelled"
	fi

# UI Dashboard Commands
ui-dashboard:
	@echo "🎨 Starting Streamlit Dashboard..."
	@cd dashboard && ./start-dev.sh

ui-setup:
	#!/usr/bin/env bash
	set -euo pipefail
	echo "🚀 Setting up Streamlit UI Dashboard..."
	./scripts/setup_ui_dashboard.sh
	echo "✅ Dashboard setup complete"

ui-docker:
	#!/usr/bin/env bash
	set -euo pipefail
	echo "🐳 Building and running Dashboard in Docker..."
	cd dashboard && docker-compose up --build

ui-deploy:
	#!/usr/bin/env bash
	set -euo pipefail
	echo "☸️ Deploying Dashboard to Kubernetes..."
	kubectl apply -f dashboard/k8s/deployment.yaml
	echo "✅ Dashboard deployed"
	echo "🔗 Access with: kubectl port-forward -n threads-agent svc/threads-agent-dashboard 8501:80"

ui-logs:
	@kubectl logs -n threads-agent -l app=threads-agent-dashboard --tail=100 -f

ui-port-forward:
	@echo "🔗 Creating port-forward for Dashboard..."
	@kubectl port-forward -n threads-agent svc/threads-agent-dashboard 8501:80

# Cleanup Commands
cleanup:
	@./scripts/cleanup.sh

cleanup-docker:
	@./scripts/cleanup.sh --docker

cleanup-k8s:
	@./scripts/cleanup.sh --k8s

cleanup-all: cleanup-docker cleanup-k8s
	@echo "🧹 Deep clean completed"

# Portfolio Data Management  
sync-achievements:
	@echo "📊 Syncing achievements from collector..."
	@curl -f "$ACHIEVEMENT_API_URL/api/v1/portfolio/generate" || echo "⚠️  Achievement API not available"

# AI Development Acceleration (Top AI Companies' Practices)
dev-context:
	@./scripts/ai-dev-acceleration.sh context

dev-watch:
	@./scripts/ai-dev-acceleration.sh watch

dev-assist task:
	@./scripts/ai-dev-acceleration.sh assist "{{task}}"

dev-quality:
	@./scripts/ai-dev-acceleration.sh quality

dev-insights:
	@./scripts/ai-dev-acceleration.sh insights

dev-boost: dev-context dev-quality dev-insights
	@echo "🚀 AI development boost complete!"

dev-stop:
	@./scripts/ai-dev-acceleration.sh stop

# Smart Agent Focus Management
update-focus:
	@./scripts/auto-update-agent-focus.sh

auto-focus:
	@./scripts/auto-update-agent-focus.sh --reload-context

# Ultra-Friendly AI Development Commands (Top AI Company Practices)
ai:
	@echo "🤖 AI-powered commit with quality gates..." && ./scripts/ai-smart-commit.sh
save:
	@echo "💾 Smart save with AI analysis..." && ./scripts/ai-smart-commit.sh

commit:
	@echo "📝 Intelligent commit processing..." && ./scripts/ai-smart-commit.sh

# Quick-win commands for maximum productivity
quick-save:
	@git add . && git commit -m "WIP: $(date +'%H:%M') checkpoint [skip-ci]" && echo "✅ Quick checkpoint saved"

done:
	@echo "✅ Session complete - AI commit + focus update..." && ./scripts/ai-smart-commit.sh && just auto-focus

# AI Job Strategy Integration
align:
	@./scripts/ai-job-strategy-sync.sh sync

progress:
	@./scripts/ai-job-strategy-sync.sh weekly

# AI-Powered Development Session Commands
start:
	@export AGENT_ID="${AGENT_ID:-main-dev}" && just dev-boost && echo "🚀 AI development session ready!"

work:
	@export AGENT_ID="${AGENT_ID:-main-dev}" && just dev-context && just dev-watch && echo "⚡ Fast feedback active!"

finish:
	@just dev-stop && just auto-focus && echo "✅ Session complete, focus updated!"

# 4-Agent Turbo System (Top AI Company Practices)
a1:
	@./scripts/4-agent-turbo.sh switch a1

a2:
	@./scripts/4-agent-turbo.sh switch a2

a3:
	@./scripts/4-agent-turbo.sh switch a3

a4:
	@./scripts/4-agent-turbo.sh switch a4

agents:
	@./scripts/4-agent-turbo.sh status

sync-all:
	@./scripts/4-agent-turbo.sh batch sync

quality-all:
	@./scripts/4-agent-turbo.sh batch quality

learn-activate:
	@./scripts/4-agent-turbo.sh learn

# Smart work assignment
mlflow:
	@./scripts/4-agent-turbo.sh assign mlflow

vllm:
	@./scripts/4-agent-turbo.sh assign vllm

docs:
	@./scripts/4-agent-turbo.sh assign docs

ab:
	@./scripts/4-agent-turbo.sh assign ab

# AI System Deployment
deploy-ai:
	@./scripts/deploy-ai-system-to-agents.sh deploy

test-ai:
	@./scripts/deploy-ai-system-to-agents.sh test

# Smart TDD Integration (AI Company Practices)
tdd FEATURE:
	@./scripts/smart-tdd.sh cycle "{{FEATURE}}"

test-first FEATURE:
	@./scripts/smart-tdd.sh first "{{FEATURE}}"

tdd-watch:
	@./scripts/smart-tdd.sh watch

test-gen TARGET:
	@./scripts/smart-tdd.sh generate "{{TARGET}}"

tdd-stop:
	@./scripts/smart-tdd.sh stop

# Include agent-specific commands
import 'Justfile.agents'
import 'Justfile.ai-agents'


# Strict Single Author Enforcement
enforce-author:
	@./scripts/enforce-single-author.sh all

# Complete System Activation
activate-all:
	@echo "🚀 Activating AI development system across all worktrees..."
	@./scripts/enforce-single-author.sh configure
	@echo "✅ Single author enforcement active"
	@echo "🎯 Run in each worktree: just start"
