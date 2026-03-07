"""MCP tools for YouTube video ingestion: transcript + key frame extraction."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from claude_agent_sdk import create_sdk_mcp_server, tool

from config import KEYFRAME_INTERVAL_SECONDS, OUTPUT_DIR, VIDEO_FORMAT


def _extract_video_id(url: str) -> str:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r"(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"(?:embed/)([a-zA-Z0-9_-]{11})",
        r"(?:shorts/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from: {url}")


# ── Core logic (directly testable) ───────────────────────────────────


async def _get_transcript_impl(video_url: str) -> dict:
    """Fetch transcript — separated from @tool wrapper for testability."""
    video_id = _extract_video_id(video_url)

    from youtube_transcript_api import YouTubeTranscriptApi

    api = YouTubeTranscriptApi()

    # Try fetching transcript with language fallback cascade
    transcript_entries = None
    for language_codes in [["en"], ["te"], ["hi"]]:
        try:
            transcript_entries = api.fetch(video_id, languages=language_codes)
            break
        except Exception:
            continue

    # Last resort: any available transcript, translated to English
    if transcript_entries is None:
        try:
            transcript_list = api.list(video_id)
            for t in transcript_list:
                transcript_entries = t.translate("en").fetch()
                break
        except Exception:
            pass

    if not transcript_entries:
        return {"error": "No transcript available", "video_id": video_id}

    # FetchedTranscriptSnippet has .text, .start, .duration attributes
    segments = [
        {"text": e.text, "start": e.start, "duration": e.duration}
        for e in transcript_entries
    ]
    return {"video_id": video_id, "segment_count": len(segments), "segments": segments}


async def _extract_keyframes_impl(
    video_url: str, interval: int = KEYFRAME_INTERVAL_SECONDS, output_dir: Path = OUTPUT_DIR
) -> dict:
    """Extract key frames — separated from @tool wrapper for testability."""
    video_id = _extract_video_id(video_url)

    frames_dir = output_dir / video_id / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    existing = sorted(frames_dir.glob("frame_*.jpg"))
    if existing:
        frames = [{"path": str(f), "timestamp": i * interval} for i, f in enumerate(existing)]
        return {
            "video_id": video_id,
            "frame_count": len(frames),
            "frames": frames,
            "cached": True,
        }

    video_path = output_dir / video_id / "video.mp4"
    subprocess.run(
        [
            "yt-dlp",
            "--format",
            VIDEO_FORMAT,
            "--output",
            str(video_path),
            "--no-playlist",
            "--quiet",
            video_url,
        ],
        check=True,
        capture_output=True,
    )

    subprocess.run(
        [
            "ffmpeg",
            "-i",
            str(video_path),
            "-vf",
            f"fps=1/{interval}",
            "-q:v",
            "5",
            str(frames_dir / "frame_%04d.jpg"),
            "-y",
            "-loglevel",
            "error",
        ],
        check=True,
        capture_output=True,
    )

    video_path.unlink(missing_ok=True)

    extracted = sorted(frames_dir.glob("frame_*.jpg"))
    frames = [{"path": str(f), "timestamp": i * interval} for i, f in enumerate(extracted)]
    return {
        "video_id": video_id,
        "frame_count": len(frames),
        "frames": frames,
        "cached": False,
    }


# ── @tool wrappers (thin, delegate to _impl) ─────────────────────────


@tool(
    "get_transcript",
    "Fetch the transcript of a YouTube video. Attempts English first, "
    "then falls back to Telugu-translated-to-English, then any auto-generated.",
    {"video_url": str},
)
async def get_transcript(args: dict) -> dict:
    data = await _get_transcript_impl(args["video_url"])
    return {"content": [{"type": "text", "text": json.dumps(data)}]}


@tool(
    "extract_keyframes",
    "Download a YouTube video at lowest quality and extract key frames "
    "at regular intervals using ffmpeg. Returns file paths to extracted frames.",
    {"video_url": str, "interval_seconds": int},
)
async def extract_keyframes(args: dict) -> dict:
    data = await _extract_keyframes_impl(
        args["video_url"],
        args.get("interval_seconds", KEYFRAME_INTERVAL_SECONDS),
    )
    return {"content": [{"type": "text", "text": json.dumps(data)}]}


def create_youtube_server():
    """Create the YouTube MCP server with transcript and keyframe tools."""
    return create_sdk_mcp_server(
        name="youtube",
        version="1.0.0",
        tools=[get_transcript, extract_keyframes],
    )
