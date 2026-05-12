# Production Deployment Guide for Socrates

## Pre-Deployment Checklist

### Security & Compliance
- [ ] Generate strong encryption keys (32+ characters, alphanumeric + symbols)
- [ ] Create `.env.production` with all secrets (never commit)
- [ ] Set `ENVIRONMENT=production`
- [ ] Disable `DEBUG=true` (ensure `DEBUG=false`)
- [ ] Configure CORS_ORIGINS to your specific domain(s)
- [ ] Enable HTTPS/TLS with valid certificates
- [ ] Set up rate limiting: `RATE_LIMIT_PER_MINUTE=60`
- [ ] Configure authentication: `AUTH_ENABLED=true`
- [ ] Enable request signing: `REQUIRE_REQUEST_SIGNATURE=true`

### Database & Storage
- [ ] Use PostgreSQL (not SQLite) for data durability
- [ ] Configure PostgreSQL with:
  - Replication (for high availability)
  - Automated backups (daily minimum)
  - Connection pooling (pgBouncer or PgPool)
- [ ] Set up persistent volumes:
  - `socrates_data/` for vector DB and project data
  - `socrates_logs/` for application logs
  - `postgres_data/` for PostgreSQL data
- [ ] Configure database backups:
  ```bash
  pg_dump -h postgres -U socrates -d socrates_prod > backup_$(date +%Y%m%d_%H%M%S).sql
  ```

### Cache & Performance
- [ ] Enable Redis for distributed caching
- [ ] Configure Redis persistence:
  - `appendonly yes` (AOF - append-only file)
  - `appendfsync everysec` (balance performance/durability)
- [ ] Set up Redis replication for HA
- [ ] Configure connection pooling: `REDIS_POOL_SIZE=20`
- [ ] Set cache TTLs appropriately:
  - Embeddings: 86400s (24 hours)
  - Knowledge: 43200s (12 hours)
  - Session: 3600s (1 hour)

### Resource Management
- [ ] Set resource limits in docker-compose or Kubernetes:
  ```yaml
  resources:
    limits:
      cpus: '2'
      memory: 4G
    reservations:
      cpus: '1'
      memory: 2G
  ```
- [ ] Configure connection limits:
  - `MAX_DATABASE_CONNECTIONS=20`
  - `MAX_REDIS_CONNECTIONS=20`
  - `MAX_CONCURRENT_GENERATIONS=5`
- [ ] Set up request timeouts:
  - API request: `REQUEST_TIMEOUT=30s`
  - Database query: `DB_QUERY_TIMEOUT=10s`
  - LLM generation: `LLM_TIMEOUT=120s`

### Observability & Monitoring
- [ ] Set up log aggregation (ELK, DataDog, CloudWatch)
- [ ] Enable structured logging: `LOG_FORMAT=json`
- [ ] Configure log levels:
  - Production: `LOG_LEVEL=INFO`
  - Critical issues only: `LOG_LEVEL=WARNING`
- [ ] Set up Prometheus metrics collection
- [ ] Configure health check endpoints:
  - `/health` - basic liveness
  - `/health/detailed` - comprehensive status
- [ ] Set up alerting on:
  - API response times > 5s
  - Error rate > 1%
  - Database connection failures
  - Redis unavailable
  - Disk space < 10%
  - Memory usage > 90%

---

## Deployment Architecture

### Three-Tier Deployment

```
┌─────────────────────────────────────────────────────────┐
│                    LOAD BALANCER                         │
│              (HTTPS/TLS termination)                     │
└─────────────┬───────────────────────────────────┬───────┘
              │                                   │
     ┌────────▼────────┐              ┌──────────▼─────────┐
     │  API Instance 1 │              │  API Instance 2    │
     │  (FastAPI)      │              │  (FastAPI)         │
     └────────┬────────┘              └──────────┬─────────┘
              │                                  │
     ┌────────▼──────────────────────────────────▼─────────┐
     │        Shared Service Layer (Stateless)            │
     ├──────────────────────────────────────────────────────┤
     │  ┌──────────┐  ┌────────┐  ┌─────────────┐         │
     │  │PostgreSQL│  │ Redis  │  │  ChromaDB   │         │
     │  │(RW + RR) │  │(Cluster)  │ (Distributed)│        │
     │  └──────────┘  └────────┘  └─────────────┘         │
     └──────────────────────────────────────────────────────┘
```

### Load Balancer Configuration

