"""CLI entry point for the ODH SRE agent.

Usage:
    uv run python main.py --query "Why are pods crashlooping in redhat-ods-applications?"
    uv run python main.py --query "..." --namespace redhat-ods-applications
    uv run python main.py --query "..." --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

console = Console()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SRE agent for OpenShift/ROSA clusters running Open Data Hub",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  python main.py --query "Why are pods crashlooping in redhat-ods-applications?"\n'
            '  python main.py --query "Check cluster health" --dry-run\n'
            '  python main.py --query "Scale odh-dashboard" --namespace redhat-ods-applications'
        ),
    )
    parser.add_argument(
        "--query",
        required=True,
        help="SRE query to investigate",
    )
    parser.add_argument(
        "--namespace",
        default=None,
        help="Kubernetes namespace to focus on (optional)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run with mock data (no live cluster needed)",
    )
    return parser.parse_args()


async def stream_pipeline(query_text: str, namespace: str, dry_run: bool) -> None:
    """Run the orchestrator pipeline and stream output to the console."""
    from claude_agent_sdk import (
        AssistantMessage,
        CLIConnectionError,
        ResultMessage,
        TextBlock,
        ToolUseBlock,
    )

    from orchestrator import run_pipeline

    agent_labels = {
        "cluster-agent": "Cluster Health",
        "workload-agent": "Workload Diagnostics",
        "networking-agent": "Networking",
        "helm-agent": "Helm Releases",
        "remediation-agent": "Remediation",
    }

    console.print()
    console.print(
        Panel(
            f"[bold cyan]ODH SRE Agent[/bold cyan]\n\n"
            f"[dim]Query:[/dim]     {query_text}\n"
            f"[dim]Namespace:[/dim] {namespace or '(all)'}\n"
            f"[dim]Mode:[/dim]     {'DRY RUN' if dry_run else 'LIVE'}",
            title="SRE Investigation",
            border_style="cyan",
        )
    )
    console.print()

    try:
        async for message in run_pipeline(query_text, namespace, dry_run=dry_run):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock) and block.text.strip():
                        console.print(Markdown(block.text))
                    elif (
                        isinstance(block, ToolUseBlock)
                        and block.name == "Task"
                        and isinstance(block.input, dict)
                    ):
                        agent = block.input.get("agent", "")
                        label = agent_labels.get(agent, f"Running {agent}")
                        console.print(
                            f"\n[bold yellow]>[/bold yellow] {label}..."
                        )

            elif isinstance(message, ResultMessage):
                console.print()
                console.print(
                    Panel(
                        f"[green]Investigation complete[/green]\n"
                        f"[dim]Cost:[/dim]  ${getattr(message, 'total_cost_usd', 0):.4f}\n"
                        f"[dim]Turns:[/dim] {getattr(message, 'num_turns', '?')}",
                        title="Done",
                        border_style="green",
                    )
                )
    except BaseExceptionGroup as eg:
        _, rest = eg.split(lambda e: isinstance(e, CLIConnectionError))
        if rest:
            raise rest from eg
    except Exception as exc:
        error_msg = str(exc)
        if "exit code" in error_msg:
            console.print()
            console.print(
                Panel(
                    f"[red]{error_msg}[/red]",
                    title="Error",
                    border_style="red",
                )
            )
            sys.exit(1)
        raise


async def main():
    from config import DEFAULT_NAMESPACE

    args = parse_args()
    namespace = args.namespace if args.namespace is not None else DEFAULT_NAMESPACE
    await stream_pipeline(args.query, namespace, args.dry_run)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted.[/dim]")
        sys.exit(130)
