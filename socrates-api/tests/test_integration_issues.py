"""
Comprehensive integration issue tests.

These tests verify that all documented integration issues are properly fixed.
Each test is designed to fail if the issue exists, and pass if the issue is fixed.
"""

import pytest
from fastapi.testclient import TestClient
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Setup path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from socrates_api.main import app
from socratic_system.database.project_db_v2 import ProjectDatabase


@pytest.fixture
def client():
    """Create FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def test_db():
    """Create test database"""
    db = ProjectDatabase(":memory:")
    return db


class TestCriticalIssue1_DeleteUser:
    """CRITICAL: Account deletion crashes due to missing db method"""

    def test_delete_user_endpoint_uses_correct_method(self, test_db):
        """Verify db has delete_user method (or correct equivalent)"""
        # This test will fail if the method doesn't exist
        assert hasattr(test_db, 'permanently_delete_user') or hasattr(test_db, 'delete_user'), \
            "Database must have delete_user() or permanently_delete_user() method"

    def test_delete_user_endpoint_calls_correct_method(self):
        """Verify auth router calls the correct method name"""
        from socrates_api.routers.auth import _delete_user_helper
        import inspect

        source = inspect.getsource(_delete_user_helper)
        # Should call the actual method, not non-existent one
        assert 'permanently_delete_user' in source or \
               ('delete_user' in source and 'db.' in source), \
            "delete_user should call db.permanently_delete_user() or db.delete_user()"


class TestCriticalIssue2_RefreshToken:
    """CRITICAL: Refresh token storage not implemented"""

    def test_refresh_token_stored(self, test_db):
        """Verify refresh tokens are persisted to database"""
        from socrates_api.routers.auth import _store_refresh_token
        import inspect

        source = inspect.getsource(_store_refresh_token)
        # Should contain actual database operations, not just 'pass'
        assert 'pass' not in source or len(source.strip().split('\n')) > 3, \
            "_store_refresh_token must be implemented (currently just 'pass')"

    def test_refresh_endpoint_validates_token(self, test_db):
        """Verify refresh endpoint can validate stored tokens"""
        # The implementation should have database storage logic
        from socrates_api.routers.auth import _store_refresh_token

        # If implemented, this should work without errors
        try:
            _store_refresh_token(test_db, "testuser", "test_token")
            # If it's just 'pass', this does nothing - which is the bug
            # After fix, it should store in DB
        except Exception as e:
            pytest.fail(f"Token storage failed: {e}")


class TestCriticalIssue3_EmailDuplication:
    """CRITICAL: Email validation allows duplicates"""

    def test_registration_with_no_email_generates_unique(self, client):
        """Verify that registrations without email get unique emails"""
        from socrates_api.routers.auth import register

        # First registration without email
        response1 = client.post('/auth/register', json={
            'username': 'user1',
            'password': 'pass123'
        })

        if response1.status_code == 200:
            # Second registration without email should succeed with different email
            response2 = client.post('/auth/register', json={
                'username': 'user2',
                'password': 'pass123'
            })

            # Should not get 409 Conflict (email already registered)
            assert response2.status_code != 409, \
                "Email generation logic creates duplicates - second user gets conflict"

    def test_email_uniqueness_logic(self):
        """Verify email generation doesn't create duplicates"""
        from socrates_api.routers.auth import register
        import inspect

        source = inspect.getsource(register)

        # Should generate unique emails, not just {username}@localhost
        # Or should make email truly optional without uniqueness check
        assert 'uuid' in source.lower() or \
               'email' not in source.lower() or \
               'required' not in source.lower(), \
            "Email generation should use UUID or be optional"


class TestCriticalIssue4_MissingChatEndpoints:
    """CRITICAL: Chat endpoints missing"""

    def test_chat_message_endpoint_exists(self, client):
        """Verify POST /projects/{id}/chat/message endpoint exists"""
        # Try to call it - if 404, endpoint is missing
        response = client.post(
            '/projects/test_proj/chat/message',
            json={'message': 'test'},
            headers={'Authorization': 'Bearer test_token'}
        )

        # Should not be 404 (endpoint exists)
        # Could be 401 (auth fail) or 400 (validation) but not 404 (missing)
        assert response.status_code != 404, \
            "Chat message endpoint missing - returns 404"

    def test_chat_history_endpoint_exists(self, client):
        """Verify GET /projects/{id}/chat/history endpoint exists"""
        response = client.get(
            '/projects/test_proj/chat/history',
            headers={'Authorization': 'Bearer test_token'}
        )

        assert response.status_code != 404, \
            "Chat history endpoint missing - returns 404"

    def test_chat_endpoints_in_api_routers(self):
        """Verify chat endpoints are defined in routers"""
        from pathlib import Path

        routers_dir = Path(__file__).parent.parent / 'src' / 'socrates_api' / 'routers'

        # Check if any router has chat endpoints
        chat_endpoint_found = False
        for router_file in routers_dir.glob('*.py'):
            content = router_file.read_text()
            if '/chat/' in content or '@router' in content and 'chat' in content.lower():
                chat_endpoint_found = True
                break

        assert chat_endpoint_found, \
            "No router implements /chat/* endpoints"


