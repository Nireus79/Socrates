#!/usr/bin/env python3
"""
Comprehensive API Endpoint Testing Suite

Tests all fixed endpoints to verify routing fixes are working correctly.
This script validates:
1. Correct HTTP status codes (200, 201, 401, 404, etc.)
2. Proper path routing (no 404 errors for endpoints we fixed)
3. Response structure matches expectations
4. Authentication and access control working
"""

import sys
from typing import Dict

import requests

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER = "test_user_api_verification"
TEST_PASSWORD = "TestPassword123!"
TEST_PROJECT_ID = None
ACCESS_TOKEN = None
REFRESH_TOKEN = None

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


class APITestSuite:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []
        self.session = requests.Session()

    def test(
        self,
        name: str,
        method: str,
        path: str,
        expected_status: int,  # noqa: C901
        json_data: Dict = None,
        headers: Dict = None,
        check_response_structure: callable = None,
    ) -> bool:
        """
        Execute a single API test

        Args:
            name: Test name/description
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path (relative to BASE_URL)
            expected_status: Expected HTTP status code
            json_data: Request body (for POST/PUT)
            headers: Request headers
            check_response_structure: Optional callback to verify response structure

        Returns:
            bool: Test passed (True) or failed (False)
        """
        url = f"{BASE_URL}{path}"

        # Add auth header if token available
        if headers is None:
            headers = {}
        if ACCESS_TOKEN and "Authorization" not in headers:
            headers["Authorization"] = f"Bearer {ACCESS_TOKEN}"

        try:
            # Make request
            if method == "GET":
                response = self.session.get(url, headers=headers)
            elif method == "POST":
                response = self.session.post(url, json=json_data, headers=headers)
            elif method == "PUT":
                response = self.session.put(url, json=json_data, headers=headers)
            elif method == "DELETE":
                response = self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Unknown method: {method}")

            # Check status code
            status_match = response.status_code == expected_status

            # Check response structure if provided
            structure_match = True
            if check_response_structure and status_match:
                try:
                    response_data = response.json() if response.text else {}
                    structure_match = check_response_structure(response_data)
                except Exception as e:
                    structure_match = False
                    print(f"  Response structure check failed: {e}")

            passed = status_match and structure_match

            # Record result
            status_symbol = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
            self.results.append(
                {
                    "name": name,
                    "passed": passed,
                    "method": method,
                    "path": path,
                    "expected_status": expected_status,
                    "actual_status": response.status_code,
                    "response": response.text[:100] if response.text else "",
                }
            )

            if passed:
                self.passed += 1
                print(f"{status_symbol} {BLUE}{method}{RESET} {path} -> {response.status_code}")
            else:
                self.failed += 1
                print(
                    f"{status_symbol} {BLUE}{method}{RESET} {path} -> {response.status_code} (expected {expected_status})"
                )
                if response.text:
                    print(f"  Response: {response.text[:200]}")

            return passed

        except Exception as e:
            self.failed += 1
            print(f"{RED}FAIL{RESET} {BLUE}{method}{RESET} {path} -> ERROR: {e}")
            self.results.append(
                {"name": name, "passed": False, "method": method, "path": path, "error": str(e)}
            )
            return False

    def run_auth_tests(self):
        """Test authentication endpoints"""
        print(f"\n{YELLOW}=== AUTHENTICATION ENDPOINTS ==={RESET}")
        global ACCESS_TOKEN, REFRESH_TOKEN

        # Register new user
        self.test(
            "Register new user",
            "POST",
            "/auth/register",
            201,
            json_data={"username": TEST_USER, "password": TEST_PASSWORD},
        )

        # Login with credentials
        if self.test(
            "Login with credentials",
            "POST",
            "/auth/login",
            200,
            json_data={"username": TEST_USER, "password": TEST_PASSWORD},
            check_response_structure=lambda r: "access_token" in r and "refresh_token" in r,
        ):
            try:
                response = self.session.post(
                    f"{BASE_URL}/auth/login",
                    json={"username": TEST_USER, "password": TEST_PASSWORD},
                )
                data = response.json()
                ACCESS_TOKEN = data.get("access_token")
                REFRESH_TOKEN = data.get("refresh_token")
                print(f"  Access token obtained: {ACCESS_TOKEN[:20]}...")
            except Exception as e:
                print(f"  Failed to extract token: {e}")

        # Get current user profile
        self.test(
            "Get current user profile",
            "GET",
            "/auth/me",
            200,
            check_response_structure=lambda r: "username" in r,
        )

        # PUT /auth/me - THIS WAS MISSING AND IS NOW FIXED
        self.test(
            "Update user profile (FIXED ENDPOINT)",
            "PUT",
            "/auth/me",
            200,
            check_response_structure=lambda r: "username" in r,
        )

        # Refresh token
        if REFRESH_TOKEN:
            self.test(
                "Refresh access token",
                "POST",
                "/auth/refresh",
                200,
                json_data={"refresh_token": REFRESH_TOKEN},
                check_response_structure=lambda r: "access_token" in r,
            )

        # Logout
        self.test(
            "Logout", "POST", "/auth/logout", 200, check_response_structure=lambda r: "success" in r
        )

    def run_projects_tests(self):
        """Test project endpoints"""
        print(f"\n{YELLOW}=== PROJECT ENDPOINTS ==={RESET}")
        global TEST_PROJECT_ID

        # Create project
        if self.test(
            "Create new project",
            "POST",
            "/projects",
            200,
            json_data={
                "name": "Test API Project",
                "owner": TEST_USER,
                "description": "Testing API endpoints after routing fixes",
            },
            check_response_structure=lambda r: "project_id" in r or "project" in r,
        ):
            try:
                # Try to extract project_id from response
                response = self.session.post(
                    f"{BASE_URL}/projects",
                    json={
                        "name": "Test API Project 2",
                        "owner": TEST_USER,
                        "description": "Testing",
                    },
                    headers={"Authorization": f"Bearer {ACCESS_TOKEN}"} if ACCESS_TOKEN else {},
                )
                data = response.json()
                if "project_id" in data:
                    TEST_PROJECT_ID = data["project_id"]
                elif "project" in data and "project_id" in data["project"]:
                    TEST_PROJECT_ID = data["project"]["project_id"]
                if TEST_PROJECT_ID:
                    print(f"  Project ID obtained: {TEST_PROJECT_ID}")
            except Exception as e:
                print(f"  Could not extract project ID: {e}")

        # List projects
        self.test(
            "List all projects",
            "GET",
            "/projects",
            200,
            check_response_structure=lambda r: "projects" in r or "total" in r,
        )

        # Get project details (requires valid project ID)
        if TEST_PROJECT_ID:
            self.test(
                "Get project details",
                "GET",
                f"/projects/{TEST_PROJECT_ID}",
                200,
                check_response_structure=lambda r: "project_id" in r or "name" in r,
            )

            # Get project stats
            self.test(
                "Get project stats",
                "GET",
                f"/projects/{TEST_PROJECT_ID}/stats",
                200,
                check_response_structure=lambda r: "project_id" in r or "phase" in r,
            )

            # Get project maturity
            self.test(
                "Get project maturity",
                "GET",
                f"/projects/{TEST_PROJECT_ID}/maturity",
                200,
                check_response_structure=lambda r: "project_id" in r or "overall_maturity" in r,
            )

            # GET /projects/{id}/analytics - THIS WAS MISSING AND IS NOW FIXED
            self.test(
                "Get project analytics (FIXED ENDPOINT)",
                "GET",
                f"/projects/{TEST_PROJECT_ID}/analytics",
                200,
                check_response_structure=lambda r: "analytics" in r or "status" in r,
            )

            # Update project
            self.test(
                "Update project",
                "PUT",
                f"/projects/{TEST_PROJECT_ID}",
                200,
                json_data={"name": "Updated Test Project", "phase": "analysis"},
                check_response_structure=lambda r: "name" in r or "project_id" in r,
            )

            # Advance phase
            self.test(
                "Advance project phase",
                "PUT",
                f"/projects/{TEST_PROJECT_ID}/phase",
                200,
                json_data={"new_phase": "design"},
                check_response_structure=lambda r: "phase" in r,
            )

    def run_chat_tests(self):
        """Test chat endpoints"""
        print(f"\n{YELLOW}=== CHAT ENDPOINTS (FIXED - ROUTING PATHS) ==={RESET}")

        if not TEST_PROJECT_ID:
            print(f"{YELLOW}Skipping chat tests - no project ID available{RESET}")
            return

        # Send chat message - WAS BROKEN WITH PATH /ws/projects//chat/message
        self.test(
            "Send chat message (FIXED ROUTING)",
            "POST",
            f"/projects/{TEST_PROJECT_ID}/chat/message",
            200,
            json_data={"message": "Test message", "mode": "socratic"},
            check_response_structure=lambda r: "status" in r or "message" in r,
        )

        # Get chat history - WAS BROKEN WITH PATH /ws/projects//chat/history
        self.test(
            "Get chat history (FIXED ROUTING)",
            "GET",
            f"/projects/{TEST_PROJECT_ID}/chat/history",
            200,
            check_response_structure=lambda r: "messages" in r or "status" in r,
        )

        # Switch chat mode - WAS BROKEN WITH PATH /ws/projects//chat/mode
        self.test(
            "Switch chat mode (FIXED ROUTING)",
            "PUT",
            f"/projects/{TEST_PROJECT_ID}/chat/mode",
            200,
            json_data={"mode": "direct"},
            check_response_structure=lambda r: "status" in r or "mode" in r,
        )

        # Request hint - WAS BROKEN WITH PATH /ws/projects//chat/hint
        self.test(
            "Request hint (FIXED ROUTING)",
            "GET",
            f"/projects/{TEST_PROJECT_ID}/chat/hint",
            200,
            check_response_structure=lambda r: "hint" in r or "status" in r,
        )

        # Get chat summary - WAS BROKEN WITH PATH /ws/projects//chat/summary
        self.test(
            "Get chat summary (FIXED ROUTING)",
            "GET",
            f"/projects/{TEST_PROJECT_ID}/chat/summary",
            200,
            check_response_structure=lambda r: "summary" in r or "status" in r,
        )

        # Clear chat history - WAS BROKEN WITH PATH /ws/projects//chat/clear
        self.test(
            "Clear chat history (FIXED ROUTING)",
            "DELETE",
            f"/projects/{TEST_PROJECT_ID}/chat/clear",
            200,
            check_response_structure=lambda r: "message" in r or "status" in r,
        )

    def run_code_tests(self):
        """Test code generation endpoints"""
        print(f"\n{YELLOW}=== CODE GENERATION ENDPOINTS (FIXED - PATH PREFIX) ==={RESET}")

        if not TEST_PROJECT_ID:
            print(f"{YELLOW}Skipping code tests - no project ID available{RESET}")
            return

        # Generate code - WAS BROKEN WITH PATH /code/{id}/code/generate
        self.test(
            "Generate code (FIXED PATH PREFIX)",
            "POST",
            f"/projects/{TEST_PROJECT_ID}/code/generate",
            200,
            json_data={
                "language": "python",
                "specification": "Write a function to add two numbers",
            },
            check_response_structure=lambda r: "code" in r or "status" in r,
        )

        # Validate code - WAS BROKEN WITH PATH /code/{id}/code/validate
        self.test(
            "Validate code (FIXED PATH PREFIX)",
            "POST",
            f"/projects/{TEST_PROJECT_ID}/code/validate",
            200,
            json_data={"code": "def add(a, b): return a + b", "language": "python"},
            check_response_structure=lambda r: "valid" in r or "status" in r or "errors" in r,
        )

        # Get code history - WAS BROKEN WITH PATH /code/{id}/code/history
        self.test(
            "Get code history (FIXED PATH PREFIX)",
            "GET",
            f"/projects/{TEST_PROJECT_ID}/code/history",
            200,
            check_response_structure=lambda r: "history" in r or "code_items" in r or "status" in r,
        )

        # Refactor code - WAS BROKEN WITH PATH /code/{id}/code/refactor
        self.test(
            "Refactor code (FIXED PATH PREFIX)",
            "POST",
            f"/projects/{TEST_PROJECT_ID}/code/refactor",
            200,
            json_data={
                "code": "def add(a, b): return a + b",
                "language": "python",
                "refactor_type": "optimize",
            },
            check_response_structure=lambda r: "refactored_code" in r or "status" in r,
        )

    def run_collaboration_tests(self):
        """Test collaboration endpoints"""
        print(
            f"\n{YELLOW}=== COLLABORATION ENDPOINTS (FIXED - PATH PREFIX & DOUBLE SLASH) ==={RESET}"
        )

        if not TEST_PROJECT_ID:
            print(f"{YELLOW}Skipping collaboration tests - no project ID available{RESET}")
            return

        # Add collaborator - WAS BROKEN WITH PATH /collaboration//{id}/collaborators
        self.test(
            "Add collaborator (FIXED PATH)",
            "POST",
            f"/projects/{TEST_PROJECT_ID}/collaborators",
            200,
            json_data={"username": "test_collab", "role": "editor"},
            check_response_structure=lambda r: "username" in r or "status" in r,
        )

        # List collaborators - WAS BROKEN WITH PATH /collaboration//{id}/collaborators
        self.test(
            "List collaborators (FIXED PATH)",
            "GET",
            f"/projects/{TEST_PROJECT_ID}/collaborators",
            200,
            check_response_structure=lambda r: "collaborators" in r
            or "status" in r
            or isinstance(r, list),
        )

        # Get presence - WAS BROKEN WITH PATH /collaboration//{id}/presence
        self.test(
            "Get presence (FIXED PATH)",
            "GET",
            f"/projects/{TEST_PROJECT_ID}/presence",
            200,
            check_response_structure=lambda r: "active_users" in r or "status" in r,
        )

        # Record activity - WAS BROKEN WITH PATH /collaboration//{id}/activity
        self.test(
            "Record activity (FIXED PATH)",
            "POST",
            f"/projects/{TEST_PROJECT_ID}/activity",
            200,
            json_data={"activity_type": "code_generated", "details": {"language": "python"}},
            check_response_structure=lambda r: "activity_id" in r or "status" in r,
        )

    def print_summary(self):
        """Print test summary"""
        total = self.passed + self.failed
        percentage = (self.passed / total * 100) if total > 0 else 0

        print(f"\n{YELLOW}{'='*60}{RESET}")
        print(f"{YELLOW}TEST SUMMARY{RESET}")
        print(f"{YELLOW}{'='*60}{RESET}")
        print(f"{GREEN}Passed: {self.passed}/{total}{RESET}")
        print(f"{RED}Failed: {self.failed}/{total}{RESET}")
        print(f"Pass Rate: {percentage:.1f}%")

        if self.failed > 0:
            print(f"\n{RED}Failed Tests:{RESET}")
            for result in self.results:
                if not result["passed"]:
                    print(f"  - {result['name']}")
                    print(f"    {result['method']} {result['path']}")
                    if "error" in result:
                        print(f"    Error: {result['error']}")
                    else:
                        print(
                            f"    Expected: {result['expected_status']}, Got: {result['actual_status']}"
                        )

        print(f"\n{YELLOW}Key Fixes Verified:{RESET}")
        verified_fixes = [r for r in self.results if "FIXED" in r["name"] and r["passed"]]
        if verified_fixes:
            for fix in verified_fixes:
                print(f"  {GREEN}PASS{RESET} {fix['name']}")

        return self.failed == 0


def main():
    """Run all tests"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}API ENDPOINT VERIFICATION TEST SUITE{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"Testing backend at: {BASE_URL}")

    # Initialize API first
    print(f"\n{YELLOW}=== INITIALIZING API ==={RESET}")
    try:
        response = requests.post(f"{BASE_URL}/initialize")
        if response.status_code == 200:
            print("PASS API initialization successful")
        else:
            print(f"FAIL API initialization failed: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
    except Exception as e:
        print(f"FAIL Could not initialize API: {e}")

    suite = APITestSuite()

    # Run test categories
    suite.run_auth_tests()
    suite.run_projects_tests()
    suite.run_chat_tests()
    suite.run_code_tests()
    suite.run_collaboration_tests()

    # Print summary
    all_passed = suite.print_summary()

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
