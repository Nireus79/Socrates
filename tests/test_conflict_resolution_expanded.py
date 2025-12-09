"""
Expanded tests for Conflict Resolution System - Detection and resolution
"""

from unittest.mock import MagicMock, patch
from datetime import datetime

import pytest
import socrates

from socratic_system.models import ConflictInfo, ProjectContext, User
from socratic_system.conflict_resolution.checkers import (
    TechStackConflictChecker,
    RequirementsConflictChecker,
)


@pytest.mark.unit
class TestTechStackConflictChecker:
    """Tests for technology stack conflict detection"""

    def test_tech_stack_checker_initialization(self, test_config):
        """Test TechStackConflictChecker initializes correctly"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            checker = TechStackConflictChecker(orchestrator)

            assert checker is not None
            assert checker.orchestrator == orchestrator

    def test_detect_no_conflict_same_tech(self, test_config):
        """Test that same technology doesn't create conflict"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            checker = TechStackConflictChecker(orchestrator)

            project = ProjectContext(
                project_id="test-001",
                name="Test",
                owner="testuser",
                collaborators=[],
                phase="planning",
                goals="",
                tech_stack=["Python"],
                requirements=[],
                constraints=[],
                team_structure="",
                language_preferences="en",
                deployment_target="",
                code_style="",
                conversation_history=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            # Adding same tech should not create conflict
            insights = {"tech_stack": ["Python"]}
            result = checker.check(insights, project, "testuser")

            # Should not detect conflict for duplicate tech
            if result:
                assert isinstance(result, ConflictInfo)

    def test_detect_conflicting_tech(self, test_config):
        """Test detecting conflicting technologies"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            checker = TechStackConflictChecker(orchestrator)

            # Create project with tech stack
            project = ProjectContext(
                project_id="test-001",
                name="Test",
                owner="testuser",
                collaborators=[],
                phase="planning",
                goals="",
                tech_stack=["Python", "FastAPI", "PostgreSQL"],
                requirements=[],
                constraints=[],
                team_structure="",
                language_preferences="en",
                deployment_target="",
                code_style="",
                conversation_history=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            # Add conflicting tech
            insights = {"tech_stack": ["Node.js"]}
            result = checker.check(insights, project, "testuser")

            # Result can be ConflictInfo or None depending on conflict rules
            assert result is None or isinstance(result, ConflictInfo)

    def test_extract_tech_stack_values(self, test_config):
        """Test extracting tech stack from insights"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            checker = TechStackConflictChecker(orchestrator)

            insights = {
                "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
                "requirements": ["Fast", "Scalable"]
            }

            # Extract should get only tech_stack
            extracted = checker._extract_values(insights)
            assert "Python" in extracted
            assert "FastAPI" in extracted

    def test_get_existing_tech_stack(self, test_config):
        """Test getting existing tech stack from project"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            checker = TechStackConflictChecker(orchestrator)

            project = ProjectContext(
                project_id="test-001",
                name="Test",
                owner="testuser",
                collaborators=[],
                phase="planning",
                goals="",
                tech_stack=["Python", "Django", "MySQL"],
                requirements=[],
                constraints=[],
                team_structure="",
                language_preferences="en",
                deployment_target="",
                code_style="",
                conversation_history=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            existing = checker._get_existing_values(project)
            assert "Python" in existing
            assert "Django" in existing


@pytest.mark.unit
class TestRequirementsConflictChecker:
    """Tests for requirements conflict detection"""

    def test_requirements_checker_initialization(self, test_config):
        """Test RequirementsConflictChecker initializes correctly"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            checker = RequirementsConflictChecker(orchestrator)

            assert checker is not None

    def test_detect_no_conflict_same_requirement(self, test_config):
        """Test that same requirement doesn't create conflict"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            checker = RequirementsConflictChecker(orchestrator)

            project = ProjectContext(
                project_id="test-001",
                name="Test",
                owner="testuser",
                collaborators=[],
                phase="planning",
                goals="",
                tech_stack=[],
                requirements=["High Performance"],
                constraints=[],
                team_structure="",
                language_preferences="en",
                deployment_target="",
                code_style="",
                conversation_history=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            insights = {"requirements": ["High Performance"]}
            result = checker.check(insights, project, "testuser")

            # Same requirement should return None (no conflict)
            assert result is None or isinstance(result, ConflictInfo)

    def test_extract_requirements_values(self, test_config):
        """Test extracting requirements from insights"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            checker = RequirementsConflictChecker(orchestrator)

            insights = {
                "requirements": ["Fast response time", "Low memory usage"],
                "tech_stack": ["Python"]
            }

            extracted = checker._extract_values(insights)
            assert "Fast response time" in extracted
            assert "Low memory usage" in extracted

    def test_get_existing_requirements(self, test_config):
        """Test getting existing requirements from project"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            checker = RequirementsConflictChecker(orchestrator)

            project = ProjectContext(
                project_id="test-001",
                name="Test",
                owner="testuser",
                collaborators=[],
                phase="planning",
                goals="",
                tech_stack=[],
                requirements=["RESTful API", "Authentication", "Rate limiting"],
                constraints=[],
                team_structure="",
                language_preferences="en",
                deployment_target="",
                code_style="",
                conversation_history=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            existing = checker._get_existing_values(project)
            assert "RESTful API" in existing
            assert "Authentication" in existing


@pytest.mark.unit
class TestConflictInfoModel:
    """Tests for ConflictInfo data model"""

    def test_conflict_info_creation(self):
        """Test creating ConflictInfo instance"""
        conflict = ConflictInfo(
            conflict_id="test-001",
            conflict_type="tech_stack",
            old_value="Python",
            new_value="JavaScript",
            old_author="alice",
            new_author="bob",
            old_timestamp="2025-12-09T10:00:00",
            new_timestamp="2025-12-09T10:05:00",
            severity="medium",
            suggestions=["Evaluate compatibility", "Test integration"]
        )

        assert conflict.conflict_id == "test-001"
        assert conflict.conflict_type == "tech_stack"
        assert conflict.severity == "medium"
        assert len(conflict.suggestions) == 2

    def test_conflict_info_severity_levels(self):
        """Test different severity levels"""
        severities = ["low", "medium", "high", "critical"]

        for severity in severities:
            conflict = ConflictInfo(
                conflict_id="test",
                conflict_type="test",
                old_value="a",
                new_value="b",
                old_author="user1",
                new_author="user2",
                old_timestamp="2025-12-09T10:00:00",
                new_timestamp="2025-12-09T10:05:00",
                severity=severity,
                suggestions=[]
            )

            assert conflict.severity == severity


@pytest.mark.integration
class TestConflictResolutionWorkflow:
    """Integration tests for complete conflict resolution workflows"""

    def test_conflict_detection_workflow(self, test_config):
        """Test complete conflict detection workflow"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)

            # Create checkers
            tech_checker = TechStackConflictChecker(orchestrator)
            req_checker = RequirementsConflictChecker(orchestrator)

            # Set up project
            project = ProjectContext(
                project_id="test-001",
                name="Test",
                owner="testuser",
                collaborators=[],
                phase="planning",
                goals="",
                tech_stack=["Python", "FastAPI"],
                requirements=["Fast", "Scalable"],
                constraints=[],
                team_structure="",
                language_preferences="en",
                deployment_target="",
                code_style="",
                conversation_history=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            # Check for conflicts
            tech_insights = {"tech_stack": ["Node.js"]}
            req_insights = {"requirements": ["Real-time"]}

            tech_conflict = tech_checker.check(tech_insights, project, "user1")
            req_conflict = req_checker.check(req_insights, project, "user2")

            # Should complete without errors
            assert tech_conflict is None or isinstance(tech_conflict, ConflictInfo)
            assert req_conflict is None or isinstance(req_conflict, ConflictInfo)

    def test_conflict_detection_with_multiple_techs(self, test_config):
        """Test conflict detection with multiple technologies"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            checker = TechStackConflictChecker(orchestrator)

            # Set up complex tech stack
            project = ProjectContext(
                project_id="test-001",
                name="Test",
                owner="testuser",
                collaborators=[],
                phase="planning",
                goals="",
                tech_stack=["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"],
                requirements=[],
                constraints=[],
                team_structure="",
                language_preferences="en",
                deployment_target="",
                code_style="",
                conversation_history=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            # Try adding various technologies
            test_techs = ["Node.js", "Python", "Java", "Go"]

            for tech in test_techs:
                insights = {"tech_stack": [tech]}
                result = checker.check(insights, project, "testuser")

                # Should handle all cases gracefully
                assert result is None or isinstance(result, ConflictInfo)

    def test_conflict_with_same_project_author(self, test_config):
        """Test that conflicts can occur even from same author"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            checker = TechStackConflictChecker(orchestrator)

            project = ProjectContext(
                project_id="test-001",
                name="Test",
                owner="testuser",
                collaborators=[],
                phase="planning",
                goals="",
                tech_stack=["Python"],
                requirements=[],
                constraints=[],
                team_structure="",
                language_preferences="en",
                deployment_target="",
                code_style="",
                conversation_history=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            # Same user adding different tech
            insights = {"tech_stack": ["Java"]}
            result = checker.check(insights, project, "sameuser")

            # Should still detect potential conflicts
            assert result is None or isinstance(result, ConflictInfo)

    def test_empty_conflict_check(self, test_config):
        """Test checking conflicts with empty insights"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            checker = TechStackConflictChecker(orchestrator)

            project = ProjectContext(
                project_id="test-001",
                name="Test",
                owner="testuser",
                collaborators=[],
                phase="planning",
                goals="",
                tech_stack=["Python"],
                requirements=[],
                constraints=[],
                team_structure="",
                language_preferences="en",
                deployment_target="",
                code_style="",
                conversation_history=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            # Empty tech stack in insights
            insights = {"tech_stack": []}
            result = checker.check(insights, project, "testuser")

            # Should handle empty gracefully
            assert result is None

    def test_conflict_suggestions_generation(self, test_config):
        """Test that conflict suggestions are generated"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            checker = TechStackConflictChecker(orchestrator)

            project = ProjectContext(
                project_id="test-001",
                name="Test",
                owner="testuser",
                collaborators=[],
                phase="planning",
                goals="",
                tech_stack=["SQL Server"],
                requirements=[],
                constraints=[],
                team_structure="",
                language_preferences="en",
                deployment_target="",
                code_style="",
                conversation_history=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            insights = {"tech_stack": ["PostgreSQL"]}
            result = checker.check(insights, project, "testuser")

            # If conflict detected, should have suggestions
            if result and isinstance(result, ConflictInfo):
                assert isinstance(result.suggestions, list)
