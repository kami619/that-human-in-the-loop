# AGENTS.md

Monorepo with standalone projects. Sub-projects with their own `AGENTS.md` are listed below.

## Cyberpunk Dashboard (repo root)

### Commands
- Serve: `python -m http.server 3000` or `npx serve .`
- BFCL data: `python functions/update_bfcl_leaderboard.py`
- Tests: `python -m pytest functions/test_update_bfcl.py`
- Deploy worker: `wrangler deploy`

### Conventions
- No build step — pure HTML/CSS/JS
- Shared CSS variables in `theme.css`, linked from both pages
- Widget JS is inline within each HTML file (no bundler)
- BFCL: GitHub Actions daily cron pushes to `bfcl` branch

## Sub-projects

| Directory | Description |
|-----------|-------------|
| `food-vlog-agent/` | Multi-agent YouTube food vlog → itinerary pipeline (Claude Agent SDK) |
| `odh-sre-agent/` | Multi-agent SRE system for ROSA OpenShift + Open Data Hub (Claude Agent SDK) |
| `chess-pgn/` | PGN files of chess games |
