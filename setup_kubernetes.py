"""
MAOS v7.0 - Kubernetes配置
生产级Kubernetes部署
"""

k8s_deployment = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: maos-api
  namespace: maos
  labels:
    app: maos
    version: v7.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app: maos
  template:
    metadata:
      labels:
        app: maos
        version: v7.0
    spec:
      containers:
      - name: maos-api
        image: maos/maos:v7.0
        ports:
        - containerPort: 8000
        env:
        - name: MAOS_API_PORT
          value: "8000"
        - name: SILICONFLOW_API_KEY
          valueFrom:
            secretKeyRef:
              name: maos-secrets
              key: api-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      restartPolicy: Always
"""

k8s_service = """apiVersion: v1
kind: Service
metadata:
  name: maos-api-service
  namespace: maos
spec:
  selector:
    app: maos
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
"""

k8s_ingress = """apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: maos-ingress
  namespace: maos
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.maos.example.com
    secretName: maos-tls
  rules:
  - host: api.maos.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: maos-api-service
            port:
              number: 80
"""

k8s_hpa = """apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: maos-api-hpa
  namespace: maos
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: maos-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
"""

k8s_configmap = """apiVersion: v1
kind: ConfigMap
metadata:
  name: maos-config
  namespace: maos
data:
  MAOS_SYSTEM_NAME: "MAOS"
  MAOS_DEBUG: "false"
  MAOS_API_PORT: "8000"
  MAOS_MAX_TASKS: "100"
"""

import os

# 创建k8s目录
k8s_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'kubernetes')
os.makedirs(k8s_dir, exist_ok=True)

# 写入配置文件
files = {
    'deployment.yaml': k8s_deployment,
    'service.yaml': k8s_service,
    'ingress.yaml': k8s_ingress,
    'hpa.yaml': k8s_hpa,
    'configmap.yaml': k8s_configmap
}

for filename, content in files.items():
    filepath = os.path.join(k8s_dir, filename)
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"✅ Created: {filepath}")

# 创建README
readme_content = """# MAOS Kubernetes配置

生产级Kubernetes部署配置

## 快速部署

```bash
# 创建命名空间
kubectl create namespace maos

# 部署
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml
kubectl apply -f configmap.yaml

# 启用自动扩展
kubectl apply -f hpa.yaml

# 检查状态
kubectl get pods -n maos
kubectl get svc -n maos
```

## 配置说明

### Deployment
- 3个副本
- 资源限制: 256Mi-512Mi内存, 250m-500m CPU
- 健康检查: /health端点

### Service
- LoadBalancer类型
- 端口80 -> 8000

### Ingress
- HTTPS支持
- 自动TLS证书

### HPA
- 2-10个副本
- CPU > 70%时扩展
- Memory > 80%时扩展

### ConfigMap
- 系统配置
- API端口
- 最大任务数

## 环境变量

通过Secret配置:
- SILICONFLOW_API_KEY: API密钥

## 监控

推荐使用Prometheus + Grafana:

```bash
# 安装Prometheus
helm install prometheus prometheus-community/prometheus

# 安装Grafana
helm install grafana grafana
```
"""

readme_file = os.path.join(k8s_dir, 'README.md')
with open(readme_file, 'w') as f:
    f.write(readme_content)

print(f"✅ Created: {readme_file}")
print("\n📦 Kubernetes配置已准备就绪！")
