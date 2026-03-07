"""Mock cluster data for --dry-run mode.

Since we use the external kubernetes-mcp-server (not custom MCP tools),
dry-run works by starting the MCP server with --cluster-provider disabled.
The MCP server will return empty results for all tool calls.

This module provides mock scenario data that can be injected into agent
system prompts for realistic demos without a live cluster. The orchestrator
can prepend this context when dry_run=True.
"""

from __future__ import annotations

# Simulated ODH cluster scenario: multiple issues for the agent to find

MOCK_SCENARIO = """\
## MOCK DATA (dry-run mode — no live cluster)

You are operating in dry-run mode. Instead of querying a live cluster,
use the following simulated cluster state to demonstrate your investigation
and diagnosis capabilities. Respond as if you queried these results from
the cluster tools.

### Cluster Info
- Cluster Version: 4.14.12
- Platform: ROSA (AWS us-east-1)
- 6 nodes (3 master, 3 worker)

### Node Status
| Node | Role | CPU | Memory | Conditions |
|------|------|-----|--------|------------|
| ip-10-0-1-10.ec2.internal | master | 32% | 45% | Ready |
| ip-10-0-1-11.ec2.internal | master | 28% | 41% | Ready |
| ip-10-0-1-12.ec2.internal | master | 35% | 48% | Ready |
| ip-10-0-2-20.ec2.internal | worker | 78% | 85% | Ready, MemoryPressure |
| ip-10-0-2-21.ec2.internal | worker | 45% | 62% | Ready |
| ip-10-0-2-22.ec2.internal | worker | 52% | 58% | Ready |

### ClusterOperators
All Available except:
- machine-config: Degraded=True, message="nodes ip-10-0-2-20 are not updated"

### Namespaces
redhat-ods-operator, redhat-ods-applications, redhat-ods-monitoring,
openshift-operators, openshift-monitoring, default, kube-system

### Pods in redhat-ods-applications
| Pod | Phase | Ready | Restarts | Node |
|-----|-------|-------|----------|------|
| odh-dashboard-7f8b9c4d5-abc12 | Running | True | 0 | ip-10-0-2-21 |
| odh-dashboard-7f8b9c4d5-def34 | CrashLoopBackOff | False | 47 | ip-10-0-2-20 |
| odh-notebook-controller-6d5c4b3-ghi56 | Running | True | 0 | ip-10-0-2-22 |
| modelmesh-serving-8e7f6d5c-jkl78 | Running | True | 2 | ip-10-0-2-21 |
| data-science-pipelines-api-9a8b7c-mno90 | Pending | False | 0 | - |

### Events (redhat-ods-applications)
| Type | Reason | Object | Message |
|------|--------|--------|---------|
| Warning | BackOff | Pod/odh-dashboard-7f8b9c4d5-def34 | Back-off restarting failed container |
| Warning | OOMKilled | Pod/odh-dashboard-7f8b9c4d5-def34 | Container dashboard OOMKilled |
| Warning | FailedScheduling | Pod/data-science-pipelines-api-9a8b7c-mno90 | 0/3 nodes available: insufficient memory |
| Normal | Pulled | Pod/odh-dashboard-7f8b9c4d5-abc12 | Successfully pulled image |

### Pod Logs (odh-dashboard-7f8b9c4d5-def34)
```
2026-03-07T10:15:23Z ERROR Failed to allocate memory for cache initialization
2026-03-07T10:15:23Z ERROR Heap allocation failed: requested 512Mi, available 128Mi
2026-03-07T10:15:23Z FATAL Out of memory — container memory limit is 256Mi but dashboard requires minimum 512Mi
```

### Pod Logs (data-science-pipelines-api-9a8b7c-mno90)
```
(no logs — pod never started)
```

### PVCs in redhat-ods-applications
| PVC | Status | StorageClass | Capacity |
|-----|--------|-------------|----------|
| odh-dashboard-config | Bound | gp3-csi | 1Gi |
| jupyter-nb-user1-pvc | Pending | gp3-csi | 10Gi |

### Routes in redhat-ods-applications
| Route | Host | Service | TLS | Admitted |
|-------|------|---------|-----|----------|
| odh-dashboard | odh-dashboard.apps.rosa-cluster.example.com | odh-dashboard | true | true |
| notebook-controller | notebooks.apps.rosa-cluster.example.com | odh-notebook-controller | true | true |

### Services in redhat-ods-applications
| Service | Type | ClusterIP | Ports | Endpoints |
|---------|------|-----------|-------|-----------|
| odh-dashboard | ClusterIP | 172.30.45.12 | 8443/TCP | 1 ready (should be 2) |
| odh-notebook-controller | ClusterIP | 172.30.45.13 | 8080/TCP | 1 ready |
| modelmesh-serving | ClusterIP | 172.30.45.14 | 8033/TCP, 8008/TCP | 1 ready |

### Helm Releases
| Name | Namespace | Status | Chart | App Version |
|------|-----------|--------|-------|-------------|
| odh-operator | redhat-ods-operator | deployed | opendatahub-operator-2.10.0 | 2.10.0 |

### Summary of Issues
1. odh-dashboard pod (def34) is OOMKilled — memory limit 256Mi is too low (needs 512Mi)
2. data-science-pipelines-api pod is Pending — no node has enough memory (worker ip-10-0-2-20 under MemoryPressure)
3. jupyter-nb-user1-pvc is Pending (likely waiting for pod to bind)
4. machine-config ClusterOperator is Degraded (node ip-10-0-2-20 not updated)
5. odh-dashboard Service has only 1/2 endpoints ready (because one pod is crashlooping)
"""
