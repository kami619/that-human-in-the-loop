"""Environment-based configuration."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Kubernetes
KUBECONFIG = os.getenv("KUBECONFIG", str(Path.home() / ".kube" / "config"))
DEFAULT_NAMESPACE = os.getenv("SRE_DEFAULT_NAMESPACE", "")

# Budget
MAX_BUDGET_USD = 2.00
