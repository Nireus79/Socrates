# Observability Guide for Socrates

## Overview

Observability encompasses three pillars: **logs**, **metrics**, and **traces**. This guide covers implementing comprehensive observability for production Socrates deployments.

```
┌──────────────────────────────────────────────────────┐
│              Observability Stack                     │
├──────────────────────────────────────────────────────┤
│  Logs      → Structured JSON → ELK/Loki/CloudWatch │
│  Metrics   → Prometheus      → Grafana/DataDog      │
│  Traces    → OpenTelemetry  → Jaeger/Tempo/DataDog │
│  Alerts    → Prometheus Rules → Slack/PagerDuty    │
└──────────────────────────────────────────────────────┘
```

---

## Structured Logging

### Configuration

**Enable JSON Logging**:
```env
LOG_FORMAT=json
LOG_LEVEL=INFO
LOG_OUTPUT=stdout
```

**Python Setup**:
```python
import logging
import json
import sys
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_object = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_object["exception"] = self.formatException(record.exc_info)

        # Add custom fields
        if hasattr(record, 'user_id'):
            log_object['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_object['request_id'] = record.request_id

        return json.dumps(log_object)

# Configure handler
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())

logger = logging.getLogger("socratic_system")
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

### Request Tracking

**Middleware for Request Context**:
```python
from fastapi import Request
from contextvars import ContextVar
import uuid

request_id_contextvar = ContextVar('request_id', default=None)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    # Generate or extract request ID
    request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
    request_id_contextvar.set(request_id)

    # Add to response headers
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# Use in logging
import logging
extra = {"request_id": request_id_contextvar.get()}
logger.info("Processing generation request", extra=extra)
```

### Log Events to Emit

**API Lifecycle**:
```python
logger.info("api.request.started", extra={
    "request_id": request_id,
    "method": request.method,
    "path": request.url.path,
    "client_ip": request.client.host,
})

logger.info("api.request.completed", extra={
    "request_id": request_id,
    "status_code": response.status_code,
    "duration_ms": elapsed_time,
})

logger.error("api.request.failed", extra={
    "request_id": request_id,
    "error": str(exc),
    "status_code": 500,
})
```

**Database Operations**:
```python
logger.info("database.query.executed", extra={
    "query_type": "SELECT",
    "table": "projects",
    "duration_ms": query_time,
    "rows_affected": len(results),
})

logger.warning("database.query.slow", extra={
    "query": truncate_query(sql),
    "duration_ms": 5000,
    "threshold_ms": 1000,
})

logger.error("database.connection.failed", extra={
    "error": str(exc),
    "host": db_host,
    "retries": 3,
})
```

**LLM Generation**:
```python
logger.info("llm.generation.started", extra={
    "request_id": request_id,
    "model": "claude-3-sonnet",
    "tokens_estimated": 500,
})

logger.info("llm.generation.completed", extra={
    "request_id": request_id,
    "tokens_input": 150,
    "tokens_output": 280,
    "duration_ms": 3500,
    "cost": 0.045,
})

logger.warning("llm.generation.retried", extra={
    "request_id": request_id,
    "error": "rate_limit_exceeded",
    "retry_attempt": 2,
    "backoff_ms": 5000,
})
```

**Cache Operations**:
```python
logger.debug("cache.hit", extra={
    "key": "embedding:abc123",
    "ttl_remaining_ms": 43200000,
})

logger.debug("cache.miss", extra={
    "key": "knowledge:query123",
    "reason": "expired",
})

logger.info("cache.eviction", extra={
    "keys_evicted": 150,
    "reason": "memory_pressure",
    "memory_freed_mb": 256,
})
```

---

## Metrics Collection

### Prometheus Integration

**Installation**:
```bash
pip install prometheus-client
```

**Setup**:
```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

# HTTP Request Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0)
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests in progress',
    ['method', 'endpoint']
)

# LLM Metrics
llm_generation_duration_seconds = Histogram(
    'llm_generation_duration_seconds',
    'LLM generation duration',
    ['model'],
    buckets=(1, 5, 10, 30, 60, 120)
)

llm_tokens_generated = Counter(
    'llm_tokens_generated',
    'Total tokens generated',
    ['model']
)

llm_generation_errors_total = Counter(
    'llm_generation_errors_total',
    'LLM generation errors',
    ['model', 'error_type']
)

# Database Metrics
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['query_type'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0)
)

db_connections_active = Gauge(
    'db_connections_active',
    'Active database connections'
)

db_connection_errors_total = Counter(
    'db_connection_errors_total',
    'Database connection errors',
    ['error_type']
)

# Cache Metrics
cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

