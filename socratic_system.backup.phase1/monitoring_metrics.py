"""
Application Monitoring Metrics

Tracks key metrics for application health, performance, and usage.
Provides real-time metrics and historical trends.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional


@dataclass
class MetricPoint:
    """Single metric data point."""

    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class HealthStatus:
    """Application health status."""

    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: datetime
    checks: Dict[str, bool]
    details: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Collect and aggregate application metrics."""

    def __init__(self, retention_hours: int = 24):
        """
        Initialize metrics collector.

        Args:
            retention_hours: How long to retain historical metrics
        """
        self.retention_hours = retention_hours
        self.metrics: Dict[str, List[MetricPoint]] = defaultdict(list)
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.last_cleanup = datetime.now()

    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Record a metric value.

        Args:
            name: Metric name
            value: Metric value
            tags: Optional tags for categorization
        """
        self._cleanup_old_metrics()

        point = MetricPoint(
            timestamp=datetime.now(),
            value=value,
            tags=tags or {},
        )
        self.metrics[name].append(point)

    def increment_counter(self, name: str, amount: int = 1) -> None:
        """
        Increment a counter metric.

        Args:
            name: Counter name
            amount: Amount to increment
        """
        self.counters[name] += amount

    def set_gauge(self, name: str, value: float) -> None:
        """
        Set a gauge metric (point-in-time value).

        Args:
            name: Gauge name
            value: Gauge value
        """
        self.gauges[name] = value

    def get_metric_stats(self, name: str, minutes: int = 60) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a metric over time period.

        Args:
            name: Metric name
            minutes: Look back window in minutes

        Returns:
            Dictionary with count, min, max, avg, latest
        """
        if name not in self.metrics:
            return None

        cutoff = datetime.now() - timedelta(minutes=minutes)
        recent = [m for m in self.metrics[name] if m.timestamp >= cutoff]

        if not recent:
            return None

        values = [m.value for m in recent]

        return {
            "count": float(len(values)),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[-1],
            "timestamp": recent[-1].timestamp.isoformat(),
        }

    def get_all_counters(self) -> Dict[str, int]:
        """Get all counter values."""
        return dict(self.counters)

    def get_all_gauges(self) -> Dict[str, float]:
        """Get all gauge values."""
        return dict(self.gauges)

    def reset_counter(self, name: str) -> None:
        """Reset a counter to zero."""
        self.counters[name] = 0

    def _cleanup_old_metrics(self) -> None:
        """Remove metrics older than retention period."""
        if (datetime.now() - self.last_cleanup).total_seconds() < 300:
            return  # Cleanup every 5 minutes max

        cutoff = datetime.now() - timedelta(hours=self.retention_hours)

        for name in list(self.metrics.keys()):
            self.metrics[name] = [m for m in self.metrics[name] if m.timestamp >= cutoff]
            if not self.metrics[name]:
                del self.metrics[name]

        self.last_cleanup = datetime.now()


class HealthChecker:
    """Check application health status."""

    def __init__(self):
        """Initialize health checker."""
        self.checks: Dict[str, Callable[[], bool]] = {}

    def register_check(self, name: str, check_fn: Callable[[], bool]) -> None:
        """
        Register a health check function.

        Args:
            name: Check name
            check_fn: Callable that returns bool (True = healthy)
        """
        self.checks[name] = check_fn

    def get_health_status(self) -> HealthStatus:
        """
        Get overall health status.

        Returns:
            HealthStatus with individual check results
        """
        check_results = {}
        details = {}

        for name, check_fn in self.checks.items():
            try:
                result = check_fn()
                check_results[name] = result
            except Exception as e:
                check_results[name] = False
                details[name] = str(e)

        # Determine overall status
        if all(check_results.values()):
            status = "healthy"
        elif any(check_results.values()):
            status = "degraded"
        else:
            status = "unhealthy"

        return HealthStatus(
            status=status,
            timestamp=datetime.now(),
            checks=check_results,
            details=details,
        )


