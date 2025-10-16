"""
Phase D - CRUD Operations Tests
================================

Comprehensive tests for all CRUD (Create, Read, Update, Delete) operations
across all repositories in the database layer.
"""

import pytest
import os
from datetime import datetime
from src.models import (
    User, Project, Module, Task, SocraticSession, ConversationMessage,
    GeneratedCodebase, GeneratedFile, Conflict, ProjectCollaborator,
    UserStatus, ProjectStatus, ModuleStatus, TaskStatus, Priority,
    ConversationStatus, TechnicalRole, ConflictType
)


@pytest.mark.system
@pytest.mark.integration
class TestUserRepositoryCRUD:
    """Test User repository CRUD operations"""

    def test_user_create_read(self, clean_db):
        """Test creating and reading a user"""
        from src.database import get_database
        import hashlib

        db = get_database()
        user_id = 'user_crud_' + os.urandom(4).hex()

        user = User(
            id=user_id,
            username='cruduser',
            email='crud@example.com',
            password_hash=hashlib.sha256(b'password').hexdigest(),
            status=UserStatus.ACTIVE
        )

        # Create
        result = db.users.create(user)
        assert result is True

        # Read
        retrieved = db.users.get_by_id(user_id)
        assert retrieved is not None
        assert retrieved.username == 'cruduser'
        assert retrieved.email == 'crud@example.com'

    def test_user_update(self, clean_db):
        """Test updating a user"""
        from src.database import get_database
        import hashlib

        db = get_database()
        user_id = 'user_update_' + os.urandom(4).hex()

        user = User(
            id=user_id,
            username='originalname',
            email='original@example.com',
            password_hash=hashlib.sha256(b'pass').hexdigest(),
            status=UserStatus.ACTIVE
        )
        db.users.create(user)

        # Update
        user.username = 'updatedname'
        user.email = 'updated@example.com'
        result = db.users.update(user)
        assert result is True

        # Verify update
        retrieved = db.users.get_by_id(user_id)
        assert retrieved.username == 'updatedname'
        assert retrieved.email == 'updated@example.com'

    def test_user_delete(self, clean_db):
        """Test deleting a user"""
        from src.database import get_database
        import hashlib

        db = get_database()
        user_id = 'user_delete_' + os.urandom(4).hex()

        user = User(
            id=user_id,
            username='tobedeleted',
            email='delete@example.com',
            password_hash=hashlib.sha256(b'pass').hexdigest(),
            status=UserStatus.ACTIVE
        )
        db.users.create(user)

        # Verify exists
        assert db.users.exists(user_id) is True

        # Delete
        result = db.users.delete(user_id)
        assert result is True

        # Verify deleted
        assert db.users.exists(user_id) is False
        assert db.users.get_by_id(user_id) is None

    def test_user_get_all(self, clean_db):
        """Test getting all users"""
        from src.database import get_database
        import hashlib

        db = get_database()

        # Create multiple users
        for i in range(3):
            user = User(
                id='user_all_' + str(i) + '_' + os.urandom(2).hex(),
                username=f'user{i}',
                email=f'user{i}@example.com',
                password_hash=hashlib.sha256(b'pass').hexdigest(),
                status=UserStatus.ACTIVE
            )
            db.users.create(user)

        # Get all
        all_users = db.users.get_all()
        assert len(all_users) >= 3

    def test_user_count(self, clean_db):
        """Test counting users"""
        from src.database import get_database
        import hashlib

        db = get_database()

        # Count before
        count_before = db.users.count()

        # Create a user
        user = User(
            id='user_count_' + os.urandom(4).hex(),
            username='counttest',
            email='count@example.com',
            password_hash=hashlib.sha256(b'pass').hexdigest(),
            status=UserStatus.ACTIVE
        )
        db.users.create(user)

        # Count after
        count_after = db.users.count()
        assert count_after == count_before + 1


