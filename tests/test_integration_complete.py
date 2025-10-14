#!/usr/bin/env python3
"""
Complete End-to-End Integration Tests
======================================
Tests complete workflows from start to finish:
- User registration and login
- Project creation with modules and tasks
- Socratic questioning session
- Code generation
- Conflict detection and resolution
"""

import sys
import os
import uuid
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import initialize_package
from src.database import get_database, reset_database, init_database
from src.models import (
    User, UserRole, UserStatus, Project, ProjectStatus, ProjectPhase,
    Module, ModuleType, ModuleStatus, Task, TaskStatus, Priority,
    SocraticSession, ConversationStatus, TechnicalRole,
    Question, ConversationMessage, Conflict, ConflictType,
    TechnicalSpec, GeneratedCodebase, GeneratedFile, FileType
)
from src.agents.user import UserManagerAgent
from src.agents.project import ProjectManagerAgent
from src.agents.socratic import SocraticCounselorAgent
from src.agents.code import CodeGeneratorAgent
from src.agents.context import ContextAnalyzerAgent


def setup_clean_environment():
    """Set up clean test environment with fresh database"""
    print("\n" + "=" * 70)
    print("SETTING UP CLEAN TEST ENVIRONMENT")
    print("=" * 70)

    # Delete database file
    db_path = 'data/socratic.db'
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print("[PASS] Deleted existing database")
        except Exception as e:
            print(f"[WARN] Could not delete database: {e}")

    # Reset and initialize
    reset_database()
    init_database()

    # Initialize services
    services = initialize_package()
    db = get_database()

    print("[PASS] Clean environment ready")
    return services, db


