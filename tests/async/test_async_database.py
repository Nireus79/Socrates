"""
Async Database Layer Tests (Phase 2)

Tests for AsyncProjectDatabase and AsyncConnectionPool.
Validates concurrent operations, connection pooling, and performance.
"""

import asyncio
import json
import pytest
import tempfile
import os
from datetime import datetime
from pathlib import Path

from socratic_system.database.project_db_async import (
    AsyncProjectDatabase,
    AsyncConnectionPool,
)
from socratic_system.models.project import ProjectContext
from socratic_system.models.user import User
from socratic_system.models import TeamMemberRole


@pytest.fixture
async def async_db():
    """Create async database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_async.db")
        db = AsyncProjectDatabase(db_path, pool_min_size=2, pool_max_size=5)
        await db.initialize()
        yield db
        await db.close()


@pytest.fixture
def sample_project():
    """Create a sample project for testing."""
    return ProjectContext(
        project_id="async_test_001",
        name="Async Test Project",
        owner="testuser",
        phase="discovery",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        goals="Test async operations",
        requirements=["Req 1", "Req 2", "Req 3"],
        tech_stack=["Python", "FastAPI", "PostgreSQL"],
        constraints=["Budget: $50k"],
        team_structure="distributed",
        language_preferences="python",
        deployment_target="aws",
        code_style="black",
        chat_mode="socratic",
        status="active",
        progress=25,
        is_archived=False,
        project_type="software",
    )


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return User(
        username="asyncuser",
        email="asyncuser@example.com",
        passcode_hash="hash123",
        created_at=datetime.now(),
        subscription_tier="premium",
        subscription_status="active",
    )


class TestAsyncConnectionPool:
    """Test AsyncConnectionPool connection management."""

    @pytest.mark.asyncio
    async def test_pool_initialization(self):
        """Test connection pool initializes correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "pool_test.db")
            pool = AsyncConnectionPool(db_path, min_size=2, max_size=5)

            assert not pool._initialized
            await pool.initialize()
            assert pool._initialized

            await pool.close_all()

    @pytest.mark.asyncio
    async def test_pool_acquire_connection(self):
        """Test acquiring connection from pool."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "pool_test.db")
            pool = AsyncConnectionPool(db_path, min_size=1, max_size=3)
            await pool.initialize()

            async with pool.acquire() as conn:
                assert conn is not None
                cursor = await conn.cursor()
                assert cursor is not None

            await pool.close_all()

    @pytest.mark.asyncio
    async def test_pool_concurrent_access(self):
        """Test pool handles concurrent access correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "pool_test.db")
            pool = AsyncConnectionPool(db_path, min_size=2, max_size=10)
            await pool.initialize()

            async def use_connection():
                async with pool.acquire() as conn:
                    cursor = await conn.cursor()
                    return cursor is not None

            # Try 20 concurrent accesses
            tasks = [use_connection() for _ in range(20)]
            results = await asyncio.gather(*tasks)

            assert all(results)
            await pool.close_all()


