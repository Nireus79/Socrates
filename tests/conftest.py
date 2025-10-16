"""
Pytest Configuration and Shared Fixtures
=========================================

Centralized pytest configuration, fixtures, and setup/teardown hooks
for the Socratic RAG Enhanced test suite.

This module provides:
- Database isolation fixtures
- Flask test client fixture
- Authenticated user fixtures
- Mock services
- Custom markers for test categorization
"""

import pytest
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "ui: mark test as UI/web test")
    config.addinivalue_line("markers", "system: mark test as system/end-to-end test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "workflow: mark test as workflow test")
    config.addinivalue_line("markers", "performance: mark test as performance test")


@pytest.fixture(scope="function")
def clean_db():
    """
    Fixture providing a clean database for each test.

    Ensures database isolation by:
    1. Deleting existing database file
    2. Initializing fresh database
    3. Resetting singleton instances

    Yields:
        Database manager instance with clean state
    """
    import os
    from src.database import init_database, reset_database, get_database

    db_path = 'data/socratic.db'

    # Clean up before test
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError:
            pass

    # Reset singletons
    reset_database()

    # Initialize fresh database
    init_database()

    # Get database instance
    db = get_database()

    yield db

    # Clean up after test
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError:
            pass

    reset_database()


@pytest.fixture(scope="function")
def app_client(clean_db):
    """
    Fixture providing a Flask test client.

    Yields:
        Flask test client for making HTTP requests
    """
    from web.app import create_app

    app = create_app()
    app.config['TESTING'] = True

    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture(scope="function")
def authenticated_user(clean_db):
    """
    Fixture providing a pre-authenticated test user.

    Creates a test user and returns user data.

    Yields:
        Dict containing: {
            'id': user_id,
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
    """
    from src.database import get_database
    from src.models import User, UserStatus
    import hashlib

    db = get_database()

    # Create test user
    user_id = 'user_test_' + os.urandom(4).hex()
    username = 'testuser'
    email = 'test@example.com'
    password = 'testpass123'
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    # Add user to database using model object
    user_obj = User(
        id=user_id,
        username=username,
        email=email,
        password_hash=password_hash,
        status=UserStatus.ACTIVE
    )
    db.users.create(user_obj)

    yield {
        'id': user_id,
        'username': username,
        'email': email,
        'password': password,
        'user_obj': user_obj
    }


@pytest.fixture(scope="function")
def authenticated_session(app_client, authenticated_user):
    """
    Fixture providing a Flask test client with authenticated session.

    Logs in the test user and returns client with session.

    Yields:
        Tuple of (client, authenticated_user_data)
    """
    user_data = authenticated_user

    # Login user
    app_client.post('/login', data={
        'username': user_data['username'],
        'password': user_data['password']
    })

    yield app_client, user_data


@pytest.fixture(scope="function")
def test_project(clean_db, authenticated_user):
    """
    Fixture providing a test project for authenticated user.

    Yields:
        Dict containing project data: {
            'id': project_id,
            'name': 'Test Project',
            'owner_id': authenticated_user['id'],
            ...
        }
    """
    from src.database import get_database
    from src.models import Project, ProjectStatus
    from datetime import datetime

    db = get_database()

    project_id = 'proj_test_' + os.urandom(4).hex()

    project_obj = Project(
        id=project_id,
        name='Test Project',
        description='Test project for unit tests',
        owner_id=authenticated_user['id'],
        status=ProjectStatus.ACTIVE,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    db.projects.create(project_obj)

    yield {
        'id': project_id,
        'name': 'Test Project',
        'description': 'Test project for unit tests',
        'owner_id': authenticated_user['id'],
        'status': 'planning',
        'project_type': 'web_application'
    }


@pytest.fixture(scope="function")
def test_session_data(clean_db, authenticated_user, test_project):
    """
    Fixture providing test data for Socratic session.

    Yields:
        Dict containing session data with project and user info
    """
    from src.database import get_database
    from src.models import SocraticSession, SocraticSessionStatus  # TODO Cannot find reference 'SocraticSessionStatus' in 'models.py'
    from datetime import datetime

    db = get_database()

    session_id = 'sess_test_' + os.urandom(4).hex()

    session_obj = SocraticSession(
        id=session_id,
        project_id=test_project['id'],
        user_id=authenticated_user['id'],
        role='developer',  # TODO Unexpected argument
        status=SocraticSessionStatus.IN_PROGRESS,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    db.socratic_sessions.create(session_obj)

    yield {
        'id': session_id,
        'project_id': test_project['id'],
        'user_id': authenticated_user['id'],
        'role': 'developer',
        'status': 'in_progress'
    }


@pytest.fixture(scope="function")
def mock_services():
    """
    Fixture providing mock services for testing.

    Yields:
        Dict containing mock service instances
    """
    from unittest.mock import MagicMock

    services = {
        'logger': MagicMock(),
        'config': MagicMock(),
        'event_system': MagicMock(),
        'claude_service': MagicMock(),
        'git_service': MagicMock(),
        'ide_service': MagicMock(),
        'vector_service': MagicMock()
    }

    yield services


@pytest.fixture(scope="session")
def test_data_dir():
    """
    Fixture providing path to test data directory.

    Yields:
        Path to tests/data directory
    """
    test_dir = Path(__file__).parent / 'data'
    test_dir.mkdir(exist_ok=True)
    yield test_dir


# Custom assertions and helpers

class TestDataBuilder:
    """Helper class for building test data."""

    @staticmethod
    def create_user(db, username='testuser', email='test@example.com'):
        """Create a test user."""
        from src.models import User, UserStatus
        import hashlib
        user_id = 'user_' + os.urandom(4).hex()
        password_hash = hashlib.sha256('password123'.encode()).hexdigest()

        user_obj = User(
            id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            status=UserStatus.ACTIVE
        )
        db.users.create(user_obj)
        return user_obj

    @staticmethod
    def create_project(db, owner_id, name='Test Project'):
        """Create a test project."""
        from src.models import Project, ProjectStatus
        from datetime import datetime
        project_id = 'proj_' + os.urandom(4).hex()

        project_obj = Project(
            id=project_id,
            name=name,
            description=f'Test project: {name}',
            owner_id=owner_id,
            status=ProjectStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.projects.create(project_obj)
        return project_obj

    @staticmethod
    def create_module(db, project_id, name='Test Module'):
        """Create a test module."""
        from src.models import Module, ModuleStatus
        from datetime import datetime
        module_id = 'mod_' + os.urandom(4).hex()

        module_obj = Module(
            id=module_id,
            project_id=project_id,
            name=name,
            description=f'Test module: {name}',
            status=ModuleStatus.PENDING,  # TODO Unresolved attribute reference 'PENDING' for class 'ModuleStatus'
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.modules.create(module_obj)
        return module_obj

    @staticmethod
    def create_task(db, module_id, title='Test Task'):
        """Create a test task."""
        from src.models import Task, TaskStatus, TaskPriority
        from datetime import datetime
        task_id = 'task_' + os.urandom(4).hex()

        task_obj = Task(
            id=task_id,
            module_id=module_id,
            title=title,
            description=f'Test task: {title}',
            status=TaskStatus.PENDING,  # TODO Unresolved attribute reference 'PENDING' for class 'TaskStatus'
            priority=TaskPriority.MEDIUM,  # TODO Expected type 'Priority', got 'TaskPriority' instead
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.tasks.create(task_obj)
        return task_obj


@pytest.fixture
def data_builder(clean_db):
    """Fixture providing test data builder."""
    from src.database import get_database
    db = get_database()

    builder = TestDataBuilder()
    # Inject database
    builder.db = db

    yield builder


# Logging configuration for tests

@pytest.fixture(autouse=True)
def setup_test_logging(caplog):
    """Auto-use fixture to configure logging for tests."""
    import logging

    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    yield caplog


# Error reporting

def pytest_runtest_logreport(report):
    """Hook to enhance test report output."""
    if report.when == "call" and report.outcome == "failed":
        # Could add custom error reporting here
        pass
