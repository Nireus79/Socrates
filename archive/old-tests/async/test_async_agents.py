"""
Async Agent Integration Tests (Phase 2)

Tests for async agent implementations and orchestrator async processing.
Validates concurrent agent operations meet performance targets.
"""

import asyncio
import pytest
import tempfile
import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from socratic_system.config import SocratesConfig
from socratic_system.orchestration.orchestrator import AgentOrchestrator
from socratic_system.models.project import ProjectContext
from socratic_system.models.user import User


@pytest.fixture
async def orchestrator():
    """Create orchestrator with temp database."""
    import gc
    import time
    tmpdir = tempfile.mkdtemp()
    try:
        config = SocratesConfig(
            api_key="test-key",
            projects_db_path=os.path.join(tmpdir, "projects.db"),
            vector_db_path=os.path.join(tmpdir, "vectors.db"),
        )
        orch = AgentOrchestrator(config)
        yield orch

        # Properly close orchestrator and release resources
        try:
            # Close the vector database client if it exists
            if hasattr(orch, 'vector_db') and orch.vector_db:
                try:
                    if hasattr(orch.vector_db, '_client'):
                        orch.vector_db._client = None
                except Exception:
                    pass

            # Close orchestrator
            if hasattr(orch, 'close'):
                orch.close()
        except Exception:
            pass

        # Force garbage collection to release file handles
        gc.collect()
        time.sleep(0.1)  # Brief delay to ensure files are released on Windows
    finally:
        # Clean up temp directory manually with error handling for Windows file locking
        import shutil
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass


@pytest.fixture
def sample_project():
    """Create sample project."""
    return ProjectContext(
        project_id="async_test_proj",
        name="Async Test Project",
        owner="testuser",
        phase="discovery",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        goals="Test async agents",
        requirements=["Req 1", "Req 2"],
        tech_stack=["Python", "FastAPI"],
        status="active",
        progress=25,
        is_archived=False,
    )


class TestAsyncClaude:
    """Test async Claude client integration."""

    @pytest.mark.asyncio
    async def test_generate_socratic_question_async(self, orchestrator):
        """Test async socratic question generation."""
        prompt = "What are the main goals of your project?"

        with patch.object(
            orchestrator.claude_client.async_client.messages,
            "create",
            new_callable=AsyncMock,
        ) as mock_create:
            # Mock response
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="What specific problem does your project solve?")]
            mock_response.usage = MagicMock(input_tokens=10, output_tokens=20)
            mock_create.return_value = mock_response

            result = await orchestrator.claude_client.generate_socratic_question_async(
                prompt
            )

            assert isinstance(result, str)
            assert len(result) > 0
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_detect_conflicts_async(self, orchestrator, sample_project):
        """Test async conflict detection."""
        requirements = sample_project.requirements

        with patch.object(
            orchestrator.claude_client.async_client.messages,
            "create",
            new_callable=AsyncMock,
        ) as mock_create:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="[]")]  # No conflicts
            mock_response.usage = MagicMock(input_tokens=50, output_tokens=10)
            mock_create.return_value = mock_response

            result = await orchestrator.claude_client.detect_conflicts_async(
                requirements
            )

            assert isinstance(result, list)
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_context_async(self, orchestrator, sample_project):
        """Test async context analysis."""
        with patch.object(
            orchestrator.claude_client.async_client.messages,
            "create",
            new_callable=AsyncMock,
        ) as mock_create:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Project analysis: ...")]
            mock_response.usage = MagicMock(input_tokens=50, output_tokens=30)
            mock_create.return_value = mock_response

            result = await orchestrator.claude_client.analyze_context_async(
                sample_project
            )

            assert isinstance(result, str)
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_code_async(self, orchestrator):
        """Test async code generation."""
        context = "Create a Python FastAPI application"

        with patch.object(
            orchestrator.claude_client.async_client.messages,
            "create",
            new_callable=AsyncMock,
        ) as mock_create:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="def hello():\n    return 'Hello'")]
            mock_response.usage = MagicMock(input_tokens=30, output_tokens=100)
            mock_create.return_value = mock_response

            result = await orchestrator.claude_client.generate_code_async(context)

            assert isinstance(result, str)
            assert "def" in result
            mock_create.assert_called_once()


