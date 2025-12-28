"""Database health monitoring and status endpoint.

Provides real-time health checks for:
- Database connectivity and latency
- Connection pool statistics
- Query performance metrics
- Database file integrity (SQLite)
- Backup file status (optional)

GET /database/health - Overall database health
GET /database/health/detailed - Detailed health metrics
GET /database/stats - Connection pool and query statistics
"""

import logging
import os
import time
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Router setup
router = APIRouter(prefix="/database", tags=["database"])


# ============================================================================
# Response Models
# ============================================================================


class PoolStatusModel(BaseModel):
    """Connection pool status metrics."""

    size: int = Field(description="Number of connections in pool")
    checked_in: int = Field(description="Available connections")
    checked_out: int = Field(description="Connections in use")
    overflow: int = Field(description="Overflow connections")
    total: int = Field(description="Total active connections")
    utilization_percent: float = Field(description="Pool utilization percentage")


class QueryStatsModel(BaseModel):
    """Query performance statistics."""

    total_queries: int = Field(description="Total queries executed")
    slow_queries: int = Field(description="Queries exceeding slow threshold")
    slow_percentage: float = Field(description="Percentage of slow queries")
    avg_time_ms: float = Field(description="Average query execution time")
    max_time_ms: float = Field(description="Maximum query execution time")


class DatabaseHealthModel(BaseModel):
    """Overall database health status."""

    status: str = Field(description="Health status: healthy, degraded, or unhealthy")
    message: str = Field(description="Health status message")
    latency_ms: float = Field(description="Database round-trip latency")
    timestamp: str = Field(description="Check timestamp")


class DetailedHealthModel(DatabaseHealthModel):
    """Detailed database health with metrics."""

    pool_status: PoolStatusModel = Field(description="Connection pool metrics")
    query_stats: Optional[QueryStatsModel] = Field(description="Query performance metrics")


class DatabaseStatsModel(BaseModel):
    """Complete database statistics."""

    pool_status: PoolStatusModel = Field(description="Connection pool metrics")
    query_stats: Optional[QueryStatsModel] = Field(description="Query statistics")
    cache_info: Optional[Dict[str, Any]] = Field(description="Cache statistics")
    file_info: Optional[Dict[str, Any]] = Field(description="Database file info")


# ============================================================================
# Dependency Injection
# ============================================================================


async def get_connection_pool():
    """Get database connection pool instance.

    Returns:
        DatabaseConnectionPool: The initialized connection pool

    Raises:
        HTTPException: If pool not initialized
    """
    from socratic_system.database.connection_pool import get_pool

    try:
        return get_pool()
    except RuntimeError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database pool not initialized: {str(e)}",
        )


async def get_query_profiler():
    """Get query performance profiler instance.

    Returns:
        QueryProfiler: The global profiler instance
    """
    from socratic_system.database.query_profiler import get_profiler

    return get_profiler()


# ============================================================================
# Health Check Endpoints
# ============================================================================


