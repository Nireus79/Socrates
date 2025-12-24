"""
Comprehensive API Testing Suite
Tests all major workflows through the API endpoints
"""

import requests
import json
from datetime import datetime
import time

BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

# Test results tracking
test_results = []

def test_result(name, passed, details=""):
    """Track test result"""
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} {name}")
    if details:
        print(f"       {details}")
    test_results.append((name, passed))
    return passed

def print_section(title):
    """Print section header"""
    print("\n" + "="*70)
    print(title)
    print("="*70 + "\n")

# ============================================================================
# Test 1: Health Check
# ============================================================================

def test_health_check():
    """Test API health endpoint"""
    print_section("TEST 1: Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health")
        passed = response.status_code == 200
        test_result("Health endpoint", passed, f"Status: {response.status_code}")
        return passed
    except Exception as e:
        test_result("Health endpoint", False, f"Error: {str(e)}")
        return False

# ============================================================================
# Test 2: User Registration
# ============================================================================

def test_user_registration():
    """Test user registration"""
    print_section("TEST 2: User Registration")
    try:
        username = f"testuser_{int(datetime.now().timestamp() * 1000)}"
        email = f"{username}@test.local"

        payload = {
            "username": username,
            "email": email,
            "password": "TestPassword123!"
        }

        response = requests.post(
            f"{BASE_URL}/auth/register",
            json=payload,
            headers=HEADERS
        )

        passed = response.status_code in [200, 201]

        if response.status_code in [200, 201]:
            data = response.json()
            has_tokens = "access_token" in data and "refresh_token" in data
            has_user = "user" in data
            test_result("User registration", has_tokens and has_user,
                       f"Status: {response.status_code}, Tokens: {has_tokens}, User: {has_user}")

            # Store for next tests
            return {
                "username": username,
                "email": email,
                "access_token": data.get("access_token"),
                "refresh_token": data.get("refresh_token")
            }
        else:
            test_result("User registration", False,
                       f"Status: {response.status_code}, Response: {response.text[:100]}")
            return None

    except Exception as e:
        test_result("User registration", False, f"Error: {str(e)}")
        return None

# ============================================================================
# Test 3: User Login
# ============================================================================

def test_user_login(username, password):
    """Test user login"""
    print_section("TEST 3: User Login")
    try:
        payload = {
            "username": username,
            "password": password
        }

        response = requests.post(
            f"{BASE_URL}/auth/login",
            json=payload,
            headers=HEADERS
        )

        if response.status_code == 200:
            data = response.json()
            has_tokens = "access_token" in data and "refresh_token" in data
            has_user = "user" in data
            test_result("User login", has_tokens and has_user,
                       f"Status: {response.status_code}")
            return {
                "access_token": data.get("access_token"),
                "refresh_token": data.get("refresh_token")
            }
        else:
            test_result("User login", False, f"Status: {response.status_code}")
            return None

    except Exception as e:
        test_result("User login", False, f"Error: {str(e)}")
        return None

# ============================================================================
# Test 4: Get User Profile
# ============================================================================

