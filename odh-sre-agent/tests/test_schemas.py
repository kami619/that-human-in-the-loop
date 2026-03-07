"""Tests for Pydantic v2 schemas."""

from models.schemas import (
    ActionType,
    ClusterHealth,
    HelmRelease,
    HelmStatus,
    NodeStatus,
    PodPhase,
    PodStatus,
    RemediationAction,
    RemediationResult,
    RouteStatus,
    ServiceStatus,
    SREReport,
    WorkloadStatus,
)


class TestClusterHealth:
    def test_defaults(self):
        health = ClusterHealth()
        assert health.node_count == 0
        assert health.nodes == []
        assert health.degraded_operators == []

    def test_with_nodes(self):
        node = NodeStatus(
            name="worker-1",
            ready=True,
            roles=["worker"],
            cpu_usage="45%",
            memory_usage="72%",
            conditions=["MemoryPressure"],
        )
        health = ClusterHealth(
            cluster_version="4.14.12",
            platform="ROSA",
            node_count=1,
            nodes=[node],
        )
        assert health.nodes[0].name == "worker-1"
        assert "MemoryPressure" in health.nodes[0].conditions

    def test_json_schema(self):
        schema = ClusterHealth.model_json_schema()
        assert "properties" in schema
        assert "nodes" in schema["properties"]


class TestWorkloadStatus:
    def test_defaults(self):
        status = WorkloadStatus()
        assert status.pods == []
        assert status.events == []
        assert status.log_snippets == {}

    def test_pod_phases(self):
        pod = PodStatus(
            name="test-pod",
            namespace="default",
            phase=PodPhase.RUNNING,
            ready=True,
        )
        assert pod.phase == PodPhase.RUNNING
        assert pod.phase.value == "Running"

    def test_crashloopbackoff_pod(self):
        pod = PodStatus(
            name="crash-pod",
            namespace="redhat-ods-applications",
            phase=PodPhase.RUNNING,
            ready=False,
            restarts=47,
            container_statuses=["CrashLoopBackOff"],
        )
        assert pod.restarts == 47
        assert "CrashLoopBackOff" in pod.container_statuses


class TestNetworkingStatus:
    def test_route(self):
        route = RouteStatus(
            name="odh-dashboard",
            namespace="redhat-ods-applications",
            host="odh.example.com",
            service="odh-dashboard",
            tls=True,
            admitted=True,
        )
        assert route.admitted is True

    def test_service(self):
        svc = ServiceStatus(
            name="odh-dashboard",
            type="ClusterIP",
            ports=["8443/TCP"],
            endpoints_ready=2,
        )
        assert svc.endpoints_ready == 2


class TestHelmStatus:
    def test_release(self):
        release = HelmRelease(
            name="odh-operator",
            namespace="redhat-ods-operator",
            status="deployed",
            chart="opendatahub-operator-2.10.0",
        )
        status = HelmStatus(releases=[release])
        assert len(status.releases) == 1
        assert status.releases[0].status == "deployed"


class TestRemediationResult:
    def test_action(self):
        action = RemediationAction(
            action=ActionType.RESTART,
            target="Deployment/odh-dashboard",
            namespace="redhat-ods-applications",
            detail="Deleted pod to trigger restart",
            success=True,
        )
        result = RemediationResult(
            actions=[action],
            verification="Pod restarted successfully, now Running",
            follow_up=["Monitor for 15 minutes"],
        )
        assert result.actions[0].action == ActionType.RESTART
        assert result.actions[0].success is True

    def test_action_types(self):
        assert ActionType.RESTART.value == "restart"
        assert ActionType.SCALE.value == "scale"
        assert ActionType.PATCH.value == "patch"


class TestSREReport:
    def test_empty_report(self):
        report = SREReport(query="test query")
        assert report.cluster is None
        assert report.workload is None
        assert report.recommendations == []

    def test_full_report(self):
        report = SREReport(
            query="check health",
            cluster=ClusterHealth(cluster_version="4.14.12"),
            workload=WorkloadStatus(namespace="default"),
            summary="All healthy",
            recommendations=["Continue monitoring"],
        )
        assert report.cluster is not None
        assert report.cluster.cluster_version == "4.14.12"

    def test_json_roundtrip(self):
        report = SREReport(query="test", summary="ok")
        data = report.model_dump_json()
        restored = SREReport.model_validate_json(data)
        assert restored.query == "test"
        assert restored.summary == "ok"
