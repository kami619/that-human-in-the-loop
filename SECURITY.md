# Security

## Static dashboard

- **Content-Security-Policy** meta tags are set on `index.html`, `dashboard.html`, `ipl-trades.html`, and `solar-system.html`.
- Third-party scripts (TradingView, Tailwind CDN, Three.js) are allow-listed in CSP. **Do not** add `crossorigin` on the Tailwind CDN script (it fails CORS and breaks styling). Tailwind CDN has no stable SRI pin; prefer vendoring CSS if you need stricter supply-chain control.
- `security-utils.js` provides `sanitizeHttpsUrl()` and `safeGradientTint()` for the IPL trade terminal.

## IPL trade data

- `functions/ipl_security.py` validates franchise gradient `tint` strings and `sourceUrl` (HTTPS, `iplt20.com` only) before writing `ipl-trades.json`.
- Run `python functions/update_ipl_trades.py` after changing trade mappings.

## Python dependencies

- Dashboard ETL pins `requests` in `functions/requirements.txt`.
- Weekly **Security audit** workflow: `.github/workflows/security-audit.yml` runs `pip-audit` on that file; `odh-sre-agent` is audited informatively (`continue-on-error: true`).

## Cloudflare waitlist worker

`README.md` references `functions/api/subscribe.js`, but that worker **is not in this repository**. If a worker is still deployed in Cloudflare, treat it as out-of-band: review rate limiting, input validation, and secrets there, or decommission the route and update the docs.

## Reporting

Open a private issue or contact the maintainer for suspected vulnerabilities.