@pytest.mark.system
@pytest.mark.integration
class TestProjectRepositoryCRUD:
    """Test Project repository CRUD operations"""

    def test_project_create_read(self, clean_db, authenticated_user):
        """Test creating and reading a project"""
        from src.database import get_database

        db = get_database()
        project_id = 'proj_crud_' + os.urandom(4).hex()

        project = Project(
            id=project_id,
            name='CRUD Test Project',
            description='Test project for CRUD',
            owner_id=authenticated_user['id'],
            status=ProjectStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Create
        result = db.projects.create(project)
        assert result is True

        # Read
        retrieved = db.projects.get_by_id(project_id)
        assert retrieved is not None
        assert retrieved.name == 'CRUD Test Project'
        assert retrieved.owner_id == authenticated_user['id']

    def test_project_update(self, clean_db, authenticated_user):
        """Test updating a project"""
        from src.database import get_database

        db = get_database()
        project_id = 'proj_update_' + os.urandom(4).hex()

        project = Project(
            id=project_id,
            name='Original Name',
            description='Original description',
            owner_id=authenticated_user['id'],
            status=ProjectStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.projects.create(project)

        # Update
        project.name = 'Updated Name'
        project.description = 'Updated description'
        result = db.projects.update(project)
        assert result is True

        # Verify
        retrieved = db.projects.get_by_id(project_id)
        assert retrieved.name == 'Updated Name'
        assert retrieved.description == 'Updated description'

    def test_project_delete(self, clean_db, authenticated_user):
        """Test deleting a project"""
        from src.database import get_database

        db = get_database()
        project_id = 'proj_delete_' + os.urandom(4).hex()

        project = Project(
            id=project_id,
            name='To Delete',
            owner_id=authenticated_user['id'],
            status=ProjectStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.projects.create(project)

        # Delete
        result = db.projects.delete(project_id)
        assert result is True

        # Verify
        assert db.projects.get_by_id(project_id) is None

    def test_project_get_by_owner(self, clean_db, authenticated_user):
        """Test getting projects by owner"""
        from src.database import get_database

        db = get_database()

        # Create multiple projects for user
        for i in range(2):
            project = Project(
                id='proj_owner_' + str(i) + '_' + os.urandom(2).hex(),
                name=f'Project {i}',
                owner_id=authenticated_user['id'],
                status=ProjectStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.projects.create(project)

        # Get by owner
        owner_projects = db.projects.get_by_owner(authenticated_user['id'])
        assert len(owner_projects) >= 2


@pytest.mark.system
@pytest.mark.integration
class TestModuleRepositoryCRUD:
    """Test Module repository CRUD operations"""

    def test_module_create_read(self, clean_db, test_project):
        """Test creating and reading a module"""
        from src.database import get_database

        db = get_database()
        module_id = 'mod_crud_' + os.urandom(4).hex()

        module = Module(
            id=module_id,
            project_id=test_project['id'],
            name='CRUD Module',
            status=ModuleStatus.PLANNED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Create
        result = db.modules.create(module)
        assert result is True

        # Read
        retrieved = db.modules.get_by_id(module_id)
        assert retrieved is not None
        assert retrieved.name == 'CRUD Module'

    def test_module_update(self, clean_db, test_project):
        """Test updating a module"""
        from src.database import get_database

        db = get_database()
        module_id = 'mod_update_' + os.urandom(4).hex()

        module = Module(
            id=module_id,
            project_id=test_project['id'],
            name='Original Module',
            status=ModuleStatus.PLANNED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.modules.create(module)

        # Update
        module.name = 'Updated Module'
        module.status = ModuleStatus.IN_PROGRESS
        result = db.modules.update(module)
        assert result is True

        # Verify
        retrieved = db.modules.get_by_id(module_id)
        assert retrieved.name == 'Updated Module'

    def test_module_delete(self, clean_db, test_project):
        """Test deleting a module"""
        from src.database import get_database

        db = get_database()
        module_id = 'mod_delete_' + os.urandom(4).hex()

        module = Module(
            id=module_id,
            project_id=test_project['id'],
            name='To Delete',
            status=ModuleStatus.PLANNED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.modules.create(module)

        # Delete
        result = db.modules.delete(module_id)
        assert result is True

        # Verify
        assert db.modules.get_by_id(module_id) is None

    def test_module_get_by_project(self, clean_db, test_project):
        """Test getting modules by project"""
        from src.database import get_database

        db = get_database()

        # Create modules for project
        for i in range(2):
            module = Module(
                id='mod_proj_' + str(i) + '_' + os.urandom(2).hex(),
                project_id=test_project['id'],
                name=f'Module {i}',
                status=ModuleStatus.PLANNED,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.modules.create(module)

        # Get by project
        project_modules = db.modules.get_by_project_id(test_project['id'])
        assert len(project_modules) >= 2


@pytest.mark.system
@pytest.mark.integration
class TestTaskRepositoryCRUD:
    """Test Task repository CRUD operations"""

    def test_task_create_read(self, clean_db, test_project):
        """Test creating and reading a task"""
        from src.database import get_database

        db = get_database()

        # Create module first
        module_id = 'mod_task_' + os.urandom(4).hex()
        module = Module(
            id=module_id,
            project_id=test_project['id'],
            name='Task Module',
            status=ModuleStatus.PLANNED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.modules.create(module)

        # Create task
        task_id = 'task_crud_' + os.urandom(4).hex()
        task = Task(
            id=task_id,
            module_id=module_id,
            project_id=test_project['id'],
            title='CRUD Task',
            status=TaskStatus.TODO,
            priority=Priority.MEDIUM,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Create
        result = db.tasks.create(task)
        assert result is True

        # Read
        retrieved = db.tasks.get_by_id(task_id)
        assert retrieved is not None
        assert retrieved.title == 'CRUD Task'

    def test_task_update(self, clean_db, test_project):
        """Test updating a task"""
        from src.database import get_database

        db = get_database()

        # Create module
        module_id = 'mod_task_upd_' + os.urandom(4).hex()
        module = Module(
            id=module_id,
            project_id=test_project['id'],
            name='Task Module',
            status=ModuleStatus.PLANNED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.modules.create(module)

        # Create task
        task_id = 'task_update_' + os.urandom(4).hex()
        task = Task(
            id=task_id,
            module_id=module_id,
            project_id=test_project['id'],
            title='Original Task',
            status=TaskStatus.TODO,
            priority=Priority.LOW,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.tasks.create(task)

        # Update
        task.title = 'Updated Task'
        task.status = TaskStatus.IN_PROGRESS
        task.priority = Priority.HIGH
        result = db.tasks.update(task)
        assert result is True

        # Verify
        retrieved = db.tasks.get_by_id(task_id)
        assert retrieved.title == 'Updated Task'
        assert retrieved.status == TaskStatus.IN_PROGRESS

    def test_task_delete(self, clean_db, test_project):
        """Test deleting a task"""
        from src.database import get_database

        db = get_database()

        # Create module
        module_id = 'mod_task_del_' + os.urandom(4).hex()
        module = Module(
            id=module_id,
            project_id=test_project['id'],
            name='Task Module',
            status=ModuleStatus.PLANNED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.modules.create(module)

        # Create task
        task_id = 'task_delete_' + os.urandom(4).hex()
        task = Task(
            id=task_id,
            module_id=module_id,
            project_id=test_project['id'],
            title='To Delete',
            status=TaskStatus.TODO,
            priority=Priority.MEDIUM,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.tasks.create(task)

        # Delete
        result = db.tasks.delete(task_id)
        assert result is True

        # Verify
        assert db.tasks.get_by_id(task_id) is None


@pytest.mark.system
@pytest.mark.integration
class TestSessionAndMessageCRUD:
    """Test SocraticSession and ConversationMessage CRUD operations"""

    def test_session_create_read(self, clean_db, authenticated_user, test_project):
        """Test creating and reading a session"""
        from src.database import get_database

        db = get_database()
        session_id = 'sess_crud_' + os.urandom(4).hex()

        session = SocraticSession(
            id=session_id,
            project_id=test_project['id'],
            user_id=authenticated_user['id'],
            current_role=TechnicalRole.PROJECT_MANAGER,
            status=ConversationStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Create
        result = db.socratic_sessions.create(session)
        assert result is True

        # Read
        retrieved = db.socratic_sessions.get_by_id(session_id)
        assert retrieved is not None
        assert retrieved.status == ConversationStatus.ACTIVE

    def test_message_create_read(self, clean_db, authenticated_user, test_project):
        """Test creating and reading a message"""
        from src.database import get_database

        db = get_database()

        # Create session
        session_id = 'sess_msg_' + os.urandom(4).hex()
        session = SocraticSession(
            id=session_id,
            project_id=test_project['id'],
            user_id=authenticated_user['id'],
            status=ConversationStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.socratic_sessions.create(session)

        # Create message
        msg_id = 'msg_crud_' + os.urandom(4).hex()
        message = ConversationMessage(
            id=msg_id,
            session_id=session_id,
            project_id=test_project['id'],
            message_type='user',
            content='Test message content',
            role='user',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Create
        result = db.conversation_messages.create(message)
        assert result is True

        # Read
        retrieved = db.conversation_messages.get_by_id(msg_id)
        assert retrieved is not None
        assert retrieved.content == 'Test message content'

    def test_get_messages_by_session(self, clean_db, authenticated_user, test_project):
        """Test getting messages by session"""
        from src.database import get_database

        db = get_database()

        # Create session
        session_id = 'sess_msgs_' + os.urandom(4).hex()
        session = SocraticSession(
            id=session_id,
            project_id=test_project['id'],
            user_id=authenticated_user['id'],
            status=ConversationStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.socratic_sessions.create(session)

        # Create multiple messages
        for i in range(3):
            message = ConversationMessage(
                id='msg_sess_' + str(i) + '_' + os.urandom(2).hex(),
                session_id=session_id,
                project_id=test_project['id'],
                message_type='user' if i % 2 == 0 else 'assistant',
                content=f'Message {i}',
                role='user' if i % 2 == 0 else 'assistant',
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.conversation_messages.create(message)

        # Get by session
        session_messages = db.conversation_messages.get_by_session_id(session_id)
        assert len(session_messages) >= 3


@pytest.mark.system
@pytest.mark.integration
class TestCodebaseAndFilesCRUD:
    """Test GeneratedCodebase and GeneratedFile CRUD operations"""

    def test_codebase_create_read(self, clean_db, test_project):
        """Test creating and reading a codebase"""
        from src.database import get_database

        db = get_database()
        codebase_id = 'cb_crud_' + os.urandom(4).hex()

        codebase = GeneratedCodebase(
            id=codebase_id,
            project_id=test_project['id'],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Create
        result = db.codebases.create(codebase)
        assert result is True

        # Read
        retrieved = db.codebases.get_by_id(codebase_id)
        assert retrieved is not None

    def test_file_create_read(self, clean_db, test_project):
        """Test creating and reading a generated file"""
        from src.database import get_database

        db = get_database()

        # Create codebase
        codebase_id = 'cb_file_' + os.urandom(4).hex()
        codebase = GeneratedCodebase(
            id=codebase_id,
            project_id=test_project['id'],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.codebases.create(codebase)

        # Create file
        file_id = 'file_crud_' + os.urandom(4).hex()
        file_obj = GeneratedFile(
            id=file_id,
            codebase_id=codebase_id,
            project_id=test_project['id'],
            file_path='src/crud_test.py',
            content='print("CRUD test")',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Create
        result = db.generated_files.create(file_obj)
        assert result is True

        # Read
        retrieved = db.generated_files.get_by_id(file_id)
        assert retrieved is not None
        assert retrieved.file_path == 'src/crud_test.py'
        assert retrieved.content == 'print("CRUD test")'

    def test_file_update(self, clean_db, test_project):
        """Test updating a generated file"""
        from src.database import get_database

        db = get_database()

        # Create codebase
        codebase_id = 'cb_file_upd_' + os.urandom(4).hex()
        codebase = GeneratedCodebase(
            id=codebase_id,
            project_id=test_project['id'],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.codebases.create(codebase)

        # Create file
        file_id = 'file_update_' + os.urandom(4).hex()
        file_obj = GeneratedFile(
            id=file_id,
            codebase_id=codebase_id,
            project_id=test_project['id'],
            file_path='src/original.py',
            content='original',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.generated_files.create(file_obj)

        # Update content (note: file_path is not updated by GeneratedFileRepository.update())
        file_obj.content = 'updated content'
        result = db.generated_files.update(file_obj)
        assert result is True

        # Verify content updated (file_path is not updated by repository)
        retrieved = db.generated_files.get_by_id(file_id)
        assert retrieved.content == 'updated content'
        assert retrieved.file_path == 'src/original.py'  # file_path not updated by update() method

    def test_get_files_by_codebase(self, clean_db, test_project):
        """Test getting files by codebase"""
        from src.database import get_database

        db = get_database()

        # Create codebase
        codebase_id = 'cb_files_' + os.urandom(4).hex()
        codebase = GeneratedCodebase(
            id=codebase_id,
            project_id=test_project['id'],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.codebases.create(codebase)

        # Create multiple files
        for i in range(3):
            file_obj = GeneratedFile(
                id='file_cb_' + str(i) + '_' + os.urandom(2).hex(),
                codebase_id=codebase_id,
                project_id=test_project['id'],
                file_path=f'src/file{i}.py',
                content=f'# File {i}',
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.generated_files.create(file_obj)

        # Get by codebase
        codebase_files = db.generated_files.get_by_codebase_id(codebase_id)
        assert len(codebase_files) >= 3


@pytest.mark.system
@pytest.mark.integration
class TestConflictCRUD:
    """Test Conflict repository CRUD operations"""

    def test_conflict_create_read(self, clean_db, test_project):
        """Test creating and reading a conflict"""
        from src.database import get_database

        db = get_database()
        conflict_id = 'conf_crud_' + os.urandom(4).hex()

        conflict = Conflict(
            id=conflict_id,
            project_id=test_project['id'],
            conflict_type=ConflictType.TECHNICAL,
            first_requirement='Requirement A',
            second_requirement='Requirement B',
            severity='high',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Create
        result = db.conflicts.create(conflict)
        assert result is True

        # Read
        retrieved = db.conflicts.get_by_id(conflict_id)
        assert retrieved is not None
        assert retrieved.first_requirement == 'Requirement A'

    def test_conflict_update(self, clean_db, test_project):
        """Test updating a conflict"""
        from src.database import get_database

        db = get_database()
        conflict_id = 'conf_update_' + os.urandom(4).hex()

        conflict = Conflict(
            id=conflict_id,
            project_id=test_project['id'],
            conflict_type=ConflictType.TECHNICAL,
            first_requirement='Original A',
            second_requirement='Original B',
            severity='low',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.conflicts.create(conflict)

        # Update
        conflict.severity = 'critical'
        result = db.conflicts.update(conflict)
        assert result is True

        # Verify
        retrieved = db.conflicts.get_by_id(conflict_id)
        assert retrieved.severity == 'critical'

    def test_conflict_delete(self, clean_db, test_project):
        """Test deleting a conflict"""
        from src.database import get_database

        db = get_database()
        conflict_id = 'conf_delete_' + os.urandom(4).hex()

        conflict = Conflict(
            id=conflict_id,
            project_id=test_project['id'],
            conflict_type=ConflictType.TECHNICAL,
            first_requirement='Req A',
            second_requirement='Req B',
            severity='high',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.conflicts.create(conflict)

        # Delete
        result = db.conflicts.delete(conflict_id)
        assert result is True

        # Verify
        assert db.conflicts.get_by_id(conflict_id) is None

    def test_get_conflicts_by_project(self, clean_db, test_project):
        """Test getting conflicts by project"""
        from src.database import get_database

        db = get_database()

        # Create multiple conflicts
        for i in range(2):
            conflict = Conflict(
                id='conf_proj_' + str(i) + '_' + os.urandom(2).hex(),
                project_id=test_project['id'],
                conflict_type=ConflictType.TECHNICAL if i % 2 == 0 else ConflictType.RESOURCE,
                first_requirement=f'Req A{i}',
                second_requirement=f'Req B{i}',
                severity='high',
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.conflicts.create(conflict)

        # Get by project
        project_conflicts = db.conflicts.get_by_project_id(test_project['id'])
        assert len(project_conflicts) >= 2


pytestmark = [
    pytest.mark.system,
]
