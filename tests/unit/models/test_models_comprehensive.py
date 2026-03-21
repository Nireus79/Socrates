"""
Comprehensive tests for socratic_system models.

Tests all dataclasses and enums to ensure proper serialization,
validation, and behavior.
"""

import datetime
from typing import List

import pytest

from socratic_system.models.project import ProjectContext, ProjectPhase, AccessControl
from socratic_system.models.user import User, SubscriptionTier
from socratic_system.models.workflow import Workflow, WorkflowDefinition, WorkflowState
from socratic_system.models.role import Role
from socratic_system.models.llm_provider import LLMProvider


class TestProjectPhaseEnum:
    """Tests for ProjectPhase enum."""

    def test_project_phase_values(self):
        """Test all ProjectPhase enum values exist."""
        assert ProjectPhase.PLANNING.value in ['planning', 'PLANNING']
        assert ProjectPhase.DESIGN.value in ['design', 'DESIGN']
        assert ProjectPhase.DEVELOPMENT.value in ['development', 'DEVELOPMENT']
        assert ProjectPhase.TESTING.value in ['testing', 'TESTING']
        assert ProjectPhase.DEPLOYMENT.value in ['deployment', 'DEPLOYMENT']
        assert ProjectPhase.MAINTENANCE.value in ['maintenance', 'MAINTENANCE']

    def test_project_phase_comparison(self):
        """Test ProjectPhase enum comparison."""
        assert ProjectPhase.PLANNING == ProjectPhase.PLANNING
        assert ProjectPhase.PLANNING != ProjectPhase.DESIGN


class TestAccessControl:
    """Tests for AccessControl dataclass."""

    def test_access_control_creation(self):
        """Test creating AccessControl instance."""
        ac = AccessControl(
            owner="user123",
            collaborators=["user456", "user789"],
            is_public=False
        )
        assert ac.owner == "user123"
        assert "user456" in ac.collaborators
        assert ac.is_public is False

    def test_access_control_empty_collaborators(self):
        """Test AccessControl with no collaborators."""
        ac = AccessControl(owner="user123", collaborators=[], is_public=True)
        assert ac.owner == "user123"
        assert len(ac.collaborators) == 0
        assert ac.is_public is True

    def test_access_control_with_many_collaborators(self):
        """Test AccessControl with multiple collaborators."""
        collaborators = [f"user{i}" for i in range(10)]
        ac = AccessControl(owner="owner", collaborators=collaborators)
        assert len(ac.collaborators) == 10


class TestProjectContext:
    """Tests for ProjectContext dataclass."""

    def test_project_context_creation(self):
        """Test creating a complete ProjectContext."""
        now = datetime.datetime.now()
        project = ProjectContext(
            project_id="proj-123",
            name="Test Project",
            owner="user123",
            collaborators=["user456"],
            goals="Build amazing software",
            requirements=["Requirement 1", "Requirement 2"],
            tech_stack=["Python", "FastAPI"],
            constraints=["Budget limit: $10k"],
            team_structure="distributed",
            language_preferences="Python",
            deployment_target="cloud",
            code_style="Google",
            phase=ProjectPhase.DEVELOPMENT,
            conversation_history=[],
            created_at=now,
            updated_at=now,
            access_control=AccessControl(owner="user123", collaborators=[])
        )

        assert project.project_id == "proj-123"
        assert project.name == "Test Project"
        assert project.owner == "user123"
        assert project.phase == ProjectPhase.DEVELOPMENT
        assert project.created_at == now

    def test_project_context_minimal(self):
        """Test ProjectContext with minimal required fields."""
        now = datetime.datetime.now()
        project = ProjectContext(
            project_id="proj-456",
            name="Minimal Project",
            owner="user789",
            collaborators=[],
            goals="",
            requirements=[],
            tech_stack=[],
            constraints=[],
            team_structure="",
            language_preferences="",
            deployment_target="",
            code_style="",
            phase=ProjectPhase.PLANNING,
            conversation_history=[],
            created_at=now,
            updated_at=now
        )

        assert project.project_id == "proj-456"
        assert len(project.collaborators) == 0
        assert len(project.requirements) == 0

    def test_project_context_phase_transitions(self):
        """Test ProjectContext with different phases."""
        now = datetime.datetime.now()

        for phase in [ProjectPhase.PLANNING, ProjectPhase.DESIGN, ProjectPhase.DEVELOPMENT]:
            project = ProjectContext(
                project_id="proj-test",
                name="Phase Test",
                owner="user",
                collaborators=[],
                goals="",
                requirements=[],
                tech_stack=[],
                constraints=[],
                team_structure="",
                language_preferences="",
                deployment_target="",
                code_style="",
                phase=phase,
                conversation_history=[],
                created_at=now,
                updated_at=now
            )
            assert project.phase == phase

    def test_project_context_conversation_history(self):
        """Test ProjectContext with conversation history."""
        now = datetime.datetime.now()
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]

        project = ProjectContext(
            project_id="proj-conv",
            name="Conv Project",
            owner="user",
            collaborators=[],
            goals="",
            requirements=[],
            tech_stack=[],
            constraints=[],
            team_structure="",
            language_preferences="",
            deployment_target="",
            code_style="",
            phase=ProjectPhase.PLANNING,
            conversation_history=history,
            created_at=now,
            updated_at=now
        )

        assert len(project.conversation_history) == 2
        assert project.conversation_history[0]["role"] == "user"