cache_size_bytes = Gauge(
    'cache_size_bytes',
    'Cache size in bytes',
    ['cache_type']
)

# Custom Business Metrics
projects_total = Counter(
    'projects_total',
    'Total projects created',
    ['owner']
)

active_sessions = Gauge(
    'active_sessions',
    'Active user sessions'
)

embeddings_generated_total = Counter(
    'embeddings_generated_total',
    'Total embeddings generated'
)

# Start metrics server on port 8001
start_http_server(8001)
```

### Middleware for Metrics

```python
from fastapi import Request
import time

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()

    # Track in-progress requests
    http_requests_in_progress.labels(
        method=request.method,
        endpoint=request.url.path
    ).inc()

    try:
        response = await call_next(request)
        duration = time.time() - start_time

        # Record metrics
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)

        http_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()

        return response
    finally:
        http_requests_in_progress.labels(
            method=request.method,
            endpoint=request.url.path
        ).dec()
```

### Recording Metrics in Code

```python
# LLM Generation
start = time.time()
response = await client.messages.create(...)
duration = time.time() - start

llm_generation_duration_seconds.labels(model="claude-3-sonnet").observe(duration)
llm_tokens_generated.labels(model="claude-3-sonnet").inc(response.usage.output_tokens)

# Database Query
start = time.time()
results = session.query(Project).filter(...).all()
duration = time.time() - start

db_query_duration_seconds.labels(query_type="SELECT").observe(duration)

# Cache Operations
if is_cached:
    cache_hits_total.labels(cache_type="embeddings").inc()
else:
    cache_misses_total.labels(cache_type="embeddings").inc()

# Update cache size
redis_size = redis_client.info()['used_memory']
cache_size_bytes.labels(cache_type="redis").set(redis_size)
```

### Prometheus Configuration

**prometheus.yml**:
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'socrates-monitor'

scrape_configs:
  - job_name: 'socrates-api'
    static_configs:
      - targets: ['localhost:8001']  # Metrics port
    scrape_interval: 15s
    scrape_timeout: 10s

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']  # postgres_exporter
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']  # redis_exporter
    scrape_interval: 30s

  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']  # node_exporter
    scrape_interval: 30s
```

---

## Health Checks

### Implementation

**Liveness Check** (is the service alive?):
```python
@app.get("/health")
async def health_liveness():
    return {
        "status": "ok",
        "version": "1.2.3",
        "timestamp": datetime.utcnow().isoformat(),
    }
```

**Readiness Check** (is the service ready to serve traffic?):
```python
@app.get("/health/ready")
async def health_readiness():
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "embeddings_model": await check_model(),
    }

    all_ready = all(checks.values())
    status_code = 200 if all_ready else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "ready": all_ready,
            "checks": checks,
        }
    )

async def check_database():
    try:
        async with get_db_session() as session:
            await session.execute(text("SELECT 1"))
            return True
    except:
        return False

async def check_redis():
    try:
        redis_client.ping()
        return True
    except:
        return False
```

**Detailed Health Check** (full status):
```python
@app.get("/health/detailed")
async def health_detailed():
    import psutil
    import pkg_resources

    return {
        "status": "ok",
        "version": get_version(),
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": time.time() - start_time,
        "services": {
            "database": {
                "healthy": await check_database(),
                "connections": db_pool.size(),
            },
            "redis": {
                "healthy": await check_redis(),
                "memory_mb": redis_client.info()['used_memory_mb'],
            },
            "embeddings": {
                "model_loaded": embeddings_model is not None,
                "cache_hits": cache_hits_total._value.get(),
            },
        },
        "system": {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
        },
        "dependencies": {
            "anthropic": pkg_resources.get_distribution("anthropic").version,
            "fastapi": pkg_resources.get_distribution("fastapi").version,
        },
    }
```

### Docker Compose Health Check

```yaml
services:
  api:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart_policy:
      condition: on-failure
      delay: 5s
      max_attempts: 5

  postgres:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U socrates_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
```

### Kubernetes Health Probes

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: socrates-api
spec:
  containers:
  - name: api
    image: nireus79/socrates-api:latest

    livenessProbe:
      httpGet:
        path: /health
        port: 8000
        scheme: HTTP
      initialDelaySeconds: 30
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 3

    readinessProbe:
      httpGet:
        path: /health/ready
        port: 8000
        scheme: HTTP
      initialDelaySeconds: 10
      periodSeconds: 5
      timeoutSeconds: 3
      failureThreshold: 2

    startupProbe:
      httpGet:
        path: /health
        port: 8000
        scheme: HTTP
      initialDelaySeconds: 0
      periodSeconds: 10
      timeoutSeconds: 3
      failureThreshold: 30  # 5 minutes max