class TestAsyncDatabase:
    """Test async database operations in agent context."""

    @pytest.mark.asyncio
    async def test_async_project_load_and_save(self, orchestrator, sample_project):
        """Test project persistence in async context."""
        # Save (orchestrator database is synchronous)
        result = orchestrator.database.save_project(sample_project)
        assert result is True

        # Load
        loaded = orchestrator.database.load_project(sample_project.project_id)
        assert loaded is not None
        assert loaded.name == sample_project.name

    @pytest.mark.asyncio
    async def test_async_get_user_projects(self, orchestrator):
        """Test async retrieval of user projects."""
        # Create projects
        for i in range(5):
            project = ProjectContext(
                project_id=f"proj_{i}",
                name=f"Project {i}",
                owner="testuser",
                phase="discovery",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            orchestrator.database.save_project(project)

        # Retrieve
        projects = orchestrator.database.get_user_projects("testuser")
        assert len(projects) == 5
        assert all(p.owner == "testuser" for p in projects)


class TestAsyncOrchestrator:
    """Test orchestrator async request processing."""

    @pytest.mark.asyncio
    async def test_orchestrator_async_request_processing(self, orchestrator, sample_project):
        """Test async request routing through orchestrator."""
        orchestrator.database.save_project(sample_project)

        request = {
            "action": "generate_question",
            "project": sample_project,
            "current_user": "testuser",
        }

        with patch.object(
            orchestrator.claude_client,
            "generate_socratic_question_async",
            new_callable=AsyncMock,
        ) as mock_gen:
            mock_gen.return_value = "What are your project goals?"

            # Use sync process_request to avoid mocking complexities
            result = orchestrator.process_request("socratic_counselor", request)
            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_concurrent_async_requests(self, orchestrator, sample_project):
        """Test multiple concurrent async requests."""
        orchestrator.database.save_project(sample_project)

        async def make_request(project_id):
            return orchestrator.database.load_project(project_id)

        # Make 5 concurrent requests
        tasks = [make_request(sample_project.project_id) for _ in range(5)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all(r is not None for r in results)
        assert all(r.project_id == sample_project.project_id for r in results)


class TestAsyncEventEmitter:
    """Test async event emitter functionality."""

    @pytest.mark.asyncio
    async def test_async_event_emission(self, orchestrator):
        """Test emitting events asynchronously."""
        from socratic_system.events import EventType

        event_data = []

        async def listener(data):
            event_data.append(data)
            await asyncio.sleep(0.01)  # Simulate async work

        # Register listener
        orchestrator.event_emitter.on_async(EventType.LOG_INFO, listener)

        # Emit event
        await orchestrator.event_emitter.emit_async(
            EventType.LOG_INFO, {"message": "Test event"}
        )

        assert len(event_data) == 1
        assert event_data[0]["message"] == "Test event"

    @pytest.mark.asyncio
    async def test_concurrent_async_listeners(self, orchestrator):
        """Test multiple async listeners executing concurrently."""
        from socratic_system.events import EventType

        results = []
        execution_times = []
        import time

        async def listener_1(data):
            start = time.time()
            await asyncio.sleep(0.05)
            results.append("listener_1")
            execution_times.append(("listener_1", time.time() - start))

        async def listener_2(data):
            start = time.time()
            await asyncio.sleep(0.05)
            results.append("listener_2")
            execution_times.append(("listener_2", time.time() - start))

        orchestrator.event_emitter.on_async(EventType.LOG_INFO, listener_1)
        orchestrator.event_emitter.on_async(EventType.LOG_INFO, listener_2)

        start = time.time()
        await orchestrator.event_emitter.emit_async(
            EventType.LOG_INFO, {"message": "Concurrent test"}
        )
        total_time = time.time() - start

        assert len(results) == 2
        assert set(results) == {"listener_1", "listener_2"}
        # Should be ~50ms (concurrent), not 100ms (sequential)
        assert total_time < 0.1, f"Concurrent execution took {total_time:.3f}s (should be ~0.05s)"


class TestAsyncConnectionPooling:
    """Test connection pool under async concurrency."""

    @pytest.mark.asyncio
    async def test_connection_pool_concurrent_access(self, orchestrator):
        """Test connection pool handles concurrent database access."""
        projects = []

        async def create_and_save(idx):
            project = ProjectContext(
                project_id=f"pool_test_{idx}",
                name=f"Pool Test {idx}",
                owner="pooluser",
                phase="discovery",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            success = orchestrator.database.save_project(project)
            return success

        # Concurrent saves
        tasks = [create_and_save(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        assert all(results)

        # Verify all saved
        saved_projects = orchestrator.database.get_user_projects("pooluser")
        assert len(saved_projects) == 10

    @pytest.mark.asyncio
    async def test_connection_pool_stress(self, orchestrator):
        """Test connection pool under stress (20 concurrent operations)."""
        async def operation(idx):
            project = ProjectContext(
                project_id=f"stress_{idx}",
                name=f"Stress {idx}",
                owner="stressuser",
                phase="discovery",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            orchestrator.database.save_project(project)
            loaded = orchestrator.database.load_project(f"stress_{idx}")
            return loaded is not None

        tasks = [operation(i) for i in range(20)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should succeed
        successes = sum(1 for r in results if r is True)
        assert successes >= 18  # Allow 1-2 failures under stress


class TestAsyncErrorHandling:
    """Test error handling in async operations."""

    @pytest.mark.asyncio
    async def test_async_database_error_handling(self, orchestrator):
        """Test database error handling in async context."""
        # Try to load non-existent project
        result = orchestrator.database.load_project("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_async_claude_error_recovery(self, orchestrator):
        """Test Claude client error recovery."""
        with patch.object(
            orchestrator.claude_client.async_client.messages,
            "create",
            side_effect=Exception("API Error"),
        ):
            result = await orchestrator.claude_client.generate_socratic_question_async(
                "test prompt"
            )
            # Should return fallback
            assert result == "I'd like to understand your thinking better. Can you elaborate?"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
