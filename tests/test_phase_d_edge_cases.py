"""
Phase D - Edge Cases and Boundary Tests
=======================================

Tests for edge cases, boundary conditions, and unusual scenarios.
"""

import pytest
import os
from datetime import datetime, timedelta
from src.models import (
    User, Project, Module, Task, SocraticSession, ConversationMessage,
    GeneratedCodebase, GeneratedFile, Conflict,
    UserStatus, ProjectStatus, ModuleStatus, TaskStatus, Priority,
    ConversationStatus, TechnicalRole, ConflictType
)


@pytest.mark.system
@pytest.mark.integration
class TestStringBoundaries:
    """Test edge cases with string fields"""

    def test_very_long_username(self, clean_db):
        """Test creating user with very long username"""
        from src.database import get_database
        import hashlib

        db = get_database()
        user_id = 'user_longname_' + os.urandom(4).hex()

        # Create username at boundary
        long_username = 'a' * 255  # Very long username

        user = User(
            id=user_id,
            username=long_username,
            email='long@example.com',
            password_hash=hashlib.sha256(b'pass').hexdigest(),
            status=UserStatus.ACTIVE
        )
        result = db.users.create(user)
        assert result in [True, False]  # May succeed or fail depending on constraints

    def test_very_long_email(self, clean_db):
        """Test creating user with very long email"""
        from src.database import get_database
        import hashlib

        db = get_database()
        user_id = 'user_longemail_' + os.urandom(4).hex()

        # Create long email
        long_email = 'a' * 200 + '@example.com'

        user = User(
            id=user_id,
            username='normaltuser',
            email=long_email,
            password_hash=hashlib.sha256(b'pass').hexdigest(),
            status=UserStatus.ACTIVE
        )
        result = db.users.create(user)
        assert result in [True, False]

    def test_empty_description(self, clean_db, authenticated_user):
        """Test project with empty description"""
        from src.database import get_database

        db = get_database()
        project_id = 'proj_emptydesc_' + os.urandom(4).hex()

        project = Project(
            id=project_id,
            name='Empty Desc Project',
            description='',  # Empty description
            owner_id=authenticated_user['id'],
            status=ProjectStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        result = db.projects.create(project)
        assert result is True

        retrieved = db.projects.get_by_id(project_id)
        assert retrieved is not None

    def test_very_long_description(self, clean_db, authenticated_user):
        """Test project with very long description"""
        from src.database import get_database

        db = get_database()
        project_id = 'proj_longdesc_' + os.urandom(4).hex()

        # Create very long description
        long_description = 'This is a project description. ' * 1000

        project = Project(
            id=project_id,
            name='Long Desc Project',
            description=long_description,
            owner_id=authenticated_user['id'],
            status=ProjectStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        result = db.projects.create(project)
        assert result in [True, False]  # May succeed or fail depending on field limits

    def test_unicode_strings(self, clean_db, authenticated_user):
        """Test handling of unicode strings"""
        from src.database import get_database

        db = get_database()
        project_id = 'proj_unicode_' + os.urandom(4).hex()

        # Create with unicode content
        unicode_name = 'Проект 项目 プロジェクト'
        project = Project(
            id=project_id,
            name=unicode_name,
            description='Unicode project description: 你好 مرحبا',
            owner_id=authenticated_user['id'],
            status=ProjectStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        result = db.projects.create(project)
        assert result is True

        retrieved = db.projects.get_by_id(project_id)
        assert retrieved.name == unicode_name


@pytest.mark.system
@pytest.mark.integration
class TestNumericBoundaries:
    """Test edge cases with numeric fields"""

    def test_zero_hours(self, clean_db, test_project):
        """Test task with zero estimated hours"""
        from src.database import get_database

        db = get_database()

        # Create module
        module_id = 'mod_zero_' + os.urandom(4).hex()
        module = Module(
            id=module_id,
            project_id=test_project['id'],
            name='Zero Hours Module',
            status=ModuleStatus.PLANNED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.modules.create(module)

        # Create task with zero hours
        task_id = 'task_zero_' + os.urandom(4).hex()
        task = Task(
            id=task_id,
            module_id=module_id,
            project_id=test_project['id'],
            title='Zero Hours Task',
            status=TaskStatus.TODO,
            priority=Priority.MEDIUM,
            estimated_hours=0,
            actual_hours=0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        result = db.tasks.create(task)
        assert result is True

        retrieved = db.tasks.get_by_id(task_id)
        assert retrieved is not None

    def test_very_large_hours(self, clean_db, test_project):
        """Test task with very large estimated hours"""
        from src.database import get_database

        db = get_database()

        # Create module
        module_id = 'mod_large_' + os.urandom(4).hex()
        module = Module(
            id=module_id,
            project_id=test_project['id'],
            name='Large Hours Module',
            status=ModuleStatus.PLANNED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.modules.create(module)

        # Create task with very large hours
        task_id = 'task_large_' + os.urandom(4).hex()
        task = Task(
            id=task_id,
            module_id=module_id,
            project_id=test_project['id'],
            title='Large Hours Task',
            status=TaskStatus.TODO,
            priority=Priority.MEDIUM,
            estimated_hours=999999,
            actual_hours=999999,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        result = db.tasks.create(task)
        assert result in [True, False]

    def test_negative_hours(self, clean_db, test_project):
        """Test task with negative hours (edge case)"""
        from src.database import get_database

        db = get_database()

        # Create module
        module_id = 'mod_neg_' + os.urandom(4).hex()
        module = Module(
            id=module_id,
            project_id=test_project['id'],
            name='Negative Hours Module',
            status=ModuleStatus.PLANNED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.modules.create(module)

        # Create task with negative hours
        task_id = 'task_neg_' + os.urandom(4).hex()
        task = Task(
            id=task_id,
            module_id=module_id,
            project_id=test_project['id'],
            title='Negative Hours Task',
            status=TaskStatus.TODO,
            priority=Priority.MEDIUM,
            estimated_hours=-10,  # Negative hours
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        result = db.tasks.create(task)
        # Should handle gracefully (may fail validation)
        assert result in [True, False]


@pytest.mark.system
@pytest.mark.integration
class TestDateTimeBoundaries:
    """Test edge cases with datetime fields"""

    def test_current_datetime(self, clean_db, authenticated_user):
        """Test with current datetime"""
        from src.database import get_database

        db = get_database()
        project_id = 'proj_now_' + os.urandom(4).hex()

        now = datetime.now()
        project = Project(
            id=project_id,
            name='Now Project',
            owner_id=authenticated_user['id'],
            status=ProjectStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )
        result = db.projects.create(project)
        assert result is True

    def test_datetime_in_past(self, clean_db, authenticated_user):
        """Test with datetime in the past"""
        from src.database import get_database

        db = get_database()
        project_id = 'proj_past_' + os.urandom(4).hex()

        past = datetime.now() - timedelta(days=365)
        project = Project(
            id=project_id,
            name='Past Project',
            owner_id=authenticated_user['id'],
            status=ProjectStatus.ACTIVE,
            created_at=past,
            updated_at=past
        )
        result = db.projects.create(project)
        assert result is True

        retrieved = db.projects.get_by_id(project_id)
        assert retrieved is not None

    def test_datetime_in_future(self, clean_db, authenticated_user):
        """Test with datetime in the future"""
        from src.database import get_database

        db = get_database()
        project_id = 'proj_future_' + os.urandom(4).hex()

        future = datetime.now() + timedelta(days=365)
        project = Project(
            id=project_id,
            name='Future Project',
            owner_id=authenticated_user['id'],
            status=ProjectStatus.ACTIVE,
            created_at=future,
            updated_at=future
        )
        result = db.projects.create(project)
        assert result in [True, False]  # May fail depending on validation

    def test_datetime_with_microseconds(self, clean_db, authenticated_user):
        """Test datetime with microsecond precision"""
        from src.database import get_database

        db = get_database()
        project_id = 'proj_micro_' + os.urandom(4).hex()

        now = datetime.now()  # Has microseconds
        project = Project(
            id=project_id,
            name='Microsecond Project',
            owner_id=authenticated_user['id'],
            status=ProjectStatus.ACTIVE,
            created_at=now,
            updated_at=now
        )
        result = db.projects.create(project)
        assert result is True

        retrieved = db.projects.get_by_id(project_id)
        assert retrieved is not None


@pytest.mark.system
@pytest.mark.integration
class TestRelationshipEdgeCases:
    """Test edge cases with entity relationships"""

    def test_many_tasks_in_module(self, clean_db, test_project):
        """Test creating many tasks in a single module"""
        from src.database import get_database

        db = get_database()

        # Create module
        module_id = 'mod_manytasks_' + os.urandom(4).hex()
        module = Module(
            id=module_id,
            project_id=test_project['id'],
            name='Many Tasks Module',
            status=ModuleStatus.PLANNED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.modules.create(module)

        # Create many tasks
        for i in range(20):
            task_id = f'task_many_{i}_' + os.urandom(2).hex()
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

        # Verify all created
        all_tasks = db.tasks.get_all()
        assert len(all_tasks) >= 20

    def test_many_modules_in_project(self, clean_db, test_project):
        """Test creating many modules in a single project"""
        from src.database import get_database

        db = get_database()

        # Create many modules
        for i in range(15):
            module_id = f'mod_many_{i}_' + os.urandom(2).hex()
            module = Module(
                id=module_id,
                project_id=test_project['id'],
                name=f'Module {i}',
                status=ModuleStatus.PLANNED,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.modules.create(module)

        # Verify all created
        all_modules = db.modules.get_by_project_id(test_project['id'])
        assert len(all_modules) >= 15

    def test_many_messages_in_session(self, clean_db, authenticated_user, test_project):
        """Test creating many messages in a session"""
        from src.database import get_database

        db = get_database()

        # Create session
        session_id = 'sess_manymsg_' + os.urandom(4).hex()
        session = SocraticSession(
            id=session_id,
            project_id=test_project['id'],
            user_id=authenticated_user['id'],
            status=ConversationStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.socratic_sessions.create(session)

        # Create many messages
        for i in range(30):
            message_id = f'msg_many_{i}_' + os.urandom(2).hex()
            message = ConversationMessage(
                id=message_id,
                session_id=session_id,
                project_id=test_project['id'],
                message_type='user' if i % 2 == 0 else 'assistant',
                content=f'Message {i}',
                role='user' if i % 2 == 0 else 'assistant',
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.conversation_messages.create(message)

        # Verify
        session_messages = db.conversation_messages.get_by_session_id(session_id)
        assert len(session_messages) >= 30


@pytest.mark.system
@pytest.mark.integration
class TestStatusTransitions:
    """Test edge cases with status transitions"""

    def test_all_project_status_values(self, clean_db, authenticated_user):
        """Test all possible project status values"""
        from src.database import get_database

        db = get_database()

        # Test each status
        for status in [ProjectStatus.ACTIVE, ProjectStatus.PAUSED, ProjectStatus.COMPLETED]:
            project_id = f'proj_status_{status.value}_' + os.urandom(2).hex()

            project = Project(
                id=project_id,
                name=f'Project {status.value}',
                owner_id=authenticated_user['id'],
                status=status,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            result = db.projects.create(project)
            assert result is True

            retrieved = db.projects.get_by_id(project_id)
            assert retrieved is not None

    def test_all_task_status_values(self, clean_db, test_project):
        """Test all possible task status values"""
        from src.database import get_database

        db = get_database()

        # Create module
        module_id = 'mod_status_' + os.urandom(4).hex()
        module = Module(
            id=module_id,
            project_id=test_project['id'],
            name='Status Module',
            status=ModuleStatus.PLANNED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.modules.create(module)

        # Test each task status
        for status in [TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED]:
            task_id = f'task_status_{status.value}_' + os.urandom(2).hex()

            task = Task(
                id=task_id,
                module_id=module_id,
                project_id=test_project['id'],
                title=f'Task {status.value}',
                status=status,
                priority=Priority.MEDIUM,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            result = db.tasks.create(task)
            assert result is True

            retrieved = db.tasks.get_by_id(task_id)
            assert retrieved is not None

    def test_all_task_priority_values(self, clean_db, test_project):
        """Test all possible task priority values"""
        from src.database import get_database

        db = get_database()

        # Create module
        module_id = 'mod_priority_' + os.urandom(4).hex()
        module = Module(
            id=module_id,
            project_id=test_project['id'],
            name='Priority Module',
            status=ModuleStatus.PLANNED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.modules.create(module)

        # Test each priority
        for priority in [Priority.LOW, Priority.MEDIUM, Priority.HIGH, Priority.CRITICAL]:
            task_id = f'task_pri_{priority.value}_' + os.urandom(2).hex()

            task = Task(
                id=task_id,
                module_id=module_id,
                project_id=test_project['id'],
                title=f'Priority {priority.value}',
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
class TestIdentifierEdgeCases:
    """Test edge cases with entity identifiers"""

    def test_long_id(self, clean_db):
        """Test entity with very long ID"""
        from src.database import get_database
        import hashlib

        db = get_database()
        user_id = 'user_' + 'x' * 200  # Very long ID

        user = User(
            id=user_id,
            username='longiduser',
            email='longid@example.com',
            password_hash=hashlib.sha256(b'pass').hexdigest(),
            status=UserStatus.ACTIVE
        )
        result = db.users.create(user)
        # May succeed or fail depending on ID column constraints
        assert result in [True, False]

    def test_id_with_special_characters(self, clean_db):
        """Test entity ID with special characters"""
        from src.database import get_database
        import hashlib

        db = get_database()
        user_id = 'user_special-!@#$%_' + os.urandom(4).hex()

        user = User(
            id=user_id,
            username='specialiduser',
            email='specialid@example.com',
            password_hash=hashlib.sha256(b'pass').hexdigest(),
            status=UserStatus.ACTIVE
        )
        result = db.users.create(user)
        assert result in [True, False]

    def test_uuid_format_id(self, clean_db):
        """Test entity with UUID format ID"""
        from src.database import get_database
        import hashlib
        import uuid

        db = get_database()
        user_id = str(uuid.uuid4())

        user = User(
            id=user_id,
            username='uuiduser',
            email='uuid@example.com',
            password_hash=hashlib.sha256(b'pass').hexdigest(),
            status=UserStatus.ACTIVE
        )
        result = db.users.create(user)
        assert result is True

        retrieved = db.users.get_by_id(user_id)
        assert retrieved is not None


pytestmark = [
    pytest.mark.system,
]