**Nginx (Docker/standalone)**:
```nginx
upstream socrates_api {
    least_conn;
    server api1:8000 max_fails=3 fail_timeout=30s;
    server api2:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 443 ssl http2;
    server_name api.socrates.example.com;

    ssl_certificate /etc/nginx/certs/cert.pem;
    ssl_certificate_key /etc/nginx/certs/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://socrates_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 10s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    location /health {
        proxy_pass http://socrates_api;
        access_log off;
    }
}
```

**Kubernetes Service**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: socrates-api-lb
spec:
  type: LoadBalancer
  selector:
    app: socrates-api
  ports:
    - port: 443
      targetPort: 8000
      protocol: TCP
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 3600
```

---

## Database Setup

### PostgreSQL Configuration

**Initialization**:
```bash
# Create database
createdb -h postgres -U postgres socrates_prod

# Create user
createuser -h postgres -U postgres -d socrates_user
psql -h postgres -U postgres -c "ALTER USER socrates_user WITH PASSWORD 'strong_password_here';"

# Run migrations
alembic upgrade head
```

**Connection String**:
```env
DATABASE_URL=postgresql://socrates_user:password@postgres:5432/socrates_prod?sslmode=require
```

**Performance Tuning**:
```sql
-- Increase connection pool
ALTER SYSTEM SET max_connections = 100;

-- Enable query parallelization
ALTER SYSTEM SET max_parallel_workers = 4;
ALTER SYSTEM SET max_parallel_workers_per_gather = 2;

-- Optimize work memory
ALTER SYSTEM SET work_mem = '256MB';

-- Enable query planning improvement
ALTER SYSTEM SET effective_cache_size = '2GB';

-- Reload configuration
SELECT pg_reload_conf();
```

**Backups**:
```bash
# Automated daily backup
0 2 * * * pg_dump -h postgres -U socrates_user socrates_prod | gzip > /backups/socrates_$(date +\%Y\%m\%d).sql.gz

# Point-in-time recovery
pg_basebackup -h postgres -U replication_user -D /mnt/backup -Pv -Xstream -C
```

### High Availability Setup

**Read Replicas** (PostgreSQL streaming replication):
```yaml
# Primary
postgres-primary:
  image: postgres:15
  environment:
    POSTGRES_REPLICATION_MODE: master
    POSTGRES_REPLICATION_USER: repl_user
    POSTGRES_REPLICATION_PASSWORD: repl_pass

# Replica
postgres-replica:
  image: postgres:15
  environment:
    POSTGRES_REPLICATION_MODE: slave
    POSTGRES_MASTER_SERVICE: postgres-primary
```

**Connection Pooling** (PgPool):
```yaml
pgpool:
  image: pgpool2:4.4
  environment:
    PGPOOL_BACKEND_NODES: "0:postgres-primary:5432 1:postgres-replica:5432"
    PGPOOL_LOAD_BALANCE_MODE: "on"
    PGPOOL_SR_CHECK_PERIOD: 10
  ports:
    - "5433:5432"
```

---

## TLS/HTTPS Configuration

### Certificate Management

**Option 1: Let's Encrypt (Automatic)**:
```bash
# Using Certbot
certbot certonly \
  --standalone \
  -d api.socrates.example.com \
  -d socrates.example.com

# Auto-renew
0 0 * * * certbot renew --quiet
```

**Option 2: Self-Signed (Development)**:
```bash
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout key.pem -out cert.pem -days 365
```

### Docker Compose with TLS

```yaml
services:
  api:
    image: nireus79/socrates-api:latest
    ports:
      - "8000:8000"
    volumes:
      - /etc/letsencrypt/live/api.socrates.example.com:/certs:ro
    environment:
      SSL_CERT_FILE: /certs/fullchain.pem
      SSL_KEY_FILE: /certs/privkey.pem

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
```

---

## Monitoring & Alerting

### Health Check Configuration

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "https://localhost:8000/health/detailed"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Prometheus Metrics

**Metrics to collect**:
```
# API Performance
http_requests_total{endpoint, method, status}
http_request_duration_seconds{endpoint, method}
http_requests_in_progress

# LLM Performance
llm_generation_duration_seconds
llm_tokens_generated
llm_errors_total

# Database Performance
db_query_duration_seconds{query_type}
db_connections_active
db_connection_errors_total

# Cache Performance
cache_hits_total{cache_type}
cache_misses_total{cache_type}
cache_evictions_total

# System
process_resident_memory_bytes
process_cpu_seconds_total
go_goroutines  # or equivalent for Python

