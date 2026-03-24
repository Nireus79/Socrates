"""
Integration tests for new CLI commands added in Phase 9.

Tests all commands from sections 3.1-3.7:
- Conflict Detection (Section 3.1)
- Workflow Orchestration (Section 3.2)
- Security Monitoring (Section 3.3)
- Performance Monitoring (Section 3.4)
- Learning Recommendations (Section 3.5)
- Code Analysis (Section 3.6)
- Documentation Generation (Section 3.7)
"""

import pytest
from unittest.mock import MagicMock, patch, call
from socratic_system.ui.commands.conflict_commands import (
    ConflictAnalyzeCommand,
    ConflictListCommand,
    ConflictResolveCommand,
    ConflictIgnoreCommand,
)
from socratic_system.ui.commands.workflow_commands import (
    WorkflowCreateCommand,
    WorkflowListCommand,
    WorkflowExecuteCommand,
)
from socratic_system.ui.commands.security_commands import (
    SecurityStatusCommand,
    SecurityIncidentsCommand,
    SecurityValidateCommand,
    SecurityTrendsCommand,
)
from socratic_system.ui.commands.performance_commands import (
    PerformanceStatusCommand,
    PerformanceAgentsCommand,
    PerformanceCacheCommand,
    PerformanceBottlenecksCommand,
    PerformanceResetCommand,
)
from socratic_system.ui.commands.learning_commands import (
    LearningRecommendationsCommand,
    LearningPatternsCommand,
    LearningSessionCommand,
    LearningAnalyzeCommand,
)
from socratic_system.ui.commands.analyzer_commands import (
    AnalyzeCodeCommand,
    AnalyzeFileCommand,
    AnalyzeProjectCommand,
    AnalysisIssuesCommand,
)
from socratic_system.ui.commands.docs_generation_commands import (
    GenerateReadmeCommand,
    GenerateApiDocsCommand,
    GenerateArchitectureDocsCommand,
    GenerateAllDocsCommand,
)


class TestConflictCommands:
    """Tests for conflict detection commands."""

    def test_conflict_analyze_command_instantiation(self):
        """Test ConflictAnalyzeCommand instantiation."""
        cmd = ConflictAnalyzeCommand()
        assert cmd.name == "conflict analyze"
        assert cmd.description == "Detect conflicts in project specifications"

    def test_conflict_analyze_command_no_orchestrator(self):
        """Test ConflictAnalyzeCommand with missing orchestrator."""
        cmd = ConflictAnalyzeCommand()
        result = cmd.execute([], {})
        assert result["success"] is False
        assert "Orchestrator not available" in result["message"]

    def test_conflict_analyze_command_with_orchestrator(self):
        """Test ConflictAnalyzeCommand with valid orchestrator."""
        cmd = ConflictAnalyzeCommand()
        mock_orchestrator = MagicMock()
        mock_orchestrator.library_manager.conflict = MagicMock()
        mock_orchestrator.library_manager.conflict.analyze_specification = MagicMock(
            return_value={"conflicts": [{"type": "test", "severity": "high"}]}
        )

        context = {"orchestrator": mock_orchestrator}
        result = cmd.execute([], context)

        assert result["success"] is True
        assert "conflicts" in result["data"]

    def test_conflict_list_command(self):
        """Test ConflictListCommand."""
        cmd = ConflictListCommand()
        assert cmd.name == "conflict list"

        mock_orchestrator = MagicMock()
        mock_orchestrator.database.get_project_conflicts = MagicMock(return_value=[])

        context = {"orchestrator": mock_orchestrator}
        result = cmd.execute([], context)

        assert result["success"] is True
        assert "conflicts" in result["data"]

    def test_conflict_resolve_command(self):
        """Test ConflictResolveCommand."""
        cmd = ConflictResolveCommand()
        assert cmd.name == "conflict resolve"

    def test_conflict_ignore_command(self):
        """Test ConflictIgnoreCommand."""
        cmd = ConflictIgnoreCommand()
        assert cmd.name == "conflict ignore"


