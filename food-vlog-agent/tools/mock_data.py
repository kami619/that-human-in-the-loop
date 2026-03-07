"""Mock tool responses for --dry-run mode. Simulates a Hyderabad food vlog."""

from __future__ import annotations

import json

from claude_agent_sdk import create_sdk_mcp_server, tool

# ── Mock YouTube tools ────────────────────────────────────────────────


MOCK_TRANSCRIPT = {
    "video_id": "demo_hyd_food",
    "segment_count": 8,
    "segments": [
        {
            "text": "Namaste everyone! Welcome to my Hyderabad food tour!",
            "start": 0.0,
            "duration": 4.0,
        },
        {
            "text": "First stop - Paradise Biryani on MG Road. This place has been serving the best biryani since 1953.",
            "start": 15.0,
            "duration": 6.0,
        },
        {
            "text": "Look at this chicken dum biryani! The rice is perfectly layered with the meat. Amazing flavors.",
            "start": 45.0,
            "duration": 5.5,
        },
        {
            "text": "Now heading to Shah Ghouse in Tolichowki for their famous haleem and kebabs.",
            "start": 120.0,
            "duration": 5.0,
        },
        {
            "text": "This mutton haleem is incredible! So rich and creamy. Only 250 rupees for a full plate.",
            "start": 180.0,
            "duration": 5.0,
        },
        {
            "text": "Next up is Chutneys restaurant in Banjara Hills for South Indian breakfast.",
            "start": 300.0,
            "duration": 4.5,
        },
        {
            "text": "Their paper dosa and pesarattu are legendary. Pure vegetarian place with amazing chutneys.",
            "start": 330.0,
            "duration": 5.0,
        },
        {
            "text": "Last stop - Nimrah Cafe at Charminar for Irani chai and Osmania biscuits. Perfect ending!",
            "start": 450.0,
            "duration": 5.0,
        },
    ],
}

MOCK_FRAMES = {
    "video_id": "demo_hyd_food",
    "frame_count": 5,
    "frames": [
        {"path": "output/demo_hyd_food/frames/frame_0001.jpg", "timestamp": 0},
        {"path": "output/demo_hyd_food/frames/frame_0002.jpg", "timestamp": 30},
        {"path": "output/demo_hyd_food/frames/frame_0003.jpg", "timestamp": 120},
        {"path": "output/demo_hyd_food/frames/frame_0004.jpg", "timestamp": 300},
        {"path": "output/demo_hyd_food/frames/frame_0005.jpg", "timestamp": 450},
    ],
    "cached": True,
}

# ── Mock Vision tools ─────────────────────────────────────────────────

MOCK_OCR_RESULTS = {
    "output/demo_hyd_food/frames/frame_0001.jpg": {
        "image_path": "output/demo_hyd_food/frames/frame_0001.jpg",
        "full_text": "HYDERABAD FOOD TOUR\nSubscribe for more!",
        "annotations": [],
    },
    "output/demo_hyd_food/frames/frame_0002.jpg": {
        "image_path": "output/demo_hyd_food/frames/frame_0002.jpg",
        "full_text": "PARADISE\nBIRYANI\nSince 1953\nMG Road, Secunderabad",
        "annotations": [
            {"description": "PARADISE", "confidence": 0.98},
            {"description": "BIRYANI", "confidence": 0.97},
        ],
    },
    "output/demo_hyd_food/frames/frame_0003.jpg": {
        "image_path": "output/demo_hyd_food/frames/frame_0003.jpg",
        "full_text": "SHAH GHOUSE\nCafe & Restaurant\nTolichowki",
        "annotations": [
            {"description": "SHAH GHOUSE", "confidence": 0.95},
        ],
    },
    "output/demo_hyd_food/frames/frame_0004.jpg": {
        "image_path": "output/demo_hyd_food/frames/frame_0004.jpg",
        "full_text": "CHUTNEYS\nPure Vegetarian\nBanjara Hills",
        "annotations": [
            {"description": "CHUTNEYS", "confidence": 0.96},
        ],
    },
    "output/demo_hyd_food/frames/frame_0005.jpg": {
        "image_path": "output/demo_hyd_food/frames/frame_0005.jpg",
        "full_text": "NIMRAH\nCafe & Bakery\nCharminar",
        "annotations": [
            {"description": "NIMRAH", "confidence": 0.94},
        ],
    },
}

