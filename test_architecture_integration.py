#!/usr/bin/env python
"""
Integration test to verify new agent_bus architecture works end-to-end.
Tests orchestrator initialization, agent_bus routing, and API compatibility.
"""

import sys
import asyncio
from unittest.mock import MagicMock, patch

def test_orchestrator_initialization():
    """Test that orchestrator initializes with agent_bus."""
    print("\n" + "=" * 60)
    print("TEST 1: Orchestrator Initialization with Agent Bus")
    print("=" * 60)

    try:
        from socratic_system.orchestration.orchestrator import AgentOrchestrator

        # Create orchestrator
        orchestrator = AgentOrchestrator("test-api-key")

        # Verify agent_bus exists
        assert hasattr(orchestrator, "agent_bus"), "Missing agent_bus"
        print("[PASS] Orchestrator has agent_bus")

        # Verify agent_bus methods exist
        assert hasattr(orchestrator.agent_bus, "send_request_sync"), "Missing send_request_sync"
        print("[PASS] agent_bus has send_request_sync method")

        assert hasattr(orchestrator.agent_bus, "send_request"), "Missing async send_request"
        print("[PASS] agent_bus has async send_request method")

        # Verify database is initialized
        assert hasattr(orchestrator, "database"), "Missing database"
        print("[PASS] Orchestrator has database")

        # Verify agent registry exists
        assert hasattr(orchestrator, "agent_registry"), "Missing agent_registry"
        print("[PASS] Orchestrator has agent_registry")

        print("\n[SUCCESS] Orchestrator initialization test passed")
        return True
    except Exception as e:
        print(f"\n[FAILED] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_bus_send_request_sync():
    """Test that agent_bus.send_request_sync works."""
    print("\n" + "=" * 60)
    print("TEST 2: Agent Bus send_request_sync")
    print("=" * 60)

    try:
        from socratic_system.orchestration.orchestrator import AgentOrchestrator
        from socratic_system.events import EventEmitter

        # Create orchestrator with mocked client to avoid API calls
        with patch('socratic_nexus.clients.ClaudeClient'):
            orchestrator = AgentOrchestrator("test-api-key")

        # Mock agent response
        def mock_agent_process(request):
            return {"status": "success", "data": "test_response"}

        # Patch an agent's process method
        with patch.object(orchestrator.project_manager, 'process', side_effect=mock_agent_process):
            # Call via agent_bus
            result = orchestrator.agent_bus.send_request_sync(
                "project_manager",
                {"action": "test", "data": "test"}
            )

            assert result.get("status") == "success", f"Unexpected status: {result}"
            print("[PASS] agent_bus.send_request_sync returned expected result")

        print("\n[SUCCESS] Agent bus send_request_sync test passed")
        return True
    except Exception as e:
        print(f"\n[FAILED] {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_bus_async():
    """Test that agent_bus async methods work."""
    print("\n" + "=" * 60)
    print("TEST 3: Agent Bus Async Methods")
    print("=" * 60)

    try:
        from socratic_system.orchestration.orchestrator import AgentOrchestrator

        # Create orchestrator
        with patch('socratic_nexus.clients.ClaudeClient'):
            orchestrator = AgentOrchestrator("test-api-key")

        # Mock agent response
        async def mock_agent_process_async(request):
            return {"status": "success", "data": "async_response"}

        # Patch an agent's process_async method
        with patch.object(orchestrator.project_manager, 'process_async', side_effect=mock_agent_process_async):
            # Call via agent_bus async
            result = await orchestrator.agent_bus.send_request(
                "project_manager",
                {"action": "test_async", "data": "test"}
            )

            assert result.get("status") == "success", f"Unexpected status: {result}"
            print("[PASS] agent_bus.send_request (async) returned expected result")

        print("\n[SUCCESS] Agent bus async test passed")
        return True
    except Exception as e:
        print(f"\n[FAILED] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_initialization():
    """Test that database singleton initializes properly."""
    print("\n" + "=" * 60)
    print("TEST 4: Database Singleton Initialization")
    print("=" * 60)

    try:
        from socrates_api.database import DatabaseSingleton

        # Reset singleton
        DatabaseSingleton.reset()

        # Initialize database
        DatabaseSingleton.initialize()
        db = DatabaseSingleton.get_instance()

        assert db is not None, "Database instance is None"
        print("[PASS] Database singleton initialized successfully")

        # Verify we can get instance again
        db2 = DatabaseSingleton.get_instance()
        assert db is db2, "Database singleton not returning same instance"
        print("[PASS] Database singleton returns same instance")

        print("\n[SUCCESS] Database initialization test passed")
        return True
    except Exception as e:
        print(f"\n[FAILED] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_main_py_imports():
    """Test that main.py imports work with new architecture."""
    print("\n" + "=" * 60)
    print("TEST 5: API main.py Imports")
    print("=" * 60)

    try:
        # Import the main app
        from socrates_api.main import app, get_orchestrator

        assert app is not None, "Failed to import FastAPI app"
        print("[PASS] FastAPI app imported successfully")

        print("[PASS] get_orchestrator function available")

        print("\n[SUCCESS] API main.py imports test passed")
        return True
    except Exception as e:
        print(f"\n[FAILED] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_router_imports():
    """Test that all routers import successfully."""
    print("\n" + "=" * 60)
    print("TEST 6: Router Imports")
    print("=" * 60)

    routers = [
        "auth_router",
        "projects_router",
        "code_generation_router",
        "agents_router",
        "analysis_router",
    ]

    try:
        from socrates_api.main import (
            auth_router, projects_router, code_generation_router,
            agents_router, analysis_router
        )

        for router_name in routers:
            print(f"[PASS] {router_name} imported successfully")

        print("\n[SUCCESS] Router imports test passed")
        return True
    except Exception as e:
        print(f"\n[FAILED] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_service_layer_access():
    """Test that services can access agent_bus through orchestrator."""
    print("\n" + "=" * 60)
    print("TEST 7: Service Layer Agent Bus Access")
    print("=" * 60)

    try:
        from socratic_system.services import CodeService
        from socratic_system.orchestration.orchestrator import AgentOrchestrator
        from unittest.mock import MagicMock

        # Create orchestrator
        with patch('socratic_nexus.clients.ClaudeClient'):
            orchestrator = AgentOrchestrator("test-api-key")

        # Create service
        config = MagicMock()
        service = CodeService(config=config, orchestrator=orchestrator)

        # Verify service has access to agent_bus through orchestrator
        assert hasattr(service.orchestrator, "agent_bus"), "Service orchestrator missing agent_bus"
        print("[PASS] Service can access orchestrator.agent_bus")

        print("\n[SUCCESS] Service layer agent_bus access test passed")
        return True
    except Exception as e:
        print(f"\n[FAILED] {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests."""
    print("\n" + "=" * 60)
    print("ARCHITECTURE INTEGRATION TEST SUITE")
    print("=" * 60)

    tests = [
        ("Orchestrator Initialization", test_orchestrator_initialization),
        ("Agent Bus Sync", test_agent_bus_send_request_sync),
        ("Database Initialization", test_database_initialization),
        ("API Main.py Imports", test_api_main_py_imports),
        ("Router Imports", test_router_imports),
        ("Service Layer Access", test_service_layer_access),
    ]

    async_tests = [
        ("Agent Bus Async", test_agent_bus_async),
    ]

    results = {}

    # Run sync tests
    for name, test_func in tests:
        results[name] = test_func()

    # Run async tests
    for name, test_func in async_tests:
        try:
            results[name] = asyncio.run(test_func())
        except Exception as e:
            print(f"[FAILED] {name}: {e}")
            results[name] = False

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n[SUCCESS] All integration tests passed!")
        print("New agent_bus architecture is working correctly.")
        return 0
    else:
        print(f"\n[FAILED] {total - passed} tests failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