# Custom
socrates_projects_total
socrates_active_sessions
socrates_embeddings_generated_total
```

**Prometheus Configuration**:
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'socrates-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Alerting Rules

```yaml
groups:
  - name: socrates
    interval: 30s
    rules:
      - alert: APIHighErrorRate
        expr: |
          (sum(rate(http_requests_total{status=~"5.."}[5m])) /
           sum(rate(http_requests_total[5m]))) > 0.01
        for: 5m
        annotations:
          summary: "API error rate > 1%"

      - alert: DatabaseConnectionFailed
        expr: increase(db_connection_errors_total[5m]) > 0
        for: 2m
        annotations:
          summary: "Database connection errors detected"

      - alert: RedisUnavailable
        expr: redis_up == 0
        for: 1m
        annotations:
          summary: "Redis is unavailable"

      - alert: HighMemoryUsage
        expr: |
          (process_resident_memory_bytes /
           node_memory_MemTotal_bytes) > 0.9
        for: 5m
        annotations:
          summary: "Memory usage > 90%"

      - alert: DiskSpaceLow
        expr: |
          (node_filesystem_avail_bytes{mountpoint="/"} /
           node_filesystem_size_bytes{mountpoint="/"}) < 0.1
        for: 10m
        annotations:
          summary: "Disk space < 10%"
```

### Log Aggregation

**ELK Stack Example**:
```yaml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
    environment:
      discovery.type: single-node
    volumes:
      - elastic_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.5.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

  kibana:
    image: docker.elastic.co/kibana/kibana:8.5.0
    ports:
      - "5601:5601"

  api:
    logging:
      driver: "json-file"
      options:
        labels: "service=socrates-api"
        max-size: "10m"
        max-file: "3"
```

**Logstash Configuration**:
```
input {
  http {
    port => 8080
    codec => json
  }
}

filter {
  if [logger_name] == "socratic_system" {
    mutate {
      add_field => { "[@metadata][index_name]" => "socrates-%{+YYYY.MM.dd}" }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "%{[@metadata][index_name]}"
  }
}
```

---

## Upgrade & Maintenance

### Zero-Downtime Deployments

**Blue-Green Deployment**:
```bash
#!/bin/bash
# Deploy new version while keeping current running

# 1. Start new version on different port
docker-compose -f docker-compose.blue.yml up -d

# 2. Run migrations
docker-compose -f docker-compose.blue.yml exec api alembic upgrade head

# 3. Run smoke tests
curl http://localhost:9000/health/detailed

# 4. Switch load balancer
sed -i 's/blue/green/g' /etc/nginx/upstream.conf
nginx -s reload

# 5. Stop old version
docker-compose -f docker-compose.green.yml down
```

**Rolling Update** (Kubernetes):
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: socrates-api
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: socrates-api
  template:
    metadata:
      labels:
        app: socrates-api
    spec:
      containers:
      - name: api
        image: nireus79/socrates-api:v1.2.3
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

### Database Migrations

```bash
# Pre-deployment checks
alembic current  # Check current version
alembic heads    # Check all heads

# Backup before migration
pg_dump socrates_prod > backup_pre_migration.sql

# Dry run
alembic upgrade head --sql > migration_plan.sql

# Execute migration
alembic upgrade head

# Verify
alembic current
sqlalchemy-utils db_status

# Rollback if needed
alembic downgrade -1
```

### Rollback Procedure

```bash
# 1. Stop current version
docker-compose down

# 2. Restore previous database backup
psql socrates_prod < backup_pre_migration.sql

# 3. Start previous version
git checkout v1.2.2  # Previous tag
docker-compose up -d

# 4. Verify
curl https://api.socrates.example.com/health/detailed

# 5. Investigate failure
docker-compose logs api
```

---

## Security Hardening

### Network Security

**Firewall Rules**:
```bash
# Allow only necessary ports
# 443: HTTPS API
# 5432: PostgreSQL (internal only)
# 6379: Redis (internal only)

ufw allow 443/tcp
ufw allow 22/tcp  # SSH (restrict to admin IPs)

# Deny by default
ufw default deny incoming
```

**Network Isolation**:
```yaml
networks:
  api-network:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.name: socrates_api

  db-network:
    driver: bridge
    internal: true  # No external access

services:
  api:
    networks:
      - api-network
      - db-network

  postgres:
    networks:
      - db-network
```

### Secrets Management

**Environment Variables** (.env.production - never commit):
```env
# API Keys
ANTHROPIC_API_KEY=sk-ant-xxxxx
ENCRYPTION_KEY=your-32-char-key-here-minimum

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db
DATABASE_POOL_SIZE=20
DATABASE_ECHO=false

# Redis
REDIS_URL=redis://user:pass@redis:6379/0

# Security
JWT_SECRET_KEY=your-secret-jwt-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Authentication
AUTH_ENABLED=true
REQUIRE_REQUEST_SIGNATURE=true
RATE_LIMIT_PER_MINUTE=60

# CORS
CORS_ORIGINS=https://app.socrates.example.com,https://admin.socrates.example.com

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# System
ENVIRONMENT=production
DEBUG=false
WORKERS=4
```

**Vault Integration** (HashiCorp Vault):
```python
from hvac import Client

vault_client = Client(url="https://vault.example.com", token=vault_token)

secrets = vault_client.secrets.kv.read_secret_version(
    path="socrates/production"
)

api_key = secrets['data']['data']['ANTHROPIC_API_KEY']
```

### API Security

**Authentication**:
```python
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthCredentials = Security(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

**Rate Limiting**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/generate")
@limiter.limit("60/minute")
async def generate(request: Request):
    # API endpoint logic
    pass
```

**Input Validation**:
```python
from pydantic import BaseModel, validator

class ProjectCreate(BaseModel):
    name: str
    description: str

    @validator('name')
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        if len(v) > 255:
            raise ValueError('Name too long')
        return v.strip()
```

---

## Performance Tuning

### Concurrency Settings

```env
# FastAPI Workers
WORKERS=4  # 2 * CPU cores for production

# Database Connection Pool
DATABASE_POOL_SIZE=20
DATABASE_POOL_RECYCLE=3600

# Redis Connection Pool
REDIS_POOL_SIZE=20

# Concurrent LLM Generations
MAX_CONCURRENT_GENERATIONS=5

# HTTP Client Pool
HTTP_POOL_CONNECTIONS=100
HTTP_POOL_MAXSIZE=100
```

### Caching Strategy

```python
from functools import lru_cache
from redis import Redis

redis_client = Redis(host='redis', port=6379)

# Cache LLM embeddings for 24 hours
@cache_with_ttl(redis_client, ttl=86400)
async def get_embeddings(text: str):
    return await embedding_model.embed(text)

# Cache knowledge entries for 12 hours
@cache_with_ttl(redis_client, ttl=43200)
async def get_knowledge(query: str):
    return await knowledge_db.search(query)
```

### Query Optimization

```python
# Use connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Use bulk operations
session.bulk_insert_mappings(Knowledge, [
    {"content": item["content"], "vector": item["vector"]}
    for item in batch
])
session.commit()

# Use indexes
class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True)
    owner = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, index=True)
    __table_args__ = (
        Index('idx_owner_created', 'owner', 'created_at'),
    )
