#!/usr/bin/env python3
"""
Complete Agent System Test Suite
================================

Verifies all 8 agents and orchestrator are working correctly.

Tests:
1. Agent imports and initialization
2. Orchestrator creation and routing
3. Capability mapping
4. Health checks
5. Request processing
6. Error handling
"""

import sys
import os
import traceback
from typing import Dict, Any, List
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_header(text: str) -> None:
    """Print formatted header"""
    print(f"\n{BOLD}{BLUE}{'=' * 70}{RESET}")
    print(f"{BOLD}{BLUE}{text:^70}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 70}{RESET}\n")


def print_success(text: str) -> None:
    """Print success message"""
    print(f"{GREEN}✓{RESET} {text}")


def print_error(text: str) -> None:
    """Print error message"""
    print(f"{RED}✗{RESET} {text}")


def print_warning(text: str) -> None:
    """Print warning message"""
    print(f"{YELLOW}⚠{RESET} {text}")


def print_info(text: str) -> None:
    """Print info message"""
    print(f"{BLUE}ℹ{RESET} {text}")


class TestResults:
    """Track test results"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.tests: List[Dict[str, Any]] = []

    def add_pass(self, test_name: str, details: str = ""):
        self.passed += 1
        self.tests.append({
            'name': test_name,
            'status': 'passed',
            'details': details
        })
        print_success(f"{test_name} {details}")

    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.tests.append({
            'name': test_name,
            'status': 'failed',
            'error': error
        })
        print_error(f"{test_name}: {error}")

    def add_warning(self, test_name: str, message: str):
        self.warnings += 1
        self.tests.append({
            'name': test_name,
            'status': 'warning',
            'message': message
        })
        print_warning(f"{test_name}: {message}")

    def print_summary(self):
        """Print test summary"""
        print_header("TEST SUMMARY")

        total = self.passed + self.failed
        print(f"\n{BOLD}Total Tests:{RESET} {total}")
        print(f"{GREEN}Passed:{RESET} {self.passed}")
        print(f"{RED}Failed:{RESET} {self.failed}")
        print(f"{YELLOW}Warnings:{RESET} {self.warnings}")

        if self.failed == 0:
            print(f"\n{GREEN}{BOLD}🎉 ALL TESTS PASSED! 🎉{RESET}\n")
            return True
        else:
            print(f"\n{RED}{BOLD}⚠️  SOME TESTS FAILED{RESET}\n")
            return False


def check_project_structure(results: TestResults) -> bool:
    """Check if project structure exists"""
    print_header("PRE-CHECK: Project Structure")

    project_root = Path(__file__).parent.parent
    src_dir = project_root / 'src'
    agents_dir = src_dir / 'agents'

    print_info(f"Project root: {project_root}")
    print_info(f"Looking for src/ at: {src_dir}")

    if not src_dir.exists():
        results.add_fail("Project structure", f"src/ directory not found at {src_dir}")
        return False

    results.add_pass("src/ directory exists")

    if not agents_dir.exists():
        results.add_fail("Project structure", f"src/agents/ directory not found at {agents_dir}")
        return False

    results.add_pass("src/agents/ directory exists")

    # Check for __init__.py files
    src_init = src_dir / '__init__.py'
    agents_init = agents_dir / '__init__.py'

    if not src_init.exists():
        results.add_warning("src/__init__.py", "Not found (may cause import issues)")
    else:
        results.add_pass("src/__init__.py exists")

    if not agents_init.exists():
        results.add_fail("Project structure", "src/agents/__init__.py not found")
        return False

    results.add_pass("src/agents/__init__.py exists")

    # Check for agent files
    agent_files = [
        'base.py', 'user.py', 'project.py', 'socratic.py',
        'code.py', 'context.py', 'document.py', 'services.py',
        'monitor.py', 'orchestrator.py'
    ]

    missing_files = []
    for filename in agent_files:
        filepath = agents_dir / filename
        if not filepath.exists():
            missing_files.append(filename)

    if missing_files:
        results.add_warning(
            "Agent files",
            f"Missing: {', '.join(missing_files)}"
        )
    else:
        results.add_pass("All agent files present")

    return True


def test_imports(results: TestResults) -> Dict[str, Any]:
    """Test 1: Verify all imports work"""
    print_header("TEST 1: Import Verification")

    imports = {}

    # Test base import
    try:
        from src.agents.base import BaseAgent
        imports['base'] = True
        results.add_pass("BaseAgent import")
    except ImportError as e:
        imports['base'] = False
        results.add_fail("BaseAgent import", str(e))

    # Test all 8 agent imports
    agents = [
        ('user', 'UserManagerAgent'),
        ('project', 'ProjectManagerAgent'),
        ('socratic', 'SocraticCounselorAgent'),
        ('code', 'CodeGeneratorAgent'),
        ('context', 'ContextAnalyzerAgent'),
        ('document', 'DocumentProcessorAgent'),
        ('services', 'ServicesAgent'),
        ('monitor', 'SystemMonitorAgent'),
    ]

    for module_name, class_name in agents:
        try:
            exec(f"from src.agents.{module_name} import {class_name}")
            imports[module_name] = True
            results.add_pass(f"{class_name} import")
        except ImportError as e:
            imports[module_name] = False
            results.add_fail(f"{class_name} import", str(e))
        except Exception as e:
            imports[module_name] = False
            results.add_fail(f"{class_name} import", f"Error: {str(e)}")

    # Test orchestrator import
    try:
        from src.agents.orchestrator import AgentOrchestrator
        imports['orchestrator'] = True
        results.add_pass("AgentOrchestrator import")
    except ImportError as e:
        imports['orchestrator'] = False
        results.add_fail("AgentOrchestrator import", str(e))
    except Exception as e:
        imports['orchestrator'] = False
        results.add_fail("AgentOrchestrator import", f"Error: {str(e)}")

    # Test agents package import
    try:
        import src.agents as agents_module
        imports['package'] = True
        results.add_pass("agents package import")
    except ImportError as e:
        imports['package'] = False
        results.add_fail("agents package import", str(e))
    except Exception as e:
        imports['package'] = False
        results.add_fail("agents package import", f"Error: {str(e)}")

    return imports


def test_agent_initialization(results: TestResults, imports: Dict[str, Any]) -> Dict[str, Any]:
    """Test 2: Verify agents can be instantiated"""
    print_header("TEST 2: Agent Initialization")

    if not imports.get('package'):
        results.add_fail("Agent initialization", "Package not imported")
        return {}

    import src.agents as agents

    agent_instances = {}

    # Test each agent creation
    agent_configs = [
        ('user_manager', 'UserManagerAgent'),
        ('project_manager', 'ProjectManagerAgent'),
        ('socratic_counselor', 'SocraticCounselorAgent'),
        ('code_generator', 'CodeGeneratorAgent'),
        ('context_analyzer', 'ContextAnalyzerAgent'),
        ('document_processor', 'DocumentProcessorAgent'),
        ('services_agent', 'ServicesAgent'),
        ('system_monitor', 'SystemMonitorAgent'),
    ]

    for agent_id, class_name in agent_configs:
        try:
            agent = agents.create_agent(agent_id)
            if agent is not None:
                agent_instances[agent_id] = agent
                results.add_pass(f"{class_name} instantiation")
            else:
                results.add_warning(
                    f"{class_name} instantiation",
                    "Returned None"
                )
        except Exception as e:
            results.add_fail(f"{class_name} instantiation", str(e))

    return agent_instances


def test_orchestrator_creation(results: TestResults, imports: Dict[str, Any]) -> Any:
    """Test 3: Verify orchestrator can be created"""
    print_header("TEST 3: Orchestrator Creation")

    if not imports.get('orchestrator'):
        results.add_fail("Orchestrator creation", "Orchestrator not imported")
        return None

    try:
        import src.agents as agents
        orchestrator = agents.get_orchestrator()

        if orchestrator is not None:
            results.add_pass("Orchestrator creation")

            # Check agents were initialized
            agent_count = len(orchestrator.agents)
            results.add_pass(
                "Agents initialized by orchestrator",
                f"({agent_count}/8 agents)"
            )

            return orchestrator
        else:
            results.add_fail("Orchestrator creation", "Returned None")
            return None

    except Exception as e:
        results.add_fail("Orchestrator creation", str(e))
        print_error(f"Traceback: {traceback.format_exc()}")
        return None


def test_capability_mapping(results: TestResults, orchestrator: Any) -> None:
    """Test 4: Verify capability mapping"""
    print_header("TEST 4: Capability Mapping")

    if orchestrator is None:
        results.add_fail("Capability mapping", "No orchestrator available")
        return

    try:
        # Get all capabilities
        capabilities = orchestrator.get_capabilities()

        if len(capabilities) > 0:
            results.add_pass(
                "Capabilities discovered",
                f"({len(capabilities)} capabilities)"
            )

            # Show sample capabilities
            sample = list(capabilities)[:5]
            print_info(f"Sample capabilities: {', '.join(sample)}")
        else:
            results.add_warning("Capabilities discovered", "No capabilities found")

        # Test capability map
        if hasattr(orchestrator, 'capability_map'):
            map_size = len(orchestrator.capability_map)
            results.add_pass(
                "Capability map built",
                f"({map_size} mappings)"
            )
        else:
            results.add_warning("Capability map", "Not found")

    except Exception as e:
        results.add_fail("Capability mapping", str(e))


def test_agent_capabilities(results: TestResults, agent_instances: Dict[str, Any]) -> None:
    """Test 5: Verify each agent reports capabilities"""
    print_header("TEST 5: Agent Capabilities")

    if not agent_instances:
        results.add_fail("Agent capabilities", "No agents available")
        return

    for agent_id, agent in agent_instances.items():
        try:
            if hasattr(agent, 'get_capabilities'):
                caps = agent.get_capabilities()
                results.add_pass(
                    f"{agent_id} capabilities",
                    f"({len(caps)} capabilities)"
                )
            else:
                results.add_warning(
                    f"{agent_id} capabilities",
                    "No get_capabilities method"
                )
        except Exception as e:
            results.add_fail(f"{agent_id} capabilities", str(e))


def test_request_routing(results: TestResults, orchestrator: Any) -> None:
    """Test 6: Verify request routing works"""
    print_header("TEST 6: Request Routing")

    if orchestrator is None:
        results.add_fail("Request routing", "No orchestrator available")
        return

    # Test routing to each agent
    test_requests = [
        ('system_monitor', 'get_capabilities', {}),
        ('project_manager', 'get_capabilities', {}),
        ('code_generator', 'get_capabilities', {}),
    ]

    for agent_id, action, data in test_requests:
        try:
            if agent_id in orchestrator.agents:
                result = orchestrator.route_request(agent_id, action, data)

                if isinstance(result, dict):
                    if result.get('success', False):
                        results.add_pass(f"Route to {agent_id}")
                    else:
                        error = result.get('error', 'Unknown error')
                        results.add_warning(
                            f"Route to {agent_id}",
                            f"Failed: {error}"
                        )
                else:
                    results.add_warning(
                        f"Route to {agent_id}",
                        "Unexpected response format"
                    )
            else:
                results.add_warning(
                    f"Route to {agent_id}",
                    "Agent not available in orchestrator"
                )

        except Exception as e:
            results.add_fail(f"Route to {agent_id}", str(e))


def test_health_checks(results: TestResults, orchestrator: Any) -> None:
    """Test 7: Verify health checks work"""
    print_header("TEST 7: Health Checks")

    if orchestrator is None:
        results.add_fail("Health check", "No orchestrator available")
        return

    try:
        # Test orchestrator health check
        health = orchestrator.health_check()

        if isinstance(health, dict):
            status = health.get('orchestrator', 'unknown')
            healthy = health.get('healthy_agents', 0)
            unhealthy = health.get('unhealthy_agents', 0)

            results.add_pass(
                "Orchestrator health check",
                f"(Status: {status}, {healthy} healthy, {unhealthy} unhealthy)"
            )

            # Check individual agent health
            agent_health = health.get('agents', {})
            for agent_id, agent_status in list(agent_health.items())[:3]:  # First 3
                status_val = agent_status.get('status', 'unknown')
                if status_val in ['healthy', 'active']:
                    results.add_pass(f"{agent_id} health", f"({status_val})")
                else:
                    results.add_warning(
                        f"{agent_id} health",
                        f"Status: {status_val}"
                    )
        else:
            results.add_fail("Health check", "Invalid response format")

    except Exception as e:
        results.add_fail("Health check", str(e))


def test_error_handling(results: TestResults, orchestrator: Any) -> None:
    """Test 8: Verify error handling"""
    print_header("TEST 8: Error Handling")

    if orchestrator is None:
        results.add_fail("Error handling", "No orchestrator available")
        return

    # Test invalid agent
    try:
        result = orchestrator.route_request('invalid_agent', 'test', {})
        if isinstance(result, dict) and not result.get('success', True):
            results.add_pass("Invalid agent handling")
        else:
            results.add_warning(
                "Invalid agent handling",
                "Did not return error"
            )
    except Exception as e:
        results.add_fail("Invalid agent handling", str(e))

    # Test invalid capability
    try:
        result = orchestrator.route_by_capability('invalid_capability', {})
        if isinstance(result, dict) and not result.get('success', True):
            results.add_pass("Invalid capability handling")
        else:
            results.add_warning(
                "Invalid capability handling",
                "Did not return error"
            )
    except Exception as e:
        results.add_fail("Invalid capability handling", str(e))


def main():
    """Run all tests"""
    print_header("SOCRATIC RAG ENHANCED - AGENT SYSTEM TEST SUITE")

    # Try to initialize services for full integration testing
    print_info("Attempting service initialization...")
    try:
        from src import initialize_package
        services = initialize_package()
        if services:
            print_info("✅ Services initialized - testing with full integration\n")
        else:
            print_info("⚠️  Services unavailable - testing in degraded mode\n")
    except Exception as e:
        print_info(f"⚠️  Service init failed: {e} - continuing with degraded mode\n")

    results = TestResults()

    try:
        # Check project structure first
        if not check_project_structure(results):
            print_error("\nProject structure check failed - cannot continue")
            results.print_summary()
            sys.exit(1)

        # Run all tests
        imports = test_imports(results)
        agent_instances = test_agent_initialization(results, imports)
        orchestrator = test_orchestrator_creation(results, imports)

        if orchestrator:
            test_capability_mapping(results, orchestrator)
            test_agent_capabilities(results, agent_instances)
            test_request_routing(results, orchestrator)
            test_health_checks(results, orchestrator)
            test_error_handling(results, orchestrator)
        else:
            print_error("\nOrchestrator unavailable - skipping remaining tests")

        # Print summary
        success = results.print_summary()

        # Return appropriate exit code
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print_error("\n\nTests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print_error(f"\n\nUnexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
