#!/usr/bin/env python3
"""
Test Suite for Authorization System
====================================
Tests the require_authentication and require_project_access decorators.
"""

import pytest
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import get_database, init_database
from src.models import User, Project, ProjectCollaborator, UserStatus, UserRole
from src.agents.base import BaseAgent, require_authentication, require_project_access


# Minimal mock services for testing
class MockServices:
    """Minimal service container for testing"""
    def get_db_manager(self):
        from src.database import get_database
        db = get_database()
        return db.db_manager if db else None

    def get_config(self):
        return None

    def get_logger(self, name=None):
        import logging
        return logging.getLogger(name or 'test')

    def get_event_system(self):
        return None

    def get_event_bus(self):
        return None


# Test Agent for authorization testing
class TestAuthAgent(BaseAgent):
    """Test agent with decorated methods"""

    def __init__(self, services=None):
        # Initialize with minimal services for database access
        super().__init__('test_auth_agent', 'Test Auth Agent', services or MockServices())

    def get_capabilities(self):
        return ['auth_test', 'project_test']

    @require_authentication
    def test_auth_method(self, data):
        """Method that requires authentication"""
        return self._success_response(
            "Authenticated successfully",
            {'user_id': data.get('user_id')}
        )

    @require_project_access
    def test_project_method(self, data):
        """Method that requires project access"""
        return self._success_response(
            "Project access granted",
            {
                'user_id': data.get('user_id'),
                'project_id': data.get('project_id'),
                'role': data.get('_project_role')
            }
        )


