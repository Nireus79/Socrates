"""
Unit tests for new CLI commands added in Phase 9.

These tests verify command instantiation, error handling, and basic functionality
without requiring external services or API servers.
"""

import pytest
from unittest.mock import MagicMock, patch
from socratic_system.ui.commands.conflict_commands import ConflictAnalyzeCommand
from socratic_system.ui.commands.workflow_commands import WorkflowCreateCommand
from socratic_system.ui.commands.security_commands import SecurityStatusCommand
from socratic_system.ui.commands.performance_commands import PerformanceStatusCommand
from socratic_system.ui.commands.learning_commands import LearningRecommendationsCommand
from socratic_system.ui.commands.analyzer_commands import AnalyzeCodeCommand
from socratic_system.ui.commands.docs_generation_commands import GenerateReadmeCommand


@pytest.mark.unit
class TestConflictCommandsUnit:
    """Unit tests for conflict detection commands."""

    def test_conflict_analyze_command_has_required_attributes(self):
        """Test ConflictAnalyzeCommand has required attributes."""
        cmd = ConflictAnalyzeCommand()
        assert hasattr(cmd, 'name')
        assert hasattr(cmd, 'description')
        assert hasattr(cmd, 'usage')
        assert hasattr(cmd, 'execute')

    def test_conflict_analyze_command_name_correct(self):
        """Test ConflictAnalyzeCommand has correct name."""
        cmd = ConflictAnalyzeCommand()
        assert cmd.name == "conflict analyze"

    def test_conflict_analyze_command_execute_returns_dict(self):
        """Test ConflictAnalyzeCommand execute returns dict."""
        cmd = ConflictAnalyzeCommand()
        result = cmd.execute([], {})
        assert isinstance(result, dict)
        assert "status" in result
        assert "message" in result

    def test_conflict_analyze_command_without_orchestrator_fails(self):
        """Test ConflictAnalyzeCommand fails without orchestrator."""
        cmd = ConflictAnalyzeCommand()
        result = cmd.execute([], {"some_key": "value"})
        assert result["status"] == "error"


@pytest.mark.unit
class TestWorkflowCommandsUnit:
    """Unit tests for workflow commands."""

    def test_workflow_create_command_has_required_attributes(self):
        """Test WorkflowCreateCommand has required attributes."""
        cmd = WorkflowCreateCommand()
        assert cmd.name == "workflow create"
        assert "workflow" in cmd.description.lower()
        assert "create" in cmd.usage.lower()

    def test_workflow_create_command_returns_error_without_context(self):
        """Test WorkflowCreateCommand returns error without context."""
        cmd = WorkflowCreateCommand()
        result = cmd.execute([], {})
        assert isinstance(result, dict)
        assert "status" in result


@pytest.mark.unit
class TestSecurityCommandsUnit:
    """Unit tests for security commands."""

    def test_security_status_command_name(self):
        """Test SecurityStatusCommand has correct name."""
        cmd = SecurityStatusCommand()
        assert cmd.name == "security status"

    def test_security_status_command_description(self):
        """Test SecurityStatusCommand has appropriate description."""
        cmd = SecurityStatusCommand()
        assert "security" in cmd.description.lower()
        assert "status" in cmd.description.lower()

    def test_security_status_command_execute_fails_without_orchestrator(self):
        """Test SecurityStatusCommand fails without orchestrator."""
        cmd = SecurityStatusCommand()
        result = cmd.execute([], {})
        assert result["status"] == "error"
        assert "Orchestrator" in result["message"]

    def test_security_status_command_with_mock_orchestrator(self):
        """Test SecurityStatusCommand works with mocked orchestrator."""
        cmd = SecurityStatusCommand()
        mock_orch = MagicMock()
        mock_orch.database.get_security_incidents = MagicMock(return_value=[])

        result = cmd.execute([], {"orchestrator": mock_orch})
        assert result["status"] == "success"
        assert "data" in result


