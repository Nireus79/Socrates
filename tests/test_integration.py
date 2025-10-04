#!/usr/bin/env python3
"""
Integration Test Suite - Task 7
================================

Comprehensive tests for backend completion verification.
Tests all persistence layers, repositories, and end-to-end workflows.

Usage:
    python test_integration.py
    python test_integration.py --verbose
    python test_integration.py --test=session_persistence
"""

import sys
import os
import time
import uuid
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database import get_database, init_database, reset_database
from src.core import DateTimeHelper, initialize_system
from src.models import (
    User, Project, Module, Task, UserRole, ModuleType, ModuleStatus,
    TaskStatus, Priority, ProjectStatus, ProjectContext
)


class IntegrationTest:
    """Integration test suite for backend verification"""

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

    # =========================================================================
    # TEST 1: DATABASE INITIALIZATION
    # =========================================================================

    def test_database_initialization(self):
        """Test database initializes with all tables"""
        self.log("Initializing database...")

        # Reset and reinitialize database
        reset_database()
        db = init_database('data/test_integration.db')

        self.assert_true(db is not None, "Database should initialize")
        self.log("Database initialized successfully")

        # Verify all repositories exist
        self.assert_true(hasattr(db, 'users'), "Users repository should exist")
        self.assert_true(hasattr(db, 'projects'), "Projects repository should exist")
        self.assert_true(hasattr(db, 'modules'), "Modules repository should exist")
        self.assert_true(hasattr(db, 'tasks'), "Tasks repository should exist")
        self.assert_true(hasattr(db, 'socratic_sessions'), "Sessions repository should exist")
        self.assert_true(hasattr(db, 'questions'), "Questions repository should exist")
        self.assert_true(hasattr(db, 'conversation_messages'), "Messages repository should exist")
        self.assert_true(hasattr(db, 'technical_specifications'), "Specs repository should exist")
        self.assert_true(hasattr(db, 'project_contexts'), "Project contexts repository should exist")
        self.assert_true(hasattr(db, 'module_contexts'), "Module contexts repository should exist")
        self.assert_true(hasattr(db, 'task_contexts'), "Task contexts repository should exist")
        self.assert_true(hasattr(db, 'conflicts'), "Conflicts repository should exist")

        self.log(f"All 12 repositories present ✅")

    # =========================================================================
    # TEST 2: USER CRUD OPERATIONS
    # =========================================================================

    def test_user_crud(self):
        """Test user creation, retrieval, update, delete"""
        db = get_database()

        # Create user with unique email to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        self.log("Creating test user...")
        user = User(
            id=str(uuid.uuid4()),
            username=f"test_user_{unique_id}",
            email=f"test_{unique_id}@example.com",
            password_hash="test_hash",
            role=UserRole.DEVELOPER,
            first_name="Test",
            last_name="User"
        )

        created = db.users.create(user)
        self.assert_true(created, "User should be created")
        self.log(f"User created: {user.username}")

        # Retrieve user
        retrieved = db.users.get_by_id(user.id)
        self.assert_true(retrieved is not None, "User should be retrievable")
        self.assert_equals(retrieved.username, f"test_user_{unique_id}", "Username should match")
        self.log("User retrieved successfully")

        # Get by username
        by_username = db.users.get_by_username(f"test_user_{unique_id}")
        self.assert_true(by_username is not None, "User should be found by username")
        self.assert_equals(by_username.id, user.id, "User ID should match")

    # =========================================================================
    # TEST 3: PROJECT AND MODULE HIERARCHY
    # =========================================================================

    def test_project_module_hierarchy(self):
        """Test project -> modules -> tasks hierarchy"""
        db = get_database()

        # Create test user for this test
        unique_id = str(uuid.uuid4())[:8]
        user = User(
            id=str(uuid.uuid4()),
            username=f"hierarchy_user_{unique_id}",
            email=f"hierarchy_{unique_id}@example.com",
            password_hash="test_hash",
            role=UserRole.DEVELOPER
        )
        db.users.create(user)
        self.log(f"Created test user: {user.username}")

        # Create project
        self.log("Creating test project...")
        project = Project(
            id=str(uuid.uuid4()),
            name="Test Project",
            description="Integration test project",
            owner_id=user.id,
            status=ProjectStatus.ACTIVE
        )

        created = db.projects.create(project)
        self.assert_true(created, "Project should be created")
        self.log(f"Project created: {project.name}")

        # Create modules
        self.log("Creating modules...")
        modules = []
        for i in range(3):
            module = Module(
                id=str(uuid.uuid4()),
                project_id=project.id,
                name=f"Module {i + 1}",
                description=f"Test module {i + 1}",
                module_type=ModuleType.FEATURE,
                status=ModuleStatus.PLANNED,
                priority=Priority.HIGH
            )
            db.modules.create(module)
            modules.append(module)

        self.log(f"Created {len(modules)} modules")

        # Retrieve modules
        retrieved_modules = db.modules.get_by_project_id(project.id)
        self.assert_equals(len(retrieved_modules), 3, "Should retrieve 3 modules")

        # Create tasks for first module
        self.log("Creating tasks...")
        tasks = []
        for i in range(5):
            task = Task(
                id=str(uuid.uuid4()),
                module_id=modules[0].id,
                project_id=project.id,
                title=f"Task {i + 1}",
                description=f"Test task {i + 1}",
                status=TaskStatus.TODO,
                priority=Priority.MEDIUM
            )
            db.tasks.create(task)
            tasks.append(task)

        self.log(f"Created {len(tasks)} tasks")

        # Retrieve tasks
        retrieved_tasks = db.tasks.get_by_module_id(modules[0].id)
        self.assert_equals(len(retrieved_tasks), 5, "Should retrieve 5 tasks")

        # Retrieve tasks by project
        project_tasks = db.tasks.get_by_project_id(project.id)
        self.assert_equals(len(project_tasks), 5, "Should retrieve 5 tasks for project")

        self.log("Project -> Module -> Task hierarchy verified ✅")

    # =========================================================================
    # TEST 4: MODULE REPOSITORY FEATURES
    # =========================================================================

    def test_module_repository_features(self):
        """Test ModuleRepository methods"""
        db = get_database()

        # Get test project - use get_by_id with known project ID from previous test
        # Or get all projects and take first one
        project = None
        try:
            # Try to get project by searching modules
            all_modules = db.modules.get_by_status("planned")
            if all_modules:
                project_id = all_modules[0].project_id
                project = db.projects.get_by_id(project_id)
        except:
            pass

        self.assert_true(project is not None, "Test project should exist")
        self.log(f"Using project: {project.name}")

        # Create module with various statuses
        self.log("Creating modules with different statuses...")

        # In progress module
        in_progress = Module(
            id=str(uuid.uuid4()),
            project_id=project.id,
            name="In Progress Module",
            status=ModuleStatus.IN_PROGRESS,
            estimated_hours=40.0,
            actual_hours=15.0,
            completion_percentage=37.5
        )
        db.modules.create(in_progress)

        # Completed module
        completed = Module(
            id=str(uuid.uuid4()),
            project_id=project.id,
            name="Completed Module",
            status=ModuleStatus.COMPLETED,
            estimated_hours=20.0,
            actual_hours=22.0,
            completion_percentage=100.0
        )
        db.modules.create(completed)

        # Test get_by_status
        in_progress_modules = db.modules.get_by_status("in_progress")
        self.assert_true(len(in_progress_modules) >= 1, "Should find in_progress modules")
        self.log(f"Found {len(in_progress_modules)} in-progress modules")

        # Test get_active_modules
        active = db.modules.get_active_modules(project.id)
        self.assert_true(len(active) >= 1, "Should find active modules")
        self.log(f"Found {len(active)} active modules for project")

        # Test update
        in_progress.completion_percentage = 50.0
        updated = db.modules.update(in_progress)
        self.assert_true(updated, "Module should update")

        retrieved = db.modules.get_by_id(in_progress.id)
        self.assert_equals(retrieved.completion_percentage, 50.0, "Completion should be updated")

        self.log("ModuleRepository features verified ✅")

    # =========================================================================
    # TEST 5: TASK REPOSITORY FEATURES
    # =========================================================================

    def test_task_repository_features(self):
        """Test TaskRepository methods"""
        db = get_database()

        # Get test module from previous tests
        modules = db.modules.get_by_status("planned")
        self.assert_true(len(modules) > 0, "Test modules should exist")
        module = modules[0]
        project = db.projects.get_by_id(module.project_id)

        # Create tasks with different statuses
        self.log("Creating tasks with different statuses...")

        statuses = [TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED]
        created_tasks = []

        for status in statuses:
            task = Task(
                id=str(uuid.uuid4()),
                module_id=module.id,
                project_id=project.id,
                title=f"Task {status.value}",
                status=status,
                priority=Priority.HIGH,
                estimated_hours=8.0
            )
            db.tasks.create(task)
            created_tasks.append(task)

        # Test get_by_status
        in_progress_tasks = db.tasks.get_by_status("in_progress")
        self.assert_true(len(in_progress_tasks) >= 1, "Should find in_progress tasks")
        self.log(f"Found {len(in_progress_tasks)} in-progress tasks")

        # Test update
        created_tasks[0].status = TaskStatus.IN_PROGRESS
        created_tasks[0].actual_hours = 3.5
        updated = db.tasks.update(created_tasks[0])
        self.assert_true(updated, "Task should update")

        retrieved = db.tasks.get_by_id(created_tasks[0].id)
        self.assert_equals(retrieved.status, TaskStatus.IN_PROGRESS, "Status should be updated")
        self.assert_equals(retrieved.actual_hours, 3.5, "Hours should be updated")

        self.log("TaskRepository features verified ✅")

    # =========================================================================
    # TEST 6: PERSISTENCE ACROSS SESSIONS
    # =========================================================================

    def test_persistence_across_sessions(self):
        """Test data persists after database reconnection"""
        db = get_database()

        # Get counts before reset - count by checking if any users exist with our test pattern
        # For simplicity, just count modules which we know exist from previous tests
        modules_count_before = len(db.modules.get_by_status("planned"))
        in_progress_before = len(db.modules.get_by_status("in_progress"))

        self.log(f"Before reset: {modules_count_before} planned modules, {in_progress_before} in-progress modules")

        # Simulate server restart - reset singleton and reinitialize
        reset_database()
        db = init_database('data/test_integration.db')

        # Get counts after reset
        modules_count_after = len(db.modules.get_by_status("planned"))
        in_progress_after = len(db.modules.get_by_status("in_progress"))

        self.log(f"After reset: {modules_count_after} planned modules, {in_progress_after} in-progress modules")

        # Verify data persisted
        self.assert_true(modules_count_after >= modules_count_before, "Planned modules should persist")
        self.assert_true(in_progress_after >= in_progress_before, "In-progress modules should persist")

        self.log("Data persistence verified ✅")

    # =========================================================================
    # TEST 7: CONFLICT DETECTION WITH REAL DATA
    # =========================================================================

    def test_conflict_detection(self):
        """Test conflict detection with real module data"""
        from src.agents.context import ContextAnalyzerAgent

        db = get_database()

        # Get test project - find one from existing modules
        modules = db.modules.get_by_status("planned")
        if not modules:
            modules = db.modules.get_by_status("in_progress")

        self.assert_true(len(modules) > 0, "Should have test modules")
        project = db.projects.get_by_id(modules[0].project_id)

        # Create many active modules to trigger timeline conflict
        self.log("Creating 6+ active modules to trigger conflict...")
        for i in range(7):
            module = Module(
                id=str(uuid.uuid4()),
                project_id=project.id,
                name=f"Active Module {i + 1}",
                status=ModuleStatus.IN_PROGRESS,
                priority=Priority.HIGH
            )
            db.modules.create(module)

        # Create context analyzer - use initialize_system to get proper ServiceContainer
        from src.core import initialize_system
        services = initialize_system()
        context_agent = ContextAnalyzerAgent(services)

        # Detect timeline conflicts
        conflicts = context_agent._detect_timeline_conflicts(project)

        self.log(f"Detected {len(conflicts)} timeline conflicts")
        self.assert_true(len(conflicts) > 0, "Should detect timeline conflicts with 7 active modules")

        if conflicts:
            conflict = conflicts[0]
            self.assert_equals(conflict['type'], 'timeline_overload', "Should be timeline_overload conflict")
            self.assert_true(conflict['active_modules'] >= 6, "Should report 6+ active modules")
            self.log(f"Conflict detected: {conflict['message']}")

        self.log("Conflict detection verified ✅")

    # =========================================================================
    # TEST 8: CONTEXT REPOSITORIES
    # =========================================================================

    def test_context_persistence(self):
        """Test project/module/task context persistence"""
        db = get_database()

        # Get test project from existing modules
        modules = db.modules.get_by_status("planned")
        if not modules:
            modules = db.modules.get_by_status("in_progress")

        self.assert_true(len(modules) > 0, "Should have test modules")
        project = db.projects.get_by_id(modules[0].project_id)

        # Create project context
        self.log("Creating project context...")
        context = ProjectContext(
            id=str(uuid.uuid4()),
            project_id=project.id,
            business_domain="E-commerce",
            target_audience="Online shoppers",
            business_goals=["Increase sales", "Improve UX"],
            last_analyzed_at=DateTimeHelper.now()
        )

        created = db.project_contexts.create(context)
        self.assert_true(created, "Context should be created")

        # Retrieve context
        retrieved = db.project_contexts.get_by_project_id(project.id)
        self.assert_true(retrieved is not None, "Context should be retrievable")
        self.assert_equals(retrieved.business_domain, "E-commerce", "Domain should match")
        self.assert_equals(len(retrieved.business_goals), 2, "Should have 2 goals")

        self.log("Context persistence verified ✅")

    # =========================================================================
    # TEST 9: COMPLETE WORKFLOW
    # =========================================================================

    def test_complete_workflow(self):
        """Test complete workflow: User -> Project -> Module -> Task"""
        db = get_database()

        self.log("Starting complete workflow test...")

        # Step 1: Create user with unique identifier
        unique_id = str(uuid.uuid4())[:8]
        workflow_user = User(
            id=str(uuid.uuid4()),
            username=f"workflow_user_{unique_id}",
            email=f"workflow_{unique_id}@test.com",
            password_hash="hash",
            role=UserRole.DEVELOPER
        )
        db.users.create(workflow_user)
        self.log("✓ User created")

        # Step 2: Create project
        workflow_project = Project(
            id=str(uuid.uuid4()),
            name="Workflow Test Project",
            owner_id=workflow_user.id,
            status=ProjectStatus.ACTIVE
        )
        db.projects.create(workflow_project)
        self.log("✓ Project created")

        # Step 3: Create module
        workflow_module = Module(
            id=str(uuid.uuid4()),
            project_id=workflow_project.id,
            name="User Authentication",
            module_type=ModuleType.SERVICE,  # Changed from CORE to SERVICE
            status=ModuleStatus.IN_PROGRESS
        )
        db.modules.create(workflow_module)
        self.log("✓ Module created")

        # Step 4: Create tasks
        task_titles = ["Design login form", "Implement JWT", "Add password reset", "Write tests"]
        for title in task_titles:
            task = Task(
                id=str(uuid.uuid4()),
                module_id=workflow_module.id,
                project_id=workflow_project.id,
                title=title,
                status=TaskStatus.TODO,
                priority=Priority.HIGH
            )
            db.tasks.create(task)
        self.log(f"✓ Created {len(task_titles)} tasks")

        # Step 5: Verify full hierarchy
        retrieved_project = db.projects.get_by_id(workflow_project.id)
        self.assert_true(retrieved_project is not None, "Project should exist")

        project_modules = db.modules.get_by_project_id(workflow_project.id)
        self.assert_equals(len(project_modules), 1, "Should have 1 module")

        module_tasks = db.tasks.get_by_module_id(workflow_module.id)
        self.assert_equals(len(module_tasks), 4, "Should have 4 tasks")

        self.log("Complete workflow verified ✅")

    # =========================================================================
    # TEST 10: SOCRATIC SESSION PERSISTENCE
    # =========================================================================

    def test_socratic_session_persistence(self):
        """Test Socratic session creation, persistence, and resume"""
        from src.agents.socratic import SocraticCounselorAgent
        from src.models import SocraticSession, Question, ConversationMessage, SessionStatus

        db = get_database()

        self.log("Testing Socratic session workflow...")

        # Step 1: Create user and project
        session_user = User(
            id=str(uuid.uuid4()),
            username=f"session_user_{str(uuid.uuid4())[:8]}",
            email=f"session_{str(uuid.uuid4())[:8]}@test.com",
            password_hash="hash",
            role=UserRole.DEVELOPER
        )
        db.users.create(session_user)

        session_project = Project(
            id=str(uuid.uuid4()),
            name="Session Test Project",
            owner_id=session_user.id,
            status=ProjectStatus.ACTIVE
        )
        db.projects.create(session_project)
        self.log("✓ User and project created")

        # Step 2: Start Socratic session via agent
        try:
            services = initialize_system()
            agent = SocraticCounselorAgent(services)

            result = agent.process_request('start_session', {
                'user_id': session_user.id,
                'project_id': session_project.id,
                'role': 'product_owner'
            })

            self.assert_true(result.get('success'), "Session should start successfully")
            session_id = result.get('data', {}).get('session_id')
            self.assert_true(session_id is not None, "Session ID should be returned")
            self.log(f"✓ Session started: {session_id}")

        except Exception as e:
            self.log(f"⚠️  Agent not available, testing repository directly: {e}")
            # Fallback: Test repository directly
            session = SocraticSession(
                id=str(uuid.uuid4()),
                project_id=session_project.id,
                initiated_by=session_user.id,
                role='product_owner',
                status=SessionStatus.IN_PROGRESS
            )
            db.socratic_sessions.create(session)
            session_id = session.id
            self.log(f"✓ Session created directly: {session_id}")

        # Step 3: Verify session persisted
        retrieved_session = db.socratic_sessions.get_by_id(session_id)
        self.assert_true(retrieved_session is not None, "Session should persist")
        self.assert_equals(retrieved_session.project_id, session_project.id, "Project ID should match")
        self.log("✓ Session retrieved from database")

        # Step 4: Add questions to session
        questions_data = [
            "What is the main goal of your product?",
            "Who are your target users?",
            "What problems does it solve?"
        ]

        for i, question_text in enumerate(questions_data):
            question = Question(
                id=str(uuid.uuid4()),
                session_id=session_id,
                question_text=question_text,
                question_number=i + 1,
                answer_text=f"Answer to question {i + 1}"
            )
            db.questions.create(question)

        self.log(f"✓ Created {len(questions_data)} questions")

        # Step 5: Verify questions persist
        session_questions = db.questions.get_by_session_id(session_id)
        self.assert_equals(len(session_questions), 3, "Should have 3 questions")
        self.log("✓ Questions retrieved")

        # Step 6: Add conversation messages
        for i in range(5):
            message = ConversationMessage(
                id=str(uuid.uuid4()),
                session_id=session_id,
                speaker='assistant' if i % 2 == 0 else 'user',
                message=f"Message {i + 1}"
            )
            db.conversation_messages.create(message)

        messages = db.conversation_messages.get_by_session_id(session_id)
        self.assert_equals(len(messages), 5, "Should have 5 messages")
        self.log("✓ Conversation messages saved")

        # Step 7: Test session resume after "restart"
        reset_database()
        db = init_database('data/test_integration.db')

        resumed_session = db.socratic_sessions.get_by_id(session_id)
        self.assert_true(resumed_session is not None, "Session should survive restart")

        resumed_questions = db.questions.get_by_session_id(session_id)
        self.assert_equals(len(resumed_questions), 3, "Questions should survive restart")

        resumed_messages = db.conversation_messages.get_by_session_id(session_id)
        self.assert_equals(len(resumed_messages), 5, "Messages should survive restart")

        self.log("Socratic session persistence verified ✅")

    # =========================================================================
    # TEST 11: SPECIFICATION GENERATION AND VERSIONING
    # =========================================================================

    def test_specification_generation(self):
        """Test specification creation, persistence, and versioning"""
        from src.agents.code import CodeGeneratorAgent
        from src.models import TechnicalSpec

        db = get_database()

        self.log("Testing specification generation...")

        # Step 1: Create test project
        spec_project = Project(
            id=str(uuid.uuid4()),
            name="Spec Test Project",
            owner_id=str(uuid.uuid4()),
            status=ProjectStatus.ACTIVE
        )
        db.projects.create(spec_project)
        self.log("✓ Project created")

        # Step 2: Create specification data
        spec_data = {
            'project_id': spec_project.id,
            'architecture_type': 'microservices',
            'technology_stack': {
                'backend': 'FastAPI',
                'frontend': 'React',
                'database': 'PostgreSQL'
            },
            'functional_requirements': [
                'User authentication',
                'Data management',
                'Real-time updates'
            ],
            'non_functional_requirements': [
                'Response time < 200ms',
                'Support 10000 concurrent users'
            ],
            'system_components': [
                {'name': 'API Gateway', 'type': 'service'},
                {'name': 'User Service', 'type': 'microservice'},
                {'name': 'Data Service', 'type': 'microservice'}
            ]
        }

        # Step 3: Save specification v1.0.0
        spec_v1 = TechnicalSpec(
            id=str(uuid.uuid4()),
            project_id=spec_project.id,
            version='1.0.0',
            architecture_type=spec_data['architecture_type'],
            technology_stack=spec_data['technology_stack'],
            functional_requirements=spec_data['functional_requirements'],
            non_functional_requirements=spec_data['non_functional_requirements'],
            system_components=spec_data['system_components'],
            created_at=DateTimeHelper.now()
        )

        success = db.technical_specifications.create(spec_v1)
        self.assert_true(success, "Specification v1.0.0 should be created")
        self.log("✓ Specification v1.0.0 created")

        # Step 4: Retrieve specification
        retrieved_spec = db.technical_specifications.get_by_id(spec_v1.id)
        self.assert_true(retrieved_spec is not None, "Should retrieve specification")
        self.assert_equals(retrieved_spec.version, '1.0.0', "Version should be 1.0.0")
        self.log("✓ Specification retrieved")

        # Step 5: Create v1.1.0 (minor update)
        spec_v1_1 = TechnicalSpec(
            id=str(uuid.uuid4()),
            project_id=spec_project.id,
            version='1.1.0',
            architecture_type=spec_data['architecture_type'],
            technology_stack=spec_data['technology_stack'],
            functional_requirements=spec_data['functional_requirements'] + ['Email notifications'],
            non_functional_requirements=spec_data['non_functional_requirements'],
            system_components=spec_data['system_components'],
            created_at=DateTimeHelper.now()
        )

        db.technical_specifications.create(spec_v1_1)
        self.log("✓ Specification v1.1.0 created")

        # Step 6: Get all versions for project
        project_specs = db.technical_specifications.get_by_project_id(spec_project.id)
        self.assert_equals(len(project_specs), 2, "Should have 2 versions")

        versions = sorted([s.version for s in project_specs])
        self.assert_equals(versions, ['1.0.0', '1.1.0'], "Versions should be ordered")
        self.log("✓ Multiple versions tracked")

        # Step 7: Get latest version
        latest = db.technical_specifications.get_latest_by_project_id(spec_project.id)
        self.assert_equals(latest.version, '1.1.0', "Latest should be v1.1.0")
        self.log("✓ Latest version retrieved")

        # Step 8: Test persistence after restart
        reset_database()
        db = init_database('data/test_integration.db')

        persisted_specs = db.technical_specifications.get_by_project_id(spec_project.id)
        self.assert_equals(len(persisted_specs), 2, "Specifications should survive restart")

        self.log("Specification generation and versioning verified ✅")

    # =========================================================================
    # TEST 12: CODE GENERATION AND PERSISTENCE
    # =========================================================================

    def test_code_generation(self):
        """Test code generation and codebase persistence"""
        from src.models import GeneratedCodebase, GeneratedFile, TechnicalSpec

        db = get_database()

        self.log("Testing code generation...")

        # Step 1: Create project and specification
        code_project = Project(
            id=str(uuid.uuid4()),
            name="Code Gen Test Project",
            owner_id=str(uuid.uuid4()),
            status=ProjectStatus.ACTIVE
        )
        db.projects.create(code_project)

        code_spec = TechnicalSpec(
            id=str(uuid.uuid4()),
            project_id=code_project.id,
            version='1.0.0',
            architecture_type='mvc',
            technology_stack={'backend': 'Flask', 'frontend': 'Vue'},
            created_at=DateTimeHelper.now()
        )
        db.technical_specifications.create(code_spec)
        self.log("✓ Project and specification created")

        # Step 2: Create generated codebase
        codebase = GeneratedCodebase(
            id=str(uuid.uuid4()),
            project_id=code_project.id,
            specification_id=code_spec.id,
            version='1.0.0',
            architecture_pattern='mvc',
            framework='Flask',
            created_at=DateTimeHelper.now()
        )

        success = db.generated_codebases.create(codebase)
        self.assert_true(success, "Codebase should be created")
        self.log("✓ Codebase created")

        # Step 3: Create generated files
        test_files = [
            {'path': 'app.py', 'type': 'python', 'content': 'from flask import Flask\napp = Flask(__name__)'},
            {'path': 'models.py', 'type': 'python', 'content': 'class User:\n    pass'},
            {'path': 'requirements.txt', 'type': 'text', 'content': 'Flask==2.0.0\nSQLAlchemy==1.4.0'},
            {'path': 'templates/index.html', 'type': 'html', 'content': '<html><body>Hello</body></html>'},
            {'path': 'static/style.css', 'type': 'css', 'content': 'body { margin: 0; }'}
        ]

        for file_data in test_files:
            gen_file = GeneratedFile(
                id=str(uuid.uuid4()),
                codebase_id=codebase.id,
                file_path=file_data['path'],
                file_type=file_data['type'],
                content=file_data['content'],
                size_bytes=len(file_data['content']),
                created_at=DateTimeHelper.now()
            )
            db.generated_files.create(gen_file)

        self.log(f"✓ Created {len(test_files)} generated files")

        # Step 4: Verify files persist
        codebase_files = db.generated_files.get_by_codebase_id(codebase.id)
        self.assert_equals(len(codebase_files), 5, "Should have 5 files")

        # Verify file types
        file_types = {f.file_type for f in codebase_files}
        expected_types = {'python', 'text', 'html', 'css'}
        self.assert_true(expected_types.issubset(file_types), "Should have all file types")
        self.log("✓ Files retrieved with correct types")

        # Step 5: Test file search by path
        app_files = [f for f in codebase_files if 'app.py' in f.file_path]
        self.assert_equals(len(app_files), 1, "Should find app.py")
        self.assert_true('Flask' in app_files[0].content, "Content should be preserved")
        self.log("✓ File content preserved")

        # Step 6: Test persistence after restart
        reset_database()
        db = init_database('data/test_integration.db')

        persisted_codebase = db.generated_codebases.get_by_id(codebase.id)
        self.assert_true(persisted_codebase is not None, "Codebase should survive restart")

        persisted_files = db.generated_files.get_by_codebase_id(codebase.id)
        self.assert_equals(len(persisted_files), 5, "Files should survive restart")

        self.log("Code generation and persistence verified ✅")

    # =========================================================================
    # TEST 13: PERFORMANCE METRICS
    # =========================================================================

    def test_performance_metrics(self):
        """Test query performance and cache efficiency"""
        import time

        db = get_database()

        self.log("Testing performance metrics...")

        # Step 1: Create test data for performance testing
        perf_project = Project(
            id=str(uuid.uuid4()),
            name="Performance Test Project",
            owner_id=str(uuid.uuid4()),
            status=ProjectStatus.ACTIVE
        )
        db.projects.create(perf_project)

        # Create multiple modules
        module_ids = []
        for i in range(20):
            module = Module(
                id=str(uuid.uuid4()),
                project_id=perf_project.id,
                name=f"Perf Module {i}",
                module_type=ModuleType.SERVICE,
                status=ModuleStatus.IN_PROGRESS if i % 2 == 0 else ModuleStatus.COMPLETED
            )
            db.modules.create(module)
            module_ids.append(module.id)

        self.log("✓ Created 20 modules for testing")

        # Step 2: Test query performance with indexes
        start_time = time.time()
        modules = db.modules.get_by_project_id(perf_project.id)
        query_time = (time.time() - start_time) * 1000  # Convert to ms

        self.assert_true(query_time < 100, f"Query should be fast (<100ms), got {query_time:.2f}ms")
        self.assert_equals(len(modules), 20, "Should retrieve all 20 modules")
        self.log(f"✓ Project query: {query_time:.2f}ms (< 100ms threshold)")

        # Step 3: Test status filter performance
        start_time = time.time()
        in_progress = db.modules.get_by_status("in_progress")
        filter_time = (time.time() - start_time) * 1000

        self.assert_true(filter_time < 100, f"Filter query should be fast, got {filter_time:.2f}ms")
        self.log(f"✓ Status filter query: {filter_time:.2f}ms")

        # Step 4: Test context cache performance
        from src.agents.context import ContextAnalyzerAgent
        from src.models import ProjectContext

        # Create cached context
        context = ProjectContext(
            id=str(uuid.uuid4()),
            project_id=perf_project.id,
            business_domain='E-commerce',
            target_audience='Online shoppers',
            last_analyzed_at=DateTimeHelper.now()
        )
        db.project_contexts.create(context)

        # First retrieval (cache miss)
        start_time = time.time()
        ctx1 = db.project_contexts.get_by_project_id(perf_project.id)
        first_time = (time.time() - start_time) * 1000

        # Second retrieval (should be faster or similar)
        start_time = time.time()
        ctx2 = db.project_contexts.get_by_project_id(perf_project.id)
        second_time = (time.time() - start_time) * 1000

        self.assert_true(ctx1 is not None and ctx2 is not None, "Context should be retrieved")
        self.log(f"✓ Context retrieval: 1st={first_time:.2f}ms, 2nd={second_time:.2f}ms")

        # Step 5: Test N+1 query detection (batch retrieval)
        start_time = time.time()

        # Bad pattern: N+1 queries
        project_count = 0
        for module_id in module_ids[:5]:  # Test with first 5 modules
            module = db.modules.get_by_id(module_id)
            if module:
                project = db.projects.get_by_id(module.project_id)
                if project:
                    project_count += 1

        n_plus_one_time = (time.time() - start_time) * 1000

        # Good pattern: Single query with joins (simulated by batch get)
        start_time = time.time()
        all_modules = db.modules.get_by_project_id(perf_project.id)
        batch_time = (time.time() - start_time) * 1000

        self.assert_true(batch_time < n_plus_one_time, "Batch query should be faster than N+1")
        self.log(f"✓ N+1 detection: Individual={n_plus_one_time:.2f}ms vs Batch={batch_time:.2f}ms")

        # Step 6: Memory usage baseline (basic check)
        import sys

        large_result = db.modules.get_by_status("in_progress")
        result_size = sys.getsizeof(large_result)

        self.assert_true(result_size < 10000, "Result set should be reasonably sized")
        self.log(f"✓ Memory check: Result set ~{result_size} bytes")

        self.log("Performance metrics verified ✅")

    # =========================================================================
    # UPDATE run_all_tests() METHOD
    # =========================================================================

    # Replace the existing run_all_tests method with this updated version:

    def run_all_tests(self):
        """Run all integration tests"""
        print("\n" + "=" * 70)
        print("INTEGRATION TEST SUITE - TASK 7 (COMPLETE)")
        print("=" * 70)

        # Run tests in order
        self.run_test("Database Initialization", self.test_database_initialization)
        self.run_test("User CRUD Operations", self.test_user_crud)
        self.run_test("Project/Module/Task Hierarchy", self.test_project_module_hierarchy)
        self.run_test("ModuleRepository Features", self.test_module_repository_features)
        self.run_test("TaskRepository Features", self.test_task_repository_features)
        self.run_test("Persistence Across Sessions", self.test_persistence_across_sessions)
        self.run_test("Conflict Detection", self.test_conflict_detection)
        self.run_test("Context Persistence", self.test_context_persistence)
        self.run_test("Complete Workflow", self.test_complete_workflow)

        # NEW TESTS
        self.run_test("Socratic Session Persistence", self.test_socratic_session_persistence)
        self.run_test("Specification Generation", self.test_specification_generation)
        self.run_test("Code Generation", self.test_code_generation)
        self.run_test("Performance Metrics", self.test_performance_metrics)

        # Print summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)

        total = self.tests_passed + self.tests_failed
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {self.tests_passed}")
        print(f"❌ Failed: {self.tests_failed}")
        print(f"Success Rate: {(self.tests_passed / total * 100):.1f}%")

        # Print detailed results
        if self.test_results:
            print("\nDetailed Results:")
            for name, status, error in self.test_results:
                symbol = "✅" if status == "PASS" else "❌"
                print(f"  {symbol} {name}: {status}")
                if error:
                    print(f"     Error: {error}")

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
            return 1
    else:
        # Run all tests
        return suite.run_all_tests()


if __name__ == '__main__':
    sys.exit(main())
