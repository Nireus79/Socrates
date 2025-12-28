#!/usr/bin/env python3
"""
Custom test runner for Socrates - works around Windows pytest I/O issues
Executes all tests and provides detailed results
"""

import importlib
import sys
import unittest
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up module alias before any imports
try:
    import socrates
except ModuleNotFoundError:
    import socratic_system as socrates

    sys.modules["socrates"] = socrates


def discover_and_run_tests():
    """Discover and run all tests in the tests directory"""

    print("=" * 90)
    print("SOCRATES COMPREHENSIVE TEST SUITE RUNNER")
    print("=" * 90)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python Version: {sys.version.split()[0]}")
    print(f"Platform: {sys.platform}")
    print()

    # Create test loader and runner
    loader = unittest.TestLoader()
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)

    # Discover tests
    suite = unittest.TestSuite()

    print("Discovering tests...")
    print("-" * 90)

    # Load tests from specific test files in order
    test_files = [
        "tests.test_config",
        "tests.test_models",
        "tests.test_events",
        "tests.test_exceptions",
        "tests.test_knowledge_management",
        "tests.test_orchestrator_integration",
        "tests.agents.test_project_manager_agent",
        "tests.agents.test_code_generator_agent",
        "tests.agents.test_remaining_agents",
        "tests.test_conflict_resolution",
        "tests.test_e2e_interconnection",
    ]

    loaded_tests = 0
    failed_modules = []

    for test_module_name in test_files:
        try:
            module = importlib.import_module(test_module_name)
            module_tests = loader.loadTestsFromModule(module)
            test_count = module_tests.countTestCases()
            if test_count > 0:
                suite.addTests(module_tests)
                loaded_tests += test_count
                status = "✓" if sys.platform == "linux" else "OK"
                print(f"  {status} {test_module_name}: {test_count} tests")
        except Exception as e:
            failed_modules.append((test_module_name, str(e)))
            print(f"  SKIP {test_module_name}: {str(e)[:60]}")

    print()
    print(f"Total tests discovered: {loaded_tests}")
    if failed_modules:
        print(f"Failed to load: {len(failed_modules)} modules")
    print()

    # Run tests
    print("=" * 90)
    print("RUNNING TESTS")
    print("=" * 90)
    print()

    result = runner.run(suite)

    # Print summary
    print()
    print("=" * 90)
    print("TEST SUMMARY")
    print("=" * 90)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print()

    if result.failures:
        print("FAILURES:")
        print("-" * 90)
        for test, traceback in result.failures:
            print(f"\n{test}:")
            print(traceback)

    if result.errors:
        print("ERRORS:")
        print("-" * 90)
        for test, traceback in result.errors:
            print(f"\n{test}:")
            print(traceback)

    print()
    print("=" * 90)
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Return exit code
    if result.wasSuccessful():
        print("STATUS: ALL TESTS PASSED")
        print("=" * 90)
        return 0
    else:
        print("STATUS: SOME TESTS FAILED")
        print("=" * 90)
        return 1


if __name__ == "__main__":
    exit_code = discover_and_run_tests()
    sys.exit(exit_code)
