"""
Load testing for Socrates REST API

Tests API performance under concurrent load using locust.

Run with:
    locust -f tests/load_test.py --host=http://localhost:8000

Or with headless mode:
    locust -f tests/load_test.py --host=http://localhost:8000 \
            --users=100 --spawn-rate=10 --run-time=5m --headless
"""

import os
from locust import HttpUser, task, between, events
import json


class SocratesAPIUser(HttpUser):
    """Simulates a user interacting with Socrates API"""

    # Wait between 1-3 seconds between requests
    wait_time = between(1, 3)

    def on_start(self):
        """Initialize user session"""
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "sk-ant-test")
        self.project_id = None
        self.initialize_api()

    def initialize_api(self):
        """Initialize API connection"""
        response = self.client.post("/initialize", json={
            "api_key": self.api_key
        })

        if response.status_code == 200:
            self.project_id = "test_proj_load"

    @task(3)
    def list_projects(self):
        """List projects (weight: 3)"""
        with self.client.get(
            "/projects",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 503:
                response.failure("Service not initialized")
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(2)
    def create_project(self):
        """Create a project (weight: 2)"""
        with self.client.post(
            "/projects",
            json={
                "name": f"Load Test Project {self.client.task_id}",
                "owner": "load_test_user"
            },
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
                try:
                    data = response.json()
                    self.project_id = data.get("project_id")
                except:
                    pass
            elif response.status_code in [400, 503]:
                response.failure(f"Failed to create project: {response.status_code}")
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(2)
    def get_event_history(self):
        """Get event history (weight: 2)"""
        with self.client.get(
            "/api/events/history?limit=50",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(1)
    def health_check(self):
        """Health check (weight: 1)"""
        with self.client.get(
            "/health",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(1)
    def test_connection(self):
        """Test API connection (weight: 1)"""
        with self.client.post(
            "/api/test-connection",
            json={},
            catch_response=True
        ) as response:
            if response.status_code in [200, 400]:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")


class AdminUser(HttpUser):
    """Admin user performing monitoring tasks"""

    wait_time = between(5, 10)

    @task
    def get_info(self):
        """Get system info"""
        with self.client.get(
            "/info",
            catch_response=True
        ) as response:
            if response.status_code in [200, 503]:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")


# Event hooks for monitoring
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts"""
    print("=" * 70)
    print("SOCRATES API LOAD TEST STARTED")
    print("=" * 70)
    print(f"Target: {environment.host}")
    print(f"Users: {len(environment.user_instances)}")
    print()


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops"""
    print("\n" + "=" * 70)
    print("SOCRATES API LOAD TEST STOPPED")
    print("=" * 70)

    # Print statistics
    stats = environment.stats
    print("\nResponse Statistics:")
    print(f"  Total Requests: {stats.total.num_requests}")
    print(f"  Total Failures: {stats.total.num_failures}")
    print(f"  Average Response Time: {stats.total.avg_response_time:.0f}ms")
    print(f"  Min Response Time: {stats.total.min_response_time:.0f}ms")
    print(f"  Max Response Time: {stats.total.max_response_time:.0f}ms")
    print(f"  Requests/sec: {stats.total.total_rps:.2f}")

    # Request breakdown
    print("\nRequest Breakdown:")
    for endpoint, stats_entry in stats.entries.items():
        print(f"  {endpoint}")
        print(f"    Requests: {stats_entry.num_requests}")
        print(f"    Failures: {stats_entry.num_failures}")
        print(f"    Avg Response: {stats_entry.avg_response_time:.0f}ms")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, response, context, exception, **kwargs):
    """Called after each request"""
    if exception:
        print(f"[ERROR] {request_type} {name}: {exception}")


# Load test configurations
LOAD_TEST_SCENARIOS = {
    "light": {
        "description": "Light load test",
        "users": 10,
        "spawn_rate": 2,
        "duration": "1m"
    },
    "medium": {
        "description": "Medium load test",
        "users": 50,
        "spawn_rate": 5,
        "duration": "5m"
    },
    "heavy": {
        "description": "Heavy load test",
        "users": 200,
        "spawn_rate": 20,
        "duration": "10m"
    },
    "stress": {
        "description": "Stress test (find breaking point)",
        "users": 500,
        "spawn_rate": 50,
        "duration": "15m"
    }
}


def print_load_test_guide():
    """Print load test usage guide"""
    print("""
SOCRATES API LOAD TESTING GUIDE
================================

1. Start the API server:
   python socrates-api/src/socrates_api/main.py

2. In another terminal, run load tests:

   Interactive mode (with web UI):
   locust -f tests/load_test.py --host=http://localhost:8000

   Headless mode (light load):
   locust -f tests/load_test.py --host=http://localhost:8000 \\
       --users=10 --spawn-rate=2 --run-time=1m --headless

   Headless mode (medium load):
   locust -f tests/load_test.py --host=http://localhost:8000 \\
       --users=50 --spawn-rate=5 --run-time=5m --headless

   Headless mode (heavy load):
   locust -f tests/load_test.py --host=http://localhost:8000 \\
       --users=200 --spawn-rate=20 --run-time=10m --headless

   Headless mode (stress test):
   locust -f tests/load_test.py --host=http://localhost:8000 \\
       --users=500 --spawn-rate=50 --run-time=15m --headless

3. View results in the web UI (http://localhost:8089) or terminal

Load Test Scenarios
===================
""")

    for scenario, config in LOAD_TEST_SCENARIOS.items():
        print(f"\n{scenario.upper()}: {config['description']}")
        print(f"  Users: {config['users']}")
        print(f"  Spawn rate: {config['spawn_rate']} users/sec")
        print(f"  Duration: {config['duration']}")

    print("""

Task Weights
============
- list_projects: 3 (30% of requests)
- create_project: 2 (20% of requests)
- get_event_history: 2 (20% of requests)
- health_check: 1 (10% of requests)
- test_connection: 1 (10% of requests)
- (admin) get_info: varied

Performance Targets
===================
- Response time: < 500ms (avg)
- 95th percentile: < 2000ms
- 99th percentile: < 5000ms
- Error rate: < 1%
- Throughput: > 100 req/s

Expected Results
================
Light Load (10 users):
  - Expected throughput: 10-20 req/s
  - Expected response time: 50-200ms

Medium Load (50 users):
  - Expected throughput: 50-100 req/s
  - Expected response time: 100-500ms

Heavy Load (200 users):
  - Expected throughput: 100-200 req/s
  - Expected response time: 200-1000ms

Stress Test (500 users):
  - Find breaking point
  - Identify bottlenecks
  - Response times may exceed 5s
""")


if __name__ == "__main__":
    print_load_test_guide()
