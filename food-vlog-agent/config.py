"""Environment-based configuration."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).parent
OUTPUT_DIR = PROJECT_ROOT / "output"

# Google Cloud Vision
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

# Google Maps
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

# Frame extraction
KEYFRAME_INTERVAL_SECONDS = 30
VIDEO_FORMAT = "worst[ext=mp4]"

# Budget
MAX_BUDGET_USD = 5.00
