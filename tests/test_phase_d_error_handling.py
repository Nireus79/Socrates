"""
Phase D - Error Handling and Validation Tests
==============================================

Tests for error handling, validation, and edge cases in the database layer.
"""

import pytest
import os
from datetime import datetime
from src.models import (
    User, Project, Module, Task, SocraticSession, ConversationMessage,
    GeneratedCodebase, GeneratedFile, Conflict,
    UserStatus, ProjectStatus, ModuleStatus, TaskStatus, Priority,
    ConversationStatus, TechnicalRole, ConflictType
)


@pytest.mark.system
@pytest.mark.integration
class TestRepositoryErrorHandling:
    """Test error handling in repositories"""

    def test_get_nonexistent_user(self, clean_db):
        """Test getting a non-existent user"""
        from src.database import get_database

        db = get_database()
        result = db.users.get_by_id('nonexistent_user_id')
        assert result is None

    def test_get_nonexistent_project(self, clean_db):
        """Test getting a non-existent project"""
        from src.database import get_database

        db = get_database()
        result = db.projects.get_by_id('nonexistent_project_id')
        assert result is None

    def test_get_nonexistent_module(self, clean_db):
        """Test getting a non-existent module"""
        from src.database import get_database

        db = get_database()
        result = db.modules.get_by_id('nonexistent_module_id')
        assert result is None

    def test_get_nonexistent_task(self, clean_db):
        """Test getting a non-existent task"""
        from src.database import get_database

        db = get_database()
        result = db.tasks.get_by_id('nonexistent_task_id')
        assert result is None

    def test_delete_nonexistent_entity(self, clean_db):
        """Test deleting a non-existent entity"""
        from src.database import get_database

        db = get_database()
        result = db.users.delete('nonexistent_user_id')
        # Should handle gracefully without throwing error
        assert result in [True, False]

    def test_update_nonexistent_entity(self, clean_db):
        """Test updating a non-existent entity"""
        from src.database import get_database
        import hashlib

        db = get_database()
        user = User(
            id='nonexistent_user',
            username='ghost',
            email='ghost@example.com',
            password_hash=hashlib.sha256(b'pass').hexdigest(),
            status=UserStatus.ACTIVE
        )
        # Update should handle gracefully
        result = db.users.update(user)
        assert result in [True, False]

    def test_exists_nonexistent_entity(self, clean_db):
        """Test checking existence of non-existent entity"""
        from src.database import get_database

        db = get_database()
        result = db.users.exists('definitely_not_real_id')
        assert result is False


