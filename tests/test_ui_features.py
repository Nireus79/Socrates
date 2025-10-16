"""
Comprehensive UI Testing Script for Phase C Sessions 1-4
=========================================================

Tests all UI features built in Phase C:
- Session 1: Authentication & Settings
- Session 2: Project Management
- Session 3: Chat Mode & Socratic UI
- Session 4: GitHub Repository Import

This script tests the Flask application by making HTTP requests
and verifying responses.
"""

import requests

BASE_URL = "http://localhost:5002"


class UITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []

    def test(self, name: str, func):
        """Run a test and track results."""
        try:
            print(f"\n{'=' * 60}")
            print(f"TEST: {name}")
            print('=' * 60)
            result = func()
            if result:
                print(f"[PASS] {name}")
                self.test_results.append((name, "PASS", None))
            else:
                print(f"[FAIL] {name}")
                self.test_results.append((name, "FAIL", "Test returned False"))
        except Exception as e:
            print(f"[ERROR] {name}")
            print(f"   Error: {str(e)}")
            self.test_results.append((name, "ERROR", str(e)))

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        passed = sum(1 for _, status, _ in self.test_results if status == "PASS")
        failed = sum(1 for _, status, _ in self.test_results if status == "FAIL")
        errors = sum(1 for _, status, _ in self.test_results if status == "ERROR")
        total = len(self.test_results)

        print(f"Total Tests: {total}")
        print(f"[+] Passed: {passed}")
        print(f"[-] Failed: {failed}")
        print(f"[!] Errors: {errors}")
        print(f"Success Rate: {(passed / total * 100):.1f}%")

        if failed > 0 or errors > 0:
            print("\nFailed/Error Tests:")
            for name, status, error in self.test_results:
                if status != "PASS":
                    print(f"  - {name}: {status}")
                    if error:
                        print(f"    {error}")

    # =================================================================
    # SESSION 1: AUTHENTICATION & SETTINGS TESTS
    # =================================================================

    def test_home_page(self) -> bool:
        """Test that home page loads."""
        response = self.session.get(f"{self.base_url}/")
        print(f"Status: {response.status_code}")
        return response.status_code == 200

    def test_login_page(self) -> bool:
        """Test that login page loads."""
        response = self.session.get(f"{self.base_url}/login")
        print(f"Status: {response.status_code}")
        return response.status_code == 200 and b"login" in response.content.lower()

    def test_register_page(self) -> bool:
        """Test that registration page loads."""
        response = self.session.get(f"{self.base_url}/register")
        print(f"Status: {response.status_code}")
        return response.status_code == 200 and b"register" in response.content.lower()

    def test_settings_page_redirect(self) -> bool:
        """Test that settings page redirects to login when not authenticated."""
        response = self.session.get(f"{self.base_url}/settings", allow_redirects=False)
        print(f"Status: {response.status_code}")
        # Should redirect to login
        return response.status_code in [302, 303, 307, 401]

    # =================================================================
    # SESSION 2: PROJECT MANAGEMENT TESTS
    # =================================================================

    def test_projects_page_redirect(self) -> bool:
        """Test that projects page redirects to login when not authenticated."""
        response = self.session.get(f"{self.base_url}/projects", allow_redirects=False)
        print(f"Status: {response.status_code}")
        return response.status_code in [302, 303, 307, 401]

    def test_dashboard_redirect(self) -> bool:
        """Test that dashboard redirects to login when not authenticated."""
        response = self.session.get(f"{self.base_url}/dashboard", allow_redirects=False)
        print(f"Status: {response.status_code}")
        return response.status_code in [302, 303, 307, 401]

    # =================================================================
    # SESSION 3: CHAT MODE & SOCRATIC UI TESTS
    # =================================================================

    def test_sessions_page_redirect(self) -> bool:
        """Test that sessions page redirects to login when not authenticated."""
        response = self.session.get(f"{self.base_url}/sessions", allow_redirects=False)
        print(f"Status: {response.status_code}")
        return response.status_code in [302, 303, 307, 401]

    # =================================================================
    # SESSION 4: GITHUB REPOSITORY IMPORT TESTS
    # =================================================================

    def test_repositories_page_redirect(self) -> bool:
        """Test that repositories page redirects to login when not authenticated."""
        response = self.session.get(f"{self.base_url}/repositories", allow_redirects=False)
        print(f"Status: {response.status_code}")
        return response.status_code in [302, 303, 307, 401]

    def test_repository_import_page_redirect(self) -> bool:
        """Test that import page redirects to login when not authenticated."""
        response = self.session.get(f"{self.base_url}/repositories/import", allow_redirects=False)
        print(f"Status: {response.status_code}")
        return response.status_code in [302, 303, 307, 401]

    # =================================================================
    # ADDITIONAL TESTS
    # =================================================================

    def test_code_dashboard_redirect(self) -> bool:
        """Test that code dashboard redirects to login when not authenticated."""
        response = self.session.get(f"{self.base_url}/code", allow_redirects=False)
        print(f"Status: {response.status_code}")
        return response.status_code in [302, 303, 307, 401]

    def test_api_health(self) -> bool:
        """Test that API health endpoint works."""
        try:
            response = self.session.get(f"{self.base_url}/api/health")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {data}")
                return True
            return False
        except Exception as e:
            print(f"Health endpoint not available: {e}")
            return False

    def test_static_resources(self) -> bool:
        """Test that Bootstrap CSS loads."""
        # Check if base.html references Bootstrap
        response = self.session.get(f"{self.base_url}/")
        if response.status_code == 200:
            content = response.text
            has_bootstrap = "bootstrap" in content.lower()
            has_icons = "bootstrap-icons" in content.lower()
            print(f"Has Bootstrap: {has_bootstrap}")
            print(f"Has Bootstrap Icons: {has_icons}")
            return has_bootstrap and has_icons
        return False


