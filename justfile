# =========================================
#  Threads-Agent – Dev helper recipes
# =========================================
set dotenv-load

# ---------- K8s Dev Platform ----------
bootstrap:          # spin local k3d
    ./scripts/dev-up.sh

deploy-dev:         # helm install into k3d
    helm upgrade --install threads ./chart \
         -f chart/values-dev.yaml \
         --wait --timeout 120s

k3d-stop-all:
	k3d cluster stop --all

k3d-nuke-all:
	k3d cluster delete --all

test:               # run unit + e2e
    pytest -q

logs:               # follow all pod logs
    kubectl logs -l app=threads -f --tail=100

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

default: deploy-dev
