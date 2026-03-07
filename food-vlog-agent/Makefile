.PHONY: install test lint format check run dry-run clean

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

run:  ## Run pipeline (pass URL and PREFS, e.g. make run URL=https://youtu.be/xxx PREFS="Spicy")
	uv run python main.py --url "$(URL)" --preferences "$(PREFS)"

dry-run:  ## Run pipeline with mock data (no API keys needed)
	uv run python main.py --url "https://youtube.com/watch?v=demo1234567" --preferences "Spicy Vegetarian" --dry-run

clean:  ## Remove build artifacts and caches
	rm -rf output/*/ .pytest_cache __pycache__ .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
