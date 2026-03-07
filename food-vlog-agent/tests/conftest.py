"""Shared test fixtures for the food vlog agent tests."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add project root to path so tools/ can import config
sys.path.insert(0, str(Path(__file__).parent.parent))


class _Snippet:
    """Mimics youtube_transcript_api FetchedTranscriptSnippet."""

    def __init__(self, text, start, duration):
        self.text = text
        self.start = start
        self.duration = duration


@pytest.fixture
def sample_transcript_entries():
    """Sample YouTube transcript snippets (attribute-based, not dicts)."""
    return [
        _Snippet("Welcome to Hyderabad food tour!", 0.0, 3.5),
        _Snippet("First stop is Paradise Biryani.", 3.5, 4.0),
        _Snippet("This chicken biryani is amazing!", 30.0, 3.0),
        _Snippet("Now we're heading to Shah Ghouse for haleem.", 120.0, 5.0),
        _Snippet("Best vegetarian thali at Chutneys restaurant.", 300.0, 4.5),
    ]


@pytest.fixture
def sample_frame_paths(tmp_path):
    """Create temporary frame files and return their paths."""
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()
    paths = []
    for i in range(5):
        frame = frames_dir / f"frame_{i:04d}.jpg"
        frame.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 100)  # Minimal JPEG header
        paths.append(str(frame))
    return paths


@pytest.fixture
def sample_vision_ocr_response():
    """Mock Google Vision OCR response."""
    mock_response = MagicMock()
    mock_response.error.message = ""

    annotation1 = MagicMock()
    annotation1.description = "PARADISE\nBIRYANI\nSince 1953\nHyderabad"
    annotation1.confidence = 0.95

    annotation2 = MagicMock()
    annotation2.description = "PARADISE"
    annotation2.confidence = 0.98

    annotation3 = MagicMock()
    annotation3.description = "BIRYANI"
    annotation3.confidence = 0.97

    mock_response.text_annotations = [annotation1, annotation2, annotation3]
    return mock_response


@pytest.fixture
def sample_vision_label_response():
    """Mock Google Vision label detection response."""
    mock_response = MagicMock()
    mock_response.error.message = ""

    labels = []
    for desc, score in [
        ("Food", 0.98),
        ("Biryani", 0.95),
        ("Rice", 0.92),
        ("Restaurant", 0.88),
        ("Indian cuisine", 0.85),
    ]:
        label = MagicMock()
        label.description = desc
        label.score = score
        labels.append(label)

    mock_response.label_annotations = labels
    return mock_response


@pytest.fixture
def sample_maps_search_response():
    """Mock Google Maps text search response."""
    return {
        "results": [
            {
                "place_id": "ChIJ_paradise_123",
                "name": "Paradise Biryani",
                "formatted_address": "MG Road, Secunderabad, Hyderabad",
                "rating": 4.2,
                "user_ratings_total": 15000,
                "price_level": 2,
                "types": ["restaurant", "food"],
                "opening_hours": {"open_now": True},
            },
            {
                "place_id": "ChIJ_paradise_456",
                "name": "Paradise Food Court",
                "formatted_address": "Kukatpally, Hyderabad",
                "rating": 3.8,
                "user_ratings_total": 500,
                "price_level": 1,
                "types": ["restaurant"],
                "opening_hours": {"open_now": False},
            },
        ]
    }


@pytest.fixture
def sample_maps_details_response():
    """Mock Google Maps place details response."""
    return {
        "result": {
            "name": "Paradise Biryani",
            "formatted_address": "MG Road, Secunderabad, Hyderabad 500003",
            "formatted_phone_number": "+91 40 6666 6666",
            "website": "https://www.paradisebiryani.com",
            "rating": 4.2,
            "user_ratings_total": 15000,
            "price_level": 2,
            "opening_hours": {
                "weekday_text": [
                    "Monday: 11:00 AM – 11:00 PM",
                    "Tuesday: 11:00 AM – 11:00 PM",
                ]
            },
            "url": "https://maps.google.com/?cid=123456",
            "reviews": [
                {
                    "rating": 5,
                    "text": "Best biryani in Hyderabad!",
                    "relative_time_description": "a week ago",
                },
            ],
        }
    }


@pytest.fixture
def sample_directions_response():
    """Mock Google Maps directions response."""
    return [
        {
            "legs": [
                {
                    "distance": {"text": "5.2 km"},
                    "duration": {"text": "18 mins"},
                    "start_address": "Paradise Biryani, MG Road",
                    "end_address": "Shah Ghouse, Tolichowki",
                    "steps": [
                        {
                            "html_instructions": "Head south on MG Road",
                            "distance": {"text": "1.2 km"},
                            "duration": {"text": "4 mins"},
                        },
                        {
                            "html_instructions": "Turn left onto Tank Bund Road",
                            "distance": {"text": "2.0 km"},
                            "duration": {"text": "7 mins"},
                        },
                    ],
                }
            ]
        }
    ]