class RequestMetrics:
    """Track HTTP request metrics."""

    def __init__(self, collector: MetricsCollector):
        """Initialize request metrics."""
        self.collector = collector
        self.active_requests: Dict[str, float] = {}

    def start_request(self, request_id: str) -> None:
        """Track start of a request."""
        self.active_requests[request_id] = time.time()
        self.collector.increment_counter("requests.total")
        self.collector.set_gauge("requests.active", len(self.active_requests))

    def end_request(
        self,
        request_id: str,
        method: str,
        path: str,
        status_code: int,
        error: Optional[str] = None,
    ) -> None:
        """Track end of a request."""
        if request_id in self.active_requests:
            duration = (time.time() - self.active_requests[request_id]) * 1000
            del self.active_requests[request_id]

            # Record metrics
            self.collector.record_metric(
                "request.duration_ms",
                duration,
                tags={
                    "method": method,
                    "path": path,
                    "status": str(status_code),
                },
            )

            # Track by status code
            if status_code < 400:
                self.collector.increment_counter("requests.success")
            elif status_code < 500:
                self.collector.increment_counter("requests.client_error")
            else:
                self.collector.increment_counter("requests.server_error")
                if error:
                    self.collector.increment_counter(f"errors.{error}")

            self.collector.set_gauge("requests.active", len(self.active_requests))


class DatabaseMetrics:
    """Track database operation metrics."""

    def __init__(self, collector: MetricsCollector):
        """Initialize database metrics."""
        self.collector = collector

    def record_query(
        self, query_type: str, duration: float, rows_affected: int = 0, error: bool = False
    ) -> None:
        """
        Record database query metrics.

        Args:
            query_type: Type of query (SELECT, INSERT, UPDATE, DELETE)
            duration: Query duration in seconds
            rows_affected: Number of rows affected
            error: Whether query had an error
        """
        duration_ms = duration * 1000

        self.collector.record_metric(
            "db.query.duration_ms",
            duration_ms,
            tags={"query_type": query_type},
        )

        self.collector.increment_counter(f"db.queries.{query_type.lower()}")

        if rows_affected > 0:
            self.collector.record_metric(
                "db.rows_affected",
                rows_affected,
                tags={"query_type": query_type},
            )

        if error:
            self.collector.increment_counter("db.query.errors")


class ExportMetrics:
    """Track export and publish metrics."""

    def __init__(self, collector: MetricsCollector):
        """Initialize export metrics."""
        self.collector = collector

    def record_export(
        self,
        project_id: str,
        format: str,
        size_bytes: int,
        duration_ms: float,
        success: bool = True,
    ) -> None:
        """
        Record project export metrics.

        Args:
            project_id: Project ID
            format: Export format (zip, tar, etc.)
            size_bytes: Size of exported archive
            duration_ms: Export duration in milliseconds
            success: Whether export was successful
        """
        self.collector.increment_counter("exports.total")
        self.collector.increment_counter(f"exports.format.{format}")

        if success:
            self.collector.increment_counter("exports.success")
            self.collector.record_metric(
                "export.duration_ms",
                duration_ms,
                tags={"format": format},
            )
            self.collector.record_metric(
                "export.size_bytes",
                size_bytes,
                tags={"format": format},
            )
        else:
            self.collector.increment_counter("exports.failures")

    def record_github_publish(
        self,
        project_id: str,
        success: bool,
        duration_ms: float,
        error_type: Optional[str] = None,
    ) -> None:
        """
        Record GitHub publish metrics.

        Args:
            project_id: Project ID
            success: Whether publish was successful
            duration_ms: Operation duration
            error_type: Type of error if failed
        """
        self.collector.increment_counter("github_publish.total")

        if success:
            self.collector.increment_counter("github_publish.success")
            self.collector.record_metric("github_publish.duration_ms", duration_ms)
        else:
            self.collector.increment_counter("github_publish.failures")
            if error_type:
                self.collector.increment_counter(f"github_publish.error.{error_type}")


# Global metrics instance
_metrics_collector: Optional[MetricsCollector] = None
_health_checker: Optional[HealthChecker] = None


def initialize_metrics() -> MetricsCollector:
    """Initialize global metrics collector."""
    global _metrics_collector, _health_checker
    _metrics_collector = MetricsCollector(retention_hours=24)
    _health_checker = HealthChecker()
    return _metrics_collector


def get_metrics() -> MetricsCollector:
    """Get global metrics collector."""
    if _metrics_collector is None:
        raise RuntimeError("Metrics not initialized. Call initialize_metrics() first.")
    return _metrics_collector


def get_health_checker() -> HealthChecker:
    """Get global health checker."""
    if _health_checker is None:
        raise RuntimeError("Health checker not initialized. Call initialize_metrics() first.")
    return _health_checker
