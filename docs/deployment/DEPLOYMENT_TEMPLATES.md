# Deployment Templates - Docker & Kubernetes
## Complete Deployment Configurations for Socrates AI Modular Platform

---

## PART 1: DOCKER SINGLE-PROCESS DEPLOYMENT

### 1.1 Dockerfile (All Services in One Container)

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose ports
EXPOSE 8000 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/system/health')"

# Start application
CMD ["python", "socrates.py", "--mode", "single-process", "--host", "0.0.0.0"]
```

### 1.2 Docker Compose (Development)

```yaml
# docker-compose.yml
version: '3.8'

services:
  socrates:
    build: .
    container_name: socrates-ai
    ports:
      - "8000:8000"  # API
      - "8001:8001"  # CLI
    environment:
      - DEPLOYMENT_MODE=single_process
      - LOG_LEVEL=debug
      - DEBUG=true
      - DATABASE_PATH=/data/socrates.db
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./data:/data
      - ./logs:/app/logs
      - ./config:/app/config
    depends_on:
      - redis
      - sqlite
    networks:
      - socrates-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: socrates-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - socrates-network
    restart: unless-stopped

  sqlite:
    image: alpine:latest
    container_name: socrates-sqlite
    volumes:
      - ./data:/data
    networks:
      - socrates-network
    restart: unless-stopped

volumes:
  redis-data:

networks:
  socrates-network:
    driver: bridge
```

### 1.3 Docker Build & Run Commands

```bash
# Build image
docker build -t socrates-ai:latest .

# Run container
docker run -d \
  --name socrates-ai \
  -p 8000:8000 \
  -p 8001:8001 \
  -v $(pwd)/data:/data \
  -v $(pwd)/logs:/app/logs \
  -e DEPLOYMENT_MODE=single_process \
  socrates-ai:latest

# Using docker-compose
docker-compose up -d

# View logs
docker logs -f socrates-ai

# Stop container
docker stop socrates-ai
docker rm socrates-ai
```

---

## PART 2: KUBERNETES MICROSERVICES DEPLOYMENT

### 2.1 Namespace

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: socrates-ai
  labels:
    app: socrates
```

### 2.2 ConfigMap for Configuration

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: socrates-config
  namespace: socrates-ai
data:
  DEPLOYMENT_MODE: "microservices"
  LOG_LEVEL: "info"
  DATABASE_PATH: "/data/socrates.db"
  REDIS_HOST: "redis.socrates-ai.svc.cluster.local"
  REDIS_PORT: "6379"
  API_HOST: "0.0.0.0"
  API_PORT: "8000"
```

### 2.3 Secrets for Sensitive Data

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: socrates-secrets
  namespace: socrates-ai
type: Opaque
stringData:
  ANTHROPIC_API_KEY: "sk-ant-xxx"
  OPENAI_API_KEY: "sk-proj-xxx"
  GOOGLE_API_KEY: "xxx"
  DATABASE_PASSWORD: "your-db-password"
```

### 2.4 Redis Deployment

```yaml
# k8s/redis.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: socrates-ai
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        volumeMounts:
        - name: redis-data
          mountPath: /data
        livenessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 30
          periodSeconds: 10
      volumes:
      - name: redis-data
        emptyDir: {}

---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: socrates-ai
spec:
  selector:
    app: redis
  ports:
  - protocol: TCP
    port: 6379
    targetPort: 6379
  type: ClusterIP
```

### 2.5 Agent Service Deployment

```yaml
# k8s/agent-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agents
  namespace: socrates-ai
  labels:
    app: socrates
    service: agents
spec:
  replicas: 3
  selector:
    matchLabels:
      app: socrates
      service: agents
  template:
    metadata:
      labels:
        app: socrates
        service: agents
    spec:
      containers:
      - name: agents
        image: socrates-ai:latest
        imagePullPolicy: Always
        command: ["python", "socrates.py", "--service", "agents"]
        ports:
        - containerPort: 8000
          name: http
        envFrom:
        - configMapRef:
            name: socrates-config
        - secretRef:
            name: socrates-secrets
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /api/v1/system/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /api/v1/system/health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
        volumeMounts:
        - name: data
          mountPath: /data
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: socrates-data
      - name: logs
        emptyDir: {}
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: service
                  operator: In
                  values:
                  - agents
              topologyKey: kubernetes.io/hostname

---
apiVersion: v1
kind: Service
metadata:
  name: agents
  namespace: socrates-ai
  labels:
    app: socrates
    service: agents
spec:
  type: ClusterIP
  selector:
    app: socrates
    service: agents
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
    name: http
```

