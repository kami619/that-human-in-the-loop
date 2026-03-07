"""Tests for agent definitions."""

from agents.definitions import AGENTS

EXPECTED_AGENTS = [
    "cluster-agent",
    "workload-agent",
    "networking-agent",
    "helm-agent",
    "remediation-agent",
]


class TestAgentDefinitions:
    def test_all_agents_present(self):
        for name in EXPECTED_AGENTS:
            assert name in AGENTS, f"Missing agent: {name}"

    def test_agent_count(self):
        assert len(AGENTS) == 5

    def test_all_tools_have_mcp_prefix(self):
        for name, agent in AGENTS.items():
            for tool in agent.tools:
                assert tool.startswith("mcp__k8s__"), (
                    f"Agent '{name}' has tool '{tool}' without mcp__k8s__ prefix"
                )

    def test_all_agents_have_prompts(self):
        for name, agent in AGENTS.items():
            assert agent.prompt, f"Agent '{name}' has empty prompt"
            assert len(agent.prompt) > 50, f"Agent '{name}' has very short prompt"

    def test_all_agents_have_descriptions(self):
        for name, agent in AGENTS.items():
            assert agent.description, f"Agent '{name}' has empty description"

    def test_agent_models(self):
        assert AGENTS["cluster-agent"].model == "haiku"
        assert AGENTS["workload-agent"].model == "haiku"
        assert AGENTS["networking-agent"].model == "haiku"
        assert AGENTS["helm-agent"].model == "haiku"
        assert AGENTS["remediation-agent"].model == "sonnet"

    def test_cluster_agent_tools(self):
        tools = AGENTS["cluster-agent"].tools
        assert "mcp__k8s__nodes_top" in tools
        assert "mcp__k8s__nodes_stats_summary" in tools
        assert "mcp__k8s__namespaces_list" in tools
        assert "mcp__k8s__projects_list" in tools

    def test_workload_agent_tools(self):
        tools = AGENTS["workload-agent"].tools
        assert "mcp__k8s__pods_list" in tools
        assert "mcp__k8s__pods_log" in tools
        assert "mcp__k8s__events_list" in tools
        assert "mcp__k8s__resources_get" in tools

    def test_remediation_agent_has_write_tools(self):
        tools = AGENTS["remediation-agent"].tools
        assert "mcp__k8s__pods_delete" in tools
        assert "mcp__k8s__resources_create_or_update" in tools
        assert "mcp__k8s__resources_scale" in tools

    def test_read_agents_have_no_write_tools(self):
        write_tools = {
            "mcp__k8s__pods_delete",
            "mcp__k8s__pods_run",
            "mcp__k8s__pods_exec",
            "mcp__k8s__resources_create_or_update",
            "mcp__k8s__resources_delete",
            "mcp__k8s__resources_scale",
            "mcp__k8s__helm_install",
            "mcp__k8s__helm_uninstall",
        }
        for name in ["cluster-agent", "workload-agent", "networking-agent"]:
            agent_tools = set(AGENTS[name].tools)
            overlap = agent_tools & write_tools
            assert not overlap, (
                f"Read-only agent '{name}' has write tools: {overlap}"
            )
