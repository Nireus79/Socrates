#!/usr/bin/env python
"""
Verification script for Phase 5 interface integration.
Tests that both interface package integrations are accessible and functional.
"""

import sys
import logging
import os
from pathlib import Path

# Set dummy API key for testing
os.environ['ANTHROPIC_API_KEY'] = 'test_key_for_verification'

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("phase5_verification")


def verify_cli_integration():
    """Verify CLIIntegration enhancements"""
    logger.info("=" * 70)
    logger.info("VERIFYING CLI INTEGRATION")
    logger.info("=" * 70)

    results = {}

    try:
        from socratic_system.orchestration.library_integrations import CLIIntegration

        integration = CLIIntegration()
        logger.info("PASS: CLIIntegration class found and instantiated")

        # Test new Phase 5 methods
        methods = [
            'list_commands',
            'list_categories',
            'get_help',
            'get_command_info',
            'execute_command',
            'search_commands',
            'get_status'
        ]

        all_exist = True
        for method in methods:
            exists = hasattr(integration, method) and callable(getattr(integration, method))
            logger.info(f"  - CLIIntegration.{method}: {exists}")
            all_exist = all_exist and exists

        # Test status
        status = integration.get_status()
        logger.info(f"  - get_status() returned: interface={status.get('interface')}")

        # Test methods that should return lists/dicts
        commands = integration.list_commands()
        logger.info(f"  - list_commands() returned: {type(commands).__name__}")

        categories = integration.list_categories()
        logger.info(f"  - list_categories() returned: {type(categories).__name__}")

        results["CLIIntegration"] = all_exist
    except Exception as e:
        logger.error(f"FAIL: CLIIntegration verification failed: {e}")
        results["CLIIntegration"] = False

    passed = sum(1 for v in results.values() if v)
    logger.info(f"\nCLI Integration: {passed}/1 passed")
    return passed == 1


def verify_api_integration():
    """Verify APIIntegration enhancements"""
    logger.info("\n" + "=" * 70)
    logger.info("VERIFYING API INTEGRATION")
    logger.info("=" * 70)

    results = {}

    try:
        from socratic_system.orchestration.library_integrations import APIIntegration

        integration = APIIntegration()
        logger.info("PASS: APIIntegration class found and instantiated")

        # Test new Phase 5 methods
        methods = [
            'list_projects',
            'create_project',
            'get_project',
            'delete_project',
            'list_chats',
            'start_chat',
            'send_message',
            'get_knowledge_items',
            'import_knowledge',
            'get_analytics',
            'call_api_endpoint',
            'get_status'
        ]

        all_exist = True
        for method in methods:
            exists = hasattr(integration, method) and callable(getattr(integration, method))
            logger.info(f"  - APIIntegration.{method}: {exists}")
            all_exist = all_exist and exists

        # Test status
        status = integration.get_status()
        logger.info(f"  - get_status() returned: interface={status.get('interface')}")

        # Test methods that should return lists
        projects = integration.list_projects()
        logger.info(f"  - list_projects() returned: {type(projects).__name__}")

        knowledge = integration.get_knowledge_items()
        logger.info(f"  - get_knowledge_items() returned: {type(knowledge).__name__}")

        results["APIIntegration"] = all_exist
    except Exception as e:
        logger.error(f"FAIL: APIIntegration verification failed: {e}")
        results["APIIntegration"] = False

    passed = sum(1 for v in results.values() if v)
    logger.info(f"\nAPI Integration: {passed}/1 passed")
    return passed == 1


def verify_library_manager_update():
    """Verify SocraticLibraryManager has both interface integrations"""
    logger.info("\n" + "=" * 70)
    logger.info("VERIFYING LIBRARY MANAGER UPDATES")
    logger.info("=" * 70)

    try:
        from socratic_system.orchestration.library_integrations import SocraticLibraryManager

        manager = SocraticLibraryManager({})
        logger.info("PASS: SocraticLibraryManager instantiated")

        # Check for new interface integrations
        has_cli = hasattr(manager, 'cli')
        has_api = hasattr(manager, 'api')

        logger.info(f"  - Has cli property: {has_cli}")
        logger.info(f"  - Has api property: {has_api}")

        # Check status includes both
        status = manager.get_status()
        logger.info(f"  - Total integrations in status: {len(status)}")
        logger.info(f"  - Includes 'cli': {'cli' in status}")
        logger.info(f"  - Includes 'api': {'api' in status}")

        # Check repr
        repr_str = repr(manager)
        logger.info(f"  - Manager repr: {repr_str}")

        return has_cli and has_api and 'cli' in status and 'api' in status
    except Exception as e:
        logger.error(f"FAIL: Library manager verification failed: {e}")
        return False


def main():
    """Run all Phase 5 verifications"""
    logger.info("\n" + "=" * 70)
    logger.info("PHASE 5 INTERFACE INTEGRATION VERIFICATION")
    logger.info("=" * 70 + "\n")

    results = {
        "CLI Integration": verify_cli_integration(),
        "API Integration": verify_api_integration(),
        "Library Manager": verify_library_manager_update(),
    }

    logger.info("\n" + "=" * 70)
    logger.info("PHASE 5 VERIFICATION SUMMARY")
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
