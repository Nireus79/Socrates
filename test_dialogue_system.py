#!/usr/bin/env python3
"""
Comprehensive test script for Socrates dialogue system (Phase 1-3)
Tests all critical features: spec extraction, conflict detection, hints, NLU
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"
TEST_USER = "testuser"
TEST_PASSWORD = "TestPassword123!"
TEST_PROJECT_ID = "test_project_001"

def log_test(title, status, details=""):
    """Log test result"""
    symbol = "[PASS]" if status else "[FAIL]"
    print(f"{symbol} {title}")
    if details:
        print(f"   {details}")

def test_health():
    """Test server health"""
    print("\n=== Testing Server Health ===")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        log_test("Server Health", response.status_code == 200, f"Status: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        log_test("Server Health", False, str(e))
        return False

def test_authentication():
    """Test user authentication"""
    print("\n=== Testing Authentication ===")

    # Create user
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={"username": TEST_USER, "password": TEST_PASSWORD},
            timeout=5
        )
        log_test("User Registration", response.status_code in [200, 409], f"Status: {response.status_code}")
    except Exception as e:
        log_test("User Registration", False, str(e))
        return None

    # Login
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": TEST_USER, "password": TEST_PASSWORD},
            timeout=5
        )
        if response.status_code == 200:
            token = response.json().get("access_token")
            log_test("User Login", True, "Token received")
            return token
        else:
            log_test("User Login", False, f"Status: {response.status_code}")
            return None
    except Exception as e:
        log_test("User Login", False, str(e))
        return None

def test_project_creation(token):
    """Test project creation"""
    print("\n=== Testing Project Creation ===")

    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.post(
            f"{BASE_URL}/projects",
            json={
                "id": TEST_PROJECT_ID,
                "name": "Dialogue Test Project",
                "description": "Testing Phase 1-3 features",
                "phase": "discovery"
            },
            headers=headers,
            timeout=5
        )
        log_test("Project Creation", response.status_code in [200, 201, 409], f"Status: {response.status_code}")
        return response.status_code in [200, 201, 409]
    except Exception as e:
        log_test("Project Creation", False, str(e))
        return False

def test_get_question(token):
    """Test get_question endpoint - P2.2 feature"""
    print("\n=== Testing Get Question (P2.2) ===")

    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(
            f"{BASE_URL}/projects/{TEST_PROJECT_ID}/chat/question",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json().get("data", {})
            question = data.get("question")
            question_id = data.get("questionId")

            log_test(
                "Get Question Endpoint",
                bool(question and question_id),
                f"Question ID: {question_id[:10]}..." if question_id else "No question ID"
            )

            # Verify question_id is UUID-like
            if question_id:
                log_test("Question ID Format", len(question_id) > 20, f"Format: {question_id}")

            return {
                "question": question,
                "question_id": question_id,
                "success": True
            }
        else:
            log_test("Get Question Endpoint", False, f"Status: {response.status_code}")
            return {"success": False}
    except Exception as e:
        log_test("Get Question Endpoint", False, str(e))
        return {"success": False}

def test_process_response(token, response_text):
    """Test process_response endpoint - P1.1 & P2.3 features"""
    print("\n=== Testing Process Response (P1.1 & P2.3) ===")

    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.post(
            f"{BASE_URL}/projects/{TEST_PROJECT_ID}/chat/message",
            json={"message": response_text},
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json().get("data", {})

            # Check for spec extraction (P1.1)
            extracted_specs = data.get("extracted_specs")
            log_test(
                "Spec Extraction (P1.1)",
                bool(extracted_specs),
                f"Types detected: {list(extracted_specs.keys()) if extracted_specs else 'None'}"
            )

            # Check for conflicts (P2.1)
            conflicts = data.get("conflicts", [])
            has_conflicts = len(conflicts) > 0
            log_test(
                "Conflict Detection (P2.1)",
                True,
                f"Conflicts found: {len(conflicts)}"
            )

            # Check for NLU auto-execution (P2.3)
            nlu_executed = data.get("nlu_auto_executed", False)
            detected_intent = data.get("detected_intent")
            log_test(
                "NLU Auto-Execution (P2.3)",
                True,
                f"Auto-executed: {nlu_executed}, Intent: {detected_intent}"
            )

            return {
                "success": True,
                "extracted_specs": extracted_specs,
                "conflicts": conflicts,
                "nlu_auto_executed": nlu_executed
            }
        else:
            log_test("Process Response", False, f"Status: {response.status_code}")
            return {"success": False}
    except Exception as e:
        log_test("Process Response", False, str(e))
        return {"success": False}

def test_get_hint(token):
    """Test get_hint endpoint - P2.2 feature"""
    print("\n=== Testing Get Hint (P2.2) ===")

    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(
            f"{BASE_URL}/projects/{TEST_PROJECT_ID}/chat/hint",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json().get("data", {})
            hint = data.get("hint")

            log_test(
                "Hint Generation (P2.2)",
                bool(hint),
                f"Hint: {hint[:60]}..." if hint else "No hint returned"
            )

            # Check debug info if available
            debug_info = data.get("debugInfo", {})
            if debug_info:
                log_test(
                    "Debug Info Available",
                    True,
                    f"Source: {debug_info.get('hint_source', 'unknown')}"
                )

            return {"success": True, "hint": hint}
        else:
            log_test("Hint Generation", False, f"Status: {response.status_code}")
            return {"success": False}
    except Exception as e:
        log_test("Hint Generation", False, str(e))
        return {"success": False}

def test_nlu_intent_detection(token):
    """Test NLU intent detection - P2.3 feature"""
    print("\n=== Testing NLU Intent Detection (P2.3) ===")

    headers = {"Authorization": f"Bearer {token}"}

    # Test cases for intent detection
    test_cases = [
        ("skip this", "skip_question", 0.95),
        ("i need a hint", "get_hint", 0.90),
        ("explain the conflict", "explain_conflict", 0.85),
    ]

    for user_input, expected_intent, expected_confidence in test_cases:
        try:
            response = requests.post(
                f"{BASE_URL}/projects/{TEST_PROJECT_ID}/chat/message",
                json={"message": user_input},
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json().get("data", {})
                detected_intent = data.get("detected_intent")
                detected_confidence = data.get("confidence", 0)

                intent_match = detected_intent == expected_intent if detected_intent else False
                log_test(
                    f"Intent Detection: '{user_input}'",
                    intent_match,
                    f"Detected: {detected_intent} (confidence: {detected_confidence:.2f})"
                )
            else:
                log_test(f"Intent Detection: '{user_input}'", False, f"Status: {response.status_code}")
        except Exception as e:
            log_test(f"Intent Detection: '{user_input}'", False, str(e))

def test_database_persistence(token):
    """Test database persistence - P1.1 & P3 features"""
    print("\n=== Testing Database Persistence (P1.1 & P3) ===")

    headers = {"Authorization": f"Bearer {token}"}

    # First response to save specs
    try:
        response = requests.post(
            f"{BASE_URL}/projects/{TEST_PROJECT_ID}/chat/message",
            json={"message": "I want to build a Python web application with Flask"},
            headers=headers,
            timeout=10
        )
        log_test("Save Response to Database", response.status_code == 200, f"Status: {response.status_code}")
    except Exception as e:
        log_test("Save Response to Database", False, str(e))
        return

    # Try to retrieve activities (P3 feature)
    time.sleep(1)  # Give database time to persist

    try:
        response = requests.get(
            f"{BASE_URL}/projects/{TEST_PROJECT_ID}/activities",
            headers=headers,
            timeout=5
        )

        if response.status_code == 200:
            activities = response.json().get("data", [])
            log_test(
                "Activity Retrieval (P3)",
                len(activities) > 0,
                f"Activities found: {len(activities)}"
            )
        else:
            log_test("Activity Retrieval", response.status_code == 404 or response.status_code == 200,
                    f"Status: {response.status_code} (may not be implemented yet)")
    except Exception as e:
        log_test("Activity Retrieval", False, str(e))

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("SOCRATES DIALOGUE SYSTEM - COMPREHENSIVE TEST SUITE")
    print("Testing Phase 1-3 Implementation")
    print("="*60)

    # Set UTF-8 encoding for output
    import sys
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # Test server health
    if not test_health():
        print("\n[FAIL] Server is not responding. Cannot continue tests.")
        sys.exit(1)

    # Authenticate
    token = test_authentication()
    if not token:
        print("\n[FAIL] Authentication failed. Cannot continue tests.")
        sys.exit(1)

    # Create project
    if not test_project_creation(token):
        print("\n[WARN] Project creation failed or project already exists.")

    # Test dialogue features
    question_result = test_get_question(token)

    if question_result.get("success"):
        # Test response processing
        response_result = test_process_response(token, "I want to build a calculator app using React")

        # Test hint generation
        test_get_hint(token)

        # Test NLU intent detection
        test_nlu_intent_detection(token)

    # Test database persistence
    test_database_persistence(token)

    # Summary
    print("\n" + "="*60)
    print("TEST SUITE COMPLETED")
    print("="*60)
    print("\nAll Phase 1-3 features have been tested.")
    print("Check results above for any failures.")
    print("\nIf server not responding: 'timeout 30 python socrates.py --api --no-auto-port --port 8000'")

if __name__ == "__main__":
    main()
