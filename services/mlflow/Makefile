# MLflow Service Makefile

.PHONY: help install uninstall upgrade port-forward test lint

NAMESPACE := threads-agent
RELEASE_NAME := mlflow
CHART_PATH := ./helm

help: ## Show this help message
	@echo "MLflow Service Management"
	@echo "========================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

deps: ## Update Helm dependencies
	helm repo add bitnami https://charts.bitnami.com/bitnami
	helm repo update
	helm dependency update $(CHART_PATH)

install: deps ## Install MLflow with Helm
	helm install $(RELEASE_NAME) $(CHART_PATH) -n $(NAMESPACE) --create-namespace

uninstall: ## Uninstall MLflow
	helm uninstall $(RELEASE_NAME) -n $(NAMESPACE)

upgrade: deps ## Upgrade MLflow deployment
	helm upgrade $(RELEASE_NAME) $(CHART_PATH) -n $(NAMESPACE)

port-forward: ## Port forward MLflow UI to localhost:5000
	kubectl port-forward svc/$(RELEASE_NAME) 5000:5000 -n $(NAMESPACE)

logs: ## View MLflow logs
	kubectl logs -f deployment/$(RELEASE_NAME) -n $(NAMESPACE)

status: ## Check deployment status
	@echo "=== Pods ==="
	kubectl get pods -n $(NAMESPACE) -l app.kubernetes.io/name=mlflow
	@echo "\n=== Services ==="
	kubectl get svc -n $(NAMESPACE) -l app.kubernetes.io/name=mlflow
	@echo "\n=== Ingress ==="
	kubectl get ingress -n $(NAMESPACE) -l app.kubernetes.io/name=mlflow

test: ## Run tests
	pytest tests/ -v

lint: ## Lint Helm chart
	helm lint $(CHART_PATH)

dry-run: deps ## Dry run installation
	helm install $(RELEASE_NAME) $(CHART_PATH) -n $(NAMESPACE) --dry-run --debug