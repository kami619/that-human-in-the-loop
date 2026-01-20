# AGENTS.md

## Project Overview
A cyberpunk-themed dashboard for monitoring engineering metrics, market data, and AI tool calling performance.

## Key Components
1. **Landing Page** (`index.html`) - Entry point with animated header and waitlist signup
2. **Dashboard** (`dashboard.html`) - Main interface with multiple data widgets
3. **Backend Functions** - Cloudflare Worker and Python script for data processing
4. **Data Files** - JSON data for BFCL leaderboard

## Dev Environment Tips
- No build step required - pure HTML/CSS/JS frontend
- Serve locally with `python -m http.server 3000` or `npx serve .`
- Edit files directly and refresh browser to see changes
- For backend development, use `wrangler dev` for Cloudflare Workers testing
- Update BFCL data with `python functions/update_bfcl_leaderboard.py`

## Widget Implementation Details

### Weather Widget
- Uses ipapi.co for geolocation (fallback to ipwho.is)
- Open-Meteo API for weather data
- Custom condition analysis function in `dashboard.html`
- Updates on page load only

### Clocks Widget
- Pure client-side JavaScript implementation
- Timezone selection via dropdowns
- Updates every second with setInterval

### BFCL Leaderboard Widget
- Displays top AI models by tool calling accuracy
- Data sourced from Berkeley Function-Calling Leaderboard
- JSON data file updated via Python script
- Shows model name, provider, and accuracy percentage

### Market Widgets
- TradingView widgets for indices and financial news
- Embedded via TradingView's official embedding script
- Configured for dark theme to match site aesthetic

## Backend Implementation

### Waitlist Signup (`functions/api/subscribe.js`)
- Cloudflare Worker function
- Stores emails in WAITLIST KV namespace
- Simple email validation
- Returns JSON response

### BFCL Data Update (`functions/update_bfcl_leaderboard.py`)
- Fetches CSV data from Berkeley's BFCL
- Processes and cleans model names/types
- Updates `bfcl-leaderboard.json` file
- Run manually to refresh leaderboard data

## Testing Instructions
- Test frontend by opening `index.html` and `dashboard.html` in browser
- Verify all widget functionality (weather, clocks, leaderboard)
- Test waitlist form submission with valid/invalid emails
- Run Python script to verify BFCL data update process
- Check responsive design on different screen sizes
- Test fallback mechanisms for API failures

## Deployment Instructions
1. Frontend files can be deployed to any static hosting service (Vercel, Netlify, GitHub Pages)
2. Cloudflare Worker for waitlist signup:
   - Deploy with `wrangler deploy`
   - Configure WAITLIST KV namespace in Cloudflare Dashboard
3. Set up cron job or manual process for BFCL data updates
4. Configure domain and SSL as needed

## Project Specific Tips
- Maintain consistent cyberpunk aesthetic when adding new features
- All styling is in CSS within HTML files - no external CSS files
- Keep JavaScript minimal and focused on specific widget functionality
- When adding new widgets, follow existing patterns for consistency
- Update AGENTS.md when adding significant new functionality
- Test all API integrations with appropriate error handling