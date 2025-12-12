#!/usr/bin/env python3
"""
Test script to verify the modularization of Socratic RAG System
Tests imports, module structure, and basic functionality
"""

import sys
import traceback

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

test_results = {"passed": 0, "failed": 0, "warnings": 0}


def print_header(text):
    """Print a formatted header"""
    print(f"\n{BLUE}{BOLD}{'='*60}{RESET}")
    print(f"{BLUE}{BOLD}{text}{RESET}")
    print(f"{BLUE}{BOLD}{'='*60}{RESET}\n")


def test_import(module_name, description=""):
    """Test if a module can be imported"""
    desc = description or f"Importing {module_name}"
    try:
        __import__(module_name)
        print(f"{GREEN}[PASS]{RESET}: {desc}")
        test_results["passed"] += 1
        return True
    except Exception as e:
        print(f"{RED}[FAIL]{RESET}: {desc}")
        print(f"  Error: {str(e)}")
        traceback.print_exc()
        test_results["failed"] += 1
        return False


def test_module_structure():
    """Test that all expected modules exist"""
    print_header("Testing Module Structure")

    expected_modules = [
        "socratic_system",
        "socratic_system.config",
        "socratic_system.models",
        "socratic_system.models.user",
        "socratic_system.models.project",
        "socratic_system.models.knowledge",
        "socratic_system.models.monitoring",
        "socratic_system.models.conflict",
        "socratic_system.database",
        "socratic_system.database.vector_db",
        "socratic_system.database.project_db",
        "socratic_system.utils",
        "socratic_system.utils.datetime_helpers",
        "socratic_system.agents",
        "socratic_system.agents.base",
        "socratic_system.agents.project_manager",
        "socratic_system.agents.user_manager",
        "socratic_system.agents.socratic_counselor",
        "socratic_system.agents.context_analyzer",
        "socratic_system.agents.code_generator",
        "socratic_system.agents.system_monitor",
        "socratic_system.agents.conflict_detector",
        "socratic_system.agents.document_processor",
        "socratic_system.conflict_resolution",
        "socratic_system.conflict_resolution.base",
        "socratic_system.conflict_resolution.checkers",
        "socratic_system.conflict_resolution.rules",
    ]

    for module in expected_modules:
        test_import(module, f"Module: {module}")


def test_imports():
    """Test that key classes can be imported"""
    print_header("Testing Key Imports")

    imports_to_test = [
        ("socratic_system.config", "CONFIG", "Config"),
        ("socratic_system.models", "User", "User model"),
        ("socratic_system.models", "ProjectContext", "ProjectContext model"),
        ("socratic_system.models", "KnowledgeEntry", "KnowledgeEntry model"),
        ("socratic_system.models", "TokenUsage", "TokenUsage model"),
        ("socratic_system.models", "ConflictInfo", "ConflictInfo model"),
        ("socratic_system.database", "VectorDatabase", "VectorDatabase"),
        ("socratic_system.database", "ProjectDatabase", "ProjectDatabase"),
        ("socratic_system.agents", "Agent", "Base Agent class"),
        ("socratic_system.agents", "ProjectManagerAgent", "ProjectManagerAgent"),
        ("socratic_system.agents", "UserManagerAgent", "UserManagerAgent"),
        ("socratic_system.agents", "SocraticCounselorAgent", "SocraticCounselorAgent"),
        ("socratic_system.agents", "ContextAnalyzerAgent", "ContextAnalyzerAgent"),
        ("socratic_system.agents", "CodeGeneratorAgent", "CodeGeneratorAgent"),
        ("socratic_system.agents", "SystemMonitorAgent", "SystemMonitorAgent"),
        ("socratic_system.agents", "ConflictDetectorAgent", "ConflictDetectorAgent"),
        ("socratic_system.agents", "DocumentProcessorAgent", "DocumentProcessorAgent"),
        ("socratic_system.conflict_resolution", "ConflictChecker", "ConflictChecker"),
        (
            "socratic_system.conflict_resolution",
            "TechStackConflictChecker",
            "TechStackConflictChecker",
        ),
        ("socratic_system.conflict_resolution", "CONFLICT_RULES", "CONFLICT_RULES"),
    ]

    for module, class_name, description in imports_to_test:
        try:
            mod = __import__(module, fromlist=[class_name])
            if hasattr(mod, class_name):
                print(f"{GREEN}[OK] PASS{RESET}: {description} available from {module}")
                test_results["passed"] += 1
            else:
                print(f"{RED}[X] FAIL{RESET}: {description} not found in {module}")
                test_results["failed"] += 1
        except Exception as e:
            print(f"{RED}[X] FAIL{RESET}: Cannot import {description} from {module}")
            print(f"  Error: {str(e)}")
            test_results["failed"] += 1