def run_all_tests():
    """Run all UI tests."""
    print("=" * 60)
    print("SOCRATIC RAG ENHANCED - UI TESTING SUITE")
    print("Phase C Sessions 1-4 Verification")
    print("=" * 60)

    tester = UITester()

    # Session 1: Authentication & Settings
    print("\n" + "=" * 60)
    print("PHASE C SESSION 1: AUTHENTICATION & SETTINGS")
    print("=" * 60)
    tester.test("Home page loads", tester.test_home_page)
    tester.test("Login page loads", tester.test_login_page)
    tester.test("Register page loads", tester.test_register_page)
    tester.test("Settings requires authentication", tester.test_settings_page_redirect)

    # Session 2: Project Management
    print("\n" + "=" * 60)
    print("PHASE C SESSION 2: PROJECT MANAGEMENT")
    print("=" * 60)
    tester.test("Projects page requires authentication", tester.test_projects_page_redirect)
    tester.test("Dashboard requires authentication", tester.test_dashboard_redirect)

    # Session 3: Chat Mode & Socratic UI
    print("\n" + "=" * 60)
    print("PHASE C SESSION 3: CHAT MODE & SOCRATIC UI")
    print("=" * 60)
    tester.test("Sessions page requires authentication", tester.test_sessions_page_redirect)

    # Session 4: GitHub Repository Import
    print("\n" + "=" * 60)
    print("PHASE C SESSION 4: GITHUB REPOSITORY IMPORT")
    print("=" * 60)
    tester.test("Repositories page requires authentication", tester.test_repositories_page_redirect)
    tester.test("Repository import page requires authentication", tester.test_repository_import_page_redirect)

    # Additional Tests
    print("\n" + "=" * 60)
    print("ADDITIONAL TESTS")
    print("=" * 60)
    tester.test("Code dashboard requires authentication", tester.test_code_dashboard_redirect)
    tester.test("API health endpoint", tester.test_api_health)
    tester.test("Static resources (Bootstrap/Icons)", tester.test_static_resources)

    # Print summary
    tester.print_summary()

    return tester


if __name__ == "__main__":
    print("\nWARNING: Make sure Flask is running on http://localhost:5002")
    print("   Run: python run.py --no-browser --port 5002\n")

    input("Press Enter to start testing...")

    tester = run_all_tests()

    print("\n" + "=" * 60)
    print("Testing complete! Review results above.")
    print("=" * 60)
