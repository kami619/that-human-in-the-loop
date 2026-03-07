"""MCP tools for Google Maps: place search, details, and directions."""

from __future__ import annotations

import json

import googlemaps
from claude_agent_sdk import create_sdk_mcp_server, tool

from config import GOOGLE_MAPS_API_KEY


_maps_client: googlemaps.Client | None = None


def _get_client() -> googlemaps.Client:
    global _maps_client
    if _maps_client is None:
        _maps_client = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
    return _maps_client


# ── Core logic (directly testable) ───────────────────────────────────


async def _search_place_impl(query: str, location_bias: str = "") -> dict:
    """Search for a place — separated from @tool wrapper for testability."""
    client = _get_client()

    kwargs: dict = {"query": query}
    if location_bias and "," in location_bias:
        parts = location_bias.split(",")
        try:
            lat, lng = float(parts[0].strip()), float(parts[1].strip())
            kwargs["location"] = (lat, lng)
            kwargs["radius"] = 5000
        except ValueError:
            pass

    results = client.places(**kwargs).get("results", [])

    places = []
    for r in results[:5]:
        places.append(
            {
                "place_id": r.get("place_id", ""),
                "name": r.get("name", ""),
                "address": r.get("formatted_address", ""),
                "rating": r.get("rating"),
                "total_ratings": r.get("user_ratings_total"),
                "price_level": r.get("price_level"),
                "types": r.get("types", []),
                "open_now": r.get("opening_hours", {}).get("open_now"),
            }
        )

    return {"query": query, "result_count": len(places), "places": places}


async def _get_place_details_impl(place_id: str) -> dict:
    """Get place details — separated from @tool wrapper for testability."""
    client = _get_client()
    result = client.place(
        place_id=place_id,
        fields=[
            "name",
            "formatted_address",
            "formatted_phone_number",
            "website",
            "rating",
            "user_ratings_total",
            "price_level",
            "opening_hours",
            "url",
            "reviews",
        ],
    ).get("result", {})

    hours = []
    if "opening_hours" in result:
        hours = result["opening_hours"].get("weekday_text", [])

    reviews_summary = []
    for review in result.get("reviews", [])[:3]:
        reviews_summary.append(
            {
                "rating": review.get("rating"),
                "text": review.get("text", "")[:200],
                "time": review.get("relative_time_description", ""),
            }
        )

    return {
        "place_id": place_id,
        "name": result.get("name", ""),
        "address": result.get("formatted_address", ""),
        "phone": result.get("formatted_phone_number", ""),
        "website": result.get("website", ""),
        "rating": result.get("rating"),
        "total_ratings": result.get("user_ratings_total"),
        "price_level": result.get("price_level"),
        "opening_hours": hours,
        "maps_url": result.get("url", ""),
        "top_reviews": reviews_summary,
    }


async def _get_directions_impl(origin: str, destination: str, mode: str = "driving") -> dict:
    """Get directions — separated from @tool wrapper for testability."""
    client = _get_client()
    result = client.directions(origin=origin, destination=destination, mode=mode)

    if not result:
        return {"error": "No route found", "origin": origin, "destination": destination}

    leg = result[0]["legs"][0]
    return {
        "origin": origin,
        "destination": destination,
        "mode": mode,
        "distance": leg["distance"]["text"],
        "duration": leg["duration"]["text"],
        "start_address": leg.get("start_address", ""),
        "end_address": leg.get("end_address", ""),
        "steps": [
            {
                "instruction": step.get("html_instructions", ""),
                "distance": step["distance"]["text"],
                "duration": step["duration"]["text"],
            }
            for step in leg["steps"][:10]
        ],
    }


# ── @tool wrappers ───────────────────────────────────────────────────


@tool(
    "search_place",
    "Search for a restaurant or food place on Google Maps. "
    "Returns place ID, name, address, and rating.",
    {"query": str, "location_bias": str},
)
async def search_place(args: dict) -> dict:
    data = await _search_place_impl(args["query"], args.get("location_bias", ""))
    return {"content": [{"type": "text", "text": json.dumps(data)}]}


@tool(
    "get_place_details",
    "Get detailed information about a place by its Google Maps place ID. "
    "Returns hours, phone, website, reviews summary.",
    {"place_id": str},
)
async def get_place_details(args: dict) -> dict:
    data = await _get_place_details_impl(args["place_id"])
    return {"content": [{"type": "text", "text": json.dumps(data)}]}


@tool(
    "get_directions",
    "Get driving/walking directions between two places. "
    "Returns route summary, distance, and estimated travel time.",
    {"origin": str, "destination": str, "mode": str},
)
async def get_directions(args: dict) -> dict:
    data = await _get_directions_impl(
        args["origin"], args["destination"], args.get("mode", "driving")
    )
    return {"content": [{"type": "text", "text": json.dumps(data)}]}


def create_maps_server():
    """Create the Maps MCP server with search, details, and directions tools."""
    return create_sdk_mcp_server(
        name="maps",
        version="1.0.0",
        tools=[search_place, get_place_details, get_directions],
    )
