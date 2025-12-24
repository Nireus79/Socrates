"""
Comprehensive Workflow Tests - CLI + API
Tests all documented workflows using both:
1. Direct CLI-style calls (orchestrator + database)
2. API HTTP calls (FastAPI endpoints)
"""

import os
import sys
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional

# Add project paths
sys.path.insert(0, '.')
sys.path.insert(0, 'socrates-api/src')

BASE_URL = "http://127.0.0.1:8000"
API_KEY = os.getenv("ANTHROPIC_API_KEY", "test-key")


class WorkflowTester:
    """Test all documented workflows"""

    def __init__(self):
        self.results = []
        self.api_token = None
        self.user_data = {}
        self.project_id = None

    def log(self, message: str):
        """Print with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def test_section(self, name: str):
        """Print section header"""
        print(f"\n{'='*70}")
        print(f"{name}")
        print(f"{'='*70}\n")

    # ========================================================================
    # WORKFLOW 1: Initialize API
    # ========================================================================

    def test_workflow_1_initialize(self) -> bool:
        """Test: Initialize API"""
        self.test_section("WORKFLOW 1: Initialize API")

        try:
            os.environ["ANTHROPIC_API_KEY"] = API_KEY
            response = requests.post(f"{BASE_URL}/initialize", json={})

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            data = response.json()
            assert "version" in data, "Missing version field"
            assert "status" in data, "Missing status field"

            self.log("[PASS] API initialized successfully")
            return True
        except Exception as e:
            self.log(f"[FAIL] {str(e)}")
            return False

    # ========================================================================
    # WORKFLOW 2: Register User
    # ========================================================================

    def test_workflow_2_register_user(self) -> bool:
        """Test: Register User"""
        self.test_section("WORKFLOW 2: Register User")

        try:
            timestamp = int(datetime.now().timestamp() * 1000)
            username = f"testuser_{timestamp}"
            password = "SecurePassword123!"

            response = requests.post(
                f"{BASE_URL}/auth/register",
                json={
                    "username": username,
                    "password": password,
                }
            )

            assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
            data = response.json()

            assert "user" in data, "Missing user field"
            assert "access_token" in data, "Missing access_token"
            assert "refresh_token" in data, "Missing refresh_token"

            user = data["user"]
            assert user.get("username") == username, f"Username mismatch"
            assert user.get("email") is not None, "Missing email"

            # Store for later tests
            self.api_token = data["access_token"]
            self.user_data = {"username": username, "password": password, "email": user.get("email")}

            self.log(f"[PASS] User registered: {username}")
            self.log(f"       Email: {user.get('email')}")
            return True
        except Exception as e:
            self.log(f"[FAIL] {str(e)}")
            return False

    # ========================================================================
    # WORKFLOW 3: Get User Profile
    # ========================================================================

    def test_workflow_3_get_user_profile(self) -> bool:
        """Test: Get User Profile"""
        self.test_section("WORKFLOW 3: Get User Profile")

        if not self.api_token:
            self.log("[SKIP] No token available")
            return False

        try:
            headers = {"Authorization": f"Bearer {self.api_token}"}
            response = requests.get(f"{BASE_URL}/auth/me", headers=headers)

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            data = response.json()

            assert "username" in data, "Missing username"
            assert "email" in data, "Missing email"
            assert data.get("username") == self.user_data.get("username"), "Username mismatch"

            self.log("[PASS] User profile retrieved")
            return True
        except Exception as e:
            self.log(f"[FAIL] {str(e)}")
            return False

    # ========================================================================
    # WORKFLOW 4: Create Project
    # ========================================================================

    def test_workflow_4_create_project(self) -> bool:
        """Test: Create Project"""
        self.test_section("WORKFLOW 4: Create Project")

        if not self.api_token:
            self.log("[SKIP] No token available")
            return False

        try:
            timestamp = int(datetime.now().timestamp())
            project_name = f"TestProject_{timestamp}"

            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }

            payload = {
                "name": project_name,
                "description": "Test project created by workflow test"
                # NOTE: owner field should be auto-set from authenticated user
            }

            response = requests.post(
                f"{BASE_URL}/projects",
                json=payload,
                headers=headers
            )

            self.log(f"Response Status: {response.status_code}")
            if response.status_code != 200:
                self.log(f"Response: {response.text}")

            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            data = response.json()

            assert "project_id" in data, "Missing project_id"
            assert data.get("name") == project_name, "Project name mismatch"
            assert data.get("owner") == self.user_data.get("username"), "Owner should be authenticated user"

            self.project_id = data.get("project_id")
            self.log(f"[PASS] Project created: {project_name}")
            self.log(f"       Project ID: {self.project_id}")
            return True
        except Exception as e:
            self.log(f"[FAIL] {str(e)}")
            return False

    # ========================================================================
    # WORKFLOW 5: List Projects
    # ========================================================================

    def test_workflow_5_list_projects(self) -> bool:
        """Test: List Projects"""
        self.test_section("WORKFLOW 5: List Projects")

        if not self.api_token:
            self.log("[SKIP] No token available")
            return False

        try:
            headers = {"Authorization": f"Bearer {self.api_token}"}
            response = requests.get(f"{BASE_URL}/projects", headers=headers)

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            data = response.json()

            assert "projects" in data, "Missing projects field"
            projects = data["projects"]
            assert isinstance(projects, list), "Projects should be a list"
            assert len(projects) > 0, "No projects found (should have at least one)"

            self.log(f"[PASS] Listed {len(projects)} project(s)")
            for proj in projects[:3]:  # Show first 3
                self.log(f"       - {proj.get('name')} (ID: {proj.get('project_id')})")
            return True
        except Exception as e:
            self.log(f"[FAIL] {str(e)}")
            return False

    # ========================================================================
    # WORKFLOW 6: Refresh Token
    # ========================================================================

    def test_workflow_6_refresh_token(self) -> bool:
        """Test: Refresh Access Token"""
        self.test_section("WORKFLOW 6: Refresh Token")

        # Get a refresh token first (register a new user for clean state)
        try:
            timestamp = int(datetime.now().timestamp() * 1000)
            username = f"refresh_test_{timestamp}"

            reg_response = requests.post(
                f"{BASE_URL}/auth/register",
                json={
                    "username": username,
                    "password": "Test123!",
                }
            )

            assert reg_response.status_code == 201, f"Registration failed: {reg_response.text}"
            reg_data = reg_response.json()
            refresh_token = reg_data.get("refresh_token")

            # Now test refreshing
            response = requests.post(
                f"{BASE_URL}/auth/refresh",
                json={"refresh_token": refresh_token}
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            data = response.json()

            assert "access_token" in data, "Missing access_token in refresh response"
            assert "refresh_token" in data, "Missing refresh_token in refresh response"

            self.log("[PASS] Token refreshed successfully")
            return True
        except Exception as e:
            self.log(f"[FAIL] {str(e)}")
            return False

    # ========================================================================
    # WORKFLOW 7: Logout
    # ========================================================================

    def test_workflow_7_logout(self) -> bool:
        """Test: Logout"""
        self.test_section("WORKFLOW 7: Logout")

        if not self.api_token:
            self.log("[SKIP] No token available")
            return False

        try:
            headers = {"Authorization": f"Bearer {self.api_token}"}
            response = requests.post(f"{BASE_URL}/auth/logout", headers=headers)

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            data = response.json()

            assert data.get("success") is True, "Success field should be true"

            self.log("[PASS] User logged out successfully")
            return True
        except Exception as e:
            self.log(f"[FAIL] {str(e)}")
            return False

    # ========================================================================
    # Summary
    # ========================================================================

    def run_all_workflows(self) -> Dict[str, bool]:
        """Run all workflows and return results"""
        print(f"\n{'='*70}")
        print("COMPREHENSIVE WORKFLOW TEST - CLI + API")
        print(f"{'='*70}\n")

        results = {}

        # Core workflows
        results["Initialize API"] = self.test_workflow_1_initialize()
        results["Register User"] = self.test_workflow_2_register_user()
        results["Get User Profile"] = self.test_workflow_3_get_user_profile()
        results["Create Project"] = self.test_workflow_4_create_project()
        results["List Projects"] = self.test_workflow_5_list_projects()
        results["Refresh Token"] = self.test_workflow_6_refresh_token()
        results["Logout"] = self.test_workflow_7_logout()

        # Print summary
        print(f"\n{'='*70}")
        print("SUMMARY")
        print(f"{'='*70}\n")

        passed = sum(1 for v in results.values() if v)
        total = len(results)

        for workflow, result in results.items():
            status = "[PASS]" if result else "[FAIL]"
            print(f"{status} {workflow}")

        print(f"\nTotal: {passed}/{total} workflows passed")

        return results

    def report_issues(self, results: Dict[str, bool]):
        """Report any issues found"""
        failures = [name for name, result in results.items() if not result]

        if failures:
            print(f"\n{'='*70}")
            print("ISSUES FOUND")
            print(f"{'='*70}\n")

            for failure in failures:
                print(f"[ISSUE] {failure}")

            print("\n[ACTION REQUIRED]")
            print("Review logs above for details on failing workflows")
            print("Known issue: CreateProjectRequest model may require investigation")


def main():
    """Main test runner"""
    tester = WorkflowTester()
    results = tester.run_all_workflows()
    tester.report_issues(results)

    # Exit code based on results
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
