"""Orchestrator: wires MCP servers, agents, and the outer-loop pipeline.

The orchestrator uses Claude Sonnet as the outer loop, dispatching to
5 specialized sub-agents via the Task tool. Each sub-agent has its own
model, tools, and system prompt — but cannot spawn further sub-agents.
"""

from __future__ import annotations

import asyncio
import os

from claude_agent_sdk import ClaudeAgentOptions, query

from agents.definitions import AGENTS
from config import MAX_BUDGET_USD
from tools.maps_tools import create_maps_server
from tools.vision_tools import create_vision_server
from tools.youtube_tools import create_youtube_server

# Clear CLAUDECODE so the child CLI doesn't refuse to start
# when invoked from inside a Claude Code terminal session.
os.environ.pop("CLAUDECODE", None)

SYSTEM_PROMPT = """\
You are a food vlog processing orchestrator. Your job is to take a YouTube
food vlog URL and the user's food preferences, then run a 5-step pipeline
to produce a curated food travel itinerary.

## Pipeline Steps

Execute these steps IN ORDER, passing relevant context from each step to
the next via natural language:

### Step 1 → ingest-agent
Give it the YouTube URL. It will return the video transcript and extracted
key frame file paths.

### Step 2 → vision-agent
Give it the list of frame file paths from Step 1. It will return OCR text
and image labels for each frame.

### Step 3 → poi-extractor
Give it the full transcript from Step 1 AND the vision analysis from Step 2.
It will return a structured list of restaurant/food POIs with evidence.

### Step 4 → validator-agent
Give it the POI list and city from Step 3. It will validate each POI against
Google Maps and return enriched data (address, rating, hours, maps URL).

### Step 5 → itinerary-agent
Give it the validated POIs from Step 4 AND the user's food preferences.
It will return an optimized food travel itinerary.

## Important Rules

- Execute steps sequentially — each step depends on the previous one.
- Pass ALL relevant data between steps (don't summarize away details).
- If a step fails or returns partial data, continue with what you have.
- After Step 5, present the final itinerary to the user in a clear,
  readable format — not raw JSON.
- Include the source video URL in the final output.
- ONLY use the Task tool to dispatch to sub-agents. Do NOT use Read,
  Bash, WebFetch, or any other tool directly. All data gathering must
  happen through the sub-agents. Do NOT read files, do NOT run commands,
  do NOT try to "help" the sub-agents — just dispatch and pass data along.
- Keep status updates brief — one short sentence per step, not paragraphs.

## Output Format

After the pipeline completes, present the itinerary with:
1. A catchy title
2. City and food preference context
3. Each stop with: name, address, must-try dishes, travel time, notes
4. Total estimated time
5. Practical tips
"""


def build_options(dry_run: bool = False) -> ClaudeAgentOptions:
    """Build ClaudeAgentOptions with all MCP servers and agent definitions.

    Args:
        dry_run: If True, use mock MCP servers (no API keys needed).
    """
    if dry_run:
        from tools.mock_data import (
            create_mock_maps_server,
            create_mock_vision_server,
            create_mock_youtube_server,
        )

        mcp_servers = {
            "youtube": create_mock_youtube_server(),
            "vision": create_mock_vision_server(),
            "maps": create_mock_maps_server(),
        }
    else:
        mcp_servers = {
            "youtube": create_youtube_server(),
            "vision": create_vision_server(),
            "maps": create_maps_server(),
        }

    return ClaudeAgentOptions(
        model="sonnet",
        allowed_tools=["Task"],  # Orchestrator only dispatches to sub-agents
        system_prompt=SYSTEM_PROMPT,
        mcp_servers=mcp_servers,
        agents=AGENTS,
        max_turns=10,
        max_budget_usd=MAX_BUDGET_USD,
        permission_mode="bypassPermissions",
    )


async def _held_message(text: str, done: asyncio.Event):
    """Yield one user message, then block until *done* is set.

    The SDK's ``stream_input`` closes stdin once the async iterable is
    exhausted **and** the first ``result`` message arrives.  With sub-agents
    the first result belongs to a sub-agent, not the final pipeline — so
    stdin gets closed too early and the orchestrator loses its MCP channel.

    By keeping this generator alive until the outer ``run_pipeline`` loop
    finishes, ``stream_input`` never reaches the ``end_input()`` call while
    the orchestrator still needs it.
    """
    yield {
        "type": "user",
        "session_id": "",
        "message": {"role": "user", "content": text},
        "parent_tool_use_id": None,
    }
    # Hold the generator open — stream_input won't close stdin until
    # we return, regardless of how many sub-agent results arrive.
    await done.wait()


async def run_pipeline(video_url: str, preferences: str, dry_run: bool = False):
    """Run the full food vlog processing pipeline.

    Yields messages from the orchestrator as they stream in.
    """
    options = build_options(dry_run=dry_run)

    prompt = (
        f"Process this food vlog and create a food travel itinerary.\n\n"
        f"YouTube URL: {video_url}\n"
        f"Food Preferences: {preferences}\n\n"
        f"Execute the full 5-step pipeline now."
    )

    done = asyncio.Event()
    try:
        async for message in query(prompt=_held_message(prompt, done), options=options):
            yield message
    finally:
        done.set()