```

---

## Distributed Tracing

### OpenTelemetry Setup

**Installation**:
```bash
pip install opentelemetry-api opentelemetry-sdk
pip install opentelemetry-exporter-jaeger
pip install opentelemetry-instrumentation-fastapi
pip install opentelemetry-instrumentation-sqlalchemy
```

**Configuration**:
```python
from opentelemetry import trace, metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

# Jaeger exporter
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)

# Set up tracer
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# Instrument libraries
FastAPIInstrumentor.instrument_app(app)
SQLAlchemyInstrumentor().instrument(engine=db_engine)

# Get tracer
tracer = trace.get_tracer(__name__)
```

### Manual Span Creation

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def generate_content(project_id: str, prompt: str):
    with tracer.start_as_current_span("generate_content") as span:
        span.set_attribute("project_id", project_id)
        span.set_attribute("prompt_length", len(prompt))

        # Database lookup
        with tracer.start_as_current_span("fetch_project") as db_span:
            project = await fetch_project(project_id)
            db_span.set_attribute("found", project is not None)

        # LLM call
        with tracer.start_as_current_span("llm_generation") as llm_span:
            response = await client.messages.create(
                model="claude-3-sonnet",
                messages=[{"role": "user", "content": prompt}]
            )
            llm_span.set_attribute("tokens_input", response.usage.input_tokens)
            llm_span.set_attribute("tokens_output", response.usage.output_tokens)

        return response.content[0].text
```

### Jaeger UI Access

```bash
# Docker Compose - Jaeger runs on port 16686
docker-compose up jaeger

# Then visit: http://localhost:16686/search
```

---

## Dashboards with Grafana

### Docker Compose Setup

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
    volumes:
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus

volumes:
  prometheus_data:
  grafana_data:
```

### Grafana Dashboards

**Key Metrics Dashboard**:
```json
{
  "dashboard": {
    "title": "Socrates API Overview",
    "panels": [
      {
        "title": "Requests per Second",
        "targets": [
          {
            "expr": "rate(http_requests_total[1m])"
          }
        ]
      },
      {
        "title": "Request Duration (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, http_request_duration_seconds_bucket)"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Active Database Connections",
        "targets": [
          {
            "expr": "db_connections_active"
          }
        ]
      },
      {
        "title": "Cache Hit Rate",
        "targets": [
          {
            "expr": "cache_hits_total / (cache_hits_total + cache_misses_total)"
          }
        ]
      },
      {
        "title": "LLM Generation Time (p50)",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, llm_generation_duration_seconds_bucket)"
          }
        ]
      }
    ]
  }
}
```

**System Resources Dashboard**:
```json
{
  "dashboard": {
    "title": "System Resources",
    "panels": [
      {
        "title": "CPU Usage",
        "targets": [
          {
            "expr": "rate(process_cpu_seconds_total[5m]) * 100"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "targets": [
          {
            "expr": "process_resident_memory_bytes / 1024 / 1024"
          }
        ]
      },
      {
        "title": "Disk I/O",
        "targets": [
          {
            "expr": "rate(node_disk_io_time_seconds_total[5m])"
          }
        ]
      },
      {
        "title": "Network Bytes In",
        "targets": [
          {
            "expr": "rate(node_network_receive_bytes_total[5m])"
          }
        ]
      }
    ]
  }
}
```

---

## Alerting

### Alert Rules

**prometheus-rules.yml**:
```yaml
groups:
  - name: socrates
    interval: 30s
    rules:
      # API Alerts
      - alert: HighErrorRate
        expr: |
          (sum(rate(http_requests_total{status=~"5.."}[5m])) /
           sum(rate(http_requests_total[5m]))) > 0.01
        for: 5m
        annotations:
          summary: "API error rate > 1% for 5 minutes"
          description: "Error rate is {{ $value | humanizePercentage }}"

      - alert: SlowResponses
        expr: |
          histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 5
        for: 10m
        annotations:
          summary: "API p95 response time > 5s"

      - alert: HighConcurrency
        expr: http_requests_in_progress > 100
        for: 2m
        annotations:
          summary: "More than 100 concurrent requests"

      # Database Alerts
      - alert: DatabaseConnectionFailed
        expr: increase(db_connection_errors_total[5m]) > 0
        for: 2m
        annotations:
          summary: "Database connection errors detected"

      - alert: DatabasePoolExhausted
        expr: db_connections_active >= 19
        for: 5m
        annotations:
          summary: "Database connection pool almost full"

      - alert: SlowDatabaseQueries
        expr: |
          histogram_quantile(0.95, rate(db_query_duration_seconds_bucket[5m])) > 1
        for: 10m
        annotations:
          summary: "Database queries taking > 1 second (p95)"

      # Cache Alerts
      - alert: LowCacheHitRate
        expr: |
          rate(cache_hits_total[5m]) /
          (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m])) < 0.5
        for: 15m
        annotations:
          summary: "Cache hit rate < 50%"

      - alert: RedisUnavailable
        expr: up{job="redis"} == 0
        for: 1m
        annotations:
          summary: "Redis is unavailable"

      # System Alerts
      - alert: HighMemoryUsage
        expr: |
          (process_resident_memory_bytes / 1024 / 1024) > 3500
        for: 5m
        annotations:
          summary: "Memory usage > 3.5 GB"

      - alert: HighCPUUsage
        expr: |
          rate(process_cpu_seconds_total[5m]) * 100 > 80
        for: 10m
        annotations:
          summary: "CPU usage > 80%"

      - alert: DiskSpaceLow
        expr: |
          (node_filesystem_avail_bytes{mountpoint="/"} /
           node_filesystem_size_bytes{mountpoint="/"}) < 0.1
        for: 10m
        annotations:
          summary: "Disk space < 10%"

      # LLM Alerts
      - alert: LLMGenerationFailures
        expr: increase(llm_generation_errors_total[5m]) > 5
        for: 5m
        annotations:
          summary: "{{ $value }} LLM generation errors in 5 minutes"

      - alert: LLMSlowGenerations
        expr: |
          histogram_quantile(0.95, rate(llm_generation_duration_seconds_bucket[5m])) > 60
        for: 15m
        annotations:
          summary: "LLM generation time (p95) > 60 seconds"
