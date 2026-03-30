#!/usr/bin/env python
"""
HTTP Integration Tests for Socrates API
Tests actual API endpoints via HTTP
"""

import asyncio
import httpx
import json
import sys
from datetime import datetime
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"

# Test credentials
TEST_USER = "test_user@example.com"
TEST_PASSWORD = "TestPassword123!"
TEST_TOKEN = None


async def get_test_token():
    """Get or create test token via signup/login"""
    global TEST_TOKEN

    async with httpx.AsyncClient() as client:
        # Try signup first
        try:
            response = await client.post(
                f"{BASE_URL}/auth/signup",
                json={
                    "email": TEST_USER,
                    "password": TEST_PASSWORD,
                    "full_name": "Test User"
                }
            )
            if response.status_code == 201:
                data = response.json()
                TEST_TOKEN = data.get("data", {}).get("access_token")
                print(f"[OK] New user created and token obtained")
                return TEST_TOKEN
            elif response.status_code == 400 and "already exists" in response.text:
                # User exists, try login
                pass
        except Exception as e:
            print(f"Signup error (expected if user exists): {e}")

        # Try login
        try:
            response = await client.post(
                f"{BASE_URL}/auth/login",
                json={
                    "email": TEST_USER,
                    "password": TEST_PASSWORD
                }
            )
            if response.status_code == 200:
                data = response.json()
                TEST_TOKEN = data.get("data", {}).get("access_token")
                print(f"[OK] User logged in, token obtained")
                return TEST_TOKEN
        except Exception as e:
            print(f"Login error: {e}")

    return None


def get_headers():
    """Get authorization headers"""
    if not TEST_TOKEN:
        return {}
    return {"Authorization": f"Bearer {TEST_TOKEN}"}


async def test_health_check():
    """Test that server is running"""
    print("\n" + "="*60)
    print("TEST 1: Server Health Check")
    print("="*60)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BASE_URL}/system/help", headers=get_headers())

            if response.status_code == 200:
                print("[OK] Server is responding")
                return True
            elif response.status_code == 401:
                print("[INFO] Server responding but auth required")
                return True
            else:
                print(f"[FAIL] Server returned status {response.status_code}")
                return False
    except Exception as e:
        print(f"[FAIL] Could not connect to server: {e}")
        return False


async def test_create_project():
    """Test creating a project via API"""
    print("\n" + "="*60)
    print("TEST 2: Create Project via API")
    print("="*60)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/projects",
                headers=get_headers(),
                json={
                    "name": "E2E Test Project",
                    "description": "A test project created via HTTP API",
                    "goals": "Test all functionality",
                    "phase": "discovery",
                    "chat_mode": "socratic"
                }
            )

            if response.status_code == 201:
                data = response.json()
                project = data.get("data", {})
                project_id = project.get("project_id")
                print(f"[OK] Project created: {project_id}")
                return True, project_id
            elif response.status_code == 401:
                print("[SKIP] Authentication required - user may not be created yet")
                return False, None
            else:
                print(f"[FAIL] Status {response.status_code}: {response.text[:100]}")
                return False, None
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False, None


async def test_get_question(project_id):
    """Test getting a Socratic question"""
    print("\n" + "="*60)
    print("TEST 3: Get Socratic Question")
    print("="*60)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/projects/{project_id}/chat/question",
                headers=get_headers()
            )

            if response.status_code == 200:
                data = response.json()
                question = data.get("data", {}).get("question")
                print(f"[OK] Question generated: {question[:60]}...")
                return True
            elif response.status_code == 401:
                print("[SKIP] Authentication required")
                return False
            elif response.status_code == 404:
                print("[FAIL] Project not found")
                return False
            else:
                print(f"[FAIL] Status {response.status_code}: {response.text[:100]}")
                return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


async def test_send_message(project_id):
    """Test sending a chat message in Socratic mode"""
    print("\n" + "="*60)
    print("TEST 4: Send Chat Message (Socratic Mode)")
    print("="*60)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/projects/{project_id}/chat/message",
                headers=get_headers(),
                json={
                    "message": "I want to create a simple calculator in Python",
                    "mode": "socratic"
                }
            )

            if response.status_code == 200:
                data = response.json()
                success = data.get("success", False)
                if success:
                    print("[OK] Socratic message processed")
                    return True
                else:
                    msg = data.get("message", "Unknown error")
                    print(f"[FAIL] Processing failed: {msg}")
                    return False
            elif response.status_code == 401:
                print("[SKIP] Authentication required")
                return False
            elif response.status_code == 500:
                error = data.get("detail", "Server error")
                print(f"[FAIL] Server error: {error}")
                return False
            else:
                print(f"[FAIL] Status {response.status_code}: {response.text[:100]}")
                return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


