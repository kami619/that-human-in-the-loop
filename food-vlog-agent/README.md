# Food Vlog Agent

A multi-agent system that processes YouTube food vlogs (particularly Telugu/Hindi vloggers), extracts restaurant POIs, validates them against Google Maps, and generates a curated food travel itinerary.

Built with the [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python) to showcase inner/outer loop agentic workflow patterns.

## Architecture

```
YouTube URL + Food Preferences (e.g., "Spicy Vegetarian")
        |
        v
+------------------------------+
|  ORCHESTRATOR (Sonnet)        |  <-- Outer Loop: dispatches via Task tool
|  Guides sequential pipeline   |
+-----------+------------------+
            |
            +--1-> [ingest-agent (Haiku)]
            |      Tools: get_transcript, extract_keyframes
            |      Output: transcript segments + frame file paths
            |
            +--2-> [vision-agent (Haiku)]
            |      Tools: analyze_image_ocr, detect_image_labels
            |      Output: OCR text + labels per frame
            |
            +--3-> [poi-extractor (Sonnet)]
            |      No tools (pure reasoning)
            |      Output: structured POI list with evidence
            |
            +--4-> [validator-agent (Haiku)]
            |      Tools: search_place, get_place_details
            |      Output: POIs enriched with Google Maps data
            |
            +--5-> [itinerary-agent (Sonnet)]
                   Tools: get_directions
                   Output: optimized food itinerary
```

Sub-agents cannot spawn sub-agents. The orchestrator dispatches all 5 directly, passing results between them via natural language context.

## Prerequisites

### API Keys