class TestUser:
    """Tests for User dataclass."""

    def test_user_creation(self):
        """Test creating a User."""
        now = datetime.datetime.now()
        user = User(
            username="testuser",
            email="test@example.com",
            passcode_hash="hashed_password",
            created_at=now,
            projects=["proj1", "proj2"],
            subscription_tier=SubscriptionTier.PRO
        )

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.subscription_tier == SubscriptionTier.PRO
        assert len(user.projects) == 2

    def test_user_free_tier(self):
        """Test User with free subscription."""
        user = User(
            username="freeuser",
            email="free@example.com",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier=SubscriptionTier.FREE
        )

        assert user.subscription_tier == SubscriptionTier.FREE

    def test_user_enterprise_tier(self):
        """Test User with enterprise subscription."""
        user = User(
            username="enterprise",
            email="enterprise@example.com",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=["proj1", "proj2", "proj3"],
            subscription_tier=SubscriptionTier.ENTERPRISE
        )

        assert user.subscription_tier == SubscriptionTier.ENTERPRISE

    def test_user_empty_projects(self):
        """Test User with no projects."""
        user = User(
            username="noproject",
            email="np@example.com",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=[],
            subscription_tier=SubscriptionTier.FREE
        )

        assert len(user.projects) == 0


class TestSubscriptionTier:
    """Tests for SubscriptionTier enum."""

    def test_subscription_tier_values(self):
        """Test all SubscriptionTier enum values."""
        assert hasattr(SubscriptionTier, 'FREE')
        assert hasattr(SubscriptionTier, 'PRO')
        assert hasattr(SubscriptionTier, 'ENTERPRISE')

    def test_subscription_tier_comparison(self):
        """Test SubscriptionTier enum comparison."""
        assert SubscriptionTier.FREE == SubscriptionTier.FREE
        assert SubscriptionTier.FREE != SubscriptionTier.PRO


class TestWorkflow:
    """Tests for Workflow dataclass."""

    def test_workflow_creation(self):
        """Test creating a Workflow."""
        now = datetime.datetime.now()
        workflow = Workflow(
            workflow_id="wf-123",
            project_id="proj-123",
            name="Development Workflow",
            steps=["Step 1", "Step 2", "Step 3"],
            current_step=0,
            status="active",
            created_at=now,
            updated_at=now
        )

        assert workflow.workflow_id == "wf-123"
        assert workflow.project_id == "proj-123"
        assert len(workflow.steps) == 3
        assert workflow.current_step == 0

    def test_workflow_step_progression(self):
        """Test Workflow with different step indexes."""
        now = datetime.datetime.now()
        steps = ["Step 1", "Step 2", "Step 3"]

        for i in range(len(steps)):
            workflow = Workflow(
                workflow_id=f"wf-{i}",
                project_id="proj",
                name="Test",
                steps=steps,
                current_step=i,
                status="active",
                created_at=now,
                updated_at=now
            )
            assert workflow.current_step == i


