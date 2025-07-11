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

	for img in orchestrator celery-worker persona-runtime fake-threads; do \
		k3d image import ${img}:local -c dev; \
	done

	@echo "🔍  images inside k3d nodes:"
	docker exec k3d-dev-agent-0 crictl images | grep -E 'orchestrator|celery|persona|fake'

deploy-fast TIMEOUT="360s":
    helm upgrade --install threads ./chart \
         -f chart/values-dev.yaml \
         --wait --timeout {{TIMEOUT}}

k3d-stop-all:
	k3d cluster stop --all

k3d-nuke-all:
	k3d cluster delete --all

# ---------- Local e2e run ----------
e2e-prepare:
    just bootstrap
    just images
    just deploy-fast

e2e:
    pytest -s -m e2e

# ---------- Unit-only test run ----------
unit:
    pytest -q -m "not e2e"

logs:               # follow pod logs
    kubectl logs -l app=orchestrator -f --tail=100

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
	ruff check --fix .
	ruff format .
	isort . --profile black --filter-files
	black .

check: lint
	@echo "🔍  mypy type-check"
	mypy services scripts
	@echo "🧪  pytest suite"
	pytest -q
	@echo "✅  all green"

# ---------- CI-green commit ➜ push ➜ PR ----------
# Usage:
#   just ship "feat: awesome (CRA-123)"
#   just ship "wip: spike" NO_PR=true
ship MESSAGE NO_PR="false":
    just check
    pre-commit run --all-files
    git add -A
    git commit -m "{{MESSAGE}}" --no-verify
    @bash -ceu 'br=$(git branch --show-current); echo "▶ push → $br"; git push -u origin "$br"'
    @if [ "{{NO_PR}}" != "true" ] && command -v gh >/dev/null; then \
        echo "▶ open PR..."; gh pr create --fill --web || true; \
    else echo "ℹ︎  skip PR"; fi

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
