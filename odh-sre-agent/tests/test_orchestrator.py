"""Tests for orchestrator configuration."""

import unittest.mock

import pytest

from orchestrator import SYSTEM_PROMPT, _find_k8s_mcp_binary, build_options


class TestSystemPrompt:
    def test_contains_agent_names(self):
        for agent in [
            "cluster-agent",
            "workload-agent",
            "networking-agent",
            "helm-agent",
            "remediation-agent",
        ]:
            assert agent in SYSTEM_PROMPT, f"System prompt missing agent: {agent}"

    def test_contains_odh_namespaces(self):
        assert "redhat-ods-operator" in SYSTEM_PROMPT
        assert "redhat-ods-applications" in SYSTEM_PROMPT

    def test_remediation_safety(self):
        assert "ONLY" in SYSTEM_PROMPT
        assert "diagnosis" in SYSTEM_PROMPT.lower()


class TestBuildOptions:
    @unittest.mock.patch("orchestrator.shutil.which", return_value="/usr/local/bin/kubernetes-mcp-server")
    def test_live_mode(self, mock_which):
        options = build_options(dry_run=False)
        assert options.model == "sonnet"
        assert options.allowed_tools == ["Task"]
        assert "k8s" in options.mcp_servers
        assert options.permission_mode == "bypassPermissions"
        k8s_args = options.mcp_servers["k8s"]["args"]
        assert "--kubeconfig" in k8s_args

    @unittest.mock.patch("orchestrator.shutil.which", return_value="/usr/local/bin/kubernetes-mcp-server")
    def test_dry_run_mode(self, mock_which):
        options = build_options(dry_run=True)
        k8s_args = options.mcp_servers["k8s"]["args"]
        assert "--cluster-provider" in k8s_args
        assert "disabled" in k8s_args
        assert "MOCK DATA" in options.system_prompt

    @unittest.mock.patch("orchestrator.shutil.which", return_value="/usr/local/bin/kubernetes-mcp-server")
    def test_agents_included(self, mock_which):
        options = build_options()
        assert "cluster-agent" in options.agents
        assert "remediation-agent" in options.agents
        assert len(options.agents) == 5

    @unittest.mock.patch("orchestrator.shutil.which", return_value="/usr/local/bin/kubernetes-mcp-server")
    def test_budget_set(self, mock_which):
        options = build_options()
        assert options.max_budget_usd > 0


class TestFindBinary:
    @unittest.mock.patch("orchestrator.shutil.which", return_value=None)
    def test_missing_binary_raises(self, mock_which):
        with pytest.raises(FileNotFoundError, match="kubernetes-mcp-server"):
            _find_k8s_mcp_binary()

    @unittest.mock.patch("orchestrator.shutil.which", return_value="/usr/bin/kubernetes-mcp-server")
    def test_found_binary(self, mock_which):
        result = _find_k8s_mcp_binary()
        assert result == "/usr/bin/kubernetes-mcp-server"