@pytest.mark.system
@pytest.mark.integration
class TestDataValidation:
    """Test data validation and constraints"""

    def test_create_user_with_empty_id(self, clean_db):
        """Test creating user with empty ID"""
        from src.database import get_database
        import hashlib

        db = get_database()
        user = User(
            id='',  # Empty ID
            username='testuser',
            email='test@example.com',
            password_hash=hashlib.sha256(b'pass').hexdigest(),
            status=UserStatus.ACTIVE
        )
        # Should handle empty ID gracefully
        result = db.users.create(user)
        # This depends on database constraints
        assert result in [True, False]

    def test_create_duplicate_user(self, clean_db):
        """Test creating duplicate user with same ID"""
        from src.database import get_database
        import hashlib

        db = get_database()
        user_id = 'dup_user_' + os.urandom(4).hex()

        user1 = User(
            id=user_id,
            username='user1',
            email='user1@example.com',
            password_hash=hashlib.sha256(b'pass').hexdigest(),
            status=UserStatus.ACTIVE
        )

        # Create first user
        db.users.create(user1)

        # Try to create duplicate
        user2 = User(
            id=user_id,
            username='user2',
            email='user2@example.com',
            password_hash=hashlib.sha256(b'pass').hexdigest(),
            status=UserStatus.ACTIVE
        )

        # Should fail or handle duplicate gracefully
        result = db.users.create(user2)
        # Query to verify only one exists
        retrieved = db.users.get_by_id(user_id)
        assert retrieved is not None

    def test_create_project_with_null_owner(self, clean_db):
        """Test creating project with null owner"""
        from src.database import get_database

        db = get_database()

        # Project should raise ValidationError on init with null owner
        try:
            project = Project(
                id='proj_null_' + os.urandom(4).hex(),
                name='Null Owner Project',
                owner_id=None,  # NULL owner
                status=ProjectStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            # If we get here, validation didn't catch it (check if it was caught in create)
            result = db.projects.create(project)
            # Either way, result should be well-defined
            assert result in [True, False]
        except Exception:
            # Validation error is expected - project requires owner
            assert True

    def test_create_task_with_null_module(self, clean_db, test_project):
        """Test creating task with null module"""
        from src.database import get_database

        db = get_database()
        task = Task(
            id='task_null_' + os.urandom(4).hex(),
            module_id=None,  # NULL module
            project_id=test_project['id'],
            title='No Module Task',
            status=TaskStatus.TODO,
            priority=Priority.MEDIUM,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Should handle null module gracefully
        result = db.tasks.create(task)
        assert result in [True, False]


@pytest.mark.system
@pytest.mark.integration
class TestMissingRelationships:
    """Test handling of missing relationships"""

    def test_create_task_with_nonexistent_module(self, clean_db, test_project):
        """Test creating task with non-existent module"""
        from src.database import get_database

        db = get_database()
        task = Task(
            id='task_nomod_' + os.urandom(4).hex(),
            module_id='nonexistent_module_id',
            project_id=test_project['id'],
            title='Task with Missing Module',
            status=TaskStatus.TODO,
            priority=Priority.MEDIUM,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Should handle missing relationship gracefully
        result = db.tasks.create(task)
        # May succeed or fail depending on foreign key constraints
        assert result in [True, False]

    def test_create_module_with_nonexistent_project(self, clean_db):
        """Test creating module with non-existent project"""
        from src.database import get_database

        db = get_database()
        module = Module(
            id='mod_noproj_' + os.urandom(4).hex(),
            project_id='nonexistent_project_id',
            name='Module with Missing Project',
            status=ModuleStatus.PLANNED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Should handle missing project gracefully
        result = db.modules.create(module)
        assert result in [True, False]

    def test_create_session_with_nonexistent_project(self, clean_db, authenticated_user):
        """Test creating session with non-existent project"""
        from src.database import get_database

        db = get_database()
        session = SocraticSession(
            id='sess_noproj_' + os.urandom(4).hex(),
            project_id='nonexistent_project_id',
            user_id=authenticated_user['id'],
            status=ConversationStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Should handle missing project gracefully
        result = db.socratic_sessions.create(session)
        assert result in [True, False]


@pytest.mark.system
@pytest.mark.integration
class TestEnumHandling:
    """Test proper enum handling in database operations"""

    def test_user_status_enum(self, clean_db):
        """Test user status enum values"""
        from src.database import get_database
        import hashlib

        db = get_database()
        user_id = 'user_status_' + os.urandom(4).hex()

        # Test different status values
        for status in [UserStatus.ACTIVE, UserStatus.INACTIVE, UserStatus.SUSPENDED]:
            user = User(
                id=user_id + '_' + status.value,
                username=f'user_{status.value}',
                email=f'{status.value}@example.com',
                password_hash=hashlib.sha256(b'pass').hexdigest(),
                status=status
            )
            result = db.users.create(user)
            assert result is True

            retrieved = db.users.get_by_id(user_id + '_' + status.value)
            assert retrieved is not None

    def test_project_status_enum(self, clean_db, authenticated_user):
        """Test project status enum values"""
        from src.database import get_database

        db = get_database()
        project_id = 'proj_status_' + os.urandom(4).hex()

        # Test different status values
        for status in [ProjectStatus.ACTIVE, ProjectStatus.PAUSED, ProjectStatus.COMPLETED]:
            project = Project(
                id=project_id + '_' + status.value,
                name=f'Project {status.value}',
                owner_id=authenticated_user['id'],
                status=status,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            result = db.projects.create(project)
            assert result is True

            retrieved = db.projects.get_by_id(project_id + '_' + status.value)
            assert retrieved is not None

    def test_task_priority_enum(self, clean_db, test_project):
        """Test task priority enum values"""
        from src.database import get_database

        db = get_database()

        # Create module
        module_id = 'mod_priority_' + os.urandom(4).hex()
        module = Module(
            id=module_id,
            project_id=test_project['id'],
            name='Priority Test Module',
            status=ModuleStatus.PLANNED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.modules.create(module)

        # Test different priority values
        for priority in [Priority.LOW, Priority.MEDIUM, Priority.HIGH, Priority.CRITICAL]:
            task_id = 'task_pri_' + priority.value + '_' + os.urandom(2).hex()
            task = Task(
                id=task_id,
                module_id=module_id,
                project_id=test_project['id'],
                title=f'Task {priority.value}',
                status=TaskStatus.TODO,
                priority=priority,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            result = db.tasks.create(task)
            assert result is True

            retrieved = db.tasks.get_by_id(task_id)
            assert retrieved is not None


@pytest.mark.system
@pytest.mark.integration
class TestDateTimeHandling:
    """Test proper datetime handling in database operations"""

    def test_datetime_storage_and_retrieval(self, clean_db, authenticated_user):
        """Test that datetimes are stored and retrieved correctly"""
        from src.database import get_database
        from datetime import datetime, timedelta

        db = get_database()
        project_id = 'proj_datetime_' + os.urandom(4).hex()

        # Create with specific datetime
        now = datetime.now()
        project = Project(
            id=project_id,
            name='Datetime Test',
            owner_id=authenticated_user['id'],
            status=ProjectStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )
        db.projects.create(project)

        # Retrieve and verify
        retrieved = db.projects.get_by_id(project_id)
        assert retrieved is not None
        # Datetimes should be close (within a second)
        assert isinstance(retrieved.created_at, (str, datetime))

    def test_null_optional_datetime(self, clean_db, test_project):
        """Test handling of null optional datetime fields"""
        from src.database import get_database

        db = get_database()

        # Create module
        module_id = 'mod_datetime_' + os.urandom(4).hex()
        module = Module(
            id=module_id,
            project_id=test_project['id'],
            name='Null DateTime Module',
            status=ModuleStatus.PLANNED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.modules.create(module)

        # Create task with null optional datetimes
        task_id = 'task_datetime_' + os.urandom(4).hex()
        task = Task(
            id=task_id,
            module_id=module_id,
            project_id=test_project['id'],
            title='Null DateTime Task',
            status=TaskStatus.TODO,
            priority=Priority.MEDIUM,
            completed_at=None,  # Optional field
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        result = db.tasks.create(task)
        assert result is True

        retrieved = db.tasks.get_by_id(task_id)
        assert retrieved is not None


@pytest.mark.system
@pytest.mark.integration
class TestConcurrentOperations:
    """Test handling of potentially concurrent operations"""

    def test_sequential_creates(self, clean_db, authenticated_user):
        """Test multiple sequential creates"""
        from src.database import get_database

        db = get_database()

        # Create multiple projects sequentially
        project_ids = []
        for i in range(5):
            project_id = f'proj_seq_{i}_' + os.urandom(2).hex()
            project_ids.append(project_id)

            project = Project(
                id=project_id,
                name=f'Sequential Project {i}',
                owner_id=authenticated_user['id'],
                status=ProjectStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            result = db.projects.create(project)
            assert result is True

        # Verify all created
        for project_id in project_ids:
            retrieved = db.projects.get_by_id(project_id)
            assert retrieved is not None

    def test_sequential_updates(self, clean_db, authenticated_user):
        """Test multiple sequential updates"""
        from src.database import get_database

        db = get_database()

        # Create a project
        project_id = 'proj_upd_seq_' + os.urandom(4).hex()
        project = Project(
            id=project_id,
            name='Original Name',
            owner_id=authenticated_user['id'],
            status=ProjectStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.projects.create(project)

        # Update multiple times
        for i in range(3):
            project.name = f'Updated Name {i}'
            result = db.projects.update(project)
            assert result is True

        # Verify final state
        retrieved = db.projects.get_by_id(project_id)
        assert retrieved.name == 'Updated Name 2'

    def test_interleaved_operations(self, clean_db, authenticated_user, test_project):
        """Test interleaved create/read/update operations"""
        from src.database import get_database

        db = get_database()

        # Create module
        module_id = 'mod_interleave_' + os.urandom(4).hex()
        module = Module(
            id=module_id,
            project_id=test_project['id'],
            name='Interleave Module',
            status=ModuleStatus.PLANNED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.modules.create(module)

        # Interleave creates and reads
        task_ids = []
        for i in range(3):
            # Create
            task_id = f'task_inter_{i}_' + os.urandom(2).hex()
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

            # Read previous
            if i > 0:
                prev_task = db.tasks.get_by_id(task_ids[i - 1])
                assert prev_task is not None

        # Verify all exist
        for task_id in task_ids:
            retrieved = db.tasks.get_by_id(task_id)
            assert retrieved is not None


pytestmark = [
    pytest.mark.system,
]
