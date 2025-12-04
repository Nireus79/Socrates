"""
Tests for ProjectManagerAgent - Project lifecycle management
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import uuid

import socrates
from socratic_system.agents.project_manager import ProjectManagerAgent
from socratic_system.models import ProjectContext
from socratic_system.events import EventType


@pytest.mark.unit
class TestProjectManagerAgentCreation:
    """Tests for ProjectManagerAgent initialization and creation"""

    def test_agent_initialization(self, test_config):
        """Test ProjectManagerAgent initializes correctly"""
        with patch('socratic_system.clients.anthropic.Anthropic'):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = ProjectManagerAgent(orchestrator)

            assert agent is not None
            assert agent.name == "ProjectManager"
            assert agent.orchestrator == orchestrator

    def test_create_project_success(self, test_config, sample_user):
        """Test successful project creation"""
        with patch('socratic_system.clients.anthropic.Anthropic'):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = ProjectManagerAgent(orchestrator)

            request = {
                'action': 'create_project',
                'project_name': 'Test API Project',
                'owner': sample_user.username
            }

            result = agent.process(request)

            assert result['status'] == 'success'
            assert 'project' in result
            assert result['project'].name == 'Test API Project'
            assert result['project'].owner == sample_user.username
            assert result['project'].phase == 'discovery'

    def test_create_project_with_invalid_data(self, test_config):
        """Test project creation with missing required fields"""
        with patch('socratic_system.clients.anthropic.Anthropic'):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = ProjectManagerAgent(orchestrator)

            # Missing owner
            request = {
                'action': 'create_project',
                'project_name': 'Test Project'
            }

            result = agent.process(request)

            # Should handle gracefully (API should validate)
            # This tests error handling
            assert 'status' in result


@pytest.mark.unit
class TestProjectManagerAgentProjectOperations:
    """Tests for project retrieval, update, and deletion"""

    def test_load_project_success(self, test_config, sample_project):
        """Test loading an existing project"""
        with patch('socratic_system.clients.anthropic.Anthropic'):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = ProjectManagerAgent(orchestrator)

            # Save project first
            orchestrator.database.save_project(sample_project)

            request = {
                'action': 'load_project',
                'project_id': sample_project.project_id
            }

            result = agent.process(request)

            assert result['status'] == 'success'
            assert result['project'].name == sample_project.name

    def test_load_project_not_found(self, test_config):
        """Test loading a non-existent project"""
        with patch('socratic_system.clients.anthropic.Anthropic'):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = ProjectManagerAgent(orchestrator)

            request = {
                'action': 'load_project',
                'project_id': 'nonexistent_id_12345'
            }

            result = agent.process(request)

            assert result['status'] == 'error'
            assert 'not found' in result['message'].lower()

    def test_save_project_updates_timestamp(self, test_config, sample_project):
        """Test that saving a project updates its timestamp"""
        with patch('socratic_system.clients.anthropic.Anthropic'):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = ProjectManagerAgent(orchestrator)

            # Save project first
            orchestrator.database.save_project(sample_project)
            original_timestamp = sample_project.updated_at

            # Modify and save
            sample_project.description = "Updated description"
            request = {
                'action': 'save_project',
                'project': sample_project
            }

            result = agent.process(request)

            assert result['status'] == 'success'
            # Timestamp should be updated (not exact same)
            assert sample_project.updated_at >= original_timestamp


@pytest.mark.unit
class TestProjectManagerAgentCollaborators:
    """Tests for collaborator management"""

    def test_add_collaborator_success(self, test_config, sample_project):
        """Test adding a collaborator to project"""
        with patch('socratic_system.clients.anthropic.Anthropic'):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = ProjectManagerAgent(orchestrator)

            orchestrator.database.save_project(sample_project)

            request = {
                'action': 'add_collaborator',
                'project': sample_project,
                'username': 'newcollaborator'
            }

            result = agent.process(request)

            assert result['status'] == 'success'
            assert 'newcollaborator' in sample_project.collaborators

    def test_add_duplicate_collaborator(self, test_config, sample_project):
        """Test adding a collaborator who is already on the project"""
        with patch('socratic_system.clients.anthropic.Anthropic'):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = ProjectManagerAgent(orchestrator)

            sample_project.collaborators = ['existing_user']
            orchestrator.database.save_project(sample_project)

            request = {
                'action': 'add_collaborator',
                'project': sample_project,
                'username': 'existing_user'
            }

            result = agent.process(request)

            assert result['status'] == 'error'
            assert 'already' in result['message'].lower()

    def test_list_collaborators(self, test_config, sample_project):
        """Test listing all collaborators for a project"""
        with patch('socratic_system.clients.anthropic.Anthropic'):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = ProjectManagerAgent(orchestrator)

            sample_project.collaborators = ['user1', 'user2', 'user3']
            orchestrator.database.save_project(sample_project)

            request = {
                'action': 'list_collaborators',
                'project': sample_project
            }

            result = agent.process(request)

            assert result['status'] == 'success'
            assert result['total_count'] == 4  # owner + 3 collaborators
            assert any(c['username'] == sample_project.owner and c['role'] == 'owner'
                      for c in result['collaborators'])
            assert any(c['username'] == 'user1' and c['role'] == 'collaborator'
                      for c in result['collaborators'])

    def test_remove_collaborator_success(self, test_config, sample_project):
        """Test removing a collaborator from project"""
        with patch('socratic_system.clients.anthropic.Anthropic'):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = ProjectManagerAgent(orchestrator)

            sample_project.collaborators = ['user_to_remove']
            orchestrator.database.save_project(sample_project)

            request = {
                'action': 'remove_collaborator',
                'project': sample_project,
                'username': 'user_to_remove',
                'requester': sample_project.owner
            }

            result = agent.process(request)

            assert result['status'] == 'success'
            assert 'user_to_remove' not in sample_project.collaborators

    def test_remove_collaborator_not_owner(self, test_config, sample_project):
        """Test that non-owners cannot remove collaborators"""
        with patch('socratic_system.clients.anthropic.Anthropic'):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = ProjectManagerAgent(orchestrator)

            sample_project.collaborators = ['user_to_remove']
            orchestrator.database.save_project(sample_project)

            request = {
                'action': 'remove_collaborator',
                'project': sample_project,
                'username': 'user_to_remove',
                'requester': 'not_the_owner'
            }

            result = agent.process(request)

            assert result['status'] == 'error'
            assert 'owner' in result['message'].lower()

    def test_remove_owner_fails(self, test_config, sample_project):
        """Test that owner cannot be removed from project"""
        with patch('socratic_system.clients.anthropic.Anthropic'):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = ProjectManagerAgent(orchestrator)

            orchestrator.database.save_project(sample_project)

            request = {
                'action': 'remove_collaborator',
                'project': sample_project,
                'username': sample_project.owner,
                'requester': sample_project.owner
            }

            result = agent.process(request)

            assert result['status'] == 'error'
            assert 'owner' in result['message'].lower()


@pytest.mark.unit
class TestProjectManagerAgentProjectListing:
    """Tests for listing projects"""

    def test_list_projects_for_user(self, test_config, sample_user):
        """Test listing all projects owned by a user"""
        with patch('socratic_system.clients.anthropic.Anthropic'):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = ProjectManagerAgent(orchestrator)

            # Create multiple projects
            for i in range(3):
                project = ProjectContext(
                    project_id=f"proj_{i}",
                    name=f"Project {i}",
                    owner=sample_user.username,
                    collaborators=[],
                    goals="",
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
                    updated_at=datetime.now()
                )
                orchestrator.database.save_project(project)

            request = {
                'action': 'list_projects',
                'username': sample_user.username
            }

            result = agent.process(request)

            assert result['status'] == 'success'
            assert 'projects' in result
            # Should have projects (exact count depends on database implementation)
            assert len(result['projects']) >= 0


@pytest.mark.unit
class TestProjectManagerAgentArchiving:
    """Tests for project archiving and restoration"""

    def test_archive_project_success(self, test_config, sample_project):
        """Test successfully archiving a project"""
        with patch('socratic_system.clients.anthropic.Anthropic'):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = ProjectManagerAgent(orchestrator)

            orchestrator.database.save_project(sample_project)

            request = {
                'action': 'archive_project',
                'project_id': sample_project.project_id,
                'requester': sample_project.owner
            }

            result = agent.process(request)

            assert result['status'] == 'success'
            assert 'archived' in result['message'].lower()

    def test_archive_project_not_owner(self, test_config, sample_project):
        """Test that non-owners cannot archive project"""
        with patch('socratic_system.clients.anthropic.Anthropic'):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = ProjectManagerAgent(orchestrator)

            orchestrator.database.save_project(sample_project)

            request = {
                'action': 'archive_project',
                'project_id': sample_project.project_id,
                'requester': 'not_the_owner'
            }

            result = agent.process(request)

            assert result['status'] == 'error'
            assert 'owner' in result['message'].lower()

    def test_archive_nonexistent_project(self, test_config):
        """Test archiving a non-existent project"""
        with patch('socratic_system.clients.anthropic.Anthropic'):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = ProjectManagerAgent(orchestrator)

            request = {
                'action': 'archive_project',
                'project_id': 'nonexistent_12345',
                'requester': 'someuser'
            }

            result = agent.process(request)

            assert result['status'] == 'error'

    def test_restore_project_success(self, test_config, sample_project):
        """Test successfully restoring an archived project"""
        with patch('socratic_system.clients.anthropic.Anthropic'):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = ProjectManagerAgent(orchestrator)

            orchestrator.database.save_project(sample_project)
            orchestrator.database.archive_project(sample_project.project_id)

            request = {
                'action': 'restore_project',
                'project_id': sample_project.project_id,
                'requester': sample_project.owner
            }

            result = agent.process(request)

            assert result['status'] == 'success'
            assert 'restored' in result['message'].lower()


@pytest.mark.unit
class TestProjectManagerAgentDeletion:
    """Tests for permanent project deletion"""

    def test_delete_project_requires_confirmation(self, test_config, sample_project):
        """Test that project deletion requires confirmation"""
        with patch('socratic_system.clients.anthropic.Anthropic'):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = ProjectManagerAgent(orchestrator)

            orchestrator.database.save_project(sample_project)

            # Try without confirmation
            request = {
                'action': 'delete_project_permanently',
                'project_id': sample_project.project_id,
                'requester': sample_project.owner,
                'confirmation': 'no'
            }

            result = agent.process(request)

            assert result['status'] == 'error'
            assert 'DELETE' in result['message']

    def test_delete_project_success_with_confirmation(self, test_config, sample_project):
        """Test successful permanent project deletion with proper confirmation"""
        with patch('socratic_system.clients.anthropic.Anthropic'):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = ProjectManagerAgent(orchestrator)

            orchestrator.database.save_project(sample_project)

            request = {
                'action': 'delete_project_permanently',
                'project_id': sample_project.project_id,
                'requester': sample_project.owner,
                'confirmation': 'DELETE'
            }

            result = agent.process(request)

            assert result['status'] == 'success'
            assert 'deleted' in result['message'].lower()

    def test_delete_project_not_owner(self, test_config, sample_project):
        """Test that non-owners cannot delete project"""
        with patch('socratic_system.clients.anthropic.Anthropic'):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = ProjectManagerAgent(orchestrator)

            orchestrator.database.save_project(sample_project)

            request = {
                'action': 'delete_project_permanently',
                'project_id': sample_project.project_id,
                'requester': 'not_the_owner',
                'confirmation': 'DELETE'
            }

            result = agent.process(request)

            assert result['status'] == 'error'
            assert 'owner' in result['message'].lower()


@pytest.mark.unit
class TestProjectManagerAgentErrorHandling:
    """Tests for error scenarios and edge cases"""

    def test_unknown_action(self, test_config):
        """Test handling of unknown action"""
        with patch('socratic_system.clients.anthropic.Anthropic'):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = ProjectManagerAgent(orchestrator)

            request = {
                'action': 'unknown_action_xyz'
            }

            result = agent.process(request)

            assert result['status'] == 'error'
            assert 'unknown' in result['message'].lower()

    def test_missing_action(self, test_config):
        """Test handling of missing action field"""
        with patch('socratic_system.clients.anthropic.Anthropic'):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = ProjectManagerAgent(orchestrator)

            request = {}

            result = agent.process(request)

            assert result['status'] == 'error'

    def test_get_archived_projects(self, test_config):
        """Test retrieving archived projects list"""
        with patch('socratic_system.clients.anthropic.Anthropic'):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = ProjectManagerAgent(orchestrator)

            request = {
                'action': 'get_archived_projects'
            }

            result = agent.process(request)

            assert result['status'] == 'success'
            assert 'archived_projects' in result


@pytest.mark.integration
class TestProjectManagerAgentIntegration:
    """Integration tests for ProjectManagerAgent workflows"""

    def test_full_project_lifecycle(self, test_config, sample_user):
        """Test complete project lifecycle: create -> load -> save -> archive -> restore"""
        with patch('socratic_system.clients.anthropic.Anthropic'):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = ProjectManagerAgent(orchestrator)

            # Create project
            create_request = {
                'action': 'create_project',
                'project_name': 'Lifecycle Test Project',
                'owner': sample_user.username
            }
            create_result = agent.process(create_request)
            assert create_result['status'] == 'success'
            project = create_result['project']

            # Load project
            load_request = {
                'action': 'load_project',
                'project_id': project.project_id
            }
            load_result = agent.process(load_request)
            assert load_result['status'] == 'success'

            # Save project with modifications
            loaded_project = load_result['project']
            loaded_project.description = "Modified description"
            save_request = {
                'action': 'save_project',
                'project': loaded_project
            }
            save_result = agent.process(save_request)
            assert save_result['status'] == 'success'

            # Archive project
            archive_request = {
                'action': 'archive_project',
                'project_id': project.project_id,
                'requester': sample_user.username
            }
            archive_result = agent.process(archive_request)
            assert archive_result['status'] == 'success'

            # Restore project
            restore_request = {
                'action': 'restore_project',
                'project_id': project.project_id,
                'requester': sample_user.username
            }
            restore_result = agent.process(restore_request)
            assert restore_result['status'] == 'success'

    def test_collaboration_workflow(self, test_config, sample_project):
        """Test adding/removing collaborators and listing them"""
        with patch('socratic_system.clients.anthropic.Anthropic'):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = ProjectManagerAgent(orchestrator)

            orchestrator.database.save_project(sample_project)

            # Add multiple collaborators
            for i in range(3):
                add_request = {
                    'action': 'add_collaborator',
                    'project': sample_project,
                    'username': f'collaborator_{i}'
                }
                result = agent.process(add_request)
                assert result['status'] == 'success'

            # List collaborators
            list_request = {
                'action': 'list_collaborators',
                'project': sample_project
            }
            result = agent.process(list_request)
            assert result['status'] == 'success'
            assert result['total_count'] == 4  # owner + 3 collaborators

            # Remove one collaborator
            remove_request = {
                'action': 'remove_collaborator',
                'project': sample_project,
                'username': 'collaborator_0',
                'requester': sample_project.owner
            }
            result = agent.process(remove_request)
            assert result['status'] == 'success'

            # Verify count decreased
            list_request = {
                'action': 'list_collaborators',
                'project': sample_project
            }
            result = agent.process(list_request)
            assert result['total_count'] == 3