MOCK_LABEL_RESULTS = {
    "output/demo_hyd_food/frames/frame_0001.jpg": {
        "image_path": "output/demo_hyd_food/frames/frame_0001.jpg",
        "labels": [
            {"description": "City", "score": 0.92},
            {"description": "Street", "score": 0.88},
        ],
    },
    "output/demo_hyd_food/frames/frame_0002.jpg": {
        "image_path": "output/demo_hyd_food/frames/frame_0002.jpg",
        "labels": [
            {"description": "Biryani", "score": 0.97},
            {"description": "Rice", "score": 0.95},
            {"description": "Food", "score": 0.98},
            {"description": "Restaurant", "score": 0.90},
            {"description": "Indian cuisine", "score": 0.88},
        ],
    },
    "output/demo_hyd_food/frames/frame_0003.jpg": {
        "image_path": "output/demo_hyd_food/frames/frame_0003.jpg",
        "labels": [
            {"description": "Haleem", "score": 0.93},
            {"description": "Kebab", "score": 0.90},
            {"description": "Food", "score": 0.97},
            {"description": "Restaurant", "score": 0.89},
        ],
    },
    "output/demo_hyd_food/frames/frame_0004.jpg": {
        "image_path": "output/demo_hyd_food/frames/frame_0004.jpg",
        "labels": [
            {"description": "Dosa", "score": 0.96},
            {"description": "South Indian food", "score": 0.93},
            {"description": "Vegetarian", "score": 0.91},
            {"description": "Restaurant", "score": 0.88},
        ],
    },
    "output/demo_hyd_food/frames/frame_0005.jpg": {
        "image_path": "output/demo_hyd_food/frames/frame_0005.jpg",
        "labels": [
            {"description": "Tea", "score": 0.95},
            {"description": "Biscuit", "score": 0.90},
            {"description": "Cafe", "score": 0.92},
        ],
    },
}

# ── Mock Maps tools ───────────────────────────────────────────────────

MOCK_PLACES = {
    "Paradise Biryani": {
        "query": "Paradise Biryani Hyderabad",
        "result_count": 1,
        "places": [
            {
                "place_id": "ChIJm_paradise_hyd",
                "name": "Paradise Biryani",
                "address": "MG Road, Secunderabad, Hyderabad 500003",
                "rating": 4.2,
                "total_ratings": 15420,
                "price_level": 2,
                "types": ["restaurant", "food"],
                "open_now": True,
            }
        ],
    },
    "Shah Ghouse": {
        "query": "Shah Ghouse Hyderabad",
        "result_count": 1,
        "places": [
            {
                "place_id": "ChIJm_shahghouse_hyd",
                "name": "Shah Ghouse Cafe & Restaurant",
                "address": "Tolichowki, Hyderabad 500008",
                "rating": 4.3,
                "total_ratings": 22100,
                "price_level": 2,
                "types": ["restaurant", "food"],
                "open_now": True,
            }
        ],
    },
    "Chutneys": {
        "query": "Chutneys Hyderabad",
        "result_count": 1,
        "places": [
            {
                "place_id": "ChIJm_chutneys_hyd",
                "name": "Chutneys",
                "address": "Road No. 10, Banjara Hills, Hyderabad 500034",
                "rating": 4.4,
                "total_ratings": 8900,
                "price_level": 2,
                "types": ["restaurant", "food"],
                "open_now": True,
            }
        ],
    },
    "Nimrah": {
        "query": "Nimrah Cafe Hyderabad",
        "result_count": 1,
        "places": [
            {
                "place_id": "ChIJm_nimrah_hyd",
                "name": "Nimrah Cafe & Bakery",
                "address": "Charminar, Hyderabad 500002",
                "rating": 4.1,
                "total_ratings": 12300,
                "price_level": 1,
                "types": ["cafe", "bakery", "food"],
                "open_now": True,
            }
        ],
    },
}

MOCK_PLACE_DETAILS = {
    "ChIJm_paradise_hyd": {
        "place_id": "ChIJm_paradise_hyd",
        "name": "Paradise Biryani",
        "address": "MG Road, Secunderabad, Hyderabad 500003",
        "phone": "+91 40 6666 1234",
        "website": "https://www.paradisebiryani.com",
        "rating": 4.2,
        "total_ratings": 15420,
        "price_level": 2,
        "opening_hours": ["Monday: 11:00 AM – 11:00 PM", "Tuesday: 11:00 AM – 11:00 PM"],
        "maps_url": "https://maps.google.com/?cid=paradise123",
        "top_reviews": [{"rating": 5, "text": "Best biryani in Hyderabad!", "time": "a week ago"}],
    },
    "ChIJm_shahghouse_hyd": {
        "place_id": "ChIJm_shahghouse_hyd",
        "name": "Shah Ghouse Cafe & Restaurant",
        "address": "Tolichowki, Hyderabad 500008",
        "phone": "+91 40 2354 5678",
        "website": "",
        "rating": 4.3,
        "total_ratings": 22100,
        "price_level": 2,
        "opening_hours": ["Monday: 5:00 AM – 1:00 AM", "Tuesday: 5:00 AM – 1:00 AM"],
        "maps_url": "https://maps.google.com/?cid=shahghouse123",
        "top_reviews": [{"rating": 5, "text": "Haleem here is unmatched!", "time": "2 weeks ago"}],
    },
    "ChIJm_chutneys_hyd": {
        "place_id": "ChIJm_chutneys_hyd",
        "name": "Chutneys",
        "address": "Road No. 10, Banjara Hills, Hyderabad 500034",
        "phone": "+91 40 2335 9012",
        "website": "",
        "rating": 4.4,
        "total_ratings": 8900,
        "price_level": 2,
        "opening_hours": ["Monday: 7:00 AM – 10:30 PM", "Tuesday: 7:00 AM – 10:30 PM"],
        "maps_url": "https://maps.google.com/?cid=chutneys123",
        "top_reviews": [{"rating": 5, "text": "Best dosas in the city!", "time": "3 days ago"}],
    },
    "ChIJm_nimrah_hyd": {
        "place_id": "ChIJm_nimrah_hyd",
        "name": "Nimrah Cafe & Bakery",
        "address": "Charminar, Hyderabad 500002",
        "phone": "+91 40 2457 3456",
        "website": "",
        "rating": 4.1,
        "total_ratings": 12300,
        "price_level": 1,
        "opening_hours": ["Monday: 5:00 AM – 11:00 PM", "Tuesday: 5:00 AM – 11:00 PM"],
        "maps_url": "https://maps.google.com/?cid=nimrah123",
        "top_reviews": [{"rating": 4, "text": "Irani chai is a must-try", "time": "a month ago"}],
    },
}

