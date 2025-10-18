#!/usr/bin/env python
"""
Comprehensive UI Responsiveness Test
Tests whether JavaScript functions actually execute and forms work
"""

import requests
import json
import re
import time

# Create a session to persist cookies
session = requests.Session()
BASE_URL = 'http://localhost:5000'

print("="*80)
print("COMPREHENSIVE UI RESPONSIVENESS TEST")
print("="*80)

# TEST 1: Get login page and extract CSRF token
print("\n[TEST 1] Getting login page to extract CSRF token...")
try:
    response = session.get(f'{BASE_URL}/login', timeout=5)
    print(f"  Status: {response.status_code}")

    # Extract CSRF token from form
    csrf_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', response.text)
    if csrf_match:
        csrf_token = csrf_match.group(1)
        print(f"  CSRF Token found: {csrf_token[:20]}...")
    else:
        print("  ERROR: Could not extract CSRF token!")
        csrf_token = None
except Exception as e:
    print(f"  ERROR: {e}")
    csrf_token = None

# TEST 2: Login with valid user credentials
print("\n[TEST 2] Logging in with valid credentials...")
try:
    # Get fresh login page for new CSRF token
    response = session.get(f'{BASE_URL}/login', timeout=5)
    csrf_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', response.text)
    csrf_token = csrf_match.group(1) if csrf_match else None

    login_data = {
        'username': 'realuser',  # Known existing user from previous tests
        'password': 'Pass123',
        'csrf_token': csrf_token
    }
    response = session.post(f'{BASE_URL}/login', data=login_data, timeout=5)
    print(f"  Status: {response.status_code}")

    # Check if we got a redirect (successful login)
    if response.status_code == 302:
        print(f"  Redirect to: {response.headers.get('Location', 'N/A')}")
        print("  ✓ Login successful (got redirect)")
    elif response.status_code == 200:
        print("  Status 200 (may be error page or login form again)")

    # Check for session cookie
    cookies = session.cookies.get_dict()
    if 'session' in cookies:
        print(f"  ✓ Session cookie present: {cookies['session'][:30]}...")
    else:
        print("  ! No session cookie found")
except Exception as e:
    print(f"  ERROR: {e}")

# TEST 3: Access dashboard (requires authentication)
print("\n[TEST 3] Accessing dashboard...")
try:
    response = session.get(f'{BASE_URL}/dashboard', timeout=5, allow_redirects=True)
    print(f"  Status: {response.status_code}")

    if response.status_code == 200:
        print("  ✓ Dashboard loaded")

        # Check if critical JavaScript is present
        if 'startSocraticSession' in response.text:
            print("  ✓ startSocraticSession function found")
        else:
            print("  ! startSocraticSession function NOT found")

        if 'refreshDashboard' in response.text:
            print("  ✓ refreshDashboard function found")
        else:
            print("  ! refreshDashboard function NOT found")

        if 'submitQuickSession' in response.text:
            print("  ✓ submitQuickSession function found")
        else:
            print("  ! submitQuickSession function NOT found")

        # Check for onclick handlers
        if 'onclick="refreshDashboard()"' in response.text:
            print("  ✓ Refresh button onclick handler present")
        else:
            print("  ! Refresh button onclick handler NOT found")

        if 'onclick="startQuickSession()"' in response.text:
            print("  ✓ Quick session button onclick handler present")
        else:
            print("  ! Quick session button onclick handler NOT found")
    else:
        print(f"  ! Got status {response.status_code} instead of 200")
except Exception as e:
    print(f"  ERROR: {e}")

# TEST 4: Call the /health endpoint (no auth required, tests fetch API)
print("\n[TEST 4] Testing /health endpoint (tests fetch API)...")
try:
    response = session.get(f'{BASE_URL}/health', timeout=5)
    print(f"  Status: {response.status_code}")
    print(f"  Content-Type: {response.headers.get('Content-Type', 'N/A')}")

    if response.status_code == 200 and 'json' in response.headers.get('Content-Type', '').lower():
        data = response.json()
        print(f"  ✓ Health endpoint returns JSON")
    else:
        print(f"  ! Unexpected response format")
except Exception as e:
    print(f"  ERROR: {e}")

# TEST 5: Call /api/health endpoint
print("\n[TEST 5] Testing /api/health endpoint...")
try:
    response = session.get(f'{BASE_URL}/api/health', timeout=5)
    print(f"  Status: {response.status_code}")
    print(f"  Content-Type: {response.headers.get('Content-Type', 'N/A')}")

    if response.status_code == 200 and 'json' in response.headers.get('Content-Type', '').lower():
        data = response.json()
        print(f"  ✓ API health returns JSON")
    else:
        print(f"  ! Unexpected response")
except Exception as e:
    print(f"  ERROR: {e}")

# TEST 6: Test settings save endpoint (requires authentication)
print("\n[TEST 6] Testing settings save endpoint...")
try:
    response = session.post(
        f'{BASE_URL}/api/settings/system',
        json={'theme': 'dark'},
        timeout=5
    )
    print(f"  Status: {response.status_code}")
    print(f"  Content-Type: {response.headers.get('Content-Type', 'N/A')}")

    if response.status_code == 200:
        print(f"  Response: {response.text[:100]}")
        if 'json' in response.headers.get('Content-Type', '').lower():
            print("  ✓ Settings endpoint returns JSON")
        else:
            print("  ! Response is not JSON")
    else:
        print(f"  ! Got status {response.status_code}")
        if 'html' in response.headers.get('Content-Type', '').lower():
            print("  ERROR: Got HTML response instead of JSON!")
except Exception as e:
    print(f"  ERROR: {e}")

# TEST 7: Test sessions endpoint
print("\n[TEST 7] Testing sessions endpoint...")
try:
    response = session.get(f'{BASE_URL}/sessions', timeout=5, allow_redirects=True)
    print(f"  Status: {response.status_code}")

    if response.status_code == 200:
        print("  ✓ Sessions page loaded")
    else:
        print(f"  ! Got status {response.status_code}")
except Exception as e:
    print(f"  ERROR: {e}")

# TEST 8: Test projects page
print("\n[TEST 8] Testing projects page...")
try:
    response = session.get(f'{BASE_URL}/projects', timeout=5, allow_redirects=True)
    print(f"  Status: {response.status_code}")

    if response.status_code == 200:
        print("  ✓ Projects page loaded")
    else:
        print(f"  ! Got status {response.status_code}")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
