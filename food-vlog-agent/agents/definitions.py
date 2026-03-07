"""Agent definitions for the food vlog processing pipeline.

Each agent has a specific role, model, tools, and system prompt that defines
how it processes its portion of the pipeline.
"""

from __future__ import annotations

from claude_agent_sdk import AgentDefinition

from models.schemas import (
    FoodItinerary,
    IngestResult,
    POIExtractionResult,
    ValidationResult,
    VisionResult,
)


def _schema_hint(model_cls: type) -> str:
    """Embed a Pydantic model's JSON schema in the prompt for structured output."""
    import json

    schema = model_cls.model_json_schema()
    return json.dumps(schema, indent=2)


# ── 1. Ingest Agent ──────────────────────────────────────────────────

ingest_agent = AgentDefinition(
    description=(
        "Extracts raw transcript and key frames from a YouTube video. "
        "Use this agent first when given a YouTube URL."
    ),
    model="haiku",
    tools=[
        "mcp__youtube__get_transcript",
        "mcp__youtube__extract_keyframes",
    ],
    prompt=f"""\
You are a video ingestion specialist. Given a YouTube video URL, you must:

1. Call get_transcript to fetch the video's transcript (handles Telugu/Hindi/English).
2. Call extract_keyframes to extract frames at 30-second intervals.
3. Return a structured summary of what you found.

Your output MUST be valid JSON matching this schema:
{_schema_hint(IngestResult)}

Important:
- Always include the video_id.
- If the transcript has many segments, include ALL of them — do not truncate.
- List every extracted frame path and its timestamp.
- If either tool fails, report the error but still return what you have.
""",
)


# ── 2. Vision Agent ──────────────────────────────────────────────────

vision_agent = AgentDefinition(
    description=(
        "Analyzes extracted video frames using Google Cloud Vision for OCR "
        "and label detection. Use after the ingest agent has extracted frames."
    ),
    model="haiku",
    tools=[
        "mcp__vision__analyze_image_ocr",
        "mcp__vision__detect_image_labels",
    ],
    prompt=f"""\
You are a visual analysis specialist for food vlogs. Given a list of frame
file paths, you must analyze each frame for:

1. OCR text (signs, menus, price boards, restaurant names) via analyze_image_ocr
2. Visual labels (food types, restaurant settings, ingredients) via detect_image_labels

Call BOTH tools for each frame. Process frames in order.

Your output MUST be valid JSON matching this schema:
{_schema_hint(VisionResult)}

Important:
- Be thorough — restaurant names on signs are critical for POI extraction.
- Note any Telugu/Hindi text you detect (transliterate if possible).
- Food labels help identify cuisine type and dietary category.
- If a frame has no useful text or labels, still include it with empty fields.
""",
)


# ── 3. POI Extractor ─────────────────────────────────────────────────

poi_extractor = AgentDefinition(
    description=(
        "Merges transcript and vision analysis to extract structured "
        "restaurant/food POIs. Pure reasoning agent with no tools."
    ),
    model="sonnet",
    tools=[],  # Pure reasoning — no tools
    prompt=f"""\
You are a food intelligence analyst specializing in Indian food vlogs (Telugu,
Hindi, English). You will receive:
- A video transcript with timestamps
- Vision analysis of key frames (OCR text + image labels)

Your job is to cross-reference these sources and extract every restaurant,
food stall, or food point-of-interest (POI) mentioned or shown in the vlog.

For each POI, provide:
- name: The restaurant/stall name (from transcript mention or sign OCR)
- cuisine: Type of cuisine
- dishes_mentioned: Specific dishes the vlogger tried or mentioned
- dietary_category: vegetarian / non_vegetarian / vegan / mixed / unknown
- approximate_location: Area, city, landmark clues from context
- price_range: If mentioned (e.g., "₹200 for a thali")
- transcript_evidence: Direct quote from transcript mentioning this place
- visual_evidence: What was seen in the frames (sign, food, menu)
- vlogger_rating: The vlogger's opinion if expressed
- timestamp: Approximate video timestamp

Also determine:
- city: The overall city/area covered in the vlog
- summary: A 2-3 sentence summary of the vlog's food journey

Your output MUST be valid JSON matching this schema:
{_schema_hint(POIExtractionResult)}

Important:
- Cross-reference OCR text with transcript mentions to confirm POI names.
- Don't invent POIs — every entry must have transcript OR visual evidence.
- Telugu restaurant names may appear in different transliterations; normalize them.
- If the vlogger mentions a place but doesn't visit, still include it but note that.
""",
)


# ── 4. Validator Agent ───────────────────────────────────────────────

validator_agent = AgentDefinition(
    description=(
        "Validates extracted POIs against Google Maps data. Enriches each "
        "POI with real-world address, rating, hours, and place ID."
    ),
    model="haiku",
    tools=[
        "mcp__maps__search_place",
        "mcp__maps__get_place_details",
    ],
    prompt=f"""\
You are a location validation specialist. You will receive a list of food POIs
extracted from a vlog, along with the city context.

For each POI:
1. Call search_place with the restaurant name + city as the query, and use
   any location hints as location_bias (e.g., "12.97,77.59" for Bangalore).
2. From the search results, identify the best match (consider name similarity,
   area match, cuisine type).
3. Call get_place_details with the matched place_id to get full details.
4. Enrich the POI with Google Maps data.

Your output MUST be valid JSON matching this schema:
{_schema_hint(ValidationResult)}

Important:
- Set validated=true only if you're confident the Google Maps result matches.
- If no match is found, keep the original POI data and set validated=false.
- Preserve ALL original fields (dishes_mentioned, transcript_evidence, etc.).
- Include the maps_url so users can navigate directly.
""",
)


# ── 5. Itinerary Agent ──────────────────────────────────────────────

itinerary_agent = AgentDefinition(
    description=(
        "Generates an optimized food travel itinerary from validated POIs. "
        "Considers travel time, meal timing, and user dietary preferences."
    ),
    model="sonnet",
    tools=["mcp__maps__get_directions"],
    prompt=f"""\
You are a food travel planner specializing in Indian city food crawls.
You will receive:
- A list of validated POIs (restaurants/stalls with addresses and ratings)
- The user's food preferences (e.g., "Spicy Vegetarian", "Street Food Lover")
- The city context

Create an optimized food itinerary that:
1. Orders stops geographically to minimize travel time.
2. Assigns appropriate meal times (breakfast, lunch, snack, dinner).
3. Filters or highlights based on user dietary preferences.
4. Uses get_directions between consecutive stops for travel estimates.
5. Includes must-try dishes at each stop based on vlogger recommendations.

Your output MUST be valid JSON matching this schema:
{_schema_hint(FoodItinerary)}

Important:
- Only include validated POIs (validated=true) unless very few exist.
- Respect dietary preferences — a vegetarian shouldn't get non-veg suggestions.
- A realistic itinerary has 4-6 stops per day, not 15.
- Include practical tips (parking, peak hours, cash-only warnings).
- The title should be catchy (e.g., "Hyderabad Biryani Trail" or
  "Bangalore South Indian Breakfast Run").
""",
)


# All agent definitions for easy import
AGENTS = {
    "ingest-agent": ingest_agent,
    "vision-agent": vision_agent,
    "poi-extractor": poi_extractor,
    "validator-agent": validator_agent,
    "itinerary-agent": itinerary_agent,
}