@router.get("/health", response_model=DatabaseHealthModel)
async def database_health(
    pool=Depends(get_connection_pool),
) -> DatabaseHealthModel:
    """Check overall database health status.

    Performs a quick connectivity test and returns health status.

    Returns:
        DatabaseHealthModel: Health status and metrics

    Raises:
        HTTPException 503: If database is unhealthy

    Example:
        ```bash
        curl http://localhost:8000/database/health
        ```

        Response (healthy):
        ```json
        {
            "status": "healthy",
            "message": "Database is operating normally",
            "latency_ms": 12.34,
            "timestamp": "2025-01-01T12:00:00Z"
        }
        ```
    """
    health = await pool.get_pool_health()

    # Map health status to HTTP status code
    status_code = 200  # OK
    if health.get("status") == "degraded":
        status_code = 200  # Still OK, but degraded
    elif health.get("status") == "unhealthy":
        status_code = 503  # Service Unavailable

    if status_code == 503:
        raise HTTPException(
            status_code=503,
            detail={
                "status": health.get("status"),
                "message": "Database is unhealthy",
                "error": health.get("error"),
                "latency_ms": health.get("latency_ms"),
            },
        )

    status_message = {
        "healthy": "Database is operating normally",
        "degraded": "Database is operating with reduced capacity",
        "unhealthy": "Database is not responding",
    }.get(health.get("status"), "Unknown status")

    return DatabaseHealthModel(
        status=health.get("status", "unknown"),
        message=status_message,
        latency_ms=health.get("latency_ms", 0),
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


@router.get("/health/detailed", response_model=DetailedHealthModel)
async def database_health_detailed(
    pool=Depends(get_connection_pool),
    profiler=Depends(get_query_profiler),
) -> DetailedHealthModel:
    """Get detailed database health with metrics.

    Includes connection pool statistics and query performance metrics.

    Returns:
        DetailedHealthModel: Health status with detailed metrics

    Example:
        ```bash
        curl http://localhost:8000/database/health/detailed
        ```
    """
    health = await pool.get_pool_health()

    # Get pool status
    pool_status_dict = health.get("pool_status", {})
    pool_status = PoolStatusModel(
        size=pool_status_dict.get("size", 0),
        checked_in=pool_status_dict.get("checked_in", 0),
        checked_out=pool_status_dict.get("checked_out", 0),
        overflow=pool_status_dict.get("overflow", 0),
        total=pool_status_dict.get("total", 0),
        utilization_percent=pool_status_dict.get("utilization_percent", 0),
    )

    # Get query statistics
    stats = profiler.get_stats()
    total_queries = sum(s["count"] for s in stats.values())
    slow_queries = sum(s["slow_count"] for s in stats.values())
    slow_percentage = (
        (slow_queries / total_queries * 100) if total_queries > 0 else 0
    )

    avg_times = [s["avg_time_ms"] for s in stats.values() if s["count"] > 0]
    max_times = [s["max_time_ms"] for s in stats.values() if s["count"] > 0]

    query_stats = (
        QueryStatsModel(
            total_queries=total_queries,
            slow_queries=slow_queries,
            slow_percentage=round(slow_percentage, 1),
            avg_time_ms=round(sum(avg_times) / len(avg_times), 2) if avg_times else 0,
            max_time_ms=max(max_times) if max_times else 0,
        )
        if total_queries > 0
        else None
    )

    status_message = {
        "healthy": "Database is operating normally",
        "degraded": "Database is operating with reduced capacity",
        "unhealthy": "Database is not responding",
    }.get(health.get("status"), "Unknown status")

    return DetailedHealthModel(
        status=health.get("status", "unknown"),
        message=status_message,
        latency_ms=health.get("latency_ms", 0),
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        pool_status=pool_status,
        query_stats=query_stats,
    )


# ============================================================================
# Statistics Endpoints
# ============================================================================


@router.get("/stats", response_model=DatabaseStatsModel)
async def database_stats(
    pool=Depends(get_connection_pool),
    profiler=Depends(get_query_profiler),
) -> DatabaseStatsModel:
    """Get comprehensive database statistics.

    Returns:
        DatabaseStatsModel: Complete statistics including pool, queries, and files

    Example:
        ```bash
        curl http://localhost:8000/database/stats
        ```
    """
    # Get pool status
    pool_status_dict = await pool.get_pool_status()
    pool_status = PoolStatusModel(
        size=pool_status_dict.get("size", 0),
        checked_in=pool_status_dict.get("checked_in", 0),
        checked_out=pool_status_dict.get("checked_out", 0),
        overflow=pool_status_dict.get("overflow", 0),
        total=pool_status_dict.get("total", 0),
        utilization_percent=pool_status_dict.get("utilization_percent", 0),
    )

    # Get query statistics
    stats = profiler.get_stats()
    total_queries = sum(s["count"] for s in stats.values())
    slow_queries = sum(s["slow_count"] for s in stats.values())

    query_stats = None
    if total_queries > 0:
        slow_percentage = (slow_queries / total_queries * 100) if total_queries > 0 else 0
        avg_times = [s["avg_time_ms"] for s in stats.values() if s["count"] > 0]
        max_times = [s["max_time_ms"] for s in stats.values() if s["count"] > 0]

        query_stats = QueryStatsModel(
            total_queries=total_queries,
            slow_queries=slow_queries,
            slow_percentage=round(slow_percentage, 1),
            avg_time_ms=round(sum(avg_times) / len(avg_times), 2) if avg_times else 0,
            max_time_ms=max(max_times) if max_times else 0,
        )

    # Get file info if SQLite
    file_info = None
    db_url = pool.database_url
    if "sqlite" in db_url:
        # Extract database file path from URL
        db_path = db_url.replace("sqlite+aiosqlite:///", "").replace("sqlite://", "")
        if os.path.exists(db_path):
            stat = os.stat(db_path)
            file_info = {
                "path": db_path,
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "modified_at": time.ctime(stat.st_mtime),
            }

    return DatabaseStatsModel(
        pool_status=pool_status,
        query_stats=query_stats,
        file_info=file_info,
    )


# ============================================================================
# Query Performance Endpoints
# ============================================================================


@router.get("/slow-queries", tags=["database", "performance"])
async def get_slow_queries(
    min_count: int = 1,
    profiler=Depends(get_query_profiler),
) -> Dict[str, Any]:
    """Get list of slow queries.

    Args:
        min_count: Minimum number of slow executions to include

    Returns:
        Dict with slow query list sorted by count

    Example:
        ```bash
        curl http://localhost:8000/database/slow-queries?min_count=5
        ```
    """
    slow_queries = profiler.get_slow_queries(min_slow_count=min_count)

    return {
        "total_slow_queries": len(slow_queries),
        "min_count": min_count,
        "queries": slow_queries,
    }


@router.get("/slowest-queries", tags=["database", "performance"])
async def get_slowest_queries(
    limit: int = 10,
    profiler=Depends(get_query_profiler),
) -> Dict[str, Any]:
    """Get slowest queries by average execution time.

    Args:
        limit: Maximum number of queries to return

    Returns:
        Dict with slowest queries

    Example:
        ```bash
        curl http://localhost:8000/database/slowest-queries?limit=5
        ```
    """
    slowest = profiler.get_slowest_queries(limit=limit)

    return {
        "limit": limit,
        "total_tracked": len(profiler.stats),
        "queries": slowest,
    }


# ============================================================================
# Admin Endpoints
# ============================================================================


@router.post("/stats/reset", tags=["database", "admin"])
async def reset_statistics(
    query_name: Optional[str] = None,
    profiler=Depends(get_query_profiler),
) -> Dict[str, str]:
    """Reset query statistics.

    Args:
        query_name: Specific query to reset, or None for all

    Returns:
        Dict with reset status

    Example:
        ```bash
        # Reset all statistics
        curl -X POST http://localhost:8000/database/stats/reset

        # Reset specific query
        curl -X POST "http://localhost:8000/database/stats/reset?query_name=get_user"
        ```
    """
    profiler.reset_stats(query_name)

    if query_name:
        return {
            "status": "reset",
            "message": f"Statistics reset for query: {query_name}",
        }
    else:
        return {
            "status": "reset",
            "message": "All statistics reset",
        }


# ============================================================================
# Health Check for Kubernetes/Load Balancers
# ============================================================================


@router.get("/live", tags=["health"])
async def liveness_probe(
    pool=Depends(get_connection_pool),
) -> Dict[str, str]:
    """Liveness probe for Kubernetes/container orchestration.

    Returns:
        Dict with status

    Example:
        ```bash
        curl http://localhost:8000/database/live
        ```
    """
    try:
        is_alive = await pool.test_connection()
        if not is_alive:
            raise HTTPException(status_code=503, detail="Database connection failed")
        return {"status": "alive"}
    except Exception as e:
        logger.error(f"Liveness probe failed: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/ready", tags=["health"])
async def readiness_probe(
    pool=Depends(get_connection_pool),
) -> Dict[str, str]:
    """Readiness probe for Kubernetes/container orchestration.

    Returns:
        Dict with status

    Example:
        ```bash
        curl http://localhost:8000/database/ready
        ```
    """
    try:
        health = await pool.get_pool_health()

        if health.get("status") == "unhealthy":
            raise HTTPException(
                status_code=503,
                detail="Database is not ready",
            )

        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness probe failed: {e}")
        raise HTTPException(status_code=503, detail=str(e))
