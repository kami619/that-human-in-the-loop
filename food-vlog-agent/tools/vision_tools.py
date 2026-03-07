"""MCP tools for Google Cloud Vision: OCR and label detection on frames."""

from __future__ import annotations

import json

from claude_agent_sdk import create_sdk_mcp_server, tool

from config import GOOGLE_APPLICATION_CREDENTIALS

# ── Cached client ───────────────────────────────────────────────────

_vision_client = None


def _get_vision_client():
    """Return a cached Vision client using the explicit service account key.

    Avoids ADC silently picking up a different GCP project from
    ``~/.config/gcloud/application_default_credentials.json``.
    """
    global _vision_client
    if _vision_client is None:
        from google.cloud import vision
        from google.oauth2 import service_account

        if GOOGLE_APPLICATION_CREDENTIALS:
            creds = service_account.Credentials.from_service_account_file(
                GOOGLE_APPLICATION_CREDENTIALS
            )
            _vision_client = vision.ImageAnnotatorClient(credentials=creds)
        else:
            _vision_client = vision.ImageAnnotatorClient()
    return _vision_client


def _load_image(image_path: str):
    """Read an image file and return a Vision Image object."""
    from google.cloud import vision

    with open(image_path, "rb") as f:
        content = f.read()
    return vision.Image(content=content)


# ── Core logic (directly testable) ───────────────────────────────────


async def _analyze_image_ocr_impl(image_path: str) -> dict:
    """Perform OCR — separated from @tool wrapper for testability."""
    client = _get_vision_client()
    response = client.text_detection(image=_load_image(image_path))

    if response.error.message:
        return {"error": response.error.message, "image_path": image_path}

    texts = [
        {"description": text.description, "confidence": getattr(text, "confidence", None)}
        for text in response.text_annotations[:10]
    ]

    full_text = texts[0]["description"] if texts else ""

    return {
        "image_path": image_path,
        "full_text": full_text,
        "annotations": texts[1:],
    }


async def _detect_image_labels_impl(image_path: str) -> dict:
    """Detect labels — separated from @tool wrapper for testability."""
    client = _get_vision_client()
    response = client.label_detection(image=_load_image(image_path))

    if response.error.message:
        return {"error": response.error.message, "image_path": image_path}

    labels = [
        {"description": label.description, "score": round(label.score, 3)}
        for label in response.label_annotations
    ]

    return {"image_path": image_path, "labels": labels}


# ── @tool wrappers ───────────────────────────────────────────────────


@tool(
    "analyze_image_ocr",
    "Perform OCR (text detection) on an image file. Reads signs, menus, "
    "price boards, and other text visible in food vlog frames.",
    {"image_path": str},
)
async def analyze_image_ocr(args: dict) -> dict:
    data = await _analyze_image_ocr_impl(args["image_path"])
    return {"content": [{"type": "text", "text": json.dumps(data)}]}


@tool(
    "detect_image_labels",
    "Detect labels (objects, food types, settings) in an image file. "
    "Identifies food items, restaurant environments, and scene context.",
    {"image_path": str},
)
async def detect_image_labels(args: dict) -> dict:
    data = await _detect_image_labels_impl(args["image_path"])
    return {"content": [{"type": "text", "text": json.dumps(data)}]}


def create_vision_server():
    """Create the Vision MCP server with OCR and label detection tools."""
    return create_sdk_mcp_server(
        name="vision",
        version="1.0.0",
        tools=[analyze_image_ocr, detect_image_labels],
    )
