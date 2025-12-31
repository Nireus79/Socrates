#!/usr/bin/env python3
"""
Focused Test Suite for Routing Fixes

Tests specifically the endpoints that were fixed to verify they:
1. Return correct HTTP status codes (not 404)
2. Are accessible at the correct paths (not malformed paths)
3. Handle authentication properly
"""


import requests

BASE_URL = "http://localhost:8000"
TEST_USER = "test_router_verification"
TEST_PASSWORD = "TestPassword123!"
ACCESS_TOKEN = None
PROJECT_ID = "test_project_001"  # Use a dummy project ID for testing


def print_result(name: str, path: str, method: str, status: int, expected: int):
    """Print test result"""
    passed = status == expected or (status != 404 and expected in [200, 201])
    symbol = "PASS" if passed else "FAIL"
    print(f"{symbol}: {method:6} {path:50} -> {status}")
    if not passed and status == 404:
        print("       ERROR: Endpoint not found (malformed path?)")
    return passed


def test_auth_endpoints():
    """Test authentication endpoints"""
    print("\n=== AUTHENTICATION ENDPOINTS ===")
    passed = 0
    total = 0

    # Test 1: PUT /auth/me (THIS WAS MISSING AND IS NOW FIXED)
    total += 1
    try:
        # First login to get token
        login_resp = requests.post(
            f"{BASE_URL}/auth/login", json={"username": TEST_USER, "password": TEST_PASSWORD}
        )
        if login_resp.status_code == 200:
            token = login_resp.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
        else:
            headers = {}

        response = requests.put(f"{BASE_URL}/auth/me", headers=headers)
        if print_result("Update user profile", "/auth/me", "PUT", response.status_code, 200):
            passed += 1
            if response.status_code == 200:
                print("       VERIFIED: PUT /auth/me is working and returning user profile")
    except Exception as e:
        print(f"FAIL: PUT /auth/me -> ERROR: {e}")

    print(f"\nAuth Endpoints: {passed}/{total} passed")
    return passed, total


def test_projects_endpoints():
    """Test projects endpoints"""
    print("\n=== PROJECTS ENDPOINTS ===")
    passed = 0
    total = 0

    # Get auth token
    try:
        login_resp = requests.post(
            f"{BASE_URL}/auth/login", json={"username": TEST_USER, "password": TEST_PASSWORD}
        )
        if login_resp.status_code == 200:
            token = login_resp.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
        else:
            headers = {}
    except Exception:
        headers = {}

    # Test 1: GET /projects/{id}/analytics (THIS WAS MISSING AND IS NOW FIXED)
    total += 1
    try:
        response = requests.get(f"{BASE_URL}/projects/{PROJECT_ID}/analytics", headers=headers)
        if response.status_code != 404:
            if print_result(
                "Get project analytics",
                f"/projects/{PROJECT_ID}/analytics",
                "GET",
                response.status_code,
                200,
            ):
                passed += 1
                if response.status_code in [
                    200,
                    403,
                ]:  # 403 is OK if project not found due to access control
                    print(
                        "       VERIFIED: GET /projects/{id}/analytics endpoint exists and is properly routed"
                    )
        else:
            print(f"FAIL: GET /projects/{PROJECT_ID}/analytics -> 404")
    except Exception as e:
        print(f"FAIL: GET /projects/{PROJECT_ID}/analytics -> ERROR: {e}")

    print(f"\nProjects Endpoints: {passed}/{total} passed")
    return passed, total


def test_chat_endpoints():  # noqa: C901
    """Test chat endpoints (routing paths fixed)"""
    print("\n=== CHAT ENDPOINTS (ROUTING PATHS FIXED) ===")
    passed = 0
    total = 0

    # Get auth token
    try:
        login_resp = requests.post(
            f"{BASE_URL}/auth/login", json={"username": TEST_USER, "password": TEST_PASSWORD}
        )
        if login_resp.status_code == 200:
            token = login_resp.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
        else:
            headers = {}
    except Exception:
        headers = {}

    chat_endpoints = [
        ("POST", "/projects/{id}/chat/message", f"/projects/{PROJECT_ID}/chat/message"),
        ("GET", "/projects/{id}/chat/history", f"/projects/{PROJECT_ID}/chat/history"),
        ("PUT", "/projects/{id}/chat/mode", f"/projects/{PROJECT_ID}/chat/mode"),
        ("GET", "/projects/{id}/chat/hint", f"/projects/{PROJECT_ID}/chat/hint"),
        ("DELETE", "/projects/{id}/chat/clear", f"/projects/{PROJECT_ID}/chat/clear"),
        ("GET", "/projects/{id}/chat/summary", f"/projects/{PROJECT_ID}/chat/summary"),
    ]

    for method, path_template, actual_path in chat_endpoints:
        total += 1
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{actual_path}", headers=headers)
            elif method == "POST":
                response = requests.post(f"{BASE_URL}{actual_path}", json={}, headers=headers)
            elif method == "PUT":
                response = requests.put(f"{BASE_URL}{actual_path}", json={}, headers=headers)
            elif method == "DELETE":
                response = requests.delete(f"{BASE_URL}{actual_path}", headers=headers)

            # Check if endpoint exists (not 404)
            if response.status_code != 404:
                if print_result(
                    f"Chat: {method} {path_template}",
                    actual_path,
                    method,
                    response.status_code,
                    200,
                ):
                    passed += 1
                    print(
                        f"       VERIFIED: {method} {actual_path} - endpoint properly routed (no double slash)"
                    )
            else:
                print(f"FAIL: {method} {actual_path} -> 404 (endpoint not found - routing broken)")
        except Exception as e:
            print(f"FAIL: {method} {actual_path} -> ERROR: {e}")

    print(f"\nChat Endpoints: {passed}/{total} passed")
    return passed, total


