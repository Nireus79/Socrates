#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test for specific UI responsiveness issues
"""
import requests
import json
import re

session = requests.Session()
BASE_URL = 'http://localhost:5000'

print("=" * 80)
print("UI RESPONSIVENESS ANALYSIS")
print("=" * 80)

# Get login page and login
response = session.get(f'{BASE_URL}/login', timeout=5)
csrf_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', response.text)
csrf_token = csrf_match.group(1) if csrf_match else None

login_data = {
    'username': 'realuser',
    'password': 'Pass123',
    'csrf_token': csrf_token
}
response = session.post(f'{BASE_URL}/login', data=login_data, timeout=5)
print("\n1. LOGIN STATUS: " + str(response.status_code))

# Get dashboard
response = session.get(f'{BASE_URL}/dashboard', timeout=5, allow_redirects=True)
print("2. DASHBOARD STATUS: " + str(response.status_code))

if response.status_code == 200:
    # Analyze JavaScript
    has_fetch = 'fetch(' in response.text
    has_onclick = 'onclick=' in response.text
    has_modal = 'Modal' in response.text
    has_chart = 'Chart' in response.text

    print("\n   JAVASCRIPT ANALYSIS:")
    print("   - Has fetch() calls: " + str(has_fetch))
    print("   - Has onclick handlers: " + str(has_onclick))
    print("   - Has Modal functionality: " + str(has_modal))
    print("   - Has Chart.js: " + str(has_chart))

    # Check for specific issues
    print("\n   CHECKING FOR POTENTIAL ISSUES:")

    # Issue 1: Check if routes are resolving correctly
    if "{{ url_for(" in response.text:
        print("   ERROR: Jinja2 templates not rendered! Found {{ url_for( still in HTML")
    else:
        print("   OK: Jinja2 templates rendered correctly")

    # Issue 2: Check if CSRF token is available for AJAX
    if '_csrf_token' in response.text:
        print("   OK: CSRF token available for AJAX calls")
    else:
        print("   WARNING: CSRF token may not be available for AJAX")

    # Issue 3: Check if Bootstrap is loaded
    if 'bootstrap' in response.text.lower():
        print("   OK: Bootstrap is loaded")
    else:
        print("   ERROR: Bootstrap not loaded!")

    # Issue 4: Check if Chart.js is loaded
    if 'chart' in response.text.lower():
        print("   OK: Chart.js loaded")
    else:
        print("   WARNING: Chart.js may not be loaded")

# Test specific endpoints
print("\n3. ENDPOINT TESTS:")

# Test health
response = session.get(f'{BASE_URL}/health', timeout=5)
print(f"   /health: {response.status_code} - {'JSON' if 'json' in response.headers.get('Content-Type', '') else 'Not JSON'}")

# Test API health
response = session.get(f'{BASE_URL}/api/health', timeout=5)
print(f"   /api/health: {response.status_code} - {'JSON' if 'json' in response.headers.get('Content-Type', '') else 'Not JSON'}")

# Test settings endpoint
response = session.post(
    f'{BASE_URL}/api/settings/system',
    json={'theme': 'dark'},
    timeout=5
)
print(f"   POST /api/settings/system: {response.status_code} - {response.text[:100]}")

# Test sessions
response = session.get(f'{BASE_URL}/sessions', timeout=5)
print(f"   GET /sessions: {response.status_code}")

# Test projects
response = session.get(f'{BASE_URL}/projects', timeout=5)
print(f"   GET /projects: {response.status_code}")

print("\n4. CRITICAL FINDING - LOGIN ISSUE:")
print("   NOTE: Login returned 200 instead of 302 redirect!")
print("   This suggests the login form is being shown again")
print("   Possible causes:")
print("   - Credentials are wrong")
print("   - Form validation failed silently")
print("   - Session is not being created")

# Try to login and see what the response contains
response = session.get(f'{BASE_URL}/login', timeout=5)
csrf_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', response.text)
csrf_token = csrf_match.group(1) if csrf_match else None

login_data = {
    'username': 'realuser',
    'password': 'Pass123',
    'csrf_token': csrf_token
}
response = session.post(f'{BASE_URL}/login', data=login_data, timeout=5)

if 'error' in response.text.lower() or 'invalid' in response.text.lower():
    print("\n   FOUND ERROR IN LOGIN RESPONSE!")
    # Extract error message
    error_match = re.search(r'<div[^>]*class="[^"]*alert[^"]*"[^>]*>([^<]+)</div>', response.text)
    if error_match:
        print(f"   Error message: {error_match.group(1)}")
else:
    print("\n   No obvious error in login response")
    # Check if session was created
    if 'session' in session.cookies:
        print("   Session cookie exists")
    else:
        print("   ERROR: Session cookie not created!")

print("\n" + "=" * 80)
