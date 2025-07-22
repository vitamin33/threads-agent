# =========================================
#  Threads-Agent – Dev helper recipes
# =========================================
set dotenv-load

# ---------- K8s Dev Platform ----------
bootstrap:          # spin local k3d
    ./scripts/dev-up.sh


# -----------------------------------------------------------------
# single helper that builds + pre-pulls all images, then loads
# everything (including Postgres & RabbitMQ) into the k3d cluster
# -----------------------------------------------------------------
images:
	@echo "🐳  building dev images …"

	for svc in orchestrator celery_worker persona_runtime fake_threads viral_engine; do \
		docker build -f services/${svc}/Dockerfile -t ${svc//_/-}:local .; \
	done

	docker pull bitnami/postgresql:16
	docker pull rabbitmq:3.13-management-alpine

	# ---------- Qdrant ----------
	docker pull qdrant/qdrant:v1.9.4
	k3d image import qdrant/qdrant:v1.9.4 -c dev

	for img in orchestrator celery-worker persona-runtime fake-threads viral-engine; do \
		k3d image import ${img}:local -c dev; \
	done

	@echo "🔍  images inside k3d nodes:"
	docker exec k3d-dev-agent-0 crictl images | grep -E 'orchestrator|celery|persona|fake|viral'

deploy-dev TIMEOUT="360s":
	@bash -ceu 'extra=""; [ -f chart/values-dev.local.yaml ] && extra="-f chart/values-dev.local.yaml"; \
	            helm upgrade --install threads ./chart -f chart/values-dev.yaml $extra \
	            --wait --timeout {{TIMEOUT}}'

k3d-stop-all:
	k3d cluster stop --all

k3d-nuke-all:
	k3d cluster delete --all

docker-cache-clear:
    @echo "🧹  pruning buildx cache …"
    docker builder prune -af

# full reset: cluster + cache
reset-hard:
    just k3d-nuke-all
    just docker-cache-clear

# ---------- Local e2e run ----------
e2e-prepare:          # full e2e setup: bootstrap + images + deploy + test
    @echo "🚀  setting up complete e2e environment..."
    just bootstrap
    just images  
    just deploy-dev
    @echo "⏳  waiting for services to be ready..."
    kubectl wait --for=condition=ready pod -l app=postgres --timeout=300s
    kubectl wait --for=condition=ready pod -l app=orchestrator --timeout=300s
    @echo "✅  e2e environment ready!"

e2e:
    @echo "🧪  running e2e tests (with automatic service checks)..."
    PYTHONPATH=$PWD:${PYTHONPATH:-} pytest -s -m e2e

# ---------- Unit-only test run ----------
unit:
    PYTHONPATH=$PWD:${PYTHONPATH:-} pytest -q -m "not e2e"

logs:
    kubectl logs -l app=orchestrator -f --tail=100

logs-celery:
	kubectl logs -f deploy/celery-worker

test-watch SERVICE="":
	@echo "🔁  watching tests…"
	@if [ "$(SERVICE)" != "" ]; then \
	    pt="services/$(SERVICE)"; \
	else \
	    pt="."; \
	fi; \
	pytest $$pt --maxfail=1 -q -f

scaffold SERVICE:
    mkdir -p services/{{SERVICE}}
    cp -r templates/service-template/* services/{{SERVICE}}/

    # replace in main.py
    sed -i '' "s/TEMPLATE_NAME/{{SERVICE}}/g" services/{{SERVICE}}/main.py

    # replace in test
    sed -i '' "s/TEMPLATE_NAME/{{SERVICE}}/g" services/{{SERVICE}}/tests/test_health.py

# ---------- Lint / Type-check / Tests ----------
lint:
	@echo "⚙  ruff (lint+format) → isort → black"
	@if [ -f .venv/bin/activate ]; then source .venv/bin/activate; fi && \
	ruff check --fix . && \
	ruff format . && \
	isort . --profile black --filter-files && \
	black .
	@./scripts/learning-system.sh track "just lint" 0 "1.0" "auto-format" 2>/dev/null || true

check: lint
	@echo "🔍  mypy type-check"
	@if [ -f .venv/bin/activate ]; then source .venv/bin/activate; fi && mypy --config-file mypy.ini .
	@echo "🧪  pytest suite"
	@if [ -f .venv/bin/activate ]; then source .venv/bin/activate; fi && PYTHONPATH=$PWD:${PYTHONPATH:-} pytest -q
	@echo "✅  all green"
	@./scripts/learning-system.sh track "just check" 0 "5.0" "full-check" 2>/dev/null || true

# ---------- Quality Gates ----------
quality-gate PHASE="pre-commit": # run quality gates system
	./scripts/quality-gates.sh {{PHASE}}

pre-commit-check: # lightweight pre-commit quality gates
	just lint
	./scripts/quality-gates.sh pre-commit

pre-commit-fix: # auto-fix issues then run pre-commit gates
	just lint
	@SKIP_FORMAT_CHECK=true SKIP_CLAUDE_REVIEW=true ./scripts/quality-gates.sh pre-commit

pre-deploy-check: # comprehensive pre-deploy quality gates  
	./scripts/quality-gates.sh pre-deploy

claude-review: # run Claude Code automated review
	./scripts/quality-gates.sh claude-review

security-check: # run security-focused quality checks
	./scripts/quality-gates.sh security

# ---------- Learning System ----------
learn ACTION="dashboard": # intelligent development learning and optimization
	./scripts/learning-system.sh {{ACTION}}

analyze-patterns: # analyze development patterns and suggest optimizations
	./scripts/learning-system.sh analyze && ./scripts/learning-system.sh suggest

learning-dashboard: # show interactive learning dashboard
	./scripts/learning-system.sh dashboard

learning-report: # generate comprehensive learning report
	./scripts/learning-system.sh report

benchmark-performance: # benchmark development operations
	./scripts/learning-system.sh benchmark

# ---------- Advanced Workflow Automation ----------
workflow ACTION="dashboard": # advanced workflow automation system
	./scripts/workflow-automation.sh {{ACTION}}

epic NAME DESCRIPTION="": # break down epic into features  
	./scripts/workflow-automation.sh epic "{{NAME}}" "{{DESCRIPTION}}"

feature ACTION ID: # manage feature lifecycle
	./scripts/workflow-automation.sh feature {{ACTION}} {{ID}}

orchestrate MODE="suggest": # intelligent development orchestration
	./scripts/workflow-automation.sh orchestrate {{MODE}}

workflow-dashboard: # show workflow automation dashboard
	./scripts/workflow-automation.sh dashboard

workflow-report: # generate workflow automation report
	./scripts/workflow-automation.sh report

# ---------- Solopreneur Morning Routine ----------
business-morning: # comprehensive morning briefing for solopreneurs
	@echo "🌅 Good Morning! Starting your business briefing..."
	@echo "==============================================="
	@echo ""
	@echo "📊 CUSTOMER INTELLIGENCE OVERVIEW"
	@echo "-----------------------------------"
	@just ci-dashboard
	@echo ""
	@echo "💰 BUSINESS INTELLIGENCE SUMMARY" 
	@echo "--------------------------------"
	@just bi-dashboard
	@echo ""
	@echo "🧠 DEVELOPMENT INSIGHTS"
	@echo "----------------------"
	@just learning-dashboard
	@echo ""
	@echo "📈 DAILY ACTION ITEMS"
	@echo "--------------------"
	@just daily-insights
	@echo ""
	@echo "✨ Morning briefing complete! Have a productive day! ✨"

business-evening: # enhanced customer-focused end-of-day review
	./scripts/customer-priority.sh enhanced-evening customer_centric

# Level 8A Customer Priority Commands
next-customer-priority FOCUS="all": # AI-powered next customer priority recommendation
	./scripts/customer-priority.sh next-priority {{FOCUS}}

code-for-retention FOCUS="engagement": # analyze retention-focused development opportunities
	./scripts/customer-priority.sh code-for-retention {{FOCUS}}

weekly-strategic-review FOCUS="comprehensive": # generate comprehensive weekly strategic review
	./scripts/customer-priority.sh weekly-strategic-review {{FOCUS}}

business-weekly: # enhanced weekly business review with strategic analysis
	./scripts/customer-priority.sh weekly-strategic-review comprehensive

# ---------- Customer Intelligence System ----------
ci ACTION="dashboard": # solopreneur customer intelligence system
	./scripts/customer-intelligence.sh {{ACTION}}

track-behavior USER ACTION PAGE="home" DURATION="0": # track user behavior event
	./scripts/customer-intelligence.sh track-behavior {{USER}} {{ACTION}} {{PAGE}} {{DURATION}}

pmf-survey USER DISAPPOINTED NPS BENEFIT IMPROVEMENT: # record PMF survey response
	./scripts/customer-intelligence.sh pmf-survey {{USER}} {{DISAPPOINTED}} {{NPS}} "{{BENEFIT}}" "{{IMPROVEMENT}}"

add-competitor NAME WEBSITE="" SOCIAL="" FOCUS="general": # add competitor to monitoring
	./scripts/customer-intelligence.sh add-competitor "{{NAME}}" "{{WEBSITE}}" "{{SOCIAL}}" {{FOCUS}}

competitor-update NAME TYPE DESCRIPTION IMPACT="medium" SOURCE="manual": # track competitor update
	./scripts/customer-intelligence.sh competitor-update "{{NAME}}" {{TYPE}} "{{DESCRIPTION}}" {{IMPACT}} {{SOURCE}}

ci-dashboard: # show customer intelligence dashboard
	./scripts/customer-intelligence.sh dashboard

ci-report TYPE="weekly": # generate customer intelligence report
	./scripts/customer-intelligence.sh report {{TYPE}}

daily-insights: # generate automated daily insights
	./scripts/customer-intelligence.sh daily-insights

setup-ci-automation: # configure automated CI tasks
	./scripts/customer-intelligence.sh setup-automation

# ---------- Business Intelligence System ----------
bi ACTION="dashboard": # solopreneur business intelligence system
	./scripts/business-intelligence.sh {{ACTION}}

roi-calculator FEATURE HOURS="40" RATE="150" REVENUE="0" IMPACT="medium": # calculate feature ROI
	./scripts/business-intelligence.sh roi "{{FEATURE}}" {{HOURS}} {{RATE}} {{REVENUE}} {{IMPACT}}

market-timing FEATURE TREND="stable" COMPETITION="none" SEASONAL="neutral": # analyze market timing
	./scripts/business-intelligence.sh market "{{FEATURE}}" {{TREND}} {{COMPETITION}} {{SEASONAL}}

revenue-predictor FEATURE ACQUISITION="10" RETENTION="5" ELASTICITY="medium" WEEKS="4": # predict revenue impact
	./scripts/business-intelligence.sh revenue "{{FEATURE}}" {{ACQUISITION}} {{RETENTION}} {{ELASTICITY}} {{WEEKS}}

compare-features FEATURE1 FEATURE2: # compare two features for ROI and impact
	./scripts/business-intelligence.sh compare "{{FEATURE1}}" "{{FEATURE2}}"

customer-feedback FEATURE SEGMENT SENTIMENT TEXT PAY="0": # add customer validation feedback
	./scripts/business-intelligence.sh feedback "{{FEATURE}}" "{{SEGMENT}}" "{{SENTIMENT}}" "{{TEXT}}" {{PAY}}

bi-dashboard: # show business intelligence dashboard
	./scripts/business-intelligence.sh dashboard

bi-report TYPE="weekly": # generate executive report
	./scripts/business-intelligence.sh report {{TYPE}}

# ---------- Unified Command Center (Level 9) ----------
command-center ACTION="dashboard": # unified command center integrating all 7 systems
	./scripts/command-center.sh {{ACTION}}

cc ACTION="dashboard": # unified command center integrating all 7 systems
	./scripts/cc-working.sh {{ACTION}}

cc-generate: # generate new prioritized action plan
	./scripts/cc-working.sh generate

cc-review: # review current action plan in JSON format
	./scripts/cc-working.sh review

cc-feedback ACTION_ID OUTCOME IMPACT="75": # track decision feedback and outcomes
	@echo "Feedback tracking: Action {{ACTION_ID}} -> {{OUTCOME}} (Impact: {{IMPACT}}/100)"
	@echo "This helps improve future recommendations and KPI accuracy"

# ---------- Universal Plan Memory System ----------
memory ACTION="analyze": # universal development plan memory with deep code-context awareness
	./scripts/plan-memory.sh {{ACTION}}

memory-analyze: # deep codebase analysis and pattern recognition
	./scripts/plan-memory.sh analyze

memory-epic NAME AREA="general": # generate context-aware epic
	./scripts/plan-memory.sh epic "{{NAME}}" {{AREA}}

memory-plan GOAL TIMEFRAME="medium": # generate intelligent development plan
	./scripts/plan-memory.sh plan "{{GOAL}}" {{TIMEFRAME}}

memory-opportunities: # show identified development opportunities
	./scripts/plan-memory.sh opportunities

memory-dashboard: # show plan memory system dashboard
	./scripts/plan-memory.sh dashboard

memory-report: # generate comprehensive memory analysis report
	./scripts/plan-memory.sh report

memory-sync: # sync memory system with workflow and learning systems
	./scripts/plan-memory.sh sync

# ---------- Claude Code Session Management ----------
claude-start TASK="general development": # start new Claude session with tracking
	./scripts/claude-session-tracker.sh start
	@echo "📝 Claude session started for: {{TASK}}"
	@echo "Use 'just claude-end' when session is complete"

claude-end SUMMARY="Claude Code session completed": # end Claude session and auto-commit
	./scripts/claude-session-tracker.sh end "{{SUMMARY}}"

claude-status: # show current Claude session status
	./scripts/claude-session-tracker.sh status

claude-sessions LIMIT="10": # list recent Claude sessions
	./scripts/claude-session-tracker.sh list {{LIMIT}}

claude-ship SUMMARY="Claude Code changes": # quick commit current Claude session changes
	@echo "🚀 Committing Claude Code session changes..."
	./scripts/claude-session-tracker.sh end "{{SUMMARY}}"

claude-watch-start: # start automatic file watcher for Claude sessions
	./scripts/claude-file-watcher.sh start

claude-watch-stop: # stop automatic file watcher
	./scripts/claude-file-watcher.sh stop

claude-watch-status: # check file watcher status
	./scripts/claude-file-watcher.sh status

# ---------- CI-green commit ➜ push ➜ PR ----------
# Usage:
#   just ship "feat: awesome (CRA-123)"
#   just ship "wip: spike" NO_PR=true
ship MESSAGE NO_PR="false":
    just pre-commit-fix
    just check
    pre-commit run --all-files
    git add -A
    git commit -m "{{MESSAGE}}" --no-verify
    @bash -ceu 'br=$(git branch --show-current); echo "▶ push → $br"; git push -u origin "$br"'
    @if [ "{{NO_PR}}" != "true" ] && command -v gh >/dev/null; then \
        echo "▶ open PR..."; gh pr create --fill --web || true; \
    else echo "ℹ︎  skip PR"; fi
    @./scripts/learning-system.sh workflow "ship-workflow" "pre-commit-fix,check,commit,push,pr" true "30.0" 2>/dev/null || true

# ---------- Context Management ----------
ctx-save NAME:      # save current session context
    ./scripts/smart-queries.sh save-ctx {{NAME}}

ctx-load NAME:      # load saved session context
    ./scripts/smart-queries.sh load-ctx {{NAME}}

ctx-show:           # show current session context
    ./scripts/smart-queries.sh show-ctx

ctx-list:           # list all saved contexts
    ./scripts/smart-queries.sh list-ctx

ctx-clean DAYS="7": # clean old contexts (default: 7 days)
    ./scripts/smart-queries.sh clean-ctx {{DAYS}}

# session continuity aliases
save NAME: # alias for ctx-save
    just ctx-save {{NAME}}

load NAME: # alias for ctx-load
    just ctx-load {{NAME}}

context: ctx-show   # alias for ctx-show

# ---------- Predictive Development ----------
health:             # infrastructure health check
    ./scripts/efficient-dev.sh health

predict:            # predictive development suggestions
    ./scripts/efficient-dev.sh predict

smart:              # comprehensive health + predictions
    ./scripts/efficient-dev.sh smart

dev-status: smart   # alias for smart

# ---------- Utilities ----------
jaeger-ui:          # open Jaeger in browser (mac)
    open http://localhost:16686 || true

build-runtime:
    docker build -f services/persona_runtime/Dockerfile \
      -t ghcr.io/threads-agent-stack/persona-runtime:${TAG:-0.3.0} .

push-runtime:
    docker push ghcr.io/threads-agent-stack/persona-runtime:${TAG:-0.3.0}

dev-runtime: build-runtime push-runtime

default: unit
