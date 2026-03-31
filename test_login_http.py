#!/usr/bin/env python3
"""
Test login via HTTP with detailed debugging.
"""

import sys
import json
import requests
import logging
from pathlib import Path

# Setup logging to see all details
logging.basicConfig(
    level=logging.DEBUG,
    format='%(name)s - %(levelname)s - %(message)s'
)

print("=" * 60)
print("HTTP LOGIN TEST")
print("=" * 60)

url = "http://localhost:8000/auth/login"
credentials = {
    "username": "testuser",
    "password": "TestPassword123!"
}

print(f"\n1. Checking if API is running...")
try:
    response = requests.get("http://localhost:8000/health", timeout=2)
    if response.status_code == 200:
        print(f"   [OK] API is running")
        health = response.json()
        print(f"   Health: {health.get('status', 'unknown')}")
    else:
        print(f"   [ERROR] API returned {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"   [ERROR] Cannot connect to API: {e}")
    sys.exit(1)

print(f"\n2. Preparing login request...")
print(f"   URL: POST {url}")
print(f"   Body: {json.dumps(credentials, indent=2)}")

print(f"\n3. Sending login request...")
try:
    response = requests.post(
        url,
        json=credentials,
        timeout=5,
        headers={"Content-Type": "application/json"}
    )

    print(f"   Status Code: {response.status_code}")
    print(f"   Response Headers:")
    for key, value in response.headers.items():
        if key.lower() not in ['set-cookie']:
            print(f"     {key}: {value}")

    print(f"\n4. Parsing response...")
    try:
        data = response.json()
        print(f"   Response Body:")
        print(json.dumps(data, indent=2))

        if response.status_code == 200:
            print(f"\n[OK] LOGIN SUCCESSFUL!")
            if "access_token" in data:
                print(f"   Access Token: {data['access_token'][:30]}...")
            if "user" in data:
                print(f"   User: {data['user']}")
        elif response.status_code == 401:
            print(f"\n[ERROR] Invalid credentials")
        elif response.status_code == 500:
            print(f"\n[ERROR] Server error - check API logs")
            print(f"        Error: {data.get('message', 'Unknown error')}")
        else:
            print(f"\n[ERROR] Unexpected status code {response.status_code}")

    except Exception as e:
        print(f"   [ERROR] Failed to parse response as JSON: {e}")
        print(f"   Raw response: {response.text[:200]}")

except requests.exceptions.RequestException as e:
    print(f"   [ERROR] Request failed: {e}")
    sys.exit(1)
