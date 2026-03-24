# Performance Tuning Guide

**Version:** 1.0
**Status:** Complete
**Last Updated:** 2026-03-24

---

## Table of Contents

1. [Performance Baselines](#performance-baselines)
2. [Profiling](#profiling)
3. [Optimization Strategies](#optimization-strategies)
4. [Caching](#caching)
5. [Concurrency](#concurrency)
6. [Database Optimization](#database-optimization)
7. [Configuration Profiles](#configuration-profiles)

---

## Performance Baselines

### Typical Performance Metrics

| Operation | Typical Time | Acceptable Range |
|-----------|--------------|------------------|
| Agent execution | 1-5s | 0.5-10s |
| Database query | 10-100ms | <500ms |
| Vector search | 100-500ms | <1s |
| Request processing | 100-200ms | <500ms |
| Maturity calculation | 50-100ms | <200ms |

### Measurement

```python
import time
from functools import wraps

def measure_performance(func):
    """Decorator to measure function performance"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()

        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration = (time.perf_counter() - start) * 1000  # ms
            print(f"{func.__name__} took {duration:.1f}ms")

    return wrapper

@measure_performance
def analyze_project(project_id: str):
    # ... implementation ...
    pass
```

---

## Profiling

### CPU Profiling

```python
import cProfile
import pstats

def profile_agent_processing():
    """Profile agent execution"""

    profiler = cProfile.Profile()
    profiler.enable()

    # Execute code to profile
    result = orchestrator.process_request({
        "agent": "QualityController",
        "action": "analyze",
        "project_id": "proj_123"
    })

    profiler.disable()

    # Print statistics
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # Top 10 functions

    return result
```

### Memory Profiling

```python
from memory_profiler import profile

@profile
def process_large_dataset(items: list):
    """Profile memory usage"""

    results = []

    for item in items:
        # Process each item
        result = expensive_operation(item)
        results.append(result)

    return results

# Run: python -m memory_profiler script.py
```

### Timing Analysis

```python
import logging
from contextlib import contextmanager
from time import perf_counter

@contextmanager
def timer(name: str):
    """Context manager for timing"""

    start = perf_counter()

    try:
        yield
    finally:
        duration = (perf_counter() - start) * 1000
        logging.info(f"{name}: {duration:.1f}ms")

# Usage
with timer("Quality Analysis"):
    result = orchestrator.process_request(request)
```

---

## Optimization Strategies

### Strategy 1: Request Batching

Combine multiple requests into single operation.

```python
# Bad: Individual requests (slow)
for project_id in project_ids:
    result = orchestrator.process_request({
        "agent": "QualityController",
        "action": "analyze",
        "project_id": project_id
    })
    process_result(result)

# Good: Batch processing (fast)
results = orchestrator.batch_process([
    {
        "agent": "QualityController",
        "action": "analyze",
        "project_id": project_id
    }
    for project_id in project_ids
])

for result in results:
    process_result(result)
```

### Strategy 2: Lazy Loading

Load data only when needed.

```python
class Project:
    def __init__(self, project_id: str, db):
        self.id = project_id
        self.db = db
        self._data = None  # Lazy load

    @property
    def data(self):
        """Load data on first access"""
        if self._data is None:
            self._data = self.db.load_project(self.id)
        return self._data

    @property
    def quality_score(self):
        """Only load what's needed"""
        if not self._data:
            return self.db.get_project_quality(self.id)
        return self._data.quality_score
```

### Strategy 3: Early Termination

Stop processing when result is determined.

```python
def find_high_quality_projects(projects: list, threshold=0.9):
    """Stop searching after finding enough"""

    high_quality = []
    target_count = 5

    for project in projects:
        if project.quality_score > threshold:
            high_quality.append(project)

            # Early termination
            if len(high_quality) >= target_count:
                break

    return high_quality
```

### Strategy 4: Sampling

Analyze subset instead of full dataset.

```python
import random

def estimate_quality(project_id: str, sample_size=100):
    """Estimate quality by sampling code"""

    db = ProjectDatabase()
    all_files = db.get_project_files(project_id)

    # Sample files
    if len(all_files) > sample_size:
        sample = random.sample(all_files, sample_size)
    else:
        sample = all_files

    # Analyze sample
    orchestrator = OrchestratorService.get_orchestrator("system")
    result = orchestrator.process_request({
        "agent": "QualityController",
        "action": "analyze",
        "files": sample,
        "extrapolate": True  # Estimate to full dataset
    })

    return result
```

---

## Caching

### Query Caching

```python
from socratic_core.utils import TTLCache

class CachedDatabase:
    def __init__(self, db):
        self.db = db
        self.cache = TTLCache(ttl_minutes=30)

    def get_project(self, project_id: str):
        """Cache project lookups"""

        if project_id in self.cache:
            return self.cache[project_id]

        project = self.db.load_project(project_id)
        self.cache[project_id] = project

        return project

    def get_user_projects(self, user_id: str):
        """Cache user project lists"""

        cache_key = f"user_projects:{user_id}"

        if cache_key in self.cache:
            return self.cache[cache_key]

        projects = self.db.get_user_projects(user_id)
        self.cache[cache_key] = projects

        return projects

    def invalidate(self, project_id: str):
        """Invalidate cache when data changes"""

        del self.cache[project_id]

        # Also invalidate related caches
        for key in list(self.cache.keys()):
            if key.startswith("user_projects:"):
                del self.cache[key]
```

### Result Caching

```python
from functools import lru_cache

class CachedOrchestrator:
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        # Cache with max 1000 results, 1 hour TTL
        self._cache = TTLCache(ttl_minutes=60)

    def process_request(self, request: dict) -> dict:
        """Cache agent results"""

        # Create cache key from request
        cache_key = self._make_cache_key(request)

        if cache_key in self._cache:
            return self._cache[cache_key]

        # Execute and cache
        result = self.orchestrator.process_request(request)
        self._cache[cache_key] = result

        return result

    def _make_cache_key(self, request: dict) -> str:
        """Create hashable cache key"""

        # Only cache reads, not mutations
        if request.get("action") not in ["analyze", "validate", "report"]:
            return None

        # Include relevant fields
        return f"{request['agent']}:{request['action']}:{request.get('project_id')}"
```

---

## Concurrency

### Async Processing

```python
import asyncio

async def process_projects_concurrent(project_ids: list):
    """Process multiple projects concurrently"""

    orchestrator = OrchestratorService.get_orchestrator("system")

    # Create tasks for all projects
    tasks = [
        orchestrator.process_async({
            "agent": "QualityController",
            "action": "analyze",
            "project_id": project_id
        })
        for project_id in project_ids
    ]

    # Execute concurrently
    results = await asyncio.gather(*tasks)

    return results

# Usage
import time

start = time.time()
results = asyncio.run(process_projects_concurrent(["p1", "p2", "p3", "p4", "p5"]))
elapsed = time.time() - start

print(f"Processed {len(results)} projects in {elapsed:.1f}s")
```

### Connection Pooling

```python
from concurrent.futures import ThreadPoolExecutor

class PooledOrchestrator:
    def __init__(self, pool_size=10):
        self.orchestrator = OrchestratorService.get_orchestrator("system")
        self.executor = ThreadPoolExecutor(max_workers=pool_size)

    def process_batch(self, requests: list) -> list:
        """Process requests using thread pool"""

        futures = [
            self.executor.submit(
                self.orchestrator.process_request,
                request
            )
            for request in requests
        ]

        # Wait for all to complete
        results = [f.result() for f in futures]

        return results

    def shutdown(self):
        """Clean up thread pool"""
        self.executor.shutdown(wait=True)

# Usage
pool = PooledOrchestrator(pool_size=10)
results = pool.process_batch(requests)
pool.shutdown()
```

---

## Database Optimization

### Index Creation

```python
from socratic_system.database import ProjectDatabase

db = ProjectDatabase()

# Create indexes for frequently queried columns
db.create_index("projects", "owner_id")
db.create_index("projects", "status")
db.create_index("projects", "quality_score")
db.create_index("projects", "created_at")

# Compound index for common queries
db.create_compound_index("projects", ["owner_id", "status"])
```

### Query Optimization

```python
# Bad: Full table scan
projects = db.execute(
    "SELECT * FROM projects WHERE quality_score > 0.8"
).fetchall()

# Good: With index and limit
projects = db.execute(
    "SELECT id, name, quality_score FROM projects "
    "WHERE quality_score > ? "
    "ORDER BY quality_score DESC "
    "LIMIT ?",
    (0.8, 100)
).fetchall()
```

### Pagination

```python
def paginate_projects(page: int = 1, page_size: int = 20):
    """Get paginated results"""

    db = ProjectDatabase()
    offset = (page - 1) * page_size

    projects = db.execute(
        "SELECT * FROM projects "
        "WHERE status = ? "
        "ORDER BY created_at DESC "
        "LIMIT ? OFFSET ?",
        ("active", page_size, offset)
    ).fetchall()

    # Get total count (for pagination UI)
    total = db.execute(
        "SELECT COUNT(*) FROM projects WHERE status = ?",
        ("active",)
    ).fetchone()[0]

    return {
        "items": projects,
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": (total + page_size - 1) // page_size
    }
```

---

## Configuration Profiles

### High-Throughput Profile

Optimize for maximum requests/second.

```python
from socratic_core import SocratesConfig

# High-throughput config
config = SocratesConfig(
    api_key="sk-...",
    # Caching
    enable_cache=True,
    cache_ttl=3600,
    # Connection pooling
    connection_pool_size=50,
    # Async
    enable_async=True,
    # Batch processing
    batch_size=100,
    # Indexing
    enable_indexes=True,
    # Compression
    enable_compression=True,
    # Log level (minimal logging)
    log_level="WARNING"
)
```

### Low-Resource Profile

Optimize for minimal memory/CPU usage.

```python
config = SocratesConfig(
    api_key="sk-...",
    # Minimal caching
    enable_cache=False,
    # Single connection
    connection_pool_size=1,
    # Synchronous
    enable_async=False,
    # Sequential processing
    batch_size=1,
    # No indexing
    enable_indexes=False,
    # Compression
    enable_compression=True,
    # Minimal logging
    log_level="ERROR"
)
```

### Balanced Profile

Balance performance and resource usage.

```python
config = SocratesConfig(
    api_key="sk-...",
    # Moderate caching
    enable_cache=True,
    cache_ttl=600,
    # Connection pool
    connection_pool_size=10,
    # Async support
    enable_async=True,
    # Batch processing
    batch_size=20,
    # Selective indexing
    enable_indexes=True,
    # Standard logging
    log_level="INFO"
)
```

---

## Benchmarking

### Performance Test

```python
import time
from statistics import mean, stdev

def benchmark_agent(agent_name: str, iterations=10):
    """Benchmark agent performance"""

    orchestrator = OrchestratorService.get_orchestrator("system")
    times = []

    for i in range(iterations):
        start = time.perf_counter()

        result = orchestrator.process_request({
            "agent": agent_name,
            "action": "analyze",
            "project_id": f"proj_{i}"
        })

        duration = (time.perf_counter() - start) * 1000  # ms
        times.append(duration)

    return {
        "agent": agent_name,
        "iterations": iterations,
        "min_ms": min(times),
        "max_ms": max(times),
        "mean_ms": mean(times),
        "stdev_ms": stdev(times) if len(times) > 1 else 0,
        "results": times
    }

# Usage
results = benchmark_agent("QualityController", iterations=10)
print(f"{results['agent']}: {results['mean_ms']:.1f}ms (±{results['stdev_ms']:.1f}ms)")
```

---

## Monitoring in Production

### Key Metrics

```python
class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            "request_count": 0,
            "total_duration_ms": 0,
            "error_count": 0,
            "agent_timings": {}
        }

    def record_request(self, agent: str, duration_ms: float, success: bool):
        """Record performance metrics"""

        self.metrics["request_count"] += 1
        self.metrics["total_duration_ms"] += duration_ms

        if not success:
            self.metrics["error_count"] += 1

        if agent not in self.metrics["agent_timings"]:
            self.metrics["agent_timings"][agent] = []

        self.metrics["agent_timings"][agent].append(duration_ms)

    def get_summary(self) -> dict:
        """Get performance summary"""

        if self.metrics["request_count"] == 0:
            return {}

        agent_stats = {
            agent: {
                "count": len(timings),
                "avg_ms": mean(timings),
                "max_ms": max(timings)
            }
            for agent, timings in self.metrics["agent_timings"].items()
        }

        return {
            "total_requests": self.metrics["request_count"],
            "total_errors": self.metrics["error_count"],
            "avg_response_ms": (
                self.metrics["total_duration_ms"] /
                self.metrics["request_count"]
            ),
            "error_rate": (
                self.metrics["error_count"] /
                self.metrics["request_count"] * 100
            ),
            "by_agent": agent_stats
        }

# Usage
monitor = PerformanceMonitor()

start = time.time()
result = orchestrator.process_request(request)
duration = (time.time() - start) * 1000

monitor.record_request(
    agent=request["agent"],
    duration_ms=duration,
    success=(result["status"] == "success")
)

# Periodic reporting
if monitor.metrics["request_count"] % 1000 == 0:
    summary = monitor.get_summary()
    logger.info(f"Performance: {summary}")
```

---

## Related Documentation

- [Architecture Overview](../ARCHITECTURE.md)
- [Configuration Guide](./CONFIGURATION_GUIDE.md)
- [Common Integration Patterns](./COMMON_INTEGRATION_PATTERNS.md)