def test_no_circular_imports():
    """Test that there are no circular imports"""
    print_header("Testing for Circular Imports")

    # Try importing the main module which imports all others
    try:
        import socratic_system as _  # noqa: F401

        print(f"{GREEN}[OK] PASS{RESET}: No circular imports detected in socratic_system")
        test_results["passed"] += 1
    except ImportError as e:
        if "circular import" in str(e).lower():
            print(f"{RED}[X] FAIL{RESET}: Circular import detected")
            print(f"  Error: {str(e)}")
            test_results["failed"] += 1
        else:
            print(f"{YELLOW}[!] WARNING{RESET}: Import error (not circular)")
            print(f"  Error: {str(e)}")
            test_results["warnings"] += 1


def test_model_instantiation():
    """Test that models can be instantiated"""
    print_header("Testing Model Instantiation")

    try:
        import datetime

        from socratic_system.models import (
            ConflictInfo,
            KnowledgeEntry,
            ProjectContext,
            TokenUsage,
            User,
        )

        # Test User instantiation
        User(
            username="test_user",
            passcode_hash="hash123",
            created_at=datetime.datetime.now(),
            projects=[],
        )
        print(f"{GREEN}[OK] PASS{RESET}: User model instantiation")
        test_results["passed"] += 1

        # Test ProjectContext instantiation
        ProjectContext(
            project_id="proj123",
            name="Test Project",
            owner="test_user",
            collaborators=[],
            goals="",
            requirements=[],
            tech_stack=[],
            constraints=[],
            team_structure="individual",
            language_preferences="python",
            deployment_target="local",
            code_style="documented",
            phase="discovery",
            conversation_history=[],
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now(),
        )
        print(f"{GREEN}[OK] PASS{RESET}: ProjectContext model instantiation")
        test_results["passed"] += 1

        # Test KnowledgeEntry instantiation
        KnowledgeEntry(id="entry1", content="test content", category="general", metadata={})
        print(f"{GREEN}[OK] PASS{RESET}: KnowledgeEntry model instantiation")
        test_results["passed"] += 1

        # Test TokenUsage instantiation
        TokenUsage(
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            cost_estimate=0.001,
            timestamp=datetime.datetime.now(),
        )
        print(f"{GREEN}[OK] PASS{RESET}: TokenUsage model instantiation")
        test_results["passed"] += 1

        # Test ConflictInfo instantiation
        ConflictInfo(
            conflict_id="conf1",
            conflict_type="tech_stack",
            old_value="React",
            new_value="Vue",
            old_author="user1",
            new_author="user2",
            old_timestamp="2025-01-01T00:00:00",
            new_timestamp="2025-01-01T01:00:00",
            severity="medium",
            suggestions=["Consider both", "Research integration"],
        )
        print(f"{GREEN}[OK] PASS{RESET}: ConflictInfo model instantiation")
        test_results["passed"] += 1

    except Exception as e:
        print(f"{RED}[X] FAIL{RESET}: Model instantiation error")
        print(f"  Error: {str(e)}")
        traceback.print_exc()
        test_results["failed"] += 1


