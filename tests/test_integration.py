#!/usr/bin/env python3
"""
Integration Test Suite - Task 7 (CORRECTED VERSION)
===================================================

Comprehensive tests for backend completion verification.
Tests core database functionality, repositories, and persistence.

✅ CORRECTED: All unexpected arguments removed
- SocraticSession: uses current_role, total_questions
- Question: uses role, context
- ConversationMessage: uses content, message_type
- TechnicalSpec: uses architecture_type, functional_requirements
- User: uses valid UserRole values

Usage:
    python test_integration.py
    python test_integration.py --verbose
    python test_integration.py --test=database_init
"""

import sys
import os
import uuid
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Core imports
from src.database import get_database, init_database, reset_database
from src.models import (
    User, Project, Module, Task, UserRole, ModuleType, ModuleStatus,
    TaskStatus, Priority, ProjectStatus, SocraticSession,
    Question, ConversationMessage, TechnicalSpec, GeneratedCodebase,
    GeneratedFile, FileType, TechnicalRole
)

# Optional imports
try:
    from src.core import DateTimeHelper
except ImportError:
    class DateTimeHelper:
        @staticmethod
        def now():
            return datetime.now()

        @staticmethod
        def to_iso_string(dt):
            return dt.isoformat() if dt else None


class IntegrationTest:
    """Clean integration test suite for backend verification"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []

    def log(self, message: str):
        """Log message if verbose mode enabled"""
        if self.verbose:
            print(f"  {message}")

    def assert_true(self, condition: bool, message: str):
        """Assert condition is true"""
        if not condition:
            raise AssertionError(f"Assertion failed: {message}")

    def assert_equals(self, actual, expected, message: str):
        """Assert actual equals expected"""
        if actual != expected:
            raise AssertionError(f"{message}\n  Expected: {expected}\n  Actual: {actual}")

    def run_test(self, test_name: str, test_func):
        """Run a single test and track results"""
        print(f"\n{'=' * 70}")
        print(f"Running: {test_name}")
        print('=' * 70)

        try:
            test_func()
            self.tests_passed += 1
            self.test_results.append((test_name, "PASS", None))
            print(f"✅ PASS: {test_name}")
        except Exception as e:
            self.tests_failed += 1
            self.test_results.append((test_name, "FAIL", str(e)))
            print(f"❌ FAIL: {test_name}")
            print(f"   Error: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()

    def test_database_initialization(self):
        """Test database initializes with all tables"""
        self.log("Initializing database...")

        # Reset and reinitialize database
        reset_database()
        db = init_database('data/test_integration.db')

        self.assert_true(db is not None, "Database should initialize")
        self.log("Database initialized successfully")

        # Verify core repositories exist
        repositories = [
            ('users', 'Users repository'),
            ('projects', 'Projects repository'),
            ('modules', 'Modules repository'),
            ('tasks', 'Tasks repository'),
            ('socratic_sessions', 'Sessions repository'),
            ('questions', 'Questions repository'),
            ('conversation_messages', 'Messages repository'),
            ('technical_specifications', 'Specs repository'),
            ('generated_codebases', 'Codebases repository'),
            ('generated_files', 'Files repository')
        ]

        for repo_name, description in repositories:
            self.assert_true(hasattr(db, repo_name), f"{description} should exist")

        self.log(f"All {len(repositories)} core repositories present ✅")

    def test_user_repository(self):
        """Test user CRUD operations"""
        db = get_database()

        # Create unique user
        unique_id = str(uuid.uuid4())[:8]
        user = User(
            id=str(uuid.uuid4()),
            username=f"test_user_{unique_id}",
            email=f"test_{unique_id}@example.com",
            password_hash="test_hash",
            role=UserRole.DEVELOPER,
            first_name="Test",
            last_name="User"
        )

        # Create user
        created = db.users.create(user)
        self.assert_true(created, "User should be created")

        # Read user
        retrieved = db.users.get_by_id(user.id)
        self.assert_true(retrieved is not None, "User should be retrievable")
        self.assert_equals(retrieved.username, user.username, "Username should match")

        # Update user
        user.first_name = "Updated"
        updated = db.users.update(user)
        self.assert_true(updated, "User should be updated")

        # Verify update
        retrieved = db.users.get_by_id(user.id)
        self.assert_equals(retrieved.first_name, "Updated", "First name should be updated")

        self.log("User CRUD operations verified ✅")

    def test_project_repository(self):
        """Test project CRUD operations"""
        db = get_database()

        # Create test user
        user = User(
            id=str(uuid.uuid4()),
            username=f"project_owner_{str(uuid.uuid4())[:8]}",
            email=f"owner_{str(uuid.uuid4())[:8]}@example.com",
            password_hash="test_hash",
            role=UserRole.DEVELOPER
        )
        db.users.create(user)

        # Create project
        project = Project(
            id=str(uuid.uuid4()),
            name="Test Project",
            description="Test project for integration testing",
            owner_id=user.id,
            status=ProjectStatus.ACTIVE
        )

        created = db.projects.create(project)
        self.assert_true(created, "Project should be created")

        # Test retrieval
        retrieved = db.projects.get_by_id(project.id)
        self.assert_true(retrieved is not None, "Project should be retrievable")
        self.assert_equals(retrieved.name, "Test Project", "Name should match")

        # Test status filtering
        active_projects = db.projects.get_by_status(ProjectStatus.ACTIVE.value)
        project_ids = [p.id for p in active_projects]
        self.assert_true(project.id in project_ids, "Project should be in active list")

        self.log("Project repository operations verified ✅")

    def test_module_repository(self):
        """Test module CRUD operations"""
        db = get_database()

        # Create test user and project
        user = User(
            id=str(uuid.uuid4()),
            username=f"module_user_{str(uuid.uuid4())[:8]}",
            email=f"module_{str(uuid.uuid4())[:8]}@example.com",
            password_hash="test_hash",
            role=UserRole.DEVELOPER
        )
        db.users.create(user)

        project = Project(
            id=str(uuid.uuid4()),
            name="Module Test Project",
            description="Test project for module testing",
            owner_id=user.id,
            status=ProjectStatus.ACTIVE
        )
        db.projects.create(project)

        # Create modules
        modules = []
        for i, module_type in enumerate([ModuleType.FEATURE, ModuleType.SERVICE]):
            module = Module(
                id=str(uuid.uuid4()),
                project_id=project.id,
                name=f"Test Module {i+1}",
                description=f"Test module of type {module_type.value}",
                module_type=module_type,
                status=ModuleStatus.IN_PROGRESS
            )
            created = db.modules.create(module)
            self.assert_true(created, f"Module {i+1} should be created")
            modules.append(module)

        self.log(f"Created {len(modules)} test modules")

        # Test retrieval
        if modules:
            project_modules = db.modules.get_by_project_id(modules[0].project_id)
            self.assert_true(len(project_modules) >= len(modules), "Should retrieve project modules")

        self.log("Module repository operations verified ✅")

    def test_task_repository(self):
        """Test task CRUD operations"""
        db = get_database()

        # Create test user and project
        user = User(
            id=str(uuid.uuid4()),
            username=f"task_user_{str(uuid.uuid4())[:8]}",
            email=f"task_{str(uuid.uuid4())[:8]}@example.com",
            password_hash="test_hash",
            role=UserRole.DEVELOPER
        )
        db.users.create(user)

        project = Project(
            id=str(uuid.uuid4()),
            name="Task Test Project",
            description="Test project for task testing",
            owner_id=user.id,
            status=ProjectStatus.ACTIVE
        )
        db.projects.create(project)

        # Get or create module
        modules = db.modules.get_by_project_id(project.id)
        if not modules:
            module = Module(
                id=str(uuid.uuid4()),
                project_id=project.id,
                name="Test Module for Tasks",
                description="Module for task testing",
                module_type=ModuleType.FEATURE,
                status=ModuleStatus.IN_PROGRESS
            )
            db.modules.create(module)
        else:
            module = modules[0]

        # Create tasks
        tasks = []
        for i, priority in enumerate([Priority.HIGH, Priority.MEDIUM, Priority.LOW]):
            task = Task(
                id=str(uuid.uuid4()),
                project_id=project.id,
                module_id=module.id,
                title=f"Test Task {i+1}",
                description=f"Test task with {priority.value} priority",
                status=TaskStatus.TODO,
                priority=priority
            )
            created = db.tasks.create(task)
            self.assert_true(created, f"Task {i+1} should be created")
            tasks.append(task)

        self.log(f"Created {len(tasks)} test tasks")

        # Test retrieval by project
        if tasks:
            project_tasks = db.tasks.get_by_project_id(tasks[0].project_id)
            self.assert_true(len(project_tasks) >= len(tasks), "Should retrieve project tasks")

            # Test retrieval by module
            module_tasks = db.tasks.get_by_module_id(tasks[0].module_id)
            self.assert_true(len(module_tasks) >= 1, "Should retrieve module tasks")

        self.log("Task repository operations verified ✅")

    def test_session_persistence(self):
        """Test socratic session persistence"""
        db = get_database()

        # Create test user and project
        user = User(
            id=str(uuid.uuid4()),
            username=f"session_user_{str(uuid.uuid4())[:8]}",
            email=f"session_{str(uuid.uuid4())[:8]}@example.com",
            password_hash="test_hash",
            role=UserRole.DEVELOPER
        )
        db.users.create(user)

        project = Project(
            id=str(uuid.uuid4()),
            name="Session Test Project",
            description="Test project for session testing",
            owner_id=user.id,
            status=ProjectStatus.ACTIVE
        )
        db.projects.create(project)

        # Create socratic session
        session = SocraticSession(
            id=str(uuid.uuid4()),
            project_id=project.id,
            user_id=user.id,
            current_role=TechnicalRole.PROJECT_MANAGER,
            total_questions=0,
            session_notes="Test session for integration testing"
        )

        created = db.socratic_sessions.create(session)
        self.assert_true(created, "Session should be created")

        # Create questions and messages
        question = Question(
            id=str(uuid.uuid4()),
            session_id=session.id,
            question_text="What is the main goal of this project?",
            role=TechnicalRole.PROJECT_MANAGER,
            context="Integration testing context"
        )
        db.questions.create(question)

        message = ConversationMessage(
            id=str(uuid.uuid4()),
            session_id=session.id,
            project_id=project.id,
            content="The main goal is to test integration.",
            message_type="user"
        )
        db.conversation_messages.create(message)

        # Test retrieval
        retrieved_session = db.socratic_sessions.get_by_id(session.id)
        self.assert_true(retrieved_session is not None, "Session should be retrievable")

        session_questions = db.questions.get_by_session_id(session.id)
        self.assert_true(len(session_questions) >= 1, "Should have session questions")

        session_messages = db.conversation_messages.get_by_session_id(session.id)
        self.assert_true(len(session_messages) >= 1, "Should have session messages")

        self.log("Session persistence verified ✅")

    def test_specification_persistence(self):
        """Test technical specification persistence"""
        db = get_database()

        # Create test user and project
        user = User(
            id=str(uuid.uuid4()),
            username=f"spec_user_{str(uuid.uuid4())[:8]}",
            email=f"spec_{str(uuid.uuid4())[:8]}@example.com",
            password_hash="test_hash",
            role=UserRole.PROJECT_MANAGER
        )
        db.users.create(user)

        project = Project(
            id=str(uuid.uuid4()),
            name="Specification Test Project",
            description="Test project for specification testing",
            owner_id=user.id,
            status=ProjectStatus.ACTIVE
        )
        db.projects.create(project)

        # Create technical specification
        spec = TechnicalSpec(
            id=str(uuid.uuid4()),
            project_id=project.id,
            version="1.0.0",
            architecture_type="layered",
            technology_stack={
                "backend": "Python",
                "database": "SQLite",
                "framework": "Flask"
            },
            functional_requirements=[
                "Set up project structure",
                "Implement core functionality",
                "Add tests"
            ]
        )

        created = db.technical_specifications.create(spec)
        self.assert_true(created, "Specification should be created")

        # Test retrieval
        retrieved = db.technical_specifications.get_by_id(spec.id)
        self.assert_true(retrieved is not None, "Specification should be retrievable")
        self.assert_equals(retrieved.version, "1.0.0", "Version should match")

        # Test project specifications
        project_specs = db.technical_specifications.get_by_project_id(project.id)
        spec_ids = [s.id for s in project_specs]
        self.assert_true(spec.id in spec_ids, "Specification should be in project list")

        self.log("Specification persistence verified ✅")

    def test_generated_code_persistence(self):
        """Test generated code persistence"""
        db = get_database()

        # Create test user and project
        user = User(
            id=str(uuid.uuid4()),
            username=f"code_user_{str(uuid.uuid4())[:8]}",
            email=f"code_{str(uuid.uuid4())[:8]}@example.com",
            password_hash="test_hash",
            role=UserRole.DEVELOPER
        )
        db.users.create(user)

        project = Project(
            id=str(uuid.uuid4()),
            name="Code Generation Test Project",
            description="Test project for code generation",
            owner_id=user.id,
            status=ProjectStatus.ACTIVE
        )
        db.projects.create(project)

        # Create codebase
        codebase = GeneratedCodebase(
            id=str(uuid.uuid4()),
            project_id=project.id,
            version="1.0.0",
            architecture_type="mvc",
            technology_stack={"language": "Python", "framework": "Flask"}
        )

        created = db.generated_codebases.create(codebase)
        self.assert_true(created, "Codebase should be created")

        # Create files
        files = []
        for i, file_type in enumerate([FileType.PYTHON, FileType.TEST, FileType.CONFIG]):
            file = GeneratedFile(
                id=str(uuid.uuid4()),
                codebase_id=codebase.id,
                file_path=f"test/file_{i+1}.py",
                file_type=file_type,
                content=f"# Test file {i+1}\nprint('Hello')"
            )
            created = db.generated_files.create(file)
            self.assert_true(created, f"File {i+1} should be created")
            files.append(file)

        self.log(f"Created codebase with {len(files)} files")

        # Test retrieval
        retrieved_codebase = db.generated_codebases.get_by_id(codebase.id)
        self.assert_true(retrieved_codebase is not None, "Codebase should be retrievable")

        codebase_files = db.generated_files.get_by_codebase_id(codebase.id)
        self.assert_true(len(codebase_files) >= len(files), "Should retrieve all files")

        self.log("Generated code persistence verified ✅")

    def run_all_tests(self):
        """Run all integration tests"""
        print("\n" + "=" * 70)
        print("SOCRATIC RAG - INTEGRATION TEST SUITE (CORRECTED)")
        print("=" * 70)

        # Run all tests
        self.run_test("Database Initialization", self.test_database_initialization)
        self.run_test("User Repository", self.test_user_repository)
        self.run_test("Project Repository", self.test_project_repository)
        self.run_test("Module Repository", self.test_module_repository)
        self.run_test("Task Repository", self.test_task_repository)
        self.run_test("Session Persistence", self.test_session_persistence)
        self.run_test("Specification Persistence", self.test_specification_persistence)
        self.run_test("Generated Code Persistence", self.test_generated_code_persistence)

        # Print summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)

        for test_name, result, error in self.test_results:
            status = "✅ PASS" if result == "PASS" else "❌ FAIL"
            print(f"{status}: {test_name}")
            if error and self.verbose:
                print(f"   Error: {error}")

        total = self.tests_passed + self.tests_failed
        percentage = (self.tests_passed / total * 100) if total > 0 else 0

        print("\n" + "=" * 70)
        print(f"Results: {self.tests_passed}/{total} tests passed ({percentage:.1f}%)")
        print("=" * 70)

        # Phase A completion assessment
        if self.tests_failed == 0:
            print(f"🎉 SUCCESS: All {self.tests_passed} tests passed!")
            print("✅ Phase A Backend Completion: 100%")
            print("✅ Ready to proceed to Phase B (UI Development)")
        elif self.tests_passed >= 7:
            print(f"🎯 MOSTLY COMPLETE: {self.tests_passed}/{total} tests passed")
            print("✅ Phase A Backend Completion: ~90%+")
            print("✅ Core functionality working - can proceed to Phase B")
        else:
            print(f"⚠️  NEEDS WORK: {self.tests_passed}/{total} tests passed")
            print("❌ Phase A Backend needs more work before Phase B")

        # Return exit code
        return 0 if self.tests_failed == 0 else 1


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Run integration tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--test', '-t', type=str, help='Run specific test')

    args = parser.parse_args()

    # Create test suite
    suite = IntegrationTest(verbose=args.verbose)

    # Run tests
    if args.test:
        # Run specific test
        test_method = getattr(suite, f"test_{args.test}", None)
        if test_method:
            suite.run_test(args.test, test_method)
        else:
            print(f"Error: Test '{args.test}' not found")
            available_tests = [method for method in dir(suite) if method.startswith('test_')]
            print(f"Available tests: {', '.join(available_tests)}")
            return 1
    else:
        # Run all tests
        return suite.run_all_tests()


if __name__ == '__main__':
    sys.exit(main())
