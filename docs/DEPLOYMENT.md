# Socrates API - Deployment Guide

Complete guide for deploying Socrates API to production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Docker Deployment](#docker-deployment)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Database Setup](#database-setup)
6. [Monitoring & Observability](#monitoring--observability)
7. [Security Hardening](#security-hardening)
8. [Troubleshooting](#troubleshooting)
9. [Scaling & Performance](#scaling--performance)

---

## Prerequisites

### Required Tools
- Docker & Docker Compose (for containerized deployment)
- kubectl & Helm (for Kubernetes deployment)
- PostgreSQL 13+ (production database)
- Redis 6+ (caching and rate limiting)
- Python 3.10+ (for development)

### Required Credentials
- Anthropic API key (`ANTHROPIC_API_KEY`)
- AWS credentials (if using S3 backups)
- Database credentials (PostgreSQL)

### System Requirements (Production)
- **CPU:** Minimum 2 cores (4+ cores recommended)
- **Memory:** Minimum 4GB RAM (8GB+ recommended)
- **Storage:** Minimum 20GB (depends on data volume)
- **Network:** 1Gbps+ connectivity

---

## Docker Deployment

### Quick Start with Docker Compose

```bash
# Clone repository
git clone https://github.com/your-org/socrates.git
cd socrates

# Create environment configuration
cp .env.production.example .env.production
# Edit .env.production with your values

# Start all services
docker-compose -f docker-compose.yml up -d

# Verify services
docker-compose ps
curl http://localhost:8000/health
```

### Docker Image Building

```bash
# Build API image
docker build -f Dockerfile.api -t socrates-api:latest .

# Build frontend image
docker build -f socrates-frontend/Dockerfile -t socrates-frontend:latest socrates-frontend/

# Tag for registry
docker tag socrates-api:latest ghcr.io/your-org/socrates-api:latest
docker tag socrates-frontend:latest ghcr.io/your-org/socrates-frontend:latest

# Push to registry
docker push ghcr.io/your-org/socrates-api:latest
docker push ghcr.io/your-org/socrates-frontend:latest
```

### Docker Compose Production Setup

See `docker-compose.yml` for complete multi-service configuration:
- **socrates-api:** FastAPI backend service
- **postgres:** PostgreSQL database
- **redis:** Cache and rate limiting
- **chromadb:** Vector database for embeddings
- **nginx:** Reverse proxy and load balancer

### Network Configuration

```yaml
# Docker Compose networking
networks:
  socrates:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Volume Management

```bash
# Create persistent volumes
docker volume create socrates_postgres_data
docker volume create socrates_redis_data
docker volume create socrates_backups

# List volumes
docker volume ls | grep socrates

# Backup volume data
docker run --rm -v socrates_postgres_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/postgres_backup.tar.gz -C /data .
```

---

## Kubernetes Deployment

### Prerequisites

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install Helm repo
helm repo add socrates https://charts.socrates.app
helm repo update
```

### Namespace Setup

```bash
# Create namespace
kubectl create namespace socrates-prod

# Set default namespace
kubectl config set-context --current --namespace=socrates-prod

# Verify
kubectl get namespace socrates-prod
```

### ConfigMap and Secrets

```bash
# Create ConfigMap for non-sensitive config
kubectl create configmap socrates-config \
  --from-literal=ENVIRONMENT=production \
  --from-literal=LOG_LEVEL=INFO \
  -n socrates-prod

# Create Secrets for sensitive data
kubectl create secret generic socrates-secrets \
  --from-literal=JWT_SECRET_KEY=$(python scripts/generate_jwt_secret.py --format hex) \
  --from-literal=ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  --from-literal=DATABASE_PASSWORD=$DB_PASSWORD \
  -n socrates-prod

# Verify
kubectl get configmap socrates-config -n socrates-prod
kubectl get secret socrates-secrets -n socrates-prod
```

### Deploy with Helm

```bash
# Create values override file
cat > values-prod.yaml <<EOF
replicaCount: 3

image:
  repository: ghcr.io/your-org/socrates-api
  tag: latest
  pullPolicy: IfNotPresent

resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

ingress:
  enabled: true
  className: nginx
  hosts:
    - host: api.socrates.app
      paths:
        - path: /
          pathType: Prefix
EOF

# Deploy via Helm
helm install socrates-api socrates/socrates \
  -f values-prod.yaml \
  -n socrates-prod

# Verify deployment
kubectl get deployments -n socrates-prod
kubectl get pods -n socrates-prod
kubectl get svc -n socrates-prod
```

### Manual Kubernetes Deployment

If not using Helm, apply manifests directly:

```bash
# Create ConfigMap
kubectl apply -f kubernetes/configmap.yaml -n socrates-prod

# Create Secrets
kubectl apply -f kubernetes/secrets.yaml -n socrates-prod

# Deploy database
kubectl apply -f kubernetes/postgres-deployment.yaml -n socrates-prod

# Deploy cache
kubectl apply -f kubernetes/redis-deployment.yaml -n socrates-prod

# Deploy API
kubectl apply -f kubernetes/api-deployment.yaml -n socrates-prod

# Deploy ingress
kubectl apply -f kubernetes/ingress.yaml -n socrates-prod

# Verify
kubectl get all -n socrates-prod
```

### Health Checks & Probing

Kubernetes automatically performs health checks via configured probes:

```yaml
# Liveness probe (restart if unhealthy)
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

# Readiness probe (remove from load balancer if not ready)
readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
```

### Horizontal Pod Autoscaling

```bash
# Create HPA
kubectl autoscale deployment socrates-api \
  --min=2 --max=10 \
  --cpu-percent=70 \
  -n socrates-prod

# Monitor scaling
kubectl get hpa -n socrates-prod -w
```

---

## Environment Configuration

### Production Environment Variables

```bash
# See .env.production.example for all variables

# Critical variables that MUST be set:
export ENVIRONMENT=production
export JWT_SECRET_KEY=$(python scripts/generate_jwt_secret.py --format hex)
export ANTHROPIC_API_KEY=sk-ant-...
export DATABASE_URL=postgresql://user:pass@postgres:5432/socrates
export REDIS_URL=redis://redis:6379
export ALLOWED_ORIGINS=https://socrates.app,https://app.socrates.app
```

### Loading from Environment File

```bash
# Load from .env.production
export $(cat .env.production | xargs)

# Verify
env | grep SOCRATES_API
```

### Secret Management (Production)

#### AWS Secrets Manager

```bash
# Store secrets in AWS Secrets Manager
aws secretsmanager create-secret \
  --name socrates/production/jwt-secret \
  --secret-string "$(python scripts/generate_jwt_secret.py --format hex)"

# Retrieve in application
import json
import boto3

client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='socrates/production/jwt-secret')
jwt_secret = json.loads(secret['SecretString'])['jwt_secret']
```

#### HashiCorp Vault

```bash
# Write secrets to Vault
vault kv put secret/socrates/production \
  jwt_secret="$(python scripts/generate_jwt_secret.py --format hex)" \
  anthropic_api_key="sk-ant-..."

# Read in application
import hvac
client = hvac.Client(url='https://vault.example.com')
secret = client.secrets.kv.read_secret_version(path='socrates/production')
```

---

## Database Setup

### PostgreSQL Initialization

```bash
# Create database and user
psql -U postgres -h postgres.example.com <<EOF
CREATE DATABASE socrates;
CREATE USER socrates_user WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE socrates TO socrates_user;
EOF

# Run migrations (automatic on startup via Alembic)
docker exec socrates-api alembic upgrade head
```

### Database Backup

```bash
# Manual backup
pg_dump -h postgres.example.com -U socrates_user -d socrates \
  | gzip > socrates_backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Automated backup (cron job)
0 2 * * * /scripts/backup_database.sh

# Upload to S3
aws s3 cp socrates_backup*.sql.gz s3://my-backups/socrates/
```

### Database Restoration

```bash
# Restore from backup
gunzip -c socrates_backup_20240115_020000.sql.gz | \
  psql -h postgres.example.com -U socrates_user -d socrates
```

---

## Monitoring & Observability

### Prometheus Setup

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'socrates-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboards

```bash
# Access Grafana
http://localhost:3000
# Default credentials: admin/admin

# Add Prometheus data source
- URL: http://prometheus:9090
- Access: Browser

# Import dashboard
- Dashboard ID: 12114 (FastAPI Prometheus)
```

### Logging Setup

```bash
# Application logs
docker logs socrates-api | tail -100

# Log aggregation with ELK Stack
curl -X POST "localhost:9200/socrates-logs/_doc" \
  -H 'Content-Type: application/json' \
  -d '{"timestamp": "2024-01-15T10:30:00Z", "level": "ERROR"}'
```

### Health Endpoints

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed health check
curl http://localhost:8000/health/detailed | jq .

# Metrics
curl http://localhost:8000/metrics

# Query performance
curl http://localhost:8000/metrics/queries | jq .
```

---

## Security Hardening

### HTTPS/TLS Configuration

```bash
# Generate self-signed certificate (development only)
openssl req -x509 -newkey rsa:4096 -nodes \
  -out cert.pem -keyout key.pem -days 365

# Use proper certificates in production (Let's Encrypt, etc.)
certbot certonly --standalone -d socrates.app
```

### Nginx Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name api.socrates.app;

    ssl_certificate /etc/letsencrypt/live/socrates.app/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/socrates.app/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://socrates-api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.socrates.app;
    return 301 https://$server_name$request_uri;
}
```

### Firewall Rules

```bash
# Allow only necessary ports
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 5432/tcp  # PostgreSQL (internal only)
sudo ufw allow 6379/tcp  # Redis (internal only)
```

---

## Troubleshooting

### Common Issues

#### 1. API Container Won't Start

```bash
# Check logs
docker logs socrates-api

# Check environment variables
docker inspect socrates-api | grep Env

# Test database connection
docker exec socrates-api \
  python -c "import psycopg2; psycopg2.connect('postgresql://...')"
```

#### 2. Database Connection Errors

```bash
# Verify PostgreSQL is running
docker ps | grep postgres

# Test connection
psql -h postgres -U socrates_user -d socrates -c "SELECT 1"

# Check database logs
docker logs postgres
```

#### 3. Rate Limiting Not Working

```bash
# Verify Redis is running
docker ps | grep redis

# Test Redis connection
redis-cli -h redis ping

# Check rate limiter logs
docker logs socrates-api | grep "rate"
```

#### 4. Slow Responses

```bash
# Check metrics
curl http://localhost:8000/metrics/queries/slowest

# Check database query profiling
curl http://localhost:8000/metrics/queries

# Check system resources
docker stats socrates-api
```

### Debug Mode

```bash
# Enable debug logging
ENVIRONMENT=development LOG_LEVEL=DEBUG docker-compose up

# Enable Python debugger
docker exec -it socrates-api python -m pdb main.py
```

---

## Scaling & Performance

### Horizontal Scaling

```bash
# Docker Compose - scale to 3 instances
docker-compose up -d --scale socrates-api=3

# Kubernetes - scale to 5 replicas
kubectl scale deployment socrates-api --replicas=5 -n socrates-prod

# Monitor scaling
kubectl top nodes
kubectl top pods
```

### Load Balancing

```yaml
# Kubernetes Service for load balancing
apiVersion: v1
kind: Service
metadata:
  name: socrates-api
spec:
  type: LoadBalancer
  ports:
    - port: 80
      targetPort: 8000
  selector:
    app: socrates-api
```

### Caching Strategy

- **User data:** 1 hour cache TTL
- **Project metadata:** 30 minutes cache TTL
- **Search results:** 30 minutes cache TTL
- **Session data:** 24 hours cache TTL

### Database Optimization

```sql
-- Create indexes
CREATE INDEX idx_projects_owner_archived ON projects(owner, is_archived);
CREATE INDEX idx_projects_updated_desc ON projects(updated_at DESC);
CREATE INDEX idx_projects_search ON projects USING GIN(search_vector);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM projects WHERE owner = 'user123';
```

---

## Rollback Procedures

### Docker Rollback

```bash
# Rollback to previous image
docker-compose down
docker image rm socrates-api:latest
docker pull ghcr.io/your-org/socrates-api:previous-tag
docker-compose up -d
```

### Kubernetes Rollback

```bash
# View rollout history
kubectl rollout history deployment socrates-api -n socrates-prod

# Rollback to previous version
kubectl rollout undo deployment socrates-api -n socrates-prod

# Rollback to specific revision
kubectl rollout undo deployment socrates-api \
  --to-revision=2 -n socrates-prod

# Monitor rollback
kubectl rollout status deployment socrates-api -n socrates-prod
```

---

## Support & Resources

- **API Documentation:** http://localhost:8000/docs
- **Status Page:** http://localhost:8000/health/detailed
- **Metrics Dashboard:** http://localhost:3000 (Grafana)
- **Issue Tracker:** https://github.com/your-org/socrates/issues
- **Documentation:** https://docs.socrates.app
