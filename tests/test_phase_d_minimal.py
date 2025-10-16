"""
Phase D Minimal Test Suite
==========================

Simplified tests that work with the actual models in src/models.py.
These tests verify core functionality without trying to override model designs.
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
@pytest.mark.smoke
class TestBasicModels:
    """Test that basic model creation works"""

    def test_create_user(self, clean_db):
        """Test creating a user"""
        from src.database import get_database
        import hashlib

        db = get_database()
        user_id = 'user_test_' + os.urandom(4).hex()

        user = User(
            id=user_id,
            username='testuser',
            email='test@example.com',
            password_hash=hashlib.sha256(b'pass').hexdigest(),
            status=UserStatus.ACTIVE
        )

        db.users.create(user)
        retrieved = db.users.get_by_id(user_id)
        assert retrieved is not None

    def test_create_project(self, clean_db, authenticated_user):
        """Test creating a project"""
        from src.database import get_database

        db = get_database()
        project_id = 'proj_test_' + os.urandom(4).hex()

        project = Project(
            id=project_id,
            name='Test Project',
            owner_id=authenticated_user['id'],
            status=ProjectStatus.ACTIVE,  # Use correct enum
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        db.projects.create(project)
        retrieved = db.projects.get_by_id(project_id)
        assert retrieved is not None

    def test_create_module(self, clean_db, authenticated_user, test_project):
        """Test creating a module"""
        from src.database import get_database

        db = get_database()
        module_id = 'mod_test_' + os.urandom(4).hex()

        module = Module(
            id=module_id,
            project_id=test_project['id'],
            name='Test Module',
            status=ModuleStatus.PLANNED,  # Use correct enum
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        db.modules.create(module)
        retrieved = db.modules.get_by_id(module_id)
        assert retrieved is not None

    def test_create_task(self, clean_db, test_project):
        """Test creating a task"""
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
        task_id = 'task_test_' + os.urandom(4).hex()
        task = Task(
            id=task_id,
            module_id=module_id,
            project_id=test_project['id'],
            title='Test Task',
            status=TaskStatus.TODO,  # Use correct enum
            priority=Priority.MEDIUM,  # Use correct enum
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        db.tasks.create(task)
        retrieved = db.tasks.get_by_id(task_id)
        assert retrieved is not None


@pytest.mark.system
@pytest.mark.integration
class TestSocraticSessionModels:
    """Test Socratic session models"""

    def test_create_session(self, clean_db, authenticated_user, test_project):
        """Test creating a Socratic session"""
        from src.database import get_database

        db = get_database()
        session_id = 'sess_test_' + os.urandom(4).hex()

        session = SocraticSession(
            id=session_id,
            project_id=test_project['id'],
            user_id=authenticated_user['id'],
            current_role=TechnicalRole.PROJECT_MANAGER,  # Use correct field
            status=ConversationStatus.ACTIVE,  # Use correct enum
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        db.socratic_sessions.create(session)
        retrieved = db.socratic_sessions.get_by_id(session_id)
        assert retrieved is not None

    def test_create_conversation_message(self, clean_db, authenticated_user, test_project):
        """Test creating a conversation message"""
        from src.database import get_database

        db = get_database()

        # Create session first
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
        msg_id = 'msg_test_' + os.urandom(4).hex()
        message = ConversationMessage(
            id=msg_id,
            session_id=session_id,
            project_id=test_project['id'],
            message_type='user',
            content='Test message',
            role='user',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        db.conversation_messages.create(message)
        retrieved = db.conversation_messages.get_by_session_id(session_id)
        assert retrieved is not None


@pytest.mark.system
@pytest.mark.integration
class TestCodeGenerationModels:
    """Test code generation models"""

    def test_create_codebase(self, clean_db, authenticated_user, test_project):
        """Test creating a generated codebase"""
        from src.database import get_database

        db = get_database()
        codebase_id = 'cb_test_' + os.urandom(4).hex()

        codebase = GeneratedCodebase(
            id=codebase_id,
            project_id=test_project['id'],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        db.codebases.create(codebase)
        retrieved = db.codebases.get_by_id(codebase_id)
        assert retrieved is not None

    def test_create_generated_file(self, clean_db, test_project):
        """Test creating a generated file"""
        from src.database import get_database

        db = get_database()

        # Create codebase first
        codebase_id = 'cb_file_' + os.urandom(4).hex()
        codebase = GeneratedCodebase(
            id=codebase_id,
            project_id=test_project['id'],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.codebases.create(codebase)

        # Create file
        file_id = 'file_test_' + os.urandom(4).hex()
        file_obj = GeneratedFile(
            id=file_id,
            codebase_id=codebase_id,
            project_id=test_project['id'],
            file_path='src/main.py',
            content='print("hello")',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        db.generated_files.create(file_obj)
        retrieved = db.generated_files.get_by_id(file_id)
        assert retrieved is not None


@pytest.mark.system
@pytest.mark.integration
class TestConflictModels:
    """Test conflict models"""

    def test_create_conflict(self, clean_db, authenticated_user, test_project):
        """Test creating a conflict"""
        from src.database import get_database

        db = get_database()
        conflict_id = 'conf_test_' + os.urandom(4).hex()

        conflict = Conflict(
            id=conflict_id,
            project_id=test_project['id'],
            conflict_type=ConflictType.TECHNICAL,
            first_requirement='Requirement A',  # Use correct field names
            second_requirement='Requirement B',
            severity='high',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        db.conflicts.create(conflict)
        retrieved = db.conflicts.get_by_id(conflict_id)
        assert retrieved is not None


pytestmark = [
    pytest.mark.system,
]
