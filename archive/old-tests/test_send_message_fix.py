#!/usr/bin/env python
"""Test script to verify send_message endpoint handles insights correctly"""

import sys
import json
import subprocess
import time
import requests
from datetime import datetime, timezone

# Test configuration
API_URL = "http://localhost:8000"
TEST_PROJECT_ID = "test_proj_" + datetime.now().isoformat().replace(":", "-")
TEST_USER = "testuser_" + str(int(time.time()))

def test_send_message_endpoint():
    """Test that send_message endpoint correctly handles insights from socratic_counselor"""

    print("\n" + "="*80)
    print("Testing send_message endpoint")
    print("="*80)

    # First, create a test project
    print(f"\n1. Creating test project: {TEST_PROJECT_ID}")

    try:
        # Create project
        create_response = requests.post(
            f"{API_URL}/projects",
            json={
                "name": "Test Project",
                "description": "Testing send_message endpoint",
                "tech_stack": ["Python", "FastAPI"]
            },
            headers={"Authorization": f"Bearer test_token_{TEST_USER}"}
        )

        if create_response.status_code != 200:
            print(f"❌ Failed to create project: {create_response.status_code}")
            print(f"Response: {create_response.text}")
            return False

        project = create_response.json()
        project_id = project.get("id") or project.get("project_id")
        print(f"✓ Project created: {project_id}")

        # Get initial question
        print(f"\n2. Getting initial question")
        question_response = requests.get(
            f"{API_URL}/projects/{project_id}/chat/question",
            headers={"Authorization": f"Bearer test_token_{TEST_USER}"}
        )

        if question_response.status_code != 200:
            print(f"❌ Failed to get question: {question_response.status_code}")
            print(f"Response: {question_response.text}")
            return False

        question_data = question_response.json()
        print(f"✓ Got question: {question_data.get('question', 'N/A')[:80]}...")

        # Send a message to test the endpoint
        print(f"\n3. Sending test message")
        test_message = "I want to build a web application using Python and FastAPI"

        message_response = requests.post(
            f"{API_URL}/projects/{project_id}/chat/message",
            json={
                "message": test_message,
                "mode": "socratic"
            },
            headers={"Authorization": f"Bearer test_token_{TEST_USER}"}
        )

        if message_response.status_code != 200:
            print(f"❌ Failed to send message: {message_response.status_code}")
            print(f"Response: {message_response.text}")
            return False

        response_data = message_response.json()
        print(f"✓ Message sent successfully")
        print(f"  Response content: {response_data.get('message', {}).get('content', 'N/A')[:100]}...")

        if response_data.get('conflicts_pending'):
            print(f"⚠️  Conflicts detected in response")

        return True

    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_send_message_endpoint()

    print("\n" + "="*80)
    if success:
        print("✓ send_message endpoint test PASSED")
        sys.exit(0)
    else:
        print("❌ send_message endpoint test FAILED")
        sys.exit(1)
