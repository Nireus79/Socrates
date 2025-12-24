"""
Strict End-to-End Workflow Tests for Socrates API

Tests complete user workflows without loose assertions.
Each test validates the full request-response cycle with proper assertions.
"""

import requests
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

BASE_URL = "http://localhost:8000"
API_KEY = os.getenv("ANTHROPIC_API_KEY", "test-key")


class E2EWorkflowTester:
    """Comprehensive E2E workflow testing with strict assertions."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []

    def log_test(self, name: str, passed: bool, details: str = ""):
        """Log test result."""
        self.test_results.append({
            "name": name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        })

    def assert_status_code(self, response: requests.Response, expected: int, context: str = ""):
        """Assert response status code with detailed error reporting."""
        if response.status_code != expected:
            error_msg = f"{context}: Expected {expected}, got {response.status_code}"
            try:
                error_msg += f"\nResponse: {response.json()}"
            except:
                error_msg += f"\nResponse body: {response.text}"
            raise AssertionError(error_msg)

    def assert_has_keys(self, obj: Dict, keys: list, context: str = ""):
        """Assert that dictionary has all required keys."""
        missing = [k for k in keys if k not in obj]
        if missing:
            raise AssertionError(f"{context}: Missing keys {missing} in {list(obj.keys())}")

    def assert_not_empty(self, value: Any, field: str = ""):
        """Assert that value is not empty."""
        if not value:
            raise AssertionError(f"{field} is empty: {value}")

    # ========================================================================
    # Workflow: Initialize API
    # ========================================================================

    def test_initialize_api(self) -> bool:
        """Test: Initialize API endpoint."""
        print("\n" + "=" * 70)
        print("WORKFLOW 1: Initialize API")
        print("=" * 70)

        try:
            # Set API key in environment
            os.environ["ANTHROPIC_API_KEY"] = API_KEY

            # Call initialize endpoint
            response = self.session.post(f"{self.base_url}/initialize", json={})
            print(f"Status: {response.status_code}")
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")

            # Strict assertions
            self.assert_status_code(response, 200, "Initialize endpoint")
            self.assert_has_keys(data, ["version", "status"], "Initialize response")
            self.assert_not_empty(data.get("version"), "version")
            self.assert_not_empty(data.get("status"), "status")

            self.log_test("Initialize API", True)
            print("[PASS] PASS: Initialize API")
            return True

        except Exception as e:
            self.log_test("Initialize API", False, str(e))
            print(f"[FAIL] Initialize API - {e}")
            return False

    # ========================================================================
    # Workflow: Complete User Registration
    # ========================================================================

    def test_user_registration(self) -> Optional[Dict[str, Any]]:
        """Test: Complete user registration with validation."""
        print("\n" + "=" * 70)
        print("WORKFLOW 2: Register User")
        print("=" * 70)

        try:
            # Generate unique username
            timestamp = int(datetime.now().timestamp() * 1000)
            username = f"testuser_{timestamp}"
            password = "SecurePassword123!"

            payload = {
                "username": username,
                "password": password,
            }

            # Call register endpoint
            response = self.session.post(
                f"{self.base_url}/auth/register",
                json=payload,
            )
            print(f"Status: {response.status_code}")
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)[:500]}...")

            # Strict assertions
            self.assert_status_code(response, 201, "Register endpoint")
            self.assert_has_keys(data, ["user", "access_token", "refresh_token", "token_type"], "Register response")

            # Validate user object
            user = data.get("user")
            self.assert_has_keys(user, ["username", "email", "subscription_tier"], "User object")
            assert user.get("username") == username, f"Username mismatch: {user.get('username')} != {username}"

            # Validate tokens
            access_token = data.get("access_token")
            refresh_token = data.get("refresh_token")
            self.assert_not_empty(access_token, "access_token")
            self.assert_not_empty(refresh_token, "refresh_token")

            self.log_test("User Registration", True)
            print("[PASS] PASS: User Registration")

            return {
                "username": username,
                "password": password,
                "email": user.get("email"),
                "access_token": access_token,
                "refresh_token": refresh_token,
            }

        except Exception as e:
            self.log_test("User Registration", False, str(e))
            print(f"[FAIL] FAIL: User Registration - {e}")
            return None

    # ========================================================================
    # Workflow: Create Project
    # ========================================================================

    def test_create_project(self, auth_data: Dict[str, Any]) -> Optional[str]:
        """Test: Create project with proper authentication."""
        print("\n" + "=" * 70)
        print("WORKFLOW 3: Create Project")
        print("=" * 70)

        if not auth_data:
            print("[FAIL] SKIP: Authentication data missing")
            return None

        try:
            timestamp = int(datetime.now().timestamp())
            project_name = f"test_project_{timestamp}"

            headers = {
                "Authorization": f"Bearer {auth_data.get('access_token')}",
                "Content-Type": "application/json",
            }

            payload = {
                "name": project_name,
                "description": "Test project for E2E workflow validation",
            }

            # Call create project endpoint
            response = self.session.post(
                f"{self.base_url}/projects",
                json=payload,
                headers=headers,
            )
            print(f"Status: {response.status_code}")
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")

            # Strict assertions
            self.assert_status_code(response, 200, "Create project endpoint")
            self.assert_has_keys(data, ["project_id", "name", "owner"], "Create project response")

            project_id = data.get("project_id")
            self.assert_not_empty(project_id, "project_id")
            assert data.get("name") == project_name, f"Project name mismatch: {data.get('name')} != {project_name}"
            assert data.get("owner") == auth_data.get("username"), f"Owner mismatch: {data.get('owner')} != {auth_data.get('username')}"

            self.log_test("Create Project", True)
            print("[PASS] PASS: Create Project")

            return project_id

        except Exception as e:
            self.log_test("Create Project", False, str(e))
            print(f"[FAIL] FAIL: Create Project - {e}")
            return None

    # ========================================================================
    # Workflow: List Projects
    # ========================================================================

    def test_list_projects(self, auth_data: Dict[str, Any]) -> Optional[list]:
        """Test: List user's projects with validation."""
        print("\n" + "=" * 70)
        print("WORKFLOW 4: List Projects")
        print("=" * 70)

        if not auth_data:
            print("[FAIL] SKIP: Authentication data missing")
            return None

        try:
            headers = {
                "Authorization": f"Bearer {auth_data.get('access_token')}",
            }

            # Call list projects endpoint
            response = self.session.get(
                f"{self.base_url}/projects",
                headers=headers,
            )
            print(f"Status: {response.status_code}")
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)[:500]}...")

            # Strict assertions
            self.assert_status_code(response, 200, "List projects endpoint")
            self.assert_has_keys(data, ["projects"], "List projects response")

            projects = data.get("projects")
            assert isinstance(projects, list), f"Projects should be a list, got {type(projects)}"

            # Should have at least one project (the one we just created)
            assert len(projects) > 0, "No projects found (should have at least the one created)"

            # Validate first project structure
            if projects:
                project = projects[0]
                self.assert_has_keys(project, ["project_id", "name", "owner"], "Project object")

            self.log_test("List Projects", True)
            print("[PASS] PASS: List Projects")

            return projects

        except Exception as e:
            self.log_test("List Projects", False, str(e))
            print(f"[FAIL] FAIL: List Projects - {e}")
            return None

    # ========================================================================
    # Workflow: Token Refresh
    # ========================================================================

    def test_token_refresh(self, auth_data: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Test: Refresh access token using refresh token."""
        print("\n" + "=" * 70)
        print("WORKFLOW 5: Token Refresh")
        print("=" * 70)

        if not auth_data:
            print("[FAIL] SKIP: Authentication data missing")
            return None

        try:
            payload = {
                "refresh_token": auth_data.get("refresh_token"),
            }

            # Call refresh endpoint
            response = self.session.post(
                f"{self.base_url}/auth/refresh",
                json=payload,
            )
            print(f"Status: {response.status_code}")
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)[:500]}...")

            # Strict assertions
            self.assert_status_code(response, 200, "Refresh token endpoint")
            self.assert_has_keys(data, ["access_token", "refresh_token", "token_type"], "Refresh response")

            new_access_token = data.get("access_token")
            new_refresh_token = data.get("refresh_token")
            self.assert_not_empty(new_access_token, "new access_token")
            self.assert_not_empty(new_refresh_token, "new refresh_token")

            self.log_test("Token Refresh", True)
            print("[PASS] PASS: Token Refresh")

            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
            }

        except Exception as e:
            self.log_test("Token Refresh", False, str(e))
            print(f"[FAIL] FAIL: Token Refresh - {e}")
            return None

    # ========================================================================
    # Workflow: Logout
    # ========================================================================

    def test_logout(self, auth_data: Dict[str, Any]) -> bool:
        """Test: Logout and token revocation."""
        print("\n" + "=" * 70)
        print("WORKFLOW 6: Logout")
        print("=" * 70)

        if not auth_data:
            print("[FAIL] SKIP: Authentication data missing")
            return False

        try:
            headers = {
                "Authorization": f"Bearer {auth_data.get('access_token')}",
            }

            # Call logout endpoint
            response = self.session.post(
                f"{self.base_url}/auth/logout",
                headers=headers,
            )
            print(f"Status: {response.status_code}")
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")

            # Strict assertions
            self.assert_status_code(response, 200, "Logout endpoint")
            self.assert_has_keys(data, ["success"], "Logout response")
            assert data.get("success") is True, "Logout should return success=true"

            self.log_test("Logout", True)
            print("[PASS] PASS: Logout")
            return True

        except Exception as e:
            self.log_test("Logout", False, str(e))
            print(f"[FAIL] FAIL: Logout - {e}")
            return False

    # ========================================================================
    # Test Summary and Reporting
    # ========================================================================

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 70)
        print("E2E WORKFLOW TEST SUMMARY")
        print("=" * 70)

        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["passed"])
        failed = total - passed

        for result in self.test_results:
            status = "[PASS] PASS" if result["passed"] else "[FAIL] FAIL"
            print(f"{status}: {result['name']}")
            if not result["passed"] and result["details"]:
                print(f"       Details: {result['details'][:100]}...")

        print(f"\nTotal: {passed}/{total} tests passed")
        if failed > 0:
            print(f"Failed: {failed} tests")
            return False
        return True

    # ========================================================================
    # Run Complete Workflow
    # ========================================================================

    def run_complete_workflow(self) -> bool:
        """Run the complete E2E workflow."""
        print("\n" + "=" * 70)
        print("STARTING COMPLETE E2E WORKFLOW TEST")
        print("=" * 70)

        # Step 1: Initialize
        if not self.test_initialize_api():
            print("\n[FAIL] Cannot proceed: API initialization failed")
            return False

        # Step 2: Register user
        auth_data = self.test_user_registration()
        if not auth_data:
            print("\n[FAIL] Cannot proceed: User registration failed")
            self.print_summary()
            return False

        # Step 3: Create project
        project_id = self.test_create_project(auth_data)
        if not project_id:
            print("\n[WARNING] Project creation failed, continuing with other tests")

        # Step 4: List projects
        self.test_list_projects(auth_data)

        # Step 5: Refresh token
        new_tokens = self.test_token_refresh(auth_data)

        # Step 6: Logout
        self.test_logout(auth_data)

        # Print summary
        success = self.print_summary()
        return success


def main():
    """Main test runner."""
    tester = E2EWorkflowTester()
    success = tester.run_complete_workflow()

    # Exit with appropriate code
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
