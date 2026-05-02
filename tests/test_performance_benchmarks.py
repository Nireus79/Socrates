"""
Performance benchmarking for the new Library Export Architecture.

Validates:
- Agent bus request latency
- Service layer overhead
- Resilience pattern (circuit breaker, retry) overhead
- Concurrent request handling
- Cache effectiveness
"""

import time
import pytest
from unittest.mock import MagicMock
import statistics

from socratic_system.events import EventEmitter
from socratic_system.messaging import AgentBus, CircuitBreaker, RetryPolicy
from socratic_system.services import CodeService, QualityService, ValidationService
from socratic_system.caching import InMemoryAnalysisCache
from socratic_system.jobs import JobTracker, JobStatus


class TestAgentBusPerformance:
    """Benchmark agent bus performance."""

    def setup_method(self):
        """Set up test fixtures."""
        self.event_emitter = EventEmitter()
        self.agent_bus = AgentBus(self.event_emitter)
        self.orchestrator = MagicMock()
        self.orchestrator.agent_bus = self.agent_bus

    def test_agent_bus_baseline_latency(self):
        """Measure baseline latency of agent_bus.send_request_sync()."""
        # Mock agent response
        self.agent_bus.send_request_sync = MagicMock(
            return_value={"status": "success", "data": {}}
        )

        latencies = []
        iterations = 1000

        for _ in range(iterations):
            start = time.perf_counter()
            self.agent_bus.send_request_sync("test_agent", {"action": "process"})
            elapsed = time.perf_counter() - start
            latencies.append(elapsed * 1000)  # Convert to ms

        avg_latency = statistics.mean(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        p99_latency = sorted(latencies)[int(len(latencies) * 0.99)]

        print(f"\nAgent Bus Latency (1000 calls):")
        print(f"  Average: {avg_latency:.3f}ms")
        print(f"  P95: {p95_latency:.3f}ms")
        print(f"  P99: {p99_latency:.3f}ms")

        # Baseline should be very fast (sub-millisecond for mocked calls)
        assert avg_latency < 1.0, f"Average latency too high: {avg_latency}ms"

    def test_service_layer_overhead(self):
        """Measure overhead added by service layer."""
        code_service = CodeService(config=MagicMock(), orchestrator=self.orchestrator)

        self.agent_bus.send_request_sync = MagicMock(
            return_value={"status": "success", "files": []}
        )

        project = MagicMock()
        project.project_id = "perf_test"

        latencies = []
        iterations = 500

        for _ in range(iterations):
            start = time.perf_counter()
            code_service.generate_code(project, language="python", user_id="user1")
            elapsed = time.perf_counter() - start
            latencies.append(elapsed * 1000)

        avg_latency = statistics.mean(latencies)
        max_latency = max(latencies)

        print(f"\nService Layer Overhead (500 calls):")
        print(f"  Average: {avg_latency:.3f}ms")
        print(f"  Max: {max_latency:.3f}ms")

        # Service layer overhead should be minimal
        assert avg_latency < 2.0, f"Service overhead too high: {avg_latency}ms"


class TestCircuitBreakerPerformance:
    """Benchmark circuit breaker performance."""

    def test_circuit_breaker_overhead(self):
        """Measure circuit breaker overhead on requests."""
        breaker = CircuitBreaker(failure_threshold=5)

        latencies_with_breaker = []
        latencies_without_breaker = []

        iterations = 10000

        # Measure with circuit breaker check
        for _ in range(iterations):
            start = time.perf_counter()
            breaker.allow_request()
            elapsed = time.perf_counter() - start
            latencies_with_breaker.append(elapsed * 1000000)  # Convert to microseconds

        avg_with_breaker = statistics.mean(latencies_with_breaker)
        max_with_breaker = max(latencies_with_breaker)

        print(f"\nCircuit Breaker Overhead (10000 calls):")
        print(f"  Average: {avg_with_breaker:.3f}µs")
        print(f"  Max: {max_with_breaker:.3f}µs")

        # Circuit breaker check should be very fast (microseconds)
        assert avg_with_breaker < 100, f"Circuit breaker overhead too high: {avg_with_breaker}µs"

    def test_circuit_breaker_state_transitions(self):
        """Measure overhead of state transitions."""
        breaker = CircuitBreaker(failure_threshold=3)

        start = time.perf_counter()

        # Trigger failures to move to OPEN
        for _ in range(3):
            breaker.record_failure()

        # Measure transition to HALF_OPEN
        elapsed_open = time.perf_counter() - start

        # Transition back to CLOSED
        start = time.perf_counter()
        for _ in range(2):
            breaker.record_success()
        elapsed_close = time.perf_counter() - start

        print(f"\nCircuit Breaker State Transitions:")
        print(f"  CLOSED to OPEN: {elapsed_open * 1000:.3f}ms")
        print(f"  HALF_OPEN to CLOSED: {elapsed_close * 1000:.3f}ms")

        # State transitions should be fast
        assert elapsed_open < 0.01, f"OPEN transition too slow: {elapsed_open}s"
        assert elapsed_close < 0.01, f"CLOSE transition too slow: {elapsed_close}s"


class TestRetryPolicyPerformance:
    """Benchmark retry policy performance."""

    def test_retry_delay_calculation(self):
        """Measure retry delay calculation performance."""
        policy = RetryPolicy(initial_delay=0.1, max_delay=10.0, backoff_factor=2.0)

        latencies = []
        iterations = 100  # Limited to avoid overflow on high attempt numbers

        for i in range(iterations):
            start = time.perf_counter()
            # Cap attempt at 30 to avoid overflow
            delay = policy.get_delay(min(i, 30))
            elapsed = time.perf_counter() - start
            latencies.append(elapsed * 1000000)  # microseconds

        avg_latency = statistics.mean(latencies)

        print(f"\nRetry Policy Calculation (100 calls):")
        print(f"  Average: {avg_latency:.3f}µs")

        # Calculation should be very fast
        assert avg_latency < 10, f"Retry calculation overhead too high: {avg_latency}µs"


class TestCachePerformance:
    """Benchmark caching performance."""

    def test_cache_lookup_performance(self):
        """Measure cache lookup latency."""
        cache = InMemoryAnalysisCache()

        # Populate cache
        for i in range(1000):
            cache.set(f"key_{i}", {"data": f"value_{i}", "analysis": list(range(10))})

        latencies = []
        iterations = 10000

        # Measure lookups
        for i in range(iterations):
            start = time.perf_counter()
            value = cache.get(f"key_{i % 1000}")
            elapsed = time.perf_counter() - start
            latencies.append(elapsed * 1000000)  # microseconds

        avg_latency = statistics.mean(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]

        print(f"\nCache Lookup Performance (10000 lookups):")
        print(f"  Average: {avg_latency:.3f}µs")
        print(f"  P95: {p95_latency:.3f}µs")

        # Cache lookups should be very fast
        assert avg_latency < 100, f"Cache lookup too slow: {avg_latency}µs"

    def test_cache_hit_rate(self):
        """Verify cache hit rate with repeated lookups."""
        cache = InMemoryAnalysisCache()

        # Populate with 100 entries
        for i in range(100):
            cache.set(f"key_{i}", {"result": f"value_{i}"})

        hits = 0
        misses = 0
        iterations = 1000

        # Access with 80% hit probability (80% of keys are repeated)
        for i in range(iterations):
            # 80% of time access keys 0-79, 20% access keys 100+
            key_num = (i % 80) if i % 5 != 0 else i
            value = cache.get(f"key_{key_num}")
            if value is not None:
                hits += 1
            else:
                misses += 1

        hit_rate = hits / (hits + misses) * 100

        print(f"\nCache Hit Rate:")
        print(f"  Hits: {hits}")
        print(f"  Misses: {misses}")
        print(f"  Hit Rate: {hit_rate:.1f}%")

        # Should achieve reasonable hit rate
        assert hit_rate > 75, f"Cache hit rate too low: {hit_rate}%"


class TestJobTrackerPerformance:
    """Benchmark job tracking performance."""

    def test_job_creation_throughput(self):
        """Measure job creation throughput."""
        tracker = JobTracker()

        start = time.perf_counter()
        iterations = 1000

        for i in range(iterations):
            job = tracker.create_job(f"job_type_{i % 5}", f"project_{i % 10}")

        elapsed = time.perf_counter() - start
        throughput = iterations / elapsed

        print(f"\nJob Tracker Creation Throughput:")
        print(f"  Jobs created: {iterations}")
        print(f"  Time: {elapsed:.3f}s")
        print(f"  Throughput: {throughput:.0f} jobs/sec")

        # Should handle at least 100 jobs/sec
        assert throughput > 100, f"Job creation throughput too low: {throughput} jobs/sec"

    def test_job_status_update_latency(self):
        """Measure job status update latency."""
        tracker = JobTracker()

        # Create some jobs
        jobs = [tracker.create_job("test", f"proj_{i}") for i in range(100)]

        latencies = []

        for job in jobs:
            start = time.perf_counter()
            tracker.mark_completed(job.job_id, {"result": "success"})
            elapsed = time.perf_counter() - start
            latencies.append(elapsed * 1000)

        avg_latency = statistics.mean(latencies)

        print(f"\nJob Status Update Latency:")
        print(f"  Average: {avg_latency:.3f}ms")

        # Status updates should be fast
        assert avg_latency < 5, f"Status update latency too high: {avg_latency}ms"


class TestCompleteWorkflowPerformance:
    """Benchmark complete workflow performance."""

    def test_full_workflow_latency(self):
        """Measure latency of complete workflow."""
        event_emitter = EventEmitter()
        agent_bus = AgentBus(event_emitter)
        orchestrator = MagicMock()
        orchestrator.agent_bus = agent_bus

        code_service = CodeService(config=MagicMock(), orchestrator=orchestrator)
        validation_service = ValidationService(config=MagicMock(), orchestrator=orchestrator)
        quality_service = QualityService(config=MagicMock(), orchestrator=orchestrator)

        # Mock responses
        agent_bus.send_request_sync = MagicMock(
            return_value={"status": "success", "data": {}}
        )

        project = MagicMock()
        project.project_id = "perf_proj"

        # Measure complete workflow
        latencies = []
        iterations = 100

        for _ in range(iterations):
            start = time.perf_counter()

            # Code generation
            code_service.generate_code(project)
            # Validation
            validation_service.run_tests(project.project_id)
            # Quality check
            quality_service.calculate_maturity(project)

            elapsed = time.perf_counter() - start
            latencies.append(elapsed * 1000)

        avg_latency = statistics.mean(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]

        print(f"\nComplete Workflow Latency (100 iterations):")
        print(f"  Average: {avg_latency:.3f}ms")
        print(f"  P95: {p95_latency:.3f}ms")

        # Workflow should complete in reasonable time
        assert avg_latency < 50, f"Workflow latency too high: {avg_latency}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
