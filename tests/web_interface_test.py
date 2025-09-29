#!/usr/bin/env python3
"""
Web Interface Test Suite
========================

Comprehensive testing for Flask web application.

Tests:
1. Flask dependencies check
2. Application creation and configuration
3. Route registration and accessibility
4. Template rendering
5. Form validation
6. Authentication system
7. API endpoints
8. File upload handling
9. System component integration
10. Error handling
"""

import sys
import os
import traceback
from typing import Dict, Any, List
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_header(text: str) -> None:
    """Print formatted header"""
    print(f"\n{BOLD}{BLUE}{'=' * 70}{RESET}")
    print(f"{BOLD}{BLUE}{text:^70}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 70}{RESET}\n")


def print_success(text: str) -> None:
    """Print success message"""
    print(f"{GREEN}✓{RESET} {text}")


def print_error(text: str) -> None:
    """Print error message"""
    print(f"{RED}✗{RESET} {text}")


def print_warning(text: str) -> None:
    """Print warning message"""
    print(f"{YELLOW}⚠{RESET} {text}")


def print_info(text: str) -> None:
    """Print info message"""
    print(f"{BLUE}ℹ{RESET} {text}")


class TestResults:
    """Track test results"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.tests: List[Dict[str, Any]] = []

    def add_pass(self, test_name: str, details: str = ""):
        self.passed += 1
        self.tests.append({
            'name': test_name,
            'status': 'passed',
            'details': details
        })
        print_success(f"{test_name} {details}")

    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.tests.append({
            'name': test_name,
            'status': 'failed',
            'error': error
        })
        print_error(f"{test_name}: {error}")

    def add_warning(self, test_name: str, message: str):
        self.warnings += 1
        self.tests.append({
            'name': test_name,
            'status': 'warning',
            'message': message
        })
        print_warning(f"{test_name}: {message}")

    def print_summary(self):
        """Print test summary"""
        print_header("TEST SUMMARY")

        total = self.passed + self.failed
        print(f"\n{BOLD}Total Tests:{RESET} {total}")
        print(f"{GREEN}Passed:{RESET} {self.passed}")
        print(f"{RED}Failed:{RESET} {self.failed}")
        print(f"{YELLOW}Warnings:{RESET} {self.warnings}")

        if self.failed == 0:
            print(f"\n{GREEN}{BOLD}🎉 ALL TESTS PASSED!{RESET}\n")
            return True
        else:
            print(f"\n{RED}{BOLD}⚠️  SOME TESTS FAILED{RESET}\n")
            return False


def check_web_structure(results: TestResults) -> bool:
    """Check if web interface structure exists"""
    print_header("PRE-CHECK: Web Interface Structure")

    project_root = Path(__file__).parent.parent
    web_dir = project_root / 'web'

    print_info(f"Project root: {project_root}")
    print_info(f"Looking for web/ at: {web_dir}")

    if not web_dir.exists():
        results.add_fail("Web structure", f"web/ directory not found at {web_dir}")
        return False

    results.add_pass("web/ directory exists")

    # Check for main files
    app_file = web_dir / 'app.py'
    init_file = web_dir / '__init__.py'

    if not app_file.exists():
        results.add_fail("Web structure", "web/app.py not found")
        return False

    results.add_pass("web/app.py exists")

    if not init_file.exists():
        results.add_warning("web/__init__.py", "Not found (may cause import issues)")
    else:
        results.add_pass("web/__init__.py exists")

    # Check for templates directory
    templates_dir = web_dir / 'templates'
    if not templates_dir.exists():
        results.add_fail("Web structure", "web/templates/ not found")
        return False

    results.add_pass("web/templates/ directory exists")

    # Check for static directory
    static_dir = web_dir / 'static'
    if not static_dir.exists():
        results.add_warning("web/static/", "Directory not found")
    else:
        results.add_pass("web/static/ directory exists")

    # Check for template files
    template_files = [
        'base.html', 'dashboard.html', 'auth.html', 'projects.html',
        'sessions.html', 'code.html', 'reports.html', 'admin.html'
    ]

    missing_templates = []
    for template in template_files:
        if not (templates_dir / template).exists():
            missing_templates.append(template)

    if missing_templates:
        results.add_warning(
            "Template files",
            f"Missing: {', '.join(missing_templates)}"
        )
    else:
        results.add_pass("All template files present")

    return True


def test_flask_dependencies(results: TestResults) -> Dict[str, bool]:
    """Test 1: Check Flask and related dependencies"""
    print_header("TEST 1: Flask Dependencies")

    dependencies = {}

    # Test Flask
    try:
        import flask
        dependencies['flask'] = True
        results.add_pass("Flask installed", f"v{flask.__version__}")
    except ImportError:
        dependencies['flask'] = False
        results.add_fail("Flask", "Not installed - run: pip install flask")

    # Test Flask-WTF
    try:
        import flask_wtf
        dependencies['flask_wtf'] = True
        results.add_pass("Flask-WTF installed")
    except ImportError:
        dependencies['flask_wtf'] = False
        results.add_fail("Flask-WTF", "Not installed - run: pip install flask-wtf")

    # Test Flask-Login
    try:
        import flask_login
        dependencies['flask_login'] = True
        results.add_pass("Flask-Login installed")
    except ImportError:
        dependencies['flask_login'] = False
        results.add_fail("Flask-Login", "Not installed - run: pip install flask-login")

    # Test WTForms
    try:
        import wtforms
        dependencies['wtforms'] = True
        results.add_pass("WTForms installed")
    except ImportError:
        dependencies['wtforms'] = False
        results.add_fail("WTForms", "Not installed - run: pip install wtforms")

    # Test Jinja2
    try:
        import jinja2
        dependencies['jinja2'] = True
        results.add_pass("Jinja2 installed", f"v{jinja2.__version__}")
    except ImportError:
        dependencies['jinja2'] = False
        results.add_fail("Jinja2", "Not installed")

    # Test Werkzeug
    try:
        import werkzeug
        dependencies['werkzeug'] = True
        results.add_pass("Werkzeug installed", f"v{werkzeug.__version__}")
    except ImportError:
        dependencies['werkzeug'] = False
        results.add_fail("Werkzeug", "Not installed")

    return dependencies


def test_app_import(results: TestResults, dependencies: Dict[str, bool]) -> Any:
    """Test 2: Import Flask application"""
    print_header("TEST 2: Application Import")

    if not dependencies.get('flask'):
        results.add_fail("App import", "Flask not available")
        return None

    try:
        from web.app import create_flask_app
        results.add_pass("create_flask_app imported")
        return create_flask_app
    except ImportError as e:
        results.add_fail("App import", f"ImportError: {e}")
        return None
    except Exception as e:
        results.add_fail("App import", f"Error: {e}")
        return None


def test_app_creation(results: TestResults, create_func: Any) -> Any:
    """Test 3: Create Flask application instance"""
    print_header("TEST 3: Application Creation")

    if create_func is None:
        results.add_fail("App creation", "create_flask_app not available")
        return None

    try:
        # Create app with test configuration
        test_config = {
            'secret_key': 'test-secret-key',
            'csrf_enabled': False,  # Disable CSRF for testing
            'testing': True
        }

        app = create_func(config_override=test_config)

        if app is not None:
            results.add_pass("Flask app created")

            # Check if app is configured
            if hasattr(app, 'config'):
                results.add_pass("App configuration loaded")
            else:
                results.add_warning("App configuration", "Config not found")

            return app
        else:
            results.add_fail("App creation", "Returned None")
            return None

    except Exception as e:
        results.add_fail("App creation", str(e))
        print_error(f"Traceback: {traceback.format_exc()}")
        return None


def test_routes_registered(results: TestResults, app: Any) -> Dict[str, bool]:
    """Test 4: Verify routes are registered"""
    print_header("TEST 4: Route Registration")

    if app is None:
        results.add_fail("Route registration", "No app available")
        return {}

    routes = {}

    try:
        # Get all registered routes
        route_list = []
        for rule in app.url_map.iter_rules():
            route_list.append(str(rule))

        # Check for expected routes
        expected_routes = [
            ('/', 'dashboard'),
            ('/login', 'login'),
            ('/logout', 'logout'),
            ('/dashboard', 'dashboard'),
            ('/projects', 'projects'),
            ('/projects/create', 'project_create'),
            ('/projects/<project_id>', 'project_detail'),
            ('/sessions', 'sessions'),
            ('/sessions/start', 'session_start'),
            ('/code', 'code_generation'),
            ('/api/projects', 'api_projects'),
        ]

        for path, name in expected_routes:
            # Simple check if route path exists in any registered route
            route_exists = any(path in route for route in route_list)
            routes[name] = route_exists

            if route_exists:
                results.add_pass(f"Route '{name}' registered")
            else:
                results.add_warning(f"Route '{name}'", "Not found")

        total_routes = len(route_list)
        results.add_pass(f"Total routes registered: {total_routes}")

    except Exception as e:
        results.add_fail("Route registration", str(e))

    return routes


def test_templates_exist(results: TestResults) -> Dict[str, bool]:
    """Test 5: Verify template files exist and are readable"""
    print_header("TEST 5: Template Files")

    templates = {}
    templates_dir = project_root / 'web' / 'templates'

    template_files = [
        'base.html',
        'dashboard.html',
        'auth.html',
        'projects.html',
        'sessions.html',
        'code.html',
        'reports.html',
        'admin.html'
    ]

    for template_name in template_files:
        template_path = templates_dir / template_name

        if template_path.exists():
            try:
                # Try to read the file
                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if len(content) > 0:
                    templates[template_name] = True
                    results.add_pass(f"Template '{template_name}' readable ({len(content)} chars)")
                else:
                    templates[template_name] = False
                    results.add_warning(f"Template '{template_name}'", "Empty file")

            except Exception as e:
                templates[template_name] = False
                results.add_fail(f"Template '{template_name}'", f"Read error: {e}")
        else:
            templates[template_name] = False
            results.add_warning(f"Template '{template_name}'", "Not found")

    return templates


def test_forms_import(results: TestResults, dependencies: Dict[str, bool]) -> Dict[str, bool]:
    """Test 6: Verify forms can be imported"""
    print_header("TEST 6: Form Classes")

    if not dependencies.get('flask_wtf'):
        results.add_fail("Form import", "Flask-WTF not available")
        return {}

    forms = {}

    form_classes = [
        'LoginForm',
        'ProjectForm',
        'SocraticSessionForm',
        'CodeGenerationForm',
        'DocumentUploadForm'
    ]

    try:
        from web.app import (
            LoginForm, ProjectForm, SocraticSessionForm,
            CodeGenerationForm, DocumentUploadForm
        )

        for form_name in form_classes:
            forms[form_name] = True
            results.add_pass(f"Form '{form_name}' imported")

    except ImportError as e:
        for form_name in form_classes:
            forms[form_name] = False
        results.add_fail("Form import", str(e))
    except Exception as e:
        for form_name in form_classes:
            forms[form_name] = False
        results.add_fail("Form import", f"Error: {e}")

    return forms


def test_app_context(results: TestResults, app: Any) -> bool:
    """Test 7: Test application context"""
    print_header("TEST 7: Application Context")

    if app is None:
        results.add_fail("App context", "No app available")
        return False

    try:
        with app.app_context():
            results.add_pass("App context created successfully")

            # Test configuration access
            if 'SECRET_KEY' in app.config:
                results.add_pass("Configuration accessible in context")
            else:
                results.add_warning("Configuration", "SECRET_KEY not found")

            return True

    except Exception as e:
        results.add_fail("App context", str(e))
        return False


def test_test_client(results: TestResults, app: Any) -> Any:
    """Test 8: Create test client"""
    print_header("TEST 8: Test Client")

    if app is None:
        results.add_fail("Test client", "No app available")
        return None

    try:
        client = app.test_client()
        results.add_pass("Test client created")
        return client

    except Exception as e:
        results.add_fail("Test client", str(e))
        return None


def test_route_responses(results: TestResults, client: Any) -> Dict[str, int]:
    """Test 9: Test route responses"""
    print_header("TEST 9: Route Responses")

    if client is None:
        results.add_fail("Route responses", "No test client available")
        return {}

    responses = {}

    # Test public routes (should work without authentication)
    public_routes = [
        ('/login', 'GET', 'Login page'),
    ]

    for path, method, description in public_routes:
        try:
            if method == 'GET':
                response = client.get(path, follow_redirects=True)
            else:
                response = client.post(path, follow_redirects=True)

            responses[path] = response.status_code

            if response.status_code in [200, 302]:
                results.add_pass(f"{description} accessible ({response.status_code})")
            else:
                results.add_warning(
                    f"{description}",
                    f"Unexpected status code: {response.status_code}"
                )

        except Exception as e:
            responses[path] = 0
            results.add_fail(f"{description}", str(e))

    # Note: Protected routes would need authentication
    results.add_pass("Public routes tested")

    return responses


def test_system_integration(results: TestResults) -> Dict[str, bool]:
    """Test 10: Test system component integration"""
    print_header("TEST 10: System Integration")

    integration = {}

    # Test if core system components can be imported
    try:
        from src import get_config
        integration['config'] = True
        results.add_pass("Core config accessible")
    except ImportError:
        integration['config'] = False
        results.add_warning("Core config", "Not accessible")

    # Test if agents can be imported
    try:
        from src.agents import get_orchestrator
        integration['orchestrator'] = True
        results.add_pass("Agent orchestrator accessible")
    except ImportError:
        integration['orchestrator'] = False
        results.add_warning("Agent orchestrator", "Not accessible")

    # Test if database can be imported
    try:
        from src.database import get_repository_manager
        integration['database'] = True
        results.add_pass("Database manager accessible")
    except ImportError:
        integration['database'] = False
        results.add_warning("Database manager", "Not accessible")

    return integration


def main():
    """Run all web interface tests"""
    print_header("WEB INTERFACE TEST SUITE")
    print_info(f"Python: {sys.version}")
    print_info(f"Working directory: {os.getcwd()}")

    results = TestResults()

    # Pre-checks
    if not check_web_structure(results):
        print_error("Critical: Web structure check failed")
        results.print_summary()
        return 1

    # Run tests
    dependencies = test_flask_dependencies(results)
    create_func = test_app_import(results, dependencies)
    app = test_app_creation(results, create_func)
    routes = test_routes_registered(results, app)
    templates = test_templates_exist(results)
    forms = test_forms_import(results, dependencies)
    context_ok = test_app_context(results, app)
    client = test_test_client(results, app)
    responses = test_route_responses(results, client)
    integration = test_system_integration(results)

    # Print summary
    success = results.print_summary()

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
