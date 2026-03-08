#!/usr/bin/env bash
# Create a kind cluster and deploy an ODH-like environment for SRE agent testing.
#
# Flow:
#   1. Create kind cluster
#   2. Pull ODH CRDs from the operator bundle image on quay.io
#   3. Clone odh-gitops → render DSCInitialization + DataScienceCluster CRs via helm
#   4. Deploy simulated ODH component workloads (Deployments, Services)
#   5. Inject faults for the SRE agent to find
#
# The ODH operator itself requires OpenShift (config.openshift.io APIs) and
# cannot run on kind. Instead, we install the real CRDs and CRs so the agent
# sees authentic ODH resources, then simulate workloads as Deployments.
#
# Usage: ./scripts/kind-setup.sh [cluster-name]
set -euo pipefail

CLUSTER_NAME="${1:-odh-sre-test}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CHART_DIR="${PROJECT_DIR}/.odh-gitops"
BUNDLE_DIR="${PROJECT_DIR}/.odh-bundle"

# Operator version — update this to pull a different release
ODH_VERSION="v3.4.0-ea.1"
BUNDLE_IMG="quay.io/opendatahub/opendatahub-operator-bundle:${ODH_VERSION}"

# Namespace layout (matches operator.type=odh in values.yaml)
OPERATOR_NS="opendatahub-operator-system"
APPS_NS="opendatahub"

# --- Pre-flight checks -------------------------------------------------------

for cmd in kind kubectl helm; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "ERROR: $cmd is not installed." >&2
    exit 1
  fi
done

# Detect container runtime: prefer podman, fall back to docker
if command -v podman &>/dev/null; then
  export KIND_EXPERIMENTAL_PROVIDER=podman
  CONTAINER_RT=podman
  echo "Using podman as container runtime."
elif command -v docker &>/dev/null; then
  CONTAINER_RT=docker
  echo "Using docker as container runtime."
else
  echo "ERROR: Neither podman nor docker is installed." >&2
  exit 1
fi

# --- Create cluster -----------------------------------------------------------

if kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
  echo "Cluster '${CLUSTER_NAME}' already exists — reusing."
else
  echo "Creating kind cluster '${CLUSTER_NAME}'..."
  kind create cluster \
    --name "$CLUSTER_NAME" \
    --config "$PROJECT_DIR/kind-config.yaml" \
    --wait 60s
fi

kubectl cluster-info --context "kind-${CLUSTER_NAME}" >/dev/null

# --- Extract CRDs from bundle image ------------------------------------------

if [ -d "$BUNDLE_DIR/manifests" ]; then
  echo "Bundle manifests already extracted — reusing."
else
  echo "Pulling operator bundle image: ${BUNDLE_IMG}..."
  $CONTAINER_RT pull --platform linux/amd64 "$BUNDLE_IMG" >/dev/null

  echo "Extracting CRDs from bundle..."
  mkdir -p "$BUNDLE_DIR"
  CID=$($CONTAINER_RT create "$BUNDLE_IMG" true)
  $CONTAINER_RT cp "$CID:/manifests" "$BUNDLE_DIR/manifests"
  $CONTAINER_RT rm "$CID" >/dev/null
fi

