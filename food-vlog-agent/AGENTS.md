# Food Vlog Agent

## Commands
- `make install` / `make test` / `make check` / `make dry-run`
- Always use `uv run python` not bare `python`
- Run live: `uv run python main.py --url "..." --preferences "..."`

## Conventions
- MCP tools: split into `_impl()` (testable) + `@tool` wrapper (thin)
- API clients are cached at module level (`_get_client()` / `_get_vision_client()`)
- Pydantic v2 schemas in `models/schemas.py`, embedded in agent prompts via `_schema_hint()`
- Orchestrator dispatches via `Task` tool only — no direct Read/Bash/WebFetch

## Warnings
- `CLAUDECODE` env var must be cleared before spawning child CLI (see `orchestrator.py`)
- Vision API: use explicit service account creds, not ADC — ADC can silently pick up a wrong GCP project
- Budget guard rail: `max_budget_usd=5.00` in `config.py` — actual runs cost ~$1.50, don't lower without checking
- `yt-dlp` needs both the brew binary and the Python package

## SDK Workarounds (claude-agent-sdk v0.1.x)
- **stdin hold**: `_held_message()` async generator in `orchestrator.py` — without it, SDK closes stdin after first sub-agent result
- **Shutdown race**: `BaseExceptionGroup` handler in `main.py` suppresses `CLIConnectionError`
