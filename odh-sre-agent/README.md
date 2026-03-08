# ODH SRE Agent

A multi-agent SRE system for ROSA OpenShift clusters running Open Data Hub (ODH). Investigates cluster health, workload issues, networking problems, and performs safe remediation.

Built with the [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python) and [kubernetes-mcp-server](https://github.com/containers/kubernetes-mcp-server).

## Architecture

```
User Query (e.g., "Why are pods crashlooping in redhat-ods-applications?")
        |
        v
+----------------------------------+
|  ORCHESTRATOR (Sonnet)            |  <-- Outer Loop: dispatches via Task tool
|  Dynamic routing based on query   |
+------------+---------------------+
             |
             |  Single MCP server: kubernetes-mcp-server
             |  (shared across all agents, each gets allowed_tools subset)
             |
             +---> [cluster-agent (Haiku)]
             |     Tools: nodes_top, nodes_stats_summary, nodes_log,
             |       namespaces_list, projects_list, resources_list/get,
             |       configuration_contexts_list, configuration_view
             |
             +---> [workload-agent (Haiku)]
             |     Tools: pods_list, pods_get, pods_log, pods_top,
             |       pods_exec, resources_list/get, events_list
             |
             +---> [networking-agent (Haiku)]
             |     Tools: resources_list, resources_get, events_list
             |
             +---> [helm-agent (Haiku)]
             |     Tools: helm_list, helm_install, helm_uninstall,
             |       resources_list/get
             |
             +---> [remediation-agent (Sonnet)]
                   Tools: pods_delete, pods_run, pods_exec,
                     resources_create_or_update, resources_delete,
                     resources_scale, helm_install/uninstall
```

Sub-agents cannot spawn sub-agents. The orchestrator decides which agents to invoke and in what order based on the user's query.

## Prerequisites

| Requirement | Purpose | Install |
|-------------|---------|---------|
| `kubernetes-mcp-server` | K8s/OpenShift MCP tools | `pip install kubernetes-mcp-server` |
| `uv` | Python dependency management | `brew install uv` |
| `ANTHROPIC_API_KEY` | Claude Agent SDK | [console.anthropic.com](https://console.anthropic.com) |
| Kubeconfig | Cluster access (live mode only) | `oc login` or `rosa create admin` |

## Setup

```bash
cd odh-sre-agent
cp .env.example .env
# Fill in ANTHROPIC_API_KEY in .env

make install
make test
```

## Usage

### Live mode (requires cluster access)

```bash
uv run python main.py \
  --query "Why are pods crashlooping in redhat-ods-applications?"

uv run python main.py \
  --query "Check cluster health" \
  --namespace redhat-ods-applications
```

### Dry-run mode (no cluster needed)

Uses mock data simulating an ODH cluster with multiple issues:

```bash
make dry-run

# or directly:
uv run python main.py \
  --query "Why are pods crashlooping in redhat-ods-applications?" \
  --dry-run
```

## Testing

Four levels of testing, each requiring progressively more infrastructure:

### Level 1: Unit tests (no cluster, no API key)

Validates schemas, agent definitions, orchestrator config, and tool boundaries. Fast and offline.

```bash
make test      # 38 tests, runs in <1s
make check     # lint + tests
```

**What it exercises:** Pydantic model serialization, agent tool prefixes (`mcp__k8s__`), read-only agents don't have write tools, orchestrator system prompt contains required agent names, binary lookup error handling.

### Level 2: Dry-run (needs `ANTHROPIC_API_KEY`, no cluster)

Runs the full multi-agent pipeline with real Claude API calls. The `kubernetes-mcp-server` starts with `--cluster-provider disabled` and the orchestrator gets mock cluster data (OOMKilled pod, Pending PVC, degraded operator) injected into its system prompt. Agents reason over the mock data and produce a real investigation report.

```bash
cp .env.example .env
# Set ANTHROPIC_API_KEY in .env

make dry-run
```

**What it exercises:** Full orchestrator loop, agent dispatch via Task tool, inter-agent context passing, Claude reasoning over cluster scenarios, Rich CLI output.

**Cost:** ~$0.10–0.30 per run (Sonnet orchestrator + Haiku sub-agents).

**Requires:** `ANTHROPIC_API_KEY` and `kubernetes-mcp-server` on PATH (`pip install kubernetes-mcp-server`).

### Level 3: kind cluster (needs Podman/Docker, no cloud cluster)

Runs the agent against a local [kind](https://kind.sigs.k8s.io/) cluster with a real ODH installation. The setup script clones the upstream [odh-gitops](https://github.com/opendatahub-io/odh-gitops/tree/main/charts/odh-rhoai) Helm chart, installs OLM + the ODH operator, and injects deliberate faults for the agent to diagnose.

```bash
# Create cluster, install OLM + ODH, inject faults
make kind-up

# Run the agent
make kind-test

# Tear down
make kind-down
```

**What gets deployed:**
- Real ODH CRDs (23) extracted from the [operator bundle image](https://quay.io/opendatahub/opendatahub-operator-bundle) on quay.io
- Real `DataScienceCluster` and `DSCInitialization` CRs rendered from the upstream [odh-gitops chart](https://github.com/opendatahub-io/odh-gitops/tree/main/charts/odh-rhoai) via `helm template`
- Simulated workloads (Deployments, Services) matching ODH component names
- Faults: OOMKilled dashboard pods, Pending pipelines pod, unbound PVC

**What it exercises:** End-to-end SRE workflow against real K8s API. Agents discover actual OOMKill events, Pending pods, and resource issues via `kubernetes-mcp-server` tool calls. CRDs and CRs are real — the agent can inspect `DataScienceCluster` and `DSCInitialization` resources.

**Limitations:** The ODH operator itself requires OpenShift (`config.openshift.io` APIs) and cannot run on kind. Workloads are simulated Deployments, not operator-reconciled. OpenShift-specific resources (Routes, ClusterOperators, Projects) won't exist.

**Cost:** ~$0.10–0.30 per run (Claude API); K8s API calls are free.

**Requires:** `ANTHROPIC_API_KEY`, `kubernetes-mcp-server`, `kind`, `kubectl`, `helm`, Podman (or Docker).

### Level 4: Live ROSA/OpenShift cluster

Runs against a real ROSA/OpenShift cluster. Agents call actual `kubernetes-mcp-server` tools that query the K8s API.

```bash
# Verify cluster access first
oc whoami
oc get nodes

uv run python main.py \
  --query "Check cluster health" \
  --namespace redhat-ods-applications
```

**What it exercises:** Full end-to-end SRE workflow against real cluster state with OpenShift-specific resources (Routes, ClusterOperators, Projects).

**Cost:** ~$0.10–0.30 per run (same Claude costs; K8s API calls are free).

**Requires:** `ANTHROPIC_API_KEY`, `kubernetes-mcp-server`, and active kubeconfig (`oc login` or `rosa create admin`).

## Project Structure

```
odh-sre-agent/
├── main.py                     # CLI entry point (--query, --namespace, --dry-run)
├── orchestrator.py             # Outer loop: Sonnet dispatches 5 agents via Task
├── config.py                   # Environment-based configuration
├── models/
│   └── schemas.py              # Pydantic v2 data models (ClusterHealth, WorkloadStatus, etc.)
├── agents/
│   └── definitions.py          # 5 AgentDefinition configs with allowed_tools subsets
├── tools/
│   └── mock_data.py            # Mock cluster scenario for --dry-run
├── tests/
│   ├── conftest.py
│   ├── test_schemas.py
│   ├── test_definitions.py
│   ├── test_orchestrator.py
│   └── test_config.py
├── test-fixtures/              # Config for kind cluster ODH install
│   ├── values-kind.yaml        # Helm values override (ODH type, minimal components)
│   └── faults.yaml             # Post-install fault injection (Pending pod, bad PVC)
├── scripts/
│   ├── kind-setup.sh           # Create kind cluster, install OLM + ODH, inject faults
│   └── kind-teardown.sh        # Delete kind cluster + clean cloned chart
├── kind-config.yaml            # Kind cluster configuration
├── pyproject.toml
├── Makefile
└── AGENTS.md
```

## Phase 2 Roadmap: GitOps Integration

When adopting [odh-gitops](https://github.com/opendatahub-io/odh-gitops) with ArgoCD:

- Add `argoproj-labs/mcp-for-argocd` MCP server for sync status and drift detection
- Add `modelcontextprotocol/github` MCP server for Git-based remediation (PRs instead of direct cluster mutation)
- New `gitops-agent` for ArgoCD app health and desired-vs-actual state comparison
- `remediation-agent` gains GitOps-safe mode: creates PRs to fix manifests in Git

Phase 1 agents remain unchanged — the extension is purely additive.

### References
- https://github.com/rcarrat-AI/nvidia-odh-gitops?tab=readme-ov-file (built in 2023 💥)

## License

MIT
