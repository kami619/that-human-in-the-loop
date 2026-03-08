# ODH SRE Agent

## Commands
- `make install` / `make test` / `make check` / `make dry-run`
- `make kind-up` / `make kind-test` / `make kind-down` — kind cluster with ODH fixtures
- Always use `uv run python` not bare `python`
- Run live: `uv run python main.py --query "..." --namespace "..."`

## Conventions
- External MCP server: `kubernetes-mcp-server` (no custom tools to maintain)
- Sub-agents get `allowed_tools` subsets of the shared MCP server tools
- All tools prefixed `mcp__k8s__` (server registered as "k8s")
- Orchestrator dispatches dynamically via `Task` tool — no fixed pipeline order
- Pydantic v2 schemas in `models/schemas.py`, embedded in agent prompts via `_schema_hint()`

## Warnings
- `CLAUDECODE` env var must be cleared before spawning child CLI (see `orchestrator.py`)
- `kubernetes-mcp-server` binary must be installed and on PATH
- Kubeconfig must be configured for live mode; dry-run uses `--cluster-provider disabled`
- Budget guard rail: `max_budget_usd=2.00` in `config.py`

## SDK Workarounds (claude-agent-sdk v0.1.x)
- **stdin hold**: `_held_message()` async generator in `orchestrator.py`
- **Shutdown race**: `BaseExceptionGroup` handler in `main.py` suppresses `CLIConnectionError`
