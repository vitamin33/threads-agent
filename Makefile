# Makefile for common development tasks

.PHONY: pre-pr test-quick test-full install-deps check-all

# Quick checks before creating PR
pre-pr: check-all
	@echo "✅ All pre-PR checks passed!"

# Install all dependencies
install-deps:
	@echo "📦 Installing dependencies..."
	pip install -r services/orchestrator/requirements.txt
	pip install -r services/celery_worker/requirements.txt  
	pip install -r services/persona_runtime/requirements.txt
	pip install -r services/fake_threads/requirements.txt
	pip install -r services/viral_engine/requirements.txt
	pip install -r tests/requirements.txt
	@echo "✅ Dependencies installed"

# Quick unit tests only
test-quick:
	@echo "🧪 Running quick unit tests..."
	PYTHONPATH=$(PWD) pytest -m "not e2e" -q --tb=short --maxfail=3

# Full test suite (requires k3d)
test-full:
	@echo "🧪 Running full test suite..."
	@if ! k3d cluster list | grep -q dev; then \
		echo "❌ k3d cluster 'dev' not running. Run: just dev-start"; \
		exit 1; \
	fi
	PYTHONPATH=$(PWD) pytest -v

# Run all checks
check-all: install-deps
	@echo "🔍 Running all pre-PR checks..."
	@echo ""
	@echo "1️⃣ Checking for debug prints..."
	@if grep -r "print(" services/ --include="*.py" | grep -v "# noqa" | grep -v "__pycache__"; then \
		echo "❌ Found debug print statements"; \
		exit 1; \
	else \
		echo "✅ No debug prints"; \
	fi
	@echo ""
	@echo "2️⃣ Running linters..."
	@ruff check . --select=E,W,F --quiet || (echo "❌ Linting failed" && exit 1)
	@echo "✅ Linting passed"
	@echo ""
	@echo "3️⃣ Running unit tests..."
	@$(MAKE) test-quick
	@echo ""
	@echo "4️⃣ Checking dependencies..."
	@python -c "import psutil, httpx, pytest" || (echo "❌ Missing test dependencies" && exit 1)
	@echo "✅ All dependencies present"

# Git hooks
install-hooks:
	@./scripts/install-git-hooks.sh
	@echo "✅ Git hooks installed"