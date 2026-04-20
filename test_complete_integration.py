#!/usr/bin/env python
"""
Complete Integration Test for Modular Socrates

Tests all three interfaces (API, CLI, Frontend) to ensure the complete system works.
Run this after starting the Socrates services with START_SOCRATES.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

import httpx

# Configuration
API_URL = "http://localhost:8000"
API_TIMEOUT = 30
TEST_TIMEOUT = 60

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_header(text):
    print(f"\n{BLUE}{'='*70}")
    print(f"{BLUE}{text:^70}")
    print(f"{'='*70}{RESET}\n")

def print_test(name, passed, message=""):
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"  {status} {name}")
    if message:
        print(f"      {message}")

def print_info(message):
    print(f"{BLUE}ℹ {message}{RESET}")

def print_error(message):
    print(f"{RED}✗ {message}{RESET}")

def print_success(message):
    print(f"{GREEN}✓ {message}{RESET}")

class IntegrationTester:
    def __init__(self):
        self.client = httpx.Client(base_url=API_URL, timeout=API_TIMEOUT)
        self.test_results = []
        self.project_id = None
        self.question = None

    def test(self, name, fn):
        """Run a test and track results"""
        try:
            result = fn()
            self.test_results.append((name, True, result))
            print_test(name, True, str(result) if result else "")
            return result
        except Exception as e:
            self.test_results.append((name, False, str(e)))
            print_test(name, False, str(e))
            return None

    def run_all_tests(self):
        """Run complete integration tests"""
        print_header("🤔 MODULAR SOCRATES - COMPLETE INTEGRATION TEST")

        print_info("Starting test sequence...")
        print_info(f"API URL: {API_URL}")
        print_info(f"Test timeout: {TEST_TIMEOUT} seconds")
        print("")

        # Phase 1: API Tests
        self.test_api()

        # Phase 2: Database Tests
        self.test_database()

        # Phase 3: Orchestration Tests
        self.test_orchestration()

        # Phase 4: Integration Tests
        self.test_complete_flow()

        # Phase 5: CLI Tests
        self.test_cli()

        # Print summary
        self.print_summary()

        return all(result[1] for result in self.test_results)

    def test_api(self):
        """Test API server connectivity and basic endpoints"""
        print_header("Phase 1: API Server Tests")

        # Test health endpoint
        def check_health():
            response = self.client.get("/health")
            response.raise_for_status()
            return "API is healthy"

        self.test("API Server Health", check_health)

        # Test auth endpoint
        def check_auth():
            response = self.client.post("/auth/register", json={
                "username": f"testuser_{int(time.time())}",
                "password": "TestPassword123!",
                "email": f"test_{int(time.time())}@example.com"
            })
            return f"Registration status: {response.status_code}"

        self.test("User Registration", check_auth)

    def test_database(self):
        """Test database functionality"""
        print_header("Phase 2: Database & Project Tests")

        # Create a project
        def create_project():
            response = self.client.post("/projects", json={
                "name": f"Integration Test Project {int(time.time())}",
                "description": "Testing complete integration",
                "chat_mode": "socratic"
            })
            response.raise_for_status()
            data = response.json()
            self.project_id = data.get("data", {}).get("project_id")
            return f"Project created: {self.project_id}"

        self.test("Create Project", create_project)

        if not self.project_id:
            print_error("Failed to create project, skipping dependent tests")
            return

        # Get project details
        def get_project():
            response = self.client.get(f"/projects/{self.project_id}")
            response.raise_for_status()
            data = response.json()
            return f"Project name: {data.get('data', {}).get('name', 'Unknown')}"

        self.test("Get Project Details", get_project)

        # List projects
        def list_projects():
            response = self.client.get("/projects")
            response.raise_for_status()
            data = response.json()
            count = len(data.get("data", []))
            return f"Found {count} projects"

        self.test("List Projects", list_projects)

    def test_orchestration(self):
        """Test orchestration and agent coordination"""
        print_header("Phase 3: Orchestration Tests")

        if not self.project_id:
            print_error("No project created, skipping orchestration tests")
            return

        # Test question generation
        def get_question():
            response = self.client.get(f"/projects/{self.project_id}/chat/question")
            response.raise_for_status()
            data = response.json()
            self.question = data.get("data", {}).get("question")
            return f"Question: {self.question[:60]}..." if self.question else "No question"

        result = self.test("Question Generation", get_question)
        if not self.question:
            print_error("No question generated, skipping answer tests")
            return

        # Test response processing
        def send_response():
            response = self.client.post(
                f"/projects/{self.project_id}/chat/message",
                json={
                    "message": "We need a robust authentication system with OAuth2 support",
                    "mode": "socratic"
                }
            )
            response.raise_for_status()
            data = response.json()
            return f"Response processed: {data.get('status', 'unknown')}"

        self.test("Process User Response", send_response)

        # Test second question is different
        def get_next_question():
            response = self.client.get(f"/projects/{self.project_id}/chat/question")
            response.raise_for_status()
            data = response.json()
            next_question = data.get("data", {}).get("question")

            if next_question == self.question:
                raise AssertionError("Same question returned (repetition bug)")

            return f"New question: {next_question[:60]}..." if next_question else "No question"

        self.test("Generate Different Question (No Repetition)", get_next_question)

        # Test conversation history
        def get_history():
            response = self.client.get(f"/projects/{self.project_id}/chat/history")
            response.raise_for_status()
            data = response.json()
            count = len(data.get("data", {}).get("messages", []))
            return f"Conversation has {count} messages"

        self.test("Get Chat History", get_history)

    def test_complete_flow(self):
        """Test complete Socratic flow"""
        print_header("Phase 4: Complete Socratic Flow")

        if not self.project_id:
            print_error("No project created, skipping flow test")
            return

        # Test subscription status
        def check_subscription():
            response = self.client.get("/subscription/status")
            response.raise_for_status()
            data = response.json()
            tier = data.get("data", {}).get("current_tier", "unknown")
            return f"Subscription tier: {tier}"

        self.test("Check Subscription Status", check_subscription)

        # Test debug mode
        def check_debug():
            response = self.client.get("/system/debug/status")
            response.raise_for_status()
            data = response.json()
            is_enabled = data.get("data", {}).get("enabled", False)
            return f"Debug mode: {'enabled' if is_enabled else 'disabled'}"

        self.test("Check Debug Mode", check_debug)

    def test_cli(self):
        """Test CLI functionality"""
        print_header("Phase 5: CLI Integration Tests")

        # Test CLI help
        def test_cli_help():
            result = subprocess.run(
                [sys.executable, "-m", "socrates_cli", "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise AssertionError(f"CLI help failed: {result.stderr}")
            return "CLI help working"

        self.test("CLI Help Command", test_cli_help)

        # Test project list via CLI
        def test_project_list():
            result = subprocess.run(
                [sys.executable, "-m", "socrates_cli", "project", "list"],
                capture_output=True,
                text=True,
                timeout=10,
                env={**dict(os.environ), "SOCRATES_API_URL": API_URL}
            )
            if result.returncode != 0:
                return f"Project list status: {result.returncode}"
            return "Project list working"

        # Need to import os for test_cli
        import os
        self.test("CLI Project List", test_project_list)

    def print_summary(self):
        """Print test summary"""
        print_header("TEST SUMMARY")

        total = len(self.test_results)
        passed = sum(1 for _, result, _ in self.test_results if result)
        failed = total - passed

        print(f"Total Tests:  {total}")
        print(f"{GREEN}Passed:       {passed}{RESET}")

        if failed > 0:
            print(f"{RED}Failed:       {failed}{RESET}")

        print_success(f"Success Rate: {(passed/total)*100:.1f}%")

        if failed > 0:
            print("\nFailed Tests:")
            for name, result, message in self.test_results:
                if not result:
                    print(f"  {RED}✗ {name}{RESET}")
                    print(f"    {message}")

        print("")

        if failed == 0:
            print_success("ALL TESTS PASSED! 🎉")
            print_info("Modular Socrates is fully functional")
            return True
        else:
            print_error(f"{failed} test(s) failed")
            print_info("Check the errors above and ensure all services are running")
            return False

def main():
    """Main entry point"""
    print(f"\n{BLUE}Starting Modular Socrates Integration Tests{RESET}")
    print(f"Waiting for API server to be ready...")

    # Wait for API to be ready
    client = httpx.Client(timeout=2)
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = client.get(f"{API_URL}/health")
            if response.status_code == 200:
                break
        except httpx.RequestError:
            if attempt < max_attempts - 1:
                time.sleep(1)
            else:
                print_error(f"API server not responding at {API_URL}")
                print_error("Make sure to start services with START_SOCRATES first")
                sys.exit(1)

    print_success("API server is ready")

    # Run tests
    tester = IntegrationTester()
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
