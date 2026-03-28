#!/usr/bin/env python
"""
Manual API test script to diagnose runtime issues.

This script tests basic API connectivity and helps identify what's failing.

Usage:
    python test_api_manual.py
"""

import requests
import json
import sys
from typing import Dict, Any, Optional

API_BASE = "http://127.0.0.1:8000"
TIMEOUT = 5

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def test_endpoint(method: str, endpoint: str, data: Optional[Dict] = None, token: Optional[str] = None) -> Dict[str, Any]:
    """Test an API endpoint and return the response."""
    url = f"{API_BASE}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        elif method == "POST":
            resp = requests.post(url, json=data, headers=headers, timeout=TIMEOUT)
        else:
            return {"error": f"Unknown method: {method}"}

        return {
            "status": resp.status_code,
            "headers": dict(resp.headers),
            "body": resp.json() if resp.text else None,
            "text": resp.text[:200] if resp.text else ""
        }
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}

def print_result(test_name: str, result: Dict[str, Any], expected_status: int = None) -> bool:
    """Print test result and return whether it passed."""
    if "error" in result:
        print(f"{Colors.RED}✗ {test_name}{Colors.END}")
        print(f"  Error: {result['error']}")
        if "type" in result:
            print(f"  Type: {result['type']}")
        return False

    status = result.get("status")
    passed = status == expected_status if expected_status else 200 <= status < 300

    symbol = f"{Colors.GREEN}✓{Colors.END}" if passed else f"{Colors.RED}✗{Colors.END}"
    print(f"{symbol} {test_name}")
    print(f"  Status: {status}")

    body = result.get("body")
    if isinstance(body, dict):
        if "message" in body:
            print(f"  Message: {body['message']}")
        if "detail" in body:
            print(f"  Detail: {body['detail']}")
        if "error" in body:
            print(f"  Error: {body['error']}")

    return passed

def main():
    print(f"\n{Colors.BLUE}=== Socrates API Diagnostic Test ==={Colors.END}\n")

    # Test 1: Basic connectivity
    print("1. Testing basic connectivity...")
    result = test_endpoint("GET", "/")
    passed_1 = print_result("API Root Endpoint", result, 200)
    print()

    # Test 2: Health check
    print("2. Testing health endpoint...")
    result = test_endpoint("GET", "/health")
    passed_2 = print_result("Health Check", result, 200)
    print()

    # Test 3: CSRF token (no auth needed)
    print("3. Testing CSRF token endpoint...")
    result = test_endpoint("GET", "/auth/csrf-token")
    passed_3 = print_result("CSRF Token", result, 200)
    print()

    # Test 4: Projects list (auth required - should fail with 401)
    print("4. Testing projects list (without token - should get 401)...")
    result = test_endpoint("GET", "/projects")
    passed_4 = print_result("Projects List (no token)", result, 401)
    if result.get("status") != 401:
        print(f"{Colors.YELLOW}  Note: Expected 401, got {result.get('status')}{Colors.END}")
    print()

    # Test 5: Login endpoint
    print("5. Testing login endpoint...")
    result = test_endpoint("POST", "/auth/login", {
        "username": "testuser",
        "password": "testpass"
    })
    passed_5 = not ("error" in result)  # We expect this to fail (user doesn't exist), but not crash
    if "error" in result:
        print(f"{Colors.RED}✗ Login endpoint{Colors.END}")
        print(f"  Error: {result['error']}")
    else:
        status = result.get("status")
        print(f"✓ Login endpoint (status: {status})")
        if status in [400, 401, 404]:
            print(f"  Expected 4xx for non-existent user (got {status}) - this is OK")
        body = result.get("body", {})
        if "detail" in body:
            print(f"  Detail: {body['detail']}")
    print()

    # Summary
    print(f"{Colors.BLUE}=== Summary ==={Colors.END}")
    tests = [
        ("API Root", passed_1),
        ("Health Check", passed_2),
        ("CSRF Token", passed_3),
        ("Projects List", passed_4),
        ("Login Endpoint", passed_5),
    ]

    for name, passed in tests:
        symbol = f"{Colors.GREEN}✓{Colors.END}" if passed else f"{Colors.RED}✗{Colors.END}"
        print(f"{symbol} {name}")

    total_passed = sum(1 for _, p in tests if p)
    print(f"\nPassed: {total_passed}/{len(tests)}")

    # Analysis
    print(f"\n{Colors.BLUE}=== Analysis ==={Colors.END}\n")

    if passed_1 and passed_2:
        print(f"{Colors.GREEN}✓ API is running and responding{Colors.END}")
    else:
        print(f"{Colors.RED}✗ API is not responding properly{Colors.END}")
        print("  Check that backend is running: python -m socrates_api.main")
        return 1

    if not passed_4 and result.get("status") == 401:
        print(f"{Colors.YELLOW}Note: /projects returns 401 as expected (auth required){Colors.END}")
        print("  This is normal - you need to login first")
    elif not passed_4:
        print(f"{Colors.RED}Error: /projects returned {result.get('status')} instead of 401{Colors.END}")
        print("  This suggests an issue with authentication middleware")

    return 0

if __name__ == "__main__":
    sys.exit(main())