### 2.6 Learning Service Deployment

```yaml
# k8s/learning-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: learning
  namespace: socrates-ai
  labels:
    app: socrates
    service: learning
spec:
  replicas: 2
  selector:
    matchLabels:
      app: socrates
      service: learning
  template:
    metadata:
      labels:
        app: socrates
        service: learning
    spec:
      containers:
      - name: learning
        image: socrates-ai:latest
        imagePullPolicy: Always
        command: ["python", "socrates.py", "--service", "learning"]
        ports:
        - containerPort: 8000
          name: http
        envFrom:
        - configMapRef:
            name: socrates-config
        - secretRef:
            name: socrates-secrets
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /api/v1/system/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/system/health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        volumeMounts:
        - name: data
          mountPath: /data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: socrates-data

---
apiVersion: v1
kind: Service
metadata:
  name: learning
  namespace: socrates-ai
  labels:
    app: socrates
    service: learning
spec:
  type: ClusterIP
  selector:
    app: socrates
    service: learning
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
    name: http
```

### 2.7 Knowledge Service Deployment

```yaml
# k8s/knowledge-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: knowledge
  namespace: socrates-ai
  labels:
    app: socrates
    service: knowledge
spec:
  replicas: 2
  selector:
    matchLabels:
      app: socrates
      service: knowledge
  template:
    metadata:
      labels:
        app: socrates
        service: knowledge
    spec:
      containers:
      - name: knowledge
        image: socrates-ai:latest
        imagePullPolicy: Always
        command: ["python", "socrates.py", "--service", "knowledge"]
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: socrates-config
        - secretRef:
            name: socrates-secrets
        resources:
          requests:
            memory: "1.5Gi"
            cpu: "500m"
          limits:
            memory: "3Gi"
            cpu: "1000m"
        volumeMounts:
        - name: data
          mountPath: /data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: socrates-data
```

### 2.8 Workflow Service Deployment

```yaml
# k8s/workflow-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: workflow
  namespace: socrates-ai
  labels:
    app: socrates
    service: workflow
spec:
  replicas: 2
  selector:
    matchLabels:
      app: socrates
      service: workflow
  template:
    metadata:
      labels:
        app: socrates
        service: workflow
    spec:
      containers:
      - name: workflow
        image: socrates-ai:latest
        imagePullPolicy: Always
        command: ["python", "socrates.py", "--service", "workflow"]
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: socrates-config
        - secretRef:
            name: socrates-secrets
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        volumeMounts:
        - name: data
          mountPath: /data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: socrates-data
```

### 2.9 Analytics Service Deployment

```yaml
# k8s/analytics-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: analytics
  namespace: socrates-ai
  labels:
    app: socrates
    service: analytics
spec:
  replicas: 1
  selector:
    matchLabels:
      app: socrates
      service: analytics
  template:
    metadata:
      labels:
        app: socrates
        service: analytics
    spec:
      containers:
      - name: analytics
        image: socrates-ai:latest
        imagePullPolicy: Always
        command: ["python", "socrates.py", "--service", "analytics"]
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: socrates-config
        - secretRef:
            name: socrates-secrets
        resources:
          requests:
            memory: "1Gi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "500m"
        volumeMounts:
        - name: data
          mountPath: /data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: socrates-data
```

### 2.10 API Gateway (Ingress)

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: socrates-ingress
  namespace: socrates-ai
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.socrates.local
    secretName: socrates-tls
  rules:
  - host: api.socrates.local
    http:
      paths:
      - path: /agents
        pathType: Prefix
        backend:
          service:
            name: agents
            port:
              number: 8000
      - path: /learning
        pathType: Prefix
        backend:
          service:
            name: learning
            port:
              number: 8000
      - path: /knowledge
        pathType: Prefix
        backend:
          service:
            name: knowledge
            port:
              number: 8000
      - path: /workflow
        pathType: Prefix
        backend:
          service:
            name: workflow
            port:
              number: 8000
      - path: /analytics
        pathType: Prefix
        backend:
          service:
            name: analytics
            port:
              number: 8000