@pytest.fixture(scope="function", autouse=False)
def setup_test_env():
    """Set up test environment with database and test data"""
    # Reset and initialize database with fresh state for each test
    # This ensures no stale data from previous tests
    from src.database import reset_database
    import os

    # Delete the database file to ensure clean state
    db_path = 'data/socratic.db'
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except:
            pass

    # Reset singleton instances
    reset_database()
    init_database()
    db = get_database()

    # Create test users
    active_user = User(
        id='user_active_1',
        username='active_user',
        email='active@test.com',
        password_hash='hash123',
        role=UserRole.DEVELOPER,
        status=UserStatus.ACTIVE
    )

    inactive_user = User(
        id='user_inactive_1',
        username='inactive_user',
        email='inactive@test.com',
        password_hash='hash456',
        role=UserRole.DEVELOPER,
        status=UserStatus.INACTIVE
    )

    collaborator_user = User(
        id='user_collab_1',
        username='collaborator',
        email='collab@test.com',
        password_hash='hash789',
        role=UserRole.DEVELOPER,
        status=UserStatus.ACTIVE
    )

    db.users.create(active_user)
    db.users.create(inactive_user)
    db.users.create(collaborator_user)

    # Create test project
    project = Project(
        id='project_test_1',
        name='Test Project',
        description='Test project for authorization',
        owner_id='user_active_1',
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.projects.create(project)

    # Add collaborator
    collaboration = ProjectCollaborator(
        id='collab_1',
        project_id='project_test_1',
        user_id='user_collab_1',
        role=UserRole.DEVELOPER,
        is_active=True,
        joined_at=datetime.now()
    )
    db.project_collaborators.create(collaboration)

    # Create test agent
    agent = TestAuthAgent()

    yield {
        'db': db,
        'agent': agent,
        'active_user_id': 'user_active_1',
        'inactive_user_id': 'user_inactive_1',
        'collaborator_user_id': 'user_collab_1',
        'project_id': 'project_test_1',
        'invalid_user_id': 'user_invalid_999',
        'invalid_project_id': 'project_invalid_999'
    }


class TestAuthentication:
    """Test require_authentication decorator"""

    def test_no_user_id(self, setup_test_env):
        """Test that missing user_id returns AUTH_REQUIRED error"""
        agent = setup_test_env['agent']
        result = agent.test_auth_method({})

        assert result['success'] is False
        assert result['error_code'] == 'AUTH_REQUIRED'
        assert 'Authentication required' in result['error']

    def test_invalid_user_id(self, setup_test_env):
        """Test that invalid user_id returns INVALID_USER error"""
        agent = setup_test_env['agent']
        invalid_id = setup_test_env['invalid_user_id']

        result = agent.test_auth_method({'user_id': invalid_id})

        assert result['success'] is False
        assert result['error_code'] == 'INVALID_USER'
        assert 'Invalid user' in result['error']

    def test_inactive_user(self, setup_test_env):
        """Test that inactive user returns USER_INACTIVE error"""
        agent = setup_test_env['agent']
        inactive_id = setup_test_env['inactive_user_id']

        result = agent.test_auth_method({'user_id': inactive_id})

        assert result['success'] is False
        assert result['error_code'] == 'USER_INACTIVE'
        assert 'inactive' in result['error'].lower()

    def test_active_user_success(self, setup_test_env):
        """Test that active user passes authentication"""
        agent = setup_test_env['agent']
        active_id = setup_test_env['active_user_id']

        result = agent.test_auth_method({'user_id': active_id})

        assert result['success'] is True
        assert result['data']['user_id'] == active_id


class TestProjectAccess:
    """Test require_project_access decorator"""

    def test_no_user_id(self, setup_test_env):
        """Test that missing user_id returns AUTH_REQUIRED error"""
        agent = setup_test_env['agent']
        project_id = setup_test_env['project_id']

        result = agent.test_project_method({'project_id': project_id})

        assert result['success'] is False
        assert result['error_code'] == 'AUTH_REQUIRED'

    def test_no_project_id(self, setup_test_env):
        """Test that missing project_id returns PROJECT_ID_REQUIRED error"""
        agent = setup_test_env['agent']
        active_id = setup_test_env['active_user_id']

        result = agent.test_project_method({'user_id': active_id})

        assert result['success'] is False
        assert result['error_code'] == 'PROJECT_ID_REQUIRED'
        assert 'Project ID required' in result['error']

    def test_invalid_project_id(self, setup_test_env):
        """Test that invalid project_id returns PROJECT_NOT_FOUND error"""
        agent = setup_test_env['agent']
        active_id = setup_test_env['active_user_id']
        invalid_project = setup_test_env['invalid_project_id']

        result = agent.test_project_method({
            'user_id': active_id,
            'project_id': invalid_project
        })

        assert result['success'] is False
        assert result['error_code'] == 'PROJECT_NOT_FOUND'
        assert 'Project not found' in result['error']

    def test_unauthorized_user(self, setup_test_env):
        """Test that user without access returns ACCESS_DENIED error"""
        agent = setup_test_env['agent']
        db = setup_test_env['db']
        project_id = setup_test_env['project_id']

        # Create another user who is not owner or collaborator
        unauthorized_user = User(
            id='user_unauthorized',
            username='unauthorized',
            email='unauthorized@test.com',
            password_hash='hash000',
            role=UserRole.DEVELOPER,
            status=UserStatus.ACTIVE
        )
        db.users.create(unauthorized_user)

        result = agent.test_project_method({
            'user_id': 'user_unauthorized',
            'project_id': project_id
        })

        assert result['success'] is False
        assert result['error_code'] == 'ACCESS_DENIED'
        assert 'Access denied' in result['error']

    def test_owner_access_success(self, setup_test_env):
        """Test that project owner has access"""
        agent = setup_test_env['agent']
        owner_id = setup_test_env['active_user_id']
        project_id = setup_test_env['project_id']

        result = agent.test_project_method({
            'user_id': owner_id,
            'project_id': project_id
        })

        assert result['success'] is True
        assert result['data']['user_id'] == owner_id
        assert result['data']['project_id'] == project_id
        assert result['data']['role'] == 'owner'

    def test_collaborator_access_success(self, setup_test_env):
        """Test that active collaborator has access"""
        agent = setup_test_env['agent']
        collab_id = setup_test_env['collaborator_user_id']
        project_id = setup_test_env['project_id']

        result = agent.test_project_method({
            'user_id': collab_id,
            'project_id': project_id
        })

        assert result['success'] is True
        assert result['data']['user_id'] == collab_id
        assert result['data']['project_id'] == project_id
        assert result['data']['role'] == 'developer'

    def test_inactive_collaborator_denied(self, setup_test_env):
        """Test that inactive collaborator is denied access"""
        agent = setup_test_env['agent']
        db = setup_test_env['db']
        project_id = setup_test_env['project_id']

        # Create user and add as inactive collaborator
        inactive_collab_user = User(
            id='user_inactive_collab',
            username='inactive_collab',
            email='inactive.collab@test.com',
            password_hash='hash111',
            role=UserRole.DEVELOPER,
            status=UserStatus.ACTIVE
        )
        db.users.create(inactive_collab_user)

        inactive_collaboration = ProjectCollaborator(
            id='collab_inactive',
            project_id=project_id,
            user_id='user_inactive_collab',
            role=UserRole.VIEWER,
            is_active=False,
            joined_at=datetime.now()
        )
        db.project_collaborators.create(inactive_collaboration)

        result = agent.test_project_method({
            'user_id': 'user_inactive_collab',
            'project_id': project_id
        })

        assert result['success'] is False
        assert result['error_code'] == 'ACCESS_DENIED'


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