MOCK_DIRECTIONS = {
    "origin": "Paradise Biryani, MG Road, Secunderabad",
    "destination": "Shah Ghouse, Tolichowki",
    "mode": "driving",
    "distance": "12.5 km",
    "duration": "35 mins",
    "start_address": "MG Road, Secunderabad",
    "end_address": "Tolichowki, Hyderabad",
    "steps": [
        {"instruction": "Head south on MG Road", "distance": "2.0 km", "duration": "6 mins"},
        {
            "instruction": "Take NH65 towards Tolichowki",
            "distance": "10.5 km",
            "duration": "29 mins",
        },
    ],
}


# ── Mock MCP tool wrappers ────────────────────────────────────────────


@tool("get_transcript", "Mock: return pre-built transcript", {"video_url": str})
async def mock_get_transcript(args: dict) -> dict:
    return {"content": [{"type": "text", "text": json.dumps(MOCK_TRANSCRIPT)}]}


@tool(
    "extract_keyframes",
    "Mock: return pre-built frame list",
    {"video_url": str, "interval_seconds": int},
)
async def mock_extract_keyframes(args: dict) -> dict:
    return {"content": [{"type": "text", "text": json.dumps(MOCK_FRAMES)}]}


@tool("analyze_image_ocr", "Mock: return pre-built OCR results", {"image_path": str})
async def mock_analyze_image_ocr(args: dict) -> dict:
    image_path = args["image_path"]
    data = MOCK_OCR_RESULTS.get(
        image_path,
        {"image_path": image_path, "full_text": "", "annotations": []},
    )
    return {"content": [{"type": "text", "text": json.dumps(data)}]}


@tool("detect_image_labels", "Mock: return pre-built label results", {"image_path": str})
async def mock_detect_image_labels(args: dict) -> dict:
    image_path = args["image_path"]
    data = MOCK_LABEL_RESULTS.get(
        image_path,
        {"image_path": image_path, "labels": []},
    )
    return {"content": [{"type": "text", "text": json.dumps(data)}]}


@tool("search_place", "Mock: return pre-built place search", {"query": str, "location_bias": str})
async def mock_search_place(args: dict) -> dict:
    query = args["query"]
    # Try to match by restaurant name substring
    for name, data in MOCK_PLACES.items():
        if name.lower() in query.lower():
            return {"content": [{"type": "text", "text": json.dumps(data)}]}
    return {
        "content": [
            {"type": "text", "text": json.dumps({"query": query, "result_count": 0, "places": []})}
        ]
    }


@tool("get_place_details", "Mock: return pre-built place details", {"place_id": str})
async def mock_get_place_details(args: dict) -> dict:
    place_id = args["place_id"]
    data = MOCK_PLACE_DETAILS.get(
        place_id,
        {
            "place_id": place_id,
            "name": "Unknown",
            "address": "",
            "rating": None,
            "opening_hours": [],
            "maps_url": "",
            "top_reviews": [],
        },
    )
    return {"content": [{"type": "text", "text": json.dumps(data)}]}


@tool(
    "get_directions",
    "Mock: return pre-built directions",
    {"origin": str, "destination": str, "mode": str},
)
async def mock_get_directions(args: dict) -> dict:
    data = {
        **MOCK_DIRECTIONS,
        "origin": args["origin"],
        "destination": args["destination"],
        "mode": args.get("mode", "driving"),
    }
    return {"content": [{"type": "text", "text": json.dumps(data)}]}


# ── Mock MCP servers ──────────────────────────────────────────────────


def create_mock_youtube_server():
    return create_sdk_mcp_server(
        name="youtube", version="1.0.0", tools=[mock_get_transcript, mock_extract_keyframes]
    )


def create_mock_vision_server():
    return create_sdk_mcp_server(
        name="vision", version="1.0.0", tools=[mock_analyze_image_ocr, mock_detect_image_labels]
    )


def create_mock_maps_server():
    return create_sdk_mcp_server(
        name="maps",
        version="1.0.0",
        tools=[mock_search_place, mock_get_place_details, mock_get_directions],
    )