```

---

## Runbook: Common Operations

### Scaling API Instances

```bash
# Docker Compose - scale to 3 instances
docker-compose up -d --scale api=3

# Kubernetes - scale to 5 replicas
kubectl scale deployment socrates-api --replicas=5

# Monitor scaling
kubectl get pods -l app=socrates-api
watch 'curl http://localhost:8000/health/detailed | jq .version'
```

### Clear Cache

```bash
# Clear all Redis cache
redis-cli -h redis flushall

# Clear specific cache key pattern
redis-cli -h redis KEYS "embedding:*" | xargs redis-cli -h redis DEL

# Verify
redis-cli -h redis DBSIZE
```

### Database Maintenance

```bash
# Vacuum (optimize storage)
psql -h postgres -U socrates_user socrates_prod -c "VACUUM ANALYZE;"

# Check table sizes
psql -h postgres -U socrates_user socrates_prod << EOF
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
EOF

# Monitor slow queries
psql -h postgres -U socrates_user socrates_prod << EOF
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1 second
SELECT pg_reload_conf();
EOF
```

### View System Status

```bash
# API health
curl https://api.socrates.example.com/health/detailed | jq

# Database status
docker-compose exec postgres pg_isready

# Redis status
docker-compose exec redis redis-cli PING

# Logs (last 100 lines)
docker-compose logs --tail=100 api

# Real-time logs
docker-compose logs -f api
```

---

## Summary

Production deployment requires:
1. **Security**: TLS, authentication, encryption, secrets management
2. **Reliability**: Redundancy, backups, health checks, monitoring
3. **Performance**: Connection pooling, caching, optimization
4. **Observability**: Metrics, logs, alerting, dashboards
5. **Operability**: Runbooks, automation, clear procedures

Invest in monitoring and alerting early—it pays for itself in reduced incident response time.
