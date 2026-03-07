"""Orchestrator: wires the kubernetes-mcp-server, agents, and the outer-loop pipeline.

The orchestrator uses Claude Sonnet as the outer loop, dispatching to
5 specialized sub-agents via the Task tool. Each sub-agent has its own
model, allowed tools, and system prompt — but cannot spawn further sub-agents.

Unlike the food-vlog-agent's fixed sequential pipeline, this orchestrator
dynamically decides which agents to invoke based on the user's query.
"""

from __future__ import annotations

import asyncio
import os
import shutil

from claude_agent_sdk import ClaudeAgentOptions, query

from agents.definitions import AGENTS
from config import KUBECONFIG, MAX_BUDGET_USD
from tools.mock_data import MOCK_SCENARIO

SYSTEM_PROMPT = """\
You are an SRE orchestrator for OpenShift/ROSA clusters running Open Data Hub (ODH).
You receive a user query about cluster health, workload issues, networking problems,
Helm releases, or requests for remediation. You dispatch to specialized sub-agents
to investigate and resolve the issue.

## Available Agents

- **cluster-agent**: Cluster-wide health (nodes, operators, version, context).
  Use this first for broad health checks or when you need cluster context.

- **workload-agent**: Pod and deployment troubleshooting (logs, events, status).
  Use this for CrashLoopBackOff, pending pods, OOMKilled, rollout issues.

- **networking-agent**: Route, Service, NetworkPolicy, Ingress diagnostics.
  Use this for connectivity issues, unreachable endpoints, route problems.

- **helm-agent**: Helm release status and management.
  Use this for chart deployment issues, version checks, install/uninstall.

- **remediation-agent**: Safe remediation actions (restart, scale, patch, delete).
  Use this ONLY after you have a clear diagnosis from other agents.

## Dispatch Strategy

1. Start with **cluster-agent** if the query is broad or you need context.
2. Use the most relevant agent for the specific problem domain.
3. You may invoke multiple agents sequentially — pass relevant findings
   from earlier agents as context to later ones.
4. ONLY invoke **remediation-agent** after diagnosis is established.
   Include the full diagnosis in your dispatch so it knows what to fix.
5. After all agents report, synthesize a final summary for the user.

## Important Rules

- Execute agents sequentially — pass context from each to the next.
- ONLY use the Task tool to dispatch to sub-agents. Do NOT use any other
  tools directly.
- Keep status updates brief — one short sentence per agent dispatch.
- If a namespace is mentioned in the query, pass it to the relevant agents.
- Common ODH namespaces: redhat-ods-operator, redhat-ods-applications,
  redhat-ods-monitoring, opendatahub.

## Output Format

After investigation, present findings with:
1. Brief summary of what was found
2. Root cause (if identified)
3. Actions taken (if remediation was performed)
4. Recommendations for follow-up
"""


def _find_k8s_mcp_binary() -> str:
    """Locate the kubernetes-mcp-server binary."""
    binary = shutil.which("kubernetes-mcp-server")
    if binary:
        return binary
    raise FileNotFoundError(
        "kubernetes-mcp-server not found. Install it via:\n"
        "  pip install kubernetes-mcp-server\n"
        "  # or: npm install -g kubernetes-mcp-server\n"
        "  # or: brew install containers/kubernetes-mcp-server/kubernetes-mcp-server"
    )


def build_options(dry_run: bool = False) -> ClaudeAgentOptions:
    """Build ClaudeAgentOptions with the kubernetes-mcp-server and agent definitions.

    Args:
        dry_run: If True, start kubernetes-mcp-server with --cluster-provider disabled
                 so it doesn't need a live cluster.
    """
    # Clear CLAUDECODE so the child CLI doesn't refuse to start
    # when invoked from inside a Claude Code terminal session.
    os.environ.pop("CLAUDECODE", None)

    binary = _find_k8s_mcp_binary()

    k8s_args = [
        "--toolsets", "core,config,helm",
    ]

    if dry_run:
        k8s_args.extend(["--cluster-provider", "disabled"])
    else:
        k8s_args.extend(["--kubeconfig", KUBECONFIG])

    system_prompt = SYSTEM_PROMPT
    if dry_run:
        system_prompt += "\n\n" + MOCK_SCENARIO

    return ClaudeAgentOptions(
        model="sonnet",
        allowed_tools=["Task"],
        system_prompt=system_prompt,
        mcp_servers={
            "k8s": {
                "command": binary,
                "args": k8s_args,
            },
        },
        agents=AGENTS,
        max_turns=15,
        max_budget_usd=MAX_BUDGET_USD,
        permission_mode="bypassPermissions",
    )


async def _held_message(text: str, done: asyncio.Event):
    """Yield one user message, then block until *done* is set.

    The SDK's ``stream_input`` closes stdin once the async iterable is
    exhausted **and** the first ``result`` message arrives. With sub-agents
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
    await done.wait()


async def run_pipeline(user_query: str, namespace: str = "", dry_run: bool = False):
    """Run the SRE investigation pipeline.

    Yields messages from the orchestrator as they stream in.
    """
    options = build_options(dry_run=dry_run)

    prompt = f"Investigate the following SRE query:\n\n{user_query}"
    if namespace:
        prompt += f"\n\nFocus on namespace: {namespace}"

    done = asyncio.Event()
    try:
        async for message in query(prompt=_held_message(prompt, done), options=options):
            yield message
    finally:
        done.set()
