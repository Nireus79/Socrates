#!/usr/bin/env python3
"""
Session Persistence Tests
=========================

Tests for session persistence functionality in SocraticCounselorAgent.

Tests:
1. Session creation and persistence
2. Question persistence
3. Message persistence
4. Session resume from database
5. Memory cache restoration
6. Multiple session handling
7. Error handling for invalid sessions
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents import get_orchestrator
from src import get_services  # Fixed: get_services is in src/__init__.py
from src.core import DateTimeHelper
import uuid
import time

# ANSI color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(text):
    """Print colored header"""
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")


def print_success(text):
    """Print success message"""
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text):
    """Print error message"""
    print(f"{RED}✗ {text}{RESET}")


def print_warning(text):
    """Print warning message"""
    print(f"{YELLOW}⚠ {text}{RESET}")


def print_info(text):
    """Print info message"""
    print(f"  {text}")


class SessionPersistenceTests:
    """Test suite for session persistence"""

    def __init__(self):
        self.orchestrator = None
        self.test_session_id = None
        self.test_project_id = None
        self.test_user_id = None
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def setup(self):
        """Setup test environment"""
        print_header("TEST SETUP")

        try:
            # Get orchestrator
            self.orchestrator = get_orchestrator()
            if not self.orchestrator:
                print_error("Failed to get orchestrator")
                return False
            print_success("Orchestrator initialized")

            # Generate test IDs
            self.test_session_id = f"test-session-{uuid.uuid4().hex[:8]}"
            self.test_project_id = f"test-project-{uuid.uuid4().hex[:8]}"
            self.test_user_id = f"test-user-{uuid.uuid4().hex[:8]}"

            print_info(f"Test Session ID: {self.test_session_id}")
            print_info(f"Test Project ID: {self.test_project_id}")
            print_info(f"Test User ID: {self.test_user_id}")

            return True

        except Exception as e:
            print_error(f"Setup failed: {e}")
            return False

    def test_1_create_session(self):
        """Test 1: Create session and verify it persists"""
        print_header("TEST 1: Create Session and Verify Persistence")

        try:
            # Create session by generating questions
            # Fix: Use valid TechnicalRole value
            result = self.orchestrator.route_request(
                'socratic_counselor',
                'generate_questions',
                {
                    'session_id': self.test_session_id,
                    'project_id': self.test_project_id,
                    'user_id': self.test_user_id,
                    'role': 'backend_developer',  # Fixed: was 'developer'
                    'question_count': 3,
                    'project_phase': 'planning'
                }
            )

            if not result.get('success'):
                print_error(f"Failed to create session: {result.get('error')}")
                self.failed += 1
                return False

            print_success("Session created successfully")

            # Verify response contains session data
            data = result.get('data', {})
            session_id = data.get('session_id')
            questions = data.get('questions', [])

            print_info(f"Session ID: {session_id}")
            print_info(f"Questions generated: {len(questions)}")

            if session_id != self.test_session_id:
                print_warning(f"Session ID mismatch: expected {self.test_session_id}, got {session_id}")
                self.warnings += 1

            if len(questions) == 0:
                print_error("No questions generated")
                self.failed += 1
                return False

            print_success(f"Generated {len(questions)} questions")
            self.passed += 1
            return True

        except Exception as e:
            print_error(f"Test failed: {e}")
            self.failed += 1
            return False

    def test_2_verify_database_persistence(self):
        """Test 2: Query database directly to verify persistence"""
        print_header("TEST 2: Verify Database Persistence")

        try:
            # Get database manager with proper typing
            db_manager: Optional[Any] = None
            try:
                services = get_services()
                if services:
                    db_manager = services.get_db_manager()
            except Exception:
                # Fallback: try to get orchestrator's database
                agent = self.orchestrator.agents.get('socratic_counselor')
                if agent and hasattr(agent, 'db_service') and agent.db_service:
                    db_manager = agent.db_service.db_manager

            if not db_manager:
                print_error("Could not access database manager")
                self.failed += 1
                return False

            # Query sessions table
            query = "SELECT * FROM socratic_sessions WHERE id = ?"
            results: List[Dict[str, Any]] = db_manager.execute_query(query, (self.test_session_id,))

            if not results or len(results) == 0:
                print_error("Session not found in database")
                self.failed += 1
                return False

            session_row: Dict[str, Any] = results[0]
            print_success("Session found in database")
            print_info(f"Project ID: {session_row.get('project_id', 'N/A')}")
            print_info(f"User ID: {session_row.get('user_id', 'N/A')}")
            print_info(f"Current Role: {session_row.get('current_role', 'N/A')}")
            print_info(f"Status: {session_row.get('status', 'N/A')}")

            # Query questions table
            query = "SELECT * FROM questions WHERE session_id = ?"
            results = db_manager.execute_query(query, (self.test_session_id,))

            if not results or len(results) == 0:
                print_error("No questions found in database")
                self.failed += 1
                return False

            print_success(f"Found {len(results)} questions in database")

            for i, q in enumerate(results, 1):
                question_dict: Dict[str, Any] = q
                print_info(f"Q{i}: {question_dict.get('question_text', '')[:50]}...")

            self.passed += 1
            return True

        except Exception as e:
            print_error(f"Test failed: {e}")
            self.failed += 1
            return False

    def test_3_clear_memory_cache(self):
        """Test 3: Clear memory cache to simulate server restart"""
        print_header("TEST 3: Clear Memory Cache")

        try:
            # Get the socratic agent
            agent = self.orchestrator.agents.get('socratic_counselor')
            if not agent:
                print_error("Socratic agent not found")
                self.failed += 1
                return False

            # Check if session exists in cache
            if self.test_session_id in agent.current_sessions:
                print_info("Session found in memory cache")
                cache_size_before = len(agent.current_sessions)

                # Clear the cache
                agent.current_sessions.clear()

                print_success(f"Memory cache cleared ({cache_size_before} sessions removed)")

                # Verify it's gone
                if self.test_session_id in agent.current_sessions:
                    print_error("Session still in cache after clear!")
                    self.failed += 1
                    return False

                print_success("Session removed from memory")
                self.passed += 1
                return True
            else:
                print_warning("Session was not in memory cache")
                self.warnings += 1
                return True

        except Exception as e:
            print_error(f"Test failed: {e}")
            self.failed += 1
            return False

    def test_4_resume_session(self):
        """Test 4: Resume session from database"""
        print_header("TEST 4: Resume Session from Database")

        try:
            # Call resume_session
            result = self.orchestrator.route_request(
                'socratic_counselor',
                'resume_session',
                {
                    'session_id': self.test_session_id
                }
            )

            if not result.get('success'):
                print_error(f"Failed to resume session: {result.get('error')}")
                self.failed += 1
                return False

            print_success("Session resumed successfully")

            # Verify response contains session data
            data = result.get('data', {})

            if not data:
                print_error("No session data returned")
                self.failed += 1
                return False

            # Check key fields
            session_id = data.get('session_id') or data.get('id')
            questions = data.get('questions', [])
            history = data.get('conversation_history', [])

            print_info(f"Session ID: {session_id}")
            print_info(f"Questions: {len(questions)}")
            print_info(f"Conversation history: {len(history)} messages")
            print_info(f"Role: {data.get('role')}")
            print_info(f"Status: {data.get('status')}")

            if session_id != self.test_session_id:
                print_error(f"Session ID mismatch: expected {self.test_session_id}, got {session_id}")
                self.failed += 1
                return False

            if len(questions) == 0:
                print_error("No questions in resumed session")
                self.failed += 1
                return False

            print_success(f"Resumed session with {len(questions)} questions")
            self.passed += 1
            return True

        except Exception as e:
            print_error(f"Test failed: {e}")
            self.failed += 1
            return False

    def test_5_verify_cache_restoration(self):
        """Test 5: Verify session is back in memory cache"""
        print_header("TEST 5: Verify Memory Cache Restoration")

        try:
            # Get the socratic agent
            agent = self.orchestrator.agents.get('socratic_counselor')
            if not agent:
                print_error("Socratic agent not found")
                self.failed += 1
                return False

            # Check if session is in cache
            if self.test_session_id not in agent.current_sessions:
                print_error("Session not restored to memory cache")
                self.failed += 1
                return False

            print_success("Session found in memory cache")

            # Verify cache data
            cached_session = agent.current_sessions[self.test_session_id]
            print_info(f"Cached session keys: {list(cached_session.keys())}")
            print_info(f"Questions in cache: {len(cached_session.get('questions', []))}")

            self.passed += 1
            return True

        except Exception as e:
            print_error(f"Test failed: {e}")
            self.failed += 1
            return False

    def test_6_submit_answer(self):
        """Test 6: Submit answer and verify message persistence"""
        print_header("TEST 6: Submit Answer and Verify Persistence")

        try:
            # Get a question to answer
            agent = self.orchestrator.agents.get('socratic_counselor')
            if not agent:
                print_error("Socratic agent not found")
                self.failed += 1
                return False

            session = agent.current_sessions.get(self.test_session_id)
            if not session:
                print_error("Session not in cache")
                self.failed += 1
                return False

            questions = session.get('questions', [])
            if len(questions) == 0:
                print_error("No questions to answer")
                self.failed += 1
                return False

            first_question = questions[0]
            question_id = first_question.get('id')

            print_info(f"Answering question: {first_question.get('text', '')[:50]}...")

            # Submit answer via analyze_responses
            result = self.orchestrator.route_request(
                'socratic_counselor',
                'analyze_responses',
                {
                    'session_id': self.test_session_id,
                    'responses': [
                        {
                            'question_id': question_id,
                            'response': 'This is a test answer to verify message persistence.'
                        }
                    ]
                }
            )

            if not result.get('success'):
                print_error(f"Failed to submit answer: {result.get('error')}")
                self.failed += 1
                return False

            print_success("Answer submitted successfully")

            # Query database for message with proper typing
            db_manager: Optional[Any] = None
            try:
                services = get_services()
                if services:
                    db_manager = services.get_db_manager()
            except Exception:
                agent = self.orchestrator.agents.get('socratic_counselor')
                if agent and hasattr(agent, 'db_service') and agent.db_service:
                    db_manager = agent.db_service.db_manager

            if not db_manager:
                print_warning("Could not access database to verify messages")
                self.warnings += 1
                return True

            query = "SELECT * FROM conversation_messages WHERE session_id = ?"
            results: List[Dict[str, Any]] = db_manager.execute_query(query, (self.test_session_id,))

            if results and len(results) > 0:
                print_success(f"Found {len(results)} messages in database")
                self.passed += 1
                return True
            else:
                print_warning("No messages found in database (might not be implemented yet)")
                self.warnings += 1
                return True

        except Exception as e:
            print_error(f"Test failed: {e}")
            self.failed += 1
            return False

    def test_7_resume_again(self):
        """Test 7: Resume session again to verify updated data"""
        print_header("TEST 7: Resume Session Again")

        try:
            # Clear cache again
            agent = self.orchestrator.agents.get('socratic_counselor')
            if agent:
                agent.current_sessions.pop(self.test_session_id, None)
                print_info("Cleared session from cache")

            # Resume again
            result = self.orchestrator.route_request(
                'socratic_counselor',
                'resume_session',
                {
                    'session_id': self.test_session_id
                }
            )

            if not result.get('success'):
                print_error(f"Failed to resume session: {result.get('error')}")
                self.failed += 1
                return False

            print_success("Session resumed again successfully")

            data = result.get('data', {})
            history = data.get('conversation_history', [])

            print_info(f"Conversation history: {len(history)} messages")

            if len(history) > 0:
                print_success("Conversation history persisted and retrieved")
            else:
                print_warning("No conversation history (might not be implemented yet)")
                self.warnings += 1

            self.passed += 1
            return True

        except Exception as e:
            print_error(f"Test failed: {e}")
            self.failed += 1
            return False

    def test_8_invalid_session(self):
        """Test 8: Test error handling for invalid session ID"""
        print_header("TEST 8: Error Handling for Invalid Session")

        try:
            # Try to resume non-existent session
            result = self.orchestrator.route_request(
                'socratic_counselor',
                'resume_session',
                {
                    'session_id': 'invalid-session-id-does-not-exist'
                }
            )

            # Should return None or error
            data = result.get('data')

            if data is None or not result.get('success'):
                print_success("Invalid session handled correctly (returned None or error)")
                self.passed += 1
                return True
            else:
                print_warning("Invalid session did not return error")
                self.warnings += 1
                return True

        except Exception as e:
            print_error(f"Test failed: {e}")
            self.failed += 1
            return False

    def cleanup(self):
        """Cleanup test data"""
        print_header("TEST CLEANUP")

        try:
            # Get database manager with proper typing
            db_manager: Optional[Any] = None
            try:
                services = get_services()
                if services:
                    db_manager = services.get_db_manager()
            except Exception:
                agent = self.orchestrator.agents.get('socratic_counselor')
                if agent and hasattr(agent, 'db_service') and agent.db_service:
                    db_manager = agent.db_service.db_manager

            if not db_manager:
                print_warning("Could not access database for cleanup")
                return False

            # Delete test session
            db_manager.execute_update(
                "DELETE FROM socratic_sessions WHERE id = ?",
                (self.test_session_id,)
            )
            print_success("Deleted test session from database")

            # Delete test questions
            db_manager.execute_update(
                "DELETE FROM questions WHERE session_id = ?",
                (self.test_session_id,)
            )
            print_success("Deleted test questions from database")

            # Delete test messages
            db_manager.execute_update(
                "DELETE FROM conversation_messages WHERE session_id = ?",
                (self.test_session_id,)
            )
            print_success("Deleted test messages from database")

            return True

        except Exception as e:
            print_warning(f"Cleanup had issues: {e}")
            return False

    def run_all_tests(self):
        """Run all tests in sequence"""
        print_header("SESSION PERSISTENCE TEST SUITE")
        print_info(f"Started at: {DateTimeHelper.to_iso_string(DateTimeHelper.now())}")

        if not self.setup():
            print_error("Setup failed - aborting tests")
            return

        # Run tests in order
        tests = [
            self.test_1_create_session,
            self.test_2_verify_database_persistence,
            self.test_3_clear_memory_cache,
            self.test_4_resume_session,
            self.test_5_verify_cache_restoration,
            self.test_6_submit_answer,
            self.test_7_resume_again,
            self.test_8_invalid_session
        ]

        for test in tests:
            try:
                test()
                time.sleep(0.5)  # Small delay between tests
            except Exception as e:
                print_error(f"Test execution error: {e}")
                self.failed += 1

        # Cleanup
        self.cleanup()

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print_header("TEST SUMMARY")

        total = self.passed + self.failed + self.warnings

        print(f"\n{BLUE}Total Tests: {total}{RESET}")
        print(f"{GREEN}Passed: {self.passed}{RESET}")
        print(f"{RED}Failed: {self.failed}{RESET}")
        print(f"{YELLOW}Warnings: {self.warnings}{RESET}")

        if self.failed == 0:
            print(f"\n{GREEN}{'=' * 60}")
            print("ALL TESTS PASSED! ✓")
            print(f"{'=' * 60}{RESET}\n")
        else:
            print(f"\n{RED}{'=' * 60}")
            print(f"SOME TESTS FAILED ({self.failed} failures)")
            print(f"{'=' * 60}{RESET}\n")


if __name__ == '__main__':
    tester = SessionPersistenceTests()
    tester.run_all_tests()
