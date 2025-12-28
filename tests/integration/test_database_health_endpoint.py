"""Integration tests for database health endpoint.

Tests cover:
- Health check endpoint responses
- Pool status reporting
- Query statistics aggregation
- Slow query detection endpoint
- Admin endpoints for stats management
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch


# Mock FastAPI app for testing
@pytest.fixture
def mock_app():
    """Create mock FastAPI app with health router."""
    from fastapi import FastAPI

    app = FastAPI()

    # Import and register the database health router
    from socrates_api.routers.database_health import router

    app.include_router(router)

    return app


@pytest.fixture
def client(mock_app):
    """Create test client from mock app."""
    return TestClient(mock_app)


@pytest.fixture
def mock_pool():
    """Create mock connection pool."""

    class MockPool:
        """Mock database connection pool."""

        async def get_pool_health(self):
            """Mock health check."""
            return {
                "status": "healthy",
                "latency_ms": 10.5,
                "pool_status": {
                    "size": 20,
                    "checked_in": 18,
                    "checked_out": 2,
                    "overflow": 0,
                    "total": 20,
                    "utilization_percent": 10.0,
                },
            }

        async def get_pool_status(self):
            """Mock pool status."""
            return {
                "size": 20,
                "checked_in": 18,
                "checked_out": 2,
                "overflow": 0,
                "total": 20,
                "utilization_percent": 10.0,
            }

        async def test_connection(self):
            """Mock connection test."""
            return True

        @property
        def database_url(self):
            """Mock database URL."""
            return "sqlite+aiosqlite:///:memory:"

    return MockPool()


@pytest.fixture
def mock_profiler():
    """Create mock query profiler."""

    class MockStats:
        """Mock statistics object."""

        def __init__(self):
            self.data = {
                "query1": {
                    "name": "query1",
                    "count": 100,
                    "avg_time_ms": 5.0,
                    "min_time_ms": 1.0,
                    "max_time_ms": 50.0,
                    "total_time_ms": 500.0,
                    "slow_count": 5,
                    "slow_percentage": 5.0,
                    "error_count": 0,
                    "last_executed_at": None,
                },
                "query2": {
                    "name": "query2",
                    "count": 50,
                    "avg_time_ms": 10.0,
                    "min_time_ms": 2.0,
                    "max_time_ms": 100.0,
                    "total_time_ms": 500.0,
                    "slow_count": 15,
                    "slow_percentage": 30.0,
                    "error_count": 0,
                    "last_executed_at": None,
                },
            }

    class MockProfiler:
        """Mock query profiler."""

        def __init__(self):
            self.stats = MockStats().data

        def get_stats(self):
            """Return mock statistics."""
            return self.stats

        def get_slow_queries(self, min_slow_count=1):
            """Return slow queries."""
            return [q for q in self.stats.values() if q["slow_count"] >= min_slow_count]

        def get_slowest_queries(self, limit=10):
            """Return slowest queries."""
            sorted_stats = sorted(
                self.stats.values(),
                key=lambda x: x["avg_time_ms"],
                reverse=True,
            )
            return sorted_stats[:limit]

        def reset_stats(self, query_name=None):
            """Reset statistics."""
            if query_name is None:
                self.stats.clear()
            elif query_name in self.stats:
                del self.stats[query_name]

    return MockProfiler()


class TestDatabaseHealthEndpoint:
    """Test /database/health endpoint."""

    def test_health_endpoint_healthy(self, client, mock_pool, mock_profiler):
        """Test health endpoint when database is healthy."""
        with patch(
            "socrates_api.routers.database_health.get_connection_pool",
            return_value=mock_pool,
        ):
            response = client.get("/database/health")

            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "healthy"
            assert data["message"] == "Database is operating normally"
            assert data["latency_ms"] == 10.5

    def test_health_endpoint_degraded(self, client):
        """Test health endpoint when database is degraded."""

        class DegradedPool:
            async def get_pool_health(self):
                return {
                    "status": "degraded",
                    "latency_ms": 250.0,
                    "pool_status": {
                        "size": 20,
                        "checked_in": 2,
                        "checked_out": 18,
                        "overflow": 5,
                        "total": 25,
                        "utilization_percent": 92.0,
                    },
                }

        with patch(
            "socrates_api.routers.database_health.get_connection_pool",
            return_value=DegradedPool(),
        ):
            response = client.get("/database/health")

            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "degraded"

    def test_health_endpoint_unhealthy(self, client):
        """Test health endpoint when database is unhealthy."""

        class UnhealthyPool:
            async def get_pool_health(self):
                return {
                    "status": "unhealthy",
                    "error": "Connection refused",
                    "latency_ms": 5000.0,
                }

        with patch(
            "socrates_api.routers.database_health.get_connection_pool",
            return_value=UnhealthyPool(),
        ):
            response = client.get("/database/health")

            assert response.status_code == 503


class TestDetailedHealthEndpoint:
    """Test /database/health/detailed endpoint."""

    def test_detailed_health_includes_metrics(self, client, mock_pool, mock_profiler):
        """Test detailed health endpoint includes pool and query metrics."""
        with patch(
            "socrates_api.routers.database_health.get_connection_pool",
            return_value=mock_pool,
        ), patch(
            "socrates_api.routers.database_health.get_query_profiler",
            return_value=mock_profiler,
        ):
            response = client.get("/database/health/detailed")

            assert response.status_code == 200

            data = response.json()
            assert "pool_status" in data
            assert data["pool_status"]["size"] == 20
            assert data["pool_status"]["utilization_percent"] == 10.0

            assert "query_stats" in data
            assert data["query_stats"]["total_queries"] == 150
            assert data["query_stats"]["slow_queries"] == 20


class TestStatsEndpoint:
    """Test /database/stats endpoint."""

    def test_stats_endpoint_returns_metrics(self, client, mock_pool, mock_profiler):
        """Test stats endpoint returns all database metrics."""
        with patch(
            "socrates_api.routers.database_health.get_connection_pool",
            return_value=mock_pool,
        ), patch(
            "socrates_api.routers.database_health.get_query_profiler",
            return_value=mock_profiler,
        ):
            response = client.get("/database/stats")

            assert response.status_code == 200

            data = response.json()
            assert "pool_status" in data
            assert "query_stats" in data

            # Pool stats
            assert data["pool_status"]["total"] == 20

            # Query stats
            assert data["query_stats"]["total_queries"] == 150
            assert data["query_stats"]["slow_percentage"] > 0


class TestSlowQueriesEndpoint:
    """Test /database/slow-queries endpoint."""

    def test_slow_queries_endpoint(self, client, mock_pool, mock_profiler):
        """Test slow queries endpoint returns slow query list."""
        with patch(
            "socrates_api.routers.database_health.get_connection_pool",
            return_value=mock_pool,
        ), patch(
            "socrates_api.routers.database_health.get_query_profiler",
            return_value=mock_profiler,
        ):
            response = client.get("/database/slow-queries?min_count=5")

            assert response.status_code == 200

            data = response.json()
            assert "total_slow_queries" in data
            assert "queries" in data
            assert len(data["queries"]) > 0

            # Check that returned queries have slow count >= min_count
            for query in data["queries"]:
                assert query["slow_count"] >= 5


class TestSlowestQueriesEndpoint:
    """Test /database/slowest-queries endpoint."""

    def test_slowest_queries_endpoint(self, client, mock_pool, mock_profiler):
        """Test slowest queries endpoint returns top N slowest queries."""
        with patch(
            "socrates_api.routers.database_health.get_connection_pool",
            return_value=mock_pool,
        ), patch(
            "socrates_api.routers.database_health.get_query_profiler",
            return_value=mock_profiler,
        ):
            response = client.get("/database/slowest-queries?limit=5")

            assert response.status_code == 200

            data = response.json()
            assert "queries" in data
            assert "limit" in data
            assert data["limit"] == 5

            # Should be sorted by avg_time_ms descending
            if len(data["queries"]) > 1:
                for i in range(len(data["queries"]) - 1):
                    assert (
                        data["queries"][i]["avg_time_ms"]
                        >= data["queries"][i + 1]["avg_time_ms"]
                    )


class TestStatsResetEndpoint:
    """Test /database/stats/reset admin endpoint."""

    def test_reset_all_statistics(self, client, mock_pool, mock_profiler):
        """Test resetting all statistics."""
        with patch(
            "socrates_api.routers.database_health.get_connection_pool",
            return_value=mock_pool,
        ), patch(
            "socrates_api.routers.database_health.get_query_profiler",
            return_value=mock_profiler,
        ):
            response = client.post("/database/stats/reset")

            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "reset"
            assert "All statistics" in data["message"]

    def test_reset_single_query_statistics(self, client, mock_pool, mock_profiler):
        """Test resetting statistics for single query."""
        with patch(
            "socrates_api.routers.database_health.get_connection_pool",
            return_value=mock_pool,
        ), patch(
            "socrates_api.routers.database_health.get_query_profiler",
            return_value=mock_profiler,
        ):
            response = client.post("/database/stats/reset?query_name=query1")

            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "reset"
            assert "query1" in data["message"]


class TestLivenessProbe:
    """Test /database/live endpoint for Kubernetes."""

    def test_liveness_probe_alive(self, client, mock_pool):
        """Test liveness probe when database is alive."""
        with patch(
            "socrates_api.routers.database_health.get_connection_pool",
            return_value=mock_pool,
        ):
            response = client.get("/database/live")

            assert response.status_code == 200
            assert response.json()["status"] == "alive"

    def test_liveness_probe_dead(self, client):
        """Test liveness probe when database is dead."""

        class DeadPool:
            async def test_connection(self):
                return False

        with patch(
            "socrates_api.routers.database_health.get_connection_pool",
            return_value=DeadPool(),
        ):
            response = client.get("/database/live")

            assert response.status_code == 503


class TestReadinessProbe:
    """Test /database/ready endpoint for Kubernetes."""

    def test_readiness_probe_ready(self, client, mock_pool):
        """Test readiness probe when database is ready."""
        with patch(
            "socrates_api.routers.database_health.get_connection_pool",
            return_value=mock_pool,
        ):
            response = client.get("/database/ready")

            assert response.status_code == 200
            assert response.json()["status"] == "ready"

    def test_readiness_probe_not_ready(self, client):
        """Test readiness probe when database is not ready."""

        class NotReadyPool:
            async def get_pool_health(self):
                return {
                    "status": "unhealthy",
                    "error": "Connection timeout",
                }

        with patch(
            "socrates_api.routers.database_health.get_connection_pool",
            return_value=NotReadyPool(),
        ):
            response = client.get("/database/ready")

            assert response.status_code == 503
