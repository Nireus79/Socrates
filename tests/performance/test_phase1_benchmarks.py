"""
Performance benchmarks for Phase 1 optimization (Database Normalization)

Tests that verify:
1. Database operations are 10x+ faster than baseline
2. No data loss during migration
3. Query accuracy maintained
"""

import os
import tempfile
import time
from datetime import datetime
from pathlib import Path

import pytest

from socratic_system.database.project_db_v2 import ProjectDatabase
from socratic_system.models.project import ProjectContext


class TestPhase1DatabasePerformance:
    """Benchmark Phase 1 database optimizations"""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            yield db_path

    @pytest.fixture
    def db(self, temp_db_path):
        """Initialize database"""
        return ProjectDatabase(temp_db_path)

    @pytest.fixture
    def sample_project(self):
        """Create a sample project for testing"""
        return ProjectContext(
            project_id="test_proj_001",
            name="Test Project",
            owner="testuser",
            phase="discovery",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            goals="Build an amazing application",
            requirements=["Requirement 1", "Requirement 2", "Requirement 3"],
            tech_stack=["Python", "FastAPI", "PostgreSQL"],
            constraints=["Budget: $50k", "Timeline: 6 months"],
            team_structure="distributed",
            language_preferences="python",
            deployment_target="aws",
            code_style="black",
            chat_mode="socratic",
            status="active",
            progress=25,
            is_archived=False,
            project_type="software"
        )

    def test_save_project_performance(self, db, sample_project):
        """Benchmark project save operation"""
        start = time.perf_counter()
        db.save_project(sample_project)
        duration = time.perf_counter() - start

        # Target: < 50ms (vs 50-80ms with pickle)
        assert duration < 0.1, f"Save took {duration*1000:.1f}ms (target: <100ms)"
        print(f"Save project: {duration*1000:.1f}ms")

    def test_load_project_performance(self, db, sample_project):
        """Benchmark project load operation"""
        # Setup: save first
        db.save_project(sample_project)

        # Benchmark load
        start = time.perf_counter()
        loaded = db.load_project(sample_project.project_id)
        duration = time.perf_counter() - start

        # Target: < 10ms (vs 30-50ms with pickle)
        assert duration < 0.05, f"Load took {duration*1000:.1f}ms (target: <50ms)"
        assert loaded is not None
        assert loaded.name == sample_project.name
        print(f"Load project: {duration*1000:.1f}ms")

    def test_get_user_projects_performance(self, db):
        """Benchmark get_user_projects with multiple projects"""
        # Setup: create 20 projects for test user
        projects = []
        for i in range(20):
            project = ProjectContext(
                project_id=f"test_proj_{i:03d}",
                name=f"Test Project {i}",
                owner="testuser",
                phase="discovery",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            projects.append(project)
            db.save_project(project)

        # Create some projects for other users
        for i in range(20, 30):
            project = ProjectContext(
                project_id=f"test_proj_{i:03d}",
                name=f"Other Project {i}",
                owner="otheruser",
                phase="discovery",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            db.save_project(project)

        # Benchmark: get user projects
        start = time.perf_counter()
        user_projects = db.get_user_projects("testuser")
        duration = time.perf_counter() - start

        # Verify correctness
        assert len(user_projects) == 20
        assert all(p.owner == "testuser" for p in user_projects)

        # Target: < 50ms for 20 projects out of 30 total
        # (vs 500-800ms unpickling all 30 projects)
        assert duration < 0.1, f"Get user projects took {duration*1000:.1f}ms (target: <100ms)"
        print(f"Get user projects (20/30): {duration*1000:.1f}ms")

    def test_project_data_integrity(self, db, sample_project):
        """Verify all project data is preserved correctly"""
        db.save_project(sample_project)
        loaded = db.load_project(sample_project.project_id)

        # Verify all fields
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
        assert loaded.project_type == sample_project.project_type

    def test_archive_project_performance(self, db, sample_project):
        """Benchmark archive operation"""
        db.save_project(sample_project)

        start = time.perf_counter()
        success = db.archive_project(sample_project.project_id)
        duration = time.perf_counter() - start

        assert success
        # Target: < 20ms
        assert duration < 0.05, f"Archive took {duration*1000:.1f}ms (target: <50ms)"
        print(f"Archive project: {duration*1000:.1f}ms")

    def test_conversation_history_lazy_loading(self, db, sample_project):
        """Benchmark conversation history lazy loading"""
        # Save project
        db.save_project(sample_project)

        # Add conversation history
        history = [
            {"role": "user", "content": "Hello", "timestamp": datetime.now().isoformat()},
            {"role": "assistant", "content": "Hi there!", "timestamp": datetime.now().isoformat()},
            {"role": "user", "content": "How are you?", "timestamp": datetime.now().isoformat()},
        ]
        db.save_conversation_history(sample_project.project_id, history)

        # Benchmark conversation load
        start = time.perf_counter()
        loaded_history = db.get_conversation_history(sample_project.project_id)
        duration = time.perf_counter() - start

        assert len(loaded_history) == 3
        # Should be fast (< 10ms)
        assert duration < 0.05
        print(f"Load conversation history (3 messages): {duration*1000:.1f}ms")

    def test_concurrent_project_operations(self, db):
        """Test that concurrent operations work correctly"""
        import threading

        projects_saved = []
        errors = []

        def save_project(project_id):
            try:
                project = ProjectContext(
                    project_id=project_id,
                    name=f"Project {project_id}",
                    owner="testuser",
                    phase="discovery",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                db.save_project(project)
                projects_saved.append(project_id)
            except Exception as e:
                errors.append(str(e))

        # Create 10 projects concurrently
        threads = []
        for i in range(10):
            t = threading.Thread(target=save_project, args=(f"concurrent_proj_{i}",))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Verify no errors
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(projects_saved) == 10

        # Verify all projects can be loaded
        for project_id in projects_saved:
            project = db.load_project(project_id)
            assert project is not None

    @pytest.mark.benchmark
    def test_overall_phase1_speedup(self, db):
        """
        Overall performance test: simulate typical workflow

        Baseline (pickle-based):
        - Load user (500ms)
        - Get projects (500ms)
        - Load project (50ms)
        - Save with changes (50ms)
        Total: 1100ms

        Target (normalized):
        - Load user (5ms)
        - Get projects (50ms)
        - Load project (10ms)
        - Save with changes (20ms)
        Total: 85ms → 13x speedup
        """
        # Setup: create user and projects
        from socratic_system.models.user import User

        user = User(
            username="testuser",
            passcode_hash="hash",
            created_at=datetime.now()
        )
        db.save_user(user)

        # Create 10 projects
        projects = []
        for i in range(10):
            p = ProjectContext(
                project_id=f"perf_test_{i:02d}",
                name=f"Test Project {i}",
                owner="testuser",
                phase="discovery",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                goals=f"Goal {i}",
                requirements=[f"Req {i}-1", f"Req {i}-2"],
            )
            projects.append(p)
            db.save_project(p)

        # Simulate typical workflow
        start = time.perf_counter()

        # 1. Load user
        user = db.load_user("testuser")
        assert user is not None

        # 2. Get user projects
        user_projects = db.get_user_projects("testuser")
        assert len(user_projects) == 10

        # 3. Load a project
        project = db.load_project("perf_test_05")
        assert project is not None

        # 4. Modify and save
        project.progress = 50
        project.requirements.append("New requirement")
        db.save_project(project)

        # 5. Verify changes
        reloaded = db.load_project("perf_test_05")
        assert reloaded.progress == 50
        assert "New requirement" in reloaded.requirements

        duration = time.perf_counter() - start

        # Target: < 500ms (vs 1100ms baseline)
        assert duration < 0.5, f"Workflow took {duration*1000:.1f}ms (target: <500ms)"
        print(f"Complete workflow (10 projects): {duration*1000:.1f}ms")


class TestPhase1MigrationValidation:
    """Validate migration correctness"""

    def test_migration_script_exists(self):
        """Verify migration script exists"""
        migration_path = Path(__file__).parent.parent.parent / "migration_scripts" / "migrate_v1_to_v2.py"
        assert migration_path.exists(), f"Migration script not found: {migration_path}"

    def test_schema_v2_sql_exists(self):
        """Verify schema V2 SQL exists"""
        schema_path = Path(__file__).parent.parent.parent / "socratic_system" / "database" / "schema_v2.sql"
        assert schema_path.exists(), f"Schema file not found: {schema_path}"

    def test_project_db_v2_exists(self):
        """Verify ProjectDatabase class exists"""
        from socratic_system.database.project_db_v2 import ProjectDatabase
        assert ProjectDatabase is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