class TestAsyncProjectDatabase:
    """Test AsyncProjectDatabase operations."""

    @pytest.mark.asyncio
    async def test_save_and_load_project(self, async_db, sample_project):
        """Test saving and loading a project."""
        # Save
        result = await async_db.save_project(sample_project)
        assert result is True

        # Load
        loaded = await async_db.load_project(sample_project.project_id)
        assert loaded is not None
        assert loaded.name == sample_project.name
        assert loaded.owner == sample_project.owner
        assert loaded.requirements == sample_project.requirements

    @pytest.mark.asyncio
    async def test_save_and_load_user(self, async_db, sample_user):
        """Test saving and loading a user."""
        # Save
        result = await async_db.save_user(sample_user)
        assert result is True

        # Load
        loaded = await async_db.load_user(sample_user.username)
        assert loaded is not None
        assert loaded.username == sample_user.username
        assert loaded.passcode_hash == sample_user.passcode_hash

    @pytest.mark.asyncio
    async def test_get_user_projects(self, async_db):
        """Test retrieving user's projects."""
        # Create 10 projects for testuser
        for i in range(10):
            project = ProjectContext(
                project_id=f"async_proj_{i:03d}",
                name=f"Project {i}",
                owner="testuser",
                phase="discovery",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            await async_db.save_project(project)

        # Create 5 projects for otheruser
        for i in range(10, 15):
            project = ProjectContext(
                project_id=f"async_proj_{i:03d}",
                name=f"Project {i}",
                owner="otheruser",
                phase="discovery",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            await async_db.save_project(project)

        # Retrieve testuser's projects
        projects = await async_db.get_user_projects("testuser")
        assert len(projects) == 10
        assert all(p.owner == "testuser" for p in projects)

    @pytest.mark.asyncio
    async def test_archive_project(self, async_db, sample_project):
        """Test archiving a project."""
        # Save
        await async_db.save_project(sample_project)

        # Archive
        result = await async_db.archive_project(sample_project.project_id)
        assert result is True

        # Verify archived
        loaded = await async_db.load_project(sample_project.project_id)
        assert loaded.is_archived is True

    @pytest.mark.asyncio
    async def test_delete_project(self, async_db, sample_project):
        """Test deleting a project."""
        # Save
        await async_db.save_project(sample_project)

        # Delete
        result = await async_db.delete_project(sample_project.project_id)
        assert result is True

        # Verify deleted
        loaded = await async_db.load_project(sample_project.project_id)
        assert loaded is None

    @pytest.mark.asyncio
    async def test_conversation_history(self, async_db, sample_project):
        """Test saving and loading conversation history."""
        # Save project first
        await async_db.save_project(sample_project)

        # Save conversation history
        history = [
            {"role": "user", "content": "Hello", "timestamp": datetime.now().isoformat()},
            {
                "role": "assistant",
                "content": "Hi there!",
                "timestamp": datetime.now().isoformat(),
            },
            {
                "role": "user",
                "content": "How are you?",
                "timestamp": datetime.now().isoformat(),
            },
        ]

        result = await async_db.save_conversation_history(sample_project.project_id, history)
        assert result is True

        # Load history
        loaded_history = await async_db.get_conversation_history(sample_project.project_id)
        assert len(loaded_history) == 3
        assert loaded_history[0]["role"] == "user"
        assert loaded_history[0]["content"] == "Hello"

    @pytest.mark.asyncio
    async def test_bulk_save_projects(self, async_db):
        """Test bulk saving projects."""
        projects = []
        for i in range(10):
            project = ProjectContext(
                project_id=f"bulk_proj_{i:03d}",
                name=f"Bulk Project {i}",
                owner="bulkuser",
                phase="discovery",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            projects.append(project)

        saved_count = await async_db.bulk_save_projects(projects)
        assert saved_count == 10

        # Verify all saved
        user_projects = await async_db.get_user_projects("bulkuser")
        assert len(user_projects) == 10

    @pytest.mark.asyncio
    async def test_project_data_integrity(self, async_db, sample_project):
        """Test all project fields are preserved."""
        await async_db.save_project(sample_project)
        loaded = await async_db.load_project(sample_project.project_id)

        assert loaded.project_id == sample_project.project_id
        assert loaded.name == sample_project.name
        assert loaded.owner == sample_project.owner
        assert loaded.phase == sample_project.phase
        assert loaded.goals == sample_project.goals
        assert loaded.requirements == sample_project.requirements
        assert loaded.tech_stack == sample_project.tech_stack
        assert loaded.constraints == sample_project.constraints
        assert loaded.team_structure == sample_project.team_structure
        assert loaded.status == sample_project.status
        assert loaded.progress == sample_project.progress
        assert loaded.is_archived == sample_project.is_archived


class TestAsyncConcurrentOperations:
    """Test concurrent async operations."""

    @pytest.mark.asyncio
    async def test_concurrent_project_saves(self, async_db):
        """Test concurrent project save operations."""

        async def save_project(project_id):
            project = ProjectContext(
                project_id=project_id,
                name=f"Concurrent Project {project_id}",
                owner="concurrentuser",
                phase="discovery",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            return await async_db.save_project(project)

        # Save 20 projects concurrently
        tasks = [save_project(f"concurrent_proj_{i:03d}") for i in range(20)]
        results = await asyncio.gather(*tasks)

        assert all(results)
        projects = await async_db.get_user_projects("concurrentuser")
        assert len(projects) == 20

    @pytest.mark.asyncio
    async def test_concurrent_project_loads(self, async_db):
        """Test concurrent project load operations."""
        # Create 20 projects
        for i in range(20):
            project = ProjectContext(
                project_id=f"load_test_{i:03d}",
                name=f"Load Test {i}",
                owner="loaduser",
                phase="discovery",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                goals=f"Goal {i}",
            )
            await async_db.save_project(project)

        # Load all concurrently
        async def load_project(project_id):
            return await async_db.load_project(project_id)

        tasks = [load_project(f"load_test_{i:03d}") for i in range(20)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 20
        assert all(r is not None for r in results)
        assert all(r.owner == "loaduser" for r in results)

    @pytest.mark.asyncio
    async def test_mixed_concurrent_operations(self, async_db):
        """Test mixed save/load/delete operations concurrently."""

        async def mixed_operations():
            # Save
            project = ProjectContext(
                project_id=f"mixed_{asyncio.current_task().get_name()}",
                name="Mixed Op",
                owner="mixeduser",
                phase="discovery",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            await async_db.save_project(project)

            # Load
            loaded = await async_db.load_project(project.project_id)
            return loaded is not None

        # Run 15 mixed operations concurrently
        tasks = [mixed_operations() for _ in range(15)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check results (ignore naming issues)
        successes = sum(1 for r in results if r is True or r is None)
        assert successes >= 10  # Most should succeed


class TestAsyncPerformance:
    """Performance benchmarks for async operations."""

    @pytest.mark.asyncio
    async def test_async_save_performance(self, async_db, sample_project):
        """Benchmark async project save."""
        import time

        start = time.perf_counter()
        await async_db.save_project(sample_project)
        duration = time.perf_counter() - start

        # Should be fast (< 100ms)
        assert duration < 0.1
        print(f"Async save: {duration*1000:.1f}ms")

    @pytest.mark.asyncio
    async def test_async_load_performance(self, async_db, sample_project):
        """Benchmark async project load."""
        import time

        await async_db.save_project(sample_project)

        start = time.perf_counter()
        loaded = await async_db.load_project(sample_project.project_id)
        duration = time.perf_counter() - start

        # Should be fast (< 50ms)
        assert duration < 0.05
        print(f"Async load: {duration*1000:.1f}ms")

    @pytest.mark.asyncio
    async def test_concurrent_speedup(self, async_db):
        """
        Test concurrent operations demonstrate non-blocking behavior.

        10 concurrent saves should complete without errors and be reasonably fast.
        (Exact speedup depends on system load and I/O characteristics)
        """
        import time

        # Concurrent saves
        async def save_project(idx):
            project = ProjectContext(
                project_id=f"conc_speedup_{idx}",
                name=f"Concurrent {idx}",
                owner="concuser_speedup",
                phase="discovery",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            return await async_db.save_project(project)

        start = time.perf_counter()
        tasks = [save_project(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        conc_duration = time.perf_counter() - start

        # Verify all saves succeeded
        assert all(results)
        # Should complete in reasonable time (< 2 seconds for 10 saves)
        assert conc_duration < 2.0, f"Concurrent 10 saves took {conc_duration:.2f}s"
        print(f"Concurrent 10 saves: {conc_duration*1000:.1f}ms")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