@pytest.mark.unit
class TestPerformanceCommandsUnit:
    """Unit tests for performance commands."""

    def test_performance_status_command_name(self):
        """Test PerformanceStatusCommand has correct name."""
        cmd = PerformanceStatusCommand()
        assert cmd.name == "performance status"

    def test_performance_status_command_fails_without_performance_lib(self):
        """Test PerformanceStatusCommand fails without performance library."""
        cmd = PerformanceStatusCommand()
        mock_orch = MagicMock()
        mock_orch.library_manager.performance = None

        result = cmd.execute([], {"orchestrator": mock_orch})
        assert result["status"] == "error"

    def test_performance_status_command_with_stats(self):
        """Test PerformanceStatusCommand returns stats when available."""
        cmd = PerformanceStatusCommand()
        mock_orch = MagicMock()
        mock_orch.library_manager.performance.get_performance_stats = MagicMock(
            return_value={
                "total_calls": 100,
                "avg_duration_ms": 50.0,
                "max_duration_ms": 200.0
            }
        )
        mock_orch.library_manager.performance.get_cache_stats = MagicMock(
            return_value={"cache_size": 1024, "hit_rate": "95%"}
        )

        result = cmd.execute([], {"orchestrator": mock_orch})
        assert result["status"] == "success"
        assert result["data"]["execution_stats"]["total_calls"] == 100
        assert result["data"]["cache_stats"]["hit_rate"] == "95%"


@pytest.mark.unit
class TestLearningCommandsUnit:
    """Unit tests for learning commands."""

    def test_learning_recommendations_command_name(self):
        """Test LearningRecommendationsCommand has correct name."""
        cmd = LearningRecommendationsCommand()
        assert cmd.name == "learning recommendations"

    def test_learning_recommendations_command_with_agent(self):
        """Test LearningRecommendationsCommand with agent argument."""
        cmd = LearningRecommendationsCommand()
        mock_orch = MagicMock()
        mock_orch.library_manager.learning.get_recommendations = MagicMock(
            return_value=[
                {
                    "recommendation_id": "rec1",
                    "title": "Optimize queries",
                    "confidence": 0.85,
                    "impact": "high"
                }
            ]
        )

        result = cmd.execute(["test_agent"], {"orchestrator": mock_orch})
        assert result["status"] == "success"
        assert len(result["data"]["recommendations"]) == 1
        assert result["data"]["recommendations"][0]["confidence"] == 0.85

    def test_learning_recommendations_command_no_recommendations(self):
        """Test LearningRecommendationsCommand with no recommendations."""
        cmd = LearningRecommendationsCommand()
        mock_orch = MagicMock()
        mock_orch.library_manager.learning.get_recommendations = MagicMock(
            return_value=[]
        )

        result = cmd.execute(["test_agent"], {"orchestrator": mock_orch})
        assert result["status"] == "success"
        assert result["data"]["recommendations"] == []


@pytest.mark.unit
class TestAnalyzerCommandsUnit:
    """Unit tests for analyzer commands."""

    def test_analyze_code_command_name(self):
        """Test AnalyzeCodeCommand has correct name."""
        cmd = AnalyzeCodeCommand()
        assert cmd.name == "analyze code"

    def test_analyze_code_command_description(self):
        """Test AnalyzeCodeCommand has appropriate description."""
        cmd = AnalyzeCodeCommand()
        assert "quality" in cmd.description.lower()
        assert "code" in cmd.description.lower()

    def test_analyze_code_command_fails_without_analyzer(self):
        """Test AnalyzeCodeCommand fails without analyzer library."""
        cmd = AnalyzeCodeCommand()
        mock_orch = MagicMock()
        mock_orch.library_manager.analyzer = None

        result = cmd.execute([], {"orchestrator": mock_orch})
        assert result["status"] == "error"



