"""
Performance Benchmarking Tests for Socrates

Benchmarks key operations:
- Context gathering
- Agent initialization
- Conversation summary generation
- Question generation orchestration
- Answer processing orchestration
"""

import pytest
import time
import logging
from datetime import datetime
import statistics

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Collect and analyze performance metrics"""

    def __init__(self):
        self.measurements = {}

    def record(self, operation: str, elapsed_time: float):
        """Record a measurement"""
        if operation not in self.measurements:
            self.measurements[operation] = []
        self.measurements[operation].append(elapsed_time)

    def get_stats(self, operation: str) -> dict:
        """Get statistics for an operation"""
        if operation not in self.measurements:
            return {}

        times = self.measurements[operation]
        return {
            "count": len(times),
            "min": min(times),
            "max": max(times),
            "avg": statistics.mean(times),
            "median": statistics.median(times),
            "stdev": statistics.stdev(times) if len(times) > 1 else 0,
        }

    def print_report(self):
        """Print performance report"""
        print("\n" + "=" * 70)
        print("PERFORMANCE BENCHMARK REPORT")
        print("=" * 70)

        for operation in sorted(self.measurements.keys()):
            stats = self.get_stats(operation)
            print(f"\n{operation}:")
            print(f"  Count:    {stats['count']}")
            print(f"  Min:      {stats['min']:.4f}s")
            print(f"  Max:      {stats['max']:.4f}s")
            print(f"  Average:  {stats['avg']:.4f}s")
            print(f"  Median:   {stats['median']:.4f}s")
            if stats['stdev'] > 0:
                print(f"  StdDev:   {stats['stdev']:.4f}s")

        print("\n" + "=" * 70)


metrics = PerformanceMetrics()


class TestPerformanceBenchmarks:
    """Performance benchmarking tests"""

    @pytest.fixture
    def orchestrator(self):
        """Initialize orchestrator"""
        try:
            from socrates_api.orchestrator import APIOrchestrator
            return APIOrchestrator(api_key_or_config="")
        except ImportError:
            pytest.skip("Could not import orchestrator")

    @pytest.fixture
    def mock_project(self):
        """Create mock project"""
        class MockProject:
            def __init__(self):
                self.project_id = "perf_test_001"
                self.name = "Performance Test Project"
                self.description = "Testing performance characteristics"
                self.phase = "discovery"
                self.conversation_history = []
                self.pending_questions = []
                self.asked_questions = []
                self.phase_maturity = {"discovery": 0}
                self.goals = ["Test performance"]
                self.requirements = ["Measure context gathering"]
                self.tech_stack = ["Python", "FastAPI"]
                self.constraints = []
                self.files = []
                self.members = []

                # Add conversation history for realism
                for i in range(10):
                    self.conversation_history.append({
                        "type": "question" if i % 2 == 0 else "answer",
                        "content": f"Message {i+1}" * 10,
                        "timestamp": datetime.now().isoformat(),
                    })

        return MockProject()

    def test_context_gathering_performance(self, orchestrator, mock_project):
        """Benchmark context gathering"""
        iterations = 5

        logger.info(f"Benchmarking context gathering ({iterations} iterations)...")

        for i in range(iterations):
            start = time.time()
            context = orchestrator._gather_question_context(mock_project, "user_001")
            elapsed = time.time() - start
            metrics.record("context_gathering", elapsed)
            logger.info(f"  Iteration {i+1}: {elapsed:.4f}s")

        stats = metrics.get_stats("context_gathering")
        assert stats["avg"] < 0.5, f"Context gathering too slow: {stats['avg']:.4f}s"
        logger.info(f"✓ Context gathering average: {stats['avg']:.4f}s (target: <0.5s)")

    def test_agent_context_building_performance(self, orchestrator, mock_project):
        """Benchmark agent context building"""
        iterations = 5

        logger.info(f"Benchmarking agent context building ({iterations} iterations)...")

        for i in range(iterations):
            start = time.time()
            context = orchestrator._build_agent_context(mock_project)
            elapsed = time.time() - start
            metrics.record("agent_context_building", elapsed)
            logger.info(f"  Iteration {i+1}: {elapsed:.4f}s")

        stats = metrics.get_stats("agent_context_building")
        assert stats["avg"] < 0.1, f"Agent context building too slow: {stats['avg']:.4f}s"
        logger.info(f"✓ Agent context building average: {stats['avg']:.4f}s (target: <0.1s)")

    def test_conversation_summary_performance(self, orchestrator, mock_project):
        """Benchmark conversation summary generation"""
        iterations = 10

        logger.info(f"Benchmarking conversation summary ({iterations} iterations)...")

        for i in range(iterations):
            start = time.time()
            summary = orchestrator._generate_conversation_summary(mock_project)
            elapsed = time.time() - start
            metrics.record("conversation_summary", elapsed)
            logger.info(f"  Iteration {i+1}: {elapsed:.6f}s")

        stats = metrics.get_stats("conversation_summary")
        assert stats["avg"] < 0.01, f"Conversation summary too slow: {stats['avg']:.6f}s"
        logger.info(f"✓ Conversation summary average: {stats['avg']:.6f}s (target: <0.01s)")

    def test_orchestrator_initialization_performance(self):
        """Benchmark orchestrator initialization"""
        from socrates_api.orchestrator import APIOrchestrator

        iterations = 3
        logger.info(f"Benchmarking orchestrator initialization ({iterations} iterations)...")

        for i in range(iterations):
            start = time.time()
            orch = APIOrchestrator(api_key_or_config="")
            elapsed = time.time() - start
            metrics.record("orchestrator_initialization", elapsed)
            logger.info(f"  Iteration {i+1}: {elapsed:.4f}s")

        stats = metrics.get_stats("orchestrator_initialization")
        logger.info(f"✓ Orchestrator initialization average: {stats['avg']:.4f}s")

    def test_agent_availability_performance(self, orchestrator):
        """Benchmark agent lookup performance"""
        iterations = 100

        logger.info(f"Benchmarking agent lookup ({iterations} iterations)...")

        for i in range(iterations):
            start = time.time()
            agent = orchestrator.agents.get("socratic_counselor")
            elapsed = time.time() - start
            metrics.record("agent_lookup", elapsed)

        stats = metrics.get_stats("agent_lookup")
        assert stats["avg"] < 0.001, f"Agent lookup too slow: {stats['avg']:.6f}s"
        logger.info(f"✓ Agent lookup average: {stats['avg']:.6f}s (target: <0.001s)")

    def test_event_bus_performance(self, orchestrator):
        """Benchmark event bus operations"""
        from socratic_core import EventBus

        iterations = 10
        logger.info(f"Benchmarking event bus ({iterations} iterations)...")

        def dummy_handler(event):
            pass

        for i in range(iterations):
            start = time.time()
            orchestrator.event_bus.subscribe("test_event", dummy_handler)
            elapsed = time.time() - start
            metrics.record("event_bus_subscribe", elapsed)

        stats = metrics.get_stats("event_bus_subscribe")
        logger.info(f"✓ Event bus subscribe average: {stats['avg']:.6f}s")

    def test_memory_efficiency(self, orchestrator, mock_project):
        """Test memory usage doesn't grow excessively"""
        import tracemalloc

        tracemalloc.start()

        # Create context multiple times
        for i in range(10):
            context = orchestrator._gather_question_context(mock_project, f"user_{i:03d}")
            context = orchestrator._build_agent_context(mock_project)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Memory usage should be reasonable
        memory_mb = peak / 1024 / 1024
        logger.info(f"✓ Peak memory usage: {memory_mb:.2f} MB")
        assert memory_mb < 500, f"Memory usage too high: {memory_mb:.2f} MB"

    @pytest.fixture(scope="session", autouse=True)
    def print_summary(self, request):
        """Print performance summary after all tests"""
        def print_report():
            metrics.print_report()

        request.addfinalizer(print_report)


