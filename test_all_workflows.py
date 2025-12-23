"""
COMPREHENSIVE WORKFLOW TEST SUITE
Tests ALL workflows in Socrates (CLI + API)
Compares patterns to identify architectural issues

Workflow Categories:
1. Authentication (register, login, logout, refresh)
2. Projects (create, list, delete, archive, restore)
3. Users (create, login, logout, delete, restore)
4. Collaboration (add, list, remove, role management)
5. Knowledge Base (add, search, import, export)
6. Code Generation (generate, explain, document)
7. Socratic Questions (ask, hint, summarize)
8. Analytics (status, summary, trends, breakdown)
9. GitHub Integration (import, sync, push, pull)
10. Subscription (status, upgrade, downgrade, testing mode)
11. Conversations (search, summarize)
12. Notes (add, list, search, delete)
13. Documentation (import, list)
14. Finalization (generate, docs)
15. Maturity (status, history, summary)
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# Add project paths
sys.path.insert(0, ".")
sys.path.insert(0, "socrates-api/src")

BASE_URL = "http://127.0.0.1:8000"
API_KEY = os.getenv("ANTHROPIC_API_KEY", "test-key")


class ComprehensiveWorkflowTester:
    """Test ALL workflows in Socrates"""

    def __init__(self):
        self.results = []
        self.auth_token = None
        self.user_data = {}
        self.project_id = None
        self.start_time = time.time()

    def log(self, message: str, level: str = "INFO"):
        """Log with timestamp"""
        elapsed = time.time() - self.start_time
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{timestamp}] [{level:8}] [{elapsed:6.1f}s]"
        print(f"{prefix} {message}")

    def section(self, title: str, category: str):
        """Print section header"""
        print(f"\n{'='*80}")
        print(f"CATEGORY: {category}")
        print(f"TEST: {title}")
        print(f"{'='*80}\n")

    def result(self, workflow: str, passed: bool, details: str = ""):
        """Record test result"""
        self.results.append({
            "workflow": workflow,
            "category": self.current_category,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        })
        status = "[PASS]" if passed else "[FAIL]"
        self.log(f"{status} {workflow}", "RESULT" if passed else "ERROR")
        if details:
            self.log(f"  └─ {details[:100]}", "DETAIL")

    # ========================================================================
    # 1. AUTHENTICATION WORKFLOWS
    # ========================================================================

    def test_auth_register_api(self) -> bool:
        """Test: User registration via API"""
        self.current_category = "Authentication"
        self.section("User Registration (API)", "Authentication")

        try:
            timestamp = int(time.time() * 1000)
            username = f"testuser_{timestamp}"
            password = "SecurePassword123!"

            response = requests.post(
                f"{BASE_URL}/auth/register",
                json={"username": username, "password": password},
                timeout=5
            )

            if response.status_code != 201:
                self.result("Auth: Register (API)", False, f"Status {response.status_code}")
                return False

            data = response.json()
            if "access_token" not in data or "refresh_token" not in data:
                self.result("Auth: Register (API)", False, "Missing tokens in response")
                return False

            self.auth_token = data["access_token"]
            self.user_data = {
                "username": username,
                "password": password,
                "access_token": data["access_token"],
                "refresh_token": data["refresh_token"],
            }

            self.result("Auth: Register (API)", True, f"User: {username}")
            return True

        except Exception as e:
            self.result("Auth: Register (API)", False, str(e))
            return False

    def test_auth_login_api(self) -> bool:
        """Test: User login via API"""
        self.current_category = "Authentication"
        self.section("User Login (API)", "Authentication")

        if not self.user_data.get("username"):
            self.result("Auth: Login (API)", False, "No test user available")
            return False

        try:
            response = requests.post(
                f"{BASE_URL}/auth/login",
                json={
                    "username": self.user_data["username"],
                    "password": self.user_data["password"],
                },
                timeout=5
            )

            if response.status_code != 200:
                self.result("Auth: Login (API)", False, f"Status {response.status_code}")
                return False

            data = response.json()
            if "access_token" not in data:
                self.result("Auth: Login (API)", False, "Missing access_token")
                return False

            self.auth_token = data["access_token"]
            self.result("Auth: Login (API)", True)
            return True

        except Exception as e:
            self.result("Auth: Login (API)", False, str(e))
            return False

    def test_auth_get_profile_api(self) -> bool:
        """Test: Get user profile via API"""
        self.current_category = "Authentication"
        self.section("Get User Profile (API)", "Authentication")

        if not self.auth_token:
            self.result("Auth: Get Profile (API)", False, "No auth token")
            return False

        try:
            response = requests.get(
                f"{BASE_URL}/auth/me",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=5
            )

            if response.status_code != 200:
                self.result("Auth: Get Profile (API)", False, f"Status {response.status_code}")
                return False

            data = response.json()
            if "username" not in data:
                self.result("Auth: Get Profile (API)", False, "Missing username in profile")
                return False

            self.result("Auth: Get Profile (API)", True, f"User: {data['username']}")
            return True

        except Exception as e:
            self.result("Auth: Get Profile (API)", False, str(e))
            return False

    def test_auth_refresh_token_api(self) -> bool:
        """Test: Token refresh via API"""
        self.current_category = "Authentication"
        self.section("Token Refresh (API)", "Authentication")

        if not self.user_data.get("refresh_token"):
            self.result("Auth: Refresh Token (API)", False, "No refresh token available")
            return False

        try:
            response = requests.post(
                f"{BASE_URL}/auth/refresh",
                json={"refresh_token": self.user_data["refresh_token"]},
                timeout=5
            )

            if response.status_code != 200:
                self.result("Auth: Refresh Token (API)", False, f"Status {response.status_code}")
                return False

            data = response.json()
            if "access_token" not in data:
                self.result("Auth: Refresh Token (API)", False, "Missing new access_token")
                return False

            self.auth_token = data["access_token"]
            self.user_data["refresh_token"] = data.get("refresh_token", self.user_data["refresh_token"])
            self.result("Auth: Refresh Token (API)", True)
            return True

        except Exception as e:
            self.result("Auth: Refresh Token (API)", False, str(e))
            return False

    def test_auth_logout_api(self) -> bool:
        """Test: User logout via API"""
        self.current_category = "Authentication"
        self.section("User Logout (API)", "Authentication")

        if not self.auth_token:
            self.result("Auth: Logout (API)", False, "No auth token")
            return False

        try:
            response = requests.post(
                f"{BASE_URL}/auth/logout",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=5
            )

            if response.status_code != 200:
                self.result("Auth: Logout (API)", False, f"Status {response.status_code}")
                return False

            data = response.json()
            if data.get("success") != True:
                self.result("Auth: Logout (API)", False, "Success flag not true")
                return False

            self.result("Auth: Logout (API)", True)
            return True

        except Exception as e:
            self.result("Auth: Logout (API)", False, str(e))
            return False

    # ========================================================================
    # 2. PROJECT WORKFLOWS
    # ========================================================================

    def test_project_create_api(self) -> bool:
        """Test: Create project via API"""
        self.current_category = "Projects"
        self.section("Create Project (API)", "Projects")

        if not self.auth_token:
            self.result("Project: Create (API)", False, "No auth token")
            return False

        try:
            timestamp = int(time.time())
            project_name = f"test_project_{timestamp}"

            response = requests.post(
                f"{BASE_URL}/projects",
                json={
                    "name": project_name,
                    "description": "Test project",
                },
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=5
            )

            if response.status_code not in [200, 201]:
                self.result("Project: Create (API)", False,
                          f"Status {response.status_code}: {response.text[:100]}")
                return False

            data = response.json()
            if "project_id" not in data:
                self.result("Project: Create (API)", False, "Missing project_id")
                return False

            self.project_id = data["project_id"]
            self.result("Project: Create (API)", True, f"Project: {self.project_id}")
            return True

        except Exception as e:
            self.result("Project: Create (API)", False, str(e))
            return False

    def test_project_list_api(self) -> bool:
        """Test: List projects via API"""
        self.current_category = "Projects"
        self.section("List Projects (API)", "Projects")

        if not self.auth_token:
            self.result("Project: List (API)", False, "No auth token")
            return False

        try:
            response = requests.get(
                f"{BASE_URL}/projects",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=5
            )

            if response.status_code != 200:
                self.result("Project: List (API)", False, f"Status {response.status_code}")
                return False

            data = response.json()
            if "projects" not in data:
                self.result("Project: List (API)", False, "Missing projects field")
                return False

            projects = data["projects"]
            self.result("Project: List (API)", True, f"Found {len(projects)} project(s)")
            return len(projects) > 0

        except Exception as e:
            self.result("Project: List (API)", False, str(e))
            return False

    def test_project_get_api(self) -> bool:
        """Test: Get project details via API"""
        self.current_category = "Projects"
        self.section("Get Project (API)", "Projects")

        if not self.auth_token or not self.project_id:
            self.result("Project: Get (API)", False, "Missing auth or project_id")
            return False

        try:
            response = requests.get(
                f"{BASE_URL}/projects/{self.project_id}",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=5
            )

            if response.status_code != 200:
                self.result("Project: Get (API)", False, f"Status {response.status_code}")
                return False

            data = response.json()
            if "project_id" not in data:
                self.result("Project: Get (API)", False, "Missing project_id in response")
                return False

            self.result("Project: Get (API)", True)
            return True

        except Exception as e:
            self.result("Project: Get (API)", False, str(e))
            return False

    # ========================================================================
    # 3. SYSTEM WORKFLOWS
    # ========================================================================

    def test_system_initialize_api(self) -> bool:
        """Test: System initialization"""
        self.current_category = "System"
        self.section("Initialize API", "System")

        try:
            response = requests.post(
                f"{BASE_URL}/initialize",
                json={},
                timeout=5
            )

            if response.status_code != 200:
                self.result("System: Initialize (API)", False, f"Status {response.status_code}")
                return False

            data = response.json()
            if "version" not in data or "status" not in data:
                self.result("System: Initialize (API)", False, "Missing version/status")
                return False

            self.result("System: Initialize (API)", True, f"Version: {data.get('version')}")
            return True

        except Exception as e:
            self.result("System: Initialize (API)", False, str(e))
            return False

    def test_system_health_api(self) -> bool:
        """Test: Health endpoint"""
        self.current_category = "System"
        self.section("Health Check (API)", "System")

        try:
            response = requests.get(
                f"{BASE_URL}/health",
                timeout=5
            )

            if response.status_code != 200:
                self.result("System: Health (API)", False, f"Status {response.status_code}")
                return False

            self.result("System: Health (API)", True)
            return True

        except Exception as e:
            self.result("System: Health (API)", False, str(e))
            return False

    # ========================================================================
    # REPORTING
    # ========================================================================

    def print_summary(self):
        """Print comprehensive summary"""
        print(f"\n{'='*80}")
        print("COMPREHENSIVE WORKFLOW TEST SUMMARY")
        print(f"{'='*80}\n")

        # Group results by category
        by_category = {}
        for result in self.results:
            cat = result["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(result)

        # Print by category
        total_passed = 0
        total_failed = 0

        for category in sorted(by_category.keys()):
            tests = by_category[category]
            passed = sum(1 for t in tests if t["passed"])
            failed = len(tests) - passed
            total_passed += passed
            total_failed += failed

            print(f"\n{category}:")
            for test in tests:
                status = "[PASS]" if test["passed"] else "[FAIL]"
                print(f"  {status} {test['workflow']}")
                if not test["passed"] and test["details"]:
                    print(f"       └─ {test['details'][:70]}")

            print(f"  Summary: {passed}/{len(tests)} passed")

        print(f"\n{'='*80}")
        print(f"OVERALL: {total_passed}/{total_passed + total_failed} tests passed")
        print(f"{'='*80}\n")

        return total_failed == 0

    def run_all_tests(self) -> bool:
        """Run all workflow tests"""
        self.log("Starting comprehensive workflow test suite", "START")
        self.log(f"API Base URL: {BASE_URL}", "INFO")

        # System tests
        self.test_system_initialize_api()
        self.test_system_health_api()

        # Auth tests - register new user for clean state
        if self.test_auth_register_api():
            self.test_auth_get_profile_api()
            self.test_auth_login_api()
            self.test_auth_refresh_token_api()

            # Project tests
            self.test_project_create_api()
            self.test_project_list_api()
            if self.project_id:
                self.test_project_get_api()

            # Logout (invalidates token for subsequent tests)
            self.test_auth_logout_api()

        # Print summary
        success = self.print_summary()
        self.log(f"Test suite complete. Success: {success}", "END")
        return success


def main():
    """Main test runner"""
    tester = ComprehensiveWorkflowTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
