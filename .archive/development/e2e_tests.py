#!/usr/bin/env python3
"""End-to-end API integration tests"""

import sys
import os
import requests
from datetime import datetime

sys.path.insert(0, 'socratic_system')
sys.path.insert(0, 'socrates-api/src')

from socrates_api.auth.jwt_handler import create_access_token

API_URL = "http://127.0.0.1:8000"
TESTS_PASSED = 0
TESTS_FAILED = 0

def log_test(name, status, message=""):
    global TESTS_PASSED, TESTS_FAILED
    if status:
        TESTS_PASSED += 1
        print(f"  [PASS] {name}")
    else:
        TESTS_FAILED += 1
        print(f"  [FAIL] {name}")
        if message:
            print(f"         {message[:100]}")

print("=" * 80)
print("END-TO-END API INTEGRATION TESTS")
print("=" * 80)

# Create test user token
test_user_free = "freetier_" + str(int(datetime.now().timestamp()))
token_free = create_access_token(test_user_free)
headers_free = {"Authorization": f"Bearer {token_free}"}

print(f"\nTest User (Free Tier): {test_user_free}")

# TEST 1: CREATE FIRST PROJECT
print("\n[TEST 1] Create First Project (Free Tier User)")
print("-" * 80)

project_id = None
try:
    response = requests.post(
        f"{API_URL}/projects",
        json={"name": "Test Project 1", "description": "First project"},
        headers=headers_free,
        timeout=15
    )

    if response.status_code == 200:
        # Response is ProjectResponse directly, not wrapped in data
        project_response = response.json()
        project_id = project_response.get("project_id")
        if project_id:
            log_test("Create first project", True)
            print(f"        Project ID: {project_id}")
        else:
            log_test("Create first project", False, "No project_id in response")
    else:
        log_test("Create first project", False, f"Status {response.status_code}")
        print(f"        Response: {response.text[:150]}")
except Exception as e:
    log_test("Create first project", False, str(e)[:100])

# TEST 2: CREATE SECOND PROJECT (SHOULD FAIL)
print("\n[TEST 2] Create Second Project (Should be Blocked)")
print("-" * 80)

try:
    response = requests.post(
        f"{API_URL}/projects",
        json={"name": "Test Project 2", "description": "Second project"},
        headers=headers_free,
        timeout=15
    )

    if response.status_code == 403:
        error_detail = response.json().get('detail', '')
        if 'limit' in error_detail.lower() or 'tier' in error_detail.lower():
            log_test("Block second project for free tier", True)
            print(f"        Error: {error_detail[:80]}")
        else:
            log_test("Block second project for free tier", False, f"Different error")
    elif response.status_code == 200:
        log_test("Block second project for free tier", False, "Second project was created")
    else:
        log_test("Block second project for free tier", False, f"Status {response.status_code}")
except Exception as e:
    log_test("Block second project for free tier", False, str(e)[:100])

# TEST 3: TEST /PHASE ENDPOINT
print("\n[TEST 3] Test /phase Endpoint (Auto-Advance)")
print("-" * 80)

if project_id:
    try:
        response = requests.put(
            f"{API_URL}/projects/{project_id}/phase",
            headers=headers_free,
            timeout=15
        )

        if response.status_code == 200:
            response_data = response.json()
            new_phase = response_data.get("phase", "unknown")
            log_test("Auto-advance phase", True)
            print(f"        New Phase: {new_phase}")
        else:
            log_test("Auto-advance phase", False, f"Status {response.status_code}")
            print(f"        Response: {response.text[:150]}")
    except Exception as e:
        log_test("Auto-advance phase", False, str(e)[:100])
else:
    print("  [SKIP] No project created")

# TEST 4: TEST /CODE/GENERATE
print("\n[TEST 4] Test /code/generate Endpoint (No Body)")
print("-" * 80)

if project_id:
    try:
        response = requests.post(
            f"{API_URL}/projects/{project_id}/code/generate",
            headers=headers_free,
            timeout=20
        )

        if response.status_code == 200:
            response_data = response.json()
            code = response_data.get("code", "")
            if code:
                log_test("Generate code without body", True)
                print(f"        Code: {len(code)} characters")
            else:
                log_test("Generate code without body", False, "Empty code")
        elif response.status_code == 422:
            log_test("Generate code without body", False, "422 Error")
        else:
            log_test("Generate code without body", False, f"Status {response.status_code}")
    except Exception as e:
        log_test("Generate code without body", False, str(e)[:100])
else:
    print("  [SKIP] No project created")

# TEST 5: TEST /PROGRESS ENDPOINT
print("\n[TEST 5] Test /progress Endpoint (No 500 Error)")
print("-" * 80)

if project_id:
    try:
        response = requests.get(
            f"{API_URL}/projects/{project_id}/progress",
            headers=headers_free,
            timeout=15
        )

        if response.status_code == 200:
            data = response.json().get("data", {})
            overall = data.get("overall_progress", {})
            if overall:
                log_test("Get progress without error", True)
                print(f"        Progress: {overall.get('percentage')}%")
            else:
                log_test("Get progress without error", False, "Missing data")
        elif response.status_code == 500:
            log_test("Get progress without error", False, "500 Error")
        else:
            log_test("Get progress without error", False, f"Status {response.status_code}")
    except Exception as e:
        log_test("Get progress without error", False, str(e)[:100])
else:
    print("  [SKIP] No project created")

# SUMMARY
print("\n" + "=" * 80)
print(f"RESULTS: {TESTS_PASSED} PASSED, {TESTS_FAILED} FAILED")
print("=" * 80)

if TESTS_FAILED == 0:
    print("\nALL TESTS PASSED!")
    sys.exit(0)
else:
    print(f"\n{TESTS_FAILED} test(s) failed")
    sys.exit(1)