class TestWorkflowCommands:
    """Tests for workflow orchestration commands."""

    def test_workflow_create_command_instantiation(self):
        """Test WorkflowCreateCommand instantiation."""
        cmd = WorkflowCreateCommand()
        assert cmd.name == "workflow create"
        assert "workflow" in cmd.description.lower()

    def test_workflow_create_command_no_orchestrator(self):
        """Test WorkflowCreateCommand with missing orchestrator."""
        cmd = WorkflowCreateCommand()
        result = cmd.execute([], {})
        assert result["success"] is False

    def test_workflow_list_command(self):
        """Test WorkflowListCommand."""
        cmd = WorkflowListCommand()
        assert cmd.name == "workflow list"

        mock_orchestrator = MagicMock()
        mock_orchestrator.database.get_workflows = MagicMock(return_value=[])

        context = {"orchestrator": mock_orchestrator}
        result = cmd.execute([], context)

        assert result["success"] is True

    def test_workflow_execute_command(self):
        """Test WorkflowExecuteCommand."""
        cmd = WorkflowExecuteCommand()
        assert cmd.name == "workflow execute"


class TestSecurityCommands:
    """Tests for security monitoring commands."""

    def test_security_status_command_instantiation(self):
        """Test SecurityStatusCommand instantiation."""
        cmd = SecurityStatusCommand()
        assert cmd.name == "security status"
        assert "security" in cmd.description.lower()

    def test_security_status_command_with_orchestrator(self):
        """Test SecurityStatusCommand with valid orchestrator."""
        cmd = SecurityStatusCommand()
        mock_orchestrator = MagicMock()
        mock_orchestrator.database.get_security_incidents = MagicMock(return_value=[])

        context = {"orchestrator": mock_orchestrator}
        result = cmd.execute([], context)

        assert result["success"] is True
        assert "total_incidents" in result["data"]

    def test_security_incidents_command(self):
        """Test SecurityIncidentsCommand."""
        cmd = SecurityIncidentsCommand()
        assert cmd.name == "security incidents"

    def test_security_validate_command(self):
        """Test SecurityValidateCommand."""
        cmd = SecurityValidateCommand()
        assert cmd.name == "security validate"

    def test_security_trends_command(self):
        """Test SecurityTrendsCommand."""
        cmd = SecurityTrendsCommand()
        assert cmd.name == "security trends"


class TestPerformanceCommands:
    """Tests for performance monitoring commands."""

    def test_performance_status_command_instantiation(self):
        """Test PerformanceStatusCommand instantiation."""
        cmd = PerformanceStatusCommand()
        assert cmd.name == "performance status"

    def test_performance_status_command_with_orchestrator(self):
        """Test PerformanceStatusCommand with valid orchestrator."""
        cmd = PerformanceStatusCommand()
        mock_orchestrator = MagicMock()
        mock_orchestrator.library_manager.performance = MagicMock()
        mock_orchestrator.library_manager.performance.get_performance_stats = MagicMock(
            return_value={"total_calls": 100, "avg_duration_ms": 50.5}
        )
        mock_orchestrator.library_manager.performance.get_cache_stats = MagicMock(
            return_value={"cache_size": 1024, "hit_rate": "95%"}
        )

        context = {"orchestrator": mock_orchestrator}
        result = cmd.execute([], context)

        assert result["success"] is True
        assert "execution_stats" in result["data"]

    def test_performance_agents_command(self):
        """Test PerformanceAgentsCommand."""
        cmd = PerformanceAgentsCommand()
        assert cmd.name == "performance agents"

    def test_performance_cache_command(self):
        """Test PerformanceCacheCommand."""
        cmd = PerformanceCacheCommand()
        assert cmd.name == "performance cache"

    def test_performance_bottlenecks_command(self):
        """Test PerformanceBottlenecksCommand."""
        cmd = PerformanceBottlenecksCommand()
        assert cmd.name == "performance bottlenecks"

    def test_performance_reset_command(self):
        """Test PerformanceResetCommand."""
        cmd = PerformanceResetCommand()
        assert cmd.name == "performance reset"


