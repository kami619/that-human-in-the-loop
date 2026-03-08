# ODH SRE Agent — Test Fixtures

Configuration files for deploying an ODH-like environment on a kind cluster.

## Upstream Sources (pulled at runtime by `scripts/kind-setup.sh`)

| What | Source | How |
|------|--------|-----|
| ODH CRDs (23 total) | `quay.io/opendatahub/opendatahub-operator-bundle:v3.4.0-ea.1` | Extracted from published bundle image |
| DSCInitialization + DataScienceCluster CRs | [odh-gitops chart](https://github.com/opendatahub-io/odh-gitops/tree/main/charts/odh-rhoai) | `helm template` with `values-kind.yaml` |

The ODH operator itself requires OpenShift (`config.openshift.io` APIs) and
cannot run on kind. The setup script installs the real CRDs and CRs so the
agent sees authentic ODH resources, then simulates component workloads as
vanilla Deployments.

## Files

| File | Purpose |
|------|---------|
| `values-kind.yaml` | Helm values override for `helm template`: ODH type, minimal components (dashboard + workbenches), all dependencies disabled |
| `faults.yaml` | Post-install fault injection: Pending pod (32Gi memory request), Pending PVC (non-existent `gp3-csi` StorageClass) |

## Deliberate faults (for the agent to find)

1. **OOMKill** — `odh-dashboard` containers allocate memory beyond their 64Mi
   limit → OOMKilled → CrashLoopBackOff.
2. **Pending pod** — `data-science-pipelines-api` requests 32Gi memory,
   exceeding any kind node → FailedScheduling.
3. **Pending PVC** — `jupyter-nb-user1-pvc` references StorageClass `gp3-csi`
   which doesn't exist on kind.

## Namespace

With `operator.type: odh`, the applications namespace is `opendatahub`
(not `redhat-ods-applications` which is RHOAI-specific).