@pytest.mark.unit
class TestDocsGenerationCommandsUnit:
    """Unit tests for documentation generation commands."""

    def test_generate_readme_command_name(self):
        """Test GenerateReadmeCommand has correct name."""
        cmd = GenerateReadmeCommand()
        assert cmd.name == "docs generate readme"

    def test_generate_readme_command_description(self):
        """Test GenerateReadmeCommand has appropriate description."""
        cmd = GenerateReadmeCommand()
        assert "readme" in cmd.description.lower()
        assert "generate" in cmd.description.lower()

    def test_generate_readme_command_fails_without_docs(self):
        """Test GenerateReadmeCommand fails without docs library."""
        cmd = GenerateReadmeCommand()
        mock_orch = MagicMock()
        mock_orch.library_manager.docs = None

        result = cmd.execute([], {"orchestrator": mock_orch})
        assert result["status"] == "error"


@pytest.mark.unit
class TestCommandErrorHandling:
    """Unit tests for command error handling."""

    def test_command_error_message_included(self):
        """Test command includes error message in response."""
        cmd = SecurityStatusCommand()
        result = cmd.execute([], {})
        assert "message" in result
        assert isinstance(result["message"], str)
        assert len(result["message"]) > 0

    def test_command_status_flag_present(self):
        """Test command includes status flag in all responses."""
        commands = [
            SecurityStatusCommand(),
            PerformanceStatusCommand(),
            LearningRecommendationsCommand(),
            AnalyzeCodeCommand(),
            GenerateReadmeCommand(),
        ]

        for cmd in commands:
            result = cmd.execute([], {})
            assert "status" in result
            assert isinstance(result["status"], str)
            assert result["status"] in ["success", "error"]

    def test_command_data_field_when_success(self):
        """Test command includes data field when successful."""
        cmd = SecurityStatusCommand()
        mock_orch = MagicMock()
        mock_orch.database.get_security_incidents = MagicMock(return_value=[])

        result = cmd.execute([], {"orchestrator": mock_orch})
        if result["status"] == "success":
            assert "data" in result


@pytest.mark.unit
class TestCommandConsistency:
    """Unit tests for command consistency."""

    def test_all_commands_return_dict(self):
        """Test all commands return dict response."""
        commands = [
            ConflictAnalyzeCommand(),
            WorkflowCreateCommand(),
            SecurityStatusCommand(),
            PerformanceStatusCommand(),
            LearningRecommendationsCommand(),
            AnalyzeCodeCommand(),
            GenerateReadmeCommand(),
        ]

        for cmd in commands:
            result = cmd.execute([], {})
            assert isinstance(result, dict), f"{cmd.name} did not return dict"

    def test_all_commands_have_names(self):
        """Test all commands have name attribute."""
        commands = [
            ConflictAnalyzeCommand(),
            WorkflowCreateCommand(),
            SecurityStatusCommand(),
            PerformanceStatusCommand(),
            LearningRecommendationsCommand(),
            AnalyzeCodeCommand(),
            GenerateReadmeCommand(),
        ]

        for cmd in commands:
            assert hasattr(cmd, 'name')
            assert isinstance(cmd.name, str)
            assert len(cmd.name) > 0

    def test_all_commands_have_descriptions(self):
        """Test all commands have description attribute."""
        commands = [
            ConflictAnalyzeCommand(),
            WorkflowCreateCommand(),
            SecurityStatusCommand(),
            PerformanceStatusCommand(),
            LearningRecommendationsCommand(),
            AnalyzeCodeCommand(),
            GenerateReadmeCommand(),
        ]

        for cmd in commands:
            assert hasattr(cmd, 'description')
            assert isinstance(cmd.description, str)
            assert len(cmd.description) > 0

    def test_command_names_are_unique(self):
        """Test all command names are unique."""
        commands = [
            ConflictAnalyzeCommand(),
            WorkflowCreateCommand(),
            SecurityStatusCommand(),
            PerformanceStatusCommand(),
            LearningRecommendationsCommand(),
            AnalyzeCodeCommand(),
            GenerateReadmeCommand(),
        ]

        names = [cmd.name for cmd in commands]
        assert len(names) == len(set(names)), "Duplicate command names found"