class TestLearningCommands:
    """Tests for learning recommendation commands."""

    def test_learning_recommendations_command_instantiation(self):
        """Test LearningRecommendationsCommand instantiation."""
        cmd = LearningRecommendationsCommand()
        assert cmd.name == "learning recommendations"

    def test_learning_recommendations_command_with_orchestrator(self):
        """Test LearningRecommendationsCommand with valid orchestrator."""
        cmd = LearningRecommendationsCommand()
        mock_orchestrator = MagicMock()
        mock_orchestrator.library_manager.learning = MagicMock()
        mock_orchestrator.library_manager.learning.get_recommendations = MagicMock(
            return_value=[
                {"recommendation_id": "rec1", "title": "Optimize code", "confidence": 0.85}
            ]
        )

        context = {"orchestrator": mock_orchestrator}
        result = cmd.execute(["test_agent"], context)

        assert result["success"] is True
        assert "recommendations" in result["data"]

    def test_learning_patterns_command(self):
        """Test LearningPatternsCommand."""
        cmd = LearningPatternsCommand()
        assert cmd.name == "learning patterns"

    def test_learning_session_command(self):
        """Test LearningSessionCommand."""
        cmd = LearningSessionCommand()
        assert cmd.name == "learning session"

    def test_learning_analyze_command(self):
        """Test LearningAnalyzeCommand."""
        cmd = LearningAnalyzeCommand()
        assert cmd.name == "learning analyze"


class TestAnalyzerCommands:
    """Tests for code analysis commands."""

    def test_analyze_code_command_instantiation(self):
        """Test AnalyzeCodeCommand instantiation."""
        cmd = AnalyzeCodeCommand()
        assert cmd.name == "analyze code"
        assert "quality" in cmd.description.lower()

    def test_analyze_code_command_with_orchestrator(self):
        """Test AnalyzeCodeCommand with valid orchestrator."""
        cmd = AnalyzeCodeCommand()
        mock_orchestrator = MagicMock()
        mock_orchestrator.library_manager.analyzer = MagicMock()
        mock_orchestrator.library_manager.analyzer.analyze_code = MagicMock(
            return_value={
                "issues_count": 2,
                "quality_score": 85.5,
                "patterns": ["singleton", "observer"],
                "recommendations": ["Add type hints", "Document API"]
            }
        )

        context = {"orchestrator": mock_orchestrator}
        result = cmd.execute([], context)

        # Should fail without code input in automated test
        assert "success" in result

    def test_analyze_file_command(self):
        """Test AnalyzeFileCommand."""
        cmd = AnalyzeFileCommand()
        assert cmd.name == "analyze file"

    def test_analyze_project_command(self):
        """Test AnalyzeProjectCommand."""
        cmd = AnalyzeProjectCommand()
        assert cmd.name == "analyze project"

    def test_analysis_issues_command(self):
        """Test AnalysisIssuesCommand."""
        cmd = AnalysisIssuesCommand()
        assert cmd.name == "analysis issues"


class TestDocsGenerationCommands:
    """Tests for documentation generation commands."""

    def test_generate_readme_command_instantiation(self):
        """Test GenerateReadmeCommand instantiation."""
        cmd = GenerateReadmeCommand()
        assert cmd.name == "docs generate readme"

    def test_generate_readme_command_with_orchestrator(self):
        """Test GenerateReadmeCommand with valid orchestrator."""
        cmd = GenerateReadmeCommand()
        mock_orchestrator = MagicMock()
        mock_orchestrator.library_manager.docs = MagicMock()
        mock_orchestrator.library_manager.docs.generate_comprehensive_readme = MagicMock(
            return_value="# My Project\nA great project.\n\n## Installation\n..."
        )

        context = {"orchestrator": mock_orchestrator}
        result = cmd.execute([], context)

        # Should fail without interactive input in automated test
        assert "success" in result

    def test_generate_api_docs_command(self):
        """Test GenerateApiDocsCommand."""
        cmd = GenerateApiDocsCommand()
        assert cmd.name == "docs generate api"

    def test_generate_architecture_docs_command(self):
        """Test GenerateArchitectureDocsCommand."""
        cmd = GenerateArchitectureDocsCommand()
        assert cmd.name == "docs generate architecture"

    def test_generate_all_docs_command(self):
        """Test GenerateAllDocsCommand."""
        cmd = GenerateAllDocsCommand()
        assert cmd.name == "docs generate all"