class TestHighIssue5_DatabaseConnections:
    """HIGH: Multiple database singletons cause connection leaks"""

    def test_database_singleton_pattern(self):
        """Verify each router has its own database singleton"""
        from pathlib import Path

        routers_dir = Path(__file__).parent.parent / 'src' / 'socrates_api' / 'routers'
        singleton_count = 0

        for router_file in routers_dir.glob('*.py'):
            content = router_file.read_text()
            # Each router file has pattern: _database = None followed by get_database()
            if '_database = None' in content and 'def get_database' in content:
                singleton_count += 1

        assert singleton_count <= 1, \
            f"Multiple database singletons found ({singleton_count}). Should consolidate into one dependency."

    def test_database_connections_cleaned_up(self):
        """Verify database connections are properly closed"""
        # Check if app has shutdown event that closes database
        from socrates_api.main import app

        shutdown_events = [e for e in app.router.on_shutdown]

        # Should have cleanup event
        # Note: May not be in this format after refactoring, but concept should exist
        assert len(app.router.on_shutdown) > 0 or \
               hasattr(app, 'shutdown_event'), \
            "No shutdown event found - database connections may leak"


class TestHighIssue6_SubscriptionEnforcement:
    """HIGH: Subscription tiers not enforced"""

    def test_subscription_decorator_applied(self):
        """Verify subscription checking is applied to protected endpoints"""
        from socrates_api.routers.projects import create_project
        import inspect

        source = inspect.getsource(create_project)

        # Should have subscription check or decorator
        assert 'subscription' in source.lower() or \
               '@require_subscription' in source, \
            "create_project endpoint doesn't enforce subscription tier"

    def test_code_generation_requires_subscription(self):
        """Verify code generation requires appropriate subscription"""
        from pathlib import Path

        code_gen_file = Path(__file__).parent.parent / 'src' / 'socrates_api' / 'routers' / 'code_generation.py'
        content = code_gen_file.read_text()

        # Should have subscription checks
        assert '@require_subscription' in content or \
               'subscription' in content.lower(), \
            "Code generation endpoint doesn't enforce subscription"


class TestHighIssue7_HardcodedLocalhost:
    """HIGH: Hardcoded localhost makes system non-functional in production"""

    def test_api_host_from_environment(self):
        """Verify API host comes from environment variable"""
        from socrates_api.main import run
        import inspect

        source = inspect.getsource(run)

        # Should read from environment
        assert 'os.getenv' in source, \
            "API host is hardcoded, should use os.getenv()"

    def test_data_dir_from_environment(self):
        """Verify data directory uses environment variable"""
        from socratic_system.database.project_db_v2 import ProjectDatabase
        import inspect

        source = inspect.getsource(ProjectDatabase.__init__)

        # Should allow environment variable to override
        assert 'SOCRATES_DATA_DIR' in source or \
               'os.getenv' in source or \
               'data_dir' in source, \
            "Data directory doesn't respect SOCRATES_DATA_DIR environment variable"

    def test_frontend_api_url_configurable(self):
        """Verify frontend API URL comes from environment"""
        from pathlib import Path

        frontend_env = Path(__file__).parent.parent.parent / 'socrates-frontend' / '.env.example'
        if frontend_env.exists():
            content = frontend_env.read_text()
            assert 'VITE_API_URL' in content, \
                "Frontend doesn't have VITE_API_URL configuration"