| Key | Purpose | Where to get it |
|-----|---------|-----------------|
| `ANTHROPIC_API_KEY` | Claude Agent SDK (powers all agents) | [console.anthropic.com](https://console.anthropic.com) |
| `GOOGLE_APPLICATION_CREDENTIALS` | Vision API (OCR + label detection on video frames) | See [GCP Service Account setup](#gcp-service-account-setup) below |
| `GOOGLE_MAPS_API_KEY` | Maps API (place search, details, directions) | See [Google Maps API Key setup](#google-maps-api-key-setup) below |

### Google Cloud APIs to enable

In your GCP project (APIs & Services > Library), search for and enable:
1. **Cloud Vision API** - frame OCR and label detection
2. **Places API** - restaurant search and details
3. **Directions API** - route planning between stops

### GCP Service Account setup

The Vision API requires a service account JSON key. Here's how to create one:

1. Go to **IAM & Admin > Service Accounts** in the [GCP Console](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Click **+ Create Service Account**
   - **Name**: `food-vlog-vision` (or any name you like)
   - **ID**: auto-fills from the name
   - **Description**: optional, skip it
3. Click **Create and Continue**
4. Under **Grant this service account access to project**, select role:
   - Click the Role dropdown, search for **Viewer**, and select it
   - (Vision API access is controlled by whether the API is enabled on the project, so Viewer is sufficient)
5. Click **Continue**, then **Done**
6. Click on the service account you just created
7. Go to the **Keys** tab
8. Click **Add Key > Create new key**
9. Select **JSON**, click **Create** — the `.json` file downloads automatically
10. Move it somewhere safe and reference it in your `.env`:

```bash
mv ~/Downloads/food-vlog-vision-*.json ~/.config/gcloud/food-vlog-vision.json

# In your .env file:
GOOGLE_APPLICATION_CREDENTIALS=/path/to/.config/gcloud/food-vlog-vision.json
```

### Google Maps API Key setup

The Maps API uses a simple API key (not a service account). Here's how to create one:

1. **Enable the APIs first** — they won't appear in the key restriction dropdown until enabled:
   - Go to **APIs & Services > Library** in the [GCP Console](https://console.cloud.google.com/apis/library)
   - Search for and **Enable** each of these:
     - **Places API** (or **Places API (New)**)
     - **Directions API**
     - **Geocoding API**
2. Go to **APIs & Services > Credentials** in the [GCP Console](https://console.cloud.google.com/apis/credentials)
3. Click **+ Create Credentials** at the top, then select **API key**
4. A new key is created immediately — copy it
5. Click **Edit API key** (the pencil icon) to restrict it:
   - Under **API restrictions**, select **Restrict key**
   - Check: **Places API**, **Directions API**, **Geocoding API** (they appear now because you enabled them in step 1)
   - Click **Save**
6. Add it to your `.env`:

```bash
# In your .env file:
GOOGLE_MAPS_API_KEY=AIza...your-key-here
```

> **Billing note**: Google Maps Platform requires a billing account linked to your project. New accounts get a $200/month free tier which is more than enough — each run of this project costs ~$0.25–0.50 in Maps API calls.

### Local tools

| Tool | Purpose | Install |
|------|---------|---------|
| `ffmpeg` | Extracts still frames from downloaded video at 30s intervals | `brew install ffmpeg` |
| `uv` | Python dependency management | `brew install uv` |

`yt-dlp` (YouTube downloader) is installed automatically as a Python dependency.

## Setup

```bash
cd food-vlog-agent
cp .env.example .env
# Fill in API keys in .env

brew install ffmpeg    # if not installed
make install           # installs Python deps
make test              # verify everything works
```

## Usage

### Live mode (requires API keys)

```bash
uv run python main.py \
  --url "https://youtube.com/watch?v=YOUR_VIDEO_ID" \
  --preferences "Spicy Vegetarian"
```

### Dry-run mode (no API keys needed)

Uses mock data simulating a Hyderabad food vlog:

```bash
make dry-run

# or directly:
uv run python main.py \
  --url "https://youtube.com/watch?v=demo1234567" \
  --preferences "Spicy Vegetarian" \
  --dry-run
```

### Output

The final itinerary is saved to `output/{video_id}/itinerary.md` and printed to the console. See [`examples/sample_itinerary.json`](examples/sample_itinerary.json) for sample output.

## Cost per run

For a typical 15-minute food vlog:

| Component | Cost |
|-----------|------|
| YouTube transcript | Free |
| Key frame extraction | Free (yt-dlp + ffmpeg, ~30 frames) |
| Google Vision API | ~$0.09 (30 frames x 2 features) |
| Google Maps API | ~$0.25-0.50 (5-10 POIs) |
| Claude Haiku (3 agents) | ~$0.03 |
| Claude Sonnet (2 agents) | ~$0.17 |
| **Total** | **~$0.50-$0.80** |

A `max_budget_usd=1.00` guard rail in the orchestrator stops execution if costs exceed the limit.

## Development

```bash
make check     # lint + tests
make lint      # ruff linter only
make format    # auto-format with ruff
make test      # pytest only
make clean     # remove caches and output
```

## Project structure

```
food-vlog-agent/
├── main.py                     # CLI entry point (--url, --preferences, --dry-run)
├── orchestrator.py             # Outer loop: Sonnet dispatches 5 agents via Task
├── config.py                   # Environment-based configuration
├── models/
│   └── schemas.py              # Pydantic v2 data models (POI, Itinerary, etc.)
├── agents/
│   └── definitions.py          # 5 AgentDefinition configs with embedded schemas
├── tools/
│   ├── youtube_tools.py        # get_transcript, extract_keyframes
│   ├── vision_tools.py         # analyze_image_ocr, detect_image_labels
│   ├── maps_tools.py           # search_place, get_place_details, get_directions
│   └── mock_data.py            # Mock tool responses for --dry-run mode
├── tests/
│   ├── conftest.py             # Shared fixtures
│   ├── test_youtube_tools.py   # 8 tests
│   ├── test_vision_tools.py    # 6 tests
│   └── test_maps_tools.py      # 12 tests
├── examples/
│   └── sample_itinerary.json   # Example output
├── output/                     # Runtime output (gitignored)
├── pyproject.toml
├── Makefile
└── LICENSE
```

## License

MIT