```

### 2.11 Persistent Volume

```yaml
# k8s/pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: socrates-data
  namespace: socrates-ai
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
  storageClassName: standard
```

### 2.12 HorizontalPodAutoscaler

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agents-hpa
  namespace: socrates-ai
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agents
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

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: learning-hpa
  namespace: socrates-ai
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: learning
  minReplicas: 1
  maxReplicas: 5
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 75
```

---

## PART 3: DEPLOYMENT COMMANDS

### Deploy to Kubernetes

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create ConfigMap and Secrets
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml

# Create PVC
kubectl apply -f k8s/pvc.yaml

# Deploy Redis
kubectl apply -f k8s/redis.yaml

# Deploy services
kubectl apply -f k8s/agent-service.yaml
kubectl apply -f k8s/learning-service.yaml
kubectl apply -f k8s/knowledge-service.yaml
kubectl apply -f k8s/workflow-service.yaml
kubectl apply -f k8s/analytics-service.yaml

# Create Ingress
kubectl apply -f k8s/ingress.yaml

# Deploy HPA
kubectl apply -f k8s/hpa.yaml

# Check deployment status
kubectl get deployments -n socrates-ai
kubectl get pods -n socrates-ai
kubectl get svc -n socrates-ai

# View logs
kubectl logs -f deployment/agents -n socrates-ai
kubectl logs -f deployment/learning -n socrates-ai

# Port forward for testing
kubectl port-forward svc/agents 8000:8000 -n socrates-ai

# Delete deployment
kubectl delete namespace socrates-ai
```

---

## PART 4: ENVIRONMENT VARIABLES

### Single-Process

```bash
DEPLOYMENT_MODE=single_process
LOG_LEVEL=info
DEBUG=false
DATABASE_PATH=/data/socrates.db
REDIS_URL=redis://localhost:6379
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-proj-xxx
```

### Microservices

```bash
DEPLOYMENT_MODE=microservices
LOG_LEVEL=info
DEBUG=false
DATABASE_PATH=/data/socrates.db
REDIS_HOST=redis.socrates-ai.svc.cluster.local
REDIS_PORT=6379
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-proj-xxx
SERVICE_DISCOVERY=kubernetes  # or "consul", "eureka"
```

---

## PART 5: MONITORING & LOGGING

### 2.13 Prometheus ServiceMonitor

```yaml
# k8s/prometheus.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: socrates
  namespace: socrates-ai
spec:
  selector:
    matchLabels:
      app: socrates
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
```

### 2.14 Logging with ELK Stack

```yaml
# k8s/logging.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
  namespace: socrates-ai
data:
  fluent-bit.conf: |
    [SERVICE]
        Flush         5
        Log_Level     info
        Daemon        off

    [INPUT]
        Name              tail
        Path              /var/log/containers/*_socrates-ai_*.log
        Parser            docker
        Tag               kube.*
        Refresh_Interval  5

    [OUTPUT]
        Name            es
        Match           kube.*
        Host            elasticsearch.logging.svc.cluster.local
        Port            9200
        HTTP_User       elastic
        HTTP_Passwd     ${ELASTIC_PASSWORD}
        Logstash_Format On
```

---

## PART 6: HEALTH CHECKS & READINESS

```yaml
# k8s/service-health.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: health-check-script
  namespace: socrates-ai
data:
  health-check.sh: |
    #!/bin/bash
    curl -f http://localhost:8000/api/v1/system/health || exit 1
    exit 0
```

---

## SUMMARY: Deployment Modes

### Single-Process (Development)
```
docker-compose up -d
```
- All services in one container
- Shared database
- Suitable for: Development, testing, small deployments
- Pros: Simple, low overhead
- Cons: Cannot scale services independently

### Microservices (Production)
```
kubectl apply -f k8s/
```
- Separate deployment per service
- Horizontal auto-scaling
- Service mesh ready
- Suitable for: Production, large deployments
- Pros: Scalable, fault-isolated, flexible
- Cons: More complex, distributed system challenges

---

**Version**: 1.0
**Status**: Complete
**Deployment Modes**: 2 (Single-process, Microservices)
**K8s Resources**: 15+
**Container Optimization**: Ready
