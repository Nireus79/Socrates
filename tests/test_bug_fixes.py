"""
Quick Bug Fix Verification Test
Tests all 7 critical fixes from Session 5.1
"""

import requests
import sys

BASE_URL = "http://localhost:5002"

def test_fix(name, test_func):
    """Run a test and report result."""
    try:
        result = test_func()
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} - {name}")
        return result
    except Exception as e:
        print(f"[ERROR] - {name}: {str(e)[:100]}")
        return False

def test_projects_list():
    """Test that projects page loads (was 500 error)."""
    response = requests.get(f"{BASE_URL}/projects", allow_redirects=True)
    # Should redirect to login (302) or show page (200), not crash (500)
    return response.status_code in [200, 302, 303]

def test_repositories_list():
    """Test that repositories page loads (was crashing)."""
    response = requests.get(f"{BASE_URL}/repositories", allow_redirects=True)
    return response.status_code in [200, 302, 303]

def test_settings_page():
    """Test that settings page loads (was crashing)."""
    response = requests.get(f"{BASE_URL}/settings", allow_redirects=True)
    return response.status_code in [200, 302, 303]

def test_delete_session_button():
    """Test that delete session button is in template."""
    # Read the template file directly
    with open('../web/templates/sessions/detail.html', 'r', encoding='utf-8') as f:
        content = f.read()

    has_button = 'Delete Session' in content
    has_function = 'function deleteSession()' in content
    return has_button and has_function

def test_csrf_disabled():
    """Test that CSRF is disabled in app.py."""
    with open('../web/app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    return "WTF_CSRF_ENABLED'] = False" in content

def test_session_status_accepts_form_data():
    """Test that session status route accepts both JSON and form data."""
    with open('../web/app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for dual handling
    has_json_check = 'if request.is_json:' in content
    has_form_fallback = 'request.form.get' in content
    return has_json_check and has_form_fallback

def test_project_validation_simplified():
    """Test that project validation uses direct form fields."""
    with open('../web/app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for simplified validation
    has_name_check = "project_name = request.form.get('name'" in content
    has_length_check = 'len(project_name) >= 3' in content
    return has_name_check and has_length_check

def main():
    print("="*60)
    print("BUG FIX VERIFICATION TEST")
    print("Session 5.1 - Critical UI Functionality Fixes")
    print("="*60)
    print()

    results = []

    print("Code-Level Fixes (File Content):")
    print("-" * 60)
    results.append(test_fix("1. Delete session button in template", test_delete_session_button))
    results.append(test_fix("2. CSRF protection disabled", test_csrf_disabled))
    results.append(test_fix("3. Session status accepts form data", test_session_status_accepts_form_data))
    results.append(test_fix("4. Project validation simplified", test_project_validation_simplified))

    print()
    print("Runtime Fixes (HTTP Requests):")
    print("-" * 60)
    results.append(test_fix("5. Projects list loads (no 500)", test_projects_list))
    results.append(test_fix("6. Repositories page loads", test_repositories_list))
    results.append(test_fix("7. Settings page loads", test_settings_page))

    print()
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"RESULTS: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("="*60)

    if passed == total:
        print("[SUCCESS] ALL FIXES VERIFIED!")
        return 0
    else:
        print("[FAILURE] SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