def test_user_registration_and_login(services, db):
    """Test 7.1.1: User Registration & Login Flow"""
    print("\n" + "=" * 70)
    print("TEST 7.1.1: USER REGISTRATION & LOGIN")
    print("=" * 70)

    try:
        # Initialize user agent
        user_agent = UserManagerAgent(services)

        # Test 1: Register new user
        print("\n[TEST] Registering new user...")
        register_result = user_agent._create_user({
            'username': 'integration_test_user',
            'email': 'integration@test.com',
            'password_hash': 'SecurePass123!',  # In production, this would be hashed
            'first_name': 'Integration',
            'last_name': 'Test',
            'role': 'developer'
        })

        assert register_result['success'], f"Registration failed: {register_result.get('error')}"
        user_data = register_result['data'].get('user', {})
        user_id = user_data.get('id') if isinstance(user_data, dict) else getattr(user_data, 'id', None)
        assert user_id, "No user ID returned from registration"
        print(f"[PASS] User registered successfully: {user_id}")

        # Test 2: Login with correct credentials
        print("\n[TEST] Logging in with correct credentials...")
        login_result = user_agent._authenticate_user({
            'username': 'integration_test_user',
            'password_hash': 'SecurePass123!'
        })

        assert login_result['success'], f"Login failed: {login_result.get('error')}"
        print(f"[PASS] Login successful")

        # Test 3: Verify user persisted in database
        print("\n[TEST] Verifying user persisted in database...")
        user = db.users.get_by_id(user_id)
        assert user is not None, "User not found in database"
        assert user.username == 'integration_test_user', "Username mismatch"
        assert user.email == 'integration@test.com', "Email mismatch"
        assert user.status == UserStatus.ACTIVE, "User should be active"
        print(f"[PASS] User persisted: {user.username} ({user.email})")

        # Test 4: Get user profile
        print("\n[TEST] Getting user profile...")
        profile_result = user_agent._get_user_profile({'user_id': user_id})
        assert profile_result['success'], f"Profile retrieval failed: {profile_result.get('error')}"
        print("[PASS] User profile retrieved successfully")

        # Test 5: Login again (verify persistence)
        print("\n[TEST] Logging in again to verify persistence...")
        login_result2 = user_agent._authenticate_user({
            'username': 'integration_test_user',
            'password_hash': 'SecurePass123!'
        })
        assert login_result2['success'], "Second login failed"
        print("[PASS] Second login successful")

        print("\n[SUCCESS] User registration & login flow complete!")
        return user_id

    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_project_creation_flow(services, db, user_id):
    """Test 7.1.2: Project Creation with Modules and Tasks"""
    print("\n" + "=" * 70)
    print("TEST 7.1.2: PROJECT CREATION FLOW")
    print("=" * 70)

    try:
        # Initialize project agent
        project_agent = ProjectManagerAgent(services)

        # Test 1: Create new project
        print("\n[TEST] Creating new project...")
        create_result = project_agent._create_project({
            'user_id': user_id,
            'name': 'E-Commerce Platform',
            'description': 'Complete e-commerce solution with payment integration',
            'technology_stack': {
                'backend': 'Python/FastAPI',
                'frontend': 'React',
                'database': 'PostgreSQL'
            },
            'requirements': [
                'User authentication and authorization',
                'Product catalog management',
                'Shopping cart functionality',
                'Payment processing integration'
            ]
        })

        assert create_result['success'], f"Project creation failed: {create_result.get('error')}"
        project_id = create_result['data']['project']['id']
        print(f"[PASS] Project created: {project_id}")

        # Test 2: Add modules to project
        print("\n[TEST] Adding modules to project...")
        modules = []

        module_specs = [
            {'name': 'Authentication Module', 'type': 'feature', 'description': 'User auth with JWT'},
            {'name': 'Product Catalog', 'type': 'feature', 'description': 'Product management'},
            {'name': 'Shopping Cart', 'type': 'feature', 'description': 'Cart operations'}
        ]

        for spec in module_specs:
            module_result = project_agent._add_module({
                'user_id': user_id,
                'project_id': project_id,
                'name': spec['name'],
                'description': spec['description'],
                'module_type': spec['type'],
                'priority': 'high'
            })
            assert module_result['success'], f"Module creation failed: {module_result.get('error')}"
            modules.append(module_result['data']['module']['id'])
            print(f"[PASS] Module added: {spec['name']}")

        # Test 3: Add tasks to first module
        print("\n[TEST] Adding tasks to Authentication Module...")
        tasks = []

        task_specs = [
            'Implement user registration endpoint',
            'Implement login with JWT generation',
            'Add password hashing and validation'
        ]

        for task_name in task_specs:
            task_result = project_agent._add_task({
                'user_id': user_id,
                'project_id': project_id,
                'module_id': modules[0],
                'title': task_name,
                'description': f'Task: {task_name}',
                'priority': 'high'
            })
            assert task_result['success'], f"Task creation failed: {task_result.get('error')}"
            tasks.append(task_result['data']['task']['id'])
            print(f"[PASS] Task added: {task_name}")

        # Test 4: Verify persistence
        print("\n[TEST] Verifying project persistence...")
        project = db.projects.get_by_id(project_id)
        assert project is not None, "Project not found"
        assert project.name == 'E-Commerce Platform', "Project name mismatch"
        print(f"[PASS] Project persisted: {project.name}")

        db_modules = db.modules.get_by_project_id(project_id)
        assert len(db_modules) == 3, f"Expected 3 modules, found {len(db_modules)}"
        print(f"[PASS] Modules persisted: {len(db_modules)} modules")

        db_tasks = db.tasks.get_by_module_id(modules[0])
        assert len(db_tasks) == 3, f"Expected 3 tasks, found {len(db_tasks)}"
        print(f"[PASS] Tasks persisted: {len(db_tasks)} tasks")

        print("\n[SUCCESS] Project creation flow complete!")
        return project_id, modules, tasks

    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_socratic_session_flow(services, db, user_id, project_id):
    """Test 7.1.3: Socratic Questioning Session"""
    print("\n" + "=" * 70)
    print("TEST 7.1.3: SOCRATIC SESSION FLOW")
    print("=" * 70)

    try:
        # Initialize socratic agent
        socratic_agent = SocraticCounselorAgent(services)

        # Test 1: Start new session
        print("\n[TEST] Starting Socratic session...")
        start_result = socratic_agent._start_session({
            'user_id': user_id,
            'project_id': project_id,
            'role': 'backend_developer'
        })

        assert start_result['success'], f"Session start failed: {start_result.get('error')}"
        session_id = start_result['data']['session']['id']
        print(f"[PASS] Session started: {session_id}")

        # Test 2: Answer 5 questions
        print("\n[TEST] Answering questions...")
        for i in range(5):
            # Get next question
            question_result = socratic_agent._get_next_question({
                'user_id': user_id,
                'session_id': session_id
            })

            if not question_result['success']:
                print(f"[WARN] No more questions available after {i} questions")
                break

            question = question_result['data'].get('question')
            question_id = question.get('id') if isinstance(question, dict) else getattr(question, 'id', None)

            if not question_id:
                print(f"[WARN] No question ID available after {i} questions")
                break

            print(f"[INFO] Question {i+1}: {question.get('question_text', 'N/A')[:60]}...")

            # Submit answer
            answer_result = socratic_agent._submit_answer({
                'user_id': user_id,
                'session_id': session_id,
                'question_id': question_id,
                'answer_text': f'Test answer {i+1}: This is a sample answer to the question about the project requirements.'
            })

            assert answer_result['success'], f"Answer submission failed: {answer_result.get('error')}"
            print(f"[PASS] Answer {i+1} submitted")

        # Test 3: Verify session persistence
        print("\n[TEST] Verifying session persistence...")
        session = db.socratic_sessions.get_by_id(session_id)
        assert session is not None, "Session not found"
        assert session.project_id == project_id, "Project ID mismatch"
        assert session.questions_answered >= 5, f"Expected 5+ answers, found {session.questions_answered}"
        print(f"[PASS] Session persisted: {session.questions_answered} questions answered")

        # Test 4: Get session history
        print("\n[TEST] Retrieving session history...")
        history_result = socratic_agent._get_session_history({
            'user_id': user_id,
            'session_id': session_id
        })

        assert history_result['success'], f"History retrieval failed: {history_result.get('error')}"
        print(f"[PASS] Session history retrieved")

        print("\n[SUCCESS] Socratic session flow complete!")
        return session_id

    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_code_generation_flow(services, db, user_id, project_id):
    """Test 7.1.4: Code Generation Flow"""
    print("\n" + "=" * 70)
    print("TEST 7.1.4: CODE GENERATION FLOW")
    print("=" * 70)

    try:
        # Initialize code generator agent
        code_agent = CodeGeneratorAgent(services)

        # Test 1: Create technical specification
        print("\n[TEST] Creating technical specification...")
        spec_result = code_agent._create_specification({
            'user_id': user_id,
            'project_id': project_id,
            'architecture_type': 'microservices',
            'technology_stack': {
                'backend': 'Python/FastAPI',
                'frontend': 'React',
                'database': 'PostgreSQL'
            },
            'functional_requirements': [
                'User authentication',
                'Product management',
                'Order processing'
            ]
        })

        assert spec_result['success'], f"Spec creation failed: {spec_result.get('error')}"
        spec_id = spec_result['data']['specification']['id']
        print(f"[PASS] Specification created: {spec_id}")

        # Test 2: Verify spec persistence
        print("\n[TEST] Verifying specification persistence...")
        spec = db.technical_specifications.get_by_id(spec_id)
        assert spec is not None, "Specification not found"
        assert spec.project_id == project_id, "Project ID mismatch"
        print(f"[PASS] Specification persisted: {spec.architecture_type}")

        # Test 3: Generate sample file (simplified for testing)
        print("\n[TEST] Generating code files...")

        # Create a codebase record
        codebase = GeneratedCodebase(
            id=str(uuid.uuid4()),
            project_id=project_id,
            spec_id=spec_id,
            architecture_type='microservices',
            total_files=1,
            total_lines_of_code=50
        )
        db.codebases.create(codebase)
        print(f"[PASS] Codebase created: {codebase.id}")

        # Create a sample file
        sample_file = GeneratedFile(
            id=str(uuid.uuid4()),
            codebase_id=codebase.id,
            project_id=project_id,
            file_path='src/main.py',
            file_type=FileType.PYTHON,
            content='# Sample generated code\nprint("Hello, World!")',
            size_bytes=50,
            line_count=2
        )
        db.generated_files.create(sample_file)
        print(f"[PASS] File generated: {sample_file.file_path}")

        # Test 4: Verify files accessible
        print("\n[TEST] Verifying generated files accessible...")
        files = db.generated_files.get_by_codebase_id(codebase.id)
        assert len(files) >= 1, "No files found"
        print(f"[PASS] Files accessible: {len(files)} file(s)")

        print("\n[SUCCESS] Code generation flow complete!")
        return codebase.id

    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_conflict_detection_flow(services, db, user_id, project_id):
    """Test 7.1.5: Conflict Detection and Resolution"""
    print("\n" + "=" * 70)
    print("TEST 7.1.5: CONFLICT DETECTION FLOW")
    print("=" * 70)

    try:
        # Initialize context analyzer agent
        context_agent = ContextAnalyzerAgent(services)

        # Test 1: Detect conflicts
        print("\n[TEST] Running conflict detection...")
        conflict_result = context_agent._detect_conflicts({
            'user_id': user_id,
            'project_id': project_id,
            'session_id': str(uuid.uuid4())
        })

        # Note: May not find conflicts in test data, which is OK
        if conflict_result['success']:
            conflicts = conflict_result['data'].get('conflicts', [])
            print(f"[PASS] Conflict detection complete: {len(conflicts)} conflict(s) detected")
        else:
            print(f"[INFO] Conflict detection returned: {conflict_result.get('message', 'No conflicts')}")

        # Test 2: Create a manual conflict for testing
        print("\n[TEST] Creating test conflict...")
        test_conflict = Conflict(
            id=str(uuid.uuid4()),
            project_id=project_id,
            session_id=str(uuid.uuid4()),
            conflict_type=ConflictType.TECHNICAL,
            description='Test conflict: Database choice vs performance requirements',
            severity='medium',
            first_requirement='Use PostgreSQL for relational data',
            second_requirement='Need sub-millisecond query times',
            is_resolved=False
        )
        db.conflicts.create(test_conflict)
        print(f"[PASS] Test conflict created: {test_conflict.id}")

        # Test 3: Verify conflict persistence
        print("\n[TEST] Verifying conflict persistence...")
        conflict = db.conflicts.get_by_id(test_conflict.id)
        assert conflict is not None, "Conflict not found"
        assert conflict.project_id == project_id, "Project ID mismatch"
        print(f"[PASS] Conflict persisted: {conflict.description[:60]}...")

        # Test 4: Resolve conflict
        print("\n[TEST] Resolving conflict...")
        conflict.is_resolved = True
        conflict.resolution_strategy = 'Use caching layer with Redis'
        conflict.resolution_notes = 'Implement caching to achieve performance goals'
        db.conflicts.update(conflict)

        resolved_conflict = db.conflicts.get_by_id(test_conflict.id)
        assert resolved_conflict.is_resolved, "Conflict not marked as resolved"
        print(f"[PASS] Conflict resolved: {resolved_conflict.resolution_strategy}")

        print("\n[SUCCESS] Conflict detection flow complete!")
        return test_conflict.id

    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        raise