class TestTargetMetrics:
    """Test against target performance metrics"""

    @pytest.fixture
    def orchestrator(self):
        """Initialize orchestrator"""
        try:
            from socrates_api.orchestrator import APIOrchestrator
            return APIOrchestrator(api_key_or_config="")
        except ImportError:
            pytest.skip("Could not import orchestrator")

    @pytest.fixture
    def mock_project(self):
        """Create mock project"""
        class MockProject:
            def __init__(self):
                self.project_id = "target_test_001"
                self.name = "Target Test Project"
                self.description = "Testing against targets"
                self.phase = "discovery"
                self.conversation_history = [
                    {"type": "question", "content": f"Q{i}", "timestamp": datetime.now().isoformat()}
                    for i in range(20)
                ]
                self.pending_questions = []
                self.asked_questions = []
                self.phase_maturity = {"discovery": 0}
                self.goals = ["Goal 1", "Goal 2"]
                self.requirements = ["Req 1", "Req 2"]
                self.tech_stack = ["Python"]
                self.constraints = []
                self.files = []
                self.members = []

        return MockProject()

    def test_question_generation_target_latency(self, orchestrator, mock_project):
        """
        Test question generation latency < 3 seconds (target)

        Note: Without actual LLM calls, this tests the orchestration overhead.
        Full E2E with LLM would add ~1-2s for model inference.
        """
        start = time.time()

        # Simulate question generation orchestration
        context = orchestrator._gather_question_context(mock_project, "user_001")
        # Would call agent here in real scenario
        orchestrator._build_agent_context(mock_project)

        elapsed = time.time() - start

        logger.info(f"Question generation orchestration: {elapsed:.4f}s")
        assert elapsed < 0.5, f"Orchestration overhead too high: {elapsed:.4f}s"
        logger.info("✓ Meets question generation latency target (with LLM: <3s)")

    def test_answer_processing_target_latency(self, orchestrator, mock_project):
        """
        Test answer processing latency < 2 seconds (target)

        Without actual agent calls, tests orchestration overhead.
        """
        start = time.time()

        # Simulate answer processing
        context = orchestrator._gather_question_context(mock_project, "user_001")
        orchestrator._build_agent_context(mock_project)
        orchestrator._generate_conversation_summary(mock_project)

        elapsed = time.time() - start

        logger.info(f"Answer processing orchestration: {elapsed:.4f}s")
        assert elapsed < 0.5, f"Orchestration overhead too high: {elapsed:.4f}s"
        logger.info("✓ Meets answer processing latency target (with agents: <2s)")


if __name__ == "__main__":
    # Run with: pytest tests/e2e/test_performance_benchmarking.py -v -s
    pytest.main([__file__, "-v", "-s", "--tb=short"])
