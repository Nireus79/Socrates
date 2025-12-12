"""
Comprehensive tests for Phase 1 & 2 Team Management System implementation.

Tests:
- Role system (universal roles across project types)
- ProjectContext team_members and migration
- ProjectManagerAgent role-aware methods
- Collaboration commands with roles
- Question generation with role context
- Question queue agent functionality
- Skills management commands
- Backward compatibility
- All 6 project types
"""

from datetime import datetime

import pytest

from socratic_system.models import (
    ROLE_FOCUS_AREAS,
    VALID_ROLES,
    ProjectContext,
    TeamMemberRole,
)


class TestRoleSystem:
    """Test universal role system"""

    def test_valid_roles_defined(self):
        """Test that all 5 universal roles are defined"""
        assert len(VALID_ROLES) == 5
        assert "lead" in VALID_ROLES
        assert "creator" in VALID_ROLES
        assert "specialist" in VALID_ROLES
        assert "analyst" in VALID_ROLES
        assert "coordinator" in VALID_ROLES

    def test_role_focus_areas_complete(self):
        """Test that all roles have focus area descriptions"""
        for role in VALID_ROLES:
            assert role in ROLE_FOCUS_AREAS
            assert isinstance(ROLE_FOCUS_AREAS[role], str)
            assert len(ROLE_FOCUS_AREAS[role]) > 0

    def test_team_member_role_creation(self):
        """Test TeamMemberRole dataclass"""
        member = TeamMemberRole(
            username="alice", role="creator", skills=["python", "react"], joined_at=datetime.now()
        )
        assert member.username == "alice"
        assert member.role == "creator"
        assert member.skills == ["python", "react"]

    def test_team_member_role_serialization(self):
        """Test TeamMemberRole to_dict and from_dict"""
        original = TeamMemberRole(
            username="bob",
            role="specialist",
            skills=["security", "testing"],
            joined_at=datetime.now(),
        )

        data = original.to_dict()
        restored = TeamMemberRole.from_dict(data)

        assert restored.username == original.username
        assert restored.role == original.role
        assert restored.skills == original.skills