async def test_direct_mode(project_id):
    """Test direct mode chat"""
    print("\n" + "="*60)
    print("TEST 5: Send Chat Message (Direct Mode)")
    print("="*60)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/projects/{project_id}/chat/message",
                headers=get_headers(),
                json={
                    "message": "How do I implement a basic calculator?",
                    "mode": "direct"
                }
            )

            if response.status_code == 200:
                data = response.json()
                success = data.get("success", False)
                if success:
                    print("[OK] Direct mode message processed")
                    return True
                else:
                    msg = data.get("message", "Unknown error")
                    print(f"[FAIL] Processing failed: {msg}")
                    return False
            elif response.status_code == 401:
                print("[SKIP] Authentication required")
                return False
            elif response.status_code == 500:
                error = data.get("detail", "Server error")
                print(f"[FAIL] Server error: {error}")
                return False
            else:
                print(f"[FAIL] Status {response.status_code}: {response.text[:100]}")
                return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


async def test_nlu_interpret():
    """Test NLU interpretation endpoint"""
    print("\n" + "="*60)
    print("TEST 6: NLU Mode - Interpret Input")
    print("="*60)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/nlu/interpret",
                headers=get_headers(),
                json={
                    "input": "help with my project",
                    "context": {"project_name": "Test Project"}
                }
            )

            if response.status_code == 200:
                data = response.json()
                success = data.get("success", False)
                if success:
                    print("[OK] NLU interpretation successful")
                    print(f"  Intent: {data.get('data', {}).get('intent')}")
                    return True
                else:
                    print(f"[INFO] NLU returned non-success but valid response")
                    return True
            elif response.status_code == 401:
                print("[SKIP] Authentication required")
                return False
            else:
                print(f"[FAIL] Status {response.status_code}: {response.text[:100]}")
                return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


async def test_debug_toggle():
    """Test debug mode toggle"""
    print("\n" + "="*60)
    print("TEST 7: Debug Mode Toggle")
    print("="*60)

    try:
        async with httpx.AsyncClient() as client:
            # Check current status
            response = await client.get(
                f"{BASE_URL}/system/debug/status",
                headers=get_headers()
            )

            initial_state = False
            if response.status_code == 200:
                data = response.json()
                initial_state = data.get("data", {}).get("debug_enabled", False)
                print(f"[OK] Current debug state: {initial_state}")
            elif response.status_code == 401:
                print("[SKIP] Authentication required")
                return False

            # Toggle debug mode
            response = await client.get(
                f"{BASE_URL}/system/debug/toggle?enabled={not initial_state}",
                headers=get_headers()
            )

            if response.status_code == 200:
                data = response.json()
                new_state = data.get("data", {}).get("debug_enabled")
                print(f"[OK] Debug toggled to: {new_state}")

                # Verify it toggled
                if new_state == (not initial_state):
                    print("[OK] Debug mode toggle working correctly")
                    return True
                else:
                    print("[FAIL] Debug mode did not toggle")
                    return False
            elif response.status_code == 401:
                print("[SKIP] Authentication required")
                return False
            else:
                print(f"[FAIL] Status {response.status_code}")
                return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


async def main():
    """Run all HTTP integration tests"""
    print("\n" + "="*70)
    print("SOCRATES HTTP INTEGRATION TEST SUITE")
    print("="*70)

    results = []
    project_id = None

    # Test 1: Health check
    result = await test_health_check()
    results.append(("Server Health Check", result))
    if not result:
        print("\nServer not running - cannot proceed with other tests")
        return results

    # Get test token
    print("\n[INFO] Attempting to get test authentication token...")
    await asyncio.sleep(1)  # Give server time to initialize
    token = await get_test_token()
    if not token:
        print("[WARN] Could not get auth token - some tests may be skipped")

    # Test 2: Create project
    result, project_id = await test_create_project()
    results.append(("Create Project", result))
    if not result or not project_id:
        print("\n[INFO] Could not create project via API - testing remaining components")

    # Tests that require a project
    if project_id:
        # Test 3: Get question
        result = await test_get_question(project_id)
        results.append(("Get Socratic Question", result))

        # Test 4: Send message (Socratic)
        result = await test_send_message(project_id)
        results.append(("Send Message (Socratic)", result))

        # Test 5: Send message (Direct)
        result = await test_direct_mode(project_id)
        results.append(("Send Message (Direct)", result))
    else:
        print("\n[INFO] Skipping project-specific tests")

    # Test 6: NLU interpretation
    result = await test_nlu_interpret()
    results.append(("NLU Interpretation", result))

    # Test 7: Debug toggle
    result = await test_debug_toggle()
    results.append(("Debug Mode Toggle", result))

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[OK] PASS" if result else "[FAIL] FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n[INFO] ALL HTTP TESTS PASSED!")
        return 0
    else:
        print(f"\n[WARN] {total - passed} test(s) failed or skipped")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