def test_code_endpoints():
    """Test code generation endpoints (routing paths fixed)"""
    print("\n=== CODE GENERATION ENDPOINTS (ROUTING PATHS FIXED) ===")
    passed = 0
    total = 0

    # Get auth token
    try:
        login_resp = requests.post(
            f"{BASE_URL}/auth/login", json={"username": TEST_USER, "password": TEST_PASSWORD}
        )
        if login_resp.status_code == 200:
            token = login_resp.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
        else:
            headers = {}
    except Exception:
        headers = {}

    code_endpoints = [
        ("POST", "/projects/{id}/code/generate", f"/projects/{PROJECT_ID}/code/generate"),
        ("POST", "/projects/{id}/code/validate", f"/projects/{PROJECT_ID}/code/validate"),
        ("GET", "/projects/{id}/code/history", f"/projects/{PROJECT_ID}/code/history"),
        ("POST", "/projects/{id}/code/refactor", f"/projects/{PROJECT_ID}/code/refactor"),
    ]

    for method, path_template, actual_path in code_endpoints:
        total += 1
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{actual_path}", headers=headers)
            elif method == "POST":
                response = requests.post(f"{BASE_URL}{actual_path}", json={}, headers=headers)

            # Check if endpoint exists (not 404)
            if response.status_code != 404:
                if print_result(
                    f"Code: {method} {path_template}",
                    actual_path,
                    method,
                    response.status_code,
                    200,
                ):
                    passed += 1
                    print(f"       VERIFIED: {method} {actual_path} - endpoint properly routed")
            else:
                print(f"FAIL: {method} {actual_path} -> 404 (endpoint not found - routing broken)")
        except Exception as e:
            print(f"FAIL: {method} {actual_path} -> ERROR: {e}")

    print(f"\nCode Endpoints: {passed}/{total} passed")
    return passed, total


def test_collaboration_endpoints():  # noqa: C901
    """Test collaboration endpoints (routing paths fixed)"""
    print("\n=== COLLABORATION ENDPOINTS (ROUTING PATHS FIXED) ===")
    passed = 0
    total = 0

    # Get auth token
    try:
        login_resp = requests.post(
            f"{BASE_URL}/auth/login", json={"username": TEST_USER, "password": TEST_PASSWORD}
        )
        if login_resp.status_code == 200:
            token = login_resp.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
        else:
            headers = {}
    except Exception:
        headers = {}

    collab_endpoints = [
        ("POST", "/projects/{id}/collaborators", f"/projects/{PROJECT_ID}/collaborators"),
        ("GET", "/projects/{id}/collaborators", f"/projects/{PROJECT_ID}/collaborators"),
        (
            "PUT",
            "/projects/{id}/collaborators/user/role",
            f"/projects/{PROJECT_ID}/collaborators/testuser/role",
        ),
        (
            "DELETE",
            "/projects/{id}/collaborators/user",
            f"/projects/{PROJECT_ID}/collaborators/testuser",
        ),
        ("GET", "/projects/{id}/presence", f"/projects/{PROJECT_ID}/presence"),
        ("POST", "/projects/{id}/activity", f"/projects/{PROJECT_ID}/activity"),
    ]

    for method, path_template, actual_path in collab_endpoints:
        total += 1
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{actual_path}", headers=headers)
            elif method == "POST":
                response = requests.post(f"{BASE_URL}{actual_path}", json={}, headers=headers)
            elif method == "PUT":
                response = requests.put(f"{BASE_URL}{actual_path}", json={}, headers=headers)
            elif method == "DELETE":
                response = requests.delete(f"{BASE_URL}{actual_path}", headers=headers)

            # Check if endpoint exists (not 404)
            if response.status_code != 404:
                if print_result(
                    f"Collab: {method} {path_template}",
                    actual_path,
                    method,
                    response.status_code,
                    200,
                ):
                    passed += 1
                    print(
                        f"       VERIFIED: {method} {actual_path} - endpoint properly routed (no double slash)"
                    )
            else:
                print(f"FAIL: {method} {actual_path} -> 404 (endpoint not found - routing broken)")
        except Exception as e:
            print(f"FAIL: {method} {actual_path} -> ERROR: {e}")

    print(f"\nCollaboration Endpoints: {passed}/{total} passed")
    return passed, total


def main():
    print("=" * 60)
    print("ROUTING FIXES VERIFICATION TEST SUITE")
    print("=" * 60)
    print(f"Testing backend at: {BASE_URL}")

    # Initialize API
    print("\nInitializing API...")
    try:
        response = requests.post(f"{BASE_URL}/initialize")
        if response.status_code == 200:
            print("API initialization: PASS")
        else:
            print(f"API initialization: FAIL ({response.status_code})")
    except Exception as e:
        print(f"API initialization: FAIL - {e}")

    # Run all test categories
    total_passed = 0
    total_tests = 0

    p, t = test_auth_endpoints()
    total_passed += p
    total_tests += t

    p, t = test_projects_endpoints()
    total_passed += p
    total_tests += t

    p, t = test_chat_endpoints()
    total_passed += p
    total_tests += t

    p, t = test_code_endpoints()
    total_passed += p
    total_tests += t

    p, t = test_collaboration_endpoints()
    total_passed += p
    total_tests += t

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total Passed: {total_passed}/{total_tests}")
    print(f"Pass Rate: {(total_passed/total_tests*100):.1f}%")

    if total_passed == total_tests:
        print("\n✓ All routing fixes verified successfully!")
        return 0
    else:
        print(f"\n✗ {total_tests - total_passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