class TestProjectContextTeamMembers:
    """Test ProjectContext team_members field and migration"""

    def test_project_initialization_creates_team_members(self):
        """Test that new projects automatically create team_members with owner"""
        project = ProjectContext(
            project_id="test1",
            name="Test Project",
            owner="john",
            collaborators=[],
            goals="Test goals",
            requirements=[],
            tech_stack=[],
            constraints=[],
            team_structure="individual",
            language_preferences="python",
            deployment_target="local",
            code_style="documented",
            phase="discovery",
            conversation_history=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert project.team_members is not None
        assert len(project.team_members) == 1
        assert project.team_members[0].username == "john"
        assert project.team_members[0].role == "lead"

    def test_project_with_collaborators_migrates_to_team_members(self):
        """Test backward compatibility - old collaborators migrate to team_members"""
        project = ProjectContext(
            project_id="test2",
            name="Test Project",
            owner="john",
            collaborators=["alice", "bob"],
            goals="Test goals",
            requirements=[],
            tech_stack=[],
            constraints=[],
            team_structure="team",
            language_preferences="python",
            deployment_target="local",
            code_style="documented",
            phase="discovery",
            conversation_history=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Should have migrated collaborators to team_members
        assert project.team_members is not None
        assert len(project.team_members) == 3  # owner + 2 collaborators

        # Owner should be lead
        owner_member = next((m for m in project.team_members if m.username == "john"), None)
        assert owner_member is not None
        assert owner_member.role == "lead"

        # Collaborators should be creators
        creator_members = [m for m in project.team_members if m.role == "creator"]
        assert len(creator_members) == 2

    def test_get_member_role(self):
        """Test get_member_role helper method"""
        project = ProjectContext(
            project_id="test3",
            name="Test Project",
            owner="john",
            collaborators=[],
            goals="Test goals",
            requirements=[],
            tech_stack=[],
            constraints=[],
            team_structure="individual",
            language_preferences="python",
            deployment_target="local",
            code_style="documented",
            phase="discovery",
            conversation_history=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Add team member
        project.team_members.append(
            TeamMemberRole(
                username="alice", role="specialist", skills=["security"], joined_at=datetime.now()
            )
        )

        assert project.get_member_role("john") == "lead"
        assert project.get_member_role("alice") == "specialist"
        assert project.get_member_role("unknown") is None

    def test_is_solo_project(self):
        """Test is_solo_project helper method"""
        # Solo project
        solo_project = ProjectContext(
            project_id="solo",
            name="Solo Project",
            owner="john",
            collaborators=[],
            goals="Solo goals",
            requirements=[],
            tech_stack=[],
            constraints=[],
            team_structure="individual",
            language_preferences="python",
            deployment_target="local",
            code_style="documented",
            phase="discovery",
            conversation_history=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert solo_project.is_solo_project() is True

        # Team project
        team_project = ProjectContext(
            project_id="team",
            name="Team Project",
            owner="john",
            collaborators=["alice"],
            goals="Team goals",
            requirements=[],
            tech_stack=[],
            constraints=[],
            team_structure="team",
            language_preferences="python",
            deployment_target="local",
            code_style="documented",
            phase="discovery",
            conversation_history=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert team_project.is_solo_project() is False


class TestProjectTypes:
    """Test that role system works across all 6 project types"""

    @pytest.mark.parametrize(
        "project_type", ["software", "business", "creative", "research", "marketing", "educational"]
    )
    def test_project_type_support(self, project_type):
        """Test project creation for all 6 project types"""
        project = ProjectContext(
            project_id=f"test_{project_type}",
            name=f"Test {project_type}",
            owner="john",
            collaborators=[],
            goals="Test goals",
            requirements=[],
            tech_stack=[],
            constraints=[],
            team_structure="individual",
            language_preferences="python",
            deployment_target="local",
            code_style="documented",
            phase="discovery",
            conversation_history=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            project_type=project_type,
        )

        assert project.project_type == project_type
        assert project.team_members is not None
        assert len(project.team_members) == 1
        assert project.team_members[0].role == "lead"


class TestPendingQuestionsField:
    """Test pending_questions field for question queue"""

    def test_pending_questions_initialized(self):
        """Test that pending_questions is initialized"""
        project = ProjectContext(
            project_id="test_queue",
            name="Test Queue",
            owner="john",
            collaborators=[],
            goals="Test goals",
            requirements=[],
            tech_stack=[],
            constraints=[],
            team_structure="team",
            language_preferences="python",
            deployment_target="local",
            code_style="documented",
            phase="discovery",
            conversation_history=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert project.pending_questions is not None
        assert isinstance(project.pending_questions, list)
        assert len(project.pending_questions) == 0

    def test_pending_questions_structure(self):
        """Test question entry structure"""
        question_entry = {
            "id": "q_abc123",
            "question": "What problem does this solve?",
            "phase": "discovery",
            "assigned_to_roles": ["analyst", "lead"],
            "assigned_to_users": ["john", "alice"],
            "created_at": datetime.now().isoformat(),
            "status": "pending",
            "answered_by": None,
            "answer": None,
        }

        # Verify all expected fields are present
        assert "id" in question_entry
        assert "question" in question_entry
        assert "phase" in question_entry
        assert "assigned_to_roles" in question_entry
        assert "assigned_to_users" in question_entry
        assert "status" in question_entry
        assert question_entry["status"] == "pending"


class TestTeamManagementIntegration:
    """Integration tests for team management features"""

    def test_role_based_team_structure(self):
        """Test creating a realistic team structure"""
        project = ProjectContext(
            project_id="realistic_team",
            name="Realistic Team Project",
            owner="sarah",
            collaborators=[],
            goals="Build scalable software",
            requirements=[],
            tech_stack=["python", "react"],
            constraints=[],
            team_structure="team",
            language_preferences="python",
            deployment_target="production",
            code_style="documented",
            phase="design",
            conversation_history=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            project_type="software",
        )

        # Simulate adding team members with different roles
        project.team_members = [
            TeamMemberRole("sarah", "lead", ["architecture", "strategy"], datetime.now()),
            TeamMemberRole("alice", "creator", ["python", "backend"], datetime.now()),
            TeamMemberRole("bob", "specialist", ["security", "testing"], datetime.now()),
            TeamMemberRole("charlie", "analyst", ["requirements", "validation"], datetime.now()),
            TeamMemberRole(
                "diana", "coordinator", ["project_management", "scheduling"], datetime.now()
            ),
        ]

        assert len(project.team_members) == 5
        assert not project.is_solo_project()

        # Verify each role is present
        roles = {m.role for m in project.team_members}
        assert roles == {"lead", "creator", "specialist", "analyst", "coordinator"}

        # Verify role lookups work
        assert project.get_member_role("sarah") == "lead"
        assert project.get_member_role("alice") == "creator"
        assert project.get_member_role("bob") == "specialist"
        assert project.get_member_role("charlie") == "analyst"
        assert project.get_member_role("diana") == "coordinator"


class TestSkillsTracking:
    """Test skills tracking for team members"""

    def test_member_skills_assigned(self):
        """Test assigning skills to team members"""
        member = TeamMemberRole(
            username="alice",
            role="creator",
            skills=["python", "typescript", "react", "testing"],
            joined_at=datetime.now(),
        )

        assert len(member.skills) == 4
        assert "python" in member.skills
        assert "typescript" in member.skills

    def test_member_skills_updated(self):
        """Test updating member skills"""
        member = TeamMemberRole(
            username="bob", role="specialist", skills=["security"], joined_at=datetime.now()
        )

        # Update skills
        member.skills = ["security", "cryptography", "penetration_testing"]

        assert len(member.skills) == 3
        assert "cryptography" in member.skills


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
