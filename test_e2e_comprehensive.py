#!/usr/bin/env python3
"""
Comprehensive End-to-End Testing Suite

Tests complete user workflows and feature integration:
1. Authentication flows
2. Project management workflows
3. Analytics and maturity tracking
4. Chat/dialogue operations
5. Code generation features
6. Collaboration features
7. Error handling and edge cases
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Optional, Tuple

BASE_URL = "http://localhost:8000"

class E2ETestSuite:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []
        self.session = requests.Session()
        self.test_user = None
        self.test_password = None
        self.access_token = None
        self.refresh_token = None
        self.project_id = None

    def log(self, message: str, level: str = "INFO"):
        """Log test messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level:8} {message}")

    def assert_status(self, response: requests.Response, expected_status: int, test_name: str) -> bool:
        """Assert HTTP status code"""
        if response.status_code == expected_status:
            self.log(f"[PASS] {test_name}: {response.status_code}", "PASS")
            self.passed += 1
            return True
        else:
            self.log(f"[FAIL] {test_name}: Expected {expected_status}, got {response.status_code}", "FAIL")
            if response.text:
                self.log(f"  Response: {response.text[:200]}", "DEBUG")
            self.failed += 1
            return False

    def run_test(self, name: str, test_func) -> bool:
        """Run a single test function"""
        try:
            self.log(f"Running: {name}", "TEST")
            result = test_func()
            return result
        except Exception as e:
            self.log(f"ERROR in {name}: {str(e)}", "ERROR")
            self.failed += 1
            return False

    def test_auth_register(self) -> bool:
        """Test user registration"""
        timestamp = str(int(time.time()))
        self.test_user = f"e2e_test_user_{timestamp}"
        self.test_password = "E2ETestPassword123!"

        response = self.session.post(
            f"{BASE_URL}/auth/register",
            json={"username": self.test_user, "password": self.test_password}
        )

        if self.assert_status(response, 201, "User Registration"):
            data = response.json()
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
            self.log(f"  User created: {self.test_user}", "DEBUG")
            self.log(f"  Access token: {self.access_token[:20]}...", "DEBUG")
            return True
        return False

    def test_auth_login(self) -> bool:
        """Test user login"""
        response = self.session.post(
            f"{BASE_URL}/auth/login",
            json={"username": self.test_user, "password": self.test_password}
        )

        if self.assert_status(response, 200, "User Login"):
            data = response.json()
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
            return True
        return False

    def test_auth_get_profile(self) -> bool:
        """Test getting current user profile"""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.session.get(f"{BASE_URL}/auth/me", headers=headers)

        if self.assert_status(response, 200, "Get User Profile"):
            data = response.json()
            self.log(f"  Username: {data.get('username')}", "DEBUG")
            return True
        return False

    def test_auth_update_profile(self) -> bool:
        """Test updating user profile"""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.session.put(f"{BASE_URL}/auth/me", headers=headers)

        if self.assert_status(response, 200, "Update User Profile"):
            return True
        return False

    def test_auth_refresh_token(self) -> bool:
        """Test token refresh"""
        response = self.session.post(
            f"{BASE_URL}/auth/refresh",
            json={"refresh_token": self.refresh_token}
        )

        if self.assert_status(response, 200, "Refresh Access Token"):
            data = response.json()
            self.access_token = data.get("access_token")
            self.log(f"  New token: {self.access_token[:20]}...", "DEBUG")
            return True
        return False

    def test_project_create(self) -> bool:
        """Test project creation"""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payload = {
            "name": f"E2E Test Project {int(time.time())}",
            "owner": self.test_user,
            "description": "Created during E2E testing"
        }

        response = self.session.post(
            f"{BASE_URL}/projects",
            json=payload,
            headers=headers
        )

        if response.status_code in [200, 201]:
            self.log(f"[PASS] Project Creation: {response.status_code}", "PASS")
            data = response.json()
            # Handle different response formats
            if isinstance(data, dict):
                self.project_id = data.get("project_id") or (data.get("project", {}).get("project_id") if data.get("project") else None)
            if self.project_id:
                self.log(f"  Project ID: {self.project_id}", "DEBUG")
                self.passed += 1
                return True
            else:
                self.log(f"  Could not extract project_id from response", "WARN")
                return False
        else:
            self.log(f"[FAIL] Project Creation: Expected 200/201, got {response.status_code}", "FAIL")
            if response.text:
                self.log(f"  Response: {response.text[:200]}", "DEBUG")
            self.failed += 1
            return False

    def test_project_list(self) -> bool:
        """Test listing projects"""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.session.get(f"{BASE_URL}/projects", headers=headers)

        if self.assert_status(response, 200, "List Projects"):
            data = response.json()
            count = len(data.get("projects", []))
            self.log(f"  Projects found: {count}", "DEBUG")
            return True
        return False

    def test_project_get_details(self) -> bool:
        """Test getting project details"""
        if not self.project_id:
            self.log("  Skipping: No project_id available", "WARN")
            return False

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.session.get(
            f"{BASE_URL}/projects/{self.project_id}",
            headers=headers
        )

        if self.assert_status(response, 200, "Get Project Details"):
            data = response.json()
            self.log(f"  Project: {data.get('name', 'N/A')}", "DEBUG")
            return True
        return False

    def test_project_update(self) -> bool:
        """Test updating project"""
        if not self.project_id:
            self.log("  Skipping: No project_id available", "WARN")
            return False

        headers = {"Authorization": f"Bearer {self.access_token}"}
        payload = {"name": f"Updated Project {int(time.time())}"}
        response = self.session.put(
            f"{BASE_URL}/projects/{self.project_id}",
            json=payload,
            headers=headers
        )

        if self.assert_status(response, 200, "Update Project"):
            return True
        return False

    def test_project_stats(self) -> bool:
        """Test getting project stats"""
        if not self.project_id:
            self.log("  Skipping: No project_id available", "WARN")
            return False

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.session.get(
            f"{BASE_URL}/projects/{self.project_id}/stats",
            headers=headers
        )

        if self.assert_status(response, 200, "Get Project Stats"):
            data = response.json()
            self.log(f"  Phase: {data.get('phase', 'N/A')}", "DEBUG")
            return True
        return False

    def test_project_maturity(self) -> bool:
        """Test getting project maturity"""
        if not self.project_id:
            self.log("  Skipping: No project_id available", "WARN")
            return False

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.session.get(
            f"{BASE_URL}/projects/{self.project_id}/maturity",
            headers=headers
        )

        if self.assert_status(response, 200, "Get Project Maturity"):
            data = response.json()
            self.log(f"  Maturity: {data.get('overall_maturity', 'N/A')}", "DEBUG")
            return True
        return False

    def test_project_analytics(self) -> bool:
        """Test getting project analytics"""
        if not self.project_id:
            self.log("  Skipping: No project_id available", "WARN")
            return False

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.session.get(
            f"{BASE_URL}/projects/{self.project_id}/analytics",
            headers=headers
        )

        if self.assert_status(response, 200, "Get Project Analytics"):
            data = response.json()
            self.log(f"  Analytics status: {data.get('status', 'N/A')}", "DEBUG")
            return True
        return False

    def test_advance_phase(self) -> bool:
        """Test advancing project phase"""
        if not self.project_id:
            self.log("  Skipping: No project_id available", "WARN")
            return False

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.session.put(
            f"{BASE_URL}/projects/{self.project_id}/phase?new_phase=analysis",
            headers=headers
        )

        if self.assert_status(response, 200, "Advance Project Phase"):
            data = response.json()
            self.log(f"  New phase: {data.get('phase', 'N/A')}", "DEBUG")
            return True
        return False

    def test_chat_send_message(self) -> bool:
        """Test sending chat message"""
        if not self.project_id:
            self.log("  Skipping: No project_id available", "WARN")
            return False

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.session.post(
            f"{BASE_URL}/projects/{self.project_id}/chat/message?message=Test%20message&mode=socratic",
            headers=headers
        )

        if response.status_code in [200, 201]:
            self.log(f"[PASS] Send Chat Message: {response.status_code}", "PASS")
            self.passed += 1
            return True
        else:
            self.log(f"[FAIL] Send Chat Message: {response.status_code}", "FAIL")
            self.failed += 1
            return False

    def test_chat_get_history(self) -> bool:
        """Test getting chat history"""
        if not self.project_id:
            self.log("  Skipping: No project_id available", "WARN")
            return False

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.session.get(
            f"{BASE_URL}/projects/{self.project_id}/chat/history",
            headers=headers
        )

        if self.assert_status(response, 200, "Get Chat History"):
            data = response.json()
            self.log(f"  Messages: {len(data.get('messages', []))}", "DEBUG")
            return True
        return False

    def test_chat_switch_mode(self) -> bool:
        """Test switching chat mode"""
        if not self.project_id:
            self.log("  Skipping: No project_id available", "WARN")
            return False

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.session.put(
            f"{BASE_URL}/projects/{self.project_id}/chat/mode?mode=direct",
            headers=headers
        )

        if self.assert_status(response, 200, "Switch Chat Mode"):
            return True
        return False

    def test_code_generate(self) -> bool:
        """Test code generation"""
        if not self.project_id:
            self.log("  Skipping: No project_id available", "WARN")
            return False

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.session.post(
            f"{BASE_URL}/projects/{self.project_id}/code/generate?language=python&specification=Add%20two%20numbers",
            headers=headers
        )

        if response.status_code in [200, 201]:
            self.log(f"[PASS] Generate Code: {response.status_code}", "PASS")
            self.passed += 1
            return True
        else:
            self.log(f"[FAIL] Generate Code: {response.status_code}", "FAIL")
            self.failed += 1
            return False

    def test_code_validate(self) -> bool:
        """Test code validation"""
        if not self.project_id:
            self.log("  Skipping: No project_id available", "WARN")
            return False

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.session.post(
            f"{BASE_URL}/projects/{self.project_id}/code/validate?language=python&code=def%20add(a,b):%20return%20a+b",
            headers=headers
        )

        if response.status_code in [200, 201]:
            self.log(f"[PASS] Validate Code: {response.status_code}", "PASS")
            self.passed += 1
            return True
        else:
            self.log(f"[FAIL] Validate Code: {response.status_code}", "FAIL")
            self.failed += 1
            return False

    def test_collaboration_add_member(self) -> bool:
        """Test adding team member"""
        if not self.project_id:
            self.log("  Skipping: No project_id available", "WARN")
            return False

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.session.post(
            f"{BASE_URL}/projects/{self.project_id}/collaborators?username=collaborator_test&role=editor",
            headers=headers
        )

        if response.status_code in [200, 201]:
            self.log(f"[PASS] Add Team Member: {response.status_code}", "PASS")
            self.passed += 1
            return True
        else:
            self.log(f"[FAIL] Add Team Member: {response.status_code}", "FAIL")
            self.failed += 1
            return False

    def test_collaboration_list_members(self) -> bool:
        """Test listing collaborators"""
        if not self.project_id:
            self.log("  Skipping: No project_id available", "WARN")
            return False

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.session.get(
            f"{BASE_URL}/projects/{self.project_id}/collaborators",
            headers=headers
        )

        if self.assert_status(response, 200, "List Collaborators"):
            return True
        return False

    def test_auth_logout(self) -> bool:
        """Test user logout"""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.session.post(f"{BASE_URL}/auth/logout", headers=headers)

        if self.assert_status(response, 200, "User Logout"):
            return True
        return False

    def run_all_tests(self):
        """Run complete E2E test suite"""
        print("\n" + "="*80)
        print("END-TO-END COMPREHENSIVE TEST SUITE")
        print("="*80 + "\n")

        # Initialize API
        self.log("Initializing API...", "INIT")
        response = self.session.post(f"{BASE_URL}/initialize")
        if response.status_code == 200:
            self.log("API initialized successfully", "OK")
        else:
            self.log("API initialization failed", "ERROR")
            return

        # Authentication Tests
        print("\n--- AUTHENTICATION TESTS ---")
        self.run_test("Register new user", self.test_auth_register)
        self.run_test("User login", self.test_auth_login)
        self.run_test("Get user profile", self.test_auth_get_profile)
        self.run_test("Update user profile", self.test_auth_update_profile)
        self.run_test("Refresh access token", self.test_auth_refresh_token)

        # Project Management Tests
        print("\n--- PROJECT MANAGEMENT TESTS ---")
        self.run_test("Create project", self.test_project_create)
        self.run_test("List projects", self.test_project_list)
        self.run_test("Get project details", self.test_project_get_details)
        self.run_test("Update project", self.test_project_update)
        self.run_test("Get project stats", self.test_project_stats)
        self.run_test("Get project maturity", self.test_project_maturity)
        self.run_test("Get project analytics", self.test_project_analytics)
        self.run_test("Advance project phase", self.test_advance_phase)

        # Chat Tests
        print("\n--- CHAT/DIALOGUE TESTS ---")
        self.run_test("Send chat message", self.test_chat_send_message)
        self.run_test("Get chat history", self.test_chat_get_history)
        self.run_test("Switch chat mode", self.test_chat_switch_mode)

        # Code Generation Tests
        print("\n--- CODE GENERATION TESTS ---")
        self.run_test("Generate code", self.test_code_generate)
        self.run_test("Validate code", self.test_code_validate)

        # Collaboration Tests
        print("\n--- COLLABORATION TESTS ---")
        self.run_test("Add team member", self.test_collaboration_add_member)
        self.run_test("List collaborators", self.test_collaboration_list_members)

        # Cleanup
        print("\n--- CLEANUP ---")
        self.run_test("User logout", self.test_auth_logout)

        # Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        total = self.passed + self.failed
        percentage = (self.passed / total * 100) if total > 0 else 0

        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed} ({percentage:.1f}%)")
        print(f"Failed: {self.failed}")
        print("="*80 + "\n")

        if self.failed == 0:
            print("SUCCESS: All E2E tests passed!")
        else:
            print(f"WARNING: {self.failed} test(s) failed")

def main():
    suite = E2ETestSuite()
    suite.run_all_tests()

if __name__ == "__main__":
    main()
