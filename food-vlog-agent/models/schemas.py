"""Pydantic v2 models defining the contract between agents."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

# ── Ingest Agent ──────────────────────────────────────────────────────


class TranscriptSegment(BaseModel):
    """A single segment of the video transcript."""

    text: str
    start: float = Field(description="Start time in seconds")
    duration: float = Field(description="Duration in seconds")


class KeyFrame(BaseModel):
    """A key frame extracted from the video."""

    path: str = Field(description="File path to the extracted frame image")
    timestamp: float = Field(description="Timestamp in seconds")


class IngestResult(BaseModel):
    """Output of the ingest agent."""

    video_id: str
    title: str = ""
    segments: list[TranscriptSegment] = []
    keyframes: list[KeyFrame] = []


# ── Vision Agent ──────────────────────────────────────────────────────


class VisionAnalysis(BaseModel):
    """Vision analysis for a single frame."""

    frame_path: str
    timestamp: float
    ocr_text: str = Field(default="", description="Text detected via OCR")
    labels: list[str] = Field(default_factory=list, description="Labels detected in the image")


class VisionResult(BaseModel):
    """Output of the vision agent."""

    analyses: list[VisionAnalysis] = []


# ── POI Extractor ─────────────────────────────────────────────────────


class DietaryCategory(str, Enum):
    """Dietary classification for a food item or restaurant."""

    VEGETARIAN = "vegetarian"
    NON_VEGETARIAN = "non_vegetarian"
    VEGAN = "vegan"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class POI(BaseModel):
    """A point-of-interest (restaurant/food stall) extracted from the vlog."""

    name: str
    cuisine: str = ""
    dishes_mentioned: list[str] = Field(default_factory=list)
    dietary_category: DietaryCategory = DietaryCategory.UNKNOWN
    approximate_location: str = Field(
        default="", description="Location hint from the vlog (area, city, landmark)"
    )
    price_range: str = ""
    transcript_evidence: str = Field(
        default="",
        description="Relevant transcript snippet that mentions this POI",
    )
    visual_evidence: str = Field(
        default="",
        description="Description of visual evidence (sign, menu board, etc.)",
    )
    vlogger_rating: str = Field(
        default="",
        description="Vlogger's opinion/rating if mentioned",
    )
    timestamp: float | None = Field(
        default=None, description="Approximate video timestamp in seconds"
    )


class POIExtractionResult(BaseModel):
    """Output of the POI extractor agent."""

    pois: list[POI] = []
    city: str = Field(default="", description="City identified from the vlog")
    summary: str = Field(default="", description="Brief summary of the food vlog content")


# ── Validator Agent ───────────────────────────────────────────────────


class ValidatedPOI(BaseModel):
    """A POI enriched with Google Maps data."""

    # Original POI fields
    name: str
    cuisine: str = ""
    dishes_mentioned: list[str] = Field(default_factory=list)
    dietary_category: DietaryCategory = DietaryCategory.UNKNOWN
    transcript_evidence: str = ""
    visual_evidence: str = ""
    vlogger_rating: str = ""
    timestamp: float | None = None

    # Google Maps enrichment
    place_id: str = Field(default="", description="Google Maps place ID")
    address: str = ""
    google_rating: float | None = None
    total_ratings: int | None = None
    price_level: int | None = Field(default=None, description="Google price level 0-4")
    opening_hours: list[str] = Field(default_factory=list)
    maps_url: str = ""
    validated: bool = Field(
        default=False,
        description="Whether this POI was confirmed on Google Maps",
    )


class ValidationResult(BaseModel):
    """Output of the validator agent."""

    validated_pois: list[ValidatedPOI] = []
    city: str = ""


# ── Itinerary Agent ──────────────────────────────────────────────────


class ItineraryStop(BaseModel):
    """A single stop in the food itinerary."""

    order: int
    poi: ValidatedPOI
    recommended_time: str = Field(default="", description="e.g., 'Lunch, 12:00-13:00'")
    travel_from_previous: str = Field(
        default="", description="Travel time/distance from previous stop"
    )
    must_try_dishes: list[str] = Field(default_factory=list)
    notes: str = ""


class FoodItinerary(BaseModel):
    """Final output: an optimized food travel itinerary."""

    title: str
    city: str
    food_preferences: str = ""
    stops: list[ItineraryStop] = []
    total_estimated_time: str = ""
    tips: list[str] = Field(
        default_factory=list,
        description="General tips for the food crawl",
    )
    source_video: str = Field(default="", description="Original YouTube video URL")
