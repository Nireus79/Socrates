#!/usr/bin/env python
"""
Verification script for Phase 3 framework integration.
Tests that both framework integrations are accessible and functional.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("phase3_verification")

def verify_framework_imports():
    """Verify both framework libraries can be imported"""
    logger.info("=" * 70)
    logger.info("VERIFYING FRAMEWORK IMPORTS")
    logger.info("=" * 70)

    results = {}

    try:
        from socrates_ai_langraph import create_socrates_langgraph_workflow, AgentState
        logger.info("PASS: socrates-ai-langraph imported successfully")
        results["socrates-ai-langraph"] = True
    except Exception as e:
        logger.error(f"FAIL: socrates-ai-langraph import failed: {e}")
        results["socrates-ai-langraph"] = False

    try:
        from socratic_openclaw_skill import SocraticDiscoverySkill, SocraticOpenclawConfig
        logger.info("PASS: socratic-openclaw-skill imported successfully")
        results["socratic-openclaw-skill"] = True
    except Exception as e:
        logger.error(f"FAIL: socratic-openclaw-skill import failed: {e}")
        results["socratic-openclaw-skill"] = False

    passed = sum(1 for v in results.values() if v)
    logger.info(f"\nFramework imports: {passed}/2 passed")
    return passed == 2

def verify_integration_classes():
    """Verify integration classes are accessible"""
    logger.info("\n" + "=" * 70)
    logger.info("VERIFYING INTEGRATION CLASSES")
    logger.info("=" * 70)

    results = {}

    try:
        from socratic_system.orchestration.library_integrations import LangGraphIntegration
        logger.info("PASS: LangGraphIntegration class found")

        # Try to instantiate
        integration = LangGraphIntegration()
        logger.info(f"  - Instantiation: OK")
        logger.info(f"  - Enabled: {integration.enabled}")
        results["LangGraphIntegration"] = True
    except Exception as e:
        logger.error(f"FAIL: LangGraphIntegration failed: {e}")
        results["LangGraphIntegration"] = False

    try:
        from socratic_system.orchestration.library_integrations import SocraticOpenclawIntegration
        logger.info("PASS: SocraticOpenclawIntegration class found")

        # Try to instantiate
        integration = SocraticOpenclawIntegration()
        logger.info(f"  - Instantiation: OK")
        logger.info(f"  - Enabled: {integration.enabled}")
        results["SocraticOpenclawIntegration"] = True
    except Exception as e:
        logger.error(f"FAIL: SocraticOpenclawIntegration failed: {e}")
        results["SocraticOpenclawIntegration"] = False

    passed = sum(1 for v in results.values() if v)
    logger.info(f"\nIntegration classes: {passed}/2 passed")
    return passed == 2

def verify_library_manager():
    """Verify SocraticLibraryManager has new integrations"""
    logger.info("\n" + "=" * 70)
    logger.info("VERIFYING LIBRARY MANAGER")
    logger.info("=" * 70)

    try:
        from socratic_system.orchestration.library_integrations import SocraticLibraryManager

        manager = SocraticLibraryManager()
        logger.info("PASS: SocraticLibraryManager instantiated")

        # Check for new framework integrations
        has_langgraph = hasattr(manager, 'langgraph')
        has_openclaw = hasattr(manager, 'openclaw')

        logger.info(f"  - Has langgraph property: {has_langgraph}")
        logger.info(f"  - Has openclaw property: {has_openclaw}")

        # Check status
        status = manager.get_status()
        logger.info(f"  - Total libraries in status: {len(status)}")
        logger.info(f"  - Libraries: {list(status.keys())}")

        return has_langgraph and has_openclaw and len(status) == 16
    except Exception as e:
        logger.error(f"FAIL: Library manager check failed: {e}")
        return False

def verify_integration_methods():
    """Verify integration methods are callable"""
    logger.info("\n" + "=" * 70)
    logger.info("VERIFYING INTEGRATION METHODS")
    logger.info("=" * 70)

    results = {}

    try:
        from socratic_system.orchestration.library_integrations import LangGraphIntegration

        integration = LangGraphIntegration()
        methods = ['create_workflow', 'execute_workflow', 'get_agents', 'get_status']

        all_exist = True
        for method in methods:
            exists = hasattr(integration, method) and callable(getattr(integration, method))
            logger.info(f"  - LangGraphIntegration.{method}: {exists}")
            all_exist = all_exist and exists

        results["LangGraphIntegration methods"] = all_exist
    except Exception as e:
        logger.error(f"FAIL: LangGraphIntegration methods check failed: {e}")
        results["LangGraphIntegration methods"] = False

    try:
        from socratic_system.orchestration.library_integrations import SocraticOpenclawIntegration

        integration = SocraticOpenclawIntegration()
        methods = ['start_discovery', 'respond', 'generate', 'get_session', 'list_sessions', 'get_status']

        all_exist = True
        for method in methods:
            exists = hasattr(integration, method) and callable(getattr(integration, method))
            logger.info(f"  - SocraticOpenclawIntegration.{method}: {exists}")
            all_exist = all_exist and exists

        results["SocraticOpenclawIntegration methods"] = all_exist
    except Exception as e:
        logger.error(f"FAIL: SocraticOpenclawIntegration methods check failed: {e}")
        results["SocraticOpenclawIntegration methods"] = False

    passed = sum(1 for v in results.values() if v)
    logger.info(f"\nIntegration methods: {passed}/2 passed")
    return passed == 2

def main():
    """Run all Phase 3 verifications"""
    logger.info("\n" + "=" * 70)
    logger.info("PHASE 3 FRAMEWORK INTEGRATION VERIFICATION")
    logger.info("=" * 70 + "\n")

    results = {
        "Framework Imports": verify_framework_imports(),
        "Integration Classes": verify_integration_classes(),
        "Library Manager": verify_library_manager(),
        "Integration Methods": verify_integration_methods(),
    }

    logger.info("\n" + "=" * 70)
    logger.info("PHASE 3 VERIFICATION SUMMARY")
    logger.info("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        logger.info(f"{status}: {test_name}")

    logger.info(f"\nTotal: {passed}/{total} verification groups passed")
    logger.info("=" * 70 + "\n")

    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
