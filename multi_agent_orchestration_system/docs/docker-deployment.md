# Multi-Agent Orchestration System - Production Deployment

## Docker Configuration

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY multi_agent_orchestration_system/ ./multi_agent_orchestration_system/

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO
ENV REDIS_URL=redis://redis:6379/0

# Expose ports
EXPOSE 8000 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "multi_agent_orchestration_system.interface_layer.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose
```yaml
version: '3.8'

services:
  maos-api:
    build: .
    ports:
      - "8000:8000"
      - "9090:9090"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - LOG_LEVEL=INFO
      - PYTHONUNBUFFERED=1
    depends_on:
      - redis
    networks:
      - maos-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - maos-network
    restart: unless-stopped
    command: redis-server --appendonly yes

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9091:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - maos-network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
    networks:
      - maos-network
    restart: unless-stopped

networks:
  maos-network:
    driver: bridge

volumes:
  redis-data:
  grafana-data:
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: maos-orchestrator
  labels:
    app: maos
spec:
  replicas: 3
  selector:
    matchLabels:
      app: maos
  template:
    metadata:
      labels:
        app: maos
    spec:
      containers:
      - name: maos-api
        image: maos:latest
        ports:
        - containerPort: 8000
        - containerPort: 9090
        env:
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: maos-secrets
              key: redis-url
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
---
apiVersion: v1
kind: Service
metadata:
  name: maos-service
spec:
  selector:
    app: maos
  ports:
  - name: http
    port: 8000
    targetPort: 8000
  - name: metrics
    port: 9090
    targetPort: 9090
  type: LoadBalancer
```
