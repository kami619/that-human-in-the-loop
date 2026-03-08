.PHONY: install test lint format check dry-run clean kind-up kind-down kind-test

# Unset CLAUDECODE to avoid nested-session error when running from Claude Code terminal
export CLAUDECODE=

install:  ## Install all dependencies (including dev)
	uv sync --extra dev

test:  ## Run tests
	uv run python -m pytest tests/ -v

lint:  ## Run ruff linter
	uv run ruff check .

format:  ## Format code with ruff
	uv run ruff format .
	uv run ruff check --fix .

check:  ## Run all checks (lint + test)
	uv run ruff check .
	uv run python -m pytest tests/ -v

dry-run:  ## Run with mock data (no cluster or API keys needed)
	uv run python main.py --query "Why are pods crashlooping in redhat-ods-applications?" --dry-run

kind-up:  ## Create kind cluster, install OLM + ODH from upstream chart, inject faults
	./scripts/kind-setup.sh

kind-down:  ## Delete the kind cluster and clean up cloned chart
	./scripts/kind-teardown.sh

kind-test:  ## Run the agent live against the kind cluster
	uv run python main.py \
		--query "Check cluster health and investigate issues in opendatahub namespace" \
		--namespace opendatahub

clean:  ## Remove build artifacts and caches
	rm -rf .pytest_cache __pycache__ .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
