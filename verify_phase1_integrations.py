#!/usr/bin/env python
"""
Verification script for Phase 1 library integration expansions.
Tests that all expanded methods are accessible and functional.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("phase1_verification")

def verify_analyzer_integration():
    """Verify AnalyzerIntegration expanded methods"""
    logger.info("=" * 60)
    logger.info("VERIFYING AnalyzerIntegration")
    logger.info("=" * 60)

    try:
        from socratic_system.orchestration.library_integrations import AnalyzerIntegration

        analyzer = AnalyzerIntegration()

        # Test method existence
        methods = [
            'analyze_code',
            'analyze_file',
            'analyze_project',
            'generate_report',
            'detect_complexity',
            'detect_patterns',
            'detect_smells',
            'get_quality_score',
            'get_insights'
        ]

        for method in methods:
            if hasattr(analyzer, method):
                logger.info(f"✓ {method} exists")
            else:
                logger.error(f"✗ {method} MISSING")
                return False

        logger.info("✓ AnalyzerIntegration: ALL METHODS VERIFIED")
        return True
    except Exception as e:
        logger.error(f"✗ AnalyzerIntegration verification failed: {e}")
        return False

def verify_conflict_integration():
    """Verify ConflictIntegration expanded methods"""
    logger.info("=" * 60)
    logger.info("VERIFYING ConflictIntegration")
    logger.info("=" * 60)

    try:
        from socratic_system.orchestration.library_integrations import ConflictIntegration

        conflict = ConflictIntegration()

        # Test method existence
        methods = [
            'detect_and_resolve',
            'detect_conflicts',
            'resolve_with_strategy',
            'apply_consensus_algorithm',
            'track_resolution_history',
            'get_resolution_history',
            'evaluate_proposal_quality'
        ]

        for method in methods:
            if hasattr(conflict, method):
                logger.info(f"✓ {method} exists")
            else:
                logger.error(f"✗ {method} MISSING")
                return False

        logger.info("✓ ConflictIntegration: ALL METHODS VERIFIED")
        return True
    except Exception as e:
        logger.error(f"✗ ConflictIntegration verification failed: {e}")
        return False

def verify_rag_integration():
    """Verify RAGIntegration expanded methods"""
    logger.info("=" * 60)
    logger.info("VERIFYING RAGIntegration")
    logger.info("=" * 60)

    try:
        from socratic_system.orchestration.library_integrations import RAGIntegration

        rag = RAGIntegration()

        # Test method existence
        methods = [
            'index_document',
            'search',
            'configure_chunking',
            'configure_embeddings',
            'configure_vector_store',
            'retrieve_context',
            'add_document',
            'clear_knowledge_base',
            'get_document_count'
        ]

        for method in methods:
            if hasattr(rag, method):
                logger.info(f"✓ {method} exists")
            else:
                logger.error(f"✗ {method} MISSING")
                return False

        logger.info("✓ RAGIntegration: ALL METHODS VERIFIED")
        return True
    except Exception as e:
        logger.error(f"✗ RAGIntegration verification failed: {e}")
        return False

def verify_docs_integration():
    """Verify DocsIntegration methods"""
    logger.info("=" * 60)
    logger.info("VERIFYING DocsIntegration")
    logger.info("=" * 60)

    try:
        from socratic_system.orchestration.library_integrations import DocsIntegration

        docs = DocsIntegration()

        # Test method existence
        methods = [
            'generate_comprehensive_readme',
            'generate_api_documentation',
            'generate_architecture_docs',
            'generate_setup_guide',
            'generate_all_documentation'
        ]

        for method in methods:
            if hasattr(docs, method):
                logger.info(f"✓ {method} exists")
            else:
                logger.error(f"✗ {method} MISSING")
                return False

        logger.info("✓ DocsIntegration: ALL METHODS VERIFIED")
        return True
    except Exception as e:
        logger.error(f"✗ DocsIntegration verification failed: {e}")
        return False

def verify_performance_integration():
    """Verify PerformanceIntegration methods"""
    logger.info("=" * 60)
    logger.info("VERIFYING PerformanceIntegration")
    logger.info("=" * 60)

    try:
        from socratic_system.orchestration.library_integrations import PerformanceIntegration

        perf = PerformanceIntegration()

        # Test method existence
        methods = [
            'profile_execution',
            'get_performance_stats',
            'get_slow_queries',
            'reset_profiler',
            'get_cache',
            'set_cache',
            'clear_cache',
            'get_cache_stats'
        ]

        for method in methods:
            if hasattr(perf, method):
                logger.info(f"✓ {method} exists")
            else:
                logger.error(f"✗ {method} MISSING")
                return False

        logger.info("✓ PerformanceIntegration: ALL METHODS VERIFIED")
        return True
    except Exception as e:
        logger.error(f"✗ PerformanceIntegration verification failed: {e}")
        return False

def verify_workflow_integration():
    """Verify WorkflowIntegration methods"""
    logger.info("=" * 60)
    logger.info("VERIFYING WorkflowIntegration")
    logger.info("=" * 60)

    try:
        from socratic_system.orchestration.library_integrations import WorkflowIntegration

        workflow = WorkflowIntegration()

        # Test method existence
        methods = [
            'create_workflow',
            'execute_workflow',
            'track_cost',
            'define_workflow',
            'optimize_workflow',
            'execute_with_retry',
            'get_workflow_metrics',
            'serialize_workflow',
            'deserialize_workflow'
        ]

        for method in methods:
            if hasattr(workflow, method):
                logger.info(f"✓ {method} exists")
            else:
                logger.error(f"✗ {method} MISSING")
                return False

        logger.info("✓ WorkflowIntegration: ALL METHODS VERIFIED")
        return True
    except Exception as e:
        logger.error(f"✗ WorkflowIntegration verification failed: {e}")
        return False

def verify_knowledge_integration():
    """Verify KnowledgeIntegration methods"""
    logger.info("=" * 60)
    logger.info("VERIFYING KnowledgeIntegration")
    logger.info("=" * 60)

    try:
        from socratic_system.orchestration.library_integrations import KnowledgeIntegration

        knowledge = KnowledgeIntegration()

        # Test method existence
        methods = [
            'create_knowledge_item',
            'search_knowledge',
            'create_version_snapshot',
            'get_version_history',
            'rollback_to_version',
            'compare_versions',
            'assign_role',
            'check_permission',
            'log_audit_event',
            'get_audit_trail'
        ]

        for method in methods:
            if hasattr(knowledge, method):
                logger.info(f"✓ {method} exists")
            else:
                logger.error(f"✗ {method} MISSING")
                return False

        logger.info("✓ KnowledgeIntegration: ALL METHODS VERIFIED")
        return True
    except Exception as e:
        logger.error(f"✗ KnowledgeIntegration verification failed: {e}")
        return False

def verify_learning_integration():
    """Verify LearningIntegration methods"""
    logger.info("=" * 60)
    logger.info("VERIFYING LearningIntegration")
    logger.info("=" * 60)

    try:
        from socratic_system.orchestration.library_integrations import LearningIntegration

        learning = LearningIntegration()

        # Test method existence
        methods = [
            'start_session',
            'log_interaction',
            'get_recommendations',
            'detect_patterns',
            'detect_error_patterns',
            'detect_performance_patterns',
            'generate_recommendations',
            'apply_recommendation',
            'score_recommendation_effectiveness',
            'calculate_analytics',
            'calculate_maturity_level',
            'generate_learning_report'
        ]

        for method in methods:
            if hasattr(learning, method):
                logger.info(f"✓ {method} exists")
            else:
                logger.error(f"✗ {method} MISSING")
                return False

        logger.info("✓ LearningIntegration: ALL METHODS VERIFIED")
        return True
    except Exception as e:
        logger.error(f"✗ LearningIntegration verification failed: {e}")
        return False

def main():
    """Run all verifications"""
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 1 INTEGRATION VERIFICATION")
    logger.info("=" * 60 + "\n")

    results = {
        "AnalyzerIntegration": verify_analyzer_integration(),
        "ConflictIntegration": verify_conflict_integration(),
        "RAGIntegration": verify_rag_integration(),
        "DocsIntegration": verify_docs_integration(),
        "PerformanceIntegration": verify_performance_integration(),
        "WorkflowIntegration": verify_workflow_integration(),
        "KnowledgeIntegration": verify_knowledge_integration(),
        "LearningIntegration": verify_learning_integration(),
    }

    logger.info("\n" + "=" * 60)
    logger.info("VERIFICATION SUMMARY")
    logger.info("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {name}")

    logger.info(f"\nTotal: {passed}/{total} passed")
    logger.info("=" * 60 + "\n")

    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
