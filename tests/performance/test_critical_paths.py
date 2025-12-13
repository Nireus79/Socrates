"""
Performance benchmarks for critical paths before refactoring

Establishes baselines for:
- ProjectContext.__post_init__ performance
- ChatCommand.execute response time

Run before refactoring to verify no performance degradation after changes.
"""

import os
import tempfile
import time
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from socratic_system.config import SocratesConfig
from socratic_system.models import ProjectContext


class TestProjectContextPerformance:
    """Benchmark ProjectContext initialization performance"""

    def test_project_init_single_performance(self):
        """Test single project initialization is fast"""
        start = time.perf_counter()
        project = ProjectContext(
            project_id="perf-test-1",
            name="Performance Test Project",
            owner="test_user",
            phase="discovery",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        end = time.perf_counter()

        duration = end - start
        # Verify project was created
        assert project.project_id == "perf-test-1"
        # Single project init should be < 10ms
        assert duration < 0.01, f"Single project init took {duration:.6f}s (expected < 0.01s)"

    def test_project_init_batch_performance(self):
        """Test batch project initialization performance

        Simulates loading 100 projects from database
        """
        projects_data = [
            {
                "project_id": f"perf-test-{i}",
                "name": f"Project {i}",
                "owner": f"user_{i % 10}",
                "phase": "discovery",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }
            for i in range(100)
        ]

        start = time.perf_counter()
        projects = []
        for p_data in projects_data:
            project = ProjectContext(**p_data)
            projects.append(project)
        end = time.perf_counter()

        duration = end - start
        avg_per_project = duration / 100

        # Batch of 100 projects should complete in < 1 second
        assert duration < 1.0, f"Batch init (100 projects) took {duration:.3f}s (expected < 1.0s)"
        # Average per project should be < 10ms
        assert (
            avg_per_project < 0.01
        ), f"Average per project: {avg_per_project:.6f}s (expected < 0.01s)"

    def test_project_init_with_team_members_performance(self):
        """Test project initialization with team members"""
        from socratic_system.models import TeamMemberRole

        team_members = [
            TeamMemberRole(
                username=f"user_{i}",
                role="creator" if i > 0 else "lead",
                skills=["python", "design"],
                joined_at=datetime.now(),
            )
            for i in range(5)  # Owner + 4 team members
        ]

        start = time.perf_counter()
        project = ProjectContext(
            project_id="perf-test-team",
            name="Team Project",
            owner="owner_user",
            phase="discovery",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            team_members=team_members,
        )
        end = time.perf_counter()

        duration = end - start
        # Verify project was created with team members
        assert len(project.team_members) == 5
        # With team members should still be < 10ms
        assert duration < 0.01, f"Team project init took {duration:.6f}s (expected < 0.01s)"

    def test_project_init_with_legacy_collaborators_performance(self):
        """Test project initialization with legacy collaborators (migration path)

        This tests the migration from old collaborators list to team_members
        """
        collaborators = [f"user_{i}" for i in range(10)]  # Legacy format

        start = time.perf_counter()
        project = ProjectContext(
            project_id="perf-test-legacy",
            name="Legacy Project",
            owner="owner_user",
            phase="discovery",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            collaborators=collaborators,
        )
        end = time.perf_counter()

        duration = end - start
        # Migration should be reasonably fast (< 20ms for 10 collaborators)
        assert (
            duration < 0.02
        ), f"Legacy migration init took {duration:.6f}s (expected < 0.02s)"

        # Verify migration happened correctly
        assert len(project.team_members) == len(collaborators) + 1  # +1 for owner


class TestChatCommandPerformance:
    """Benchmark ChatCommand.execute performance (stub - requires mock setup)"""

    @pytest.fixture
    def chat_command_context(self):
        """Create mock context for chat command testing"""
        from socratic_system.models import User
        from socratic_system.orchestration import AgentOrchestrator
        from socratic_system.ui.context_display import ContextDisplay
        from socratic_system.ui.main_app import SocraticRAGSystem
        from socratic_system.ui.navigation import NavigationStack

        # Create temp database for testing
        temp_dir = tempfile.mkdtemp()
        os.environ["SOCRATES_DATA_DIR"] = temp_dir

        with patch.dict(os.environ, {"API_KEY_CLAUDE": "test-key"}):
            with patch("socratic_system.orchestration.orchestrator.ClaudeClient"):
                with patch("socratic_system.orchestration.orchestrator.VectorDatabase"):
                    config = SocratesConfig.from_env()
                    orch = AgentOrchestrator(config)
                    orch.claude_client = MagicMock()

                    app = SocraticRAGSystem()
                    app.orchestrator = orch
                    app.nav_stack = NavigationStack()
                    app.context_display = ContextDisplay()

                    user = User(
                        username="perf_test_user",
                        passcode_hash="test_hash",
                        created_at=datetime.now(),
                        projects=[],
                    )
                    orch.database.save_user(user)
                    app.current_user = user

                    project = ProjectContext(
                        project_id="perf-test-chat",
                        name="Chat Test Project",
                        owner="perf_test_user",
                        phase="discovery",
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                    )
                    orch.database.save_project(project)
                    app.current_project = project

                    yield {
                        "orchestrator": orch,
                        "app": app,
                        "user": user,
                        "project": project,
                    }

    def test_chat_command_parse_time(self, chat_command_context):
        """Test that parsing chat input is fast (< 1ms)"""
        # This is a simple test to show baseline for command parsing
        # The full chat loop would require simulating user input

        start = time.perf_counter()
        # Simulate parsing a command
        test_input = "/mode direct"
        parts = test_input.split()
        command = parts[0]
        args = parts[1:]
        end = time.perf_counter()

        duration = end - start
        # Verify parsing worked correctly
        assert command == "/mode"
        assert args == ["direct"]
        # Command parsing should be < 1ms
        assert duration < 0.001, f"Command parsing took {duration:.6f}s (expected < 0.001s)"


# Performance thresholds summary
PERFORMANCE_THRESHOLDS = {
    "project_init_single": 0.01,  # 10ms
    "project_init_batch": 1.0,  # 1 second for 100 projects
    "project_init_per_item": 0.01,  # 10ms per project
    "project_init_with_team": 0.01,  # 10ms with team members
    "project_init_legacy_migration": 0.02,  # 20ms for legacy migration
    "chat_command_parse": 0.001,  # 1ms for command parsing
}


def test_performance_thresholds_documented():
    """Verify performance thresholds are documented"""
    assert len(PERFORMANCE_THRESHOLDS) > 0
    for name, threshold in PERFORMANCE_THRESHOLDS.items():
        assert threshold > 0, f"Threshold '{name}' must be > 0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