```

### Alert Routing (AlertManager)

**alertmanager.yml**:
```yaml
global:
  slack_api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
  pagerduty_url: 'https://events.pagerduty.com/v2/enqueue'

route:
  receiver: default
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 4h
  routes:
    # Critical alerts → PagerDuty + Slack
    - match:
        severity: critical
      receiver: pagerduty
      group_wait: 0s
      repeat_interval: 15m

    # Warning alerts → Slack only
    - match:
        severity: warning
      receiver: slack
      group_wait: 30s
      repeat_interval: 1h

receivers:
  - name: default
    slack_configs:
      - channel: '#alerts'
        title: 'Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: slack
    slack_configs:
      - channel: '#alerts'
        title: 'Warning: {{ .GroupLabels.alertname }}'

  - name: pagerduty
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_SERVICE_KEY'
        severity: 'critical'
```

---

## Best Practices

### What to Monitor

1. **API Metrics**
   - Requests per second
   - Response times (p50, p95, p99)
   - Error rates by endpoint
   - Request sizes

2. **Database Metrics**
   - Connection pool utilization
   - Query latency distribution
   - Slow query rate
   - Replication lag (if using replicas)

3. **Cache Metrics**
   - Hit rate trends
   - Eviction rate
   - Memory pressure
   - Key size distribution

4. **LLM Metrics**
   - Generation success rate
   - Token consumption (input/output)
   - Generation time distribution
   - Cost per generation

5. **System Metrics**
   - CPU utilization
   - Memory pressure
   - Disk I/O
   - Network throughput

### Alerting Best Practices

1. **Alert on Symptoms, Not Causes**
   - ✓ Alert on "API error rate > 1%"
   - ✗ Don't alert on "database CPU high" (symptom is slow queries)

2. **Use Meaningful Thresholds**
   - Based on SLO/SLA targets
   - Based on historical data
   - Adjusted for time of day/week

3. **Include Runbook Links**
   - Every alert should have a resolution procedure
   - Link to docs in alert annotations

4. **Avoid Alert Fatigue**
   - Use `for: duration` to reduce false positives
   - Group related alerts
   - Suppress expected transient failures

### Retention & Archival

```yaml
# Prometheus retention
docker run -v prometheus_data:/prometheus \
  prom/prometheus \
  --storage.tsdb.retention.time=15d \
  --storage.tsdb.retention.size=50GB

# Archive old metrics to long-term storage
# (e.g., S3, GCS) after retention period
```

---

## Summary

A comprehensive observability strategy includes:

1. **Logs**: JSON structured logs with request IDs for tracing
2. **Metrics**: Prometheus metrics at API, database, cache, and LLM levels
3. **Traces**: Distributed tracing with OpenTelemetry to understand request flows
4. **Health**: Regular liveness and readiness checks
5. **Alerts**: Symptom-based alerts routed to appropriate channels

Start with logs + basic metrics, then add distributed tracing when needed.
