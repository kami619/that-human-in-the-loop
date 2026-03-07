"""Tests for configuration."""

import os
from pathlib import Path

from config import DEFAULT_NAMESPACE, KUBECONFIG, MAX_BUDGET_USD


class TestConfig:
    def test_default_kubeconfig(self):
        expected = str(Path.home() / ".kube" / "config")
        if not os.getenv("KUBECONFIG"):
            assert expected == KUBECONFIG

    def test_default_namespace_empty(self):
        if not os.getenv("SRE_DEFAULT_NAMESPACE"):
            assert DEFAULT_NAMESPACE == ""

    def test_budget_positive(self):
        assert MAX_BUDGET_USD > 0

    def test_budget_reasonable(self):
        assert MAX_BUDGET_USD <= 10.0