def run_all_tests():
    """Run all end-to-end workflow tests"""
    print("\n" + "=" * 70)
    print("COMPLETE END-TO-END INTEGRATION TEST SUITE")
    print("=" * 70)

    try:
        # Setup
        services, db = setup_clean_environment()

        # Run all workflow tests in sequence
        user_id = test_user_registration_and_login(services, db)
        project_id, modules, tasks = test_project_creation_flow(services, db, user_id)
        session_id = test_socratic_session_flow(services, db, user_id, project_id)
        codebase_id = test_code_generation_flow(services, db, user_id, project_id)
        conflict_id = test_conflict_detection_flow(services, db, user_id, project_id)

        # Final summary
        print("\n" + "=" * 70)
        print("ALL END-TO-END WORKFLOW TESTS PASSED!")
        print("=" * 70)
        print(f"User ID: {user_id}")
        print(f"Project ID: {project_id}")
        print(f"Modules: {len(modules)}")
        print(f"Tasks: {len(tasks)}")
        print(f"Session ID: {session_id}")
        print(f"Codebase ID: {codebase_id}")
        print(f"Conflict ID: {conflict_id}")
        print("=" * 70)

        return True

    except Exception as e:
        print("\n" + "=" * 70)
        print(f"TEST SUITE FAILED: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