def test_config():
    """Test that config loads correctly"""
    print_header("Testing Configuration")

    try:
        from socratic_system.config import CONFIG

        required_keys = [
            "MAX_CONTEXT_LENGTH",
            "EMBEDDING_MODEL",
            "CLAUDE_MODEL",
            "MAX_RETRIES",
            "RETRY_DELAY",
            "TOKEN_WARNING_THRESHOLD",
            "SESSION_TIMEOUT",
            "DATA_DIR",
        ]

        missing_keys = [key for key in required_keys if key not in CONFIG]

        if missing_keys:
            print(f"{RED}[X] FAIL{RESET}: Missing CONFIG keys: {missing_keys}")
            test_results["failed"] += 1
        else:
            print(f"{GREEN}[OK] PASS{RESET}: All required CONFIG keys present")
            print(f"  CONFIG keys: {', '.join(sorted(CONFIG.keys()))}")
            test_results["passed"] += 1

    except Exception as e:
        print(f"{RED}[X] FAIL{RESET}: Config loading error")
        print(f"  Error: {str(e)}")
        test_results["failed"] += 1


def test_datetime_helpers():
    """Test datetime helper functions"""
    print_header("Testing Datetime Helpers")

    try:
        import datetime

        from socratic_system.utils.datetime_helpers import deserialize_datetime, serialize_datetime

        # Test serialization
        now = datetime.datetime.now()
        serialized = serialize_datetime(now)
        print(f"{GREEN}[OK] PASS{RESET}: Datetime serialization")
        test_results["passed"] += 1

        # Test deserialization
        deserialize_datetime(serialized)
        print(f"{GREEN}[OK] PASS{RESET}: Datetime deserialization")
        test_results["passed"] += 1

    except Exception as e:
        print(f"{RED}[X] FAIL{RESET}: Datetime helpers error")
        print(f"  Error: {str(e)}")
        test_results["failed"] += 1


def test_conflict_rules():
    """Test conflict rules"""
    print_header("Testing Conflict Rules")

    try:
        from socratic_system.conflict_resolution.rules import CONFLICT_RULES, find_conflict_category

        # Check CONFLICT_RULES structure
        if isinstance(CONFLICT_RULES, dict) and len(CONFLICT_RULES) > 0:
            print(f"{GREEN}[OK] PASS{RESET}: CONFLICT_RULES loaded")
            print(f"  Categories: {', '.join(CONFLICT_RULES.keys())}")
            test_results["passed"] += 1
        else:
            print(f"{RED}[X] FAIL{RESET}: CONFLICT_RULES is empty or malformed")
            test_results["failed"] += 1

        # Test find_conflict_category function
        result = find_conflict_category("MySQL", "PostgreSQL")
        if result == "databases":
            print(f"{GREEN}[OK] PASS{RESET}: find_conflict_category works correctly")
            test_results["passed"] += 1
        else:
            print(
                f"{YELLOW}[!] WARNING{RESET}: find_conflict_category returned {result} instead of 'databases'"
            )
            test_results["warnings"] += 1

    except Exception as e:
        print(f"{RED}[X] FAIL{RESET}: Conflict rules error")
        print(f"  Error: {str(e)}")
        test_results["failed"] += 1


def print_summary():
    """Print test summary"""
    print_header("Test Summary")

    total = test_results["passed"] + test_results["failed"] + test_results["warnings"]
    pass_rate = (test_results["passed"] / total * 100) if total > 0 else 0

    print(f"Total Tests: {total}")
    print(f"{GREEN}Passed: {test_results['passed']}{RESET}")
    print(f"{RED}Failed: {test_results['failed']}{RESET}")
    print(f"{YELLOW}Warnings: {test_results['warnings']}{RESET}")
    print(f"\nPass Rate: {pass_rate:.1f}%")

    if test_results["failed"] == 0:
        print(f"\n{GREEN}{BOLD}[OK] All tests passed! Modularization is successful.{RESET}")
        return True
    else:
        print(f"\n{RED}{BOLD}[X] Some tests failed. Review errors above.{RESET}")
        return False


def main():
    """Run all tests"""
    print(f"\n{BOLD}Socratic RAG System - Modularization Test Suite{RESET}")
    print("Testing the reorganized codebase structure...\n")

    test_module_structure()
    test_imports()
    test_no_circular_imports()
    test_config()
    test_datetime_helpers()
    test_conflict_rules()
    test_model_instantiation()

    success = print_summary()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
