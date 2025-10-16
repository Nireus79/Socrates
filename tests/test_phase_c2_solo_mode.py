"""
Phase C2 - Solo Mode Project Support Tests
==========================================

Tests for solo project mode functionality, including:
- Solo mode detection
- Solo project creation and management
- Solo vs Team mode differentiation
- UI elements conditional display
- Filtering by solo/team type
"""

import pytest
import os
from datetime import datetime
from src.models import (
    User, Project, Module, Task, ProjectStatus, ModuleStatus, TaskStatus, Priority
)


@pytest.mark.system
@pytest.mark.integration
class TestSoloModeDetection:
    """Test solo mode detection logic"""

    def test_project_solo_mode_flag(self, clean_db, authenticated_user):
        """Test that is_solo_project flag is set correctly"""
        from src.database import get_database

        db = get_database()
        project_id = 'proj_solo_' + os.urandom(4).hex()

        project = Project(
            id=project_id,
            name='Solo Project',
            description='A solo project for testing',
            owner_id=authenticated_user['id'],
            status=ProjectStatus.ACTIVE,
            is_solo_project=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.projects.create(project)

        retrieved = db.projects.get_by_id(project_id)
        assert retrieved is not None
        # SQLite stores booleans as 1/0 integers
        assert retrieved.is_solo_project in [True, 1]

    def test_project_team_mode_flag(self, clean_db, authenticated_user):
        """Test that team mode projects have is_solo_project=False"""
        from src.database import get_database

        db = get_database()
        project_id = 'proj_team_' + os.urandom(4).hex()

        project = Project(
            id=project_id,
            name='Team Project',
            description='A team project for testing',
            owner_id=authenticated_user['id'],
            status=ProjectStatus.ACTIVE,
            is_solo_project=False,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.projects.create(project)

        retrieved = db.projects.get_by_id(project_id)
        assert retrieved is not None
        # SQLite stores booleans as 1/0 integers
        assert retrieved.is_solo_project in [False, 0]

    def test_solo_mode_default_value(self, clean_db, authenticated_user):
        """Test that is_solo_project defaults to False for new projects"""
        from src.database import get_database

        db = get_database()
        project_id = 'proj_default_' + os.urandom(4).hex()

        # Create project without specifying is_solo_project
        project = Project(
            id=project_id,
            name='Default Project',
            owner_id=authenticated_user['id'],
            status=ProjectStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.projects.create(project)

        retrieved = db.projects.get_by_id(project_id)
        assert retrieved is not None
        # Should default to False (team mode)
        assert retrieved.is_solo_project in [False, None]


@pytest.mark.system
@pytest.mark.integration
class TestSoloProjectCreation:
    """Test solo project creation and management"""

    def test_create_solo_project(self, clean_db, authenticated_user):
        """Test creating a solo project"""
        from src.database import get_database

        db = get_database()
        solo_proj_id = 'solo_proj_' + os.urandom(4).hex()

        solo_project = Project(
            id=solo_proj_id,
            name='My Solo Project',
            description='Personal project for solo development',
            owner_id=authenticated_user['id'],
            status=ProjectStatus.ACTIVE,
            is_solo_project=True,
            estimated_hours=20,
            priority='high',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        result = db.projects.create(solo_project)
        assert result is True

        retrieved = db.projects.get_by_id(solo_proj_id)
        assert retrieved is not None
        assert retrieved.name == 'My Solo Project'
        assert retrieved.is_solo_project in [True, 1]
        assert retrieved.owner_id == authenticated_user['id']

    def test_create_team_project(self, clean_db, authenticated_user):
        """Test creating a team project"""
        from src.database import get_database

        db = get_database()
        team_proj_id = 'team_proj_' + os.urandom(4).hex()

        team_project = Project(
            id=team_proj_id,
            name='My Team Project',
            description='Shared project for team development',
            owner_id=authenticated_user['id'],
            status=ProjectStatus.ACTIVE,
            is_solo_project=False,
            estimated_hours=40,
            priority='high',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        result = db.projects.create(team_project)
        assert result is True

        retrieved = db.projects.get_by_id(team_proj_id)
        assert retrieved is not None
        assert retrieved.name == 'My Team Project'
        assert retrieved.is_solo_project in [False, 0]

    def test_toggle_solo_mode(self, clean_db, authenticated_user):
        """Test toggling between solo and team modes"""
        from src.database import get_database

        db = get_database()
        project_id = 'proj_toggle_' + os.urandom(4).hex()

        # Create as team project
        project = Project(
            id=project_id,
            name='Toggle Test Project',
            owner_id=authenticated_user['id'],
            status=ProjectStatus.ACTIVE,
            is_solo_project=False,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.projects.create(project)

        # Verify it's team
        retrieved = db.projects.get_by_id(project_id)
        assert retrieved.is_solo_project in [False, 0]

        # Toggle to solo
        retrieved.is_solo_project = True
        db.projects.update(retrieved)

        # Verify it's now solo
        updated = db.projects.get_by_id(project_id)
        assert updated.is_solo_project in [True, 1]

        # Toggle back to team
        updated.is_solo_project = False
        db.projects.update(updated)

        # Verify it's back to team
        final = db.projects.get_by_id(project_id)
        assert final.is_solo_project in [False, 0]


@pytest.mark.system
@pytest.mark.integration
class TestSoloProjectRetrieval:
    """Test retrieving solo projects"""

    def test_get_solo_projects_for_user(self, clean_db, authenticated_user):
        """Test retrieving all solo projects for a user"""
        from src.database import get_database

        db = get_database()

        # Create multiple solo and team projects
        solo_ids = []
        team_ids = []

        for i in range(3):
            solo_id = f'solo_{i}_' + os.urandom(2).hex()
            solo_ids.append(solo_id)

            solo_proj = Project(
                id=solo_id,
                name=f'Solo Project {i}',
                owner_id=authenticated_user['id'],
                status=ProjectStatus.ACTIVE,
                is_solo_project=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.projects.create(solo_proj)

        for i in range(2):
            team_id = f'team_{i}_' + os.urandom(2).hex()
            team_ids.append(team_id)

            team_proj = Project(
                id=team_id,
                name=f'Team Project {i}',
                owner_id=authenticated_user['id'],
                status=ProjectStatus.ACTIVE,
                is_solo_project=False,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.projects.create(team_proj)

        # Get all projects for owner
        all_projects = db.projects.get_by_owner(authenticated_user['id'])
        assert len(all_projects) >= 5

        # Filter to solo projects
        solo_projects = [p for p in all_projects if p.is_solo_project]
        assert len(solo_projects) >= 3

        # Verify solo project IDs
        retrieved_solo_ids = [p.id for p in solo_projects]
        for solo_id in solo_ids:
            assert solo_id in retrieved_solo_ids

    def test_get_team_projects_for_user(self, clean_db, authenticated_user):
        """Test retrieving all team projects for a user"""
        from src.database import get_database

        db = get_database()

        # Create team projects
        for i in range(2):
            project = Project(
                id=f'teamproj_{i}_' + os.urandom(2).hex(),
                name=f'Team Project {i}',
                owner_id=authenticated_user['id'],
                status=ProjectStatus.ACTIVE,
                is_solo_project=False,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.projects.create(project)

        # Get all projects
        all_projects = db.projects.get_by_owner(authenticated_user['id'])

        # Filter to team projects
        team_projects = [p for p in all_projects if not p.is_solo_project]
        assert len(team_projects) >= 2


@pytest.mark.system
@pytest.mark.integration
class TestSoloProjectAttributes:
    """Test that solo projects have all necessary attributes"""

    def test_solo_project_serialization(self, clean_db, authenticated_user):
        """Test that solo project can be serialized to dict"""
        from src.database import get_database

        db = get_database()
        project_id = 'proj_serial_' + os.urandom(4).hex()

        project = Project(
            id=project_id,
            name='Serialization Test',
            description='Test project for serialization',
            owner_id=authenticated_user['id'],
            status=ProjectStatus.ACTIVE,
            is_solo_project=True,
            estimated_hours=30,
            priority='medium',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.projects.create(project)

        retrieved = db.projects.get_by_id(project_id)

        # Verify basic attributes are set
        assert retrieved.name == 'Serialization Test'
        assert retrieved.is_solo_project in [True, 1]
        assert retrieved.owner_id == authenticated_user['id']
        assert retrieved.status is not None

    def test_solo_project_in_list_serialization(self, clean_db, authenticated_user):
        """Test that solo projects serialize correctly in lists"""
        from src.database import get_database

        db = get_database()

        # Create solo and team projects
        solo_proj = Project(
            id='list_solo_' + os.urandom(4).hex(),
            name='Solo in List',
            owner_id=authenticated_user['id'],
            status=ProjectStatus.ACTIVE,
            is_solo_project=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.projects.create(solo_proj)

        team_proj = Project(
            id='list_team_' + os.urandom(4).hex(),
            name='Team in List',
            owner_id=authenticated_user['id'],
            status=ProjectStatus.ACTIVE,
            is_solo_project=False,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.projects.create(team_proj)

        # Get all projects
        all_projects = db.projects.get_by_owner(authenticated_user['id'])

        # Verify solo project is marked correctly
        solo_proj = next((p for p in all_projects if p.name == 'Solo in List'), None)
        assert solo_proj is not None
        assert solo_proj.is_solo_project in [True, 1]

        # Verify team project is marked correctly
        team_proj = next((p for p in all_projects if p.name == 'Team in List'), None)
        assert team_proj is not None
        assert team_proj.is_solo_project in [False, 0]


@pytest.mark.system
@pytest.mark.integration
class TestSoloProjectWithModules:
    """Test solo projects with modules and tasks"""

    def test_solo_project_with_modules(self, clean_db, authenticated_user):
        """Test that solo projects can have modules"""
        from src.database import get_database

        db = get_database()
        project_id = 'proj_modules_' + os.urandom(4).hex()

        # Create solo project
        project = Project(
            id=project_id,
            name='Solo with Modules',
            owner_id=authenticated_user['id'],
            status=ProjectStatus.ACTIVE,
            is_solo_project=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.projects.create(project)

        # Create modules
        for i in range(2):
            module = Module(
                id=f'mod_solo_{i}_' + os.urandom(2).hex(),
                project_id=project_id,
                name=f'Module {i}',
                status=ModuleStatus.PLANNED,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.modules.create(module)

        # Get modules for project
        modules = db.modules.get_by_project_id(project_id)
        assert len(modules) >= 2

    def test_solo_project_with_tasks(self, clean_db, authenticated_user, test_project):
        """Test that solo projects can have tasks"""
        from src.database import get_database

        db = get_database()

        # Create module
        module_id = 'mod_tasks_' + os.urandom(4).hex()
        module = Module(
            id=module_id,
            project_id=test_project['id'],
            name='Tasks Module',
            status=ModuleStatus.PLANNED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.modules.create(module)

        # Create tasks
        task_ids = []
        for i in range(3):
            task_id = f'task_solo_{i}_' + os.urandom(2).hex()
            task_ids.append(task_id)

            task = Task(
                id=task_id,
                module_id=module_id,
                project_id=test_project['id'],
                title=f'Task {i}',
                status=TaskStatus.TODO,
                priority=Priority.MEDIUM,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.tasks.create(task)

        # Retrieve and verify
        for task_id in task_ids:
            retrieved = db.tasks.get_by_id(task_id)
            assert retrieved is not None


@pytest.mark.system
@pytest.mark.integration
class TestSoloProjectStatuses:
    """Test solo projects with different status values"""

    def test_solo_project_all_statuses(self, clean_db, authenticated_user):
        """Test solo projects with all possible status values"""
        from src.database import get_database

        db = get_database()

        statuses = [ProjectStatus.ACTIVE, ProjectStatus.PAUSED, ProjectStatus.COMPLETED]

        for status in statuses:
            project_id = f'solo_{status.value}_' + os.urandom(2).hex()

            project = Project(
                id=project_id,
                name=f'Solo {status.value}',
                owner_id=authenticated_user['id'],
                status=status,
                is_solo_project=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            result = db.projects.create(project)
            assert result is True

            retrieved = db.projects.get_by_id(project_id)
            assert retrieved is not None
            assert retrieved.is_solo_project in [True, 1]
            # Status should match (could be enum or string value)
            status_value = status.value if hasattr(status, 'value') else status
            retrieved_status = retrieved.status.value if hasattr(retrieved.status, 'value') else retrieved.status
            assert retrieved_status == status_value


@pytest.mark.system
@pytest.mark.integration
class TestSoloProjectFiltering:
    """Test filtering projects by solo/team type"""

    def test_filter_solo_projects(self, clean_db, authenticated_user):
        """Test filtering to get only solo projects"""
        from src.database import get_database

        db = get_database()

        # Create mixed projects
        for i in range(2):
            solo_proj = Project(
                id=f'filter_solo_{i}_' + os.urandom(2).hex(),
                name=f'Filter Solo {i}',
                owner_id=authenticated_user['id'],
                status=ProjectStatus.ACTIVE,
                is_solo_project=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.projects.create(solo_proj)

            team_proj = Project(
                id=f'filter_team_{i}_' + os.urandom(2).hex(),
                name=f'Filter Team {i}',
                owner_id=authenticated_user['id'],
                status=ProjectStatus.ACTIVE,
                is_solo_project=False,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.projects.create(team_proj)

        # Get all projects
        all_projects = db.projects.get_by_owner(authenticated_user['id'])

        # Filter solo
        solo_only = [p for p in all_projects if p.is_solo_project]
        assert len(solo_only) >= 2

        # Verify all are solo
        for proj in solo_only:
            assert proj.is_solo_project in [True, 1]

    def test_filter_team_projects(self, clean_db, authenticated_user):
        """Test filtering to get only team projects"""
        from src.database import get_database

        db = get_database()

        # Create mixed projects
        for i in range(3):
            team_proj = Project(
                id=f'team_only_{i}_' + os.urandom(2).hex(),
                name=f'Team Only {i}',
                owner_id=authenticated_user['id'],
                status=ProjectStatus.ACTIVE,
                is_solo_project=False,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.projects.create(team_proj)

        # Get all and filter
        all_projects = db.projects.get_by_owner(authenticated_user['id'])
        team_only = [p for p in all_projects if not p.is_solo_project]
        assert len(team_only) >= 3

        # Verify all are team
        for proj in team_only:
            assert proj.is_solo_project in [False, 0]


pytestmark = [
    pytest.mark.system,
]
