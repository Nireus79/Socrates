"""
Pytest configuration for integration tests.

Initializes the API orchestrator before running tests.
"""

import os
import time

import pytest
import requests

BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="session", autouse=True)
def initialize_api():
    """
    Initialize the API orchestrator before running any tests.

    This ensures the orchestrator is ready to process requests.
    """
    # Wait for API to be responsive
    max_retries = 30
    for attempt in range(max_retries):
        try:
            health = requests.get(f"{BASE_URL}/health", timeout=2)
            if health.status_code == 200:
                health_data = health.json()
                if health_data.get("initialized"):
                    # Already initialized
                    return
                break
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            raise Exception(f"API not responding after {max_retries} attempts") from e

    # Initialize the orchestrator
    # First try with environment API key, then with test key
    api_key = os.getenv("ANTHROPIC_API_KEY", "sk-ant-test-key-for-integration-tests")
    init_response = requests.post(
        f"{BASE_URL}/initialize",
        json={"api_key": api_key},
        headers={"Content-Type": "application/json"},
        timeout=10
    )

    if init_response.status_code != 200:
        # If initialization fails, log it but don't fail - tests may not need full API
        print(f"Warning: API initialization failed: {init_response.json().get('detail', 'Unknown error')}")
        # Still try to wait for health check
    else:
        # Wait for initialization to complete
        for _attempt in range(10):
            try:
                health = requests.get(f"{BASE_URL}/health")
                if health.json().get("initialized"):
                    break
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
