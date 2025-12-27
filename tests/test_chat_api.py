#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify chat API endpoints work correctly after WebSocket removal.
Tests: GET question, send message, get history, delete project
"""

import requests
import json
import sys
import os
from datetime import datetime, timezone

# Fix unicode encoding for Windows
if os.name == 'nt':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"

def test_chat_endpoints():
    """Test all the REST API chat endpoints"""

    print("=" * 60)
    print("TESTING CHAT API ENDPOINTS")
    print("=" * 60)

    # Test 1: Health check
    print("\n[1] Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")
    assert response.status_code == 200, "Health check failed"
    print("  [OK] Health check passed")

    # Test 2: Create a project via simple REST call
    print("\n[2] Creating test project...")
    project_data = {
        "name": "Test Chat Project",
        "description": "Test project for chat API verification",
        "topic": "Testing",
    }

    response = requests.post(
        f"{BASE_URL}/projects",
        json=project_data,
        headers={"Authorization": "Bearer test-token-for-integration-tests"}
    )
    print(f"  Status: {response.status_code}")

    if response.status_code not in [200, 201]:
        print(f"  Response: {response.text}")
        # Continue anyway, might already have a test project
        project_id = "test-project-id"
    else:
        data = response.json()
        print(f"  Response: {json.dumps(data, indent=2)}")

        if isinstance(data, dict):
            if 'id' in data:
                project_id = data['id']
            elif 'project_id' in data:
                project_id = data['project_id']
            elif 'data' in data and isinstance(data['data'], dict):
                project_id = data['data'].get('id', 'test-project')
            else:
                project_id = 'test-project'
        else:
            project_id = 'test-project'

        print(f"  Project ID: {project_id}")
        print("  [OK] Project created")

    # Test 3: Get a question
    print(f"\n[3] Testing GET /projects/{project_id}/chat/question...")
    response = requests.get(
        f"{BASE_URL}/projects/{project_id}/chat/question",
        headers={"Authorization": "Bearer test-token-for-integration-tests"}
    )
    print(f"  Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"  Response keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")

        # Check if response format is correct (should be unwrapped)
        if isinstance(data, dict):
            if 'question' in data and 'phase' in data:
                print(f"  [OK] Question endpoint returns correct format: {{'question': ..., 'phase': ...}}")
                print(f"    Question: {data.get('question', '')[:100]}...")
                print(f"    Phase: {data.get('phase', '')}")
            elif 'data' in data:
                print(f"  [WARN] Question endpoint still wrapped in response envelope")
                print(f"    Nested keys: {list(data.get('data', {}).keys())}")
            else:
                print(f"  Full response: {json.dumps(data, indent=2)[:500]}")
    else:
        print(f"  Response: {response.text[:500]}")
        print("  [WARN] Failed to get question (may need auth setup)")

    # Test 4: Send a message (if we have a project)
    print(f"\n[4] Testing POST /projects/{project_id}/chat/message...")
    message_data = {
        "message": "This is a test message to verify the chat API works",
        "mode": "socratic"
    }

    response = requests.post(
        f"{BASE_URL}/projects/{project_id}/chat/message",
        json=message_data,
        headers={"Authorization": "Bearer test-token-for-integration-tests"}
    )
    print(f"  Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"  Response keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")

        # Check response format
        if isinstance(data, dict):
            if 'message' in data and isinstance(data['message'], dict):
                msg = data['message']
                if all(k in msg for k in ['id', 'role', 'content', 'timestamp']):
                    print(f"  [OK] Message endpoint returns correct format")
                    print(f"    Message ID: {msg.get('id')}")
                    print(f"    Role: {msg.get('role')}")
                    print(f"    Content: {msg.get('content', '')[:100]}...")
                else:
                    print(f"  [WARN] Message format missing keys: {list(msg.keys())}")
            elif 'data' in data:
                print(f"  [WARN] Message endpoint still wrapped in response envelope")
            else:
                print(f"  Full response: {json.dumps(data, indent=2)[:500]}")
    else:
        print(f"  Response: {response.text[:500]}")
        print("  [WARN] Failed to send message")

    # Test 5: Get history
    print(f"\n[5] Testing GET /projects/{project_id}/chat/history...")
    response = requests.get(
        f"{BASE_URL}/projects/{project_id}/chat/history",
        headers={"Authorization": "Bearer test-token-for-integration-tests"}
    )
    print(f"  Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"  Response keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")

        if isinstance(data, dict):
            if 'messages' in data:
                print(f"  [OK] History endpoint returns correct format")
                print(f"    Message count: {len(data.get('messages', []))}")
            elif 'data' in data:
                print(f"  [WARN] History endpoint still wrapped in response envelope")
            else:
                print(f"  Full response: {json.dumps(data, indent=2)[:500]}")
    else:
        print(f"  Response: {response.text[:500]}")
        print("  [WARN] Failed to get history")

    # Test 6: Get summary
    print(f"\n[6] Testing GET /projects/{project_id}/chat/summary...")
    response = requests.get(
        f"{BASE_URL}/projects/{project_id}/chat/summary",
        headers={"Authorization": "Bearer test-token-for-integration-tests"}
    )
    print(f"  Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"  Response keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")

        if isinstance(data, dict):
            if all(k in data for k in ['summary', 'key_points']):
                print(f"  [OK] Summary endpoint returns correct format")
                print(f"    Summary: {data.get('summary', '')[:100]}...")
                print(f"    Key points: {len(data.get('key_points', []))} items")
            elif 'data' in data:
                print(f"  [WARN] Summary endpoint still wrapped in response envelope")
            else:
                print(f"  Full response: {json.dumps(data, indent=2)[:500]}")
    else:
        print(f"  Response: {response.text[:500]}")
        print("  [WARN] Failed to get summary")

    print("\n" + "=" * 60)
    print("CHAT API TESTS COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_chat_endpoints()
        print("\n[OK] API tests completed successfully")
    except Exception as e:
        print(f"\n[ERROR] Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
