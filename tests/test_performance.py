"""
Performance benchmarking tests for Socrates

Benchmarks key operations to identify bottlenecks and track performance regression.

Run with: pytest tests/test_performance.py -v --benchmark-only
"""

import pytest
from unittest.mock import patch, Mock
from datetime import datetime

import socrates


@pytest.fixture
def benchmark_config(test_config):
    """Config for benchmarking"""
    return test_config


@pytest.mark.slow
@pytest.mark.benchmark
class TestConfigPerformance:
    """Performance tests for configuration"""

    def test_config_creation_benchmark(self, benchmark, mock_api_key):
        """Benchmark SocratesConfig creation"""
        def create_config():
            return socrates.SocratesConfig(api_key=mock_api_key)

        result = benchmark(create_config)
        assert result is not None

    def test_config_from_env_benchmark(self, benchmark, mock_api_key):
        """Benchmark loading config from environment"""
        import os
        from unittest.mock import patch

        def load_config():
            with patch.dict(os.environ, {'ANTHROPIC_API_KEY': mock_api_key}):
                return socrates.SocratesConfig.from_env()

        result = benchmark(load_config)
        assert result is not None

    def test_config_builder_benchmark(self, benchmark, mock_api_key, temp_data_dir):
        """Benchmark ConfigBuilder"""
        def build_config():
            return socrates.ConfigBuilder(mock_api_key) \
                .with_data_dir(temp_data_dir) \
                .with_log_level("DEBUG") \
                .build()

        result = benchmark(build_config)
        assert result is not None


@pytest.mark.slow
@pytest.mark.benchmark
class TestEventPerformance:
    """Performance tests for event system"""

    def test_event_emission_benchmark(self, benchmark, mock_event_emitter):
        """Benchmark event emission"""
        callback = Mock()
        mock_event_emitter.on(socrates.EventType.LOG_INFO, callback)

        def emit_events():
            for i in range(100):
                mock_event_emitter.emit(socrates.EventType.LOG_INFO, {"index": i})

        benchmark(emit_events)
        assert callback.call_count == 100

    def test_listener_registration_benchmark(self, benchmark, mock_event_emitter):
        """Benchmark listener registration"""
        callbacks = [Mock() for _ in range(50)]

        def register_listeners():
            for callback in callbacks:
                mock_event_emitter.on(socrates.EventType.LOG_INFO, callback)

        benchmark(register_listeners)
        assert mock_event_emitter.listener_count(socrates.EventType.LOG_INFO) == 50

    def test_listener_removal_benchmark(self, benchmark, mock_event_emitter):
        """Benchmark listener removal"""
        callbacks = [Mock() for _ in range(50)]

        for callback in callbacks:
            mock_event_emitter.on(socrates.EventType.LOG_INFO, callback)

        def remove_listeners():
            for callback in callbacks:
                mock_event_emitter.remove_listener(socrates.EventType.LOG_INFO, callback)

        benchmark(remove_listeners)
        assert mock_event_emitter.listener_count(socrates.EventType.LOG_INFO) == 0


@pytest.mark.slow
@pytest.mark.benchmark
class TestOrchestratorPerformance:
    """Performance tests for orchestrator"""

    def test_orchestrator_creation_benchmark(self, benchmark, benchmark_config):
        """Benchmark orchestrator creation"""
        def create_orchestrator():
            with patch('anthropic.Anthropic'):
                return socrates.AgentOrchestrator(benchmark_config)

        result = benchmark(create_orchestrator)
        assert result is not None

    def test_orchestrator_request_benchmark(self, benchmark, benchmark_config):
        """Benchmark request processing"""
        with patch('anthropic.Anthropic'):
            orchestrator = socrates.AgentOrchestrator(benchmark_config)

            def process_request():
                return orchestrator.process_request('project_manager', {
                    'action': 'list_projects'
                })

            result = benchmark(process_request)
            assert result is not None


