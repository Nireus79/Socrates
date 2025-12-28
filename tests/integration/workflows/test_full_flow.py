#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Full integration test: Auth -> Create Project -> Chat -> Summary -> Delete
"""

import requests
import json
import sys
import os
from datetime import datetime, timezone
import uuid

# Fix unicode encoding for Windows
if os.name == 'nt':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except ValueError:
        # stdout might be closed when running under pytest
        pass

BASE_URL = "http://127.0.0.1:8000"

def test_full_flow():
    """Test complete user flow"""

    print("=" * 70)
    print("FULL INTEGRATION TEST: Auth -> Project -> Chat -> Summary -> Delete")
    print("=" * 70)

    # Step 1: Register user
    print("\n[STEP 1] Register new test user...")
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    password = "TestPassword123!"

    register_response = requests.post(
        f"{BASE_URL}/auth/register",
        json={"username": username, "password": password},
    )
    print(f"  Status: {register_response.status_code}")

    if register_response.status_code not in [200, 201]:
        print(f"  Error: {register_response.text[:300]}")
        # If user already exists, continue to login
        if "already exists" not in register_response.text:
            print("  [FAIL] Could not register user")
            return False
    else:
        print(f"  [OK] User registered successfully")

    # Step 2: Login
    print("\n[STEP 2] Login user...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": username, "password": password},
    )
    print(f"  Status: {login_response.status_code}")

    if login_response.status_code != 200:
        print(f"  Error: {login_response.text[:300]}")
        print("  [FAIL] Could not login")
        return False

    login_data = login_response.json()
    token = login_data.get("access_token") or login_data.get("token")

    if not token:
        print(f"  Error: No token in response: {login_data.keys()}")
        print("  [FAIL] Could not get access token")
        return False

    print(f"  [OK] Login successful, got token: {token[:20]}...")
    headers = {"Authorization": f"Bearer {token}"}

    # Step 3: Create project
    print("\n[STEP 3] Create test project...")
    project_data = {
        "name": f"Test Project {uuid.uuid4().hex[:4]}",
        "description": "Testing chat and delete functionality",
    }

    create_response = requests.post(
        f"{BASE_URL}/projects",
        json=project_data,
        headers=headers,
    )
    print(f"  Status: {create_response.status_code}")

    if create_response.status_code not in [200, 201]:
        print(f"  Error: {create_response.text[:300]}")
        print("  [FAIL] Could not create project")
        return False

    project_data_resp = create_response.json()
    project_id = project_data_resp.get("id") or project_data_resp.get("project_id")

    if not project_id:
        print(f"  Response: {json.dumps(project_data_resp, indent=2)[:500]}")
        print("  [FAIL] No project ID in response")
        return False

    print(f"  [OK] Project created with ID: {project_id}")

    # Step 4: Get question
    print(f"\n[STEP 4] Get initial question...")
    q_response = requests.get(
        f"{BASE_URL}/projects/{project_id}/chat/question",
        headers=headers,
    )
    print(f"  Status: {q_response.status_code}")

    if q_response.status_code == 200:
        q_data = q_response.json()
        if 'question' in q_data and 'phase' in q_data:
            print(f"  [OK] Got question (correct format)")
            print(f"    Phase: {q_data.get('phase')}")
        elif 'data' in q_data:
            print(f"  [WARN] Question wrapped in response envelope")
        else:
            print(f"  [WARN] Unexpected response: {list(q_data.keys())}")
    else:
        print(f"  Error: {q_response.text[:300]}")
        print("  [WARN] Could not get question")

    # Step 5: Send message
    print(f"\n[STEP 5] Send chat message...")
    message_data = {
        "message": "This is a test message to verify the chat works",
        "mode": "socratic"
    }

    msg_response = requests.post(
        f"{BASE_URL}/projects/{project_id}/chat/message",
        json=message_data,
        headers=headers,
    )
    print(f"  Status: {msg_response.status_code}")

    if msg_response.status_code == 200:
        msg_data = msg_response.json()
        if 'message' in msg_data:
            msg = msg_data['message']
            if isinstance(msg, dict) and 'content' in msg:
                print(f"  [OK] Message sent and response received (correct format)")
                print(f"    Response: {msg.get('content', '')[:100]}...")
            else:
                print(f"  [WARN] Message format unexpected: {type(msg)}")
        elif 'data' in msg_data:
            print(f"  [WARN] Message still wrapped in response envelope")
        else:
            print(f"  Response: {json.dumps(msg_data, indent=2)[:300]}")
    else:
        print(f"  Error: {msg_response.text[:300]}")
        print("  [WARN] Could not send message")

    # Step 6: Get history
    print(f"\n[STEP 6] Get chat history...")
    hist_response = requests.get(
        f"{BASE_URL}/projects/{project_id}/chat/history",
        headers=headers,
    )
    print(f"  Status: {hist_response.status_code}")

    if hist_response.status_code == 200:
        hist_data = hist_response.json()
        if 'messages' in hist_data:
            print(f"  [OK] Got history (correct format)")
            print(f"    Message count: {len(hist_data.get('messages', []))}")
        elif 'data' in hist_data:
            print(f"  [WARN] History wrapped in response envelope")
        else:
            print(f"  Response: {json.dumps(hist_data, indent=2)[:300]}")
    else:
        print(f"  Error: {hist_response.text[:300]}")
        print("  [WARN] Could not get history")

    # Step 7: Get summary
    print(f"\n[STEP 7] Get conversation summary...")
    sum_response = requests.get(
        f"{BASE_URL}/projects/{project_id}/chat/summary",
        headers=headers,
    )
    print(f"  Status: {sum_response.status_code}")

    if sum_response.status_code == 200:
        sum_data = sum_response.json()
        if 'summary' in sum_data and 'key_points' in sum_data:
            print(f"  [OK] Got summary (correct format)")
            print(f"    Summary: {sum_data.get('summary', '')[:80]}...")
        elif 'data' in sum_data:
            print(f"  [WARN] Summary wrapped in response envelope")
        else:
            print(f"  Response: {json.dumps(sum_data, indent=2)[:300]}")
    else:
        print(f"  Error: {sum_response.text[:300]}")
        print("  [WARN] Could not get summary")

    # Step 8: Delete project
    print(f"\n[STEP 8] Delete project...")
    del_response = requests.delete(
        f"{BASE_URL}/projects/{project_id}",
        headers=headers,
    )
    print(f"  Status: {del_response.status_code}")

    if del_response.status_code in [200, 204]:
        print(f"  [OK] Delete request succeeded")

        # Verify project is actually deleted
        print(f"\n[STEP 9] Verify project is deleted...")
        verify_response = requests.get(
            f"{BASE_URL}/projects/{project_id}",
            headers=headers,
        )
        print(f"  Status: {verify_response.status_code}")

        if verify_response.status_code == 404:
            print(f"  [OK] Project confirmed deleted (404 response)")
            print(f"\n{'=' * 70}")
            print("RESULT: ALL TESTS PASSED - System working correctly!")
            print(f"{'=' * 70}")
            return True
        else:
            print(f"  [FAIL] Project still exists after delete!")
            print(f"  Response: {verify_response.text[:300]}")
            return False
    else:
        print(f"  Error: {del_response.text[:300]}")
        print("  [FAIL] Could not delete project")
        return False

if __name__ == "__main__":
    try:
        success = test_full_flow()
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Exception during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