echo "Applying ODH CRDs..."
for f in "$BUNDLE_DIR"/manifests/*; do
  if grep -q "kind: CustomResourceDefinition" "$f" 2>/dev/null; then
    kubectl apply --server-side -f "$f"
  fi
done

kubectl wait --for=condition=established crd/datascienceclusters.datasciencecluster.opendatahub.io --timeout=30s
kubectl wait --for=condition=established crd/dscinitializations.dscinitialization.opendatahub.io --timeout=30s
echo "  CRDs established."

# --- Create namespaces --------------------------------------------------------

echo "Creating namespaces..."
kubectl create namespace "$OPERATOR_NS" 2>/dev/null || true
kubectl create namespace "$APPS_NS" 2>/dev/null || true

# --- Apply DSC/DSCI from odh-gitops chart -------------------------------------

if [ -d "$CHART_DIR" ]; then
  echo "odh-gitops already cloned — pulling latest."
  git -C "$CHART_DIR" pull --ff-only 2>/dev/null || true
else
  echo "Cloning odh-gitops (shallow)..."
  git clone --depth 1 https://github.com/opendatahub-io/odh-gitops.git "$CHART_DIR"
fi

CHART_PATH="${CHART_DIR}/charts/odh-rhoai"
VALUES_FILE="${PROJECT_DIR}/test-fixtures/values-kind.yaml"

echo "Applying DSCInitialization and DataScienceCluster from chart..."
helm template odh-sre-test "$CHART_PATH" \
  -f "$VALUES_FILE" \
  -s templates/operator/dscinitialization.yaml \
  | kubectl apply --server-side -f -

helm template odh-sre-test "$CHART_PATH" \
  -f "$VALUES_FILE" \
  -s templates/operator/datasciencecluster.yaml \
  | kubectl apply --server-side -f -

echo "  DSC and DSCI created."

# --- Deploy simulated workloads -----------------------------------------------
# These simulate what the operator would create when reconciling the DSC.
# Component names match real ODH component deployments.

echo "Deploying simulated ODH workloads..."
kubectl apply --server-side -f - <<EOF
---
# ODH operator (simulated — real one requires OpenShift)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: odh-operator
  namespace: ${OPERATOR_NS}
  labels:
    app.kubernetes.io/name: opendatahub-operator
    app.kubernetes.io/part-of: opendatahub
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: opendatahub-operator
  template:
    metadata:
      labels:
        app.kubernetes.io/name: opendatahub-operator
    spec:
      containers:
        - name: manager
          image: registry.k8s.io/pause:3.9
          resources:
            requests: { cpu: 10m, memory: 32Mi }
            limits: { memory: 64Mi }
---
# Dashboard component (DSC: dashboard.managementState=Managed)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: odh-dashboard
  namespace: ${APPS_NS}
  labels:
    app: odh-dashboard
    app.kubernetes.io/name: odh-dashboard
    app.kubernetes.io/part-of: opendatahub
    component: dashboard
spec:
  replicas: 2
  selector:
    matchLabels:
      app: odh-dashboard
  template:
    metadata:
      labels:
        app: odh-dashboard
        component: dashboard
    spec:
      containers:
        - name: dashboard
          # OOMKill trigger: allocates memory beyond 64Mi limit
          image: busybox:1.36
          command: ["sh", "-c", "i=0; while true; do eval block_\$i=\$(head -c 10485760 /dev/urandom | base64); i=\$((i+1)); done"]
          resources:
            requests: { cpu: 10m, memory: 32Mi }
            limits: { memory: 64Mi }
---
apiVersion: v1
kind: Service
metadata:
  name: odh-dashboard
  namespace: ${APPS_NS}
  labels: { app: odh-dashboard }
spec:
  selector: { app: odh-dashboard }
  ports:
    - { name: https, port: 8443, targetPort: 8443 }
---
# Notebook controller (DSC: workbenches.managementState=Managed)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: odh-notebook-controller
  namespace: ${APPS_NS}
  labels:
    app: odh-notebook-controller
    app.kubernetes.io/part-of: opendatahub
    component: workbenches
spec:
  replicas: 1
  selector:
    matchLabels:
      app: odh-notebook-controller
  template:
    metadata:
      labels:
        app: odh-notebook-controller
        component: workbenches
    spec:
      containers:
        - name: controller
          image: registry.k8s.io/pause:3.9
          resources:
            requests: { cpu: 10m, memory: 32Mi }
            limits: { memory: 64Mi }
---
apiVersion: v1
kind: Service
metadata:
  name: odh-notebook-controller
  namespace: ${APPS_NS}
  labels: { app: odh-notebook-controller }
spec:
  selector: { app: odh-notebook-controller }
  ports:
    - { name: http, port: 8080, targetPort: 8080 }
---
# ModelMesh serving (simulated KServe/ModelMesh)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: modelmesh-serving
  namespace: ${APPS_NS}
  labels:
    app: modelmesh-serving
    app.kubernetes.io/part-of: opendatahub
    component: kserve
spec:
  replicas: 1
  selector:
    matchLabels:
      app: modelmesh-serving
  template:
    metadata:
      labels:
        app: modelmesh-serving
        component: kserve
    spec:
      containers:
        - name: serving
          image: registry.k8s.io/pause:3.9
          resources:
            requests: { cpu: 10m, memory: 32Mi }
            limits: { memory: 64Mi }
---
apiVersion: v1
kind: Service
metadata:
  name: modelmesh-serving
  namespace: ${APPS_NS}
  labels: { app: modelmesh-serving }
spec:
  selector: { app: modelmesh-serving }
  ports:
    - { name: grpc, port: 8033, targetPort: 8033 }
    - { name: rest, port: 8008, targetPort: 8008 }
EOF

echo "Waiting for healthy workloads..."
kubectl wait --for=condition=available deployment/odh-operator \
  -n "$OPERATOR_NS" --timeout=60s 2>/dev/null || true
kubectl wait --for=condition=available deployment/odh-notebook-controller \
  -n "$APPS_NS" --timeout=60s 2>/dev/null || true
kubectl wait --for=condition=available deployment/modelmesh-serving \
  -n "$APPS_NS" --timeout=60s 2>/dev/null || true

# --- Inject faults ------------------------------------------------------------

echo "Injecting faults..."
kubectl apply -f "$PROJECT_DIR/test-fixtures/faults.yaml"

echo "Waiting 20s for fault events to accumulate..."
sleep 20

# --- Summary ------------------------------------------------------------------

echo ""
echo "=== Cluster ready: kind-${CLUSTER_NAME} ==="
echo ""
echo "ODH CRDs:"
kubectl get crd | grep opendatahub | head -5
echo "  ... ($(kubectl get crd | grep -c opendatahub) total)"
echo ""
echo "DataScienceCluster:"
kubectl get datasciencecluster -o wide 2>/dev/null || echo "(not found)"
echo ""
echo "DSCInitialization:"
kubectl get dscinitialization -o wide 2>/dev/null || echo "(not found)"
echo ""
echo "Pods in ${APPS_NS}:"
kubectl get pods -n "$APPS_NS" -o wide
echo ""
echo "Events (warnings):"
kubectl get events -n "$APPS_NS" --field-selector type=Warning --sort-by='.lastTimestamp' 2>/dev/null | tail -10 || true
echo ""
echo "PVCs:"
kubectl get pvc -n "$APPS_NS"
echo ""
echo "To run the agent:"
echo "  uv run python main.py --query 'Check cluster health and investigate issues in opendatahub' --namespace opendatahub"