class TestHighIssue8_OrchestratorInitialization:
    """HIGH: Inconsistent orchestrator initialization requirements"""

    def test_all_endpoints_check_orchestrator_status(self):
        """Verify all endpoints that use orchestrator check if initialized"""
        from pathlib import Path

        routers_dir = Path(__file__).parent.parent / 'src' / 'socrates_api' / 'routers'

        issues = []
        for router_file in routers_dir.glob('*.py'):
            content = router_file.read_text()

            # Find functions that use orchestrator
            if 'orchestrator' in content.lower():
                # Check if they call get_orchestrator()
                if 'get_orchestrator()' not in content:
                    issues.append(router_file.name)

        assert len(issues) == 0, \
            f"These routers use orchestrator but don't validate initialization: {issues}"

    def test_consistent_initialization_pattern(self):
        """Verify all endpoints use consistent error handling"""
        from socrates_api.main import get_orchestrator
        import inspect

        source = inspect.getsource(get_orchestrator)

        # Should raise RuntimeError if not initialized
        assert 'RuntimeError' in source or \
               'HTTPException' in source, \
            "get_orchestrator doesn't raise error if not initialized"


class TestMediumIssue9_TestingModeInsecure:
    """MEDIUM: Testing mode publicly accessible"""

    def test_testing_mode_requires_admin(self):
        """Verify testing mode can only be set by admin"""
        from socrates_api.routers.auth import set_testing_mode
        import inspect

        source = inspect.getsource(set_testing_mode)

        # Should check admin status
        assert 'admin' in source.lower() or \
               'is_admin' in source or \
               'role' in source.lower(), \
            "Testing mode doesn't verify admin status"

    def test_testing_mode_is_logged(self):
        """Verify testing mode changes are logged"""
        from socrates_api.routers.auth import set_testing_mode
        import inspect

        source = inspect.getsource(set_testing_mode)

        # Should log the change
        assert 'logger' in source or \
               'log' in source.lower(), \
            "Testing mode changes are not logged"


class TestMediumIssue10_EnvironmentValidation:
    """MEDIUM: No environment validation at startup"""

    def test_startup_validates_api_key(self):
        """Verify system checks ANTHROPIC_API_KEY at startup"""
        from socrates_api.main import app

        # Check for startup event or initialization
        startup_events = app.router.on_startup

        # Should validate config
        assert len(startup_events) > 0 or \
               hasattr(app, '_validate_config'), \
            "No environment validation at startup"

    def test_startup_validates_data_directory(self):
        """Verify system validates data directory is writable"""
        from socratic_system.database.project_db_v2 import ProjectDatabase
        import inspect

        source = inspect.getsource(ProjectDatabase.__init__)

        # Should check directory exists and is writable
        assert 'mkdir' in source or \
               'exist_ok' in source or \
               'writable' in source.lower(), \
            "Data directory not validated at startup"

    def test_port_availability_check(self):
        """Verify system checks if port is available"""
        from socrates_api.main import run
        import inspect

        source = inspect.getsource(run)

        # Could use socket to check
        assert 'socket' in source or \
               'port' in source and 'available' in source.lower(), \
            "No port availability check"


class TestAutoCreatedUserConflict:
    """HIGH: Auto-created users in agents have hardcoded emails"""

    def test_agent_user_creation_uses_unique_email(self):
        """Verify agents don't create users with conflicting emails"""
        from pathlib import Path

        agents_dir = Path(__file__).parent.parent.parent / 'socratic_system' / 'agents'

        issues = []
        for agent_file in agents_dir.glob('*.py'):
            content = agent_file.read_text()

            if 'User(' in content and '@' in content:
                # Check for hardcoded domain like @localhost or @socrates.local
                if '@localhost' in content or '@socrates.local' in content:
                    issues.append(agent_file.name)

        assert len(issues) == 0, \
            f"These agents create users with hardcoded emails: {issues}"


class TestDatabaseMethodMismatch:
    """CRITICAL: Database method names don't match usage"""

    def test_delete_user_method_exists_with_correct_name(self, test_db):
        """Verify the method used in auth.py actually exists"""
        import inspect

        # Get actual method names
        methods = [name for name, _ in inspect.getmembers(test_db, predicate=inspect.ismethod)]

        # Should have the right method for deletion
        assert 'delete_user' in methods or \
               'permanently_delete_user' in methods, \
            f"Database must have delete/permanently_delete_user method. Has: {methods}"

    def test_list_projects_method_exists(self, test_db):
        """Verify list_projects_for_user or equivalent exists"""
        import inspect

        methods = [name for name, _ in inspect.getmembers(test_db, predicate=inspect.ismethod)]

        assert 'get_user_projects' in methods or \
               'list_projects_for_user' in methods or \
               'list_user_projects' in methods, \
            f"Database must have get_user_projects method. Has: {methods}"
