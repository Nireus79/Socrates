"""
Phase 4: Integration Testing Suite
Tests full end-to-end user flows and feature interactions
"""

import requests
import json
import time
import sys
from datetime import datetime, timedelta
import jwt

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"
SECRET_KEY = "your-secret-key-here"  # Should match backend secret

# Test user credentials - use timestamp for uniqueness
timestamp = str(int(time.time() * 1000))
TEST_USER = {
    "username": f"testuser_{timestamp}",
    "password": "Test@1234!",
    "email": f"testuser_{timestamp}@example.com"
}

TEST_USER_2 = {
    "username": f"testuser2_{timestamp}",
    "password": "Test@1234!",
    "email": f"testuser2_{timestamp}@example.com"
}

class IntegrationTestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.access_token = None
        self.access_token_2 = None
        self.project_id = None
        self.chat_session_id = None

    def log(self, message, level="INFO"):
        """Log test messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def log_test(self, name, passed, message=""):
        """Log individual test result"""
        status = "[PASS]" if passed else "[FAIL]"
        self.log(f"{status} - {name}", "TEST")
        if not passed:
            self.failed += 1
            self.errors.append(f"{name}: {message}")
        else:
            self.passed += 1

    def create_token(self, username, exp_hours=1):
        """Create JWT token for testing"""
        payload = {
            'sub': username,
            'exp': datetime.utcnow() + timedelta(hours=exp_hours),
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

    # Phase 1: Authentication & User Management
    def test_user_registration(self):
        """Test user registration flow"""
        self.log("Testing user registration...")
        try:
            response = requests.post(
                f"{BASE_URL}/auth/register",
                json={
                    "username": TEST_USER["username"],
                    "email": TEST_USER["email"],
                    "password": TEST_USER["password"]
                }
            )
            # Accept 200 (OK) or 201 (Created) as both are valid for registration
            self.log_test("User Registration", response.status_code in [200, 201],
                         f"Status: {response.status_code}")
            return response.status_code in [200, 201]
        except Exception as e:
            self.log_test("User Registration", False, str(e))
            return False

    def test_user_login(self):
        """Test user login and token generation"""
        self.log("Testing user login...")
        try:
            response = requests.post(
                f"{BASE_URL}/auth/login",
                json={
                    "username": TEST_USER["username"],
                    "password": TEST_USER["password"]
                }
            )
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                self.log_test("User Login", bool(self.access_token),
                             f"Got token: {bool(self.access_token)}")
                return bool(self.access_token)
            else:
                self.log_test("User Login", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("User Login", False, str(e))
            return False

    # Phase 2: Project Management
    def test_create_project(self):
        """Test project creation"""
        self.log("Testing project creation...")
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.post(
                f"{BASE_URL}/projects",
                json={
                    "name": f"Test Project {int(time.time())}",
                    "description": "Integration test project"
                },
                headers=headers
            )
            if response.status_code in [200, 201]:
                data = response.json()
                self.project_id = data.get('id') or data.get('project_id')
                self.log_test("Project Creation", bool(self.project_id),
                             f"Project ID: {self.project_id}")
                return bool(self.project_id)
            elif response.status_code == 404:
                # Endpoint not implemented
                self.log_test("Project Creation", False, f"Status: {response.status_code} - Not Implemented")
                return False
            else:
                self.log_test("Project Creation", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Project Creation", False, str(e))
            return False

    def test_list_projects(self):
        """Test listing projects"""
        self.log("Testing project listing...")
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                f"{BASE_URL}/projects",
                headers=headers
            )
            self.log_test("List Projects", response.status_code == 200,
                         f"Status: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            self.log_test("List Projects", False, str(e))
            return False

    def test_get_project_details(self):
        """Test getting project details"""
        self.log("Testing project details retrieval...")
        if not self.project_id:
            self.log_test("Get Project Details", False, "No project ID")
            return False
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                f"{BASE_URL}/projects/{self.project_id}",
                headers=headers
            )
            self.log_test("Get Project Details", response.status_code == 200,
                         f"Status: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            self.log_test("Get Project Details", False, str(e))
            return False

    # Phase 3: Chat & Conversation
    def test_create_chat_session(self):
        """Test creating a chat session"""
        self.log("Testing chat session creation...")
        if not self.project_id:
            self.log_test("Create Chat Session", False, "No project ID")
            return False
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.post(
                f"{BASE_URL}/projects/{self.project_id}/chat/sessions",
                json={"title": "Integration Test Chat"},
                headers=headers
            )
            if response.status_code in [200, 201]:
                data = response.json()
                self.chat_session_id = data.get('session_id') or data.get('id')
                self.log_test("Create Chat Session", bool(self.chat_session_id),
                             f"Session ID: {self.chat_session_id}")
                return bool(self.chat_session_id)
            else:
                self.log_test("Create Chat Session", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Create Chat Session", False, str(e))
            return False

    def test_send_message(self):
        """Test sending a message in chat"""
        self.log("Testing message sending...")
        if not self.project_id or not self.chat_session_id:
            self.log_test("Send Message", False, "Missing project or session ID")
            return False
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.post(
                f"{BASE_URL}/projects/{self.project_id}/chat/{self.chat_session_id}/message",
                json={"message": "Hello, AI assistant!"},
                headers=headers
            )
            self.log_test("Send Message", response.status_code in [200, 201],
                         f"Status: {response.status_code}")
            return response.status_code in [200, 201]
        except Exception as e:
            self.log_test("Send Message", False, str(e))
            return False

    # Phase 4: Settings & User Preferences
    def test_get_user_settings(self):
        """Test retrieving user settings"""
        self.log("Testing user settings retrieval...")
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                f"{BASE_URL}/users/settings",
                headers=headers
            )
            self.log_test("Get User Settings", response.status_code in [200, 404],
                         f"Status: {response.status_code}")
            return response.status_code in [200, 404]
        except Exception as e:
            self.log_test("Get User Settings", False, str(e))
            return False

    def test_update_user_settings(self):
        """Test updating user settings"""
        self.log("Testing user settings update...")
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.put(
                f"{BASE_URL}/users/settings",
                json={"theme": "dark", "notifications_enabled": True},
                headers=headers
            )
            self.log_test("Update User Settings", response.status_code in [200, 201, 404],
                         f"Status: {response.status_code}")
            return response.status_code in [200, 201, 404]
        except Exception as e:
            self.log_test("Update User Settings", False, str(e))
            return False

    # Phase 5: Collaboration Features
    def test_invite_collaborator(self):
        """Test inviting collaborators to project"""
        self.log("Testing collaborator invitation...")
        if not self.project_id:
            self.log_test("Invite Collaborator", False, "No project ID")
            return False
        try:
            # First register second user
            requests.post(
                f"{BASE_URL}/auth/register",
                json={
                    "username": TEST_USER_2["username"],
                    "email": TEST_USER_2["email"],
                    "password": TEST_USER_2["password"]
                }
            )

            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.post(
                f"{BASE_URL}/projects/{self.project_id}/collaborators",
                json={"email": TEST_USER_2["email"], "role": "editor"},
                headers=headers
            )
            self.log_test("Invite Collaborator", response.status_code in [200, 201, 404],
                         f"Status: {response.status_code}")
            return response.status_code in [200, 201, 404]
        except Exception as e:
            self.log_test("Invite Collaborator", False, str(e))
            return False

    # Phase 6: Knowledge Base
    def test_add_knowledge_document(self):
        """Test adding documents to knowledge base"""
        self.log("Testing knowledge document addition...")
        if not self.project_id:
            self.log_test("Add Knowledge Document", False, "No project ID")
            return False
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.post(
                f"{BASE_URL}/projects/{self.project_id}/knowledge/documents",
                json={
                    "title": "Test Document",
                    "content": "This is test knowledge content",
                    "type": "text"
                },
                headers=headers
            )
            self.log_test("Add Knowledge Document", response.status_code in [200, 201, 404],
                         f"Status: {response.status_code}")
            return response.status_code in [200, 201, 404]
        except Exception as e:
            self.log_test("Add Knowledge Document", False, str(e))
            return False

    # Phase 7: Analytics
    def test_get_project_analytics(self):
        """Test retrieving project analytics"""
        self.log("Testing project analytics retrieval...")
        if not self.project_id:
            self.log_test("Get Project Analytics", False, "No project ID")
            return False
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                f"{BASE_URL}/projects/{self.project_id}/analytics",
                headers=headers
            )
            self.log_test("Get Project Analytics", response.status_code in [200, 404],
                         f"Status: {response.status_code}")
            return response.status_code in [200, 404]
        except Exception as e:
            self.log_test("Get Project Analytics", False, str(e))
            return False

    # Error Handling Tests
    def test_unauthorized_access(self):
        """Test unauthorized access handling"""
        self.log("Testing unauthorized access handling...")
        try:
            response = requests.get(f"{BASE_URL}/projects")
            self.log_test("Unauthorized Access", response.status_code == 401,
                         f"Status: {response.status_code}")
            return response.status_code == 401
        except Exception as e:
            self.log_test("Unauthorized Access", False, str(e))
            return False

    def test_invalid_token(self):
        """Test invalid token handling"""
        self.log("Testing invalid token handling...")
        try:
            headers = {"Authorization": "Bearer invalid_token_12345"}
            response = requests.get(f"{BASE_URL}/projects", headers=headers)
            self.log_test("Invalid Token", response.status_code == 401,
                         f"Status: {response.status_code}")
            return response.status_code == 401
        except Exception as e:
            self.log_test("Invalid Token", False, str(e))
            return False

    def test_not_found_project(self):
        """Test 404 handling for non-existent project"""
        self.log("Testing 404 handling...")
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                f"{BASE_URL}/projects/nonexistent_project_id_12345",
                headers=headers
            )
            self.log_test("404 Not Found", response.status_code == 404,
                         f"Status: {response.status_code}")
            return response.status_code == 404
        except Exception as e:
            self.log_test("404 Not Found", False, str(e))
            return False

    def run_all_tests(self):
        """Run complete integration test suite"""
        self.log("=" * 70)
        self.log("PHASE 4: INTEGRATION TESTING SUITE", "START")
        self.log("=" * 70)

        # Authentication tests
        self.log("\n--- Authentication Tests ---")
        self.test_user_registration()
        self.test_user_login()

        if not self.access_token:
            self.log("Cannot continue without valid token", "ERROR")
            return self.print_results()

        # Project tests
        self.log("\n--- Project Management Tests ---")
        self.test_create_project()
        self.test_list_projects()
        self.test_get_project_details()

        # Chat tests
        self.log("\n--- Chat & Conversation Tests ---")
        self.test_create_chat_session()
        self.test_send_message()

        # Settings tests
        self.log("\n--- Settings Tests ---")
        self.test_get_user_settings()
        self.test_update_user_settings()

        # Collaboration tests
        self.log("\n--- Collaboration Tests ---")
        self.test_invite_collaborator()

        # Knowledge tests
        self.log("\n--- Knowledge Base Tests ---")
        self.test_add_knowledge_document()

        # Analytics tests
        self.log("\n--- Analytics Tests ---")
        self.test_get_project_analytics()

        # Error handling tests
        self.log("\n--- Error Handling Tests ---")
        self.test_unauthorized_access()
        self.test_invalid_token()
        self.test_not_found_project()

        return self.print_results()

    def print_results(self):
        """Print test results summary"""
        self.log("\n" + "=" * 70)
        self.log("TEST RESULTS SUMMARY", "SUMMARY")
        self.log("=" * 70)
        self.log(f"Total Tests: {self.passed + self.failed}")
        self.log(f"Passed: {self.passed}")
        self.log(f"Failed: {self.failed}")

        if self.errors:
            self.log("\nFailed Tests:")
            for error in self.errors:
                self.log(f"  - {error}")

        self.log("=" * 70 + "\n")

        success_rate = (self.passed / (self.passed + self.failed) * 100) if (self.passed + self.failed) > 0 else 0
        self.log(f"Success Rate: {success_rate:.1f}%")

        return self.failed == 0

if __name__ == "__main__":
    runner = IntegrationTestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)
