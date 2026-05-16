"""
MAOS v10.0 - Kubernetes Operator实现
自定义控制器管理MAOS资源
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import yaml


class ResourceState(Enum):
    """资源状态"""
    PENDING = "Pending"
    CREATING = "Creating"
    RUNNING = "Running"
    SCALING = "Scaling"
    UPDATING = "Updating"
    DELETING = "Deleting"
    FAILED = "Failed"
    UNKNOWN = "Unknown"


@dataclass
class MAOSClusterSpec:
    """MAOS集群规格"""
    version: str = "10.0.0"
    replicas: int = 3
    image: str = "maos/maos:v10.0"
    image_pull_policy: str = "IfNotPresent"
    
    # 资源
    resources: Dict[str, str] = field(default_factory=lambda: {
        "requests.cpu": "500m",
        "requests.memory": "512Mi",
        "limits.cpu": "1000m",
        "limits.memory": "1Gi"
    })
    
    # 存储
    storage_class: str = "standard"
    storage_size: str = "10Gi"
    
    # 网络
    service_type: str = "LoadBalancer"
    api_port: int = 8000
    ws_port: int = 8001
    
    # 高级
    autoscaling_enabled: bool = True
    min_replicas: int = 2
    max_replicas: int = 10
    autoscaling_target_cpu: int = 70
    autoscaling_target_memory: int = 80
    
    # 监控
    monitoring_enabled: bool = True
    logging_level: str = "INFO"
    
    # 安全
    rbac_enabled: bool = True
    service_account: str = "maos-sa"
    
    # TLS
    tls_enabled: bool = True
    cert_manager_enabled: bool = False
    
    # 多租户
    multi_tenant: bool = False
    tenant_isolation: bool = True


@dataclass
class MAOSClusterStatus:
    """MAOS集群状态"""
    state: ResourceState = ResourceState.PENDING
    phase: str = ""
    replicas: int = 0
    ready_replicas: int = 0
    available_replicas: int = 0
    conditions: List[Dict] = field(default_factory=list)
    endpoints: List[str] = field(default_factory=list)
    version: str = ""
    last_updated: datetime = field(default_factory=datetime.now)
    failure_message: Optional[str] = None


class MAOSCluster:
    """MAOS集群自定义资源"""
    
    def __init__(
        self,
        name: str,
        namespace: str = "maos",
        spec: MAOSClusterSpec = None
    ):
        self.name = name
        self.namespace = namespace
        self.spec = spec or MAOSClusterSpec()
        self.status = MAOSClusterStatus()
        self.metadata: Dict[str, Any] = {}
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """转换为Kubernetes资源字典"""
        return {
            "apiVersion": "maos.io/v1",
            "kind": "MAOSCluster",
            "metadata": {
                "name": self.name,
                "namespace": self.namespace,
                "creationTimestamp": self.created_at.isoformat(),
                **self.metadata
            },
            "spec": {
                "version": self.spec.version,
                "replicas": self.spec.replicas,
                "image": self.spec.image,
                "imagePullPolicy": self.spec.image_pull_policy,
                "resources": self.spec.resources,
                "storage": {
                    "class": self.spec.storage_class,
                    "size": self.spec.storage_size
                },
                "network": {
                    "serviceType": self.spec.service_type,
                    "apiPort": self.spec.api_port,
                    "wsPort": self.spec.ws_port
                },
                "autoscaling": {
                    "enabled": self.spec.autoscaling_enabled,
                    "minReplicas": self.spec.min_replicas,
                    "maxReplicas": self.spec.max_replicas,
                    "targetCPUUtilizationPercentage": self.spec.autoscaling_target_cpu,
                    "targetMemoryUtilizationPercentage": self.spec.autoscaling_target_memory
                },
                "monitoring": {
                    "enabled": self.spec.monitoring_enabled
                },
                "logging": {
                    "level": self.spec.logging_level
                },
                "security": {
                    "rbacEnabled": self.spec.rbac_enabled,
                    "serviceAccount": self.spec.service_account,
                    "tlsEnabled": self.spec.tls_enabled
                },
                "multiTenant": {
                    "enabled": self.spec.multi_tenant,
                    "isolation": self.spec.tenant_isolation
                }
            },
            "status": self._build_status()
        }
    
    def _build_status(self) -> Dict:
        """构建状态"""
        return {
            "state": self.status.state.value,
            "phase": self.status.phase,
            "replicas": self.status.replicas,
            "readyReplicas": self.status.ready_replicas,
            "availableReplicas": self.status.available_replicas,
            "conditions": self.status.conditions,
            "endpoints": self.status.endpoints,
            "version": self.status.version or self.spec.version,
            "lastUpdated": self.status.last_updated.isoformat(),
            "failureMessage": self.status.failure_message
        }
    
    def to_yaml(self) -> str:
        """导出为YAML"""
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MAOSCluster':
        """从字典创建"""
        name = data["metadata"]["name"]
        namespace = data["metadata"].get("namespace", "maos")
        
        spec_data = data.get("spec", {})
        spec = MAOSClusterSpec(
            version=spec_data.get("version", "10.0.0"),
            replicas=spec_data.get("replicas", 3),
            image=spec_data.get("image", "maos/maos:v10.0")
        )
        
        cluster = cls(name, namespace, spec)
        
        if "status" in data:
            status_data = data["status"]
            cluster.status = MAOSClusterStatus(
                state=ResourceState(status_data.get("state", "Pending")),
                phase=status_data.get("phase", ""),
                replicas=status_data.get("replicas", 0),
                ready_replicas=status_data.get("readyReplicas", 0),
                available_replicas=status_data.get("availableReplicas", 0)
            )
        
        return cluster


class MAOSClusterController:
    """MAOS集群控制器"""
    
    def __init__(self):
        self.clusters: Dict[str, MAOSCluster] = {}
        self.event_log: List[Dict] = []
    
    def create_cluster(self, name: str, namespace: str = "maos", spec: MAOSClusterSpec = None) -> MAOSCluster:
        """创建集群"""
        cluster = MAOSCluster(name, namespace, spec)
        cluster.status.state = ResourceState.CREATING
        
        self.clusters[f"{namespace}/{name}"] = cluster
        self._log_event("Normal", "Creating", f"Creating MAOSCluster {name}")
        
        # 模拟异步创建
        cluster.status.state = ResourceState.RUNNING
        cluster.status.replicas = cluster.spec.replicas
        cluster.status.ready_replicas = cluster.spec.replicas
        cluster.status.available_replicas = cluster.spec.replicas
        cluster.status.phase = "Running"
        cluster.status.endpoints = [
            f"http://{name}-api.{namespace}.svc.cluster.local:{cluster.spec.api_port}"
        ]
        
        self._log_event("Normal", "Created", f"MAOSCluster {name} is running")
        
        return cluster
    
    def update_cluster(self, name: str, namespace: str = "maos", spec: MAOSClusterSpec = None) -> Optional[MAOSCluster]:
        """更新集群"""
        key = f"{namespace}/{name}"
        cluster = self.clusters.get(key)
        
        if not cluster:
            return None
        
        cluster.status.state = ResourceState.UPDATING
        self._log_event("Normal", "Updating", f"Updating MAOSCluster {name}")
        
        if spec:
            cluster.spec = spec
        
        cluster.status.state = ResourceState.RUNNING
        self._log_event("Normal", "Updated", f"MAOSCluster {name} updated")
        
        return cluster
    
    def delete_cluster(self, name: str, namespace: str = "maos") -> bool:
        """删除集群"""
        key = f"{namespace}/{name}"
        cluster = self.clusters.get(key)
        
        if not cluster:
            return False
        
        cluster.status.state = ResourceState.DELETING
        self._log_event("Warning", "Deleting", f"Deleting MAOSCluster {name}")
        
        del self.clusters[key]
        self._log_event("Warning", "Deleted", f"MAOSCluster {name} deleted")
        
        return True
    
    def scale_cluster(self, name: str, namespace: str = "maos", replicas: int = None) -> Optional[MAOSCluster]:
        """扩缩容"""
        key = f"{namespace}/{name}"
        cluster = self.clusters.get(key)
        
        if not cluster:
            return None
        
        cluster.status.state = ResourceState.SCALING
        self._log_event("Normal", "Scaling", f"Scaling MAOSCluster {name} to {replicas} replicas")
        
        if replicas:
            cluster.spec.replicas = replicas
        cluster.status.replicas = cluster.spec.replicas
        cluster.status.ready_replicas = cluster.spec.replicas
        cluster.status.available_replicas = cluster.spec.replicas
        cluster.status.state = ResourceState.RUNNING
        
        self._log_event("Normal", "Scaled", f"MAOSCluster {name} scaled to {cluster.spec.replicas} replicas")
        
        return cluster
    
    def get_cluster(self, name: str, namespace: str = "maos") -> Optional[MAOSCluster]:
        """获取集群"""
        return self.clusters.get(f"{namespace}/{name}")
    
    def list_clusters(self, namespace: str = None) -> List[MAOSCluster]:
        """列出集群"""
        if namespace:
            return [
                c for c in self.clusters.values()
                if c.namespace == namespace
            ]
        return list(self.clusters.values())
    
    def _log_event(self, event_type: str, reason: str, message: str):
        """记录事件"""
        self.event_log.append({
            "type": event_type,
            "reason": reason,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })


def generate_cluster_yaml(name: str = "maos-cluster", namespace: str = "maos") -> str:
    """生成示例集群YAML"""
    cluster = MAOSCluster(name, namespace)
    return cluster.to_yaml()


def generate_deployment_yaml() -> str:
    """生成Deployment YAML"""
    return """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: maos-operator
  namespace: maos-system
spec:
  replicas: 1
  selector:
    matchLabels:
      name: maos-operator
  template:
    metadata:
      labels:
        name: maos-operator
    spec:
      serviceAccountName: maos-operator-sa
      containers:
      - name: operator
        image: maos/maos-operator:v10.0
        args:
        - "--leader-elect"
        env:
        - name: WATCH_NAMESPACE
          value: ""
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
"""


def generate_rbac_yaml() -> str:
    """生成RBAC YAML"""
    return """
apiVersion: v1
kind: ServiceAccount
metadata:
  name: maos-operator-sa
  namespace: maos-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: maos-operator
rules:
- apiGroups: ["maos.io"]
  resources: ["maosclusters"]
  verbs: ["*"]
- apiGroups: [""]
  resources: ["services", "configmaps", "secrets"]
  verbs: ["*"]
- apiGroups: ["apps"]
  resources: ["deployments", "statefulsets"]
  verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: maos-operator
subjects:
- kind: ServiceAccount
  name: maos-operator-sa
  namespace: maos-system
roleRef:
  kind: ClusterRole
  name: maos-operator
  apiGroup: rbac.authorization.k8s.io
"""
