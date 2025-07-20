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

	for svc in orchestrator celery_worker persona_runtime fake_threads; do \
		docker build -f services/${svc}/Dockerfile -t ${svc//_/-}:local .; \
	done

	docker pull bitnami/postgresql:16
	docker pull rabbitmq:3.13-management-alpine

	# ---------- Qdrant ----------
	docker pull qdrant/qdrant:v1.9.4
	k3d image import qdrant/qdrant:v1.9.4 -c dev

	for img in orchestrator celery-worker persona-runtime fake-threads; do \
		k3d image import ${img}:local -c dev; \
	done

	@echo "🔍  images inside k3d nodes:"
	docker exec k3d-dev-agent-0 crictl images | grep -E 'orchestrator|celery|persona|fake'

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
e2e-prepare:
    just bootstrap
    just images
    just deploy-dev

e2e:
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
