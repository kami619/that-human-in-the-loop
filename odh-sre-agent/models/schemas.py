"""Pydantic v2 models defining the contract between agents."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

# -- Cluster Agent --------------------------------------------------------


class NodeStatus(BaseModel):
    """Status of a single cluster node."""

    name: str
    ready: bool = True
    roles: list[str] = Field(default_factory=list)
    cpu_usage: str = Field(default="", description="e.g. '45%'")
    memory_usage: str = Field(default="", description="e.g. '72%'")
    conditions: list[str] = Field(
        default_factory=list, description="Notable conditions (MemoryPressure, DiskPressure, etc.)"
    )


class ClusterHealth(BaseModel):
    """Output of the cluster-agent."""

    cluster_version: str = ""
    platform: str = Field(default="", description="e.g. 'ROSA', 'OCP', 'ARO'")
    node_count: int = 0
    nodes: list[NodeStatus] = Field(default_factory=list)
    degraded_operators: list[str] = Field(
        default_factory=list, description="ClusterOperators in Degraded state"
    )
    summary: str = Field(default="", description="Brief cluster health assessment")


# -- Workload Agent -------------------------------------------------------


class PodPhase(str, Enum):
    RUNNING = "Running"
    PENDING = "Pending"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    UNKNOWN = "Unknown"


class PodStatus(BaseModel):
    """Status of a single pod."""

    name: str
    namespace: str = ""
    phase: PodPhase = PodPhase.UNKNOWN
    ready: bool = False
    restarts: int = 0
    container_statuses: list[str] = Field(
        default_factory=list, description="e.g. ['CrashLoopBackOff', 'OOMKilled']"
    )
    age: str = ""
    node: str = ""


class EventSummary(BaseModel):
    """A Kubernetes event."""

    type: str = Field(default="", description="Normal or Warning")
    reason: str = ""
    message: str = ""
    object: str = Field(default="", description="e.g. 'Pod/odh-dashboard-abc123'")
    count: int = 1
    last_seen: str = ""


class WorkloadStatus(BaseModel):
    """Output of the workload-agent."""

    namespace: str = ""
    pods: list[PodStatus] = Field(default_factory=list)
    events: list[EventSummary] = Field(default_factory=list)
    log_snippets: dict[str, str] = Field(
        default_factory=dict, description="Pod name -> relevant log tail"
    )
    diagnosis: str = Field(default="", description="Root cause analysis from the agent")


# -- Networking Agent -----------------------------------------------------


class RouteStatus(BaseModel):
    """Status of an OpenShift Route."""

    name: str
    namespace: str = ""
    host: str = ""
    service: str = Field(default="", description="Backend service name")
    tls: bool = False
    admitted: bool = True


class ServiceStatus(BaseModel):
    """Status of a Kubernetes Service."""

    name: str
    namespace: str = ""
    type: str = Field(default="ClusterIP", description="ClusterIP, NodePort, LoadBalancer")
    cluster_ip: str = ""
    ports: list[str] = Field(default_factory=list, description="e.g. ['8080/TCP', '443/TCP']")
    endpoints_ready: int = 0


class NetworkingStatus(BaseModel):
    """Output of the networking-agent."""

    namespace: str = ""
    routes: list[RouteStatus] = Field(default_factory=list)
    services: list[ServiceStatus] = Field(default_factory=list)
    network_policies: list[str] = Field(
        default_factory=list, description="NetworkPolicy names in effect"
    )
    diagnosis: str = ""


# -- Helm Agent -----------------------------------------------------------


class HelmRelease(BaseModel):
    """Status of a Helm release."""

    name: str
    namespace: str = ""
    revision: int = 1
    status: str = Field(default="", description="deployed, failed, pending-install, etc.")
    chart: str = Field(default="", description="e.g. 'opendatahub-operator-2.10.0'")
    app_version: str = ""
    updated: str = ""


class HelmStatus(BaseModel):
    """Output of the helm-agent."""

    releases: list[HelmRelease] = Field(default_factory=list)
    diagnosis: str = ""


# -- Remediation Agent ----------------------------------------------------


class ActionType(str, Enum):
    RESTART = "restart"
    SCALE = "scale"
    PATCH = "patch"
    DELETE = "delete"
    HELM_UPGRADE = "helm_upgrade"
    EXEC = "exec"


class RemediationAction(BaseModel):
    """A single remediation action taken."""

    action: ActionType
    target: str = Field(description="e.g. 'Deployment/odh-dashboard'")
    namespace: str = ""
    detail: str = Field(default="", description="What was done")
    success: bool = True
    error: str = ""


class RemediationResult(BaseModel):
    """Output of the remediation-agent."""

    actions: list[RemediationAction] = Field(default_factory=list)
    verification: str = Field(default="", description="Post-remediation state check")
    follow_up: list[str] = Field(
        default_factory=list, description="Recommended follow-up actions"
    )


# -- Aggregated SRE Report ------------------------------------------------


class SREReport(BaseModel):
    """Aggregated report from the orchestrator."""

    query: str = ""
    cluster: ClusterHealth | None = None
    workload: WorkloadStatus | None = None
    networking: NetworkingStatus | None = None
    helm: HelmStatus | None = None
    remediation: RemediationResult | None = None
    summary: str = ""
    recommendations: list[str] = Field(default_factory=list)