def test_get_profile(access_token):
    """Test getting user profile"""
    print_section("TEST 4: Get User Profile")
    try:
        headers = {**HEADERS, "Authorization": f"Bearer {access_token}"}
        response = requests.get(
            f"{BASE_URL}/auth/me",
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            has_username = "username" in data
            has_subscription = "subscription_tier" in data
            test_result("Get profile", has_username and has_subscription,
                       f"Status: {response.status_code}, Username: {data.get('username')}")

            # Enable testing mode to bypass subscription checks
            print("Enabling testing mode for user...")
            test_mode_response = requests.put(
                f"{BASE_URL}/auth/me/testing-mode?enabled=true",
                headers=headers
            )
            if test_mode_response.status_code == 200:
                print("      [OK] Testing mode enabled")

            return True
        else:
            test_result("Get profile", False, f"Status: {response.status_code}")
            return False

    except Exception as e:
        test_result("Get profile", False, f"Error: {str(e)}")
        return False

# ============================================================================
# Test 5: Create Project
# ============================================================================

def test_create_project(access_token):
    """Test project creation"""
    print_section("TEST 5: Create Project")
    try:
        headers = {**HEADERS, "Authorization": f"Bearer {access_token}"}

        payload = {
            "name": f"Test Project {int(datetime.now().timestamp())}",
            "description": "Test project for comprehensive API testing",
            "knowledge_base_content": "Test knowledge base content",
            "owner": "test"  # Note: owner should be extracted from JWT, but including for compatibility
        }

        response = requests.post(
            f"{BASE_URL}/projects",
            json=payload,
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            has_id = "project_id" in data
            has_name = "name" in data
            has_owner = "owner" in data
            test_result("Create project", has_id and has_name and has_owner,
                       f"Status: {response.status_code}, Project ID: {data.get('project_id')}")
            return data.get("project_id")
        else:
            test_result("Create project", False,
                       f"Status: {response.status_code}, Response: {response.text[:200]}")
            return None

    except Exception as e:
        test_result("Create project", False, f"Error: {str(e)}")
        return None

# ============================================================================
# Test 6: Get Projects
# ============================================================================

def test_get_projects(access_token):
    """Test getting projects list"""
    print_section("TEST 6: Get Projects")
    try:
        headers = {**HEADERS, "Authorization": f"Bearer {access_token}"}
        response = requests.get(
            f"{BASE_URL}/projects",
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            has_projects = "projects" in data
            has_total = "total" in data
            is_list = isinstance(data.get("projects"), list)
            test_result("Get projects", has_projects and has_total and is_list,
                       f"Status: {response.status_code}, Count: {data.get('total')}")
            return True
        else:
            test_result("Get projects", False, f"Status: {response.status_code}")
            return False

    except Exception as e:
        test_result("Get projects", False, f"Error: {str(e)}")
        return False

# ============================================================================
# Test 7: Get Project Details
# ============================================================================

def test_get_project_details(access_token, project_id):
    """Test getting project details"""
    print_section("TEST 7: Get Project Details")
    try:
        headers = {**HEADERS, "Authorization": f"Bearer {access_token}"}
        response = requests.get(
            f"{BASE_URL}/projects/{project_id}",
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            matches_id = data.get("project_id") == project_id
            has_details = "name" in data and "owner" in data
            test_result("Get project details", matches_id and has_details,
                       f"Status: {response.status_code}, Project: {data.get('name')}")
            return True
        else:
            test_result("Get project details", False, f"Status: {response.status_code}")
            return False

    except Exception as e:
        test_result("Get project details", False, f"Error: {str(e)}")
        return False

# ============================================================================
# Test 8: Update Project
# ============================================================================

def test_update_project(access_token, project_id):
    """Test updating project"""
    print_section("TEST 8: Update Project")
    try:
        headers = {**HEADERS, "Authorization": f"Bearer {access_token}"}

        payload = {
            "name": f"Updated Project {int(datetime.now().timestamp())}",
            "phase": "implementation"
        }

        response = requests.put(
            f"{BASE_URL}/projects/{project_id}",
            json=payload,
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            updated = data.get("name") == payload["name"]
            phase_updated = data.get("phase") == payload["phase"]
            test_result("Update project", updated and phase_updated,
                       f"Status: {response.status_code}, Name: {data.get('name')}")
            return True
        else:
            test_result("Update project", False, f"Status: {response.status_code}")
            return False

    except Exception as e:
        test_result("Update project", False, f"Error: {str(e)}")
        return False

# ============================================================================
# Test 9: Refresh Token
# ============================================================================

def test_refresh_token(refresh_token):
    """Test token refresh"""
    print_section("TEST 9: Refresh Token")
    try:
        payload = {"refresh_token": refresh_token}
        response = requests.post(
            f"{BASE_URL}/auth/refresh",
            json=payload,
            headers=HEADERS
        )

        if response.status_code == 200:
            data = response.json()
            has_new_token = "access_token" in data
            test_result("Refresh token", has_new_token,
                       f"Status: {response.status_code}")
            return data.get("access_token")
        else:
            test_result("Refresh token", False, f"Status: {response.status_code}")
            return None

    except Exception as e:
        test_result("Refresh token", False, f"Error: {str(e)}")
        return None

# ============================================================================
# Test 10: Logout
# ============================================================================

def test_logout(access_token):
    """Test logout"""
    print_section("TEST 10: Logout")
    try:
        headers = {**HEADERS, "Authorization": f"Bearer {access_token}"}
        response = requests.post(
            f"{BASE_URL}/auth/logout",
            headers=headers
        )

        passed = response.status_code == 200
        test_result("Logout", passed, f"Status: {response.status_code}")
        return passed

    except Exception as e:
        test_result("Logout", False, f"Error: {str(e)}")
        return False

# ============================================================================
# Main Test Suite
# ============================================================================

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("COMPREHENSIVE API TEST SUITE")
    print("Testing all major workflows through API endpoints")
    print("="*70)

    # Test 1: Health Check
    if not test_health_check():
        print("\n[CRITICAL] API is not responding. Aborting tests.")
        return False

    time.sleep(1)

    # Test 2: User Registration
    user_data = test_user_registration()
    if not user_data:
        print("\n[ERROR] User registration failed. Cannot continue.")
        return False

    time.sleep(1)

    # Test 3: User Login
    login_tokens = test_user_login(user_data["username"], "TestPassword123!")
    if not login_tokens:
        print("\n[ERROR] User login failed. Cannot continue.")
        return False

    access_token = login_tokens["access_token"]
    refresh_token = login_tokens["refresh_token"]

    time.sleep(1)

    # Test 4: Get Profile
    test_get_profile(access_token)

    time.sleep(1)

    # Test 5: Create Project
    project_id = test_create_project(access_token)
    if not project_id:
        print("\n[WARNING] Project creation failed, skipping project tests.")
    else:
        time.sleep(1)

        # Test 6: Get Projects
        test_get_projects(access_token)

        time.sleep(1)

        # Test 7: Get Project Details
        test_get_project_details(access_token, project_id)

        time.sleep(1)

        # Test 8: Update Project
        test_update_project(access_token, project_id)

        time.sleep(1)

    # Test 9: Refresh Token
    new_token = test_refresh_token(refresh_token)

    time.sleep(1)

    # Test 10: Logout (use new token if refresh worked, otherwise use original)
    logout_token = new_token if new_token else access_token
    test_logout(logout_token)

    # Print Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70 + "\n")

    passed_count = sum(1 for _, passed in test_results if passed)
    total_count = len(test_results)

    for name, passed in test_results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {name}")

    print(f"\nResult: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n" + "="*70)
        print("[SUCCESS] ALL API TESTS PASSED!")
        print("="*70)
        print("\nWorkflows Verified:")
        print("  1. API health check")
        print("  2. User registration with tokens")
        print("  3. User login with credentials")
        print("  4. User profile retrieval")
        print("  5. Project creation")
        print("  6. Project listing")
        print("  7. Project details retrieval")
        print("  8. Project updates")
        print("  9. Token refresh")
        print(" 10. User logout")
        print("\nSTATUS: Ready for advanced feature testing")
        return True
    else:
        print(f"\n[FAIL] {total_count - passed_count} test(s) failed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
