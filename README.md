# That Human In The Loop

A monorepo containing a cyberpunk-themed personal dashboard and multi-agent AI projects built with the Claude Agent SDK.

## Cyberpunk Dashboard

A static two-page dashboard with live data widgets, served with no build step.

- **Landing page** (`index.html`) -- Animated header, chess board animation, rotating engineering quotes
- **Dashboard** (`dashboard.html`) -- Weather, multi-timezone clocks, DeepSWE coding-agent leaderboard, Artificial Analysis Intelligence Index, TradingView markets, financial news, stellar explorer
- **Solar system** (`solar-system.html`) -- 3D solar system visualization

### Run locally

```bash
python -m http.server 3000
# or
npx serve .
```

### External data

| Source | Widget | Auth |
|--------|--------|------|
| ipapi.co / ipwho.is | Geolocation (weather) | None |
| Open-Meteo | Weather | None |
| TradingView | Markets, News | None (embedded widgets) |
| DeepSWE snapshot | Coding-agent leaderboard | None |
| Artificial Analysis snapshot | Intelligence Index | None |

The dashboard uses checked-in snapshots in `deepswe-leaderboard.json` and `artificial-analysis-leaderboard.json`. They are refreshed daily by GitHub Actions (`.github/workflows/update_model_leaderboards.yml`). Each widget displays its source and snapshot date. Artificial Analysis API access is kept server-side in the workflow.

## Agent Projects

Multi-agent systems built with the [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python). Each is a standalone Python project with its own `README.md`, `AGENTS.md`, and `pyproject.toml`.

| Project | Description |
|---------|-------------|
| [`food-vlog-agent/`](food-vlog-agent/) | YouTube food vlog -> curated restaurant itinerary. 5-agent pipeline (ingest, vision, POI extraction, validation, itinerary). Uses Google Vision + Maps MCP tools. |
| [`odh-sre-agent/`](odh-sre-agent/) | SRE agent for ROSA OpenShift + Open Data Hub. 5 sub-agents (cluster, workload, networking, helm, remediation) sharing a single `kubernetes-mcp-server`. |

Both projects follow the same patterns: Sonnet orchestrator dispatching Haiku sub-agents via the `Task` tool, Pydantic v2 schemas, Rich CLI output, and `--dry-run` mode for testing without external dependencies.

## Project Structure

```
that-hitl/
├── index.html                  # Landing page
├── dashboard.html              # Dashboard with model leaderboard widgets
├── solar-system.html           # 3D solar system
├── theme.css                   # Shared CSS variables and scanline effect
├── deepswe-leaderboard.json    # DeepSWE v1.1 snapshot
├── artificial-analysis-leaderboard.json # Artificial Analysis snapshot
├── functions/
│   ├── api/subscribe.js        # Cloudflare Worker (waitlist endpoint)
│   ├── update_bfcl_leaderboard.py  # Legacy BFCL ETL
│   ├── test_update_bfcl.py     # Legacy BFCL ETL tests
│   ├── update_model_leaderboards.py # DeepSWE + Artificial Analysis ETL
│   ├── test_update_model_leaderboards.py # ETL tests
│   └── test_leaderboard_snapshots.py # Snapshot schema tests
├── .github/workflows/
│   └── update_model_leaderboards.yml # Daily leaderboard refresh
├── food-vlog-agent/            # YouTube food vlog agent (see its README)
├── odh-sre-agent/              # OpenShift SRE agent (see its README)
├── chess-pgn/                  # PGN files of chess games
└── LICENSE                     # Apache 2.0
```

## License

Apache 2.0
