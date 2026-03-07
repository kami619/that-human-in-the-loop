"""CLI entry point for the food vlog processing pipeline.

Usage:
    uv run python main.py --url "https://youtube.com/watch?v=..." --preferences "Spicy Vegetarian"
    uv run python main.py --url "..." --preferences "..." --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from config import OUTPUT_DIR

console = Console()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Process a food vlog into a curated travel itinerary",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  python main.py --url "https://youtube.com/watch?v=abc123" '
            '--preferences "Spicy Vegetarian"\n'
            '  python main.py --url "https://youtu.be/abc123" --dry-run'
        ),
    )
    parser.add_argument(
        "--url",
        required=True,
        help="YouTube video URL",
    )
    parser.add_argument(
        "--preferences",
        default="All food types",
        help='Food preferences (e.g., "Spicy Vegetarian", "Street Food")',
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without API calls (uses mock responses for demo)",
    )
    return parser.parse_args()


def validate_url(url: str) -> str:
    """Validate that the URL looks like a YouTube video URL."""
    patterns = [
        r"youtube\.com/watch\?v=",
        r"youtu\.be/",
        r"youtube\.com/embed/",
        r"youtube\.com/shorts/",
    ]
    if not any(re.search(p, url) for p in patterns):
        console.print("[red]Error:[/red] Not a valid YouTube URL")
        sys.exit(1)
    return url


def extract_video_id(url: str) -> str:
    """Extract video ID for output directory naming."""
    match = re.search(r"(?:v=|/v/|youtu\.be/|embed/|shorts/)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else "unknown"


async def stream_pipeline(url: str, preferences: str, dry_run: bool) -> str | None:
    """Run the orchestrator pipeline and stream output to the console."""
    from claude_agent_sdk import (
        AssistantMessage,
        CLIConnectionError,
        ResultMessage,
        TextBlock,
        ToolUseBlock,
    )

    from orchestrator import run_pipeline

    collected_text = []

    console.print()
    console.print(
        Panel(
            f"[bold cyan]Food Vlog → Itinerary Pipeline[/bold cyan]\n\n"
            f"[dim]URL:[/dim]         {url}\n"
            f"[dim]Preferences:[/dim] {preferences}\n"
            f"[dim]Mode:[/dim]        {'DRY RUN' if dry_run else 'LIVE'}",
            title="🍛 Food Vlog Agent",
            border_style="cyan",
        )
    )
    console.print()

    step_names = {
        "ingest-agent": "Step 1/5: Ingesting video",
        "vision-agent": "Step 2/5: Analyzing frames",
        "poi-extractor": "Step 3/5: Extracting POIs",
        "validator-agent": "Step 4/5: Validating places",
        "itinerary-agent": "Step 5/5: Building itinerary",
    }

    try:
        async for message in run_pipeline(url, preferences, dry_run=dry_run):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock) and block.text.strip():
                        collected_text.append(block.text)
                        console.print(Markdown(block.text))
                    elif isinstance(block, ToolUseBlock):
                        if block.name == "Task" and isinstance(block.input, dict):
                            agent = block.input.get("agent", "")
                            label = step_names.get(agent, f"Running {agent}")
                            console.print(f"\n[bold yellow]⟩[/bold yellow] {label}…")

            elif isinstance(message, ResultMessage):
                console.print()
                console.print(
                    Panel(
                        f"[green]Pipeline complete[/green]\n"
                        f"[dim]Cost:[/dim]  ${getattr(message, 'total_cost_usd', 0):.4f}\n"
                        f"[dim]Turns:[/dim] {getattr(message, 'num_turns', '?')}",
                        title="Done",
                        border_style="green",
                    )
                )
    except BaseExceptionGroup as eg:
        # SDK bug: _handle_control_request races with transport shutdown,
        # raising CLIConnectionError inside the task group. Suppress those
        # and re-raise anything else.
        _, rest = eg.split(lambda e: isinstance(e, CLIConnectionError))
        if rest:
            raise rest

    return "\n".join(collected_text) if collected_text else None


def save_output(video_id: str, text: str) -> Path:
    """Save the final itinerary text to the output directory."""
    out_dir = OUTPUT_DIR / video_id
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / "itinerary.md"
    out_path.write_text(text, encoding="utf-8")
    return out_path


async def main():
    args = parse_args()
    url = validate_url(args.url)
    video_id = extract_video_id(url)

    result_text = await stream_pipeline(url, args.preferences, args.dry_run)

    if result_text:
        out_path = save_output(video_id, result_text)
        console.print(f"\n[dim]Saved to:[/dim] {out_path}")
    else:
        console.print("\n[yellow]No output was generated.[/yellow]")


if __name__ == "__main__":
    asyncio.run(main())