class TestWorkflowDefinition:
    """Tests for WorkflowDefinition dataclass."""

    def test_workflow_definition_creation(self):
        """Test creating a WorkflowDefinition."""
        definition = WorkflowDefinition(
            workflow_type="planning",
            name="Planning Workflow",
            description="Workflow for planning phase",
            steps=["Analyze", "Design", "Plan"],
            required_inputs=["goals", "requirements"],
            outputs=["plan", "timeline"]
        )

        assert definition.workflow_type == "planning"
        assert len(definition.steps) == 3
        assert "goals" in definition.required_inputs


class TestWorkflowState:
    """Tests for WorkflowState enum."""

    def test_workflow_state_values(self):
        """Test all WorkflowState enum values."""
        assert hasattr(WorkflowState, 'PENDING')
        assert hasattr(WorkflowState, 'IN_PROGRESS')
        assert hasattr(WorkflowState, 'COMPLETED')
        assert hasattr(WorkflowState, 'FAILED')


class TestRole:
    """Tests for Role enum."""

    def test_role_values(self):
        """Test all Role enum values."""
        assert hasattr(Role, 'OWNER')
        assert hasattr(Role, 'EDITOR')
        assert hasattr(Role, 'VIEWER')

    def test_role_comparison(self):
        """Test Role enum comparison."""
        assert Role.OWNER == Role.OWNER
        assert Role.OWNER != Role.EDITOR


class TestLLMProvider:
    """Tests for LLMProvider dataclass."""

    def test_llm_provider_creation(self):
        """Test creating an LLMProvider."""
        provider = LLMProvider(
            name="OpenAI",
            model="gpt-4",
            api_key="sk-test",
            is_default=True,
            config={"temperature": 0.7, "max_tokens": 2000}
        )

        assert provider.name == "OpenAI"
        assert provider.model == "gpt-4"
        assert provider.is_default is True
        assert provider.config["temperature"] == 0.7

    def test_llm_provider_non_default(self):
        """Test creating non-default LLMProvider."""
        provider = LLMProvider(
            name="Anthropic",
            model="claude-3",
            api_key="sk-ant",
            is_default=False,
            config={}
        )

        assert provider.is_default is False

    def test_llm_provider_with_empty_config(self):
        """Test LLMProvider with empty config."""
        provider = LLMProvider(
            name="Test",
            model="test-model",
            api_key="key",
            is_default=False,
            config={}
        )

        assert len(provider.config) == 0


# Integration tests combining multiple models

class TestModelIntegration:
    """Tests for interactions between models."""

    def test_project_with_access_control(self):
        """Test ProjectContext with full AccessControl."""
        now = datetime.datetime.now()
        access = AccessControl(
            owner="owner",
            collaborators=["col1", "col2", "col3"],
            is_public=False
        )

        project = ProjectContext(
            project_id="proj-123",
            name="Collaborative Project",
            owner="owner",
            collaborators=["col1", "col2", "col3"],
            goals="Build together",
            requirements=[],
            tech_stack=[],
            constraints=[],
            team_structure="agile",
            language_preferences="Python",
            deployment_target="cloud",
            code_style="PEP8",
            phase=ProjectPhase.DEVELOPMENT,
            conversation_history=[],
            created_at=now,
            updated_at=now,
            access_control=access
        )

        assert project.access_control.owner == "owner"
        assert len(project.access_control.collaborators) == 3

    def test_user_with_multiple_projects(self):
        """Test User managing multiple projects."""
        user = User(
            username="poweruser",
            email="power@example.com",
            passcode_hash="hash",
            created_at=datetime.datetime.now(),
            projects=["proj1", "proj2", "proj3", "proj4", "proj5"],
            subscription_tier=SubscriptionTier.ENTERPRISE
        )

        assert len(user.projects) == 5
        assert user.subscription_tier == SubscriptionTier.ENTERPRISE

    def test_workflow_with_many_steps(self):
        """Test Workflow with complex step sequence."""
        now = datetime.datetime.now()
        steps = [f"Phase {i}" for i in range(10)]

        workflow = Workflow(
            workflow_id="complex-wf",
            project_id="proj",
            name="Complex Workflow",
            steps=steps,
            current_step=5,
            status="active",
            created_at=now,
            updated_at=now
        )

        assert len(workflow.steps) == 10
        assert workflow.current_step == 5
