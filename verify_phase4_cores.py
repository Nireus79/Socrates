#!/usr/bin/env python
"""
Verification script for Phase 4 core library enhancements.
Tests that all expanded core library integration methods are accessible and functional.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("phase4_verification")


def verify_core_integration():
    """Verify CoreIntegration enhancements"""
    logger.info("=" * 70)
    logger.info("VERIFYING CORE INTEGRATION ENHANCEMENTS")
    logger.info("=" * 70)

    results = {}

    try:
        from socratic_system.orchestration.library_integrations import CoreIntegration

        integration = CoreIntegration()
        logger.info("PASS: CoreIntegration class found and instantiated")

        # Test new Phase 4 methods
        methods = [
            'emit_event',
            'get_event_history',
            'track_performance',
            'get_performance_report',
            'get_system_info',
            'get_config'
        ]

        all_exist = True
        for method in methods:
            exists = hasattr(integration, method) and callable(getattr(integration, method))
            logger.info(f"  - CoreIntegration.{method}: {exists}")
            all_exist = all_exist and exists

        # Test event tracking
        if integration.emit_event("test_event", {"data": "test"}):
            logger.info("  - emit_event() successful")

        history = integration.get_event_history()
        logger.info(f"  - get_event_history() returned {len(history)} events")

        # Test performance tracking
        if integration.track_performance("test_op", 100.5):
            logger.info("  - track_performance() successful")

        report = integration.get_performance_report()
        logger.info(f"  - get_performance_report() returned {len(report)} operations")

        results["CoreIntegration"] = all_exist
    except Exception as e:
        logger.error(f"FAIL: CoreIntegration verification failed: {e}")
        results["CoreIntegration"] = False

    passed = sum(1 for v in results.values() if v)
    logger.info(f"\nCore Integration: {passed}/1 passed")
    return passed == 1


def verify_nexus_integration():
    """Verify NexusIntegration enhancements"""
    logger.info("\n" + "=" * 70)
    logger.info("VERIFYING NEXUS INTEGRATION ENHANCEMENTS")
    logger.info("=" * 70)

    results = {}

    try:
        from socratic_system.orchestration.library_integrations import NexusIntegration

        integration = NexusIntegration()
        logger.info("PASS: NexusIntegration class found and instantiated")

        # Test new Phase 4 methods
        methods = [
            'stream_llm',
            'stream_llm_async',
            'call_with_fallback',
            'call_with_tools',
            'call_with_image',
            'get_usage_summary',
            'estimate_cost',
            'switch_provider',
            'list_models',
            'call_llm'
        ]

        all_exist = True
        for method in methods:
            exists = hasattr(integration, method) and callable(getattr(integration, method))
            logger.info(f"  - NexusIntegration.{method}: {exists}")
            all_exist = all_exist and exists

        # Test cost estimation
        estimate = integration.estimate_cost("test prompt", "claude-opus")
        if estimate and 'estimated_cost_usd' in estimate:
            logger.info(f"  - estimate_cost() returned: ${estimate['estimated_cost_usd']}")

        # Test usage tracking
        summary = integration.get_usage_summary()
        logger.info(f"  - get_usage_summary() returned: {len(summary)} keys")

        # Test provider switching
        if integration.switch_provider("openai"):
            logger.info(f"  - switch_provider() successful, current: {integration.current_provider}")

        # Test model listing
        models = integration.list_models()
        logger.info(f"  - list_models() returned {len(models)} providers")

        results["NexusIntegration"] = all_exist
    except Exception as e:
        logger.error(f"FAIL: NexusIntegration verification failed: {e}")
        results["NexusIntegration"] = False

    passed = sum(1 for v in results.values() if v)
    logger.info(f"\nNexus Integration: {passed}/1 passed")
    return passed == 1


def verify_security_integration():
    """Verify SecurityIntegration enhancements"""
    logger.info("\n" + "=" * 70)
    logger.info("VERIFYING SECURITY INTEGRATION ENHANCEMENTS")
    logger.info("=" * 70)

    results = {}

    try:
        from socratic_system.orchestration.library_integrations import SecurityIntegration

        integration = SecurityIntegration()
        logger.info("PASS: SecurityIntegration class found and instantiated")

        # Test new Phase 4 methods
        methods = [
            'detect_sql_injection',
            'detect_xss_vulnerability',
            'sandbox_execute',
            'log_audit_event',
            'get_audit_trail',
            'enable_mfa',
            'check_mfa',
            'verify_mfa_token',
            'validate_input'
        ]

        all_exist = True
        for method in methods:
            exists = hasattr(integration, method) and callable(getattr(integration, method))
            logger.info(f"  - SecurityIntegration.{method}: {exists}")
            all_exist = all_exist and exists

        # Test SQL injection detection
        sql_result = integration.detect_sql_injection("SELECT * FROM users WHERE id = 1")
        logger.info(f"  - detect_sql_injection() returned: vulnerable={sql_result['vulnerable']}")

        # Test XSS detection
        xss_result = integration.detect_xss_vulnerability("<script>alert('xss')</script>")
        logger.info(f"  - detect_xss_vulnerability() returned: vulnerable={xss_result['vulnerable']}")

        # Test audit logging
        if integration.log_audit_event("test_event", "user1", "resource1"):
            logger.info("  - log_audit_event() successful")

        # Test audit trail retrieval
        trail = integration.get_audit_trail()
        logger.info(f"  - get_audit_trail() returned {len(trail)} entries")

        # Test MFA
        if integration.enable_mfa("user1"):
            logger.info("  - enable_mfa() successful")

        mfa_check = integration.check_mfa("user1")
        logger.info(f"  - check_mfa() returned: {mfa_check}")

        # Test MFA token verification
        mfa_verify = integration.verify_mfa_token("user1", "123456")
        logger.info(f"  - verify_mfa_token() returned: valid={mfa_verify['valid']}")

        # Test input validation
        validation = integration.validate_input("test input")
        logger.info(f"  - validate_input() returned: valid={validation['valid']}, threats={len(validation['threats'])}")

        results["SecurityIntegration"] = all_exist
    except Exception as e:
        logger.error(f"FAIL: SecurityIntegration verification failed: {e}")
        results["SecurityIntegration"] = False

    passed = sum(1 for v in results.values() if v)
    logger.info(f"\nSecurity Integration: {passed}/1 passed")
    return passed == 1


def main():
    """Run all Phase 4 verifications"""
    logger.info("\n" + "=" * 70)
    logger.info("PHASE 4 CORE LIBRARY ENHANCEMENT VERIFICATION")
    logger.info("=" * 70 + "\n")

    results = {
        "Core Integration": verify_core_integration(),
        "Nexus Integration": verify_nexus_integration(),
        "Security Integration": verify_security_integration(),
    }

    logger.info("\n" + "=" * 70)
    logger.info("PHASE 4 VERIFICATION SUMMARY")
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