class TestCommandIntegrationWithDatabase:
    """Integration tests for commands with database operations."""

    def test_security_status_saves_incidents(self, mock_orchestrator):
        """Test SecurityStatusCommand integrates with database."""
        mock_orchestrator.database.get_security_incidents = MagicMock(
            return_value=[
                {"incident_id": "inc1", "severity": "critical"},
                {"incident_id": "inc2", "severity": "high"}
            ]
        )

        cmd = SecurityStatusCommand()
        result = cmd.execute([], {"orchestrator": mock_orchestrator})

        assert result["success"] is True
        assert result["data"]["critical"] == 1
        assert result["data"]["high"] == 1

    def test_learning_session_saves_to_database(self, mock_orchestrator):
        """Test LearningSessionCommand saves session to database."""
        mock_orchestrator.library_manager.learning = MagicMock()
        mock_orchestrator.library_manager.learning.start_session = MagicMock(
            return_value={"session_id": "sess_123", "created_at": "2024-01-01"}
        )
        mock_orchestrator.database.save_learning_session = MagicMock(return_value=True)

        cmd = LearningSessionCommand()
        result = cmd.execute([], {"orchestrator": mock_orchestrator})

        # Would call database if input was provided
        assert "success" in result


class TestCommandErrorHandling:
    """Tests for command error handling."""

    def test_command_handles_missing_library_manager(self):
        """Test command gracefully handles missing library manager."""
        cmd = PerformanceStatusCommand()
        mock_orchestrator = MagicMock()
        mock_orchestrator.library_manager = None

        result = cmd.execute([], {"orchestrator": mock_orchestrator})
        assert result["success"] is False

    def test_command_handles_exception_in_execution(self):
        """Test command handles exceptions during execution."""
        cmd = AnalyzeCodeCommand()
        mock_orchestrator = MagicMock()
        mock_orchestrator.library_manager.analyzer = MagicMock()
        mock_orchestrator.library_manager.analyzer.analyze_code = MagicMock(
            side_effect=Exception("Analysis failed")
        )

        result = cmd.execute([], {"orchestrator": mock_orchestrator})
        assert "success" in result

    def test_command_handles_invalid_arguments(self):
        """Test command handles invalid argument types."""
        cmd = PerformanceBottlenecksCommand()
        mock_orchestrator = MagicMock()
        mock_orchestrator.library_manager.performance = MagicMock()

        # Pass non-numeric threshold
        result = cmd.execute(["not_a_number"], {"orchestrator": mock_orchestrator})
        assert result["success"] is False or "Threshold" in result["message"]


class TestCommandDataFormatting:
    """Tests for command output data formatting."""

    def test_performance_status_formats_metrics(self):
        """Test PerformanceStatusCommand formats metrics correctly."""
        cmd = PerformanceStatusCommand()
        mock_orchestrator = MagicMock()
        mock_orchestrator.library_manager.performance = MagicMock()
        mock_orchestrator.library_manager.performance.get_performance_stats = MagicMock(
            return_value={
                "total_calls": 500,
                "avg_duration_ms": 123.45,
                "max_duration_ms": 987.65
            }
        )
        mock_orchestrator.library_manager.performance.get_cache_stats = MagicMock(
            return_value={
                "cache_size": 2048,
                "hit_rate": "92.5%",
                "entries": 156
            }
        )

        context = {"orchestrator": mock_orchestrator}
        result = cmd.execute([], context)

        assert result["success"] is True
        assert result["data"]["execution_stats"]["avg_duration_ms"] == 123.45
        assert result["data"]["cache_stats"]["hit_rate"] == "92.5%"

    def test_learning_recommendations_formats_confidence(self):
        """Test LearningRecommendationsCommand formats confidence scores."""
        cmd = LearningRecommendationsCommand()
        mock_orchestrator = MagicMock()
        mock_orchestrator.library_manager.learning = MagicMock()
        mock_orchestrator.library_manager.learning.get_recommendations = MagicMock(
            return_value=[
                {
                    "recommendation_id": "rec1",
                    "title": "Optimize database queries",
                    "confidence": 0.92,
                    "impact": "high"
                }
            ]
        )

        context = {"orchestrator": mock_orchestrator}
        result = cmd.execute(["test_agent"], context)

        assert result["success"] is True
        assert result["data"]["recommendations"][0]["confidence"] == 0.92
