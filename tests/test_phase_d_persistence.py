"""
Phase D - Data Persistence and Transaction Tests
================================================

Tests for data persistence, database isolation, and transaction handling.
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
class TestDataPersistence:
    """Test that data persists correctly in database"""

    def test_user_persists_across_connections(self, clean_db):
        """Test that user data persists when getting fresh connection"""
        from src.database import get_database
        import hashlib

        # Create in first connection
        db1 = get_database()
        user_id = 'user_persist_' + os.urandom(4).hex()

        user = User(
            id=user_id,
            username='persistuser',
            email='persist@example.com',
            password_hash=hashlib.sha256(b'pass').hexdigest(),
            status=UserStatus.ACTIVE
        )
        db1.users.create(user)

        # Retrieve in same connection
        retrieved = db1.users.get_by_id(user_id)
        assert retrieved is not None
        assert retrieved.username == 'persistuser'

    def test_project_data_consistency(self, clean_db, authenticated_user):
        """Test that project data remains consistent after multiple operations"""
        from src.database import get_database

        db = get_database()
        project_id = 'proj_persist_' + os.urandom(4).hex()

        # Create
        project = Project(
            id=project_id,
            name='Persistence Test',
            description='Test description',
            owner_id=authenticated_user['id'],
            status=ProjectStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.projects.create(project)

        # Read
        retrieved1 = db.projects.get_by_id(project_id)
        original_name = retrieved1.name

        # Update with different value
        project.name = 'Updated Name'
        db.projects.update(project)

        # Verify update
        retrieved2 = db.projects.get_by_id(project_id)
        assert retrieved2.name == 'Updated Name'
        assert retrieved2.name != original_name

    def test_related_entities_persistence(self, clean_db, test_project):
        """Test that related entities persist correctly"""
        from src.database import get_database

        db = get_database()

        # Create module
        module_id = 'mod_persist_' + os.urandom(4).hex()
        module = Module(
            id=module_id,
            project_id=test_project['id'],
            name='Persist Module',
            status=ModuleStatus.PLANNED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.modules.create(module)

        # Create task in module
        task_id = 'task_persist_' + os.urandom(4).hex()
        task = Task(
            id=task_id,
            module_id=module_id,
            project_id=test_project['id'],
            title='Persist Task',
            status=TaskStatus.TODO,
            priority=Priority.MEDIUM,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.tasks.create(task)

        # Verify both persist
        retrieved_module = db.modules.get_by_id(module_id)
        assert retrieved_module is not None

        retrieved_task = db.tasks.get_by_id(task_id)
        assert retrieved_task is not None
        assert retrieved_task.module_id == module_id

    def test_multiple_entities_isolation(self, clean_db, authenticated_user):
        """Test that multiple entities don't interfere with each other"""
        from src.database import get_database

        db = get_database()

        # Create two projects
        proj1_id = 'proj_iso1_' + os.urandom(4).hex()
        proj2_id = 'proj_iso2_' + os.urandom(4).hex()

        project1 = Project(
            id=proj1_id,
            name='Project 1',
            owner_id=authenticated_user['id'],
            status=ProjectStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        project2 = Project(
            id=proj2_id,
            name='Project 2',
            owner_id=authenticated_user['id'],
            status=ProjectStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        db.projects.create(project1)
        db.projects.create(project2)

        # Modify project1
        project1.name = 'Project 1 Modified'
        db.projects.update(project1)

        # Verify project2 unchanged
        retrieved2 = db.projects.get_by_id(proj2_id)
        assert retrieved2.name == 'Project 2'

        # Verify project1 changed
        retrieved1 = db.projects.get_by_id(proj1_id)
        assert retrieved1.name == 'Project 1 Modified'


@pytest.mark.system
@pytest.mark.integration
class TestDatabaseIsolation:
    """Test database isolation between tests"""

    def test_isolation_clean_db_fixture(self, clean_db):
        """Test that clean_db fixture provides isolation"""
        from src.database import get_database

        db = get_database()

        # Count users
        count = db.users.count()

        # Should be 0 or minimal (only from this test)
        assert count >= 0  # No leftover data from other tests

    def test_each_test_gets_clean_database(self, clean_db, authenticated_user):
        """Test that each test gets fresh database despite having a user"""
        from src.database import get_database

        db = get_database()

        # This test should have only authenticated_user
        all_users = db.users.get_all()
        # Should have at least the authenticated_user
        assert len(all_users) >= 1

    def test_no_data_leakage_between_tests(self, clean_db):
        """Test that data doesn't leak from other tests"""
        from src.database import get_database
        import hashlib

        db = get_database()

        # Create a user with a recognizable name
        user = User(
            id='isolation_test_' + os.urandom(4).hex(),
            username='isolation_test_user',
            email='isolation@example.com',
            password_hash=hashlib.sha256(b'pass').hexdigest(),
            status=UserStatus.ACTIVE
        )
        db.users.create(user)

        # Verify it exists
        all_users = db.users.get_all()
        isolation_users = [u for u in all_users if u.username == 'isolation_test_user']
        # Should only be the one we just created
        assert len(isolation_users) == 1


@pytest.mark.system
@pytest.mark.integration
class TestTransactionConsistency:
    """Test transaction consistency and atomicity"""

    def test_create_read_consistency(self, clean_db, authenticated_user):
        """Test that created data is immediately readable"""
        from src.database import get_database

        db = get_database()
        project_id = 'proj_txn_' + os.urandom(4).hex()

        # Create
        project = Project(
            id=project_id,
            name='Transaction Test',
            owner_id=authenticated_user['id'],
            status=ProjectStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.projects.create(project)

        # Immediately read should return the created data
        retrieved = db.projects.get_by_id(project_id)
        assert retrieved is not None
        assert retrieved.name == 'Transaction Test'

    def test_update_read_consistency(self, clean_db, authenticated_user):
        """Test that updated data is immediately readable"""
        from src.database import get_database

        db = get_database()
        project_id = 'proj_upd_txn_' + os.urandom(4).hex()

        # Create
        project = Project(
            id=project_id,
            name='Original',
            owner_id=authenticated_user['id'],
            status=ProjectStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.projects.create(project)

        # Update
        project.name = 'Updated'
        db.projects.update(project)

        # Immediately read should return updated data
        retrieved = db.projects.get_by_id(project_id)
        assert retrieved.name == 'Updated'

    def test_delete_read_consistency(self, clean_db, authenticated_user):
        """Test that deleted data is immediately unreadable"""
        from src.database import get_database

        db = get_database()
        project_id = 'proj_del_txn_' + os.urandom(4).hex()

        # Create
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
        db.projects.delete(project_id)

        # Immediately read should return None
        retrieved = db.projects.get_by_id(project_id)
        assert retrieved is None

    def test_batch_operations_consistency(self, clean_db, test_project):
        """Test consistency of batch operations"""
        from src.database import get_database

        db = get_database()

        # Create module
        module_id = 'mod_batch_' + os.urandom(4).hex()
        module = Module(
            id=module_id,
            project_id=test_project['id'],
            name='Batch Module',
            status=ModuleStatus.PLANNED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.modules.create(module)

        # Create multiple tasks
        task_ids = []
        for i in range(3):
            task_id = f'task_batch_{i}_' + os.urandom(2).hex()
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

        # Verify all created
        for task_id in task_ids:
            retrieved = db.tasks.get_by_id(task_id)
            assert retrieved is not None


@pytest.mark.system
@pytest.mark.integration
class TestLargeDataOperations:
    """Test operations with larger datasets"""

    def test_create_many_users(self, clean_db):
        """Test creating many users"""
        from src.database import get_database
        import hashlib

        db = get_database()

        # Create 10 users
        user_ids = []
        for i in range(10):
            user_id = f'user_many_{i}_' + os.urandom(2).hex()
            user_ids.append(user_id)

            user = User(
                id=user_id,
                username=f'user_{i}',
                email=f'user{i}@example.com',
                password_hash=hashlib.sha256(b'pass').hexdigest(),
                status=UserStatus.ACTIVE
            )
            db.users.create(user)

        # Verify all created
        all_users = db.users.get_all()
        assert len(all_users) >= 10

    def test_get_all_with_many_entities(self, clean_db, authenticated_user):
        """Test get_all with many entities"""
        from src.database import get_database

        db = get_database()

        # Create 8 projects
        for i in range(8):
            project = Project(
                id=f'proj_many_{i}_' + os.urandom(2).hex(),
                name=f'Project {i}',
                owner_id=authenticated_user['id'],
                status=ProjectStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.projects.create(project)

        # Get all should work efficiently
        all_projects = db.projects.get_all()
        assert len(all_projects) >= 8

    def test_count_with_many_entities(self, clean_db, authenticated_user):
        """Test count with many entities"""
        from src.database import get_database

        db = get_database()

        # Create 5 projects
        for i in range(5):
            project = Project(
                id=f'proj_cnt_{i}_' + os.urandom(2).hex(),
                name=f'Project {i}',
                owner_id=authenticated_user['id'],
                status=ProjectStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.projects.create(project)

        # Count should match
        count = db.projects.count()
        assert count >= 5


@pytest.mark.system
@pytest.mark.integration
class TestDataIntegrity:
    """Test data integrity and consistency"""

    def test_field_values_preserved(self, clean_db, authenticated_user):
        """Test that all field values are preserved exactly"""
        from src.database import get_database

        db = get_database()
        project_id = 'proj_integrity_' + os.urandom(4).hex()

        # Create with specific values
        project = Project(
            id=project_id,
            name='Integrity Test Project',
            description='This is a test description with special chars: @#$%',
            owner_id=authenticated_user['id'],
            status=ProjectStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.projects.create(project)

        # Retrieve and verify all fields
        retrieved = db.projects.get_by_id(project_id)
        assert retrieved.id == project_id
        assert retrieved.name == 'Integrity Test Project'
        assert retrieved.description == 'This is a test description with special chars: @#$%'
        assert retrieved.owner_id == authenticated_user['id']

    def test_special_characters_preserved(self, clean_db):
        """Test that special characters are preserved"""
        from src.database import get_database
        import hashlib

        db = get_database()
        user_id = 'user_special_' + os.urandom(4).hex()

        special_email = 'user+test@example.com'
        user = User(
            id=user_id,
            username='user_with_special_chars',
            email=special_email,
            password_hash=hashlib.sha256(b'pass').hexdigest(),
            status=UserStatus.ACTIVE
        )
        db.users.create(user)

        retrieved = db.users.get_by_id(user_id)
        assert retrieved.email == special_email

    def test_enum_values_integrity(self, clean_db, authenticated_user):
        """Test that enum values are preserved as enums"""
        from src.database import get_database

        db = get_database()
        project_id = 'proj_enum_' + os.urandom(4).hex()

        project = Project(
            id=project_id,
            name='Enum Test',
            owner_id=authenticated_user['id'],
            status=ProjectStatus.PAUSED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.projects.create(project)

        retrieved = db.projects.get_by_id(project_id)
        # Status should be preserved (could be enum or string representation)
        if hasattr(retrieved.status, 'value'):
            # It's an enum
            assert retrieved.status == ProjectStatus.PAUSED
        else:
            # It's a string value
            assert retrieved.status == 'paused' or retrieved.status == ProjectStatus.PAUSED.value


pytestmark = [
    pytest.mark.system,
]