@pytest.mark.slow
@pytest.mark.benchmark
class TestDatabasePerformance:
    """Performance tests for database operations"""

    def test_project_save_benchmark(self, benchmark, benchmark_config, sample_project):
        """Benchmark saving a project"""
        from socratic_system.database import ProjectDatabase

        db = ProjectDatabase(str(benchmark_config.projects_db_path))

        def save_project():
            db.save_project(sample_project)

        benchmark(save_project)

    def test_project_load_benchmark(self, benchmark, benchmark_config, sample_project):
        """Benchmark loading a project"""
        from socratic_system.database import ProjectDatabase

        db = ProjectDatabase(str(benchmark_config.projects_db_path))
        db.save_project(sample_project)

        def load_project():
            return db.load_project(sample_project.project_id)

        result = benchmark(load_project)
        assert result is not None

    def test_project_list_benchmark(self, benchmark, benchmark_config):
        """Benchmark listing projects"""
        from socratic_system.database import ProjectDatabase
        from socratic_system.models import ProjectContext
        from datetime import datetime

        db = ProjectDatabase(str(benchmark_config.projects_db_path))

        # Pre-populate with test data
        for i in range(10):
            project = ProjectContext(
                project_id=f"test_proj_{i}",
                name=f"Test Project {i}",
                owner="testuser",
                phase="active",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.save_project(project)

        def list_projects():
            return db.get_user_projects("testuser")

        result = benchmark(list_projects)
        assert len(result) == 10


@pytest.mark.slow
@pytest.mark.benchmark
class TestModelPerformance:
    """Performance tests for data models"""

    def test_user_creation_benchmark(self, benchmark):
        """Benchmark creating User objects"""
        from socratic_system.models import User
        from datetime import datetime

        def create_user():
            return User(
                username="testuser",
                passcode_hash="hashed_password",
                created_at=datetime.now()
            )

        result = benchmark(create_user)
        assert result is not None

    def test_project_creation_benchmark(self, benchmark):
        """Benchmark creating ProjectContext objects"""
        from socratic_system.models import ProjectContext
        from datetime import datetime

        def create_project():
            return ProjectContext(
                project_id="test_proj",
                name="Test Project",
                owner="testuser",
                phase="active",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

        result = benchmark(create_project)
        assert result is not None

    def test_knowledge_entry_creation_benchmark(self, benchmark):
        """Benchmark creating KnowledgeEntry objects"""
        from socratic_system.models import KnowledgeEntry

        def create_entry():
            return KnowledgeEntry(
                id="entry_001",
                content="Test content " * 100,  # ~1KB content
                category="test",
                metadata={"source": "test"}
            )

        result = benchmark(create_entry)
        assert result is not None


@pytest.mark.slow
@pytest.mark.benchmark
class TestMemoryUsage:
    """Memory usage tests"""

    def test_large_event_emission(self, benchmark):
        """Benchmark memory usage with many events"""
        emitter = socrates.EventEmitter()

        def emit_many_events():
            for i in range(1000):
                emitter.emit(socrates.EventType.LOG_INFO, {
                    "index": i,
                    "data": "test" * 10
                })

        benchmark(emit_many_events)

    def test_many_listeners(self, benchmark):
        """Benchmark memory with many listeners"""
        emitter = socrates.EventEmitter()

        def register_many_listeners():
            for i in range(100):
                callback = Mock()
                emitter.on(socrates.EventType.LOG_INFO, callback)

        benchmark(register_many_listeners)
        assert emitter.listener_count(socrates.EventType.LOG_INFO) == 100


# Benchmark comparison matrix
def test_benchmark_summary(benchmark_results) -> None:
    """Summary of benchmark results"""
    if hasattr(benchmark_results, 'stats'):
        stats = benchmark_results.stats
        print(f"\nBenchmark Summary:")
        print(f"  Min: {stats.min:.3f}s")
        print(f"  Max: {stats.max:.3f}s")
        print(f"  Mean: {stats.mean:.3f}s")
        print(f"  Median: {stats.median:.3f}s")
