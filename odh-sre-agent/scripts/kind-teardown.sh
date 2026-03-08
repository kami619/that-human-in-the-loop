#!/usr/bin/env bash
# Delete the kind cluster and clean up cloned repos.
# Usage: ./scripts/kind-teardown.sh [cluster-name]
set -euo pipefail

CLUSTER_NAME="${1:-odh-sre-test}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Match the provider used by kind-setup.sh
if command -v podman &>/dev/null; then
  export KIND_EXPERIMENTAL_PROVIDER=podman
fi

if kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
  echo "Deleting kind cluster '${CLUSTER_NAME}'..."
  kind delete cluster --name "$CLUSTER_NAME"
  echo "Cluster deleted."
else
  echo "Cluster '${CLUSTER_NAME}' does not exist."
fi

for dir in "$PROJECT_DIR/.odh-operator" "$PROJECT_DIR/.odh-gitops" "$PROJECT_DIR/.odh-bundle"; do
  if [ -d "$dir" ]; then
    echo "Removing $(basename "$dir")..."
    rm -rf "$dir"
  fi
done

echo "Done."
